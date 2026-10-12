"""
Choice sets for NetBox macadress.
"""

from django.utils.translation import gettext_lazy as _
from utilities.choices import ChoiceSet


class VendorStatusChoices(ChoiceSet):
    REGISTERED = "registered"
    UNREGISTERED = "unregistered"

    CHOICES = (
        (REGISTERED, _("Registered"), "green"),
        (UNREGISTERED, _("Not registered"), "gray"),
    )


class VendorSourceChoices(ChoiceSet):
    KEYLESS = "keyless"
    API_KEY = "api_key"

    CHOICES = (
        (KEYLESS, _("Keyless"), "gray"),
        (API_KEY, _("API key"), "blue"),
    )
