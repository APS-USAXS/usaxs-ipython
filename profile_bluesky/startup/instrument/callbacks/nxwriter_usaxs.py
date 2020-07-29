
"""
define a custom NeXus file writer base for uascan raw data files
"""

# TODO: needs a newFile function, similar to instrument.framework.callbacks.newSpecFile()

__all__ = [
    # "NXWriterFlyScan",    # not yet tested
    "NXWriterUascan",
    # "NXWriterSaxsWaxs",    # not yet tested
    ]

from ..session_logs import logger
logger.info(__file__)

from apstools.filewriters import NXWriterAPS
import os


class OurCustomNXWriterBase(NXWriterAPS):
    """
    customize the NXWriter for this instrument

    Structure of the NeXus/HDF5 file

    The HDF5 files are written according to the NeXus structure,
    using only NeXus base classes.  Here is a tree view of
    the structure, edited from an example uascan run::

        entry:NXentry
            # constants and links into bluesky subdirectories
            instrument:NXinstrument
                bluesky_metadata:NXnote
                    # each key in the ``start`` document
                    # structured data encoded here as YAML
                bluesky_streams:NXnote
                    # NXdata groups, one for each monitored signal
                monochromator:NXmonochromator
                    # links to baseline start values
                slits:NXnote
                    guard_slit:NXslit
                        # links to baseline start values
                    usaxs_slit:NXslit
                        # links to baseline start values
                source:NXsource
                    # constants and links to baseline start values
                undulator:NXinsertion_device
                    # constants and links to baseline start values
            sample:NXsample
                # links to metadata and baseline start values
    """

    instrument_name = 'APS 9-ID-C USAXS'
    supported_plans = ("name", "the", "supported", "plans")
    file_extension = "h5"       # no dot
    config_version = "1.0"

    def write_entry(self):
        import apstools
        nxentry = super().write_entry()     # default technique

        nxentry["program_name"].attrs["config_version"] = self.config_version
        nxentry["SPEC_data_file"] = self.get_stream_link("user_data_spec_file")
        nxentry["sample/thickness"] = self.get_stream_link("user_data_sample_thickness")
        nxentry["sample/name"] = self.get_sample_title()
        self.root.attrs["creator_version"] = apstools.__version__

    def get_sample_title(self):
        """
        return the title for this sample
        """
        return self.get_stream_link("user_data_sample_title")

    # 2020-07-29, prj - removed on request of jil
    # def make_file_name(self):
    #     """
    #     this is the place to decide how to name data files

    #     insert the plan name after the scan number
    #     """
    #     path, fname = os.path.split(super().make_file_name())     # default technique
    #     parts = fname.split("-")
    #     parts.insert(3, self.plan_name)
    #     fname = "-".join(parts)
    #     return os.path.join(path, fname)

    def start(self, doc):
        "ensure we only collect data for plans we are prepared to handle"
        if doc.get("plan_name") in self.supported_plans:
            # pay attention to this run of documents
            super().start(doc)
            self.scanning = True
        else:
            self.scanning = False

    def writer(self):
        "write the data if this plan is supported"
        plan = self.metadata.get("plan_name")
        if plan not in self.supported_plans:
            return

        super().writer()


class NXWriterFlyScan(OurCustomNXWriterBase):

    supported_plans = ("Flyscan", )

    def write_streams(self, parent):
        "write all bluesky document streams in this run"
        bluesky = super().write_streams(parent)

        if 'primary' not in bluesky and 'mca' in bluesky:
            # link the two
            bluesky['primary'] = bluesky['mca']

        return bluesky


class NXWriterSaxsWaxs(OurCustomNXWriterBase):
    """
    writes NeXus data file from USAXS instrument SAXS & WAXS area detector scans
    """

    supported_plans = ("SAXS", "WAXS",)

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


class NXWriterUascan(OurCustomNXWriterBase):
    """
    write raw uascan data to a NeXus/HDF5 file, no specific application definition
    """
    # TODO: identify what additional data is needed to collect
    # add RE.md["detectors"] = list : first item is for NXdata @signal attribute
    # add RE.md["positioners"] = list : entire list is for NXdata @axes attribute

    nxdata_signal = "PD_USAXS"
    nxdata_signal_axes = ["a_stage_r",]
    supported_plans = ("uascan", )

    # convention: methods written in alphabetical order

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
