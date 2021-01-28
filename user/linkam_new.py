# this is a Linkam plan

from instrument.session_logs import logger
logger.info(__file__)


from bluesky import plan_stubs as bps
import time

from instrument.devices import linkam_ci94, linkam_tc1, terms
from instrument.plans import SAXS, USAXSscan, WAXS
from instrument.utils import getSampleTitle, resetSampleTitleFunction, setSampleTitleFunction

PULSE_MAX = 10000

def countProcessesRunning():
    """Watch the pulse and count how many 10 Hz processes running."""
    pulse0 = terms.HeaterProcess.linkam_pulse.get()
    time.sleep(10)  # watch for 10 s
    pulses = (terms.HeaterProcess.linkam_pulse.get() - pulse0) % PULSE_MAX
    return round(pulses / PULSE_MAX)

def myLinkamPlan(pos_X, pos_Y, thickness, scan_title, delaymin, md={}):
    """
    collect RT USAXS/SAXS/WAXS
    change temperature T to temp1 with rate1
    collect USAXS/SAXS/WAXS while Linkam is runinng on its own
    delaymin [minutes] is total time which the cycle should take. 
    it will end after this time elapses...

    reload by
    # %run -m linkam
    """

    def myTitleFunction(title):
        return f"{title}_{linkam.value:.0f}C_{(time.time()-t1)/60:.0f}min"

    def collectAllThree(debug=True):
        if debug:
            #for testing purposes, set debug=True
            sampleMod = myTitleFunction(scan_title)
            print(sampleMod)
            yield from bps.sleep(20)
        else:
            yield from USAXSscan(pos_X, pos_Y, thickness, scan_title, md={})
            yield from SAXS(pos_X, pos_Y, thickness, scan_title, md={})
            yield from WAXS(pos_X, pos_Y, thickness, scan_title, md={})

    #linkam = linkam_tc1
    linkam = linkam_ci94
    logger.info(f"Linkam controller PV prefix={linkam.prefix}")
    
    setSampleTitleFunction(myTitleFunction)

    t1 = time.time()
    yield from collectAllThree()
    
    
    # TODO: start the program
    # TODO: We have to measure the pulse in a background thread.
    # TODO: wait for number of processes to equal 1 (blocking so background thread)

    # here we need to trigger the Linkam control python program...
    yield from bps.mv(terms.HeaterProcess.linkam_trigger, 1)
    t1 = time.time()
    delay = delaymin * 60                                  # convert to seconds
    
    while time.time()-t1 < delay:                          # collects data for delay seconds
        yield from collectAllThree()

    logger.info(f"Finished after {delay} seconds")
    
    # tell the Linkam control python program to exit... 
    yield from bps.mv(terms.HeaterProcess.linkam_exit, 1)

    resetSampleTitleFunction()

    logger.info(f"finished")

