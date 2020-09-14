
"""
use this code to build new entries for #382 (related to #362)

https://github.com/APS-USAXS/ipython-usaxs/issues/382

updates into files: /share1/AreaDetectorConfig/*_config/attributes.xml

don't forget non-user info for both ESAF & proposal:
    title
    ID
    start time
    end time
    raw (YAML)
"""

def build_unit(unit_num):
    xref = dict(
        last_name = ["lastName", "family name"],
        first_name = ["firstName", "given name"],
        user_id = ["userId", "database user ID"],
        badge_number = ["badgeNumber", "ANL badge number"],
        email = ["email", "email address"],
        institution = ["institution", "institution name"],
        institution_id = ["instId", "APS insitution index ID"],
        pi_flag = ["piFlag", "Principal Investigator?"],
    )
    unit = []
    for k, v in xref.items():
        pvname = f"9idc:bss:proposal:user{unit_num}:{v[0]}"
        entry = (
            '<Attribute'
            f' name="APSBSS_user{unit_num}_{k}"'
            ' type="EPICS_PV"'
            f' source="{pvname}"'
            ' dbrtype="DBR_STRING"'
            f' description="{v[1]}"'
            ' />'
        )
        unit.append(entry)
    return unit

for i in range(9):
    print("\n".join(build_unit(i+1)))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

"""XML
    <Attribute name="BSS_activity"	type="EPICS_PV"	source="9id_bss:activity"	dbrtype="DBR_STRING"     description="Activity code"/>
"""

"""NXuser structure
NXuser (base class)
  address:NX_CHAR
  affiliation:NX_CHAR
  email:NX_CHAR
  facility_user_id:NX_CHAR
  fax_number:NX_CHAR
  name:NX_CHAR
  role:NX_CHAR
  telephone_number:NX_CHAR
"""

"""PVs
esaf.user7.badge_number       9idc:bss:esaf:user7:badgeNumber
esaf.user7.email              9idc:bss:esaf:user7:email
esaf.user7.first_name         9idc:bss:esaf:user7:firstName
esaf.user7.last_name          9idc:bss:esaf:user7:lastName
proposal.user7.badge_number   9idc:bss:proposal:user7:badgeNumber
proposal.user7.email          9idc:bss:proposal:user7:email
proposal.user7.first_name     9idc:bss:proposal:user7:firstName
proposal.user7.institution    9idc:bss:proposal:user7:institution
proposal.user7.institution_id 9idc:bss:proposal:user7:instId
proposal.user7.last_name      9idc:bss:proposal:user7:lastName
proposal.user7.pi_flag        9idc:bss:proposal:user7:piFlag      OFF
proposal.user7.user_id        9idc:bss:proposal:user7:userId
"""
