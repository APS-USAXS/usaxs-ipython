# Simple Plan for Bluesky

A bluesky plan is a python function that runs some activity.
Usually, that activity is a data-acquisition procedure but in practice,
a plan can execute something more procedural, such as moving
parts of the equipment around or archiving experimental conditions.
In Python terms, a plan is a generator.  Bluesky requires all plans
to generate at least one bluesky [Msg](https://nsls-ii.github.io/bluesky/msg.html) object.

## Example

Assuming we have some detector named `scaler0`, we construct
a simple plan that reads all available channels from that detector
and saves the values, along with some metadata.  We also connect 
with the USAXS instrument's surveillance routine `instrument_archive()`
which makes a permanent archive of all experiment activities for 
the USAXS instrument.  Here, we include the archive record's
contents to the bluesky scan's metadata.

We copy the following code into a new python file
`simple1.py` in our working directory:

```
def myPlan():
    summary = "demonstrate a simple plan"
    archive = instrument_archive(summary)
    md = dict(archive=archive, summary=summary)
    
    yield from bp.count([scaler0], md=md)
```

then load that into our bluesky (ipython) session:

    %run -i simple1.py

then test the plan: `summarize_plan(myPlan())`

```
In [3]: %run -i simple1.py                                                                                                                  

In [4]: summarize_plan(myPlan())                                                                                                            
=================================== Open Run ===================================
  Read ['scaler0']
================================== Close Run ===================================
```

Ready to run the plan: `RE(myPlan())`

```
In [5]: RE(myPlan())                                                                                                                        
Transient Scan ID: 1     Time: 2019-06-05 18:44:25
Persistent Unique Scan ID: 'a60d7f64-38fb-47c0-9d3e-5ffd149931fd'
New stream: 'baseline'
Start-of-run baseline readings:
+--------------------------------+--------------------------------+
|                 guard_slit_bot | -0.12479999999999958           |
|                 guard_slit_inb | -0.5424000000000007            |
|                guard_slit_outb | 0.5423999999999864             |
|                 guard_slit_top | 0.1248                         |
|                   guard_slit_x | -0.014999999999993463          |
|                   guard_slit_y | 14.455996484375                |
|              usaxs_slit_h_size | 0.8001624000000014             |
|                   usaxs_slit_x | 8.000000001118224e-06          |
|              usaxs_slit_v_size | 0.2000810000000044             |
|                   usaxs_slit_y | 0.24993599999999994            |
+--------------------------------+--------------------------------+
New stream: 'aps_current_monitor'
New stream: 'primary'                                                                                                                       
+-----------+------------+------------+------------+------------+------------+------------+------------+
|   seq_num |       time |    seconds |   I0_USAXS |  I00_USAXS |   PD_USAXS |   TR diode |       I000 |
+-----------+------------+------------+------------+------------+------------+------------+------------+
|         1 | 18:44:34.1 |   70000000 |       9065 |      11713 |    1594365 |          1 |          0 |
+-----------+------------+------------+------------+------------+------------+------------+------------+
generator count ['a60d7f64'] (scan num: 1)
End-of-run baseline readings:
+--------------------------------+--------------------------------+
|                 guard_slit_bot | -0.12479999999999958           |
|                 guard_slit_inb | -0.5424000000000007            |
|                guard_slit_outb | 0.5423999999999864             |
|                 guard_slit_top | 0.1248                         |
|                   guard_slit_x | -0.014999999999993463          |
|                   guard_slit_y | 14.455996484375                |
|              usaxs_slit_h_size | 0.8001624000000014             |
|                   usaxs_slit_x | 8.000000001118224e-06          |
|              usaxs_slit_v_size | 0.2000810000000044             |
|                   usaxs_slit_y | 0.24993599999999994            |
+--------------------------------+--------------------------------+



exit status: success
# descriptor(s): 3
# event(s): 18
Out[5]: ('a60d7f64-38fb-47c0-9d3e-5ffd149931fd',)
```
