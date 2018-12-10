#!/usr/bin/env python

import epics
import pyRestTable

PVFILE = "saveFlyData.xml"


def get_pv_list():
    """artless method to carve out the PVs from the XML file"""
    pvlist = []
    with open(PVFILE, "r") as f:
        for line in f.readlines():
            pos = line.find("pvname")
            if pos <0:
                continue
            line = line[pos:].strip()
            pos = line.find("\"")
            if pos < 0:
                continue
            line = line[pos+1:]
            pos = line.find("\"")
            if pos < 0:
                continue
            line = line[:pos]
            pvlist.append(line)
    return pvlist


if __name__ == "__main__":
    pvlist = get_pv_list()
    #print("\n".join(pvlist))
    #t = pyRestTable.Table()
    #t.labels = "pvname type".split()
    for pvname in pvlist:
        pv = epics.PV(pvname)
        value = pv.get()
        print(pvname, type(value))
    #    t.addRow((pvname, type(value)))

    #print(str(t))
