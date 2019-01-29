print(__file__)

"""override certain apstools.devices"""

# custom support is in AD_EpicsHdf5FileName
class myHdf5EpicsIterativeWriter(
    APS_devices.AD_EpicsHdf5FileName, 
    FileStoreIterativeWrite): pass
class myHDF5FileNames(HDF5Plugin, myHdf5EpicsIterativeWriter): pass
class EpicsDefinesHDF5FileNames(HDF5Plugin, myHdf5EpicsIterativeWriter): pass
