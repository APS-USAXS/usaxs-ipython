
"""
define a custom NeXus file writer base for uascan raw data files
"""

__all__ = ["NXWriterUascan",]

from ..session_logs import logger
logger.info(__file__)

# TODO: generalize NXWriterBase for any bluesky run
# TODO: let caller control the output file name

import datetime
import h5py
import numpy as np
import yaml

from .nxwriter_base import NXWriterBase


class NXWriterUascan(NXWriterBase):
    """
    should go into USAXS instrument package
    """
    # TODO: identify what additional data is needed to collect
    # Need to know from documents what data is signal and axes.

    supported_plans = ("uascan", )

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
