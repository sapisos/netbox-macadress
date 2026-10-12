"""
API URL patterns for NetBox macadress.
"""

from netbox.api.routers import NetBoxRouter

from .views import MACVendorViewSet

app_name = "netbox_macadress"

router = NetBoxRouter()
router.register("vendors", MACVendorViewSet)

urlpatterns = router.urls
