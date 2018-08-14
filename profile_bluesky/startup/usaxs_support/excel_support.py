# -*- coding: utf-8 -*-

"""
support for Excel files, treat them like databases
"""


from collections import OrderedDict
import datetime
import glob
import logging
import math
import os
import pandas
import uuid

from encode_decode import text_encode, to_unicode_or_bust


HOME_PATH = os.path.dirname(__file__)
logger = logging.getLogger(__name__)


class ExcelDatabaseFile(object):
    
    EXCEL_FILE = None       # subclass MUST define
    # EXCEL_FILE = os.path.join("abstracts", "index of abstracts.xlsx")
    LABELS_ROW = 3

    def __init__(self):
        self.db = OrderedDict()
        if self.EXCEL_FILE is None:
            raise ValueError("subclass must define EXCEL_FILE")
        self.fname = os.path.join(HOME_PATH, self.EXCEL_FILE)
        self.parse()
        
    def handle_single_entry(self, entry):       # subclass MUST override
        raise NotImplementedError("subclass must override handle_single_entry() method")

    def handleExcelRowEntry(self, entry):       # subclass MUST override
        raise NotImplementedError("subclass must override handleExcelRowEntry() method")

    def parse(self, labels_row_num=None, data_start_row_num=None):
        labels_row_num = labels_row_num or self.LABELS_ROW
        xl = pandas.read_excel(self.fname, sheet_name=0, header=None)
        labels = list(xl.iloc[labels_row_num,:])
        data_start_row_num = data_start_row_num or labels_row_num+1
        grid = xl.iloc[data_start_row_num:,:]
        # grid is a pandas DataFrame
        # logger.info(type(grid))
        # logger.info(grid.iloc[:,1])
        for row_number, _ignored in enumerate(grid.iloc[:,0]):
            row_data = grid.iloc[row_number,:]
            entry = {}
            for _col, label in enumerate(labels):
                entry[label] = self._getExcelColumnValue(row_data, _col)
                self.handle_single_entry(entry)
            self.handleExcelRowEntry(entry)

    def _getExcelColumnValue(self, row_data, col):
        v = row_data.values[col]
        if self._isExcel_nan(v):
            v = None
        else:
            v = to_unicode_or_bust(v)
            if isinstance(v, unicode):
                v = v.strip()
        return v
    
    def _isExcel_nan(self, value):
        if not isinstance(value, float):
            return False
        return math.isnan(value)


class AbstractDB(ExcelDatabaseFile):
    """
    metadata about abstracts from the Excel file
    """

    EXCEL_FILE = os.path.join("abstracts", "index of abstracts.xlsx")
    full_names = {}
    initiatives = [
        u'biomolecular',
        u'catalysis',
        u'combined techniques',
        u'dynamics, kinetics, and time-resolved',
        u'education',
        u'energy storage & production',
        u'grazing incidence',
        u'magnetic materials',
        u'materials science',
        u'modeling and data analysis',
        u'polymers, colloids',
        u'renewable energy',
        u'soft-matter self-assembly',
        u'Schaefer Symposium',
        u'contrast variation',
        u'data formats',
        u'instrumentation',
        u'other',
        ]

    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        if entry["sort name"] is None:
            return
        entry["sort name"] += "! " + entry["Full Name"]      # this should make them unique
        entry["sort name"] = text_encode(entry["sort name"].replace(",", "+"))

        initiatives = []
        for k in self.initiatives:
            if entry[k] is not None:
                if k == u"Schaefer Symposium":
                    entry["format"] = u"Schaefer Symposium"
                if k in (u'energy storage & production', u'renewable energy',):
                    k = u"energy"
                elif k in (u'data formats',):
                    k = u"instrumentation"
                if k not in initiatives:
                    initiatives.append(k)
        for k in self.initiatives:
            if k in entry:
                del entry[k]
        entry[u"initiatives"] = initiatives
        
        if entry["format"].strip().lower() == "oral":
            form = "oral"
            if entry["invited?"].strip().lower() == "yes":
                form = "plenary"
        elif entry["format"] == u"Schaefer Symposium":
            form = entry["format"]
        else:
            form = "poster"
        entry["format"] = form
        
        # cross-reference: sort name to Full Name
        if entry["sort name"] not in self.full_names:
            self.full_names[entry["sort name"]] = entry["Full Name"]

        k = entry["abstract number"]
        msg = "abstract {}, sort name {}".format(k, entry["sort name"])
        logger.info(msg)
        self.db[k] = entry

    def find_pdf(self, anum):
        """
        find the PDF file given the abstract number
        """
        path = os.path.join(HOME_PATH, "abstracts")
        pattern = os.path.join(path, anum + "*.pdf")
        results = glob.glob(pattern)
        if len(results) >= 1:
            if len(results) > 1:
                msg = "more than one choice for abstract {}: {}"
                msg = msg.format(anum, results)
                logger.error(msg)
            return results[0]


class AssignmentsDB(ExcelDatabaseFile):
    """
    metadata about assignments from the Excel file
    """
    EXCEL_FILE = os.path.join("resources", "assignments.xlsx")
        
    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        if entry["description"] is None or entry["iso8601"] is None:
            return
        
        entry["plenary"] = entry["plenary"] is not None
        
        key = entry["code"]
        if key in self.db:
            msg = "Assignments code %s is already defined." % key
            msg += "  Description: " + entry["description"]
            raise KeyError(msg)
        self.db[key] = entry
    
    def getByDatetime(self, start, end):
        """
        return list of all assignments between start and end times
        
        start and end are either datetime.datetime instances or strings in ISO8601 format
        """
        def to_datetime(v):
            if isinstance(v, datetime.datetime):
                return v
            elif isinstance(v, basestring):
                return datetime.datetime.strptime(v, "%Y-%m-%d %H:%M")    # ISO8601 format
            msg = "Argument must be datetime or unicode, given " + str(type(v))
            raise TypeError(msg)
            
        start = to_datetime(start)
        end = to_datetime(end)
        events = [ev  for ev in self.db.values() if start <= ev["iso8601"] < end]
        
        def getkey(ev):
            return "{}-{}".format(ev["iso8601"], ev["room"])
        
        return sorted(events, key=getkey)


class RegistrantBase(object):
    
    def __init__(self, entry, *args):
        self.full_name = entry["Full Name"]
        self.email = entry["Email Address"]
        self.affiliation = entry["Company"]
        self.allergies = entry["Food Allergies"] or ""
        self.needs_visa_letter = (entry["Require VISA"] or "").strip().lower() in ('yes',)
        self.registration = entry["Event Registration"].strip().lower() in ('yes',)
        self.event_ticket_for_what = entry["Event Ticket"].strip().lower() in ('yes',)
        self.banquet = entry["Banquet Dinner"].strip().lower() in ('yes',)
        self.online_payments = entry["Online Payments"]
        self.parse(entry, *args)
        
    def parse(self, entry, *args):
        raise NotImplementedError("must implement in subclass")
    
    def __str__(self, *args, **kwargs):
        t = [
            '{}="{}"'.format("full_name", self.full_name)
            ]
        
        s = "{}({})".format(self.__class__.__name__, ", ".join(t))
        return s


class RegisteredAttendee(RegistrantBase):

    def parse(self, entry, *args):
        self.guests = []


class RegisteredGuest(RegistrantBase):

    def parse(self, event, *args):
        self.host = args[0]
        self.host.guests.append(self)


class RegisterDB(ExcelDatabaseFile):
    """
    metadata about assignments from the Excel file
    """
    EXCEL_FILE = os.path.join("resources", "registrations.xlsx")
    LABELS_ROW = 0
    email_by_name = {}   # key: full name, value: email
    unhosted = {}       # guests who appear in .xls file before their host

    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        if entry["Invitee/Guest"] is None:
            return
        elif entry["Invitee/Guest"] == "Invitee":
            person = RegisteredAttendee(entry)
            self.db[person.email] = person

            if person.full_name in self.email_by_name:
                raise KeyError("{} is already known!".format(person.full_name))
            self.email_by_name[person.full_name] = person.email
            
            guests_found = []
            for uid, guest in self.unhosted.items():
                if person.full_name == guest["Primary Registrant (Guest of)"]:
                    RegisteredGuest(guest, person)
                    guests_found.append(uid)
            for uid in guests_found:
                del self.unhosted[uid]

        elif entry["Invitee/Guest"] == "Guest":
            host_name = entry["Primary Registrant (Guest of)"]
            host_email = self.email_by_name.get(host_name)
            if host_email is None:
                k = uuid.uuid4()
                self.unhosted[k] = entry
            else:
                person = RegisteredGuest(entry, self.db[host_email])
        else:
            msg = "Unexpected Invitee/Guest value: {}".format(entry["Invitee/Guest"])
            raise ValueError(msg)


class PracticalMattersDB(ExcelDatabaseFile):
    """
    content for Practical Matters section from the Excel file
    """
    EXCEL_FILE = os.path.join("resources", "practical matters.xlsx")

    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        # key = "key %03d" % len(self.db)
        # key = uuid.uuid4()
        key = entry["subject"]
        entry["keep"] = entry["keep"].lower() in ("yes", )
        self.db[key] = entry


class ExhibitorsDB(ExcelDatabaseFile):
    """
    content for Exhibitors, vendors, and Sponsors from the Excel file
    """
    EXCEL_FILE = os.path.join("resources", "exhibitors.xlsx")
    LABELS_ROW = 2

    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        key = entry["Name"]
        self.db[key] = entry


class SessionsDB(ExcelDatabaseFile):
    """
    about the Session organizers from the Excel file
    """
    EXCEL_FILE = os.path.join("resources", "session-organizers.xlsx")
    LABELS_ROW = 1

    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        # key = "key %03d" % len(self.db)
        key = entry["Abbrev"]
        self.db[key] = entry


class FeaturedSpeakersDB(ExcelDatabaseFile):
    """
    about the Featured Speakers from the Excel file
    """
    EXCEL_FILE = os.path.join("resources", "featured-speakers.xlsx")
    LABELS_ROW = 2

    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        # key = "key %03d" % len(self.db)
        key = entry["key"]
        self.db[key] = entry


class FinancialSupportDB(ExcelDatabaseFile):
    """
    about the Financial Support from the Excel file
    """
    EXCEL_FILE = os.path.join("resources", "financial-support", "Applications for support.xlsx")
    LABELS_ROW = 5

    def handle_single_entry(self, entry):
        pass

    def handleExcelRowEntry(self, entry):
        # key = "key %03d" % len(self.db)
        key = entry["index"]
        self.db[key] = entry


def developer():
    registrants = RegisterDB()
    for guest in registrants.unhosted.values():
        print("Unhosted: {}".format(guest))
    assert(len(registrants.unhosted) == 0)
    abstracts = AbstractDB()
    assignments = AssignmentsDB()
    faq = PracticalMattersDB()
    organizers = SessionsDB()
    
    for abstract in abstracts.db.values():
        email1 = registrants.db.get(abstract["email"])
        email2 = registrants.db.get(abstract["email2"])
        attendee = email1 or email2
        registered = attendee is not None
        if registered:
            # show abstracts
            # with emails that match on the list of registrants
            print("{}, {} <{}>".format(
                abstract["abstract number"], 
                abstract["Full Name"].encode('utf8'), 
                attendee.email))


if __name__ == "__main__":
    developer()
