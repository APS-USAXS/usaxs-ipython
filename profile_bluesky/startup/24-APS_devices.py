print(__file__)

"""override certain APS_BlueSky_tools.devices"""


class ApsFileStoreHDF5(APS_devices.ApsFileStoreHDF5):
    
    def generate_datum(self, key, timestamp, datum_kwargs):
        "Generate a uid and cache it with its key for later insertion."
        template = self.file_template.get()
        filename, read_path, write_path = self.make_filename()
        file_number = self.file_number.get() - 1
        hdf5_file_name = template % (read_path, filename, file_number)

        # inject the actual name of the HDF5 file here into datum_kwargs
        datum_kwargs["HDF5_file_name"] = hdf5_file_name
        
        # print("make_filename:", hdf5_file_name)
        return super().generate_datum(key, timestamp, datum_kwargs)


class ApsFileStoreHDF5IterativeWrite(ApsFileStoreHDF5, FileStoreIterativeWrite):
    """override"""

class ApsHDF5Plugin(HDF5Plugin, ApsFileStoreHDF5IterativeWrite):
    """override"""

# reset for now
#class ApsHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
#    pass
