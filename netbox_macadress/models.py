"""
Models for NetBox macadress.
"""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel
from utilities.querysets import RestrictedQuerySet

from .choices import VendorSourceChoices, VendorStatusChoices
from .utils import candidate_keys, format_prefix, normalize


class MACVendorQuerySet(RestrictedQuerySet):
    def for_mac(self, mac):
        """
        The cached vendor entry covering `mac` (any format), or None. The most
        specific block wins, so an MA-S entry beats its enclosing OUI.
        """
        hex12 = normalize(mac)
        if hex12 is None:
            return None
        return self.filter(prefix__in=candidate_keys(hex12)).order_by("-prefix_length").first()


class MACVendor(NetBoxModel):
    """
    One IEEE block (OUI, MA-M or MA-S) and the vendor registered to it, as last
    reported by macadress.com. Rows are created and refreshed by the lookup job.
    """

    prefix = models.CharField(
        verbose_name=_("prefix"),
        max_length=9,
        unique=True,
        help_text=_("Leading hex digits of the block, without separators"),
    )
    prefix_length = models.PositiveSmallIntegerField(
        verbose_name=_("prefix length"),
        help_text=_("Block size in bits: 24 (OUI), 28 (MA-M) or 36 (MA-S)"),
    )
    status = models.CharField(
        verbose_name=_("status"),
        max_length=20,
        choices=VendorStatusChoices,
    )
    organization = models.CharField(
        verbose_name=_("organization"),
        max_length=255,
        blank=True,
    )
    block_type = models.CharField(
        verbose_name=_("block type"),
        max_length=10,
        blank=True,
    )
    country = models.CharField(
        verbose_name=_("country"),
        max_length=2,
        blank=True,
    )
    address = models.CharField(
        verbose_name=_("address"),
        max_length=500,
        blank=True,
    )
    source = models.CharField(
        verbose_name=_("source"),
        max_length=20,
        choices=VendorSourceChoices,
    )
    last_checked = models.DateTimeField(
        verbose_name=_("last checked"),
    )

    objects = MACVendorQuerySet.as_manager()

    class Meta:
        ordering = ("prefix",)
        verbose_name = _("MAC vendor")
        verbose_name_plural = _("MAC vendors")

    def __str__(self):
        return self.prefix_display

    def get_absolute_url(self):
        return reverse("plugins:netbox_macadress:macvendor", args=[self.pk])

    @property
    def prefix_display(self):
        return format_prefix(self.prefix)

    @property
    def mac_prefix(self):
        """The prefix as the start of a colon-separated MAC, e.g. 70:B3:D5:F."""
        return self.prefix_display.split("/")[0]

    def get_status_color(self):
        return VendorStatusChoices.colors.get(self.status)

    def get_source_color(self):
        return VendorSourceChoices.colors.get(self.source)
