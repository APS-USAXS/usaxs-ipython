# Custom Plan with a Loop

If you need to loop, such as scanning over a sequence of other parameters,
you need to write your own plan.  These are the basic steps:

1. create a new python file in the *user area* (the working data directory 
   such as `/share1/USAXS_data/2019-06/`)
1. Among the other `import` statements, add: `import usaxs_support.surveillance`
1. Any commands you execute at the outer level of this file will be run
   each time the file is imported or reloaded.  
   
   Do not execute anything at the outer level.
1. In that file, create a function that will be your new bluesky plan.
   It can take whatever parameters you choose.  You'll need to supply
   and parameters you specify.
1. Add this as first line in your plan function (it will activate the 
   standard activity logging of the USAXS instrument):

       usaxs_support.surveillance.make_archive("summarize this plan")

1. Write your loop setup and activities.  Make sure you do not write
   any code that will block the `RE()` loop for a significant 
   (ca. millisecond or longer) time.  Use `yield from bps.sleep(0.1)`
   instead of `time.sleep(0.1)` to wait a short bit.  Use 
   `yield from bps.mv(signal, new_value)` instead of 
   `signal.put(new_value)`.
   
   Your plan **must** *yield* at least one bluesky `Msg` object!
   This is easy if you follow the examples.

## Example

In this example, a sample is measured in USAXS/SAXS/WAXS, then that 
sequence is repeated.  Also, before the sequence, the sample heater 
is set to temperature.  The whole sequence is test using
`summarize_plan(my_custom_plan(...))
and run using:
`RE(my_custom_plan(...))` (where `...` represents the required arguments).

```
def MeasureAllThree(sx, sy, thickness, sample_name, md={}):
    print("USAXS SAXS WAXS scan")
    yield from FlyScan(sx, sy, thickness, sample_name, md=md)
    yield from SAXS(sx, sy, thickness, sample_name, md=md)
    yield from WAXS(sx, sy, thickness, sample_name, md=md)


def my_custom_plan(sx, sy, thickness, sample_name, temperature, iterations=9, md={}):
    usaxs_support.surveillance.make_archive("summarize this plan")
    t0 = time.time()
    md = {
        "user_procedure": "USAXS SAXS WAXS scans",
        "iteration": 0,
        "total_iteration": iterations,
        }
    yield from MeasureAllThree(sx, sy, thickness, sample_name, md=md)
    yield from bps.mv(linkam.set_rate, 100)			# degrees C/minute
    yield from linkam.set_target(temperature, wait=True)	# degrees C
    for i in range(iterations):
        print(f"Iteration {i+1} of {iterations}, elapsed time = {time.time() - t0:.3f}s")
        md["iteration"] = i+1
        yield from MeasureAllThree(sx, sy, thickness, sample_name, md=md)```


## Load your python code
If you have not already imported this file, then do this
from the bluesky (ipython) command line:

    import my_python_file_name

If you have already imported this file once, then

    reload("my_python_file_name.py")	# TODO: confirm this is correct

## Test your custom plan first!

To test that your custom plan does not have any obvious errors,
enter this command at the bluesky (ipython) prompt (supply any
arguments that your plan requires):

    summarize_plan(my_custom_plan())

The `summarize_plan()` function will do a dry run through your command file,
as if the experiment was actually running.  It will print a list of 
things that will be done when given to the `RE()` command.

Revise your python file (and `reload`) until `summarize_plan()` runs to completion with no errors.

## Run your custom plan

To run your custom plan,
enter this command at the bluesky (ipython) prompt:

    RE(my_custom_plan())
