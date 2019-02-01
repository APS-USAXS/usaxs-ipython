print(__file__)

"""
instrument constants
"""


logger = logging.getLogger(os.path.split(__file__)[-1])


constants = {
    "SAXS_TR_PINY_OFFSET" : 10, # how long to measure transmission for
    "SAXS_TR_TIME" : 3, # measured on 12/09/2018 JIL, after mica windows repair and realignment of front; 
    "TR_MAX_ALLOWED_COUNTS" : 980000, # maximum allowed counts for upd before assume topped up. 
}

