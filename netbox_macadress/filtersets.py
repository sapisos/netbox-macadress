"""
Filtersets for NetBox macadress.
"""

import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

from .choices import VendorSourceChoices, VendorStatusChoices
from .models import MACVendor
from .utils import candidate_keys, normalize


class MACVendorFilterSet(NetBoxModelFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=VendorStatusChoices)
    source = django_filters.MultipleChoiceFilter(choices=VendorSourceChoices)
    mac_address = django_filters.CharFilter(method="filter_mac_address", label="MAC address")

    class Meta:
        model = MACVendor
        fields = ("id", "prefix", "prefix_length", "organization", "block_type", "country")

    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        query = Q(organization__icontains=value) | Q(country__iexact=value)
        digits = "".join(c for c in value if c.isalnum()).upper()
        if digits:
            query |= Q(prefix__startswith=digits)
        return queryset.filter(query)

    def filter_mac_address(self, queryset, name, value):
        """The block(s) that could cover this MAC address."""
        hex12 = normalize(value)
        if hex12 is None:
            return queryset.none()
        return queryset.filter(prefix__in=candidate_keys(hex12))
