from ophyd.scaler import ScalerCH
scaler0 = ScalerCH('9idcLAX:vsc:c0', name='scaler0')
# chan01 : sec (seconds)
# chan02 : I0 (I0)
# chan03 : I00 (I00)
# chan04 : upd2 (USAXS_PD)
# chan05 : trd (TR_diode)
# chan06 : I000 (I000)
scaler0.channels.read_attrs = ['chan01', 'chan02', 'chan03', 'chan04', 'chan05', 'chan06']
BotMS = EpicsMotor('9ida:m46', name='BotMS')  # MonoSl_bot
InbMS = EpicsMotor('9ida:m43', name='InbMS')  # MonoSl_inb
OutMS = EpicsMotor('9ida:m44', name='OutMS')  # MonoSl_out
TopMS = EpicsMotor('9ida:m45', name='TopMS')  # MonoSl_top
a2rp = EpicsMotor('9idcLAX:pi:c0:m1', name='a2rp')  # USAXS.a2rp
ar = EpicsMotor('9idcLAX:aero:c0:m1', name='ar')  # ar
art = EpicsMotor('9idcLAX:m58:c1:m3', name='art')  # ART50-100
asr = EpicsMotor('9idcLAX:xps:c0:m6', name='asr')  # asr
asrp = EpicsMotor('9idcLAX:pi:c0:m4', name='asrp')  # USAXS.asrp
ast = EpicsMotor('9idcLAX:xps:c0:m4', name='ast')  # ast
asy = EpicsMotor('9idcLAX:m58:c1:m4', name='asy')  # asy
ax = EpicsMotor('9idcLAX:m58:c0:m5', name='ax')  # ax
ay = EpicsMotor('9idcLAX:aero:c1:m1', name='ay')  # ay
az = EpicsMotor('9idcLAX:m58:c0:m7', name='az')  # az
camy = EpicsMotor('9idcLAX:m58:c1:m7', name='camy')  # cam_y
dx = EpicsMotor('9idcLAX:m58:c2:m3', name='dx')  # dx
dy = EpicsMotor('9idcLAX:aero:c2:m1', name='dy')  # dy
gslbot = EpicsMotor('9idcLAX:mxv:c0:m6', name='gslbot')  # GSlit_bot
gslinb = EpicsMotor('9idcLAX:mxv:c0:m4', name='gslinb')  # GSlit_inb
gslitx = EpicsMotor('9idcLAX:m58:c1:m5', name='gslitx')  # Gslit_X
gslity = EpicsMotor('9idcLAX:m58:c0:m6', name='gslity')  # Gslit_Y
gslout = EpicsMotor('9idcLAX:mxv:c0:m3', name='gslout')  # GSlit_outb
gsltop = EpicsMotor('9idcLAX:mxv:c0:m5', name='gsltop')  # GSlit_top
m2rp = EpicsMotor('9idcLAX:pi:c0:m2', name='m2rp')  # USAXS.m2rp
mr = EpicsMotor('9idcLAX:aero:c3:m1', name='mr')  # mr
msr = EpicsMotor('9idcLAX:xps:c0:m5', name='msr')  # msr
msrp = EpicsMotor('9idcLAX:pi:c0:m3', name='msrp')  # USAXS.msrp
mst = EpicsMotor('9idcLAX:xps:c0:m3', name='mst')  # mst
msx = EpicsMotor('9idcLAX:m58:c1:m1', name='msx')  # msx
msy = EpicsMotor('9idcLAX:m58:c1:m2', name='msy')  # msy
mx = EpicsMotor('9idcLAX:m58:c0:m2', name='mx')  # mx
my = EpicsMotor('9idcLAX:m58:c0:m3', name='my')  # my
pin_x = EpicsMotor('9idcLAX:mxv:c0:m1', name='pin_x')  # pin_x
pin_y = EpicsMotor('9idcLAX:mxv:c0:m8', name='pin_y')  # pin_y
pin_z = EpicsMotor('9idcLAX:mxv:c0:m2', name='pin_z')  # pin_z
sx = EpicsMotor('9idcLAX:m58:c2:m1', name='sx')  # sx
sy = EpicsMotor('9idcLAX:m58:c2:m2', name='sy')  # sy
tcam = EpicsMotor('9idcLAX:m58:c1:m6', name='tcam')  # tcam
tens = EpicsMotor('9idcLAX:m58:c1:m8', name='tens')  # Tension
un0 = EpicsMotor('9idcLAX:m58:c0:m1', name='un0')  # unused0
un19 = EpicsMotor('9idcLAX:m58:c2:m4', name='un19')  # un19
un30 = EpicsMotor('9idcLAX:mxv:c0:m7', name='un30')  # unused30
un36 = EpicsMotor('9idcLAX:xps:c0:m1', name='un36')  # unused36
un37 = EpicsMotor('9idcLAX:xps:c0:m2', name='un37')  # unused37
un42 = EpicsMotor('9idcLAX:xps:c0:m7', name='un42')  # unused42
un43 = EpicsMotor('9idcLAX:xps:c0:m8', name='un43')  # unused43
un45 = EpicsMotor('9idcLAX:mxv:c1:m1', name='un45')  # un45
un46 = EpicsMotor('9idcLAX:mxv:c1:m2', name='un46')  # un46
un47 = EpicsMotor('9idcLAX:mxv:c1:m3', name='un47')  # un47
un48 = EpicsMotor('9idcLAX:mxv:c1:m4', name='un48')  # un48
un49 = EpicsMotor('9idcLAX:mxv:c1:m5', name='un49')  # un49
un50 = EpicsMotor('9idcLAX:mxv:c1:m6', name='un50')  # un50
un51 = EpicsMotor('9idcLAX:mxv:c1:m7', name='un51')  # un51
un52 = EpicsMotor('9idcLAX:mxv:c1:m8', name='un52')  # un52
un7 = EpicsMotor('9idcLAX:m58:c0:m8', name='un7')  # unused7
uslhap = EpicsMotor('9idcLAX:m58:c2:m8', name='uslhap')  # uslithorap
uslhcen = EpicsMotor('9idcLAX:m58:c2:m6', name='uslhcen')  # uslithorcen
uslvap = EpicsMotor('9idcLAX:m58:c2:m7', name='uslvap')  # uslitverap
uslvcen = EpicsMotor('9idcLAX:m58:c2:m5', name='uslvcen')  # uslitvercen
waxsx = EpicsMotor('9idcLAX:m58:c0:m4', name='waxsx')  # WAXS X
append_wa_motor_list(BotMS, InbMS, OutMS, TopMS, a2rp, ar, art, asr)
append_wa_motor_list(asrp, ast, asy, ax, ay, az, camy, dx)
append_wa_motor_list(dy, gslbot, gslinb, gslitx, gslity, gslout, gsltop, m2rp)
append_wa_motor_list(mr, msr, msrp, mst, msx, msy, mx, my)
append_wa_motor_list(pin_x, pin_y, pin_z, sx, sy, tcam, tens, un0)
append_wa_motor_list(un19, un30, un36, un37, un42, un43, un45, un46)
append_wa_motor_list(un47, un48, un49, un50, un51, un52, un7, uslhap)
append_wa_motor_list(uslhcen, uslvap, uslvcen, waxsx)
