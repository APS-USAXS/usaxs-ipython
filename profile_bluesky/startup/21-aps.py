logger.info(__file__)
logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""
aps

MUST come before filters and shutters
"""


aps = APS_devices.ApsMachineParametersDevice(name="aps")
sd.baseline.append(aps)

undulator = APS_devices.ApsUndulatorDual("ID09", name="undulator")
sd.baseline.append(undulator)

diagnostics = DiagnosticsParameters(name="diagnostics")
sd.baseline.append(diagnostics)


def operations_in_9idc():
    """
    returns True if allowed to use X-ray beam in 9-ID-C station
    """
    return diagnostics.PSS.c_station_enabled
