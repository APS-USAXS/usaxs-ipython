# Command File (list of scans to be run)

A *command file* contains a list of scans (or other actions 
known to the instrument's `run_command_file()` routine).
Examples are provided as [text](actions.txt) and
[Excel spreadsheet](actions.xlsx) files.

The list of scans (or other actions) will be executed in sequence.
(Loops, such as a 
[temperature sequence of a sample using a sample heater](custom_loop.md), 
are not available.)

## Text Command File

A text command file contains a list of scans/actions.  [Example](actions.txt)

Each line of the file is either a comment, a blank line, or a scan/action and 
its parameters.  Any unrecognized commands will be ignored (reported 
as comments) when `run_command_file()` is executed.

Parameters should be separated on a line by white 
space and **no comma**.  **ALL** of the parameters provided will be given to
the scan/action.  The sample name should be given in "quoted text" 
(using double-quotes) unless it is only one word.  Here is an example command:

    FlyScan 0   0   0   blank

## Excel Spreadsheet Command File

A spreadsheet command file contains a table with the list of 
scans/actions.  Follow the [example given](actions.xslx).  

Each line of the table is either a comment, a blank line, or a scan/action and 
its parameters.  Any unrecognized commands will be ignored (reported 
as comments) when `run_command_file()` is executed.

Start your table 
on line 4 of the first worksheet in the file.  (The first line 
are column labels for your use.  The `run_command_file()` plan
will ignore these labels.)  Information outside of the table
will be ignored, yet it is still advised now not to write 
anything in the columns to the right of the table.

After the labels row, each row will start with a scan/action 
in the first column, then all parameters in the following columns. 
**ALL** of the parameters provided will be given to the scan/action.

A blank line will indicate the end of the table.  You can use
a comment character (such as `#`) to leave a visually blank row
if needed.

After the labels row, 

## Test your command file first!

To test that your command file does not have any obvious errors,
enter this command at the bluesky (ipython) prompt:

    summarize_plan(run_command_file("my_actions_filename.txt"))

The `summarize_plan()` function will do a dry run through your command file,
as if the experiment was actually running.  It will print a list of 
things that will be done when given to the `RE()` command.

Revise your command file until `summarize_plan()` runs to completion with no errors.

## Run your command file

To run your command file,
enter this command at the bluesky (ipython) prompt:

    RE(run_command_file("my_actions_filename.txt"))

