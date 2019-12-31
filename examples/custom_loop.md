# Custom Plan with a Loop

If you need to loop, such as scanning over a sequence of other parameters,
you need to write your own plan.  These are the basic steps:

1. Create a new python file in the *user area* (the working data directory 
   such as `/share1/USAXS_data/2019-06/`).  This file will be executed
   within the ipython shell and should have access to all that is 
   defined in that session.
1. Any commands you execute at the outer level of this file will execute
   each time the file is run.  (Only write functions or
   define constants.)
   
   Do not execute anything at the outer level.
1. In that file, create a function that will be your new bluesky plan.
   It can take whatever parameters you choose.  You'll need to supply
   and parameters you specify.
1. Add this as first line in your plan function (it will activate the 
   standard activity logging of the USAXS instrument):

       instrument_archive("summarize this plan")

1. Write your loop setup and activities.  Make sure you do not write
   any code that will block the `RE()` loop for a significant 
   (ca. millisecond or longer) time.  Use `yield from bps.sleep(0.1)`
   instead of `time.sleep(0.1)` to wait a short bit.  Use 
   `yield from bps.mv(signal, new_value)` instead of 
   `signal.put(new_value)`.
   
   Your plan **must** *yield* at least one bluesky `Msg` object!
   This is easy if you follow the examples.

## Example

In this example, a sample is measured in USAXS/SAXS/WAX at ambient temperature.
Then, the sample heater is set to some temperature provided, and the
sequence is repeated a number of times.  The whole sequence is tested using
`summarize_plan(my_custom_plan(...))
and then run using:
`RE(my_custom_plan(...))` (where `...` represents the required arguments).

```
def _measure_all_three(sx, sy, thickness, sample_name, md={}):
    """this is used internally, not called on the command line"""
    print("USAXS SAXS WAXS scan")
    yield from FlyScan(sx, sy, thickness, sample_name, md=md)
    yield from SAXS(sx, sy, thickness, sample_name, md=md)
    yield from WAXS(sx, sy, thickness, sample_name, md=md)


def my_custom_plan(sx, sy, thickness, sample_name, temperature, iterations=9, md={}):
    instrument_archive("custom plan example")
    t0 = time.time()
    md = {
        "user_procedure": "USAXS SAXS WAXS scans",
        "iteration": 0,
        "total_iteration": iterations,
        }
    yield from _measure_all_three(sx, sy, thickness, sample_name, md=md)
    yield from bps.mv(linkam.rate, 100)			# degrees C/minute
    yield from linkam.set_target(temperature, wait=True)	# degrees C
    for i in range(iterations):
        print(f"Iteration {i+1} of {iterations}, elapsed time = {time.time() - t0:.3f}s")
        md["iteration"] = i+1
        yield from _measure_all_three(sx, sy, thickness, sample_name, md=md)
```


## Load your python code

Load your code with: `%run -i my_python_file_name.py`

Be sure to use the percent sign and the `-i` terms as they are 
important to your code working with the other instrument components.

TIP: Any time you edit your python file, you can reload it 
using the same command:  `%run -i my_python_file_name.py`


## Test your custom plan first!

To test that your custom plan does not have any obvious errors,
enter this command at the bluesky (ipython) prompt (supply any
arguments that your plan requires):

    summarize_plan(my_python_file_name.my_custom_plan())

The `summarize_plan()` function will do a dry run through your command file,
as if the experiment was actually running.  It will print a list of 
things that will be done when given to the `RE()` command.

Revise your python file (and `reload`) until `summarize_plan()` runs to completion with no errors.

## Run your custom plan

To run your custom plan,
enter this command at the bluesky (ipython) prompt:

    RE(my_python_file_name.my_custom_plan())

