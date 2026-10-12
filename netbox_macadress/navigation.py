"""
Navigation menu items for NetBox macadress.
"""

from netbox.plugins import PluginMenuItem

menu_items = (
    PluginMenuItem(
        link="plugins:netbox_macadress:macvendor_list",
        link_text="MAC Vendors",
        permissions=["netbox_macadress.view_macvendor"],
    ),
)
