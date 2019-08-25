#!/usr/bin/env python

from saveFlyData import SaveFlyScan, pv_registry

fname = "test_100.hdf5"
saveFlyData_config = "saveFlyData.xml"

sfs = SaveFlyScan(fname, config_file=saveFlyData_config)
sfs.preliminaryWriteFile()

# TODO: inspect data types here
for k, obj in pv_registry.items():
    if k.lower().find("reqgain") < 0:
        continue
    print(obj.label, obj.pv)

sfs.saveFile()
