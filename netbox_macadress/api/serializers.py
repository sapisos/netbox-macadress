"""
API serializers for NetBox macadress.
"""

from netbox.api.fields import ChoiceField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from ..choices import VendorSourceChoices, VendorStatusChoices
from ..models import MACVendor


class MACVendorSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_macadress-api:macvendor-detail")
    status = ChoiceField(choices=VendorStatusChoices, read_only=True)
    source = ChoiceField(choices=VendorSourceChoices, read_only=True)

    class Meta:
        model = MACVendor
        fields = (
            "id",
            "url",
            "display",
            "prefix",
            "prefix_length",
            "status",
            "organization",
            "block_type",
            "country",
            "address",
            "source",
            "last_checked",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "prefix", "organization")
        read_only_fields = (
            "prefix",
            "prefix_length",
            "organization",
            "block_type",
            "country",
            "address",
            "last_checked",
        )
