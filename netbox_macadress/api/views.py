"""
API viewsets for NetBox macadress.
"""

from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
from ..models import MACVendor
from .serializers import MACVendorSerializer


class MACVendorViewSet(NetBoxModelViewSet):
    """Vendor entries are written by the lookup job; the API reads and deletes them."""

    queryset = MACVendor.objects.prefetch_related("tags")
    serializer_class = MACVendorSerializer
    filterset_class = filtersets.MACVendorFilterSet
    http_method_names = ["get", "delete", "head", "options"]
