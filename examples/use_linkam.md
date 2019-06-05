# Use a supported Linkam heater

There are two Linkam sample heaters already configured for use 
with the USAXS instrument and bluesky.  Talk with the instrument 
scientist to verify the heater you wish to use is in operation.

Device | Controller type | EPICS PV prefix
--- | --- | ---
`linkam_ci94` | Linkam_CI94 (the old one) | `9idcLAX:ci94:`
`linkam_tc1`  | Linkam_T96 | `9idcLINKAM:tc1:`

While the basic controls are the same for either controller type,
the additional features are different.  Consult the 
[source code](/profile_bluesky/startup/10-devices.py)
if you need more information.  Search for the controller type 
by name in that file.

## Basic Controls

The basic controls are described in this table:

control | description
--- | ---
`.set_target()` | Set the controller to a specific temperature
`.value` | controller's current temperature
`.settled` | controller at the desired temperature?
`.target.value` | controller's desired temperature
`.tolerance.value` | controller is *settled* if `|signal - target| <= tolerance`

### `.target.value` : What temperature is the controller set to? 

    controller.target.value

### `.set_target()` : Set the controller to a specific temperature

    controller.set_target(new_temperature)

### `.value` : What is the controller actual temperature now?

    print(controller.value)

(note: this is a shortcut to the actual location)

    print(controller.signal.value)

### `.settled` : Has the controller reached the desired temperature?

    print(controller.settled)

### `.tolerance.value` : How close must the actual temperature (signal) 
    be to the target temperature for the controller to indicate it is *settled*?

    print(controller.settled)

### `.tolerance.value` : How to set the `tolerance`*?

From the command line: `controller.tolerance.put(2)` (sets it to 2 degrees)

From a plan: `yield from bps.mv(controller.tolerance, 2)`

