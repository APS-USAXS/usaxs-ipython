
"""
define a custom NeXus file writer base for uascan raw data files
"""

__all__ = ["NXWriterUascan",]

from ..session_logs import logger
logger.info(__file__)

# TODO: generalize NXWriterBase for any bluesky run
# TODO: let caller control the output file name

from .nxwriter_base import NXWriterBase


class NXWriterUascan(NXWriterBase):
    """
    write raw uascan data to a NeXus/HDF5 file, no specific application definition
    """
    # TODO: identify what additional data is needed to collect
    # Need to know from documents what data is signal and axes.

    supported_plans = ("uascan", )
    nxdata_signal = "PD_USAXS"
    nxdata_signal_axes = ["a_stage_r",]

    # positioners have these strings in their PV names
    positioner_ids = ":aero: :m58:".split()

    def start(self, doc):
        "ensure we only collect data for plans we are prepared to handle"
        if doc.get("plan_name") in self.supported_plans:
            # pay attention to this run of documents
            super().start(doc)

    def writer(self):
        plan = self.metadata.get("plan_name")
        if plan not in self.supported_plans:
            return

        super().writer()

    def write_root(self, filename):
        """
        root of the HDF5 file
        """
        self.root.attrs[u'instrument'] = u'APS 9-ID-C USAXS'
        super().write_root(filename)
