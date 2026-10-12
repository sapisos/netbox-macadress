"""
Tables for NetBox macadress.
"""

import django_tables2 as tables
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from netbox.tables import NetBoxTable, columns

from .models import MACVendor
from .utils import local_status, normalize


class MACVendorTable(NetBoxTable):
    prefix = tables.Column(
        verbose_name=_("Prefix"),
        accessor="prefix_display",
        order_by=("prefix",),
        linkify=True,
    )
    organization = tables.Column(
        verbose_name=_("Organization"),
    )
    status = columns.ChoiceFieldColumn(
        verbose_name=_("Status"),
    )
    source = columns.ChoiceFieldColumn(
        verbose_name=_("Source"),
    )
    tags = columns.TagColumn(
        url_name="plugins:netbox_macadress:macvendor_list",
    )
    actions = columns.ActionsColumn(
        actions=("delete", "changelog"),
    )

    class Meta(NetBoxTable.Meta):
        model = MACVendor
        fields = (
            "pk",
            "id",
            "prefix",
            "prefix_length",
            "organization",
            "status",
            "block_type",
            "country",
            "address",
            "source",
            "last_checked",
            "tags",
            "created",
            "last_updated",
            "actions",
        )
        default_columns = ("prefix", "organization", "status", "block_type", "country", "last_checked")


class VendorColumn(tables.Column):
    """
    Vendor column added to NetBox's MAC address table. Hidden by default;
    enable it under Configure Table.
    """

    def __init__(self):
        super().__init__(accessor="mac_address", verbose_name=_("Vendor"), orderable=False, empty_values=())

    @staticmethod
    def _lookup(value):
        """(local status, MACVendor entry) for a MAC address value."""
        hex12 = normalize(value)
        if hex12 is None:
            return None, None
        if status := local_status(hex12):
            return status, None
        return None, MACVendor.objects.for_mac(hex12)

    def render(self, value):
        status, entry = self._lookup(value)
        if status:
            label = _("Multicast") if status == "multicast" else _("Locally administered")
            return format_html('<span class="text-muted">{}</span>', label)
        if entry is None or not entry.organization:
            return self.default
        return format_html('<a href="{}">{}</a>', entry.get_absolute_url(), entry.organization)

    def value(self, value):
        """Plain text for exports."""
        status, entry = self._lookup(value)
        if status:
            return "Multicast" if status == "multicast" else "Locally administered"
        return entry.organization if entry else ""
