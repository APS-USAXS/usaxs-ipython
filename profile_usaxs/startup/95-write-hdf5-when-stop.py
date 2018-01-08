print(__file__)
'''
write every scan to a file

When a `stop` document is received, write the most recent scan 
to a NeXus HDF5 file.
'''

#import suitcase.hdf5
import os
from ipython_startup_usaxs import nexus

# NOTE: refactor when this is accepted
# https://github.com/NSLS-II/suitcase/pull/27
# then: from suitcase import nexus


def write_callback(name, doc):
    '''
    write a NeXus HDF5 file when a scan ends
    '''
    if name != 'stop':
        return
    header = db[doc['run_start']]
    start = header.start
    bl_id = start.get('beamline_id') or 'testing'
    filename = '{}_{}.h5'.format(bl_id, start.scan_id)
    nexus.export(header, filename, mds, use_uid=False)
    print('wrote: ' + os.path.abspath(filename))

# RE.subscribe('stop', write_callback)

# RE(scan([noisy], m1, 0, 1, 5), LiveTable([noisy, m1]))
# write_callback('stop', db[-1]['stop'])
