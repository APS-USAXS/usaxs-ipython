To load into ipython use following command:

    %run -i -m user.linkam 

**Caution**:
    If you add or modify symbols in the user's command shell (IPython namespace) and those symbols are used in your file (`user/linkam.py` as the example shows), you must repeat the `%run` command (above) to load those changes.


## about files in `user` directory

Each file should be written like a standard Python module, including all the imports necessary to support the code.

To use symbols from the user command shell (a.k.a., the *IPython session namespace*): 
you'll need to add them.  Look at the section below for these instructions.

Usually, your code should take any necessary symbols as arguments (args) or optional keyword arguments (kwargs).

## how to access the symbols in the IPython session namespace

Add this code block at the top of the file, before anything else:

```
# get all the symbols from the IPython shell
import IPython
globals().update(IPython.get_ipython().user_ns)
logger.info(__file__)
```
