
"""
define a NeXus file writer base for custom NeXus files
"""

__all__ = ["NXWriterBase",]

from ..session_logs import logger
logger.info(__file__)

# TODO: add to apstools if/when this becomes sufficiently general
# TODO: generalize NXWriterBase for any bluesky run
# TODO: let caller control the output file name (move this to superclass)
# TODO: move all USAXS-specific content to module nxwrite_usaxs

import datetime
import h5py
import numpy as np
import yaml

from .file_writer_base import FileWriterCallbackBase


class NXWriterBase(FileWriterCallbackBase):
    """
    """
    # TODO: identify what additional data is needed to collect

    root = None                 # instance of h5py.File
    nxdata_signal = None        # name of dataset for Y axis on plot
    nxdata_signal_axes = None   # name of dataset for X axis on plot

    # positioners have these strings in their PV names
    positioner_ids = []

    def writer(self):
        filename = 'test_raw_usaxs.h5'      # TODO: let caller configure this
        with h5py.File(filename, "w") as self.root:
            self.write_root(filename)

        self.root = None
        logger.info(f"wrote NeXus file: {filename}")

    def h5string(self, text):
        if isinstance(text, (tuple, list)):
            return [self.h5string(t) for t in text]
        text = text or ""
        return text.encode("utf8")

    def add_dataset_attributes(self, ds, v, long_name=None):
        """
        add attributes from v dictionary to dataset ds
        """
        ds.attrs["units"] = self.h5string(v["units"])
        ds.attrs["source"] = self.h5string(v["source"])
        if long_name is not None:
            ds.attrs["long_name"] = self.h5string(long_name)
        if v["dtype"] not in ("string",):
            ds.attrs["precision"] = v["precision"]
            def cautious_set(key):
                if v[key] is not None:
                    ds.attrs[key] = v[key]
            cautious_set("lower_ctrl_limit")
            cautious_set("upper_ctrl_limit")

    def assign_signal_type(self):
        """
        decide if a signal in the primary stream is a detector or a positioner
        """
        primary = self.root["/entry/instrument/bluesky_streams/primary"]

        def is_positioner(item):
            source = item["value"].attrs["source"].decode()
            return max([source.find(s) for s in self.positioner_ids]) >= 0

        xref = {True: "positioner", False: "detector"}
        for v in primary.values():
            signal_type = xref[is_positioner(v)]
            v.attrs["signal_type"] = signal_type            # group
            v["value"].attrs["signal_type"] = signal_type   # dataset

    def create_NX_group(self, parent, specification):
        """
        create an h5 group with named NeXus class (specification)
        """
        local_address, nx_class = specification.split(":")
        if not nx_class.startswith("NX"):
            raise ValueError(f"NeXus base class must start with 'NX', received {nx_class}")
        group = parent.create_group(local_address)
        group.attrs["NX_class"] = nx_class
        group.attrs["target"] = group.name      # for use as NeXus link
        return group

    def get_stream_link(self, signal, stream=None, ref=None):
        """
        return the h5 object for ``signal``

        DEFAULTS

        ``stream`` : ``baseline``
        ``key`` : ``value_start``
        """
        stream = stream or "baseline"
        ref = ref or "value_start"
        h5_addr = f"/entry/instrument/bluesky_streams/{stream}/{signal}/{ref}"
        # return the h5 object, to make a link
        return self.root[h5_addr]
    
    def write_data(self, parent):
        """
        group: /entry/data:NXdata
        """
        nxdata = self.create_NX_group(parent, "data:NXdata")
        if self.nxdata_signal is not None:
            # TODO: check that these actually exist
            nxdata.attrs["signal"] = self.nxdata_signal
            if self.nxdata_signal_axes is not None:
                nxdata.attrs["axes"] = self.nxdata_signal_axes
        primary = parent["instrument/bluesky_streams/primary"]
        for k in primary.keys():
            nxdata[k] = primary[k+"/value"]
        
        # pick the timestamps from one of the datasets (the last one)
        nxdata["EPOCH"] = primary[k+"/time"]
        
        return nxdata

    def write_detector(self, parent):
        """
        group: /entry/instrument/detectors:NXnote/DETECTOR:NXdetector
        """
        primary = parent["/entry/instrument/bluesky_streams/primary"]
        # TODO: only proceed if len(detectors)>0

        group = self.create_NX_group(parent, f"detectors:NXnote")
        for k, v in primary.items():
            if v.attrs.get("signal_type") != "detector":
                continue
            nxdetector = self.create_NX_group(group, f"{k}:NXdetector")
            nxdetector["data"] = v

        return nxdetector

    def write_entry(self):
        """
        group: /entry/data:NXentry
        """
        nxentry = self.create_NX_group(self.root, self.root.attrs["default"]+":NXentry")

        ds = nxentry.create_dataset("entry_identifier", data=self.uid)
        ds.attrs["long_name"] = "bluesky run uid"

        nxentry.create_dataset(
            "start_time", 
            data=datetime.datetime.fromtimestamp(self.start_time).isoformat())
        nxentry.create_dataset(
            "end_time", 
            data=datetime.datetime.fromtimestamp(self.stop_time).isoformat())
        ds = nxentry.create_dataset("duration", data=self.stop_time-self.start_time)
        ds.attrs["units"] = "s"

        nxentry.create_dataset("program_name", data="bluesky")

        self.write_instrument(nxentry)   # also writes streams and metadata
        nxdata = self.write_data(nxentry)
        self.write_sample(nxentry)
        self.write_user(nxentry)

        # apply links
        nxentry.attrs["default"] = nxdata.name.split("/")[-1]
        nxentry["run_cycle"] = self.get_stream_link("aps_aps_cycle")
        
        # TODO: generalize: this is specific to USAXS
        nxentry["title"] = self.get_stream_link("user_data_sample_title")

        return nxentry

    def write_instrument(self, parent):
        """
        group: /entry/instrument:NXinstrument
        """
        nxinstrument = self.create_NX_group(parent, "instrument:NXinstrument")
        self.write_metadata(nxinstrument)
        self.write_streams(nxinstrument)
        self.assign_signal_type()

        self.write_slits(nxinstrument)
        self.write_detector(nxinstrument)
        self.write_undulator(nxinstrument)
        self.write_monochromator(nxinstrument)
        self.write_positioner(nxinstrument)
        self.write_source(nxinstrument)
        return nxinstrument

    def write_metadata(self, parent):
        """
        group: /entry/instrument/bluesky_metadata:NXnote
        
        metadata from the bluesky start document
        """
        bluesky = self.create_NX_group(parent, "bluesky_metadata:NXnote")
        for k, v in self.metadata.items():
            if isinstance(v, (dict, tuple, list)):
                # fallback technique: save complicated structures as YAML text
                v = yaml.dump(v)
            if isinstance(v, str):
                v = self.h5string(v)
            bluesky.create_dataset(k, data=v)

        return bluesky

    def write_monochromator(self, parent):
        """
        group: /entry/instrument/monochromator:NXmonochromator
        """
        nxmonochromator = self.create_NX_group(parent, "monochromator:NXmonochromator")

        # TODO: generalize
        nxmonochromator.create_dataset("type", data="undulator")

        keys = """wavelength energy theta y_offset mode""".split()
        pre = "monochromator_dcm"
        for key in keys:
            nxmonochromator[key] = self.get_stream_link(f"{pre}_{key}")
        
        key = "feedback_on"
        pre = "monochromator"
        nxmonochromator[key] = self.get_stream_link(f"{pre}_{key}")

        return nxmonochromator

    def write_positioner(self, parent):
        """
        group: /entry/instrument/positioners:NXnote/POSITIONER:NXpositioner
        """
        primary = parent["/entry/instrument/bluesky_streams/primary"]
        # TODO: only proceed if len(positioners)>0

        group = self.create_NX_group(parent, f"positioners:NXnote")
        for k, v in primary.items():
            if v.attrs.get("signal_type") != "positioner":
                continue
            nxpositioner = self.create_NX_group(group, f"{k}:NXpositioner")
            nxpositioner["value"] = v

        return nxpositioner

    def write_root(self, filename):
        """
        root of the HDF5 file
        """
        self.root.attrs["file_name"] = filename
        self.root.attrs["file_time"] = datetime.datetime.now().isoformat()
        self.root.attrs[u'creator'] = self.__class__.__name__
        self.root.attrs[u'NeXus_version'] = 'v2020.1'   # TODO: generalize
        self.root.attrs[u'HDF5_Version'] = h5py.version.hdf5_version
        self.root.attrs[u'h5py_version'] = h5py.version.version
        self.root.attrs["default"] = "entry"

        self.write_entry()

    def write_sample(self, parent):

        nxsample = self.create_NX_group(parent, "sample:NXsample")
        # TODO: Is all this content available, in general?

        keys = """
            chemical_formula:NX_CHAR
            concentration:NX_FLOAT[n_comp]
            description:NX_CHAR
            electric_field:NX_FLOAT[n_eField]
            magnetic_field:NX_FLOAT[n_mField]
            rotation_angle:NX_FLOAT
            scattering_length_density:NX_FLOAT[n_comp]
            stress_field:NX_FLOAT[n_sField]
            temperature:NX_FLOAT[n_Temp]
            volume_fraction:NX_FLOAT[n_comp]
            x_translation:NX_FLOAT
        """.split()
        pre = "sample_data"
        for key in keys:
            key = key.split(":")[0]
            ds = nxsample[key] = self.get_stream_link(f"{pre}_{key}")
            if key in "electric_field magnetic_field stress_field".split():
                ds.attrs["direction"] = self.get_stream_link(f"{pre}_{key}_dir")[()].lower()

        return nxsample

    def write_slits(self, parent):
        """
        group: /entry/instrument/slits:NXnote/SLIT:NXslit
        """
        group = self.create_NX_group(parent, f"slits:NXnote")
        # TODO: generalize: USAXS-specific
        pre = "guard_slit"
        for pre in "guard_slit usaxs_slit".split():
            slit = self.create_NX_group(group, f"{pre}:NXslit")
            slit["x_gap"] = self.get_stream_link(f"{pre}_h_size")
            slit["y_gap"] = self.get_stream_link(f"{pre}_v_size")
            for key in "x y".split():
                slit[key] = self.get_stream_link(f"{pre}_{key}")

    def write_source(self, parent):
        """
        group: /entry/instrument/source:NXsource

        Note: this is specific to the APS
        """
        nxsource = self.create_NX_group(parent, "source:NXsource")

        ds = nxsource.create_dataset("name", data="Advanced Photon Source")
        ds.attrs["short_name"] = "APS"
        nxsource.create_dataset("type", data="Synchrotron X-ray Source")
        nxsource.create_dataset("probe", data="x-ray")
        ds = nxsource.create_dataset("energy", data=6)
        ds.attrs["units"] = "GeV"
        
        nxsource["current"] = self.get_stream_link("aps_current")
        nxsource["cycle"] = self.get_stream_link("aps_aps_cycle")
        nxsource["fill_number"] = self.get_stream_link("aps_fill_number")

        return nxsource

    def write_streams(self, parent):
        """
        group: /entry/instrument/bluesky_streams:NXnote

        data from all the bluesky streams
        """
        bluesky = self.create_NX_group(parent, "bluesky_streams:NXnote")
        for stream_name, uids in self.streams.items():
            if len(uids) != 1:
                raise ValueError(f"stream {len(uids)} has descriptors, expecting only 1")
            group = self.create_NX_group(bluesky, stream_name+":NXnote")
            group.attrs["uid"] = uids[0]
            for k, v in self.acquisitions[uids[0]]["data"].items():
                # NXlog is for time series data but NXdata makes an automatic plot
                subgroup = self.create_NX_group(group, k+":NXdata")
                subgroup.attrs["signal"] = "value"
                subgroup.attrs["axes"] = ["time",]

                d = v["data"]
                if isinstance(d, list) and len(d) > 0:
                    if v["dtype"] in ("string",):
                        d = self.h5string(d)
                    elif v["dtype"] in ("integer", "number"):
                        d = np.array(d)
                try:
                    ds = subgroup.create_dataset("value", data=d)
                    try:
                        self.add_dataset_attributes(ds, v, k)
                    except Exception as exc:
                        logger.error(v["dtype"], type(d), k, exc)
                except TypeError as exc:
                    logger.error(v["dtype"], k, f"TypeError({exc})", v["data"])
                ds.attrs["target"] = ds.name
                if stream_name == "baseline":
                    # make it easier to pick single values
                    # identify start/end of acquisition
                    ds = subgroup.create_dataset("value_start", data=d[0])
                    self.add_dataset_attributes(ds, v, k)
                    ds.attrs["target"] = ds.name
                    ds = subgroup.create_dataset("value_end", data=d[-1])
                    self.add_dataset_attributes(ds, v, k)
                    ds.attrs["target"] = ds.name

                t = np.array(v["time"])
                ds = subgroup.create_dataset("EPOCH", data=t)
                ds.attrs["units"] = "s"
                ds.attrs["long_name"] = "epoch time (s)"
                ds.attrs["target"] = ds.name

                t_start = t[0]
                ds = subgroup.create_dataset("time", data=t - t_start)
                ds.attrs["units"] = "s"
                ds.attrs["long_name"] = "time since first data (s)"
                ds.attrs["target"] = ds.name
                ds.attrs["start_time"] = t_start
                ds.attrs["start_time_iso"] = datetime.datetime.fromtimestamp(t_start).isoformat()

        return bluesky

    def write_undulator(self, parent):
        """
        group: /entry/instrument/undulator:NXinsertion_device
        """
        undulator = self.create_NX_group(parent, "undulator:NXinsertion_device")

        undulator.create_dataset("type", data="undulator")

        keys = """
            gap gap_taper 
            energy energy_taper 
            total_power
            harmonic_value 
            device location version
        """.split()
        # TODO: generalize: beamline-specific
        pre = "undulator_downstream"
        for key in keys:
            undulator[key] = self.get_stream_link(f"{pre}_{key}")

        return undulator

    def write_user(self, parent):
        """
        group: /entry/contact:NXuser
        """
        nxuser = self.create_NX_group(parent, "contact:NXuser")

        nxuser.create_dataset("role", data="contact")
        nxuser["name"] = self.get_stream_link("bss_user_info_contact")
        nxuser["affiliation"] = self.get_stream_link("bss_user_info_institution")
        nxuser["email"] = self.get_stream_link("bss_user_info_email")
        nxuser["facility_user_id"] = self.get_stream_link("bss_user_info_badge")

        return nxuser
