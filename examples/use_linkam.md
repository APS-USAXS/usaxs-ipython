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

The basic controls (derived from 
[`apstools.devices.ProcessController`](https://apstools.readthedocs.io/en/latest/source/devices.html#apstools.devices.ProcessController))
are described in the table below.  Keep these terms in mind:

<dl>
  <dt>signal</dt>
  <dd>the measured value (temperature, degrees C)</dd>
  
  <dt>target</dt>
  <dd>the desired value (the temperature set point, degrees C)</dd>
  
  <dt>tolerance</dt>
  <dd>the maximum acceptable mismatch between signal and target (degrees C)</dd>
</dl>

control | description
--- | ---
`.set_target()` | Set the controller to a specific temperature
`.value` | controller's current temperature
`.settled` | controller at the desired temperature?
`.target.value` | controller's desired temperature
`.tolerance.value` | controller is not *settled* if `abs(signal - target) > tolerance`

### Basic Controls examples

In the examples below, replace `linkam_tc1` with the name of your temperature controller if it is different.

### `.target.value` : What temperature is `linkam_tc1` set to? 

    linkam_tc1.target.value

### `.set_target()` : Set `linkam_tc1` to a specific temperature

    linkam_tc1.set_target(new_temperature)

By default, this will wait until `linkam_tc1` is *settled* before it returns.

### `.value` : What is the `linkam_tc1` actual temperature now?

    print(linkam_tc1.value)

(note: this is a shortcut to the actual location)

    print(linkam_tc1.signal.value)

### `.settled` : Has `linkam_tc1` reached the desired temperature?

    print(linkam_tc1.settled)

### `.tolerance.value` : How close is *settled*?

How close must the actual temperature (signal) be to the target temperature for `linkam_tc1` to indicate it is *settled*?

    print(linkam_tc1.settled)

### `.tolerance.value` : How to set the `tolerance`*?

From the command line: `linkam_tc1.tolerance.put(2)` (sets it to 2 degrees)

From a plan: `yield from bps.mv(linkam_tc1.tolerance, 2)`

