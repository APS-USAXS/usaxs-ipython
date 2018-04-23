print(__file__)

"""PointGrey BlackFly detector"""


# note: this is about the easiest area detector setup in Ophyd


class MyPointGreyDetector(SingleTrigger, AreaDetector):
    """PointGrey Black Fly detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PointGreyDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")


blackfly_det = MyPointGreyDetector(
    area_detector_EPICS_PV_prefix["PointGrey BlackFly"], 
    name="blackfly_det")
