print(__file__)
print(resource_usage(os.path.split(__file__)[-1]))

'''
ensure that PyEpics is available

Do this early in the setup so other setup can benefit.
'''

import epics

