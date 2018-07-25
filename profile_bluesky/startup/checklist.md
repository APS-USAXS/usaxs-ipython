# 2018-07-25  testing checklist

* [x] restore callback SpecWriterCallback()
* [x] spec file OK for bp.count([joerger])
* [*] spec file OK for bp.scan([scaler0], m_stage.r, 8.9139070, 8.9189070, 31) : tune (#38)
* [ ] spec file OK for bp.scan([joerger], m_stage.r, 8.9141940, 8.9191940, 31) : tune (#38)
* [x] mono_shutter.open() and .close()
* [x] ti_filter_shutter.open() and .close() (fix: #32)
* [*] scaler0 operations (prefer ScalerCH since it gets names from EPICS but see #34)
* [*] mr axis tuning (#38)
* [ ] ar axis tuning
* [ ] alta_det EPICS-controlled HDF5 file names (#33)
* [ ] saxs_det EPICS-controlled HDF5 file names (#33)
* [ ] waxs_det EPICS-controlled HDF5 file names (#33)
* [ ] requested macros (#36)
