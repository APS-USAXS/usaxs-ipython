
"""
keep the legend short on BestEffortCallback plots
"""

__all__ = [
    'becplot_prune_fifo',
]

from ..session_logs import logger
logger.info(__file__)


from ..framework import bec


def becplot_prune_fifo(n, y, x):
    """
    find the plot with axes x and y and replot with only the last *n* lines

    Note: this is not a bluesky plan.  Call it as normal Python function.

    EXAMPLE::

        becplot_prune_fifo(1, noisy, m1)

    PARAMETERS
    
    n : int
        number of plots to keep
    
    y : object
        ophyd Signal object on dependent (y) axis
    
    x : object
        ophyd Signal object on independent (x) axis
    """
    for liveplot in bec._live_plots.values():
        lp = liveplot.get(y.name)
        if lp is None:
            logger.debug(f"no LivePlot with name {y.name}")
            continue
        if lp.x != x.name or lp.y != y.name:
            logger.debug(f"no LivePlot with axes ('{x.name}', '{y.name}')")
            continue
        # print(lp.x, lp.y)
        if len(lp.ax.lines) > n:
            logger.debug(f"limiting LivePlot({y.name}) to {n} traces")
            lp.ax.lines = lp.ax.lines[-n:]
            lp.update_plot()
