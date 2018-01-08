import ophyd
from ophyd import setup_ophyd
import databroker
setup_ophyd()
import portable_mds.sqlite.mds as pmqsm
from ophyd import EpicsSignal, Device, EpicsMotor, Component as Cpt
from bluesky.utils import install_qt_kicker
install_qt_kicker()

import matplotlib.pyplot as plt
plt.ion()



class SampleStage(Device):
    y = Cpt(EpicsMotor, 'm2')
    x = Cpt(EpicsMotor, 'm1')

s = SampleStage('9idcLAX:m58:c2:', name='s')

mds = pmqsm.MDS(config={'directory': '/share1/bluesky/mds', 'timezone': 'US/Central'})

import bluesky as bs
import bluesky.plans as bp
from bluesky.callbacks import LiveTable, LivePlot

RE = bs.RunEngine({})
RE.subscribe('all', mds.insert)

db = databroker.Broker(mds, None)
