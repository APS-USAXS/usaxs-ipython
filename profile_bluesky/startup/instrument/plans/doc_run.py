
"""
Read an object and create a run.
"""

__all__ = [
    "documentation_run", 
    ]

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps


def documentation_run(obj, md=None, stream=None):
    """
    Read an object and save as a bluesky run.
    """
    stream = stream or "primary"
    _md = dict(
        purpose=f"document current values of device {obj.name}",
        plan_name="documentation_run",
    )
    _md.update(md or {})
    uid = yield from bps.open_run(md=_md)
    yield from bps.create(stream)
    yield from bps.read(obj)
    yield from bps.save()
    yield from bps.close_run()
    return uid
