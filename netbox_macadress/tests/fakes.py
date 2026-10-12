"""
A stand-in for macadress.Client, so tests never reach the network.
"""

from contextlib import contextmanager
from types import SimpleNamespace


def batch_item(mac, organization=None, prefix_length=24, block_type="MA-L", country="", address="", error=None):
    return SimpleNamespace(
        input=mac,
        failed=error is not None,
        error=error,
        registered=organization is not None,
        organization=organization,
        prefix_length=prefix_length if organization else None,
        block_type=block_type if organization else None,
        country=country,
        vendor_address=address,
    )


class FakeClient:
    """Answers vendor() from `names` (hex12 -> name or None) and batch() from `items`."""

    def __init__(self, names=None, items=None, errors=None):
        self.names = names or {}
        self.items = items or {}
        self.errors = list(errors or [])
        self.vendor_calls = []
        self.batch_calls = []

    def vendor(self, mac):
        self.vendor_calls.append(mac)
        if self.errors:
            raise self.errors.pop(0)
        return self.names.get(mac)

    def batch(self, macs):
        self.batch_calls.append(list(macs))
        if self.errors:
            raise self.errors.pop(0)
        return [self.items.get(mac) or batch_item(mac) for mac in macs]

    @contextmanager
    def opener(self):
        yield self
