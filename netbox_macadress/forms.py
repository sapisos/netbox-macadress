"""
Forms for NetBox macadress.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms.fields import TagFilterField
from utilities.forms.rendering import FieldSet

from .choices import VendorSourceChoices, VendorStatusChoices
from .models import MACVendor


class MACVendorFilterForm(NetBoxModelFilterSetForm):
    model = MACVendor
    fieldsets = (
        FieldSet("q", "filter_id", "tag"),
        FieldSet("mac_address", "status", "country", "source", name=_("Vendor")),
    )
    mac_address = forms.CharField(required=False, label=_("MAC address"))
    status = forms.MultipleChoiceField(choices=VendorStatusChoices, required=False, label=_("Status"))
    country = forms.CharField(required=False, label=_("Country"))
    source = forms.MultipleChoiceField(choices=VendorSourceChoices, required=False, label=_("Source"))
    tag = TagFilterField(model)
