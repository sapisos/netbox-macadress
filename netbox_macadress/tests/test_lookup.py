from datetime import timedelta
from unittest import mock

import macadress
from dcim.models import MACAddress
from django.test import TestCase, override_settings
from django.utils import timezone

from .. import lookup
from ..choices import VendorSourceChoices, VendorStatusChoices
from ..models import MACVendor
from .fakes import FakeClient, batch_item

PLUGIN_CONFIG = {
    "api_key": "",
    "base_url": "https://api.macadress.com",
    "timeout": 10,
    "sync_interval": 60,
    "max_lookups_per_run": 500,
    "refresh_days": 30,
    "lookup_on_save": False,
}


def plugin_config(**overrides):
    return override_settings(PLUGINS_CONFIG={"netbox_macadress": {**PLUGIN_CONFIG, **overrides}})


def make_macs(*values):
    for value in values:
        MACAddress.objects.create(mac_address=value)


@mock.patch.object(lookup, "_sleep", lambda seconds: None)
@mock.patch.dict("os.environ", {"MACADRESS_API_KEY": ""})
class KeylessSyncTestCase(TestCase):
    def run_sync(self, client, **config):
        with plugin_config(**config), mock.patch.object(lookup, "open_client", client.opener):
            return lookup.sync()

    def test_one_lookup_per_oui(self):
        make_macs("00:03:93:00:00:01", "00:03:93:00:00:02", "3C:22:FB:00:00:01")
        client = FakeClient(names={"000393000001": "Apple, Inc.", "3C22FB000001": "Apple, Inc."})

        self.assertEqual(self.run_sync(client), (2, 0))
        self.assertEqual(len(client.vendor_calls), 2)
        entry = MACVendor.objects.get(prefix="000393")
        self.assertEqual(entry.organization, "Apple, Inc.")
        self.assertEqual(entry.prefix_length, 24)
        self.assertEqual(entry.status, VendorStatusChoices.REGISTERED)
        self.assertEqual(entry.source, VendorSourceChoices.KEYLESS)

        # Everything is cached now: a second run makes no calls.
        client.vendor_calls.clear()
        self.assertEqual(self.run_sync(client), (0, 0))
        self.assertEqual(client.vendor_calls, [])

    def test_local_and_multicast_skipped(self):
        make_macs("02:00:00:00:00:01", "01:00:5E:00:00:01")
        client = FakeClient()
        self.assertEqual(self.run_sync(client), (0, 0))
        self.assertEqual(client.vendor_calls, [])

    def test_unregistered_cached(self):
        make_macs("00:00:00:00:00:01")
        self.run_sync(FakeClient())
        entry = MACVendor.objects.get(prefix="000000")
        self.assertEqual(entry.status, VendorStatusChoices.UNREGISTERED)
        self.assertEqual(entry.organization, "")

    def test_shared_oui_cached_per_block(self):
        make_macs("70:B3:D5:F0:00:01", "70:B3:D5:00:00:01")
        client = FakeClient(
            names={"70B3D5F00001": "Aplex Technology Inc.", "70B3D5000001": "IEEE Registration Authority"}
        )
        self.run_sync(client)
        self.assertEqual(MACVendor.objects.for_mac("70:B3:D5:F0:00:09").organization, "Aplex Technology Inc.")
        self.assertEqual(MACVendor.objects.for_mac("70:B3:D5:00:00:09").organization, "IEEE Registration Authority")
        self.assertFalse(MACVendor.objects.filter(prefix="70B3D5").exists())
        # A different block in the same OUI is not covered by either entry.
        self.assertIsNone(MACVendor.objects.for_mac("70:B3:D5:80:00:01"))

    def test_limit(self):
        make_macs("00:03:93:00:00:01", "3C:22:FB:00:00:01", "00:00:0C:00:00:01")
        self.assertEqual(self.run_sync(FakeClient(), max_lookups_per_run=2), (2, 1))
        self.assertEqual(self.run_sync(FakeClient(), max_lookups_per_run=2), (1, 0))

    def test_stale_entries_refreshed(self):
        make_macs("00:03:93:00:00:01")
        client = FakeClient(names={"000393000001": "Apple, Inc."})
        self.run_sync(client)
        MACVendor.objects.update(last_checked=timezone.now() - timedelta(days=31))
        client.vendor_calls.clear()
        self.assertEqual(self.run_sync(client), (1, 0))
        self.assertEqual(client.vendor_calls, ["000393000001"])

    def test_rate_limit_retried_once(self):
        make_macs("00:03:93:00:00:01")
        client = FakeClient(
            names={"000393000001": "Apple, Inc."},
            errors=[macadress.RateLimitError("slow down", retry_after=2)],
        )
        self.assertEqual(self.run_sync(client), (1, 0))

    def test_quota_aborts_and_keeps_progress(self):
        make_macs("00:03:93:00:00:01", "3C:22:FB:00:00:01")
        client = FakeClient(names={"000393000001": "Apple, Inc."})
        original = client.vendor

        def vendor(mac):
            if mac.startswith("3C22FB"):
                raise macadress.RateLimitError("rate limited", retry_after=36000)
            return original(mac)

        client.vendor = vendor
        with self.assertRaises(lookup.LookupAborted):
            self.run_sync(client)
        self.assertTrue(MACVendor.objects.filter(prefix="000393").exists())


@mock.patch.object(lookup, "_sleep", lambda seconds: None)
class KeyedSyncTestCase(TestCase):
    def run_sync(self, client, **config):
        with plugin_config(api_key="mk_test", **config), mock.patch.object(lookup, "open_client", client.opener):
            return lookup.sync()

    def test_batch_stores_details(self):
        make_macs("00:03:93:00:00:01", "70:B3:D5:F0:00:01")
        client = FakeClient(
            items={
                "000393000001": batch_item(
                    "000393000001", "Apple, Inc.", country="US", address="1 Infinite Loop Cupertino CA US 95014"
                ),
                "70B3D5F00001": batch_item(
                    "70B3D5F00001", "Aplex Technology Inc.", prefix_length=36, block_type="MA-S"
                ),
            }
        )
        self.assertEqual(self.run_sync(client), (2, 0))
        self.assertEqual(len(client.batch_calls), 1)
        apple = MACVendor.objects.get(prefix="000393")
        self.assertEqual((apple.country, apple.block_type, apple.source), ("US", "MA-L", VendorSourceChoices.API_KEY))
        self.assertEqual(MACVendor.objects.get(prefix="70B3D5F00").prefix_length, 36)

    def test_keyless_entries_upgraded(self):
        make_macs("70:B3:D5:F0:00:01")
        now = timezone.now()
        MACVendor.objects.create(
            prefix="70B3D5F00",
            prefix_length=36,
            status=VendorStatusChoices.REGISTERED,
            organization="Someone",
            source=VendorSourceChoices.KEYLESS,
            last_checked=now,
        )
        client = FakeClient(
            items={"70B3D5F00001": batch_item("70B3D5F00001", "Someone", prefix_length=28, block_type="MA-M")}
        )
        self.assertEqual(self.run_sync(client), (1, 0))
        # The MA-M entry replaces the narrower keyless one it contains.
        self.assertEqual(list(MACVendor.objects.values_list("prefix", flat=True)), ["70B3D5F"])
        self.assertEqual(self.run_sync(client), (0, 0))

    def test_bad_key_aborts(self):
        make_macs("00:03:93:00:00:01")
        client = FakeClient(errors=[macadress.AuthenticationError("invalid api key", status_code=401)])
        with self.assertRaises(lookup.LookupAborted):
            self.run_sync(client)


class ForMacTestCase(TestCase):
    def test_most_specific_wins(self):
        now = timezone.now()
        for prefix, name in (("70B3D5", "IEEE Registration Authority"), ("70B3D5F00", "Aplex Technology Inc.")):
            MACVendor.objects.create(
                prefix=prefix,
                prefix_length=len(prefix) * 4,
                status=VendorStatusChoices.REGISTERED,
                organization=name,
                source=VendorSourceChoices.API_KEY,
                last_checked=now,
            )
        self.assertEqual(MACVendor.objects.for_mac("70-b3-d5-f0-00-ff").organization, "Aplex Technology Inc.")
        self.assertIsNone(MACVendor.objects.for_mac("not a mac"))


class SignalTestCase(TestCase):
    def test_save_queues_lookup_once(self):
        with (
            plugin_config(lookup_on_save=True),
            mock.patch("netbox_macadress.jobs.VendorLookupJob.enqueue_once") as enqueue,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                make_macs("00:03:93:00:00:01", "02:00:00:00:00:01")
        # The locally administered address needs no lookup.
        self.assertEqual(enqueue.call_count, 1)

    def test_disabled(self):
        with (
            plugin_config(lookup_on_save=False),
            mock.patch("netbox_macadress.jobs.VendorLookupJob.enqueue_once") as enqueue,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                make_macs("00:03:93:00:00:01")
        enqueue.assert_not_called()
