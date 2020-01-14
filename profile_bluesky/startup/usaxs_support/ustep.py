#!/usr/bin/env python

'''
Step-Size Algorithm for Bonse-Hart Ultra-Small-Angle Scattering Instruments

:see: https://www.jemian.org/SAS/ustep.pdf
'''


class Ustep(object):
    '''
    find the series of positions for the USAXS

    :param float start: required first position of list
    :param float center: position to take minStep
    :param float finish: required ending position of list
    :param float numPts: length of the list
    :param float exponent: :math:`\eta`, exponential factor
    :param float minStep: smallest allowed step size
    :param float factor: :math:`k`, multiplying factor (computed internally)
    :param [float] series: computed list of positions
    
    EXAMPLE:
    
        start = 10.0
        center = 9.5
        finish = 7
        numPts = 100
        exponent = 1.2
        minStep = 0.0001

        ar_positions_step = Ustep(start, center, finish, numPts, exponent, minStep)
        ar_positions = ar_positions_step.series
        ar_trajectory = cycler(ar, ar_positions)

        # ay_positions = make_ay_positions(ar_positions)
        # dy_positions = make_dy_positions(ar_positions)
        ay_trajectory = cycler(ay, ay_positions)
        dy_trajectory = cycler(dy, dy_positions)

        # step these motors together
        motor_trajectory = ar_trajectory + ay_trajectory + dy_trajectory

        RE(scan_nd([detector], motor_trajectory)
    
    '''
    
    def __init__(self, start, center, finish, numPts, exponent, minStep):
        self.start = start
        self.center = center
        self.finish = finish
        self.numPts = numPts
        self.exponent = exponent
        self.minStep = minStep
        self.sign = {True: 1, False: -1}[start < finish]
        self.series = []
        self.factor = self.find_factor()
        
    def find_factor(self):
        '''
        Determine the factor that will make a series with the specified parameters.
        
        This method improves on find_factor_simplistic() by 
        choosing next choice for factor from recent history.
        '''
        
        def assess(factor):
            self.make_series(factor)
            span_diff = abs(self.series[0] - self.series[-1]) - span_target
            return span_diff
            
        span_target = abs(self.finish - self.start)
        span_precision = abs(self.minStep) * 0.2
        factor = abs(self.finish-self.start) / (self.numPts -1)
        span_diff = assess(factor)
        f = [factor, factor]
        d = [span_diff, span_diff]
        
        # first make certain that d[0] < 0 and d[1] > 0, expand f[0] and f[1]
        for _ in range(100):
            if d[0] * d[1] < 0:
                break           # now, d[0] and d[1] have opposite sign
            factor *= {True: 2, False: 0.5}[span_diff < 0]
            span_diff = assess(factor)
            key = {True: 1, False: 0}[span_diff > d[1]]
            f[key] = factor
            d[key] = span_diff
        
        # now: d[0] < 0 and d[1] > 0, squeeze f[0] & f[1] to converge
        for _ in range(100):
            if (d[1] - d[0]) > span_target:
                factor = (f[0] + f[1])/2              # bracket by bisection when not close
            else:
                factor = f[0] - d[0] * (f[1]-f[0])/(d[1]-d[0])    # linear interpolation when close
            span_diff = assess(factor)
            if abs(span_diff) <= span_precision:
                break
            key = {True: 0, False: 1}[span_diff < 0]
            f[key] = factor
            d[key] = span_diff

        return factor
        
    def find_factor_simplistic(self):
        '''
        Determine the factor that will make a series with the specified parameters.
        
        Choose the factor that will minimize :math:`| x_n - finish |` subject to:
        
        .. math::
        
           x_1 = start
           x_n <= finish
        
        This routine CAN FAIL if :math:`(finish - start)/minStep >= numPts`
        
        This search technique picks a new factor based on the fit of the present choice.
        It converges but not quickly.
        '''
        #print('\t'.join('factor diff'.split()))
        span_target = abs(self.finish - self.start)
        span_precision = abs(self.minStep) * 0.2
        factor = abs(self.finish-self.start) / (self.numPts -1)
        fStep = factor
        larger = 3.0
        smaller = 0.5
        for _ in range(100):
            self.make_series(factor)
            span = abs(self.series[0] - self.series[-1])
            span_diff = span - span_target
            #print('\t'.join(map(str,[factor, span_diff])))
            if abs(span_diff) <= span_precision:
                break
            if span_diff < 0:
                fStep = abs(fStep) * larger
            else:
                fStep = -abs(fStep) * smaller
            factor += fStep
        return factor
    
    def make_series(self, factor):
        '''create self.series with the given factor'''
        x = self.start
        series = [x, ]
        for _ in range(self.numPts - 1):
            x += self.sign * self.uascanStepFunc(x, factor)
            series.append(x)
        self.series = series
    
    def uascanStepFunc(self, x, factor):
        '''Calculate the next step size with the given parameters'''
        if abs(x - self.center) > 1e100:
            step = 1e100
        else:
            step = factor * pow( abs(x - self.center), self.exponent ) + self.minStep
        return step


def main():
    start = 10.0
    center = 9.5
    finish = 7
    numPts = 100
    exponent = 1.2
    minStep = 0.0001
    u = Ustep(start, center, finish, numPts, exponent, minStep)
    print(u.factor)
    print(u.series)


if __name__ == '__main__':
    main()
