"""
MAC address helpers for NetBox macadress.

Everything here works on a MAC address normalized to 12 uppercase hex digits,
and has no database or network access.
"""

import re

from .constants import MA_M_BITS, MA_S_BITS, OUI_BITS, REGISTRATION_AUTHORITY, SHARED_OUIS

_NON_HEX = re.compile(r"[^0-9A-Fa-f]")

# Cache key lengths, in hex digits, from most to least specific.
KEY_LENGTHS = (MA_S_BITS // 4, MA_M_BITS // 4, OUI_BITS // 4)


def normalize(mac):
    """
    Return `mac` as 12 uppercase hex digits, or None if it is not a 48-bit MAC.
    Accepts any grouping (`:`, `-`, `.`, space) and netaddr EUI objects.
    """
    if mac is None:
        return None
    digits = _NON_HEX.sub("", str(mac)).upper()
    return digits if len(digits) == 12 else None


def is_multicast(hex12):
    """True for a group address (I/G bit set), which carries no vendor."""
    return bool(int(hex12[0:2], 16) & 0x01)


def is_locally_administered(hex12):
    """True when the U/L bit is set: usually a randomized or virtual address."""
    return bool(int(hex12[0:2], 16) & 0x02)


def local_status(hex12):
    """
    Classify an address that needs no lookup. Returns "multicast",
    "locally_administered", or None for a normal universally administered
    unicast address.
    """
    if is_multicast(hex12):
        return "multicast"
    if is_locally_administered(hex12):
        return "locally_administered"
    return None


def candidate_keys(hex12):
    """Every cache key that could hold this address's vendor, most specific first."""
    return [hex12[:n] for n in KEY_LENGTHS]


def is_shared_oui(hex12):
    """True when the address's OUI is subdivided into MA-M / MA-S blocks."""
    return hex12[:6] in SHARED_OUIS


def lookup_key(hex12):
    """
    The cache key a lookup for this address is stored under when the block
    width is not known (no API key): the OUI, or the 36-bit prefix inside an
    OUI that IEEE subdivides, where the OUI alone does not identify a vendor.
    """
    return hex12[: MA_S_BITS // 4] if is_shared_oui(hex12) else hex12[: OUI_BITS // 4]


def key_for_result(hex12, prefix_length, organization):
    """
    The cache key for a lookup result. `prefix_length` is the matched block
    width in bits when the API reported it, else None.

    A 24-bit answer inside a subdivided OUI only means no MA-M / MA-S block
    covers this address, so it is narrowed to 36 bits rather than applied to
    the whole OUI.
    """
    shared = is_shared_oui(hex12) or organization == REGISTRATION_AUTHORITY
    if prefix_length in (MA_M_BITS, MA_S_BITS):
        return hex12[: prefix_length // 4]
    if shared:
        return hex12[: MA_S_BITS // 4]
    return hex12[: OUI_BITS // 4]


def format_prefix(prefix):
    """Render a cache key as colon-grouped hex with its length, e.g. 70:B3:D5:F/28."""
    pairs = [prefix[i : i + 2] for i in range(0, len(prefix), 2)]
    return f"{':'.join(pairs)}/{len(prefix) * 4}"


def format_mac(hex12):
    """Render 12 hex digits as AA:BB:CC:DD:EE:FF."""
    return ":".join(hex12[i : i + 2] for i in range(0, 12, 2))
