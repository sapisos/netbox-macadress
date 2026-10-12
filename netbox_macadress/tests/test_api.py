from django.utils import timezone

from ..choices import VendorSourceChoices, VendorStatusChoices
from ..models import MACVendor
from ..testing import PluginAPITestCase
from ..testing.utils import disable_warnings


class MACVendorAPITestCase(PluginAPITestCase):
    @classmethod
    def setUpTestData(cls):
        for prefix, name in (("000393", "Apple, Inc."), ("00000C", "Cisco Systems, Inc")):
            MACVendor.objects.create(
                prefix=prefix,
                prefix_length=24,
                status=VendorStatusChoices.REGISTERED,
                organization=name,
                source=VendorSourceChoices.KEYLESS,
                last_checked=timezone.now(),
            )

    def setUp(self):
        super().setUp()
        self.list_url_name = "plugins-api:netbox_macadress-api:macvendor-list"
        self.detail_url_name = "plugins-api:netbox_macadress-api:macvendor-detail"

    def test_list(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        response = self.client.get(self._get_list_url())
        self.assertHttpStatus(response, 200)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_mac(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        response = self.client.get(self._get_list_url(), {"mac_address": "00:03:93:AB:CD:EF"})
        self.assertEqual([r["organization"] for r in response.data["results"]], ["Apple, Inc."])

    def test_get(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        instance = MACVendor.objects.get(prefix="000393")
        response = self.client.get(self._get_detail_url(instance))
        self.assertHttpStatus(response, 200)
        self.assertEqual(response.data["status"]["value"], "registered")
        self.assertEqual(response.data["display"], "00:03:93/24")

    def test_without_permission(self):
        with disable_warnings("django.request"):
            response = self.client.get(self._get_list_url())
        self.assertHttpStatus(response, 403)

    def test_create_not_allowed(self):
        self.add_permissions("netbox_macadress.add_macvendor")
        with disable_warnings("django.request"):
            response = self.client.post(self._get_list_url(), {"prefix": "ABCDEF"}, format="json")
        self.assertHttpStatus(response, 405)

    def test_delete(self):
        self.add_permissions("netbox_macadress.delete_macvendor")
        instance = MACVendor.objects.get(prefix="000393")
        response = self.client.delete(self._get_detail_url(instance))
        self.assertHttpStatus(response, 204)
        self.assertFalse(MACVendor.objects.filter(pk=instance.pk).exists())
