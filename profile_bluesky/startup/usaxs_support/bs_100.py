#!/usr/bin/env python

from ophyd import EpicsSignal
import tester_100


if __name__ == "__main__":
    pvlist = tester_100.get_pv_list()
    for pvname in pvlist:
        try:
            pv = EpicsSignal(pvname, name="pv")
            print(pvname, type(pv.value), pv.value)
        except TimeoutError:
            print(pvname, "timeout")
