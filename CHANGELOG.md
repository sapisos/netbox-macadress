# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-12

### Release Summary

Initial (**minor**) release. Looks up the IEEE vendor of every MAC address in NetBox through the
macadress.com API, keyless by default, and shows it on MAC address and interface pages.

### Added

- `MACVendor` cache of IEEE blocks (OUI, MA-M, MA-S) and their registered vendor, with list, detail,
  filtering, global search, REST API (`/api/plugins/macadress/vendors/`) and GraphQL (`mac_vendor`,
  `mac_vendor_list`)
- Scheduled background sync that looks up new MAC addresses and refreshes stale vendors, plus an
  on-demand run when a MAC address is saved or from the **Look up now** button
- Keyless mode (vendor name only) and API key mode (batch lookups with block type, country and
  address)
- Vendor panel on MAC address, device interface and VM interface pages
- Optional **Vendor** column on the MAC address table
