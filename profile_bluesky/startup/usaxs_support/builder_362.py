
"""
use this code to build new entries for #362

https://github.com/APS-USAXS/ipython-usaxs/issues/362
"""

def build_unit(unit_num):
    xref = dict(
        last_name = "lastName",
        first_name = "firstName",
        user_id = "userId",
        badge_number = "badgeNumber",
        email = "email",
        institution = "institution",
        institution_id = "instId",
        pi_flag = "piFlag",
    )
    unit = []
    unit.append(f'<group name="user{unit_num}" class="NXuser">')
    unit.append('    <attribute name="canSAS_class" value="SASuser" />')
    for k, v in xref.items():
        pvname = f"9idc:bss:proposal:user{unit_num}:{v}"
        unit.append(f'    <PV label="{k}" pvname="{pvname}" string="true" />')
    unit.append('</group>')
    return unit

for i in range(9):
    print("\n".join(build_unit(i+1)))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

"""XML
                <group name="user" class="NXuser">
                    <attribute name="canSAS_class" value="SASuser" />
                    <PV label="name" pvname="9idcLAX:UserName" />
                </group>
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
