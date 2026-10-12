from types import SimpleNamespace
from unittest import mock

from dcim.models import MACAddress
from django.urls import reverse
from django.utils import timezone

from ..choices import VendorSourceChoices, VendorStatusChoices
from ..models import MACVendor
from ..testing import PluginViewTestCase
from ..testing.utils import disable_warnings


def make_vendor(prefix="000393", organization="Apple, Inc.", **kwargs):
    return MACVendor.objects.create(
        prefix=prefix,
        prefix_length=len(prefix) * 4,
        status=VendorStatusChoices.REGISTERED if organization else VendorStatusChoices.UNREGISTERED,
        organization=organization,
        source=kwargs.pop("source", VendorSourceChoices.KEYLESS),
        last_checked=timezone.now(),
        **kwargs,
    )


class MACVendorViewTestCase(PluginViewTestCase):
    @classmethod
    def setUpTestData(cls):
        make_vendor()
        make_vendor("70B3D5F00", "Aplex Technology Inc.", block_type="MA-S", source=VendorSourceChoices.API_KEY)

    def test_list(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        response = self.client.get(reverse("plugins:netbox_macadress:macvendor_list"))
        self.assertHttpStatus(response, 200)
        self.assertContains(response, "Apple, Inc.")
        self.assertNotContains(response, "Look up now")

    def test_pages_as_superuser(self):
        """A superuser sees every action button, so every linked view must exist."""
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(reverse("plugins:netbox_macadress:macvendor_list"))
        self.assertHttpStatus(response, 200)
        self.assertContains(response, "Look up now")
        response = self.client.get(MACVendor.objects.get(prefix="000393").get_absolute_url())
        self.assertHttpStatus(response, 200)

    def test_list_filters(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        url = reverse("plugins:netbox_macadress:macvendor_list")
        response = self.client.get(url, {"mac_address": "70:B3:D5:F0:00:42"})
        self.assertContains(response, "Aplex Technology Inc.")
        self.assertNotContains(response, "Apple, Inc.")
        response = self.client.get(url, {"q": "aplex"})
        self.assertContains(response, "Aplex Technology Inc.")
        self.assertNotContains(response, "Apple, Inc.")

    def test_list_without_permission(self):
        with disable_warnings("django.request"):
            response = self.client.get(reverse("plugins:netbox_macadress:macvendor_list"))
        self.assertHttpStatus(response, 403)

    def test_detail(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        instance = MACVendor.objects.get(prefix="70B3D5F00")
        response = self.client.get(instance.get_absolute_url())
        self.assertHttpStatus(response, 200)
        self.assertContains(response, "70:B3:D5:F0:0/36")
        self.assertContains(response, "mac_address__isw=70:B3:D5:F0:0")

    def test_delete(self):
        self.add_permissions("netbox_macadress.view_macvendor", "netbox_macadress.delete_macvendor")
        instance = MACVendor.objects.get(prefix="000393")
        url = reverse("plugins:netbox_macadress:macvendor_delete", kwargs={"pk": instance.pk})
        response = self.client.post(url, {"confirm": True}, follow=True)
        self.assertHttpStatus(response, 200)
        self.assertFalse(MACVendor.objects.filter(pk=instance.pk).exists())

    def test_no_add_or_edit_views(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        response = self.client.get(reverse("plugins:netbox_macadress:macvendor_list"))
        self.assertNotContains(response, reverse("plugins:netbox_macadress:macvendor_list") + "add/")

    def test_sync_button_and_view(self):
        self.add_permissions("netbox_macadress.view_macvendor", "netbox_macadress.add_macvendor")
        response = self.client.get(reverse("plugins:netbox_macadress:macvendor_list"))
        self.assertContains(response, "Look up now")

        job = SimpleNamespace(pk=1)
        with mock.patch("netbox_macadress.views.VendorLookupJob.enqueue_once", return_value=job) as enqueue:
            response = self.client.post(reverse("plugins:netbox_macadress:macvendor_sync"))
        enqueue.assert_called_once()
        self.assertRedirects(response, reverse("core:job", kwargs={"pk": 1}), fetch_redirect_response=False)

    def test_sync_without_permission(self):
        with disable_warnings("django.request"):
            response = self.client.post(reverse("plugins:netbox_macadress:macvendor_sync"))
        self.assertHttpStatus(response, 403)


class CorePageTestCase(PluginViewTestCase):
    """The vendor panel and column on NetBox's own MAC address pages."""

    @classmethod
    def setUpTestData(cls):
        make_vendor()

    def setUp(self):
        super().setUp()
        self.add_permissions("dcim.view_macaddress")

    def get_mac_page(self, value):
        mac = MACAddress.objects.create(mac_address=value)
        return self.client.get(mac.get_absolute_url())

    def test_panel_known_vendor(self):
        response = self.get_mac_page("00:03:93:12:34:56")
        self.assertHttpStatus(response, 200)
        self.assertContains(response, "Apple, Inc.")
        self.assertContains(response, "https://macadress.com/lookup/00:03:93:12:34:56")
        self.assertContains(response, "Free API key adds country and block details")

    def test_panel_pending(self):
        self.assertContains(self.get_mac_page("00:00:0C:12:34:56"), "Lookup pending")

    def test_panel_locally_administered(self):
        self.assertContains(self.get_mac_page("02:00:00:00:00:01"), "Locally administered")

    def test_vendor_column(self):
        from dcim.tables import MACAddressTable

        MACAddress.objects.create(mac_address="00:03:93:12:34:56")
        MACAddress.objects.create(mac_address="02:00:00:00:00:01")
        table = MACAddressTable(MACAddress.objects.order_by("mac_address"))
        self.assertIn("macadress_vendor", table.columns.names())
        self.assertNotIn("macadress_vendor", table.Meta.default_columns)
        rows = list(table.rows)
        self.assertIn("Apple, Inc.", rows[0].get_cell("macadress_vendor"))
        self.assertIn("Locally administered", rows[1].get_cell("macadress_vendor"))
        self.assertEqual(rows[0].get_cell_value("macadress_vendor"), "Apple, Inc.")
