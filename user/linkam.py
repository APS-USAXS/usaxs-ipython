# this is a Linkam plan

# get all the symbols from the IPython shell
import IPython
globals().update(IPython.get_ipython().user_ns)
logger.info(__file__)


def myLinkamPlan(pos_X, pos_Y, thickness, scan_title, temp1, rate1, delay1, temp2, rate2, md={}):
    """
    collect RT USAXS/WAXS for N1
    change temperature T
    collect USAXS/WAXS while heating
    when T reached, hold for N2 minutes, collecting data repeatedly
    change T to RT
    collect data while ramping
    reach RT
    collect final data
    
    sampleTitleMod = f"{sample}_{temperature_C:.0f}C_{(time.time()-t0)/60:.0f}min"
    Flyscan(pos_X, pos_Y, thickness, scan_title, md={}):
    
    reload by : 
    %run -i -m user.linkam
    """
    def setSampleName():
        return f"{scan_title}_{linkam_tc1.value:.0f}C_{(time.time()-t0)/60:.0f}min" 
        
    def collectAllThree():
        debug=False
        sampleMod = setSampleName()
        if debug:
            #for testing purposes, set debug=True
            print(sampleMod) 
            yield from bps.sleep(20)
        else:
            md["title"]=sampleMod
            yield from Flyscan(pos_X, pos_Y, thickness, sampleMod, md={})
            sampleMod = setSampleName()
            md["title"]=sampleMod
            yield from SAXS(pox_X, pos_Y, thickness, sampleMod, md={})
            sampleMod = setSampleName()
            md["title"]=sampleMod
            yield from WAXS(pos_X, pos_Y, thickness, sampleMod, md={})
        
        
    t0 = time.time()
    yield from collectAllThree()
    
    yield from bps.mv(linkam_tc1.ramp_rate, rate1)          #sets the rate of next ramp
    yield from linkam_tc1.set_target(temp1, wait=False)     #sets the temp of next ramp
    
    while not linkam_tc1.settled:                           #runs data collection until next temp
        yield from collectAllThree()
      
    print(f"Reached temperature, now collecting data for {delay1} seconds")  
    t1 = time.time()
    
    while time.time()-t1 < delay1:                          # collects data for delay1 seconds
        yield from collectAllThree()
 
    print(f"waited for {delay1} seconds, now ramp down")  

    yield from bps.mv(linkam_tc1.ramp_rate, rate2)          #sets the rate of next ramp
    yield from linkam_tc1.set_target(temp2, wait=False)     #sets the temp of next ramp

    while not linkam_tc1.settled:                           #runs data collection until next temp
        yield from collectAllThree()

    yield from collectAllThree()

