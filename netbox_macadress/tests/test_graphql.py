from django.utils import timezone

from ..choices import VendorSourceChoices, VendorStatusChoices
from ..models import MACVendor
from ..testing import PluginGraphQLTestCase


class MACVendorGraphQLTestCase(PluginGraphQLTestCase):
    @classmethod
    def setUpTestData(cls):
        MACVendor.objects.create(
            prefix="000393",
            prefix_length=24,
            status=VendorStatusChoices.REGISTERED,
            organization="Apple, Inc.",
            source=VendorSourceChoices.KEYLESS,
            last_checked=timezone.now(),
        )

    def test_list(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        response = self.execute_query("query { mac_vendor_list { id prefix organization status } }")
        self.assertIsNone(response.get("errors"))
        self.assertEqual(response["data"]["mac_vendor_list"][0]["organization"], "Apple, Inc.")

    def test_single(self):
        self.add_permissions("netbox_macadress.view_macvendor")
        pk = MACVendor.objects.get().pk
        response = self.execute_query(f"query {{ mac_vendor(id: {pk}) {{ prefix prefix_length }} }}")
        self.assertIsNone(response.get("errors"))
        self.assertEqual(response["data"]["mac_vendor"]["prefix_length"], 24)
