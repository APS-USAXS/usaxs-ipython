print(__file__)

"""
aps

MUST come before filters and shutters
"""

aps = APS_devices.ApsMachineParametersDevice(name="aps")
sd.baseline.append(aps)

undulator = APS_devices.ApsUndulatorDual("ID09", name="undulator")
sd.baseline.append(undulator)

bc_station_beam_stop = PSS_Parameters(name="bc_station_beam_stop")


def operations_in_9idc():
    """
    returns True if allowed to use X-ray beam in 9-ID-C station
    
    The PSS has a beam plug just before the C station
    
    :Plug in place:
      Cannot use beam in 9-ID-C.
      Should not use FE or mono shutters, monochromator, ti_filter_shutter...

    :Plug removed:
      Operations in 9-ID-C are allowed
    """
    return bc_station_beam_stop.c_station_enabled
