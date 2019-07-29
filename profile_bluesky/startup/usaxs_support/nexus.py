#!/usr/bin/env python

"""
support the NeXus file output from USAXS Fly scans

PUBLIC FUNCTIONS

    ~get_manager
    ~reset_manager

INTERNAL

    ~NeXus_Structure

"""

import logging
import os


logger = logging.getLogger(os.path.split(__file__)[-1])
logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.NullHandler())

manager = None # singleton instance of NeXus_Structure


def reset_manager():
    """
    clear the NeXus structure manager
    
    The configuration file must be parsed the next time the
    structure manager object is requested using ``get_manager()``.
    """
    global manager
    logger.debug("Reset NeXus structure manager")
    manager = None


def get_manager(RE, config_file):
    """
    return a reference to the NeXus structure manager
    
    If the manager is not defined (``None``), then create a 
    new instance of ``NeXus_Structure()``.
    """
    global manager
    if manager is None:
        logger.debug("create new NeXus structure manager instance")
        manager = NeXus_Structure(RE, config_file)
    return manager


class NeXus_Structure(object):
    """
    parse XML configuration, layout structure of HDF5 file, define PVs in ophyd
    """
    
    def __init__(self, RE, config_file):
        self.RE = RE
        self.config_filename = config_file


def developer():
    print("basic tests while developing this module")
    assert manager == None, "starting condition should be None"

    boss = get_manager(None, "")
    assert isinstance(boss, NeXus_Structure), "new structure created"

    mgr = get_manager(None, "")
    assert isinstance(mgr, NeXus_Structure), "existing structure"
    assert boss == mgr, "identical to first structure"

    reset_manager()
    assert manager == None, "structure reset"

    mgr = get_manager(None, "")
    assert isinstance(mgr, NeXus_Structure), "new structure created"
    assert boss != mgr, "new structure different from first structure"

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    developer()
