# USAXS Scan of One Sample

This command, on the Bluesky (ipython) command line, will 
execute a single USAXS scan of the steel sample.  The sample stage
is positioned at `SX=10` and `SY=20`.  The sample thickness
is 0.015 mm.

    RE(FlyScan(10, 20, 0.015, "4140 steel, aged 510C 3h"))

This is an example for scanning the *blank* (no sample in the beam):

    RE(FlyScan(-10, 20, 0, "blank"))

Note:  If you want to run a batch of scans, write a
[command file](command_file.md) and
scan that.  (Please do not execute a python function that calls
`RE()` multiple times.  The `RE()` has features to help you when 
you wish to interrupt a set of scans, such as when you press 
*<control>-C*.)  For a custom batch of scans, you may need to
write your own plan, such as the [custom loop example](custom_loop.md).
