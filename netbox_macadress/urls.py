"""
URL patterns for NetBox macadress.
"""

from django.urls import include, path
from utilities.urls import get_model_urls

from . import views  # noqa: F401 (registers the model views)

urlpatterns = (
    path("vendors/", include(get_model_urls("netbox_macadress", "macvendor", detail=False))),
    path("vendors/<int:pk>/", include(get_model_urls("netbox_macadress", "macvendor"))),
)
