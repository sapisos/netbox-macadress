"""
Search indexes for NetBox macadress.
"""

from netbox.search import SearchIndex

from .models import MACVendor


class MACVendorIndex(SearchIndex):
    model = MACVendor
    fields = (
        ("organization", 100),
        ("prefix", 110),
        ("address", 500),
    )
    display_attrs = ("status", "country")


indexes = (MACVendorIndex,)
