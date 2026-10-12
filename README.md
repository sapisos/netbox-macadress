# NetBox macadress

A [NetBox](https://github.com/netbox-community/netbox) plugin that adds the IEEE vendor to every MAC
address in NetBox, using the [macadress.com](https://macadress.com) API. It works with no API key
(vendor name only). A free key adds the block type, country and registered address.

![Vendor panel on a MAC address](https://raw.githubusercontent.com/sapisos/netbox-macadress/main/docs/images/mac-address.png)

## Features

- **Vendor panel** on MAC address, device interface and VM interface pages
- **Vendor column** for the MAC address table (enable it under *Configure Table*), included in exports
- **Background sync** that looks up new MAC addresses and refreshes vendors after 30 days. A lookup is
  also queued as soon as a MAC address with an unknown vendor is saved, and from the **Look up now**
  button.
- **One lookup per block**: addresses are cached per IEEE block (OUI, MA-M or MA-S), so a few hundred
  lookups usually cover thousands of devices. Blocks that IEEE splits between several vendors are
  cached at the right width, so devices are never labeled with a neighbor's vendor.
- **No lookup** for locally administered (often randomized) or multicast addresses
- **MAC Vendors** list with filtering, global search, REST API and GraphQL

![Vendor column on the MAC address list](https://raw.githubusercontent.com/sapisos/netbox-macadress/main/docs/images/mac-address-list.png)

![MAC Vendors list](https://raw.githubusercontent.com/sapisos/netbox-macadress/main/docs/images/vendor-list.png)

## Compatibility

| NetBox    | Plugin |
|-----------|--------|
| 4.5 - 4.7 | 0.1.x  |

See [COMPATIBILITY.md](COMPATIBILITY.md). Requires Python 3.12+.

## Dependencies

- [`macadress`](https://pypi.org/project/macadress/), the official macadress.com Python client
  (installed automatically)
- A running NetBox background worker (`manage.py rqworker`), which runs the lookups
- Outbound HTTPS to `api.macadress.com`. NetBox's `HTTP_PROXIES` / `PROXY_ROUTERS` settings are
  honored.

## Installation

```bash
source /opt/netbox/venv/bin/activate
pip install netbox-macadress
```

Add it to `local_requirements.txt` so NetBox upgrades keep it, then enable it in `configuration.py`:

```python
PLUGINS = ["netbox_macadress"]
```

Apply the migration and restart NetBox and its worker:

```bash
cd /opt/netbox/netbox
python manage.py migrate
sudo systemctl restart netbox netbox-rq
```

For netbox-docker, add `netbox-macadress` to `plugin_requirements.txt` and see
[Using NetBox Plugins](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins).

## Configuration

Every setting is optional:

```python
PLUGINS_CONFIG = {
    "netbox_macadress": {
        "api_key": "",              # or set MACADRESS_API_KEY in the environment
        "sync_interval": 60,        # minutes between scheduled syncs
        "max_lookups_per_run": 500, # the rest wait for the next run
        "refresh_days": 30,         # age at which a cached vendor is looked up again
        "lookup_on_save": True,     # queue a lookup when a MAC with an unknown vendor is saved
        "timeout": 10,
        "base_url": "https://api.macadress.com",
    },
}
```

| Mode | Data | Limits |
|------|------|--------|
| No key | Vendor name | 1,000 lookups a day per IP, 60 a minute |
| [Free key](https://macadress.com/signup) | Vendor, block type, country, address | 100 addresses per batch call, 1,000 free a day, then your [plan](https://macadress.com/pricing) |

When a key is added later, entries fetched without one are refreshed on the next sync.

## REST API and GraphQL

- `GET /api/plugins/macadress/vendors/`, filterable by `mac_address`, `prefix`, `organization`,
  `status`, `country`, `source` and `q`. Delete an entry to force it to be looked up again.
- GraphQL: `mac_vendor(id: ...)` and `mac_vendor_list`

## Support

- Issues: <https://github.com/sapisos/netbox-macadress/issues>
- Maintainer: Samy Massoud, [macadress.com](https://macadress.com)

## License

Apache-2.0, see [LICENSE](LICENSE).
