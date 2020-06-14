
"""
define a custom NeXus file writer base for uascan raw data files
"""

__all__ = ["NXWriterUascan",]

from ..session_logs import logger
logger.info(__file__)

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
    instrument_name = 'APS 9-ID-C USAXS'

    def get_sample_title(self):
        """
        return the title for this sample
        """
        return self.get_stream_link("user_data_sample_title")

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

    def write_slits(self, parent):
        """
        group: /entry/instrument/slits:NXnote/SLIT:NXslit
        """
        group = self.create_NX_group(parent, f"slits:NXnote")
        pre = "guard_slit"
        for pre in "guard_slit usaxs_slit".split():
            slit = self.create_NX_group(group, f"{pre}:NXslit")
            slit["x_gap"] = self.get_stream_link(f"{pre}_h_size")
            slit["y_gap"] = self.get_stream_link(f"{pre}_v_size")
            for key in "x y".split():
                slit[key] = self.get_stream_link(f"{pre}_{key}")
