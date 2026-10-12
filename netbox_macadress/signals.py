"""
Signal handlers for NetBox macadress.
"""

from dcim.models import MACAddress
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from netbox.plugins import get_plugin_config

from .models import MACVendor
from .utils import local_status, normalize


@receiver(post_save, sender=MACAddress, dispatch_uid="netbox_macadress_lookup_on_save")
def queue_vendor_lookup(sender, instance, **kwargs):
    """
    Queue a lookup when a MAC address with no cached vendor is saved. One job
    serves any number of saves (a bulk import queues a single run).
    """
    if not get_plugin_config("netbox_macadress", "lookup_on_save"):
        return
    hex12 = normalize(instance.mac_address)
    if hex12 is None or local_status(hex12) or MACVendor.objects.for_mac(hex12) is not None:
        return

    from .jobs import VendorLookupJob

    transaction.on_commit(VendorLookupJob.enqueue_once)
