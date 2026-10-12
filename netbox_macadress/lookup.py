"""
Vendor lookups against the macadress.com API, and the cache sync that fills
the MACVendor table from the MAC addresses recorded in NetBox.

Without an API key the plugin uses the keyless name-only endpoint, one address
per request at most 60 a minute. With a key it uses the batch endpoint, 100
addresses per request, which also returns the block, country and address.
"""

import logging
import os
import time
from contextlib import contextmanager
from datetime import timedelta
from urllib.parse import urlparse

import httpx
import macadress
from django.db import transaction
from django.utils import timezone
from netbox.plugins import get_plugin_config
from utilities.proxy import resolve_proxies

from .choices import VendorSourceChoices, VendorStatusChoices
from .utils import candidate_keys, key_for_result, local_status, lookup_key, normalize

PLUGIN = "netbox_macadress"

# The keyless endpoint allows 60 requests a minute per IP.
KEYLESS_INTERVAL = 1.05
BATCH_INTERVAL = 1.0
# A rate limit with a longer Retry-After than this ends the run instead of waiting.
MAX_RETRY_WAIT = 120

# Log messages are pre-formatted: a NetBox job log stores the message without its arguments.
logger = logging.getLogger(PLUGIN)


class LookupAborted(Exception):
    """The run cannot continue (bad key, quota spent, API unreachable)."""


def setting(name):
    return get_plugin_config(PLUGIN, name)


def api_key():
    return (setting("api_key") or os.environ.get("MACADRESS_API_KEY", "")).strip()


@contextmanager
def open_client():
    """A macadress Client honoring the plugin settings and NetBox's proxy routing."""
    from . import __version__

    base_url = setting("base_url")
    timeout = float(setting("timeout"))
    scheme = urlparse(base_url).scheme or "https"
    proxies = resolve_proxies(url=base_url, protocol=scheme) or {}
    with httpx.Client(timeout=timeout, proxy=proxies.get(scheme)) as http:
        yield macadress.Client(
            api_key(),
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": f"netbox-macadress/{__version__} macadress-python/{macadress.__version__}"},
            http_client=http,
        )


def _sleep(seconds):
    time.sleep(seconds)


def _with_retry(call):
    """Run `call`, waiting out one short rate limit. Ends the run on anything fatal."""
    for attempt in range(2):
        try:
            return call()
        except macadress.QuotaExceededError as exc:
            raise LookupAborted("API quota for this billing cycle is used up.") from exc
        except macadress.RateLimitError as exc:
            wait = exc.retry_after or 0
            if attempt or wait > MAX_RETRY_WAIT:
                raise LookupAborted(f"Rate limited by the API (retry after {wait}s).") from exc
            _sleep(max(wait, 1))
        except macadress.AuthenticationError as exc:
            raise LookupAborted("The configured macadress.com API key was rejected.") from exc
        except macadress.TransportError as exc:
            raise LookupAborted(f"Could not reach the macadress.com API: {exc}") from exc


def _store(key, *, status, source, organization="", block_type="", country="", address=""):
    from .models import MACVendor

    values = {
        "prefix_length": len(key) * 4,
        "status": status,
        "organization": (organization or "")[:255],
        "block_type": block_type or "",
        "country": (country or "")[:2],
        "address": (address or "")[:500],
        "source": source,
        "last_checked": timezone.now(),
    }
    with transaction.atomic():
        MACVendor.objects.update_or_create(prefix=key, defaults=values)
        if source == VendorSourceChoices.API_KEY:
            # Keyless entries nested inside this block are superseded by it.
            MACVendor.objects.filter(
                prefix__startswith=key, source=VendorSourceChoices.KEYLESS, prefix_length__gt=values["prefix_length"]
            ).delete()


def _is_fresh(entry, keyed, cutoff):
    if entry.last_checked < cutoff:
        return False
    # A key unlocks more detail, so keyless entries are refreshed once one is set.
    return not (keyed and entry.source == VendorSourceChoices.KEYLESS)


def pending_lookups(keyed):
    """
    Map each cache key that needs a (re)lookup to one MAC address inside it,
    for every MAC address recorded in NetBox.
    """
    from dcim.models import MACAddress

    from .models import MACVendor

    cutoff = timezone.now() - timedelta(days=int(setting("refresh_days")))
    cache = {entry.prefix: entry for entry in MACVendor.objects.all()}
    pending = {}
    for value in MACAddress.objects.values_list("mac_address", flat=True).distinct().iterator():
        hex12 = normalize(value)
        if hex12 is None or local_status(hex12):
            continue
        entry = next((cache[k] for k in candidate_keys(hex12) if k in cache), None)
        if entry is not None and _is_fresh(entry, keyed, cutoff):
            continue
        key = entry.prefix if entry is not None else lookup_key(hex12)
        pending.setdefault(key, hex12)
    return pending


def _lookup_keyless(client, targets, log):
    done = 0
    for i, hex12 in enumerate(targets):
        if i:
            _sleep(KEYLESS_INTERVAL)
        try:
            name = _with_retry(lambda h=hex12: client.vendor(h))
        except macadress.InvalidMACError:
            log.warning(f"API rejected {hex12} as invalid, skipped")
            continue
        except macadress.APIError as exc:
            log.warning(f"Lookup of {hex12} failed: {exc}")
            continue
        key = key_for_result(hex12, None, name)
        status = VendorStatusChoices.REGISTERED if name else VendorStatusChoices.UNREGISTERED
        _store(key, status=status, source=VendorSourceChoices.KEYLESS, organization=name)
        done += 1
    return done


def _lookup_batch(client, targets, log):
    done = 0
    size = macadress.MAX_BATCH_SIZE
    for start in range(0, len(targets), size):
        if start:
            _sleep(BATCH_INTERVAL)
        chunk = targets[start : start + size]
        try:
            items = _with_retry(lambda c=chunk: client.batch(c))
        except macadress.APIError as exc:
            log.warning(f"Batch lookup failed: {exc}")
            continue
        for hex12, item in zip(chunk, items, strict=False):
            if item.failed:
                log.warning(f"Lookup of {hex12} failed: {item.error}")
                continue
            organization = item.organization or ""
            key = key_for_result(hex12, item.prefix_length, organization)
            _store(
                key,
                status=VendorStatusChoices.REGISTERED if item.registered else VendorStatusChoices.UNREGISTERED,
                source=VendorSourceChoices.API_KEY,
                organization=organization,
                block_type=str(item.block_type or ""),
                country=item.country or "",
                address=item.vendor_address or "",
            )
            done += 1
    return done


def sync(log=None, limit=None):
    """
    Look up every MAC address block in NetBox that has no fresh cache entry.
    Returns (looked_up, still_pending). Raises LookupAborted when the API
    refuses to continue; whatever was stored before that is kept.
    """
    log = log or logger
    keyed = bool(api_key())
    pending = pending_lookups(keyed)
    limit = int(setting("max_lookups_per_run") if limit is None else limit)
    targets = list(pending.values())[:limit] if limit > 0 else list(pending.values())
    if not targets:
        log.info("All MAC address vendors are up to date")
        return 0, 0

    mode = "batch (API key)" if keyed else "keyless"
    log.info(f"Looking up {len(targets)} of {len(pending)} pending vendor blocks, {mode}")
    with open_client() as client:
        if keyed:
            done = _lookup_batch(client, targets, log)
        else:
            done = _lookup_keyless(client, targets, log)
    log.info(f"Stored {done} vendor blocks, {len(pending) - done} left for later runs")
    return done, len(pending) - done
