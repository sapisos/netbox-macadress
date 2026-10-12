"""
Content injected into core NetBox pages.
"""

from netbox.plugins import PluginTemplateExtension

from .lookup import api_key
from .models import MACVendor
from .utils import format_mac, local_status, normalize


def _vendor_panel(extension, mac):
    hex12 = normalize(mac)
    if hex12 is None:
        return ""
    status = local_status(hex12)
    return extension.render(
        "netbox_macadress/inc/vendor_panel.html",
        extra_context={
            "mac": format_mac(hex12),
            "local_status": status,
            "vendor": None if status else MACVendor.objects.for_mac(hex12),
            "keyed": bool(api_key()),
        },
    )


class MACAddressVendorPanel(PluginTemplateExtension):
    models = ["dcim.macaddress"]

    def right_page(self):
        return _vendor_panel(self, self.context["object"].mac_address)


class InterfaceVendorPanel(PluginTemplateExtension):
    models = ["dcim.interface", "virtualization.vminterface"]

    def right_page(self):
        primary = self.context["object"].primary_mac_address
        return _vendor_panel(self, primary.mac_address) if primary else ""


class VendorListButtons(PluginTemplateExtension):
    models = ["netbox_macadress.macvendor"]

    def list_buttons(self):
        if not self.context["request"].user.has_perm("netbox_macadress.add_macvendor"):
            return ""
        return self.render("netbox_macadress/inc/sync_button.html")


template_extensions = [MACAddressVendorPanel, InterfaceVendorPanel, VendorListButtons]
