
"""
define a custom NeXus file writer base for uascan raw data files
"""

# TODO: needs a newFile function, similar to instrument.framework.callbacks.newSpecFile()

__all__ = [
    # "NXWriterAD", 
    "NXWriterUascan",
    ]

# from ..session_logs import logger
from instrument.session_logs import logger
logger.info(__file__)

from .nxwriter_base import NXWriterAps

import os


class NXWriterAD(NXWriterAps):
    """
    writes NeXus data file from USAXS instrument SAXS & WAXS area detector scans
    """

    def getResourceFile(self, resource_id):
        """
        full path to the resource file specified by uid ``resource_id``

        override in subclass as needed
        """
        # logger.debug(self.__class__.__name__)
        fname = super().getResourceFile(resource_id)
        # logger.debug("before: %s", fname)
        fname = os.path.abspath(fname)
        key = "/mnt/usaxscontrol/USAXS_data/"
        revision = "/share1/USAXS_data/"
        if fname.startswith(key):
            fname = revision + fname[len(key):]
        # logger.debug("after: %s", fname)
        return fname


class NXWriterUascan(NXWriterAps):
    """
    write raw uascan data to a NeXus/HDF5 file, no specific application definition

    Structure of the NeXus/HDF5 file

    The HDF5 files are written according to the NeXus structure, 
    using only NeXus base classes.  Here is a tree view of
    the structure, edited from an example uascan run::

        entry:NXentry
            duration:NX_FLOAT64[] = [ ... ]
            end_time:NX_CHAR = 2020-06-10T13:55:39.559547
            entry_identifier:NX_CHAR = 78b4801c-1db1-4674-b894-03c4ef4d12a5
            program_name:NX_CHAR = bluesky
            run_cycle --> /entry/instrument/bluesky_streams/baseline/aps_aps_cycle/value_start
            start_time:NX_CHAR = 2020-06-10T13:50:50.239672
            title --> /entry/instrument/bluesky_streams/baseline/user_data_sample_title/value_start
            contact:NXuser
            role:NX_CHAR = contact
            # links to data in /entry/instrument/bluesky_streams/baseline/*/value_start
            data:NXdata
            EPOCH --> /entry/instrument/bluesky_streams/primary/upd_autorange_controls_reqrange/time
            # links to each signal in the primary stream
            I00_autorange_controls_gain --> /entry/instrument/bluesky_streams/primary/I00_autorange_controls_gain/value
            # ...
            instrument:NXinstrument
            bluesky_metadata:NXnote
                # each key in the ``start`` document
                # structured data encoded here as YAML
                EPICS_CA_MAX_ARRAY_BYTES:NX_CHAR = b'1280000'
                ay0:NX_FLOAT64[] = [ ... ]
                # ...
            bluesky_streams:NXnote
                # NXdata groups, one for each monitored signal
                aps_current_monitor:NXnote
                aps_current:NXdata
                    EPOCH:NX_FLOAT64[575] = [ ... ]
                    time:NX_FLOAT64[575] = [ ... ]
                    value:NX_FLOAT64[575] = [ ... ]
                baseline:NXnote
                # NXdata groups, one for each signal in baseline
                aps_aps_cycle:NXdata
                    EPOCH:NX_FLOAT64[2] = [ ... ]
                    time:NX_FLOAT64[2] = [ ... ]
                    value:NX_CHAR[6] = 2020-2
                    value_end:NX_CHAR = b'2020-2'
                    value_start:NX_CHAR = b'2020-2'
                aps_current:NXdata
                    EPOCH:NX_FLOAT64[2] = [ ... ]
                    time:NX_FLOAT64[2] = [ ... ]
                    value:NX_FLOAT64[2] = [ ... ]
                    value_end:NX_FLOAT64[] = [ ... ]
                    value_start:NX_FLOAT64[] = [ ... ]
                # ...
                primary:NXnote
                # NXdata groups, one for each signal hinted in the plan
                I00_autorange_controls_gain:NXdata
                    EPOCH:NX_FLOAT64[300] = [ ... ]     # absolute time stamps
                    time:NX_FLOAT64[300] = [ ... ]      # EPOCH - EPOCH[0]
                    value:NX_FLOAT64[300] = [ ... ]     # values
                # ...
            monochromator:NXmonochromator
                # links to data in /entry/instrument/bluesky_streams/baseline/*/value_start
            slits:NXnote
                guard_slit:NXslit
                # links to data in /entry/instrument/bluesky_streams/baseline/*/value_start
                usaxs_slit:NXslit
                # links to data in /entry/instrument/bluesky_streams/baseline/*/value_start
            source:NXsource
                energy:NX_INT64[] = [ ... ]
                name:NX_CHAR = Advanced Photon Source
                probe:NX_CHAR = x-ray
                type:NX_CHAR = Synchrotron X-ray Source
                # links to data in /entry/instrument/bluesky_streams/baseline/*/value_start
            undulator:NXinsertion_device
                type:NX_CHAR = undulator
                # links to data in /entry/instrument/bluesky_streams/baseline/*/value_start
            sample:NXsample
            # links to data in /entry/instrument/bluesky_streams/baseline/*/value_start

    """
    # TODO: identify what additional data is needed to collect
    # add RE.md["detectors"] = list : first item is for NXdata @signal attribute
    # add RE.md["positioners"] = list : entire list is for NXdata @axes attribute

    instrument_name = 'APS 9-ID-C USAXS'
    nxdata_signal = "PD_USAXS"
    nxdata_signal_axes = ["a_stage_r",]
    supported_plans = ("uascan", )

    # convention: methods written in alphabetical order

    def get_sample_title(self):
        """
        return the title for this sample
        """
        return self.get_stream_link("user_data_sample_title")

    def make_file_name(self):
        """
        this is the place to decide how to name data files
        """
        return super().make_file_name()     # default technique

    def start(self, doc):
        "ensure we only collect data for plans we are prepared to handle"
        if doc.get("plan_name") in self.supported_plans:
            # pay attention to this run of documents
            super().start(doc)
            self.scanning = True
        else:
            self.scanning = False

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
