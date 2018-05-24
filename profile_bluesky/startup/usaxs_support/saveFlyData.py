#!/usr/bin/env python


'''
save EPICS data from USAXS Fly Scan to a NeXus file
'''


import datetime
import os
import sys

# do not warn if the HDF5 library version has changed
# headers are 1.8.15, library is 1.8.16
# THIS SETTING MIGHT BITE US IN THE FUTURE!
os.environ['HDF5_DISABLE_VERSION_CHECK'] = '2'

import h5py
import numpy
import time
from lxml import etree as lxml_etree

# matches IOC for big arrays
os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '1280000'    # was 200000000

import epics                # PyEpics support
from spec2nexus import eznx     # NeXus r/w support using h5py


path = os.path.dirname(__file__)
XML_CONFIGURATION_FILE = os.path.join(path, 'saveFlyData.xml')
XSD_SCHEMA_FILE = os.path.join(path, 'saveFlyData.xsd')

field_registry = {}    # key: node/@label,        value: Field_Specification object
group_registry = {}    # key: HDF5 absolute path, value: Group_Specification object
link_registry = {}     # key: node/@label,        value: Link_Specification object
pv_registry = {}       # key: node/@label,        value: PV_Specification object


class TimeoutException(Exception): pass


def getGroupObjectByXmlNode(xml_node):
    '''locate a Group_Specification object by matching its xml_node'''
    for group_spec_obj in group_registry.values():
        if group_spec_obj.xml_node == xml_node:
            return group_spec_obj
    return None


class Field_Specification(object):
    '''specification of the "field" element in the XML configuration file'''

    def __init__(self, xml_element_node):
        self.xml_node = xml_element_node
        xml_parent_node = xml_element_node.getparent()
        self.group_parent = getGroupObjectByXmlNode(xml_parent_node)
        self.name = xml_element_node.attrib['name']
        self.hdf5_path = self.group_parent.hdf5_path + '/' + self.name

        nodes = xml_element_node.xpath('text')
        if len(nodes) > 0:
            self.text = nodes[0].text.strip()
        else:
            self.text = ''

        self.attrib = {}
        for node in xml_element_node.xpath('attribute'):
            self.attrib[node.attrib['name']] = node.attrib['value']

        field_registry[self.hdf5_path] = self

    def __str__(self):
        try:
            nm = self.hdf5_path
        except:
            nm = 'Field_Specification object'
        return nm


class Group_Specification(object):
    '''specification of the "group" element in the XML configuration file'''

    def __init__(self, xml_element_node):
        self.hdf5_path = None
        self.xml_node = xml_element_node
        self.hdf5_group = None
        self.name = xml_element_node.attrib['name']
        self.nx_class = xml_element_node.attrib['class']

        self.attrib = {}
        for node in xml_element_node.xpath('attribute'):
            self.attrib[node.attrib['name']] = node.attrib['value']

        xml_parent_node = xml_element_node.getparent()
        self.group_children = {}
        if xml_parent_node.tag == 'group':
            # identify our parent
            self.group_parent = getGroupObjectByXmlNode(xml_parent_node)
            # next, find our HDF5 path from our parent
            path = self.group_parent.hdf5_path
            if not path.endswith('/'):
                path += '/'
            self.hdf5_path = path + self.name
            # finally, declare ourself to be a child of that parent
            self.group_parent.group_children[self.hdf5_path] = self
        elif xml_parent_node.tag == 'NX_structure':
            self.group_parent = None
            self.hdf5_path = '/'
        if self.hdf5_path in group_registry:
            msg = "Cannot create duplicate HDF5 path names: " + self.hdf5_path
            raise RuntimeError(msg)
        group_registry[self.hdf5_path] = self

    def __str__(self):
        return self.hdf5_path or 'Group_Specification object'


class Link_Specification(object):
    '''specification of the "link" element in the XML configuration file'''

    def __init__(self, xml_element_node):
        self.xml_node = xml_element_node

        self.name = xml_element_node.attrib['name']
        self.source_hdf5_path = xml_element_node.attrib['source']   # path to existing object
        self.linktype = xml_element_node.get('linktype', 'NeXus')
        if self.linktype not in ('NeXus', ):
            msg = "Cannot create HDF5 " + self.linktype + " link: " + self.hdf5_path
            raise RuntimeError(msg)

        xml_parent_node = xml_element_node.getparent()
        self.group_parent = getGroupObjectByXmlNode(xml_parent_node)
        self.name = xml_element_node.attrib['name']
        self.hdf5_path = self.group_parent.hdf5_path + '/' + self.name

        link_registry[self.hdf5_path] = self

    def make_link(self, hdf_file_object):
        '''make this link in the HDF5 file'''
        source = self.source_hdf5_path      # source: existing HDF5 object
        parent = '/'.join(source.split('/')[0:-1])     # parent: parent HDF5 path of source
        target = self.hdf5_path             # target: HDF5 node path to be created
        parent_obj = hdf_file_object[parent]
        source_obj = hdf_file_object[source]
        eznx.makeLink(parent_obj, source_obj, target)

    def __str__(self):
        try:
            nm = self.label + ' <' + self.pvname + '>'
        except:
            nm = 'Link_Specification object'
        return nm


class PV_Specification(object):
    '''specification of the "PV" element in the XML configuration file'''

    def __init__(self, xml_element_node):
        self.xml_node = xml_element_node
        self.label = xml_element_node.attrib['label']
        if self.label in pv_registry:
            msg = "Cannot use PV label more than once: " + self.label
            raise RuntimeError(msg)
        self.pvname = xml_element_node.attrib['pvname']
        self.pv = None
        aas = xml_element_node.attrib.get('acquire_after_scan', 'false')
        self.acquire_after_scan = aas.lower() in ('t', 'true')

        self.attrib = {}
        for node in xml_element_node.xpath('attribute'):
            self.attrib[node.attrib['name']] = node.attrib['value']

        # identify our parent
        xml_parent_node = xml_element_node.getparent()
        self.group_parent = getGroupObjectByXmlNode(xml_parent_node)

        self.length_limit = xml_element_node.get('length_limit', None)
        if self.length_limit is not None:
            if not self.length_limit.startswith('/'):
                # convert local to absolute reference
                self.length_limit = self.group_parent.hdf5_path + '/' + self.length_limit

        # finally, declare ourself to be a child of that parent
        self.hdf5_path = self.group_parent.hdf5_path + '/' + self.label
        self.group_parent.group_children[self.hdf5_path] = self
        pv_registry[self.hdf5_path] = self

    def __str__(self):
        try:
            nm = self.label + ' <' + self.pvname + '>'
        except:
            nm = 'PV_Specification object'
        return nm


class SaveFlyScan(object):
    '''watch trigger PV, save data to NeXus file after scan is done'''

    trigger_pv = '9idcLAX:USAXSfly:Start'
    trigger_accepted_values = (0, 'Done')
    trigger_poll_interval_s = 0.1
    scantime_pv = '9idcLAX:USAXS:FS_ScanTime'
    creator_version = 'unknown'
    flyScanNotSaved_pv = '9idcLAX:USAXS:FlyScanNotSaved'

    def __init__(self, hdf5_file, config_file = None):
        self.hdf5_file_name = hdf5_file
        path = self._get_support_code_dir()
        self.config_file = config_file or os.path.join(path, XML_CONFIGURATION_FILE)
        self._read_configuration()
        self._prepare_to_acquire()

    def waitForData(self):
        '''wait until the data is ready, then save it'''
        def keep_waiting():
            triggered = self.trigger.get() in self.trigger_accepted_values
            #time_remains = quitting_time >= datetime.datetime.now()
            #if not time_remains:
            #    raise TimeoutException()
            return not triggered
        self.trigger = epics.PV(self.trigger_pv)
        #timeout_s = max(0, epics.caget(self.scantime_pv))
        #quitting_time = datetime.datetime.now() + datetime.timedelta(seconds=(timeout_s+70))
        epics.caput(self.flyScanNotSaved_pv, 1)
        #!# measure amount of time spent in next step and write to a PV
        #!t0 = time.time()
        self.preliminaryWriteFile()        # file is already open, write preliminary data
        #!t1 = time.time()
        #!epics.caput('9idcLAX:float15.DESC', 'preliminaryWriteFile()')
        #!epics.caput('9idcLAX:float15', t1 - t0)
        #!# measure amount of time spent in next step and write to a PV
        #!t0 = time.time()
        while keep_waiting():
            time.sleep(self.trigger_poll_interval_s)
        #!t1 = time.time()
        #!epics.caput('9idcLAX:float16.DESC', 'keep_waiting()')
        #!epics.caput('9idcLAX:float16', t1 - t0)
        #!# measure amount of time spent in next step and write to a PV
        #!t0 = time.time()
        self.saveFile()                    # write the remaining data and close the file
        #!t1 = time.time()
        #!epics.caput('9idcLAX:float17.DESC', 'saveFile()')
        #!epics.caput('9idcLAX:float17', t1 - t0)
        epics.caput(self.flyScanNotSaved_pv, 0)

    def preliminaryWriteFile(self):
        '''write all preliminary data to the file while fly scan is running'''
        for pv_spec in pv_registry.values():
            if pv_spec.acquire_after_scan:
                continue
            value = pv_spec.pv.get()
            if value is [None]:
                value = 'no data'
            if not isinstance(value, numpy.ndarray):
                value = [value]
            else:
                if pv_spec.length_limit and pv_spec.length_limit in pv_registry:
                    length_limit = pv_registry[pv_spec.length_limit].pv.get()
                    if len(value) > length_limit:
                        value = value[:length_limit]

            hdf5_parent = pv_spec.group_parent.hdf5_group
            try:
                ds = eznx.makeDataset(hdf5_parent, pv_spec.label, value)
                self._attachEpicsAttributes(ds, pv_spec.pv)
                eznx.addAttributes(ds, **pv_spec.attrib)
            except Exception as e:
                print("ERROR: pv_spec.label={}, value={}".format(pv_spec.label, value))
                print("MESSAGE: ", e)
                print("RESOLUTION: writing as error message string")
                ds = eznx.makeDataset(hdf5_parent, pv_spec.label, [str(e).encode('utf8')])
                #raise

    def saveFile(self):
        '''write all desired data to the file and exit this code'''
        t = datetime.datetime.now()
        #timestamp = ' '.join((t.strftime("%Y-%m-%d"), t.strftime("%H:%M:%S")))
        timestamp = str(t).split('.')[0]
        f = group_registry['/'].hdf5_group
        eznx.addAttributes(f, timestamp = timestamp)

        # TODO: will len(caget(array)) = NORD or NELM? (useful data or full array)
        for pv_spec in pv_registry.values():
            if not pv_spec.acquire_after_scan:
                continue
            value = pv_spec.pv.get()
            if value is [None]:
                value = 'no data'
            if not isinstance(value, numpy.ndarray):
                value = [value]
            else:
                if pv_spec.length_limit and pv_spec.length_limit in pv_registry:
                    length_limit = pv_registry[pv_spec.length_limit].pv.get()
                    if len(value) > length_limit:
                        value = value[:length_limit]

            hdf5_parent = pv_spec.group_parent.hdf5_group
            try:
                ds = eznx.makeDataset(hdf5_parent, pv_spec.label, value)
                self._attachEpicsAttributes(ds, pv_spec.pv)
                eznx.addAttributes(ds, **pv_spec.attrib)
            except Exception as e:
                print("ERROR: ", pv_spec.label, value)
                print("MESSAGE: ", e)
                print("RESOLUTION: writing as error message string")
                ds = eznx.makeDataset(hdf5_parent, pv_spec.label, [str(e).encode('utf8')])
                #raise

        # as the final step, make all the links as directed
        for _k, v in link_registry.items():
            v.make_link(f)

        f.close()    # be CERTAIN to close the file

    def _read_configuration(self):
        # first, validate configuration file against an XML Schema
        path = self._get_support_code_dir()
        xml_schema_file = os.path.join(path, XSD_SCHEMA_FILE)
        xmlschema_doc = lxml_etree.parse(xml_schema_file)
        xmlschema = lxml_etree.XMLSchema(xmlschema_doc)

        config = lxml_etree.parse(self.config_file)
        if not xmlschema.validate(config):
            # XML file is not valid, let lxml report what is wrong as an exception
            #log = xmlschema.error_log    # access more details
            xmlschema.assertValid(config)   # basic exception report

        # safe to proceed parsing the file
        root = config.getroot()
        if root.tag != "saveFlyData":
            raise RuntimeError("XML file not valid for configuring saveFlyData")

        self.creator_version = root.attrib['version']

        node = root.xpath('/saveFlyData/triggerPV')[0]
        self.trigger_pv = node.attrib['pvname']
        acceptable_values = (int(node.attrib['done_value']), node.attrib['done_text'])
        self.trigger_accepted_values = acceptable_values

        node = root.xpath('/saveFlyData/timeoutPV')[0]
        self.timeout_pv = node.attrib['pvname']

        # initial default value set in this code
        # pull default poll_interval_s from XML Schema (XSD) file
        xsd_root = xmlschema_doc.getroot()
        xsd_node = xsd_root.xpath("//xs:attribute[@name='poll_time_s']", # name="poll_time_s"
                              namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})

        # allow XML configuration to override trigger_poll_interval_s
        default_value = float(xsd_node[0].get('default', self.trigger_poll_interval_s))
        self.trigger_poll_interval_s = node.get('poll_time_s', default_value)

        nx_structure = root.xpath('/saveFlyData/NX_structure')[0]
        for node in nx_structure.xpath('//group'):
            Group_Specification(node)

        for node in nx_structure.xpath('//field'):
            Field_Specification(node)

        for node in nx_structure.xpath('//PV'):
            PV_Specification(node)

        for node in nx_structure.xpath('//link'):
            Link_Specification(node)

    def _get_support_code_dir(self):
        return os.path.split(os.path.abspath(__file__))[0]

    def _prepare_to_acquire(self):
        '''connect to EPICS and create the HDF5 file and structure'''
        # connect to EPICS PVs
        for pv_spec in pv_registry.values():
            pv_spec.pv = epics.PV(pv_spec.pvname)

        # create the file
        for key, xture in sorted(group_registry.items()):
            if key == '/':
                # create the file and internal structure
                f = eznx.makeFile(self.hdf5_file_name,
                  # the following are attributes to the root element of the HDF5 file
                  file_name = self.hdf5_file_name,
                  creator = __file__,
                  creator_version = self.creator_version,
                  creator_config_file=self.config_file,
                  HDF5_Version = h5py.version.hdf5_version,
                  h5py_version = h5py.version.version,
                )
                xture.hdf5_group = f
            else:
                hdf5_parent = xture.group_parent.hdf5_group
                xture.hdf5_group = eznx.makeGroup(hdf5_parent, xture.name, xture.nx_class)
            eznx.addAttributes(xture.hdf5_group, **xture.attrib)

        for field in field_registry.values():
            if isinstance(field.text, type(u"unicode")):
                field.text = field.text.encode('utf8')
            try:
                ds = eznx.makeDataset(field.group_parent.hdf5_group, field.name, [field.text])
            except Exception as _exc:
                msg = "problem with field={}, text={}, exception={}".format(
                    field.name, field.text, _exc
                )
                raise Exception(msg)
            eznx.addAttributes(ds, **field.attrib)

    def _attachEpicsAttributes(self, node, pv):
        '''attach common attributes from EPICS to the HDF5 tree node'''
        pvname = os.path.splitext(pv.pvname)[0]
        desc = epics.caget(pvname+'.DESC') or ''
        eznx.addAttributes(node,
          epics_pv = pv.pvname.encode('utf8'),
          units = (pv.units or '').encode('utf8'),
          epics_type = pv.type,
          epics_description = desc.encode('utf8'),
        )


def get_CLI_options():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('data_file',
                    action='store',
                    help="/path/to/new/hdf5/data/file")

    parser.add_argument('xml_config_file',
                    action='store',
                    help="XML configuration file")

    return parser.parse_args()


def main():
    cli_options = get_CLI_options()
    dataFile = cli_options.data_file
    path = os.path.split(dataFile)[0]
    if len(path) > 0 and not os.path.exists(path):
        msg = 'directory for that file does not exist: ' + dataFile
        raise RuntimeError(msg)

    if os.path.exists(dataFile):
        msg = 'file exists: ' + dataFile
        raise RuntimeError(msg)

    configFile = cli_options.xml_config_file
    if not os.path.exists(configFile):
        msg = 'config file not found: ' + configFile
        raise RuntimeError(msg)

    sfs = SaveFlyScan(dataFile, configFile)
    try:
        sfs.waitForData()
    except TimeoutException as _exception_message:
        print("exiting because of timeout!!!!!!!")
        sys.exit(1)     # exit silently with error, 1=TIMEOUT
    print('wrote file: ' + dataFile)


def developer():
    sfs = SaveFlyScan('test.h5', XML_CONFIGURATION_FILE)
    sfs.waitForData()

if __name__ == '__main__':
    main()  # production system
    # developer()


'''
cd /home/beams/USAXS/Documents/eclipse/USAXS/tools
/bin/rm test.h5
caput 9idcLAX:USAXSfly:Start 0
/APSshare/anaconda/x86_64/bin/python ./saveFlyData.py ./test.h5 ./saveFlyData.xml
/APSshare/anaconda/x86_64/bin/python ~/bin/h5toText.py ./test.h5
'''