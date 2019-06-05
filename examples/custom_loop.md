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

1. TODO: write your looping activities.

## Example

TODO:


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

