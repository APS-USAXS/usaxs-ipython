logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))


CT_RANGE = [0, 0, 0, 0, 0]  # how is this used?


"""
USAXS step scan: uascan

    (base) user@host:~/.../startup/ref$ grep "^def " macros/local/usaxs_uascan.mac
    def USAXSscan '{
    def USAXSscanStep '{
    def measure_USAXS_PinT'
    def set_Filters_For_Transm '
    def resetUSAXS '{
    def uascan '
    def uascanStepFunc(x, factor, center, exponent, minStep) '{
    def uascanTestSeries(start, center, finish, numPts, factor, exponent, minStep) '{
    def uascanFindFactor(start center finish numPts exponent minStep) '{
    def _usaxs_triangulate (rot,center,dist) '{
"""


def USAXSscan(*args, **kwargs):
    """
    """
    # TODO: work-in-progress


def USAXSscanStep(*args, **kwargs):
    """
    """
    # TODO: work-in-progress


def uascan(
        motor, start, center, finish, minStep,
        dy0, SDD_mm, ay0, SAD_mm,
        exponent, intervals, count_time,
        useDynamicTime=True,
        useIntelligentTime=True,
    ):
    """
    general USAXS step scan plan

    Why do we need to pass `motor` as a parameter?
    Will it ever be anything different?
    """
    if intervals <= 0:
        raise ValueError(f"intervals must be >0, given: {intervals}")

    u = Ustep(start, center, finish, intervals, exponent, minStep)
    # print(u.factor)
    # print(u.series)

    count_time_base = count_time
    if useDynamicTime:
        count_time = count_time_base / 3
    if useIntelligentTime:
        count_time = CT_RANGE[0]

    # original values before scan
    # FIXME: get correct values
    before_scan = {
    'dy' : 0,            # position of photodiode before scan
	'ay' : 0,            # position of AY before scan
	'sy' : 0,            # position of SY before scan
	'ar' : 0,            # position of AR motor before scan
    'ASRP' : 0,          # position of ASRP motor before scan
    }

    if useSBUSAXS:
        pass        # FIXME:

    def _scan_on():
        scan_over = False
        # TODO: work-in-progress

    # TODO: work-in-progress
