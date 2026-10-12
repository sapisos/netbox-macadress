"""
Views for NetBox macadress.

Vendor entries are written by the lookup job only, so the UI offers viewing,
deleting (which forces a fresh lookup on the next run) and a run-now action.
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from netbox.object_actions import BulkDelete, BulkExport, DeleteObject
from netbox.views import generic
from utilities.views import register_model_view

from . import filtersets, forms, models, tables
from .jobs import VendorLookupJob
from .lookup import api_key


@register_model_view(models.MACVendor)
class MACVendorView(generic.ObjectView):
    queryset = models.MACVendor.objects.all()
    actions = (DeleteObject,)

    def get_extra_context(self, request, instance):
        return {"keyed": bool(api_key())}


@register_model_view(models.MACVendor, name="list", path="", detail=False)
class MACVendorListView(generic.ObjectListView):
    queryset = models.MACVendor.objects.all()
    table = tables.MACVendorTable
    filterset = filtersets.MACVendorFilterSet
    filterset_form = forms.MACVendorFilterForm
    actions = (BulkExport, BulkDelete)


@register_model_view(models.MACVendor, name="delete")
class MACVendorDeleteView(generic.ObjectDeleteView):
    queryset = models.MACVendor.objects.all()


@register_model_view(models.MACVendor, name="bulk_delete", path="delete", detail=False)
class MACVendorBulkDeleteView(generic.BulkDeleteView):
    queryset = models.MACVendor.objects.all()
    filterset = filtersets.MACVendorFilterSet
    table = tables.MACVendorTable


@register_model_view(models.MACVendor, name="sync", path="sync", detail=False)
class MACVendorSyncView(View):
    """Queue a lookup run now instead of waiting for the scheduled one."""

    def post(self, request):
        if not request.user.has_perm("netbox_macadress.add_macvendor"):
            raise PermissionDenied
        job = VendorLookupJob.enqueue_once(user=request.user)
        messages.info(request, _("Vendor lookup queued."))
        return redirect("core:job", pk=job.pk)
