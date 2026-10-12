"""
Background jobs for NetBox macadress.
"""

from core.exceptions import JobFailed
from netbox.jobs import JobRunner, system_job
from netbox.plugins import get_plugin_config

from .lookup import LookupAborted, sync


def _run(job):
    try:
        sync(log=job.logger)
    except LookupAborted as exc:
        job.logger.warning(str(exc))
        raise JobFailed(str(exc)) from exc


@system_job(interval=int(get_plugin_config("netbox_macadress", "sync_interval")))
class VendorSyncJob(JobRunner):
    """Scheduled run: picks up new MAC addresses and refreshes stale vendors."""

    class Meta:
        name = "MAC vendor sync"

    def run(self, *args, **kwargs):
        _run(self)


class VendorLookupJob(JobRunner):
    """On-demand run, queued when a MAC address is saved or from the vendor list."""

    class Meta:
        name = "MAC vendor lookup"

    def run(self, *args, **kwargs):
        _run(self)
