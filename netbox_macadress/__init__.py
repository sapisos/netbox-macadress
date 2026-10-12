"""
NetBox macadress

Plugin configuration for NetBox macadress.

For a complete list of PluginConfig attributes, see:
https://docs.netbox.dev/en/stable/plugins/development/#pluginconfig-attributes
"""

__author__ = """Samy Massoud"""
__email__ = "samymassoud@gmail.com"
__version__ = "0.1.0"


from netbox.plugins import PluginConfig


class MacadressConfig(PluginConfig):
    name = "netbox_macadress"
    verbose_name = "macadress"
    description = "Enrich NetBox MAC addresses with IEEE vendor data from macadress.com."
    author = "Samy Massoud"
    author_email = "samymassoud@gmail.com"
    version = __version__
    base_url = "macadress"
    min_version = "4.5.0"
    max_version = "4.7.99"
    graphql_schema = "graphql.schema"
    default_settings = {
        # Optional. Without a key only vendor names are fetched (1,000 lookups a
        # day per IP); a free key adds block, country and address via batch calls.
        # Falls back to the MACADRESS_API_KEY environment variable.
        "api_key": "",
        "base_url": "https://api.macadress.com",
        "timeout": 10,
        # Minutes between scheduled sync runs (read when the worker starts).
        "sync_interval": 60,
        # Upper bound on blocks looked up per run; the rest wait for the next run.
        "max_lookups_per_run": 500,
        # Days before a cached vendor is looked up again.
        "refresh_days": 30,
        # Queue a lookup as soon as a MAC address with an unknown vendor is saved.
        "lookup_on_save": True,
    }

    def ready(self):
        super().ready()
        from dcim.tables import MACAddressTable
        from utilities.tables import register_table_column

        from . import jobs, signals  # noqa: F401 (registers the system job and signal handlers)
        from .tables import VendorColumn

        register_table_column(VendorColumn(), "macadress_vendor", MACAddressTable)


config = MacadressConfig
