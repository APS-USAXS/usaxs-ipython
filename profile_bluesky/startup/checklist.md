# 2018-07-25  testing checklist

* [x] restore callback SpecWriterCallback()
* [ ] spec file OK
* [x] mono_shutter.open() and .close()
* [x] ti_filter_shutter.open() and .close() (fix: #32)
* [*] scaler0 operations (prefer ScalerCH since it gets names from EPICS but see #34)
* [ ] mr axis tuning
* [ ] ar axis tuning
* [ ] alta_det EPICS-controlled HDF5 file names (#33)
* [ ] saxs_det EPICS-controlled HDF5 file names (#33)
* [ ] waxs_det EPICS-controlled HDF5 file names (#33)
* [ ] issue #36
