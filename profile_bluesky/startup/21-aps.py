print(__file__)

"""
aps

MUST come before filters and shutters
"""

aps = APS_devices.ApsMachineParametersDevice(name="aps")
sd.baseline.append(aps)

undulator = APS_devices.ApsUndulatorDual("ID09", name="undulator")
sd.baseline.append(undulator)
