print(__file__)
print(resource_usage(os.path.split(__file__)[-1]))

"""PointGrey BlackFly detector"""


# note: this is about the easiest area detector setup in Ophyd


class MyPointGreyDetector(SingleTrigger, AreaDetector):
    """PointGrey Black Fly detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PointGreyDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")


try:
    nm = "PointGrey BlackFly"
    prefix = area_detector_EPICS_PV_prefix[nm]
    blackfly_det = MyPointGreyDetector(prefix, name="blackfly_det")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    print(msg)
