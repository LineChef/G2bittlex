"""Bittle X Pi add-on rev 0.24: one-piece body with a slide-on top panel.

Frame = the robot frame of the platform (bittle_platform/interface.py):
  X = lateral (+X = robot right), Y = up, Z = length (-Z = head end). mm.
The parts are designed in a mirror of it (X turned over, see MIRROR_X); every output is in the robot frame.
Left and right below are on the robot.

Parts
  cover_pegs : the platform (bittle_platform/): Petoi cover, unchanged, plus 4 pegs.
  pod_body   : a rounded box (squircle plan, vertical walls, flat floor). The floor is the platform
               mount plate: teardrop keyholes drop over the pegs 7 mm behind the locked place,
               slide forward, click. To remove it, slide it 7 mm rearward and lift it.
               The floor is flat: it does not follow the robot, so the cover and the pegs stay in view.
               Inside, every part goes in from the top: the mic (front wall), the Pi Zero 2 W +
               PiSugar S stack on its long edge (ports up, over the robot center, header to the left), the
               speaker (rear, sound to the rear grille) and the NS4168 amp (right gallery, under two nubs).
               The BiBoard header comes up through a notch in the floor, at the front of the left well.
  pod_panel  : the top, with the soft top edge and openings shaped to the plug bodies. It goes down 5 mm
               behind its place and slides forward: hooks go under lugs in the front and side walls, and
               a latch tongue at the rear clicks over a rib. Forks under the panel hold the stack,
               the speaker and the amp down. A spring tongue over the PiSugar button is a large button.
  pod_button : the button cap on the tongue.
  pod_camera_mount : turns into a round socket in the panel (a twist lock, lens forward or to the rear) and holds the
               Petoi AI Vision Module vertical.
  pod_camera_base_low, pod_camera_cradle_low : the head-off mount (optional): the camera lower, in front of the body.
Order: fit the platform cover, click the empty body on, put the parts in, plug in the wires, put the
button cap into the panel, slide the panel on, turn the camera mount into its socket.
Print: no supports (print_orient() has the orientation of each part).
"""
import math
import os
import sys

import numpy as np
import manifold3d as m3
from build123d import Box, Cylinder, Pos, Rot, export_stl

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))            # the folder that holds bittle_platform/
from bittle_platform import interface as PI          # platform v3.1: cover, pegs, keyholes
REF = os.path.join(ROOT, "reference")                # vendor models (Pi Zero)
PREF = os.path.join(os.path.dirname(ROOT), "bittle_platform", "reference")   # Petoi robot parts
OUT = os.path.join(ROOT, "stl")

# Design frame: the robot frame with X turned over (a mirror). On the robot the BiBoard header is at the front left
# (platform v3.2). In the design frame it is at the front right, so the parts keep the sides of rev 0.21. The stack
# and the amp are turned on the robot; in the design frame that is a mirror of their models (STAND, the amp layout). The platform and the robot come in turned over; main() turns every output back to the robot frame.
MIRROR_X = np.diag([-1.0, 1, 1, 1])[:3, :]


def flip_x(M):
    """Design frame <-> robot frame (the same mirror both ways)."""
    return M.transform(MIRROR_X)


def flip_tris(t):
    m = t.copy()
    m[:, :, 0] *= -1
    return m[:, ::-1, :]

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------
COVER_STL = PI.COVER_STL
COVER_TOP = PI.COVER_TOP
COVER_END_Z = 36.95
HUG_GAP = 0.4

# Body: a squircle plan (|x/a|^n corners), the same outline from the floor to the top.
A = 35.6                    # half width: as wide as the robot cover shell (X +-35.62)
A_LOW = 29.6                # half width at the floor: the rear legs clear the bottom edges when they swing back
STEP_Y = (30.0, 36.0)       # a 45 deg chamfer from A_LOW out to A (it prints floor down without supports)
Z0, Z1 = -37.8, 56.2        # front and rear faces
R_PLAN, NEXP = 13.0, 5.0    # plan corner size and squircle exponent
# 2.0 mm: with the Cura offsets of the body profile (xy 0.144, holes 0.292) the slicer sees 1.996 mm, 4 full lines
# of 0.5 mm. At 1.8 mm it saw 3.57 lines and changed between 3 and 4 lines along the wall.
WALL = 2.0
IN_A, ZF_IN, ZR_IN = A - WALL, Z0 + WALL, Z1 - WALL     # inner faces: 33.6, -35.8, 54.2
IN_A_LOW = A_LOW - WALL                                 # 27.6: the inner face below the chamfer
FLOOR_Y0, FLOOR_Y1 = PI.MOUNT_Y0, PI.MOUNT_Y1          # the floor is the platform mount plate
SEAM = 57.2                 # top of the body walls = bottom of the panel
TOP = 63.2                  # panel top: 0.3 over the highest port
RT = 4.0                    # round on the top edge; the last 45 deg of it is a chamfer (the bed edge in the print)
PANEL_T = 1.6
PANEL_IN = TOP - PANEL_T    # 61.6, underside of the panel top

# Pegs (on the cover) and keyholes (in the floor): platform interface v3.1
PEGS = PI.PEGS
SLIDE = PI.SLIDE            # the body drops on SLIDE rearward (+Z) of its place, then slides forward (-Z) to lock
DET = PI.DET
# No part may stand on the floor over a peg, its slide path or its click beams below this Y.
KEEP_Y = PI.HEAD_CLEAR_Y + 0.1


def keep_zone(px, pz):
    """Floor area of one keyhole: the drop-in hole, the slot, the click beams. (x0, x1, z0, z1)"""
    return (px - 5.6, px + 5.6, pz - SLIDE - PI.PEG_HEAD_D / 2 - 1.5, pz + PI.tip_len(PI.PEG_HEAD_D, PI.HEAD_TIP_DEG) + 0.6)


# Pi Zero 2 W + PiSugar S (1200 mAh) stack, on its long edge: the boards are vertical (normal +X),
# the ports and the PiSugar controls are up, the GPIO header is at the bottom with the Dupont plugs to
# the right (+X, the design frame). The SD card end is at the rear (rev 0.22: the stack of rev 0.21 turned
# end for end, so the Pi header faces the BiBoard). The models are first put in the flat frame of rev 0.15
# (FLAT_*), then turned with STAND. Places on the boards are given as distances from the SD end (sd_z).
FLAT_GPIO_X, FLAT_Z_CSI, FLAT_DY = -16.5, -16.0, 45.0
FLAT_Z_SD = FLAT_Z_CSI + 65.0
# The stack sits STACK_DX right of center, so the battery is nearer the center line. The Pi plugs end at X 18.0.
STACK_DX = 4.9
PI_PCB_TOP_X = 1.5 + STACK_DX              # the Pi component face
STACK_Y0 = 30.0                            # GPIO edge of the boards (2.5 over the floor)
STACK_ZF = -30.5                           # CSI end of the boards (front); the CSI connector stands 0.9 in front of it
STACK_ZR = STACK_ZF + 65.0                 # SD end (rear)
ZSD = STACK_ZR


def sd_z(a, b):
    """The span a..b mm from the SD end of the boards, as (z0, z1)."""
    return (ZSD - b, ZSD - a)


STAND = np.array([[0, 1, 0, PI_PCB_TOP_X - (FLAT_DY + 0.8)],
                  [1, 0, 0, STACK_Y0 - FLAT_GPIO_X],
                  [0, 0, 1, ZSD - FLAT_Z_SD],
                  [0, 0, 0, 1]], dtype=float)      # a mirror in the design frame: the robot frame turns it back
# A pin-fin heatsink on the SoC of the Pi (user photo). Its size is an estimate: 14 x 14 mm, 6.5 mm high.
HEATSINK = dict(x0=PI_PCB_TOP_X + 1.3, y=(40.0, 54.0), z=sd_z(17.8, 31.8), base=1.5, h=6.5, n=5, pin=1.6)
# PiSugar S: no 3D model from PiSugar. The fit model (pisugar_s_model) is drawn from the PCB drawing in the PiSugar docs
# (docs.pisugar.com, PiSugarS240705.jpg): 65 x 30 mm, the 4 holes of the Pi Zero, the same outline as the PiSugar 2.
# Places on the board: u = mm from the SD end, v = mm from the GPIO edge, h = mm over the part face (toward the cell).
# The places are read from the drawing (about +-0.3 mm). The part heights are estimates, except the USB-C receptacle.
PS_PCB_X = (2.6, 3.6)                      # PCB: part face (cell side) .. Pi face (the place of the PiSugar 2 model PCB)
PS_NUT_X = 5.0                             # the nuts on the Pi face end at the Pi PCB (Pi model: x 5.0)
PS_CELL_GAP = 3.3                          # part face to the cell: over the USB-C receptacle (3.26), on the two discs
# The 1200 mAh cell: 56 x 29 x 10 (PiSugar repo model2/batt-1200; the PiSugar S cell is taken as the same, not measured).
# A metal disc on the board and one on the cell face hold it (photo in the PiSugar docs). Its leads go to the BAT pads
# at the front end (CSI end).
BAT = dict(x=(PS_PCB_X[0] - PS_CELL_GAP - 10.0, PS_PCB_X[0] - PS_CELL_GAP), y=(STACK_Y0 + 0.5, STACK_Y0 + 29.5), z=sd_z(4.5, 60.5))
# Battery bay: the cell is on the PiSugar S, on its edge. Blocks on the floor carry it (0.2 mm under it,
# only where the floor is free: not over the keyholes or the amp cable). Plates from the panel stand along its
# outer face (0.3 mm), with pads over its top edge (0.3 mm): it cannot come off the PiSugar or jump up.
BAT_SUPPORT = dict(x=(-5.8, -1.0), z=[(-14.0, -6.0), (6.0, 20.0), (24.0, 30.0)], gap=0.2)
BAT_CLAMP = dict(gap=0.3, t=1.4, y0=34.5, z=[(-24.2, -17.2), (24.8, 29.5)], pad_x=3.2, pad_t=1.8,
                 pads_z=[(1.3, 6.3)])
PCB_X = (1.5 - 3.96 + STACK_DX, 1.5 + STACK_DX)  # PiSugar PCB back face .. Pi PCB component face (3.96 at the ends, user measurement)
# The user's Pi has a soldered 2x20 male header with Dupont jumpers on it (photos reference/signal-*.jpeg).
HDR_ZC = ZSD - 32.5                        # header center along the board
DUPONT_L = 10.0       # the Dupont housing on a jumper end (user measurement); header pins 11.64 mm long, 2.5 mm plastic
PI_PLUGS = dict(x=(PI_PCB_TOP_X + 0.1, PI_PCB_TOP_X + 0.1 + 2.5 + DUPONT_L), y=(STACK_Y0 + 0.96, STACK_Y0 + 6.04),
                z=(HDR_ZC - 25.4, HDR_ZC + 25.4))     # header plastic 2.5 + plug housings; the model PCB face is 0.1 over PI_PCB_TOP_X
# End posts: one vertical groove for the two PCB ends, the same depth for both boards; the bottom of the groove is
# the stop. The M2.5 screw heads of the stack (3.5 from the board corners) have pockets.
POST = dict(x=(-4.6 + STACK_DX, 4.85 + STACK_DX), top=50.0, clr=0.25, depth=2.15)
POST_SD = (ZSD - POST["depth"] - 0.1, ZSD + 0.75)             # rear post: short in Z; the SD card goes through it
POST_CSI = (STACK_ZF - 1.3, STACK_ZF + 2.4)                   # front post: the CSI connector stands out 0.9 (through it)
SCREW = dict(d=4.6, h=1.8, clr=0.4, inset=3.5)                # M2.5 pan heads on the outer faces of the stack (estimate)
SD = dict(x=(1.3 + STACK_DX, 3.35 + STACK_DX), y=(34.75, 55.25))                    # SD holder on the Pi component face (model) + clearance
SD_CARD = dict(x=(1.3 + STACK_DX, 3.1 + STACK_DX), y=(39.0, 52.0), out=2.9)         # card: 11 wide, about 2.5 out of the holder (not measured)
CSI = dict(x=(0.0 + STACK_DX, 3.05 + STACK_DX), y=(33.5, 56.5), out=1.15)           # CSI connector (model) + clearance

# Ports (from the models): PiSugar USB-C charge port, button, switch; Pi power, data USB, mini-HDMI. All up.
# The Pi power port and the PiSugar charge port are side by side: plug in one of them at a time.
PORT_PLUGS = dict(                 # (x center, z center, x size, z size) of the plug body
    hdmi=(3.25 + STACK_DX, ZSD - 12.65, 8.5, 14.0),
    pi_usb=(2.9 + STACK_DX, ZSD - 41.6, 7.5, 11.0),
    pi_power=(2.9 + STACK_DX, ZSD - 54.1, 7.5, 11.0),
    charge=(PS_PCB_X[0] - 1.63, ZSD - 53.7, 7.5, 12.5),     # USB-C plug body (estimate); the receptacle center is 1.63 over the PCB
)
PORT_TOP = 61.3                    # highest port face
# Port openings in the panel: each one is the plug body + PORT_CLR, with round corners and a 45 deg
# chamfer on the top edge. The Pi power and the PiSugar charge openings join.
PORT_CLR, PORT_R, PORT_CHAMFER = 0.4, 1.0, 0.5
# Forks under the panel over the top edge of the boards (where no port is)
STACK_FORKS = [ZSD - 27.4, ZSD - 4.0]    # z0 of each fork, 2 long: clear of the ports while the panel slides on
FORK = dict(len=2.0, lip=1.85, clr_y=0.1)
# Power switch: the PiSugar S slide switch, its lever out of the board edge (drawing: u 13.0..14.4 at OFF, the end
# at v 29.9; the ON label of the drawing is toward the SD end, not checked on a board). Lever travel about 1.5 mm (estimate, as the PiSugar 2): SW_LEVER is
# the middle of the travel, +-SW_TRAVEL. A window in the panel over it (round corners, a 45 deg chamfer on the top
# edge, like the ports): move the lever with a fingernail.
SW_TRAVEL = 0.75
SW_OFF_U = (13.0, 14.4)
SW_LEVER = dict(x=(PS_PCB_X[0] - 1.25, PS_PCB_X[0] - 0.25), y=(STACK_Y0 + 28.2, STACK_Y0 + 29.9),
                z=sd_z(SW_OFF_U[0] - SW_TRAVEL, SW_OFF_U[1] - SW_TRAVEL))
SW_WIN = dict(x=(-1.0, 2.5), z=(SW_LEVER["z"][0] - SW_TRAVEL - 1.45, SW_LEVER["z"][1] + SW_TRAVEL + 1.45))   # 1.0 web to the HDMI opening
# Button: the PiSugar S side push button, its plunger out of the board edge (drawing: u 42.3..44.5, the end at v 30.5).
PS_BTN_U = (42.3, 44.5)
BTN = dict(x=(-10.5 + STACK_DX, -4.5 + STACK_DX), z=(-11.2, -1.2), t=1.0, slit=0.6,
           cap=(PS_PCB_X[0] - 1.6, PS_PCB_X[0] - 0.4, *sd_z(*PS_BTN_U), STACK_Y0 + 30.5),     # the plunger: x0, x1, z0, z1, top
           arm_x=(-6.5 + STACK_DX, -2.5 + STACK_DX), arm_z=(-9.9, -7.9), gap=0.2, press=0.6)   # the tongue: root at z1, free end at z0
# The button cap (white) presses into a round hole in the tongue: a cross post, its ribs 0.15 over the hole on each
# side, crush into the hole wall (coarse enough for a 0.5 mm nozzle).
KEYCAP = dict(w=5.2, l=5.7, h=1.4, r=1.2, post_d=3.8, rib=1.0, press=0.05, post_h=0.9)   # small holes print about 0.2 under
# Camera: the Petoi AI Vision Module in its Petoi case (reference/AiCamera250116-*.stl, 46.7 x 29.3 x 14.9) stands
# vertical on the panel, lens forward over the head, the USB end (native -X) at the top. It stands on the twist mount
# (TW, below): cx and front_z come from the socket center.
# The mount has two side brackets with lips at the corners of the case and a hook over each top corner (clear of the
# USB port). The brackets spread to let the case in from the top; the hooks snap over its top face. A USB cable goes
# from the USB-C port in the top face of the case to the Pi data USB port, over the panel.
CAM = dict(case_x=(-1.2, 45.55), case_y=(-24.83, 4.47), case_z=(-9.8, 5.1),
           top_y=(-21.6, 1.25),                          # the top (USB) end face of the case, native Y (it is narrower)
           base=dict(chin=3.0, clr=0.15),
           brk=dict(t=2.0, clr=0.25, lip_front=0.8, lip_back=1.35, lip_h=15.0, hook=1.5, gap=0.1),
           usb=(-10.15, -1.6), mass=15.0)                # usb: center of the USB-C port in the top face (native Y, Z; case model)
# Head-off mount: for the robot without its head. The camera stands centered, lower, in front of the body: its rear
# face rear_z, its bottom y0. Two parts, each prints without supports: a base (pod_camera_base_low: the twist pedestal,
# an arm on the panel to the front edge (left of the button, to arm_x1), a chin and a front plate down the front of
# the body, with two dovetail grooves; it prints on its side) and a cradle
# (pod_camera_cradle_low: a floor and the side brackets with the hooks; their rear edges are dovetail tabs that slide
# down into the grooves until the cradle sits on the top of the base; it prints on those rear edges). A 1.75 mm
# filament pin through each side locks the cradle.
# Its USB cable goes up from the top of the case, over the panel, to the Pi data USB port.
CAM_LOW = dict(cx=0.0, rear_z=Z0 - 10.0, y0=20.0, floor_t=2.0, plate=dict(x=19.5, y0=42.0, z=(-41.2, -38.4)), arm_x1=-6.0,
               tab=dict(d=1.4, w0=1.2, w1=2.0, clr=0.1), pin=dict(y=52.0, d=1.75, clr=0.1, x0=13.0))
# Twist mount (rev 0.24): the camera mount locks into a round socket in the panel top, at the old logo place, as far
# toward the center as the port openings allow. The pedestal goes down through the hole; two lugs pass down through
# the keyways, then the mount turns `twist` deg back to the lock: the lugs go under the panel top, a stop under the
# panel ends the turn, and a bump on a spring tab in the panel top drops into a notch in the top of each lug. The tab
# presses the lug down, so the seat ring sits firm on the panel. The lock is the same with the mount turned 180 deg
# (lens to the rear). The panel prints top down, so the tabs bend in their layers. The mount prints on its back end:
# the pedestal, the seat and the lugs have 45 deg rear edges.
TW = dict(c=(-17.6, 13.0), r_hole=9.95, r_neck=9.6, r_lug=13.4, lug_a=18.0, lug_t=1.2, gap=0.15, clr=0.3, twist=-40.0,
          ramp=0.5, notch=0.35, preload=0.2, stop_clr=0.15, cs=0.45, seat_gap=0.15, R_b=18.0, rim=0.6, pocket=1.0, lip=0.8, lip_in=0.8,
          hook_flat=1.5, hook_tip=0.6, seat_side=11.2, lift=0.7, base_t=2.0, base_hx=16.9, base_hw=12.5, base_r=3.0,
          tab=dict(r0=12.0, r1=14.06, free=1.2, root=9.5, slit=0.6, t=1.2), bump=dict(r=(12.05, 13.3), tip=0.2))
# The cone of the camera mount: parallel to the countersink, seat_gap from it; it starts at the pedestal radius.
TW_CONE_Y = TOP - TW["cs"] + (TW["r_neck"] - TW["r_hole"] + TW["seat_gap"] * math.sqrt(2))
TW_TOP = TW_CONE_Y + TW["R_b"] - TW["r_neck"] + TW["rim"]   # top of the round puck
LOW_TOP = TOP + TW["lift"] + TW["base_t"]     # top of the plate of the head-off base
CAM["cx"] = TW["c"][0]
CAM["front_z"] = TW["c"][1] - (CAM["case_z"][1] - CAM["case_z"][0]) / 2
# USB cable (estimates): USB-C plug body 12.0 x 6.5, 18 long over the case; micro-USB plug body 7.5 x 11 (the Pi
# data USB opening), 18 long over the port; cable 3.5 thick, bends R 8 or more.
USB_C = dict(w=12.0, t=6.5, l=18.0)
USB_MICRO_L = 18.0
USB_R, USB_BEND = 1.75, 8.0

# BiBoard 5-pin female header in the cover slot (GND, +5V, TX2, RX2, ..), at the front right in the design frame.
# Straight Dupont plugs.
SLOT = dict(PI.SLOT, x0=-PI.SLOT["x1"], x1=-PI.SLOT["x0"])     # design frame (X turned over)
HDR = dict(PI.HDR, x0=-PI.HDR["x1"], x1=-PI.HDR["x0"])
BB_PLUG = dict(x=(HDR["x0"], HDR["x1"]), y=(HDR["top"], HDR["top"] + DUPONT_L), z=(HDR["z0"], HDR["z1"]))
HDR_NOTCH = dict(x=(23.9, IN_A_LOW + 0.01), z=(HDR["z0"] - SLIDE - 0.8, HDR["z1"] + 0.8))   # floor notch: header + slide

# Speaker: NULLLAB 3 W 4 ohm box speaker (user caliper measurements). Body 27.9 x 30 x 15.2 (X, Y, Z; caliper 15.15).
# Two wings, 3.0 thick, 44.0 across: each one tapers from wing_h high at the body to a round end (wing_r) around its
# screw hole, at the middle of the body height (user photo). It stands at the rear, sound face to the rear grille.
# The two wing ends go down into vertical grooves.
SPK = dict(l=44.0, body_l=27.9, d=31.0, h=15.2, ear_t=3.0, hole_d=2.2, hole_in=3.5, wing_h=13.0, wing_r=3.5)
SPK_ZE = 43.8                              # front face of the ear plate
# The ear plate is at the middle of the body depth (user photo reference/signal-2026-10-15-113357.jpeg):
# the body stands out (h - ear_t) / 2 in front of the ear plate and the same behind it.
SPK_BODY_Z = (SPK_ZE + SPK["ear_t"] / 2 - SPK["h"] / 2, SPK_ZE + SPK["ear_t"] / 2 + SPK["h"] / 2)
SPK_Y0 = FLOOR_Y1 + 0.1
SPK_GROOVE = dict(x_in=20.75, clr=0.25, lip=1.5, top=56.5, clr_y=0.4)

# NS4168 amp board (38.4 x 22.4 x 1.6) on edge in the left gallery, along Z. The PCB is 0.5 from the
# left wall, the parts face the battery (+X). The bottom edge stands in a slot in a bar on the floor.
AMP = dict(t=1.6, l=38.4, h=22.4, comp=10.0)
AMP_X = (-IN_A_LOW + 0.5, -IN_A_LOW + 0.5 + AMP["t"])   # -27.1 .. -25.5, on the floor below the chamfer
AMP_CABLE_X = AMP_X[1] + 2.5                    # the amp cable and the speaker lead leave the plugs here
AMP_Y0 = 28.5
AMP_Z = (-9.0, -9.0 + AMP["l"])                  # I2S 5-pin PH2.0 at the front end, speaker 2-pin PH2.0 and the screw terminal at the rear end
AMP_FORKS = [-1.0]                               # z0 of the panel fork over the amp top edge (2.5 long); the camera socket is over the rest
                                                 # of the amp and the screw terminal is at its rear end (the nubs hold both ends)
AMP_NUBS = [-5.0, 22.0]                          # z0 of the nubs on the wall over the amp top edge (4 long)
# Board layout from the NULLLAB photo (u from the I2S end, v from the edge that the photo shows on top, mm). The PH2.0
# headers are side entry: the plugs go in along the board, from the ends. ph=height of the PH headers over the PCB.
# The board stands upright (user photos): that edge (G, the screw terminal) at the top, the I2S end at the front, the
# parts toward the battery.
AMP_L = dict(ph5=(0.75, 6.8, 3.8, 17.4), ph2=(29.0, 35.7, 9.1, 17.0), term=(29.0, 36.8, 0.75, 7.6), ic=(17.7, 24.0, 7.2, 13.6),
             holes=[(15.2, 2.65), (15.2, 19.3)], hole_d=4.7, ph=5.0, term_h=8.5, plug_out=3.7)

# HiLetgo SPH0645 mic board, 12.45 x 16.12 (user caliper), on the right wall of the robot (-X in the design frame) near
# the front corner, high, port face to the wall (sound holes in the side face). The 6 pins (SEL, LRCL, DOUT, BCLK,
# GND, 3V, 3V lowest) are a straight header along its front 16.12 edge: the Dupont housings point inward, and the
# wires go straight across behind the front wall to the left well. It drops in without tools: its rear edge goes
# down a slot in a post on the wall, its bottom edge into a slotted ledge (45 deg underside), and a fork under the
# panel comes down over its top edge. The board is in front of the amp cable (Z -23.8 and rear), and the housings
# go down behind the front wall lugs.
MIC = dict(w=12.45, l=16.12, t=1.6, z0=-34.2, y0=37.0, hole_d=2.5, hole_in=2.3, pin_in=1.3)   # w along Z, l along Y
MIC_HOLD = dict(gap=2.0, clr=0.15, lip=1.2, depth=1.5)   # wall to PCB, slot clearance, back lip, slot depth on the edges
MIC_X = (-IN_A + MIC_HOLD["gap"], -IN_A + MIC_HOLD["gap"] + MIC["t"])     # PCB face to the wall and back face
MIC_PORT = (MIC["y0"] + MIC["l"] / 2, MIC["z0"] + MIC["w"] / 2)       # (Y, Z); port assumed at the board center (not measured)
MIC_PIN_Z = MIC["z0"] + MIC["pin_in"]
MIC_PIN_Y = [MIC["y0"] + (MIC["l"] - 15.24) / 2 + 1.27 + 2.54 * k for k in range(6)]   # 3V, GND, BCLK, DOUT, LRCL, SEL (bottom up, user photo)
MIC_HDR_X = (MIC_X[1], MIC_X[1] + 2.5)           # header plastic on the back face
MIC_HOUSING_X = (MIC_HDR_X[1], MIC_HDR_X[1] + DUPONT_L)
MIC_HOLES = [(y, MIC["z0"] + MIC["w"] - MIC["hole_in"]) for y in (MIC["y0"] + MIC["l"] - MIC["hole_in"], MIC["y0"] + MIC["hole_in"])]   # (Y, Z): the corner holes (not used)
LONG_L = 150.0        # the mic GND and 3V jumpers are 15 cm (their routes are 102 and 115 mm long)

# Slide lid: the panel goes down 5 mm behind its place, then slides forward 5 mm. 45 deg dovetail hooks under the
# panel go under lugs on the inner faces of the walls: the full straight width of the front wall, and 4.4 long lugs
# at a 10 mm pitch along the side walls (the hooks go down in the gaps). The left wall has no lugs where the amp
# goes in. u = distance in from the inner face of the wall. Every spring in the panel bends along its layers.
LID_SLIDE = 5.0
LID = dict(L=1.5, top=0.6, gap=0.1, gap_y=0.15, bot=54.1, t=1.2, front_x=[(-19.0, -4.5), (15.2, 19.0)], front_gap=0.05,
           hook_len=4.2, lug_len=4.4, side_z={1: [-28.4, 32.0], -1: [-28.0, -18.0, 32.0]})
# Front: no ledge where the mic goes in, and the hooks come down clear of the Pi stack. Right (design frame): no lugs
# over the uart wires (they go in from the top along the wall) and the BiBoard plug (FINGER).
LID_LUG_Y = SEAM - LID["top"] - LID["L"]                 # 55.1: the 45 deg underside of a lug meets the wall here
# The latch: a tongue in the panel top at the rear center, cut free by two slits (root at the front, the rear
# skirt at its free end). Its hook rides over a rib on the rear wall and drops in front of it. To open, lift the
# rear edge at the finger notch and slide the panel rearward. The hook is over the speaker.
LATCH = dict(hw=4.5, slit=0.6, root_z=34.0, rib_hw=3.0, rib_d=1.2, rib_top=59.6, hook_bot=58.9, hook_d=2.0,
             hook_hw=3.5, ramp=1.0, gap=0.05)
# Finger notch in the rear wall under the seam: lift the rear edge of the panel here.
NOTCH = dict(hw=7.0, h=1.5, d=1.0)
# Front-left notch, over the notch in the cover (platform GROVE_NOTCH): a 45 deg chamfer across the front bottom edge
# of the body and an opening in the floor over the BiBoard Grove socket (platform GROVE_PLUG), so a Grove cable can
# come out under the front edge. h = height at the front face. The body has no other cable hole at its base.
FRONT_NOTCH = dict(x=(12.5, 25.5), h=6.0, z1=-26.9)    # z1: rear end of the floor opening over the Grove plug
FRONT_CABLE = dict(x=(14.0, 24.0), y=(FLOOR_Y0, FLOOR_Y0 + 3.5), z=(Z0 - 3.0, Z0 + 2.0))   # cable space (check)
# Grille in the rear face, mic holes in the front face
GRILLE = dict(x=np.arange(-13.5, 13.6, 3.0), y=np.arange(33.0, 51.1, 3.0), d=1.6)

# Wire paths (check(): no printed part and no other electronics in them). Dupont jumper wire is about 1.4 mm.
WIRE_PATHS = {
    "uart: Pi header to BiBoard plug": [dict(x=(25.4, IN_A_LOW - 0.05), y=(39.3, 49.6), z=(-19.5, 23.1)),
                                        dict(x=(19.9, IN_A_LOW - 0.05), y=(31.4, 49.6), z=(16.5, 23.1))],
    "i2s: across the front to the amp": [dict(x=(AMP_CABLE_X - 0.7, AMP_CABLE_X + 0.7), y=(27.6, 45.0), z=(-24.5, -12.1)),
                                         dict(x=(AMP_CABLE_X - 0.7, AMP_CABLE_X + 0.7), y=(27.6, 37.0), z=(ZF_IN + 1.6, -24.5)),
                                         dict(x=(AMP_CABLE_X + 0.7, 11.7), y=(27.6, 37.0), z=(ZF_IN + 1.6, ZF_IN + 3.0)),
                                         dict(x=(11.7, 22.9), y=(27.6, 37.0), z=(-26.7, -25.3))],
    "mic: across the front, rearward in the right well": [dict(x=(MIC_HOUSING_X[1] + 0.5, 21.0), y=(38.2, 53.0), z=(MIC_PIN_Z - 0.7, MIC_PIN_Z + 0.7)),
                                                           dict(x=(22.7, 24.1), y=(38.2, 53.0), z=(-29.5, 24.0))],
    "speaker: amp rear end to the speaker": [dict(x=(AMP_CABLE_X - 1.3, AMP_CABLE_X + 4.7), y=(33.5, 52.0), z=(31.6, 36.2)),
                                             dict(x=(-21.0, -11.0), y=(52.0, 61.0), z=(33.0, 36.2)),
                                             dict(x=(-14.0, -6.0), y=(59.0, 61.0), z=(36.2, 44.0))],
}
WIRE_R = 0.7
# Space for a finger tip over the BiBoard plug (panel off)
FINGER = dict(x=(11.0, IN_A - 0.2), y=(37.0, SEAM), z=(-24.0, -10.5))


def flat_pi():
    """Pi Zero model (PiSugar repo model3 frame) -> the flat frame of rev 0.15."""
    return np.array([[0, 0, 1, FLAT_GPIO_X - 3.08], [0, 1, 0, FLAT_DY - 18.83 - 0.5],
                     [-1, 0, 0, FLAT_Z_SD + 6.89], [0, 0, 0, 1]], dtype=float)


def pisugar_s_model():
    """The PiSugar S fit model in place (see PS_PCB_X): [(sub, label, mesh, color)]. Drawn from the PCB drawing
    in the PiSugar docs; the part heights are estimates, except the USB-C receptacle (3.26)."""
    f0, f1 = PS_PCB_X
    def part(u0, u1, v0, v1, h0, h1):                      # a box on the part face
        return mbox(f0 - h1, f0 - h0, STACK_Y0 + v0, STACK_Y0 + v1, ZSD - u1, ZSD - u0)
    holes = [(u, v) for u in (3.5, 61.5) for v in (3.5, 26.5)]
    pcb = rbox("x", f0, f1, STACK_Y0, STACK_Y0 + 30.0, ZSD - 65.0, ZSD, 2.5)
    pcb -= union([mcyl("x", f0 - 1, f1 + 1, 1.35, STACK_Y0 + v, ZSD - u, 24) for u, v in holes])
    pcb -= rbox("x", f0 - 1, f1 + 1, STACK_Y0 + 7.4, STACK_Y0 + 12.9, ZSD - 4.8, ZSD - 2.2, 1.25)   # the slot at the SD end
    nuts = union([mcyl("x", f1 - 0.01, PS_NUT_X, 2.25, STACK_Y0 + v, ZSD - u, 6) - mcyl("x", f1 - 1, PS_NUT_X + 1, 1.25, STACK_Y0 + v, ZSD - u, 24)
                  for u, v in holes])
    # pogo pins on Pi pins 2, 4, 6 (5V, 5V, GND), 5 (SCL) and 9 (GND), through the board
    pins = union([mcyl("x", f0 - 2.5, PS_NUT_X, 0.6, *pin_yz(n), 16) for n in (2, 4, 6, 5, 9)])
    usb = rbox("y", f0 - 3.26, f0, STACK_Y0 + 23.5, STACK_Y0 + 30.9, ZSD - 53.7 - 4.47, ZSD - 53.7 + 4.47, 1.6)
    sw = part(8.9, 15.8, 25.5, 28.2, 0.0, 1.5) + part(*SW_OFF_U, 28.2, 29.9, 0.25, 1.25)       # power switch, lever at OFF
    btn = part(40.6, 46.2, 26.4, 29.4, 0.0, 2.0) + part(*PS_BTN_U, 29.39, 30.5, 0.4, 1.6)     # side push button + plunger
    auto = part(30.7, 37.6, 20.2, 23.2, 0.0, 1.5) + part(32.0, 33.3, 18.5, 20.2, 0.25, 1.25)  # auto start switch (under the cell)
    ics = part(50.3, 59.3, 5.8, 13.1, 0.0, 2.0) + part(54.4, 58.4, 14.4, 19.1, 0.0, 1.5)       # the inductor and the charger IC
    disc = mcyl("x", f0 - 1.8, f0 + 0.01, 7.1, STACK_Y0 + 14.4, ZSD - 20.0, 40)               # the metal disc for the cell
    return [("board", "PiSugar S board", pcb + nuts, "#e06aa3"), ("pins", "pogo pins", pins, "#d9b34a"),
            ("usb_c", "USB-C charge port", usb, "#c9ccd1"), ("switch", "power switch", sw, "#c9ccd1"),
            ("button", "button", btn, "#c9ccd1"), ("parts", "auto switch and parts", auto + ics, "#2b2d33"),
            ("disc", "cell disc", disc, "#c9ccd1")]


# --------------------------------------------------------------------------
# Mesh helpers (manifold3d)
# --------------------------------------------------------------------------
def load_stl(path):
    d = open(path, "rb").read()
    n = np.frombuffer(d[80:84], np.uint32)[0]
    if 84 + n * 50 == len(d):
        a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
        return a["v"].reshape(-1, 3, 3).astype(float)
    tris, cur = [], []
    for line in d.decode(errors="ignore").splitlines():
        s = line.split()
        if s and s[0] == "vertex":
            cur.append([float(t) for t in s[1:4]])
            if len(cur) == 3:
                tris.append(cur)
                cur = []
    return np.array(tris, dtype=float)


def mesh_to_manifold(tris):
    v = tris.reshape(-1, 3)
    uv, inv = np.unique(v.round(4), axis=0, return_inverse=True)
    mesh = m3.Mesh(vert_properties=uv.astype(np.float32), tri_verts=inv.reshape(-1, 3).astype(np.uint32))
    return m3.Manifold(mesh)


def stl_manifold(name, transform=None, ref=None):
    M = mesh_to_manifold(load_stl(os.path.join(ref or REF, name)))
    if transform is not None:
        M = M.transform(transform[:3, :])
    return M


def b3d_to_manifold(shape, tol=0.02):
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
        path = f.name
    export_stl(shape, path, tolerance=tol, angular_tolerance=0.1)
    M = mesh_to_manifold(load_stl(path))
    os.unlink(path)
    if M.status() != m3.Error.NoError:
        raise RuntimeError(f"tessellation not manifold: {M.status()}")
    return M


def save_stl(M, path):
    mesh = M.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(t), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = nrm
    rec["v"] = tri.reshape(-1, 9)
    with open(path, "wb") as f:
        f.write(b"bittle-pod".ljust(80, b" "))
        f.write(np.uint32(len(t)).tobytes())
        f.write(rec.tobytes())


def heightfield_solid(tris, x0, x1, z0, z1, step=0.4, lift=0.0, floor=0.0):
    """Closed solid under the top surface of a mesh (raised by `lift`)."""
    xs = np.arange(x0, x1 + 1e-9, step)
    zs = np.arange(z0, z1 + 1e-9, step)
    H = np.full((len(xs), len(zs)), -1e9)
    nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    up = tris[nrm[:, 1] > 1e-9]
    for tri in up:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
        lo_x, hi_x = min(ax, bx, cx), max(ax, bx, cx)
        lo_z, hi_z = min(az, bz, cz), max(az, bz, cz)
        i0, i1 = np.searchsorted(xs, lo_x), np.searchsorted(xs, hi_x, "right")
        j0, j1 = np.searchsorted(zs, lo_z), np.searchsorted(zs, hi_z, "right")
        if i0 >= i1 or j0 >= j1:
            continue
        X, Z = np.meshgrid(xs[i0:i1], zs[j0:j1], indexing="ij")
        det = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        if abs(det) < 1e-12:
            continue
        l1 = ((bz - cz) * (X - cx) + (cx - bx) * (Z - cz)) / det
        l2 = ((cz - az) * (X - cx) + (ax - cx) * (Z - cz)) / det
        l3 = 1 - l1 - l2
        ok = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        Y = l1 * ay + l2 * by + l3 * cy
        sub = H[i0:i1, j0:j1]
        sub[ok] = np.maximum(sub[ok], Y[ok])
    H[H < -1e8] = floor
    H = H + lift
    # dilate by one cell so the sampled surface stays above the true surface
    Hd = H.copy()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            Hd = np.maximum(Hd, np.roll(np.roll(H, di, 0), dj, 1))
    H = Hd
    nx, nz = len(xs), len(zs)
    top = np.array([[x, H[i, j], z] for i, x in enumerate(xs) for j, z in enumerate(zs)])
    bot = np.array([[x, floor, z] for x in xs for z in zs])
    V = np.vstack([top, bot]).astype(np.float32)
    idx = lambda i, j, b=0: b * nx * nz + i * nz + j
    T = []
    for i in range(nx - 1):
        for j in range(nz - 1):
            a, b_, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
            T += [(a, d, c), (a, c, b_)]                       # top (+Y)
            a, b_, c, d = idx(i, j, 1), idx(i + 1, j, 1), idx(i + 1, j + 1, 1), idx(i, j + 1, 1)
            T += [(a, c, d), (a, b_, c)]                       # bottom (-Y)
    for i in range(nx - 1):   # sides z = z0 and z = z1
        for j, flip in ((0, False), (nz - 1, True)):
            a, b_, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j, 1), idx(i, j, 1)
            T += [(a, b_, c), (a, c, d)] if not flip else [(a, c, b_), (a, d, c)]
    for j in range(nz - 1):   # sides x = x0 and x = x1
        for i, flip in ((0, False), (nx - 1, True)):
            a, b_, c, d = idx(i, j), idx(i, j + 1), idx(i, j + 1, 1), idx(i, j, 1)
            T += [(a, c, b_), (a, d, c)] if not flip else [(a, b_, c), (a, c, d)]
    M = m3.Manifold(m3.Mesh(vert_properties=V, tri_verts=np.array(T, dtype=np.uint32)))
    if M.status() != m3.Error.NoError or M.volume() <= 0:
        raise RuntimeError(f"heightfield solid failed: {M.status()} {M.volume()}")
    return M


# --------------------------------------------------------------------------
# build123d helpers
# --------------------------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_y(x, z, y0, y1, r):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, y1 - y0)


def cyl_z(x, y, z0, z1, r):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def cyl_x(y, z, x0, x1, r):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)




def mesh_solid(M, tol=0.05):
    """Faceted B-rep solid from a manifold mesh, simplified to `tol` mm. Coplanar facets are merged."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    from OCP.TopoDS import TopoDS
    from OCP.gp import gp_Pnt
    from build123d import Solid
    m = M.simplify(tol).to_mesh()
    v = np.asarray(m.vert_properties)[:, :3].astype(float)
    sw = BRepBuilderAPI_Sewing(1e-4)
    for a, b, c in np.asarray(m.tri_verts):
        poly = BRepBuilderAPI_MakePolygon(gp_Pnt(*v[a]), gp_Pnt(*v[b]), gp_Pnt(*v[c]), True)
        f = BRepBuilderAPI_MakeFace(poly.Wire(), True)
        if f.IsDone():
            sw.Add(f.Face())
    sw.Perform()
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SHELL
    mk = BRepBuilderAPI_MakeSolid()
    ex = TopExp_Explorer(sw.SewedShape(), TopAbs_SHELL)
    while ex.More():                       # a mesh can have more than one closed shell
        mk.Add(TopoDS.Shell(ex.Current()))
        ex.Next()
    S = mk.Solid()
    u = ShapeUpgrade_UnifySameDomain(S, True, True, False)
    u.Build()
    return Solid(u.Shape())




# --------------------------------------------------------------------------
# manifold3d solids
# --------------------------------------------------------------------------
def mbox(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def mcyl(axis, a0, a1, r, c0=0.0, c1=0.0, n=40):
    """Cylinder along an axis from a0 to a1; (c0, c1) = the center in the other two axes, in X, Y, Z order."""
    C = m3.Manifold.cylinder(a1 - a0, r, r, n)
    if axis == "z":
        return C.translate([c0, c1, a0])
    if axis == "y":
        return C.rotate([-90, 0, 0]).translate([c0, a0, c1])
    return C.rotate([0, 90, 0]).translate([a0, c0, c1])


def _cs(pts):
    return m3.CrossSection([np.asarray(pts, float)], m3.FillRule.NonZero)


def prism_y(pts_xz, y0, y1):
    """Polygon in plan (x, z), extruded from y0 up to y1."""
    M = _cs([(x, -z) for x, z in pts_xz]).extrude(y1 - y0)
    return M.transform(np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, -1, 0, 0]], float))


def prism_x(pts_yz, x0, x1):
    """Polygon in the (y, z) plane, extruded from x0 to x1."""
    return _cs(pts_yz).extrude(x1 - x0).transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def union(ms):
    ms = [m for m in ms if m is not None]
    return m3.Manifold.batch_boolean(ms, m3.OpType.Add) if ms else m3.Manifold()


def plan(inset, n=64, a=None):
    """Closed plan outline (x, z) of the body (half width a), moved inset along the normal from the outer face.
    Counterclockwise seen from +Y. The same points for every inset: lofts between plans are clean."""
    a, z0, z1, r = a or A, Z0, Z1, R_PLAN
    pts = []
    for cx, cz, q in ((a - r, z1 - r, 0), (-(a - r), z1 - r, 1), (-(a - r), z0 + r, 2), (a - r, z0 + r, 3)):
        for t in np.linspace(0, math.pi / 2, n, endpoint=False):
            th = q * math.pi / 2 + t
            c, s = math.cos(th), math.sin(th)
            pts.append((cx + r * math.copysign(abs(c) ** (2 / NEXP), c), cz + r * math.copysign(abs(s) ** (2 / NEXP), s)))
    P = np.array(pts)
    if inset:
        d = np.roll(P, -1, 0) - np.roll(P, 1, 0)                  # tangent (the points go counterclockwise in x, z)
        nrm = np.c_[d[:, 1], -d[:, 0]] / np.linalg.norm(d, axis=1)[:, None]   # outward normal
        P = P - inset * nrm
    return P[::-1]


def teardrop_z(z0, z1, r, x, y, n=20):
    """Hole along Z: round, with a 45 deg point on top. It prints without a bridge in a vertical wall."""
    pts = [(x + r * math.cos(a), y + r * math.sin(a)) for a in np.linspace(math.radians(45), math.radians(-225), n)]
    pts.append((x, y + r * math.sqrt(2)))
    return _cs(pts).extrude(z1 - z0).translate([0, 0, z0])


def rrect_pts(x0, x1, z0, z1, r, n=12):
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for t in np.linspace(0, 90, n):
            a = math.radians(a0 + t)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def loft_rings(rings):
    """rings: [(y, pts[n, 2] as (x, z))], bottom to top, the same n. Closed solid with flat caps."""
    n = len(rings[0][1])
    V, T = [], []
    for y, p in rings:
        V += [(x, y, z) for x, z in p]
    k = len(rings)
    for i in range(k - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            T += [(a, b + n, a + n), (a, b, b + n)]
    cb, ct = len(V), len(V) + 1
    V.append((rings[0][1][:, 0].mean(), rings[0][0], rings[0][1][:, 1].mean()))
    V.append((rings[-1][1][:, 0].mean(), rings[-1][0], rings[-1][1][:, 1].mean()))
    for j in range(n):
        T.append((cb, (j + 1) % n, j))
        T.append((ct, (k - 1) * n + j, (k - 1) * n + (j + 1) % n))
    M = m3.Manifold(m3.Mesh(vert_properties=np.array(V, np.float32), tri_verts=np.array(T, np.uint32)))
    if M.status() != m3.Error.NoError or M.volume() <= 0:
        raise RuntimeError(f"loft failed: {M.status()} {M.volume()}")
    return M


# --------------------------------------------------------------------------
# Parts
# --------------------------------------------------------------------------
def build_pegs():
    """The platform pegs (bittle_platform/build.py)."""
    from bittle_platform import build as BP
    return BP.pegs()


def body_outer():
    """A_LOW wide at the floor, a 45 deg chamfer out to A between STEP_Y, A wide to the seam."""
    return loft_rings([(FLOOR_Y0, plan(0.0, a=A_LOW)), (STEP_Y[0], plan(0.0, a=A_LOW)), (STEP_Y[1], plan(0.0)), (SEAM, plan(0.0))])


def body_cavity():
    """The inside of the body: the outer form moved in WALL (the 45 deg face moves up WALL * (sqrt 2 - 1))."""
    k = WALL * (math.sqrt(2) - 1)
    return loft_rings([(FLOOR_Y1, plan(WALL, a=A_LOW)), (STEP_Y[0] + k, plan(WALL, a=A_LOW)), (STEP_Y[1] + k, plan(WALL)),
                       (SEAM + 1, plan(WALL))])


def speaker_posts():
    """Two posts on the side walls with a vertical groove for each end of the ear plate."""
    G = SPK_GROOVE
    za, zb = SPK_ZE - G["clr"], SPK_ZE + SPK["ear_t"] + G["clr"]
    out = []
    for sx in (-1, 1):
        p = mbox(*sorted((sx * G["x_in"], sx * (IN_A + 0.5))), FLOOR_Y1 - 0.01, G["top"], za - G["lip"], zb + G["lip"])
        p -= mbox(*sorted((sx * (G["x_in"] - 1), sx * (SPK["l"] / 2 + G["clr"]))), SPK_Y0 - 0.05, 99, za, zb)
        out.append(p)
    return union(out)


def screw_heads():
    """The M2.5 screw heads at the four corners of the stack, on both outer faces."""
    S = SCREW
    out = []
    for z in (STACK_ZF + S["inset"], STACK_ZR - S["inset"]):
        for y in (STACK_Y0 + S["inset"], STACK_Y0 + 30.0 - S["inset"]):
            out.append(mcyl("x", PCB_X[0] - S["h"], PCB_X[0] + 0.01, S["d"] / 2, y, z, 24))
            out.append(mcyl("x", PCB_X[1] - 0.01, PCB_X[1] + S["h"], S["d"] / 2, y, z, 24))
    return union(out)


def stack_posts():
    """Front and rear posts with one vertical groove for the two board ends: the same width and depth for both
    boards, from the top to the bottom (the stop). The Pi side is cut out for the SD holder and the CSI connector."""
    c, (x0, x1) = POST["clr"], POST["x"]
    xg = max(SD["x"][1], CSI["x"][1])
    groove = lambda za, zb: mbox(PCB_X[0] - c, xg, STACK_Y0 - 0.15, 99, za, zb)
    r = mbox(x0, x1, FLOOR_Y1 - 0.01, POST["top"], *POST_SD)
    r -= groove(POST_SD[0] - 1, ZSD + c)
    r -= mbox(*SD_CARD["x"], *SD_CARD["y"], POST_SD[0] - 1, ZSD + SD_CARD["out"])
    f = mbox(x0, x1, FLOOR_Y1 - 0.01, POST["top"], *POST_CSI)
    f -= groove(STACK_ZF - c, POST_CSI[1] + 1)
    f -= mbox(*CSI["x"], *CSI["y"], STACK_ZF - CSI["out"], POST_CSI[1] + 1)
    S = SCREW                                              # the screw heads go down a channel to their place
    ch = union([mbox(PCB_X[0] - S["h"] - S["clr"], xg + S["h"] + S["clr"], STACK_Y0 + S["inset"] - S["d"] / 2 - S["clr"], 99,
                     z - S["d"] / 2 - S["clr"], z + S["d"] / 2 + S["clr"]) for z in (STACK_ZF + S["inset"], STACK_ZR - S["inset"])])
    return (f + r) - (ch - mbox(PCB_X[0] - POST["clr"], xg, 0, 99, -99, 99))


def teardrop_x(x0, x1, r, y, z, n=20):
    """Hole or boss along X: round, with a 45 deg point on top. It prints without a bridge in a vertical wall."""
    pts = [(y + r * math.sin(a), z + r * math.cos(a)) for a in np.linspace(math.radians(45), math.radians(-225), n)]
    pts.append((y + r * math.sqrt(2), z))
    return prism_x(pts, x0, x1)


def mic_holder():
    """A post on the right wall with a vertical slot for the rear edge of the mic, and a ledge with a slot for its
    bottom edge (a 45 deg underside into the wall). The back lip of the ledge stops behind the header."""
    H, M = MIC_HOLD, MIC
    c, d = H["clr"], H["depth"]
    xa, xf, xb = -IN_A - 0.5, MIC_X[0] - c, MIC_X[1] + c
    xl = xb + H["lip"]
    y0, y1, z0, z1 = M["y0"], M["y0"] + M["l"], M["z0"], M["z0"] + M["w"]
    slot = mbox(xf, xb, y0 - c, 99, z0 - c, z1 + c)
    post = mbox(xa, xl, y0 - 1.5, y1 - 0.5, z1 - d, z1 + 1.6)
    prof = [(xa, y0 - 1.5 - (xl - xa)), (xl, y0 - 1.5), (xl, y0 + d), (xa, y0 + d)]
    zh = MIC_PIN_Z + 1.27 + 0.3                            # behind the header: only the front lip goes forward of it
    front = [(xa, y0 - 1.5 - (xf - xa)), (xf, y0 - 1.5), (xf, y0 + d), (xa, y0 + d)]   # the lip between the wall and the board
    ledge = prism_zp(prof, zh, z1 + 1.6) + prism_zp(front, z0, zh + 0.01)
    stop = prism_zp([(xa, y0 - 1.5 - (xb - xa)), (xb, y0 - 1.5), (xb, y0 + 2.0), (xa, y0 + 2.0)], ZF_IN - 0.5, z0 - c)   # in front of the bottom corner
    return (post + ledge + stop) - slot


def amp_base():
    """Bar on the floor along the wall with a slot for the bottom edge of the amp board, and two nubs over its top
    edge: tilt the board in, press its top edge under the nubs, then set it with a dab of glue."""
    c = 0.15
    b = mbox(-IN_A - 0.5, AMP_X[1] + 1.55, FLOOR_Y1 - 0.01, 30.0, *AMP_Z)
    b -= mbox(AMP_X[0] - c, AMP_X[1] + c, AMP_Y0 - 0.15, 31.0, AMP_Z[0] - 1, AMP_Z[1] + 1)
    return b + amp_nubs()


def amp_nubs():
    """Two posts behind the amp board (up from the chamfer) with a nub over its top edge: a flat catch, a 45 deg top."""
    yt = AMP_Y0 + AMP["h"]
    xb = AMP_X[0] - 1.6                                    # the back face of the posts
    prof = [(xb, FLOOR_Y1), (AMP_X[0] - 0.05, FLOOR_Y1), (AMP_X[0] - 0.05, yt + 0.05), (AMP_X[0] + 1.0, yt + 0.05),
            (AMP_X[0] + 1.0, yt + 0.45), (xb, yt + 0.45 + 1.05 + 1.6)]
    return union([prism_zp(prof, z, z + 4.0) for z in AMP_NUBS])


def _wall_prism(pts_uy, side, z0=None, z1=None):
    """A (u, y) profile on the inner face of a wall: side +-1 = the right or left wall (along Z from z0 to z1),
    side 0 = the front wall (along X over the LID front_x segments)."""
    if side:
        return prism_zp([(side * (IN_A - u), y) for u, y in pts_uy], z0, z1)
    return union([prism_x([(y, ZF_IN + u) for u, y in pts_uy], x0, x1) for x0, x1 in LID["front_x"]])


def lid_lugs():
    """The lugs of the body: a 45 deg underside, a vertical face, the top at the seam."""
    L, y = LID["L"], LID_LUG_Y
    prof = [(-0.02, y), (L, y + L), (L, SEAM), (-0.02, SEAM)]
    out = [_wall_prism(prof, 0)]
    for sx, zs in LID["side_z"].items():
        out += [_wall_prism(prof, sx, z, z + LID["lug_len"]) for z in zs]
    return union(out)


def lid_hooks():
    """The hooks of the panel: a stem down from the panel, a 45 deg hook out under the lug (gap_y under it)."""
    L, g, t, gy, bot = LID["L"], LID["gap"], LID["t"], LID["gap_y"], LID["bot"]
    def prof(tip):
        y = lambda u: LID_LUG_Y + u - gy                  # the hook top: parallel to the lug underside
        return [(tip, bot), (L + g + t, bot), (L + g + t, PANEL_IN + 0.01), (L + g, PANEL_IN + 0.01), (L + g, y(L + g)), (tip, y(tip))]
    out = [_wall_prism(prof(LID["front_gap"]), 0)]      # the front hook tip is the forward stop
    d = (LID["lug_len"] - LID["hook_len"]) / 2
    for sx, zs in LID["side_z"].items():
        out += [_wall_prism(prof(g), sx, z + d, z + d + LID["hook_len"]) for z in zs]
    return union(out)


def lid_keepout():
    """Space near the walls that the other parts under the panel stay out of: the lugs pass through it."""
    u = LID["L"] + LID["gap"]
    y0, y1 = LID["bot"] - 0.1, SEAM + 0.05
    out = [mbox(-A - 1, A + 1, y0, y1, Z0 - 1, ZF_IN + u)]
    for sx in (-1, 1):
        out.append(mbox(*sorted((sx * (IN_A - u), sx * (A + 1))), y0, y1, Z0 - 1, Z1 + 1))
    return union(out)


def latch_rib():
    """The rib on the rear wall: a 45 deg underside, the catch face to the front, the top over the seam."""
    C = LATCH
    zf = ZR_IN - C["rib_d"]
    prof = [(SEAM - 2.2, ZR_IN + 0.02), (SEAM - 2.2 + C["rib_d"], zf), (C["rib_top"], zf), (C["rib_top"], ZR_IN - 0.1),
            (SEAM, ZR_IN - 0.1), (SEAM, ZR_IN + 0.02)]
    return prism_x(prof, -C["rib_hw"], C["rib_hw"])


def latch_hook(dy=0.0):
    """The hook under the latch tongue: the catch face to the rear (on the rib), a 45 deg ramp at the front."""
    C = LATCH
    zr = ZR_IN - C["rib_d"] - C["gap"]
    zf = zr - C["hook_d"]
    b, r = C["hook_bot"], C["ramp"]
    prof = [(PANEL_IN + 0.01, zr), (b, zr), (b, zf + r), (b + r, zf), (PANEL_IN + 0.01, zf)]
    return prism_x(prof, -C["hook_hw"], C["hook_hw"]).translate([0, dy, 0])


def latch_slits():
    """Two slits through the panel top and the rear skirt: they free the latch tongue."""
    C = LATCH
    return union([mbox(*sorted((sx * C["hw"], sx * (C["hw"] + C["slit"]))), SEAM - 1, TOP + 1, C["root_z"], Z1 + 1) for sx in (-1, 1)])


def keyhole_cut(px, pz):
    """The keyhole of the robot-frame peg at (px, pz), in the design frame (at -px)."""
    from bittle_platform import build as BP
    return flip_x(b3d_to_manifold(BP.keyhole_cutter(px, pz)))


def keyhole_bump(px, pz):
    from bittle_platform import build as BP
    return flip_x(b3d_to_manifold(BP.detent_bump(px, pz)))


def battery_supports():
    """Blocks on the floor under the cell."""
    S = BAT_SUPPORT
    return union([mbox(*S["x"], FLOOR_Y1 - 0.01, BAT["y"][0] - S["gap"], z0, z1) for z0, z1 in S["z"]])


def battery_clamp():
    """Plates from the panel along the outer face of the cell, with pads over its top edge; and a pad alone in the middle."""
    C = BAT_CLAMP
    xo = BAT["x"][0] - C["gap"]                         # outer face of the cell - gap
    ytop = BAT["y"][1] + C["gap"]
    out = []
    for z0, z1 in C["z"]:
        out.append(mbox(xo - C["t"], xo, C["y0"], PANEL_IN + 0.01, z0, z1))
        out.append(mbox(xo - C["t"], xo + C["pad_x"], ytop, PANEL_IN + 0.01, z0, z1))
    for z0, z1 in C["pads_z"]:
        out.append(mbox(BAT["x"][0] + 0.8, BAT["x"][1] - 1.2, ytop, PANEL_IN + 0.01, z0, z1))
    return union(out)


# Labels and route lines inside the body (assembly aids), cut LABEL_D into the walls and the floor: they print
# without supports (a raised label on a wall would push on the parts). Robot frame, then turned into the design frame.
FONT = os.path.join(REF, "fonts", "LiberationSans-Bold.ttf")
LABEL_D, LINE_W, LINE_D = 0.5, 0.8, 0.4


def text_cut(text, size, origin, right, up, depth=LABEL_D):
    """Text cut depth into a surface: origin on the surface, right and up along it (robot frame). It reads from the
    room side (right x up points out of the surface, into the room)."""
    from build123d import Align, Text, extrude
    s = extrude(Text(text, font_size=size, font_path=FONT, align=(Align.CENTER, Align.CENTER)), amount=depth + 0.5)
    r, u = np.asarray(right, float), np.asarray(up, float)
    n = np.cross(r, u)
    T = np.c_[r, u, n, np.asarray(origin, float) - n * depth]
    return b3d_to_manifold(s).transform(T)


def floor_line(pts_xz, w=LINE_W, d=LINE_D):
    """A groove along a polyline on the top of the floor (design frame)."""
    C = [mcyl("y", FLOOR_Y1 - d, FLOOR_Y1 + 0.5, w / 2, x, z, 12) for x, z in pts_xz]
    return union([m3.Manifold.batch_hull([a, b]) for a, b in zip(C[:-1], C[1:])])


def body_marks():
    """Names on the walls and the floor where each part goes, the Pi header pin numbers, and route lines on the floor:
    the amp cable lanes (the wires lie there) and the mic wire run across the front."""
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    nX, nZ = (-1, 0, 0), (0, 0, -1)
    S = 4.5
    t = [text_cut("MIC →", S, (22.0, 51.0, ZF_IN), X, Y),                      # front wall: the mic is on the right wall
         text_cut("AMP", S, (IN_A, 52.6, 10.0), Z, Y),                               # right wall, over the amp
         text_cut("SPEAKER", S, (0.0, 53.6, ZR_IN), nX, Y),                          # rear wall, over the grille
         text_cut("BIBOARD", S, (-IN_A, 51.0, (HDR["z0"] + HDR["z1"]) / 2), nZ, Y),   # left wall, over the BiBoard plug
         text_cut("PIN 1", 3.5, (-IN_A, 41.0, pin_yz(1)[1]), nZ, Y),                 # left wall, in line with the header ends
         text_cut("PIN 40", 3.5, (-IN_A, 41.0, pin_yz(40)[1]), nZ, Y),
         text_cut("AMP", 3.5, (16.0, FLOOR_Y1, -28.0), X, nZ),                       # floor, at the start of the amp cable
         text_cut("MIC", 3.5, (12.0, FLOOR_Y1, -33.9), X, nZ)]                       # floor, at the mic wire run
    marks = flip_x(union(t))
    lines = []
    for g, lab, col, pts in wire_routes():
        P = [p for p in pts]
        if g == "amp":                                     # the floor parts of the amp wires
            for a, b in zip(P[:-1], P[1:]):
                if a[1] <= FLOOR_WIRE + 0.6 and b[1] <= FLOOR_WIRE + 0.6:
                    lines.append(floor_line([(a[0], a[2]), (b[0], b[2])]))
    lines.append(floor_line([(MIC_HOUSING_X[1], MIC_PIN_Z), (21.0, MIC_PIN_Z), (MIC_RIB - 0.6, -29.6)]))
    keep = union([mbox(k[0], k[1], 0, 99, k[2], k[3]) for k in (keep_zone(px, pz) for px, pz in PEGS)])
    return marks + (union(lines) - keep)


def build_body():
    O = body_outer()
    B = O - body_cavity()
    B += (speaker_posts() + stack_posts() + mic_holder() + amp_base() + battery_supports()) ^ O
    for px, pz in PEGS:
        B -= keyhole_cut(px, pz)
    for px, pz in PEGS:
        B += keyhole_bump(px, pz)
    N = HDR_NOTCH
    B -= mbox(*N["x"], FLOOR_Y0 - 1, 30.0, *N["z"])                       # the BiBoard header comes up here
    B += lid_lugs() + latch_rib()
    nt = _cs([(NOTCH["hw"] + NOTCH["h"] * math.cos(t), SEAM + NOTCH["h"] * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 16)]
             + [(-NOTCH["hw"] - NOTCH["h"] * math.cos(t), SEAM - NOTCH["h"] * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 16)])
    B -= nt.extrude(NOTCH["d"] + 1).translate([0, 0, Z1 - NOTCH["d"]])   # finger notch
    holes = [teardrop_z(ZR_IN - 0.5, Z1 + 0.5, GRILLE["d"] / 2, x, y) for x in GRILLE["x"] for y in GRILLE["y"]]
    for a in [None] + list(range(0, 360, 60)):                             # mic holes around the port, in the right wall
        dz, dy = (0.0, 0.0) if a is None else (2.2 * math.cos(math.radians(a)), 2.2 * math.sin(math.radians(a)))
        holes.append(teardrop_x(-A - 0.5, -IN_A + 0.5, 0.5, MIC_PORT[0] + dy, MIC_PORT[1] + dz, n=12))
    B -= union(holes)
    h = FRONT_NOTCH["h"]
    tri = [(FLOOR_Y0 - 1, Z0 - 1), (FLOOR_Y0 + h + 1, Z0 - 1), (FLOOR_Y0 - 1, Z0 + h + 1)]     # 45 deg face
    B -= prism_x(tri, *FRONT_NOTCH["x"])
    B -= mbox(*FRONT_NOTCH["x"], FLOOR_Y0 - 1, FLOOR_Y1 + 0.01, ZF_IN - 0.5, FRONT_NOTCH["z1"])     # floor opening over the Grove plug
    return B - body_marks()


def panel_outer():
    rings = [(SEAM, plan(0.0)), (TOP - RT, plan(0.0))]
    for th in np.linspace(0, math.radians(45), 9)[1:]:
        rings.append((TOP - RT + RT * math.sin(th), plan(RT - RT * math.cos(th))))
    yc = TOP - RT + RT * math.sin(math.radians(45))
    ic = RT - RT * math.cos(math.radians(45))
    rings.append((TOP, plan(ic + (TOP - yc))))           # 45 deg chamfer to the top face (the bed edge)
    return loft_rings(rings)


def panel_forks():
    out = []
    xa, xb = PCB_X[0] - POST["clr"], CSI["x"][1]
    for z0 in STACK_FORKS:                                 # over the top edge of the boards
        f = mbox(xa - FORK["lip"], xb + FORK["lip"], 59.0, PANEL_IN + 0.01, z0, z0 + FORK["len"])   # over the screw heads
        out.append(f - mbox(xa, xb, 0, STACK_Y0 + 30.0 + FORK["clr_y"], z0 - 1, z0 + FORK["len"] + 1))
    G = SPK_GROOVE                                         # pads on the top of the speaker body, beside the latch tongue
    za, zb = SPK_ZE - G["clr"], SPK_ZE + SPK["ear_t"] + G["clr"]
    for sx in (-1, 1):
        out.append(mbox(*sorted((sx * 5.6, sx * 8.6)), SPK_Y0 + SPK["d"] - 0.5 + G["clr_y"], PANEL_IN + 0.01, zb - 2.75, zb - 0.25))   # clear of the lead path
    yt = MIC["y0"] + MIC["l"]                              # over the top edge of the mic, behind its header
    out.append(mbox(-IN_A + 1.7, MIC_X[1] + 0.8, yt + 0.1, PANEL_IN + 0.01, MIC_PIN_Z + 1.9, MIC["z0"] + MIC["w"] - 1.0))
    for z0 in AMP_FORKS:                                   # over the top edge of the amp board
        f = mbox(-IN_A + 0.15, AMP_X[1] + 1.55, 50.0, PANEL_IN + 0.01, z0, z0 + 2.5)
        out.append(f - mbox(-IN_A - 1, AMP_X[1] + 0.15, 0, AMP_Y0 + AMP["h"] + 0.3, z0 - 1, z0 + 3.5))
    return union(out)


def _plan_cs(x0, x1, z0, z1, r):
    """A rounded rectangle in plan as a CrossSection for _plan_cut."""
    return _cs([(x, -z) for x, z in rrect_pts(x0, x1, z0, z1, r)])


def _plan_cut(cs, y0, y1):
    """A plan CrossSection extruded from y0 up to y1."""
    return cs.extrude(y1 - y0).transform(np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, -1, 0, 0]], float))


def _close(cs, r):
    """Fill the gaps under 2r wide between the regions of cs (and round its inside corners to r)."""
    return cs.offset(r, m3.JoinType.Round).offset(-r, m3.JoinType.Round)


PORT_GROUPS = [("hdmi", "switch"), ("pi_usb", "pi_power", "charge")]   # each group is one opening in the panel
WEB_MIN = 1.0                      # webs under 2 x this between the openings and the tongue slits are cut away


def port_cuts():
    """The openings in the panel top: one opening for each PORT_GROUPS group (the plug bodies + PORT_CLR and the
    switch window, joined, inside corners round), a 45 deg chamfer of PORT_CHAMFER at the top face. A web
    narrower than 2 x WEB_MIN between an opening and the tongue slit is cut away too: the tongue end is then at
    the edge of the opening."""
    box = {n: (xc - sx / 2 - PORT_CLR, xc + sx / 2 + PORT_CLR, zc - sz / 2 - PORT_CLR, zc + sz / 2 + PORT_CLR)
           for n, (xc, zc, sx, sz) in PORT_PLUGS.items()}
    box["switch"] = (*SW_WIN["x"], *SW_WIN["z"])
    rect = {n: _plan_cs(*b, PORT_R) for n, b in box.items()}
    groups = [_close(union_cs([rect[n] for n in g]), WEB_MIN) for g in PORT_GROUPS]
    B = BTN
    (x0, x1), (z0, z1), w = B["x"], B["z"], B["slit"]
    slit = _plan_cs(x0 - w, x1 + w, z0 - w, z1 - 0.01, 0.0) - _plan_cs(x0, x1, z0, z1 + 1, 0.0)
    ports = union_cs(groups)
    through = _close(ports + slit, WEB_MIN)
    c = PORT_CHAMFER
    out = [_plan_cut(through, PANEL_IN - 1, TOP + 1)]
    for x0, x1, z0, z1 in box.values():                    # a 45 deg chamfer on each member (a hull: a true 45 deg face)
        out.append(m3.Manifold.batch_hull([_plan_cut(_plan_cs(x0, x1, z0, z1, PORT_R), TOP - c - 0.01, TOP - c),
                                           _plan_cut(_plan_cs(x0 - c, x1 + c, z0 - c, z1 + c, PORT_R + c), TOP, TOP + 1)]))
    return union(out)


def union_cs(cs):
    out = cs[0]
    for c in cs[1:]:
        out = out + c
    return out


def prism_zp(pts_xy, z0, z1):
    """Polygon in the (x, y) plane, extruded from z0 to z1."""
    return _cs(pts_xy).extrude(z1 - z0).translate([0, 0, z0])


def button_cuts():
    """U slit around the tongue (root at z1, free end at z0) and the thinning under it."""
    B = BTN
    (x0, x1), (z0, z1), w = B["x"], B["z"], B["slit"]
    u = mbox(x0 - w, x1 + w, PANEL_IN - 1, TOP + 1, z0 - w, z1 - 0.01) - mbox(x0, x1, PANEL_IN - 2, TOP + 2, z0, z1 + 1)
    thin = mbox(x0, x1, PANEL_IN - 1, TOP - B["t"], z0, z1 + 0.01)
    return u + thin


def button_arm(dy=0.0):
    """Arm under the free end of the tongue: down from the tongue, then across over the button."""
    B = BTN
    y_low = B["cap"][4] + B["gap"]
    v = mbox(B["arm_x"][0], B["x"][1] - 0.2, y_low, TOP - B["t"] + 0.01, *B["arm_z"])
    h = mbox(B["arm_x"][0], B["arm_x"][1], y_low, y_low + 0.8, *B["arm_z"])
    return (v + h).translate([0, dy, 0])


def keycap_center():
    K, B = KEYCAP, BTN
    return (B["x"][0] + B["x"][1]) / 2, B["z"][0] + 0.3 + K["l"] / 2


def keycap_hole():
    """Round hole through the tongue for the post of the cap."""
    xc, zc = keycap_center()
    pts = [(xc + KEYCAP["post_d"] / 2 * math.cos(t), zc + KEYCAP["post_d"] / 2 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
    return prism_y(pts, PANEL_IN - 1, TOP + 1)


def build_keycap(dz=0.0, press=True):
    """The white button cap on the tongue, its cross post in the hole (press: the ribs are over the hole size)."""
    K = KEYCAP
    xc, zc = keycap_center()
    z0, z1 = zc - K["l"] / 2, zc + K["l"] / 2
    cap = prism_y(rrect_pts(xc - K["w"] / 2, xc + K["w"] / 2, z0, z1, K["r"]), TOP + 0.02, TOP + K["h"] - 0.5)
    top = prism_y(rrect_pts(xc - K["w"] / 2 + 0.5, xc + K["w"] / 2 - 0.5, z0 + 0.5, z1 - 0.5, K["r"] - 0.3), TOP + K["h"] - 0.01, TOP + K["h"])
    cap = m3.Manifold.batch_hull([cap, top])
    e = K["post_d"] / 2 + (K["press"] if press else 0.0)
    y0 = TOP - K["post_h"]
    post = mbox(xc - e, xc + e, y0, TOP + 0.03, zc - K["rib"] / 2, zc + K["rib"] / 2) + mbox(xc - K["rib"] / 2, xc + K["rib"] / 2, y0, TOP + 0.03, zc - e, zc + e)
    post = post ^ prism_y([(xc + e * math.cos(t), zc + e * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)], y0 - 1, TOP + 1)
    lead = K["press"] + 0.35                               # 45 deg lead-in: the rib ends start inside the hole
    post = post - (mbox(xc - e - 1, xc + e + 1, y0 - 1, y0 + lead, zc - e - 1, zc + e + 1)
                   - m3.Manifold.batch_hull([prism_y(rrect_pts(xc - e + lead, xc + e - lead, zc - e + lead, zc + e - lead, 0.01), y0 - 0.01, y0),
                                             prism_y(rrect_pts(xc - e, xc + e, zc - e, zc + e, 0.01), y0 + lead, y0 + lead + 0.01)]))
    return (cap + post).translate([0, 0, dz])


# ---------- camera mount
def cam_to_body(low=False):
    """Native case frame -> design frame: native X down (the USB end up), native Y to -X (a mirror in the design frame:
    the robot frame turns it back), native Z (the lens axis) along Z. Centered at cx, on the base (or the cradle of
    the head-off mount), front at front_z."""
    C = CAM
    x0, x1, y0, y1, z0, z1 = cam_box(low)
    tx = (x0 + x1) / 2 + (C["case_y"][0] + C["case_y"][1]) / 2
    return np.array([[0, -1, 0, tx], [-1, 0, 0, y0 + C["case_x"][1]], [0, 0, 1, z0 - C["case_z"][0]], [0, 0, 0, 1]], float)


def cam_box(low=False):
    """The camera case in place, as a box (x0, x1, y0, y1, z0, z1)."""
    C = CAM
    hx = (C["case_y"][1] - C["case_y"][0]) / 2
    h, d = C["case_x"][1] - C["case_x"][0], C["case_z"][1] - C["case_z"][0]
    if low:
        L = CAM_LOW
        return (L["cx"] - hx, L["cx"] + hx, L["y0"], L["y0"] + h, L["rear_z"] - d, L["rear_z"])
    y0 = TW_TOP - TW["pocket"] + 0.05
    return (C["cx"] - hx, C["cx"] + hx, y0, y0 + h, C["front_z"], C["front_z"] + d)


def cam_usb_plug(low=False):
    """The USB-C plug in the top face of the case: (x0, x1, y0, y1, z0, z1). It goes in along -Y from above."""
    T = cam_to_body(low)
    uy, uz = CAM["usb"]
    xc, zc = T[0, 1] * uy + T[0, 3], uz + T[2, 3]
    yt = cam_box(low)[3]
    U = USB_C
    return (xc - U["w"] / 2, xc + U["w"] / 2, yt + 0.05, yt + U["l"], zc - U["t"] / 2, zc + U["t"] / 2)


def pi_usb_plug():
    """The micro-USB plug in the Pi data USB port, through its opening in the panel."""
    xc, zc, sx, sz = PORT_PLUGS["pi_usb"]
    return (xc - sx / 2, xc + sx / 2, PORT_TOP + 0.2, PORT_TOP + 0.2 + USB_MICRO_L, zc - sz / 2, zc + sz / 2)


def _chin(xa, xb, zfl, yb):
    """A chin from the top yb over the rounded front edge of the panel (forward to zfl), from xa to xb."""
    Bs = CAM["base"]
    P = panel_outer()
    cl = Bs["clr"]
    Pc = union([P.translate([0, dy, dz]) for dy in (0.0, cl) for dz in (0.0, -cl)])
    # Its underside is a 45 deg plane over the round: y >= z + k, k = the largest y - z of the panel top edge (98.71 at
    # the center line) + clr.
    k = 98.71 + Bs["clr"]
    yl = TOP - Bs["chin"]
    sec = [(zfl, yb), (zfl, yl), (yl - k, yl), (yb - k, yb)]                  # (z, y) section
    chin = _cs([(z_, -y_) for z_, y_ in sec]).extrude(xb - xa).transform(np.array([[0, 0, 1, xa], [0, -1, 0, 0], [1, 0, 0, 0]], float))
    return chin - Pc


def _case_brackets(low=False, y_floor=TOP, z_end=None, walls_to_end=False):
    """Two side brackets from y_floor: corner lips at the bottom, a hook over each top corner of the case (clear of
    the USB port). The brackets spread to let the case in from the top; the hooks snap over its top face. The back
    lips and the hooks go back to z_end (the end of the part on the print bed)."""
    C, Br = CAM, CAM["brk"]
    x0, x1, y0, y1, z0, z1 = cam_box(low)
    zf, zb = z0 - Br["clr"], z1 + Br["clr"]
    zfl = zf - Br["lip_front"]
    yt = y1 + Br["gap"]                                   # underside of the hooks, over the top face of the case
    ty = cam_to_body(low)
    ze = zb + Br["lip_back"] if z_end is None else z_end
    m = None
    for sx, xi in ((-1, x0 - Br["clr"]), (1, x1 + Br["clr"])):
        X = lambda a, b: sorted((a, b))
        xo = xi + sx * Br["t"]
        xe = ty[0, 1] * (C["top_y"][1] if sx < 0 else C["top_y"][0]) + ty[0, 3]   # edge of the top face
        tip = xe - sx * Br["hook"]
        w = mbox(*X(xi, xo), y_floor, yt + abs(xi - tip), zfl, ze if walls_to_end else zb + Br["lip_back"])
        ylip = y0 + Br["lip_h"]
        lb = zb + Br["lip_back"]                          # back lip (low part only); behind it a 45 deg end (no overhang in the print)
        lp = [(xi, zb), (xi - sx * 1.6, zb), (xi - sx * 1.6, lb), (xi, min(lb + 1.6, ze))] if ze > lb else [(xi, zb), (xi - sx * 1.6, zb), (xi - sx * 1.6, lb), (xi, lb)]
        w += prism_y(lp if sx < 0 else lp[::-1], y_floor, ylip)
        lip = [(xi, zf), (xi, zfl), (xi - sx * Br["lip_front"], zfl)]
        if sx < 0:
            lip = lip[::-1]
        pts = [(x, -z) for x, z in lip]                   # front lip, 45 deg (it prints last, the part stands on its back)
        w += _cs(pts).extrude(ylip - y_floor).transform(np.array([[1, 0, 0, 0], [0, 0, 1, y_floor], [0, -1, 0, 0]], float))
        # hook over the top corner: a flat catch over the top face, a 45 deg lead on top (the case pushes the
        # brackets apart on the way down). It reaches Br hook over the edge of the top face.
        hk = [(xi + sx * 0.01, yt), (tip, yt), (xi + sx * 0.01, yt + abs(xi - tip))]
        w += prism_zp(hk if sx > 0 else hk[::-1], zf + 1.0, ze)
        m = w if m is None else m + w
    return m


def tw_cs(pts_uw):
    """Polygon in the mount frame (u = X - center, w = Z - center) as a CrossSection for tw_place."""
    p = np.array([(u, -w) for u, w in pts_uw], float)
    if np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) < 0:
        p = p[::-1]                                                     # counterclockwise
    return _cs(p)


def tw_place(cs, y0, y1, rot=0.0):
    """A tw_cs CrossSection turned rot deg (from +Z toward +X) about the twist axis, extruded from y0 up to y1."""
    xc, zc = TW["c"]
    return cs.rotate(rot).extrude(y1 - y0).transform(np.array([[1, 0, 0, xc], [0, 0, 1, y0], [0, -1, 0, zc]], float))


def tw_turn(M, deg):
    """Turn a solid deg (from +Z toward +X) about the twist axis."""
    xc, zc = TW["c"]
    return M.translate([-xc, 0, -zc]).rotate([0, deg, 0]).translate([xc, 0, zc])


def _vdisc(r):
    """A disc with its rear (+Z) part cut to a 45 deg V, the point on the circle: it prints on its back end."""
    R = 40.0
    return m3.CrossSection.circle(r, 96) ^ tw_cs([(-R, -R), (R, -R), (R, r - R), (0.0, r), (-R, r - R)])


def _sector(r0, r1, a0, a1, n=48):
    """A ring sector in the mount frame from angle a0 to a1 (deg, from +Z toward +X), as a tw_cs CrossSection."""
    t = np.radians(np.linspace(a0, a1, n))
    return tw_cs([(r1 * math.sin(x), r1 * math.cos(x)) for x in t] + [(r0 * math.sin(x), r0 * math.cos(x)) for x in t[::-1]])


def tw_lug_cs(grow=0.0):
    """The lug on the +X side of the pedestal: a ring sector out to r_lug, +-lug_a. grow > 0: the outline grown that
    much (keyways and the space it sweeps)."""
    T = TW
    cs = _sector(T["r_neck"] - 0.5, T["r_lug"], 90.0 - T["lug_a"], 90.0 + T["lug_a"])
    return cs.offset(grow, m3.JoinType.Round) if grow else cs


def tw_y():
    """(bottom, top) of the lugs."""
    yt = PANEL_IN - TW["gap"]
    return yt - TW["lug_t"], yt


def _tw_revolve(pts_ry):
    """A solid of revolution about the twist axis from a profile [(r, y)]."""
    xc, zc = TW["c"]
    M = m3.Manifold.revolve(m3.CrossSection([np.asarray(pts_ry, float)], m3.FillRule.NonZero), 144)
    return M.transform(np.array([[1, 0, 0, xc], [0, 0, 1, 0], [0, -1, 0, zc]], float))


def tw_core(style="upright"):
    """The pedestal and the two lugs, and the seat. upright (the camera mount, it prints base down): a round pedestal,
    a 45 deg cone that sits in the countersink of the hole and flares out to the round puck (radius R_b, top TW_TOP).
    side (the head-off base, it prints on its -X side): the pedestal with a 45 deg V on its -X side and a flat seat
    ring on the panel top."""
    T = TW
    yl0, yl1 = tw_y()
    if style == "upright":
        rn, R = T["r_neck"], T["R_b"]
        m = _tw_revolve([(0.0, yl0), (rn, yl0), (rn, TW_CONE_Y), (R, TW_CONE_Y + R - rn), (R, TW_TOP), (0.0, TW_TOP)])
    else:
        m = tw_place(_vdisc(T["r_neck"]).rotate(270.0), yl0, TOP + 0.01)
        m += tw_place(_vdisc(T["seat_side"]).rotate(270.0), TOP, TOP + T["lift"] + 0.01)
    ch = T["ramp"]                                                     # the top edges of the lugs: 45 deg ramps for the bumps
    lug = m3.Manifold.batch_hull([tw_place(tw_lug_cs(), yl0, yl1 - ch), tw_place(tw_lug_cs(-ch), yl1 - 0.01, yl1)])
    B = T["bump"]
    d = T["notch"]
    v = d + B["tip"] / 2 + 0.1
    notch = prism_x([(yl1 + 0.01, -v), (yl1 + 0.01, v), (yl1 - d, B["tip"] / 2 + 0.1), (yl1 - d, -B["tip"] / 2 - 0.1)],
                    T["c"][0] + B["r"][0] - 0.5, T["c"][0] + T["r_lug"] + 1.0).translate([0, 0, T["c"][1]])
    lug -= notch
    return m + lug + tw_turn(lug, 180.0)


def _round_brackets():
    """Two side brackets on the puck, their outer faces on the puck circle: a lip at each corner of the case and a
    hook over each top corner (clear of the USB port). The brackets spread to let the case in from the top; the hooks
    snap over its top face. Each hook has a 45 deg underside and a flat catch of hook_flat at its tip (it prints
    standing up)."""
    C, Br, T = CAM, CAM["brk"], TW
    x0, x1, y0, y1, z0, z1 = cam_box()
    xc, zc = T["c"]
    disc = m3.CrossSection.circle(T["R_b"], 144).translate([xc, -zc])
    zf, zb = z0 - Br["clr"], z1 + Br["clr"]
    lip = T["lip"]
    yt = y1 + Br["gap"]                                   # underside of the hooks, over the top face of the case
    ty = cam_to_body()
    yb = TW_TOP - 0.01
    out = []
    for sx, xi in ((-1, x0 - Br["clr"]), (1, x1 + Br["clr"])):
        X = lambda a, b: sorted((a, b))
        xe = ty[0, 1] * (C["top_y"][1] if sx < 0 else C["top_y"][0]) + ty[0, 3]   # edge of the top face
        tip = xe - sx * Br["hook"]
        L = abs(xi - tip)
        f = min(T["hook_flat"], L)
        wall = _plan_cs(*X(xi, xi + sx * 6.0), zf - lip, zb + lip, 0.0) ^ disc
        out.append(_plan_cut(wall, yb, yt + L + T["hook_tip"]))
        for za, zb_ in ((zf - lip, zf), (zb, zb + lip)):   # lips at the corners of the case
            out.append(_plan_cut(_plan_cs(*X(xi - sx * T["lip_in"], xi + sx * 0.01), za, zb_, 0.0) ^ disc, yb, y0 + Br["lip_h"]))
        e = T["hook_tip"]                                 # a vertical face at the tip (no knife edge)
        hk = [(xi + sx * 0.01, yt - (L - f)), (xi - sx * (L - f), yt), (tip, yt), (tip, yt + e), (xi + sx * 0.01, yt + L + e)]
        out.append(prism_zp(hk if sx < 0 else hk[::-1], zf + 1.0, zb + lip) ^ _plan_cut(disc, 0.0, 200.0))
    return union(out)


def build_camera_mount():
    """The twist mount: a pedestal through the round hole in the panel with two lugs under the panel top, a 45 deg
    cone in the countersink of the hole that flares out to a round puck, a pocket for the case in the puck top, two
    round side brackets for the case. The lock is the same when the mount is turned 180 deg (lens to the rear)."""
    T, Br = TW, CAM["brk"]
    x0, x1, y0, y1, z0, z1 = cam_box()
    c = Br["clr"]
    pocket = mbox(x0 - c, x1 + c, TW_TOP - T["pocket"], TW_TOP + 1.0, z0 - c, z1 + c)
    return (tw_core("upright") - pocket) + _round_brackets()


def tw_tab(sign=1.0):
    """The spring tab of the +X lug (in the panel top, along Z): (tab, slits) as (u0, u1, w0, w1) boxes. The lug comes
    from the keyway side to the bump at w = 0; the tab root is on the far side."""
    t = TW["tab"]
    s = t["slit"]
    a, b = -t["free"], t["root"]
    boxes = [(t["r0"], t["r1"], a, b), (t["r0"] - s, t["r0"], a - s, b), (t["r1"], t["r1"] + s, a - s, b), (t["r0"] - s, t["r1"] + s, a - s, a)]
    if TW["twist"] < 0:                                              # the keyway is on the +Z side: mirror in w
        boxes = [(u0, u1, -w1, -w0) for u0, u1, w0, w1 in boxes]
    return boxes[0], boxes[1:]


def _tw_box(u0, u1, w0, w1, y0, y1):
    return tw_place(tw_cs([(u0, w0), (u1, w0), (u1, w1), (u0, w1)]), y0, y1)


def tw_socket_cuts():
    """The holes in the panel: the round hole with a 45 deg countersink, two keyways, the U slits of the two tabs, the
    thinning under the tabs."""
    T = TW
    k = tw_lug_cs(T["clr"])
    tab, slits = tw_tab()
    sl = union_cs([tw_cs([(u0, w0), (u1, w0), (u1, w1), (u0, w1)]) for u0, u1, w0, w1 in slits])
    cs = m3.CrossSection.circle(T["r_hole"], 96) + (k + k.rotate(180.0)).rotate(T["twist"]) + sl + sl.rotate(180.0)
    out = [tw_place(_close(cs, 0.6), PANEL_IN - 1, TOP + 1)]           # no web under 1.2 mm between the cuts
    out.append(m3.Manifold.batch_hull([tw_place(m3.CrossSection.circle(T["r_hole"], 144), TOP - T["cs"], TOP - T["cs"] + 0.01),
                                       tw_place(m3.CrossSection.circle(T["r_hole"] + T["cs"] + 1.0, 144), TOP + 1.0, TOP + 1.01)]))   # 45 deg countersink: the cone seat
    thin = _tw_box(*tab, PANEL_IN - 1, TOP - T["tab"]["t"])
    return union(out + [thin, tw_turn(thin, 180.0)])


def tw_socket_parts(which="all"):
    """Under the panel: the bump on each tab, a stop at the end of the turn for each lug. which: all, bumps, stops."""
    T, B = TW, TW["bump"]
    yl0, yl1 = tw_y()
    ytip = yl1 - T["notch"] - T["preload"]
    ytab = TOP - T["tab"]["t"]
    h = ytab - ytip
    bump = prism_x([(ytab + 0.01, -(h + B["tip"] / 2)), (ytab + 0.01, h + B["tip"] / 2), (ytip, B["tip"] / 2), (ytip, -B["tip"] / 2)],
                   T["c"][0] + B["r"][0], T["c"][0] + B["r"][1]).translate([0, 0, T["c"][1]])
    r1 = T["tab"]["r0"] - T["tab"]["slit"]
    k = 1.0 if T["twist"] < 0 else -1.0                              # the lug turns this way (in angle) to the lock
    a0 = 90.0 + k * (T["lug_a"] + math.degrees(T["stop_clr"] / T["r_hole"]))   # past the leading edge of the lug
    stop = tw_place(_sector(T["r_hole"], r1, *sorted((a0, a0 + k * 16.0))), yl0 - 0.3, PANEL_IN + 0.01)
    one = dict(all=bump + stop, bumps=bump, stops=stop)[which]
    return one + tw_turn(one, 180.0)


def tw_keepout():
    """The space the pedestal and the lugs pass through under the panel top, from the drop-in to the lock."""
    T = TW
    yl0 = tw_y()[0]
    cs = m3.CrossSection.circle(T["r_neck"] + T["clr"], 96)
    for a in np.linspace(0.0, T["twist"], 21):
        cs += tw_lug_cs(T["clr"]).rotate(float(a)) + tw_lug_cs(T["clr"]).rotate(float(a) + 180.0)
    return tw_place(cs, yl0 - 0.4, PANEL_IN + 0.01)


def _low_dovetail(clr, y):
    """The dovetail tabs on the rear edges of the cradle walls from y[0] to y[1] (clr > 0: the grooves in the base
    plate)."""
    L, Br = CAM_LOW, CAM["brk"]
    T, P = L["tab"], L["plate"]
    x0, x1 = cam_box(True)[:2]
    z0 = P["z"][0]
    ya, yb = y
    out = []
    for xc in ((x0 - Br["clr"] - Br["t"] / 2), (x1 + Br["clr"] + Br["t"] / 2)):
        a, b = T["w0"] / 2 + clr, T["w1"] / 2 + clr        # narrow at the wall, wide at the tip
        pts = [(xc - a, z0 - 0.01), (xc + a, z0 - 0.01), (xc + b, z0 + T["d"] + clr), (xc - b, z0 + T["d"] + clr)]
        out.append(prism_y(pts, ya, yb))
    return union(out)


def _low_pins(clr=0.0):
    """The filament pins: along X through the plate and the tabs, from each side of the plate."""
    L = CAM_LOW
    P, Pn, T = L["plate"], L["pin"], L["tab"]
    zc = P["z"][0] + T["d"] / 2
    return union([mcyl("x", *sorted((sx * Pn["x0"], sx * (P["x"] + 1.0))), Pn["d"] / 2 + clr, Pn["y"], zc, 16) for sx in (-1, 1)])


def build_camera_base_low():
    """The base of the head-off mount: the twist pedestal and lugs, a plate 0.7 over the panel from the socket to the
    front edge (left of the button), a chin over the front edge, a front plate down the front of the body with the
    two grooves (closed at the bottom: the stop), the pin holes. It prints on its -X side: the lug on that side is on
    the bed, and the V of the pedestal points down."""
    L, T = CAM_LOW, TW
    P = L["plate"]
    yb, yt = TOP + T["lift"], LOW_TOP
    xc, zc = T["c"]
    xbed = xc - T["r_lug"] * math.cos(math.radians(T["lug_a"])) + 0.05    # the chord of the -X lug
    hw = T["base_hw"]
    m = tw_core("side")
    m += prism_y(rrect_pts(xbed - 2.0, xc + T["base_hx"], zc - hw, zc + hw, T["base_r"]), yb, yt)      # over the socket
    m += prism_y(rrect_pts(xbed - 2.0, L["arm_x1"], ZF_IN, zc, T["base_r"]), yb, yt)                     # the arm to the front
    m += _chin(xbed, P["x"], P["z"][0], yt)
    m += mbox(xbed, P["x"], P["y0"], TOP - CAM["base"]["chin"] + 0.5, *P["z"])          # to the bed on the -X side
    m -= _low_dovetail(L["tab"]["clr"], (P["y0"] - 1.0, yt + 1.0))
    m = m ^ mbox(xbed, 100, -100, 200, -200, 200)                       # the bed side flat
    return m - _low_pins(L["pin"]["clr"])


def build_camera_cradle_low():
    """The cradle of the head-off mount: a floor under the case, the side brackets with the hooks, carried back to the
    base plate; dovetail tabs on their rear edges, the pin holes. It prints on its rear edges: below and above the
    base plate the walls and the floor go back as far as the tabs."""
    L, Br = CAM_LOW, CAM["brk"]
    x0, x1, y0, y1, z0, z1 = cam_box(True)
    yf = y0 - 0.05 - L["floor_t"]
    zr = L["plate"]["z"][0]
    ze = zr + L["tab"]["d"]                                # the print bed
    xa, xb = x0 - Br["clr"] - Br["t"], x1 + Br["clr"] + Br["t"]
    ytop = cam_box(True)[3] + Br["gap"] + 5.0
    m = _case_brackets(True, yf, ze)
    for xi, xo in ((xa, xa + Br["t"]), (xb - Br["t"], xb)):              # the walls go back to the base plate
        m += mbox(xi, xo, yf, ytop, z1, zr)
        m += mbox(xi, xo, LOW_TOP, ytop, zr - 0.01, ze)                  # over the base: the cradle sits on it
    m += mbox(xa, xb, yf, y0 - 0.05, z0 - Br["clr"] - Br["lip_front"], zr)   # floor (a bridge between the tabs in the print)
    m += _low_dovetail(0.0, (yf, ytop))
    return m - _low_pins(0.05)


# Logo on the panel top (user request: the LineChef avatar, reference/logo/linechef.jpg): two inlays printed flat in
# two colors (the white ring and M, the red ring and J), glued into a pocket in the top face. The pocket prints on
# the bed side of the panel (its floor bridges over it). Robot frame center (x, z); the logo reads from the rear. It is
# in the front right corner of the flat top (rev 0.24: the camera socket is at its old place). The panel 3MF has a
# support blocker over the pocket (write_panel_3mf). The pocket is one 0.2 mm layer deeper than the inlay
# (room for the glue) and 0.25 mm wider on each side (rev 0.24 at 0.15 was too tight).
LOGO = dict(file=os.path.join(REF, "logo", "linechef.jpg"), d=26.0, c=(18.3, -20.5), depth=0.8, pocket=1.0, clr=0.25, min_w=0.6)


def logo_shapes():
    """{'white', 'red'}: CrossSections in mm (u right, v up), centered. Traced from the image; features under
    min_w (thin tips, the shading line in the M) are rounded away, so a 0.4 or 0.5 mm nozzle prints them."""
    import contourpy
    import matplotlib.image as mi
    from scipy.ndimage import gaussian_filter
    a = mi.imread(LOGO["file"]).astype(float)[..., :3]
    mx, mn = a.max(2), a.min(2)
    masks = dict(white=(mn > 90) & (mx - mn < 50), red=(a[..., 0] > 90) & (a[..., 0] - np.maximum(a[..., 1], a[..., 2]) > 45))
    h, w = mn.shape
    k = LOGO["d"] / max(h, w)
    out = {}
    for n, m in masks.items():
        lines = contourpy.contour_generator(z=gaussian_filter(m.astype(float), 0.8)).lines(0.5)
        polys = [np.c_[(L[:, 0] - w / 2) * k, (h / 2 - L[:, 1]) * k] for L in lines if len(L) > 3]
        cs = m3.CrossSection(polys, m3.FillRule.EvenOdd)
        e = LOGO["min_w"] / 2
        out[n] = cs.offset(e).offset(-e).offset(-e).offset(e).simplify(0.02)
    return out


def _logo_place(cs, y0, y1):
    """A CrossSection on the panel top between heights y0 and y1, in the design frame."""
    cx, cz = LOGO["c"]
    T = np.array([[1, 0, 0, cx], [0, 0, 1, y0], [0, -1, 0, cz]], float)   # u -> +X, v -> -Z (robot front up), w -> +Y
    return flip_x(cs.extrude(y1 - y0).transform(T))


def logo_pocket():
    S = logo_shapes()
    return _logo_place((S["white"] + S["red"]).offset(LOGO["clr"]), TOP - LOGO["pocket"], TOP + 1)


def build_logo(color):
    return _logo_place(logo_shapes()[color], TOP - LOGO["pocket"], TOP - LOGO["pocket"] + LOGO["depth"])


def build_panel(with_latch=True):
    P = panel_outer() - prism_y(plan(WALL), SEAM - 1, PANEL_IN)
    P -= port_cuts() + button_cuts() + keycap_hole() + tw_socket_cuts() + logo_pocket()
    P += (panel_forks() + button_arm() + battery_clamp()) - lid_keepout() - tw_keepout()
    P += tw_socket_parts()
    P += lid_hooks()
    if with_latch:
        P += latch_hook()
    return P - latch_slits()


def latch_force():
    """Latch tongue: a cantilever in the panel top (k = 3EI/L^3) from its root to the hook. Forces in N."""
    C = LATCH
    L = (ZR_IN - C["rib_d"] - C["gap"] - C["hook_d"] / 2) - C["root_z"]
    b, t = 2 * C["hw"], PANEL_T
    k = 3 * PI.E_PLA * (b * t ** 3 / 12) / L ** 3
    d = C["rib_top"] - C["hook_bot"] + 0.1                 # the tongue lifts this much as the hook passes the rib
    F = k * d
    phi = math.atan(PI.MU_PLA)
    return dict(tongue_k_N_per_mm=round(k, 2), lift_mm=round(d, 2), lift_N=round(F, 1),
                slide_on_N=round(F * math.tan(math.radians(45) + phi), 1), strain_pct=round(100 * 1.5 * t * d / L ** 2, 2))


def tw_force():
    """Camera socket tabs: cantilevers in the panel top (k = 3EI/L^3) from the root to the bump. Forces in N, each tab."""
    T, t = TW, TW["tab"]
    L, b = t["root"], t["r1"] - t["r0"]
    k = 3 * PI.E_PLA * (b * t["t"] ** 3 / 12) / L ** 3
    ride = T["notch"] + T["preload"]                       # the bump lifts this much on the top of the lug
    return dict(tab_k_N_per_mm=round(k, 2), ride_mm=round(ride, 2), ride_N=round(k * ride, 1), hold_N=round(k * T["preload"], 1),
                strain_pct=round(100 * 1.5 * t["t"] * ride / L ** 2, 2), twist_deg=abs(T["twist"]))


# --------------------------------------------------------------------------
# Models (electronics, robot)
# --------------------------------------------------------------------------
def rbox(axis, x0, x1, y0, y1, z0, z1, r, n=16):
    """Box with round edges along one axis (radius r): the hull of four cylinders."""
    cs = []
    if axis == "z":
        for x in (x0 + r, x1 - r):
            for y in (y0 + r, y1 - r):
                cs.append(mcyl("z", z0, z1, r, x, y, n))
    elif axis == "x":
        for y in (y0 + r, y1 - r):
            for z in (z0 + r, z1 - r):
                cs.append(mcyl("x", x0, x1, r, y, z, n))
    else:
        for x in (x0 + r, x1 - r):
            for z in (z0 + r, z1 - r):
                cs.append(mcyl("y", y0, y1, r, x, z, n))
    return m3.Manifold.batch_hull(cs)


R_BEND = 2.0          # smallest bend radius of a designed route (jumper wire 1.4 mm): about 1.4 x its size
R_SLACK = 1.35        # smallest bend radius in the slack arches and loops of the pack jumpers
WIRE_PITCH = 1.5      # center distance of wires side by side


def round_corners(pts, R=R_BEND, n=8):
    """Polyline with each corner replaced by a circular arc of radius R. Where two corners need more than the
    segment between them, both arcs get smaller. Returns (points, the smallest radius used)."""
    P = [np.asarray(p, float) for p in pts]
    P = [p for k, p in enumerate(P) if k == 0 or np.linalg.norm(p - P[k - 1]) > 1e-6]
    m = len(P)
    turn, t = [0.0] * m, [0.0] * m
    for i in range(1, m - 1):
        u, v = P[i] - P[i - 1], P[i + 1] - P[i]
        turn[i] = math.acos(float(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
        t[i] = R * math.tan(turn[i] / 2) if turn[i] > 1e-3 else 0.0
    for i in range(m - 1):                                  # share each segment between its two corners
        L = np.linalg.norm(P[i + 1] - P[i])
        if t[i] + t[i + 1] > L:
            k = L / (t[i] + t[i + 1])
            t[i], t[i + 1] = t[i] * k, t[i + 1] * k
    out, rmin = [P[0]], 1e9
    for i in range(1, m - 1):
        if t[i] < 1e-6:
            out.append(P[i])
            continue
        u = (P[i] - P[i - 1]) / np.linalg.norm(P[i] - P[i - 1])
        v = (P[i + 1] - P[i]) / np.linalg.norm(P[i + 1] - P[i])
        r = t[i] / math.tan(turn[i] / 2)
        rmin = min(rmin, r)
        w = (v - u) / np.linalg.norm(v - u)
        ctr = P[i] + w * (r / math.cos(turn[i] / 2))
        a1, a2 = P[i] - u * t[i] - ctr, P[i] + v * t[i] - ctr
        for sv in np.linspace(0, 1, n):
            ang = turn[i] * sv
            out.append(ctr + (math.sin(turn[i] - ang) * a1 + math.sin(ang) * a2) / math.sin(turn[i]))
    out.append(P[-1])
    out = [p for k, p in enumerate(out) if k == 0 or np.linalg.norm(p - out[k - 1]) > 1e-6]
    return np.array(out), rmin


def tube(pts, r=WIRE_R, rounded=True):
    """A wire along a polyline: hulls of spheres at the points (corners rounded first)."""
    P = round_corners(pts)[0] if rounded else np.asarray(pts, float)
    S = [m3.Manifold.sphere(r, 10).translate(list(p)) for p in P]
    return union([m3.Manifold.batch_hull([a, b]) for a, b in zip(S[:-1], S[1:])])


# Pi header: 2x20, pin 1 at the SD card end (rear), odd pins in the inner row, even pins at the board edge (down).
HDR_BASE_X = (PI_PCB_TOP_X + 0.1, PI_PCB_TOP_X + 2.6)
HOUSING_END = HDR_BASE_X[1] + DUPONT_L             # Dupont housing on the header pins
EXIT_X = HOUSING_END + 0.8                          # the wire leaves the housing straight for 0.8 mm


def pin_yz(n):
    k = (n - 1) // 2
    return STACK_Y0 + 3.5 + (1.27 if n % 2 else -1.27), HDR_ZC + 25.4 - 1.27 - 2.54 * k


def bb_pin_z(k):
    """BiBoard header pin k, from the rear: TX2, RX2, GND, +5V, +5V (wiring blueprint; the direction is not verified)."""
    return HDR["z1"] - 1.27 - 2.54 * k


BB_X = (HDR["x0"] + HDR["x1"]) / 2
AMP_PLUG_Y = [AMP_Y0 + AMP["h"] - v for v in (6.6, 8.6, 10.6, 12.6, 14.6)]   # G, V, BCLK, LRCLK, DIN (G at the top)
AMP_PLUG_Z0 = AMP_Z[0] - AMP_L["plug_out"] + AMP_L["ph5"][0]                  # front face of the I2S plug
# BCLK and LRCLK: one wire from Pi pin 12 (35) to a soldered splice, then one wire to the mic and one to the amp
# (reference/g2-wiring-blueprint.html). The splices are vertical heat-shrink sleeves in the right well:
# the Pi wire and the amp wire go into the bottom end, the mic wire into the top end.
SPLICE = dict(bclk=(21.2, 3.0), lrclk=(21.0, -13.0), y=(39.0, 45.0), r=1.25)
# Lanes in the right well (X): the mic wires run rearward as a flat stack at MIC_RIB, beside the BiBoard plugs; the
# UART wires rise at UART_X; the amp ribbon runs rearward on edge at AMP_RUN_X, inside the floor
# notch for the BiBoard header (X 23.9). A wire that crosses further forward takes a lane further out, so no two
# lanes cross; DIN goes up at once.
MIC_RIB, UART_X, FLOOR_WIRE = 23.4, 27.0, FLOOR_Y1 + 0.75
AMP_DROP, AMP_FRONT_Z, AMP_RUN_X = 8.0, ZF_IN + 2.3, 23.6
AMP_JOG = (11.0, -26.0)      # the ribbon turns rearward here (past the front post) and runs behind the Grove plug space   # the amp ribbon: step down, the run behind the front wall, the run in the left well
PACK_L = 100.0        # the jumpers come from a pack of 10 cm wires (female-female): wire length between the housings
LONG_WIRES = {("mic", "GND"), ("mic", "3V")}     # LONG_L


def pack_len(key):
    return LONG_L if key in LONG_WIRES else PACK_L


def into_pin(n):
    """Last points of a route into the housing of Pi pin n: along -X out of the right well."""
    y, z = pin_yz(n)
    return [(EXIT_X, y, z), (HOUSING_END, y, z)]


def splice_end(t, top):
    x, z = SPLICE[t]
    return (x, SPLICE["y"][1] if top else SPLICE["y"][0], z)


# Wires: (group, label, color, points from the far end to the Pi header or a splice).
# Pin map: reference/g2-wiring-blueprint.html (the user's wiring blueprint).
def wire_routes():
    W = []
    # BiBoard: TX2 -> Pi 10 (RXD), RX2 -> Pi 8 (TXD), GND -> Pi 6. Up out of the plugs to the right wall, rearward
    # over the right well, down, into the housings along -X. The order turns over (the rear BiBoard pin goes to the
    # front Pi pin), so each wire runs rearward at its own height.
    # wire colors from the user photo: black, white, gray in a row on the plug (black taken as GND)
    for n, k, col, lab, lvl in ((10, 0, "#9ea0a4", "TX2", 45.6), (8, 1, "#f2f2ef", "RX2", 47.2), (6, 2, "#1d1d1f", "GND", 48.8)):
        y, z = pin_yz(n)
        zb = bb_pin_z(k)
        pts = [(BB_X, BB_PLUG["y"][1], zb), (UART_X, lvl, zb), (UART_X, lvl, z), (UART_X, y, z)] + into_pin(n)
        W.append(("uart", lab, col, pts))
    # Amp: a flat cable (bonded wires, user photo) from the I2S plug at the front end of the amp, on edge all the way
    # (G at the top, 2.0 apart): it steps down AMP_DROP in a gentle S, runs forward to the front wall, across behind the
    # front wall under the mic plugs and wires, rearward past the front post (AMP_JOG), across behind the Grove plug
    # space, and rearward along the left well (AMP_RUN_X). No twist: every turn
    # bends it across its face. In the left well each wire turns inward at its own height (DIN at the front, V at the
    # rear) and goes up or down into its pin or splice.
    order = ("G", "V", "BCLK", "LRC", "DIN")
    xc, xp = AMP_CABLE_X, EXIT_X + 2.2                     # the ribbon at the plug; a wire goes up or down here into its housing
    for i, (lab, col) in enumerate(zip(order, ("#1d1d1f", "#d83a34", "#3a6fd8", "#2e9b4f", "#f0c419"))):   # cable colors (user photo)
        y0 = AMP_PLUG_Y[i]
        y = y0 - AMP_DROP
        pts = [(xc, y0, AMP_PLUG_Z0), (xc, y0, AMP_PLUG_Z0 - 2.0), (xc, y, AMP_PLUG_Z0 - 12.0), (xc, y, AMP_FRONT_Z),
               (AMP_JOG[0], y, AMP_FRONT_Z), (AMP_JOG[0], y, AMP_JOG[1])]
        if lab == "DIN":                                    # the bottom wire turns rearward first, inside the others
            yp, zp = pin_yz(40)
            W.append(("amp", lab, col, pts + [(xp, y, AMP_JOG[1]), (xp, yp, zp)] + into_pin(40)))
            continue
        pts.append((AMP_RUN_X, y, AMP_JOG[1]))
        if lab == "LRC" or lab == "BCLK":                   # up into the bottom of its splice sleeve
            t = "lrclk" if lab == "LRC" else "bclk"
            sx, sz = SPLICE[t]
            pts += [(AMP_RUN_X, y, sz - 5.0), (sx, y, sz - 2.5), (sx, SPLICE["y"][0] - 1.5, sz - 0.5), splice_end(t, False)]
        else:
            n = {"G": 14, "V": 2}[lab]
            yp, zp = pin_yz(n)
            pts += [(AMP_RUN_X, y, zp - 5.0), (xp, y, zp - 2.5), (xp, yp, zp)] + into_pin(n)
        W.append(("amp", lab, col, pts))
    # Mic: jumpers (GND and 3V 15 cm, LONG_WIRES) from the housings on the mic header (they leave rearward), each wire at the height of its
    # pin (3V at the bottom, SEL at the top): straight inward out of the housings, across behind the front wall in front
    # of the stack, then rearward as a flat stack at MIC_RIB.
    # SEL (pin 39, to GND: left channel), DOUT (pin 38), LRCL (splice), BCLK (splice), GND (pin 9), 3V (pin 1).
    xa = MIC_RIB
    xin = EXIT_X + 2.0
    xh = MIC_HOUSING_X[1]
    # wire colors from the user photo (the pack jumpers on the mic header)
    for k, t, col, lab in ((5, 39, "#7a4a2a", "SEL"), (4, "lrclk", "#2e9b4f", "LRCL"), (3, 38, "#e8641b", "DOUT"),
                           (2, "bclk", "#3a6fd8", "BCLK"), (1, 9, "#1d1d1f", "GND"), (0, 1, "#d83a34", "3V")):
        y = MIC_PIN_Y[k]
        pts = [(xh, y, MIC_PIN_Z), (xh + 1.2, y, MIC_PIN_Z), (21.0, y, MIC_PIN_Z), (xa, y, -29.2)]
        if isinstance(t, str):                                  # up the inside of the stack into the top of the sleeve
            sx, sz = SPLICE[t]
            pts += [(xa, y, sz - 5.0), (sx + 0.6, y + 2.0, sz - 3.0), (sx + 0.6, SPLICE["y"][1] + 1.6, sz - 1.0),
                    (sx, SPLICE["y"][1] + 1.2, sz), splice_end(t, True)]
        else:
            yp, zp = pin_yz(t)
            pts += [(xa, y, zp - 3.0), (xin, y, zp - 1.6), (xin, yp + 0.6, zp)] + into_pin(t)   # in at its height, then down
        W.append(("mic", lab, col, pts))
    # The Pi end of each splice: pin 12 (GPIO18, BCLK) and pin 35 (GPIO19, LRCLK), into the bottom of the sleeve.
    for t, n, col in (("bclk", 12, "#3a6fd8"), ("lrclk", 35, "#2e9b4f")):   # the colors of the signal (not seen in a photo)
        y, z = pin_yz(n)
        sx, sz = SPLICE[t]
        if t == "bclk":         # rearward at Y 38.2, over the amp wire G, down at X 21.8
            pts = [splice_end(t, False), (21.8, 38.2, sz + 1.5), (21.8, 38.2, z - 2.0), (21.8, y, z)] + into_pin(n)
        else:                   # one quarter turn from the bottom of the sleeve into the housing of pin 35
            pts = [splice_end(t, False), (sx, y, z), (HOUSING_END, y, z)]
        W.append(("splice", t, col, pts))
    return W


def parallel_pair(center, gap, n0):
    """Two wires side by side along a center line, the offset carried along the line (no twist, no crossing)."""
    C = round_corners(center, R_BEND + gap)[0]
    T = np.gradient(C, axis=0)
    T[np.linalg.norm(T, axis=1) < 1e-9] = (0, 0, 1)
    T /= np.linalg.norm(T, axis=1)[:, None]
    nrm = np.asarray(n0, float)
    out_a, out_b = [], []
    for i, p in enumerate(C):
        nrm = nrm - np.dot(nrm, T[i]) * T[i]
        nrm /= np.linalg.norm(nrm)
        out_a.append(p + nrm * gap / 2)
        out_b.append(p - nrm * gap / 2)
    return np.array(out_a), np.array(out_b)


def parallel_ribbon(center, n, pitch, n0):
    """n wires side by side along a center line (a flat cable), the offset carried along the line (no twist).
    The corners of the center line are rounded so that the inner wire keeps R_BEND."""
    C = round_corners(center, R_BEND + pitch * (n - 1) / 2)[0]
    T = np.gradient(C, axis=0)
    T[np.linalg.norm(T, axis=1) < 1e-9] = (0, 0, 1)
    T /= np.linalg.norm(T, axis=1)[:, None]
    nrm = np.asarray(n0, float)
    out = [[] for _ in range(n)]
    for i, p in enumerate(C):
        nrm = nrm - np.dot(nrm, T[i]) * T[i]
        nrm /= np.linalg.norm(nrm)
        for k in range(n):
            out[k].append(p + nrm * pitch * (k - (n - 1) / 2))
    return [np.array(o) for o in out]


def _usb_cable(low):
    """Up out of the USB-C plug, a half circle over in the vertical plane through the two plugs, straight down
    into the micro-USB plug. The bend radius is half the plan distance between the plugs."""
    a, b = cam_usb_plug(low), pi_usb_plug()
    A = np.array([(a[0] + a[1]) / 2, a[3], (a[4] + a[5]) / 2])
    B = np.array([(b[0] + b[1]) / 2, b[3], (b[4] + b[5]) / 2])
    u = np.array([B[0] - A[0], 0.0, B[2] - A[2]])
    r = np.linalg.norm(u) / 2
    u /= 2 * r
    yc = A[1] + 4.0
    c = A + u * r
    pts = [A + [0, y, 0] for y in np.linspace(-2.0, 4.0, 4)]
    pts += [c + [0, yc - c[1], 0] - u * r * math.cos(t) + np.array([0, r * math.sin(t), 0]) for t in np.linspace(0, math.pi, 40)[1:]]
    pts += [B + [0, y, 0] for y in np.linspace(yc - B[1], -2.0, 30)[1:]]
    return [("camera", "USB", "#1d1d1f", np.array(pts))]


def camera_cable():
    """The USB cable of the camera: up out of the USB-C plug in the top of the case, rearward over the panel, down into
    the micro-USB plug in the Pi data USB port."""
    return _usb_cable(False)


def camera_cable_low():
    """The USB cable of the head-off mount: up out of the top of the case, rearward over the panel, down into the
    Pi data USB port."""
    return _usb_cable(True)


def speaker_leads():
    """The speaker lead pair: from the 2-pin plug at the rear end of the amp, up the left gallery, over the ear
    plate, into the top of the speaker body."""
    zp = AMP_Z[0] + AMP_L["ph2"][1] + AMP_L["plug_out"]           # rear face of the 2-pin plug
    yc = AMP_Y0 + AMP["h"] - 12.05
    zt = SPK_ZE + SPK["ear_t"] + 3.0                            # the leads leave the top of the rear half of the body
    center = [(AMP_CABLE_X, yc, zp), (AMP_CABLE_X, yc, 33.6), (AMP_CABLE_X, 54.6, 33.6), (-12.5, 59.9, 34.6), (-12.5, 59.9, zt - 2.2),
              (-11.0, SPK_Y0 + SPK["d"] - 0.5, zt)]
    a, b = parallel_pair(center, 2.0, (0, 1, 0))
    return [("speaker", "+", "#d83a34", a), ("speaker", "-", "#1d1d1f", b)]


HOUSING_MESH = {}     # ("pi", pin) / ("mic", k) / ("bb", k) -> Dupont housing mesh, set by build_models()
MIC_PIN_OF = {"3V": 0, "GND": 1, "BCLK": 2, "DOUT": 3, "LRCL": 4, "SEL": 5}
BB_PIN_OF = {"TX2": 0, "RX2": 1, "GND": 2}


def wire_sub(lab):
    return lab.split()[0].lower().replace("+", "pos").replace("-", "neg")


def wire_housings(g, lab):
    """The Dupont housings of a wire: [(end, HOUSING_MESH key)]. 'pi' = on the Pi header, 'dev' = on the board."""
    out = []
    to = WIRE_TO[(g, lab)]
    if to.startswith("pin "):
        out.append(("pi", ("pi", int(to.split()[1]))))
    if g == "mic":
        out.append(("dev", ("mic", MIC_PIN_OF[lab])))
    if g == "uart":
        out.append(("dev", ("bb", BB_PIN_OF[lab])))
    return out


def build_models():
    """The electronics in place. Returns (models for the checks, display parts: (model, sub, label, mesh, color))."""
    D = []
    def add(key, sub, label, M, col):
        D.append((key, sub, label, M, col))
        return M
    pisugar = union([add("pisugar_s", sub, label, M, col) for sub, label, M, col in pisugar_s_model()])
    pizero = add("pizero", "board", "Raspberry Pi Zero 2 W", stl_manifold("RaspberryPiZeroW-1.STL", STAND @ flat_pi()), "#2e9b4f")
    H = HEATSINK                                            # pin-fin heatsink on the SoC (user photo; size estimated)
    x0 = H["x0"]
    hs = mbox(x0, x0 + H["base"], *H["y"], *H["z"])
    pitch = (H["y"][1] - H["y"][0]) / H["n"]
    for a_ in range(H["n"]):
        for b_ in range(H["n"]):
            yc_, zc_ = H["y"][0] + pitch * (a_ + 0.5), H["z"][0] + pitch * (b_ + 0.5)
            hs += mbox(x0 + H["base"] - 0.01, x0 + H["h"], yc_ - H["pin"] / 2, yc_ + H["pin"] / 2, zc_ - H["pin"] / 2, zc_ + H["pin"] / 2)
    add("pizero", "heatsink", "Pi heatsink (size estimated)", hs, "#c9ccd1")
    pizero = pizero + hs
    # battery: a pouch cell with round edges, a seal flap at the front end, a disc on its face and two leads to the BAT
    # pads of the PiSugar S at the front end (the lead routes are estimates)
    bx, by, bz = BAT["x"], BAT["y"], BAT["z"]
    cell = add("battery", "cell", "1200 mAh cell", rbox("z", bx[0], bx[1], by[0], by[1], bz[0] + 2.5, bz[1], 1.6), "#b9bcc2")
    xm = (bx[0] + bx[1]) / 2
    flap = add("battery", "flap", "cell seal", rbox("z", xm - 0.5, xm + 0.5, by[0] + 1.5, by[1] - 1.5, bz[0], bz[0] + 2.6, 0.45), "#d9b34a")
    disc = add("battery", "disc", "cell disc", mcyl("x", bx[1] - 0.01, PS_PCB_X[0] - 1.85, 7.1, STACK_Y0 + 14.4, ZSD - 20.0, 40), "#c9ccd1")
    f0 = PS_PCB_X[0]
    red = [(xm + 0.7, 45.0, bz[0] + 0.3), (xm + 0.7, 45.0, bz[0] - 0.6), (f0 - 1.2, 45.4, bz[0] - 0.9),
           (f0 - 0.6, STACK_Y0 + 15.9, ZSD - 60.6)]                       # to +BAT (drawing: u 60.6, v 15.9)
    black = [(xm - 0.7, 47.5, bz[0] + 0.3), (xm - 0.7, 47.5, bz[0] - 0.8), (f0 - 1.6, 48.5, bz[0] - 1.0),
             (f0 - 1.1, 51.0, bz[0] + 1.5), (f0 - 1.1, 51.0, ZSD - 51.5),
             (f0 - 1.0, STACK_Y0 + 16.9, ZSD - 48.8)]       # under the cell, over the charger IC, to GND (u 48.8, v 16.9)
    leads = [add("battery", f"lead{i}", "cell lead", tube(P, 0.5), c) for i, (P, c) in enumerate(((red, "#d83a34"), (black, "#1d1d1f")))]
    bat = cell + flap + disc + union(leads)
    # microSD card: the part out of the holder (about 2.5 mm, not measured)
    card = add("sd_card", "card", "microSD card", rbox("x", 1.85 + STACK_DX, 2.85 + STACK_DX, 39.5, 50.5, ZSD + 0.05, ZSD + 2.5, 0.8), "#26272b")
    stack_scr = add("stack_screws", "heads", "M2.5 screw heads (size estimated)", screw_heads(), "#c8c8c8")
    # Pi header: base, the pins without a plug, a Dupont housing on each pin in use
    W = wire_routes()
    used_pins = set()
    for g, lab, col, pts in W:
        y, z = pts[-1][1], pts[-1][2]
        for n in range(1, 41):
            if abs(pin_yz(n)[0] - y) < 0.01 and abs(pin_yz(n)[1] - z) < 0.01:
                used_pins.add(n)
    base = add("pi_plugs", "header", "Pi 2x20 header", mbox(*HDR_BASE_X, PI_PLUGS["y"][0], PI_PLUGS["y"][1], *PI_PLUGS["z"]), "#1d1d1f")
    pins = union([mbox(HDR_BASE_X[1] - 0.01, HDR_BASE_X[1] + 6.0, y - 0.32, y + 0.32, z - 0.32, z + 0.32)
                  for y, z in (pin_yz(n) for n in range(1, 41))])
    add("pi_plugs", "pins", "header pins", pins, "#d9b34a")
    # The Dupont housings belong to the wires (display): they go on with their wire. The check model has them all.
    HOUSING_MESH.clear()
    for n in sorted(used_pins):
        y, z = pin_yz(n)
        HOUSING_MESH[("pi", n)] = rbox("x", HDR_BASE_X[1], HOUSING_END, y - 1.25, y + 1.25, z - 1.25, z + 1.25, 0.25, 8)
    hous = union([HOUSING_MESH[("pi", n)] for n in sorted(used_pins)])
    pi_plugs = base + pins + hous
    # BiBoard header (female, 5 pins) and three male Dupont plugs on GND, TX2, RX2
    cov = solid_cover_tris().reshape(-1, 3)
    m = (cov[:, 0] > HDR["x0"]) & (cov[:, 0] < HDR["x1"]) & (cov[:, 2] > HDR["z0"]) & (cov[:, 2] < HDR["z1"])
    hdr = mbox(HDR["x0"], HDR["x1"], float(cov[m, 1].min()) - 3.0, HDR["top"], HDR["z0"], HDR["z1"])
    hdr -= union([mbox(BB_X - 0.5, BB_X + 0.5, HDR["top"] - 3.0, HDR["top"] + 1, bb_pin_z(k) - 0.5, bb_pin_z(k) + 0.5) for k in range(5)])
    add("biboard_header", "header", "BiBoard 5-pin header (est. height)", hdr, "#0d0d0d")
    for k in (0, 1, 2):                                    # the BiBoard end of each jumper is male: a pin goes down into the socket
        pin = mbox(BB_X - 0.32, BB_X + 0.32, HDR["top"] - 2.8, BB_PLUG["y"][0] + 0.01, bb_pin_z(k) - 0.32, bb_pin_z(k) + 0.32)
        HOUSING_MESH[("bb", k)] = rbox("y", BB_X - 1.25, BB_X + 1.25, BB_PLUG["y"][0], BB_PLUG["y"][1], bb_pin_z(k) - 1.25, bb_pin_z(k) + 1.25, 0.25, 8) + pin
    bb = union([HOUSING_MESH[("bb", k)] for k in (0, 1, 2)])
    # NS4168 amp (NULLLAB photo and drawing): u along the board from the front (I2S) end, v down from the top edge
    L = AMP_L
    x0, x1 = AMP_X
    yt = AMP_Y0 + AMP["h"]
    zu = lambda u: AMP_Z[0] + u
    yv = lambda v: AMP_Y0 + AMP["h"] - v                    # upright: v down from the top edge
    pcb = rbox("x", x0, x1, AMP_Y0, yt, *AMP_Z, 1.0)
    pcb -= union([mcyl("x", x0 - 1, x1 + 1, L["hole_d"] / 2, yv(v), zu(u)) for u, v in L["holes"]])
    add("amp_ns4168", "pcb", "NS4168 amp board", pcb, "#1d1d1f")
    rings = union([mcyl("x", x1 - 0.01, x1 + 0.05, L["hole_d"] / 2 + 1.0, yv(v), zu(u)) - mcyl("x", x1 - 1, x1 + 1, L["hole_d"] / 2, yv(v), zu(u))
                   for u, v in L["holes"]])
    add("amp_ns4168", "rings", "amp hole rings", rings, "#e8e8e8")
    ph = lambda r: mbox(x1, x1 + L["ph"], yv(r[3]), yv(r[2]), zu(r[0]), zu(r[1]))
    hdrs = ph(L["ph5"]) + ph(L["ph2"])
    add("amp_ns4168", "headers", "amp PH2.0 headers", hdrs, "#efe6d2")
    p5 = mbox(x1 + 0.2, x1 + L["ph"] - 0.4, yv(L["ph5"][3]) + 0.5, yv(L["ph5"][2]) - 0.5, AMP_PLUG_Z0, zu(L["ph5"][0]) + 0.01)
    p2 = mbox(x1 + 0.2, x1 + L["ph"] - 0.4, yv(L["ph2"][3]) + 0.5, yv(L["ph2"][2]) - 0.5, zu(L["ph2"][1]) - 0.01, zu(L["ph2"][1]) + L["plug_out"])
    add("amp_ns4168", "plugs", "amp PH2.0 plugs", p5 + p2, "#fbf6ea")
    t = L["term"]
    term = mbox(x1, x1 + L["term_h"], yv(t[3]), yv(t[2]), zu(t[0]), zu(t[1]))
    add("amp_ns4168", "terminal", "amp screw terminal", term, "#2f6fd6")
    screws = union([mcyl("x", x1 + L["term_h"] - 0.01, x1 + L["term_h"] + 0.3, 1.2, yv(v), zu(32.9)) for v in (2.3, 5.9)])
    add("amp_ns4168", "screws", "terminal screws", screws, "#c8c8c8")
    ic = mbox(x1, x1 + 1.5, yv(L["ic"][3]), yv(L["ic"][2]), zu(L["ic"][0]), zu(L["ic"][1]))
    add("amp_ns4168", "ic", "NS4168 chip", ic, "#2a2a2a")
    amp = pcb + hdrs + p5 + p2 + term + screws + ic
    # SPH0645 mic board: PCB with the two corner holes and the port hole, mic part on the back face, straight header on
    # the back face at the front edge with the six Dupont housings on its pins
    M = MIC
    z0, z1, y0, y1 = M["z0"], M["z0"] + M["w"], M["y0"], M["y0"] + M["l"]
    mp = rbox("x", *MIC_X, y0, y1, z0, z1, 0.8)
    mp -= mcyl("x", MIC_X[0] - 1, MIC_X[1] + 1, 0.4, *MIC_PORT, 12)
    mp -= union([mcyl("x", MIC_X[0] - 1, MIC_X[1] + 1, M["hole_d"] / 2, y, z, 16) for y, z in MIC_HOLES])
    add("mic_sph0645", "pcb", "SPH0645 mic board", mp, "#22303f")
    can = mbox(MIC_X[1] - 0.01, MIC_X[1] + 1.0, MIC_PORT[0] - 1.33, MIC_PORT[0] + 1.33, MIC_PORT[1] - 1.75, MIC_PORT[1] + 1.75)
    add("mic_sph0645", "mic", "SPH0645 mic", can, "#c8c8c8")
    hb = mbox(MIC_HDR_X[0] - 0.01, MIC_HDR_X[1], min(MIC_PIN_Y) - 1.27, max(MIC_PIN_Y) + 1.27, MIC_PIN_Z - 1.27, MIC_PIN_Z + 1.27)
    add("mic_sph0645", "header", "mic header", hb, "#1d1d1f")
    for k, y in enumerate(MIC_PIN_Y):
        HOUSING_MESH[("mic", k)] = rbox("x", *MIC_HOUSING_X, y - 1.25, y + 1.25, MIC_PIN_Z - 1.25, MIC_PIN_Z + 1.25, 0.25, 8)
    mh = union([HOUSING_MESH[("mic", k)] for k in range(6)])
    mic = mp + can + hb + mh
    # speaker: round-edged box with the two black wings around its middle; the sound face (rear) has a grille
    z0, z1 = SPK_ZE, SPK_ZE + SPK["ear_t"]
    yc = SPK_Y0 + SPK["d"] / 2
    plate = None
    for sx in (-1, 1):
        xh = sx * (SPK["l"] / 2 - SPK["hole_in"])
        hw, r = SPK["wing_h"] / 2, SPK["wing_r"]
        ring = [(xh + r * math.cos(t), yc + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
        root = [(sx * (SPK["body_l"] / 2 - 1.0), yc + v) for v in (-hw, hw)]
        w = m3.CrossSection.hull(_cs(ring + root)).extrude(z1 - z0).translate([0, 0, z0])
        w -= mcyl("z", z0 - 1, z1 + 1, SPK["hole_d"] / 2, xh, yc, 16)
        plate = w if plate is None else plate + w
    add("speaker", "plate", "speaker wings", plate, "#26272b")
    ze = SPK_BODY_Z[1]
    body = rbox("z", -SPK["body_l"] / 2, SPK["body_l"] / 2, SPK_Y0 + 0.5, SPK_Y0 + SPK["d"] - 0.5, SPK_BODY_Z[0], ze, 3.0)
    body -= rbox("z", -SPK["body_l"] / 2 + 2.5, SPK["body_l"] / 2 - 2.5, SPK_Y0 + 3.0, SPK_Y0 + SPK["d"] - 3.0, ze - 0.6, ze + 1, 2.0)
    add("speaker", "body", "NULLLAB 3 W speaker", body, "#3a3b40")
    mesh = rbox("z", -SPK["body_l"] / 2 + 2.5, SPK["body_l"] / 2 - 2.5, SPK_Y0 + 3.0, SPK_Y0 + SPK["d"] - 3.0, ze - 0.6, ze - 0.4, 2.0)
    mesh -= union([mcyl("z", ze - 1, ze + 1, 0.45, x, y, 8) for x in np.arange(-9.0, 9.1, 1.5) for y in np.arange(SPK_Y0 + 4.5, SPK_Y0 + SPK["d"] - 4.4, 1.5)])
    add("speaker", "grille", "speaker grille", mesh, "#5a5b60")
    spk = plate + body + mesh
    cam = union([stl_manifold(f, cam_to_body(), ref=os.path.join(os.path.dirname(ROOT), "reference")) for f in ("AiCamera250116-down.stl", "AiCamera250116-up.stl")])
    add("camera", "case", "Petoi AI Vision Module in its case", cam, "#2b2d33")
    models = dict(pizero=pizero, pisugar_s=pisugar, stack_screws=stack_scr, battery=bat, sd_card=card, pi_plugs=pi_plugs, camera=cam,
                  biboard_header=hdr, biboard_plug=bb, speaker=spk, amp_ns4168=amp, mic_sph0645=mic)
    # wires
    groups = {}
    for g, lab, col, pts, smooth in all_routes():
        sub = wire_sub(lab)
        T = add(f"wires_{g}", sub, f"{g} wire {lab}", tube(pts, r=USB_R if g == "camera" else WIRE_R, rounded=not smooth), col)
        groups[g] = groups.get(g, []) + [T]
        for end, hk in wire_housings(g, lab):                  # its Dupont housings go on with it
            add(f"wires_{g}", f"{sub}_{end}", f"{g} wire {lab}: Dupont housing", HOUSING_MESH[hk], "#3a3b40")
    groups["camera"].append(add("wires_camera", "plug_cam", "USB-C plug in the camera", rbox("y", *cam_usb_plug(), 1.0), "#1d1d1f"))
    groups["camera"].append(add("wires_camera", "plug_pi", "micro-USB plug in the Pi", rbox("y", *pi_usb_plug(), 1.0), "#1d1d1f"))
    sleeves = union([mcyl("y", *SPLICE["y"], SPLICE["r"], SPLICE[t][0], SPLICE[t][1], 16) for t in ("bclk", "lrclk")])
    groups["splice"].append(add("wires_splice", "sleeves", "solder splices (heat shrink)", sleeves, "#f2f2ef"))   # white heat shrink (user photo)
    for g, Ts in groups.items():
        models[f"wires_{g}"] = union(Ts)
    return models, D


# --------------------------------------------------------------------------
# Wire settling: each pack jumper is PACK_L long. It starts on its guide route (shorter) and grows to PACK_L,
# pushed out of every part and every other wire, with a little gravity. The excess finds free space, as real
# slack does. Ends: fixed, straight out of the housing for 2 mm.
# --------------------------------------------------------------------------
GRID_H = 0.5
SETTLE = dict(seg=1.0, iters=5000, grow=0.6, gravity=0.006, bend=0.5, spans=(1, 2, 3, 4, 6, 8), clear=0.35, wire_gap=1.62,
              end_nodes=4, length_passes=10)


def obstacle_field(solids):
    """Signed distance (mm) to the solids on a grid inside the body: > 0 in free space."""
    from matplotlib.path import Path
    from scipy.ndimage import distance_transform_edt
    h = GRID_H
    xs, ys, zs = np.arange(-IN_A - 1.0, IN_A + 1.01, h), np.arange(27.0, 62.61, h), np.arange(-36.6, 55.11, h)
    occ = np.zeros((len(xs), len(ys), len(zs)), bool)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    pts = np.c_[X.ravel(), Y.ravel()]
    for k, z in enumerate(zs):
        inside = np.zeros(len(pts), bool)
        for poly in solids.slice(float(z)).to_polygons():
            if len(poly) > 2:
                inside ^= Path(np.asarray(poly)).contains_points(pts)
        occ[:, :, k] = inside.reshape(X.shape)
    occ[:, ys < FLOOR_Y1 + 0.05, :] = True                 # the floor, also over its openings
    sdf = (distance_transform_edt(~occ) - distance_transform_edt(occ)) * h
    g = np.gradient(sdf, h)
    return dict(o=np.array([xs[0], ys[0], zs[0]]), h=h, sdf=sdf, g=g)


def _field_at(F, P):
    from scipy.ndimage import map_coordinates
    idx = ((P - F["o"]) / F["h"]).T
    d = map_coordinates(F["sdf"], idx, order=1, mode="nearest")
    g = np.stack([map_coordinates(gi, idx, order=1, mode="nearest") for gi in F["g"]], axis=1)
    return d, g


def _resample(P, n):
    P = np.asarray(P, float)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, P[:, i]) for i in range(3)], axis=1)


def settle_wires(F, free, fixed, joints):
    """free: [(key, guide points, target length)]; fixed: [polylines]; joints: [(center, radius)] where wires may meet.
    Returns {key: settled polyline}."""
    from scipy.spatial import cKDTree
    S = SETTLE
    ne = S["end_nodes"]
    wires = []
    for key, pts, L in free:
        P0 = round_corners(pts)[0]
        L0 = float(np.linalg.norm(np.diff(P0, axis=0), axis=1).sum())
        n = int(round(L / S["seg"])) + 1
        P = _resample(P0, n)
        d0 = (P[1] - P[0]) / np.linalg.norm(P[1] - P[0])
        d1 = (P[-2] - P[-1]) / np.linalg.norm(P[-2] - P[-1])
        wires.append(dict(key=key, P=P, a=P[0].copy(), b=P[-1].copy(), da=d0, db=d1, L0=L0, L=L, n=n))
    fixP = np.concatenate([_resample(round_corners(q)[0], max(2, int(np.linalg.norm(np.diff(round_corners(q)[0], axis=0), axis=1).sum() / 0.8)))
                           for q in fixed]) if fixed else np.zeros((0, 3))
    fix_tree = cKDTree(fixP) if len(fixP) else None
    jc = np.array([j[0] for j in joints]) if joints else np.zeros((0, 3))
    jr = np.array([j[1] for j in joints]) if joints else np.zeros(0)
    def in_joint(Q):
        if not len(jc):
            return np.zeros(len(Q), bool)
        return (np.linalg.norm(Q[:, None, :] - jc[None], axis=2) < jr[None]).any(1)
    rng = np.random.default_rng(1)
    for w in wires:                                       # a small kink so the wire buckles sideways, not along itself
        w["P"][ne:-ne] += rng.normal(0, 0.05, w["P"][ne:-ne].shape)
    owner = np.concatenate([np.full(w["n"], i) for i, w in enumerate(wires)])
    index = np.concatenate([np.arange(w["n"]) for w in wires])
    for it in range(S["iters"]):
        f = min(1.0, it / (S["iters"] * S["grow"]))
        for w in wires:
            P, n = w["P"], w["n"]
            rest = (w["L0"] + (w["L"] - w["L0"]) * f) / (n - 1)
            for k in range(ne):                           # straight out of the housing
                P[k] = w["a"] + w["da"] * rest * k
                P[n - 1 - k] = w["b"] + w["db"] * rest * k
            P[ne:-ne, 1] -= S["gravity"]
            for span in S["spans"]:                       # bending stiffness over short and long spans: smooth arcs
                if n - 2 * span <= 2 * ne:
                    continue
                lap = 0.5 * (P[:-2 * span] + P[2 * span:]) - P[span:-span]
                lo, hi = max(ne, span), min(n - ne, n - span)
                P[lo:hi] += S["bend"] / len(S["spans"]) * lap[lo - span:hi - span]
            for _ in range(S["length_passes"]):           # segment lengths
                d = P[1:] - P[:-1]
                l = np.linalg.norm(d, axis=1)[:, None]
                c = (l - rest) / np.maximum(l, 1e-9) * d * 0.5
                mv = np.zeros_like(P)
                mv[:-1] += c
                mv[1:] -= c
                P[ne:-ne] += mv[ne:-ne]
        A = np.concatenate([w["P"] for w in wires])
        # wire to wire
        tree = cKDTree(A)
        pairs = tree.query_pairs(S["wire_gap"], output_type="ndarray")
        if len(pairs):
            i, j = pairs[:, 0], pairs[:, 1]
            keep = (owner[i] != owner[j]) | (np.abs(index[i] - index[j]) > 6)
            keep &= ~(in_joint(A[i]) & in_joint(A[j]))
            i, j = i[keep], j[keep]
            d = A[i] - A[j]
            l = np.linalg.norm(d, axis=1)[:, None]
            c = (S["wire_gap"] - l) / np.maximum(l, 1e-6) * d * 0.5
            mv = np.zeros_like(A)
            np.add.at(mv, i, c)
            np.add.at(mv, j, -c)
            A += mv
        if fix_tree is not None:
            dd, jj = fix_tree.query(A, distance_upper_bound=S["wire_gap"])
            m = np.isfinite(dd) & ~in_joint(A)
            if m.any():
                d = A[m] - fixP[jj[m]]
                l = np.linalg.norm(d, axis=1)[:, None]
                A[m] += (S["wire_gap"] - l) / np.maximum(l, 1e-6) * d
        # parts
        dist, grad = _field_at(F, A)
        m = dist < WIRE_R + S["clear"]
        if m.any():
            gn = grad[m] / np.maximum(np.linalg.norm(grad[m], axis=1)[:, None], 1e-6)
            A[m] += gn * (WIRE_R + S["clear"] - dist[m])[:, None]
        k0 = 0
        for w in wires:
            n = w["n"]
            w["P"][ne:-ne] = A[k0 + ne:k0 + n - ne]
            k0 += n
    return {w["key"]: w["P"] for w in wires}


def _length(P):
    return float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())


def _frame(P, i):
    t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
    return t / np.linalg.norm(t)


def _arch(P, i0, i1, u, A):
    """Bulge the nodes i0..i1 along u (made normal to the wire), sin^2 profile of height A."""
    Q = P.copy()
    m = i1 - i0
    for k in range(m + 1):
        t = _frame(P, i0 + k)
        v = u - np.dot(u, t) * t
        nv = np.linalg.norm(v)
        if nv < 1e-6:
            continue
        Q[i0 + k] += (v / nv) * A * math.sin(math.pi * k / m) ** 2
    return Q


def _loop(P, i, u, R, turns, pitch=1.7, h=0.0):
    """Insert a service loop at node i: a stem h out along u (made normal to the wire), `turns` turns of radius R,
    and the stem back, a pitch to the side each turn. h = 0: the loop sits on the wire."""
    t = _frame(P, i)
    v = u - np.dot(u, t) * t
    if np.linalg.norm(v) < 0.3:
        return None
    v /= np.linalg.norm(v)
    b = np.cross(t, v)
    base = P[i]
    pts = [base + v * h * k / max(1, int(h / 0.5)) for k in range(int(h / 0.5) + 1)] if h > 0 else []
    s0 = base + v * h
    ctr = s0 + v * R
    n = int(turns * 2 * math.pi * R / 0.5) + 8
    for k in range(n + 1):
        ang = 2 * math.pi * turns * k / n
        pts.append(ctr - v * R * math.cos(ang) + t * R * math.sin(ang) + b * pitch * turns * k / n)
    off = b * pitch * turns
    if h > 0:
        pts += [s0 + off - v * h * k / max(1, int(h / 0.5)) for k in range(1, int(h / 0.5) + 1)]
    pts = np.array(pts)
    rest = P[i + 1:]
    return np.vstack([P[:i], pts, rest + off * np.linspace(1, 0, len(rest))[:, None]])


TIDY_X = 16.0         # neat wiring: the slack of the right-well wires stays right of this X (over the Pi plugs)
TIDY = dict(uart=(24.6, 0.3))   # the BiBoard jumpers keep their slack by the right wall, out of the mic lane
CUR_TIDY = [TIDY_X, 0.004]


LIFT = {}             # set by settle_all: "F" = parts without the panel, "tree" = the wires already in


def _lift_bad(Q):
    """A wire is laid from above: lifted, it must not touch the parts or the wires already in."""
    if not LIFT:
        return 0.0
    bad = 0.0
    for dy in (2.0, 6.0, 12.0, 24.0, 40.0):
        R = Q + np.array([0.0, dy, 0.0])
        d, _ = _field_at(LIFT["F"], R)
        bad += float(np.clip(WIRE_R - d, 0, None).sum())
        if LIFT.get("tree") is not None:
            dd, _ = LIFT["tree"].query(R, distance_upper_bound=2 * WIRE_R)
            bad += float(np.clip(2 * WIRE_R - dd[np.isfinite(dd)], 0, None).sum())
        if LIFT.get("later") is not None:                  # nor may it lie over the path of a wire still to come
            dd, _ = LIFT["later"].query(Q - np.array([0.0, dy, 0.0]), distance_upper_bound=2 * WIRE_R)
            bad += float(np.clip(2 * WIRE_R - dd[np.isfinite(dd)], 0, None).sum())
    return 4.0 * bad


def _badness(F, P, tree, ne=8):
    """Penetration of parts and of other wires (mm, summed): 0 = clean. Slack out of the right well costs a little,
    a wire under the parts or wires already in costs more."""
    Q = P[ne:-ne]
    if not len(Q):
        return 0.0
    untidy = CUR_TIDY[1] * float(np.clip(CUR_TIDY[0] - Q[:, 0], 0, None).sum()) + _lift_bad(Q[8:-8] if len(Q) > 20 else Q)
    d, _ = _field_at(F, Q)
    bad = 20.0 * float(np.clip(WIRE_R + SETTLE["clear"] - d, 0, None).sum()) + untidy      # parts: a hard limit
    if tree is not None:
        dd, _ = tree.query(Q, distance_upper_bound=SETTLE["wire_gap"])
        bad += 10.0 * float(np.clip(SETTLE["wire_gap"] - dd[np.isfinite(dd)], 0, None).sum())
    return bad


def place_slack(F, P0, L, others, joints):
    """A wire of length L on the guide route P0 (shorter): an arch, or else a service loop. Best clean shape."""
    from scipy.spatial import cKDTree
    P0 = _resample(P0, int(_length(P0) / 0.5) + 1)
    n = len(P0)
    others = cKDTree(others) if others is not None and len(others) else None
    cands = []
    dirs = [np.array(d, float) / np.linalg.norm(d) for d in
            [(0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)] +
            [(a_, b_, 0) for a_ in (-1, 1) for b_ in (-1, 1)] + [(0, a_, b_) for a_ in (-1, 1) for b_ in (-1, 1)] +
            [(a_, 0, b_) for a_ in (-1, 1) for b_ in (-1, 1)]]
    best = None
    ne = 8
    spans = [(a_, a_ + w_) for w_ in (0.25, 0.35, 0.5, 0.65) for a_ in np.arange(0.1, 0.81 - w_, 0.05)]   # away from the plug ends
    for frac in spans:
        i0, i1 = int(n * frac[0]), int(n * frac[1])
        if i1 - i0 < 10 or i0 < ne or i1 > n - ne:
            continue
        for u in dirs:
            lo, hi = 0.0, 60.0
            if _length(_arch(P0, i0, i1, u, hi)) < L:
                continue
            for _ in range(30):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if _length(_arch(P0, i0, i1, u, mid)) < L else (lo, mid)
            Q = _arch(P0, i0, i1, u, hi)
            sc = _badness(F, Q, others)
            cands.append((sc, Q, "arch"))
            if best is None or sc < best[0]:
                best = (sc, Q, "arch")
    if True:                                               # also try a coil; an arch wins a tie
        dL = L - _length(P0)
        for h in (0.0, 5.0, 10.0, 15.0):                   # a loop on the wire, or on a stem out to free space
            for turns in (1, 2, 3):
                R = (dL - 2 * h) / (2 * math.pi * turns)
                if R < 3.0 or R > 9.0:
                    continue
                for frac in np.linspace(0.15, 0.8, 14):
                    i = int(n * frac)
                    for u in dirs:
                        Q = _loop(P0, i, u, R, turns, h=h)
                        if Q is None:
                            continue
                        sc = _badness(F, Q, others) + 0.05 + 0.01 * h
                        cands.append((sc, Q, f"{turns}-turn loop" + (f" on a {h:g} mm stem" if h else "")))
                        if best is None or sc < best[0]:
                            best = (sc, Q, f"{turns}-turn loop" + (f" on a {h:g} mm stem" if h else ""))
    cands.sort(key=lambda c: c[0])
    return cands[:12] if cands else [best]


def settle_one(F, P, others, joints, iters=600):
    """Clean up a placed wire: push out of parts and other wires, keep it smooth, keep its length."""
    from scipy.spatial import cKDTree
    S = SETTLE
    P = _resample(P, int(round(_length(P) / S["seg"])) + 1)
    rest = _length(P) / (len(P) - 1)
    ne = S["end_nodes"]
    tree = cKDTree(others) if others is not None and len(others) else None
    for _ in range(iters):
        lap = 0.5 * (P[:-2] + P[2:]) - P[1:-1]
        P[ne:-ne] += 0.15 * lap[ne - 1:-(ne - 1)]
        for _ in range(12):
            d = P[1:] - P[:-1]
            l = np.linalg.norm(d, axis=1)[:, None]
            c = (l - rest) / np.maximum(l, 1e-9) * d * 0.5
            mv = np.zeros_like(P)
            mv[:-1] += c
            mv[1:] -= c
            P[ne:-ne] += mv[ne:-ne]
        Q = P[ne:-ne]
        if tree is not None:
            dd, jj = tree.query(Q, distance_upper_bound=S["wire_gap"])
            m = np.isfinite(dd)
            if joints:
                jc = np.array([j[0] for j in joints]); jr = np.array([j[1] for j in joints])
                m &= ~(np.linalg.norm(Q[:, None] - jc[None], axis=2) < jr[None]).any(1)
            if m.any():
                d = Q[m] - others[jj[m]]
                l = np.linalg.norm(d, axis=1)[:, None]
                Q[m] += (S["wire_gap"] - l) / np.maximum(l, 1e-6) * d
        dist, grad = _field_at(F, Q)
        m = dist < WIRE_R + S["clear"]
        if m.any():
            gn = grad[m] / np.maximum(np.linalg.norm(grad[m], axis=1)[:, None], 1e-6)
            Q[m] += gn * (WIRE_R + S["clear"] - dist[m])[:, None]
        P[ne:-ne] = Q
    return P


# The two ends of each wire, for the guide and the viewer
WIRE_FROM = {("uart", "TX2"): "BiBoard TX2", ("uart", "RX2"): "BiBoard RX2", ("uart", "GND"): "BiBoard GND",
             ("amp", "G"): "amp G", ("amp", "V"): "amp V", ("amp", "BCLK"): "amp BCLK", ("amp", "LRC"): "amp LRC", ("amp", "DIN"): "amp DIN",
             ("mic", "SEL"): "mic SEL", ("mic", "LRCL"): "mic LRCL", ("mic", "DOUT"): "mic DOUT", ("mic", "BCLK"): "mic BCLK",
             ("mic", "GND"): "mic GND", ("mic", "3V"): "mic 3V", ("splice", "bclk"): "BCLK splice", ("splice", "lrclk"): "LRCLK splice",
             ("speaker", "+"): "amp speaker +", ("speaker", "-"): "amp speaker -",
             ("camera", "USB"): "camera USB-C"}
WIRE_TO = {("uart", "TX2"): "pin 10", ("uart", "RX2"): "pin 8", ("uart", "GND"): "pin 6", ("amp", "G"): "pin 14", ("amp", "V"): "pin 2",
           ("amp", "BCLK"): "BCLK splice", ("amp", "LRC"): "LRCLK splice", ("amp", "DIN"): "pin 40", ("mic", "SEL"): "pin 39",
           ("mic", "LRCL"): "LRCLK splice", ("mic", "DOUT"): "pin 38", ("mic", "BCLK"): "BCLK splice", ("mic", "GND"): "pin 9",
           ("mic", "3V"): "pin 1", ("splice", "bclk"): "pin 12", ("splice", "lrclk"): "pin 35", ("speaker", "+"): "speaker +",
           ("speaker", "-"): "speaker -", ("camera", "USB"): "Pi data USB"}

SETTLED = {}          # (group, label) -> settled polyline, set by settle_all()
SLACK_SHAPE = {}      # (group, label) -> "arch" or "loop xN"
PACK_WIRES = {("uart", "TX2"), ("uart", "RX2"), ("uart", "GND"), ("mic", "SEL"), ("mic", "DOUT"), ("mic", "GND"), ("mic", "3V")}
CUT_WIRES = {("mic", "BCLK"), ("mic", "LRCL")}      # the mic legs of the splices: cut to length when the splice is made


def _min_radius(P, span=3):
    """Smallest bend radius along a dense polyline (circle through points `span` apart)."""
    a, b, c = P[:-2 * span], P[span:-span], P[2 * span:]
    ab, bc, ca = np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1)
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    r = ab * bc * ca / np.maximum(4 * area, 1e-9)
    return float(r.min()) if len(r) else 99.0


def all_routes():
    """(group, label, color, points, already smooth) for every wire: settled pack wires, designed routes for the rest."""
    out = []
    for g, lab, col, pts in wire_routes():
        if (g, lab) in SETTLED:
            out.append((g, lab, col, SETTLED[(g, lab)], True))
        else:
            out.append((g, lab, col, pts, False))
    for g, lab, col, pts in speaker_leads() + camera_cable():
        out.append((g, lab, col, pts, True))
    return out


# The order the jumpers go in, one at a time (the guide follows it): the BiBoard jumpers first (low at the Pi
# header, while the right well is empty; their BiBoard ends are plugged last), then the mic jumpers over them,
# the lowest wire of the mic stack first.
SETTLE_ORDER = [("uart", "TX2"), ("uart", "RX2"), ("uart", "GND"),
                ("mic", "3V"), ("mic", "GND"), ("mic", "BCLK"), ("mic", "DOUT"), ("mic", "LRCL"), ("mic", "SEL")]
# (where two wires cross at two heights, the lower one goes in first)


def settle_all(parts, models):
    """Place the pack jumpers (PACK_L) one at a time, in SETTLE_ORDER, with their excess as an arch or a loop."""
    H = HEATSINK                                           # the pin fins as a block: no wire between the pins
    fins = mbox(H["x0"], H["x0"] + H["h"], *H["y"], *H["z"])
    rigid = union([parts["pod_body"], fins] + [M for k, M in models.items() if not k.startswith("wires_")])
    lid = union([parts["pod_panel"].translate([0, 0, float(dz)]) for dz in np.arange(0.0, LID_SLIDE + 0.01, 1.25)])
    ceiling = mbox(-A - 1, A + 1, PANEL_IN - 0.2, 70.0, Z0 - 1, Z1 + 1)          # no slack up into the port openings
    F = obstacle_field(rigid + lid + ceiling)     # the panel over its slide
    LIFT.clear()
    LIFT["F"] = obstacle_field(rigid)                      # when the wires go in, the panel is not on yet
    guides = {(g, lab): pts for g, lab, col, pts in wire_routes()}
    others = [_resample(round_corners(pts)[0], int(_length(round_corners(pts)[0]) / 0.8) + 2)
              for key, pts in guides.items() if key not in SETTLE_ORDER]
    others += [_resample(np.asarray(pts, float), int(_length(np.asarray(pts, float)) / 0.8) + 2) for _, _, _, pts in speaker_leads()]
    joints = [(np.array(splice_end(t, top)), 3.5) for t in ("bclk", "lrclk") for top in (True, False)]
    SETTLED.clear()
    SLACK_SHAPE.clear()
    dense = lambda pts: _resample(round_corners(pts)[0], int(_length(round_corners(pts)[0]) / 0.8) + 2)
    for idx, key in enumerate(SETTLE_ORDER):
        P0 = round_corners(guides[key])[0]
        later = [dense(guides[k]) for k in SETTLE_ORDER[idx + 1:]]       # the paths of the wires still to come
        O = np.concatenate(others + later)
        from scipy.spatial import cKDTree as _T
        earlier = [SETTLED[k] for k in SETTLE_ORDER[:idx]] + [dense(guides[k]) for k in (("splice", "bclk"), ("splice", "lrclk"))]
        LIFT["tree"] = _T(np.concatenate(earlier)) if earlier else None
        LIFT["later"] = _T(np.concatenate(later)) if later else None
        from scipy.spatial import cKDTree
        tree = cKDTree(O)
        CUR_TIDY[:] = TIDY.get(key[0], (TIDY_X, 0.004))
        if key in PACK_WIRES:
            best = None
            for sc, Q0, shape0 in place_slack(F, P0, pack_len(key), O, joints):   # the first shape that is clean after the clean-up,
                Q0 = settle_one(F, Q0, O, joints)                          # else the least bad one
                bad = _badness(F, Q0, tree, ne=4)
                if best is None or bad < best[0]:
                    best = (bad, Q0, shape0)
                if bad < 0.5:
                    break
            Q, shape = best[1], best[2]
        else:
            Q, shape = settle_one(F, P0, O, joints), "cut to length"
        SETTLED[key] = Q
        SLACK_SHAPE[key] = shape
        others.append(Q)
    return F


def wire_report():
    """Each wire: length and smallest bend radius; and every pair of wires that pass through each other
    (outside the splices, where wires join)."""
    import itertools
    rows, tubes = [], []
    for g, lab, col, pts, smooth in all_routes():
        if smooth:
            P = np.asarray(pts, float)
            rmin = _min_radius(P) if g not in ("speaker", "camera") else R_BEND
        else:
            P, rmin = round_corners(pts)
        L = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
        rows.append(dict(group=g, wire=lab, length_mm=round(L, 1), min_bend_r=round(min(rmin, 99), 2), color=col,
                         points=np.round(P, 2).tolist()))
        tubes.append((f"{g} {lab}", tube(pts, r=USB_R if g == "camera" else WIRE_R, rounded=not smooth)))
    joints = union([mcyl("y", SPLICE["y"][0] - 4.0, SPLICE["y"][1] + 3.0, SPLICE["r"] + 2.5, SPLICE[t][0], SPLICE[t][1], 16)
                    for t in ("bclk", "lrclk")])
    cross = []
    for (a, A), (b, B) in itertools.combinations(tubes, 2):
        v = ((A ^ B) - joints).volume()
        if v > 0.02:
            cross.append((a, b, round(v, 2)))
    return rows, cross


def real_models():
    return build_models()[0]


STACK = ("pizero", "pisugar_s", "stack_screws", "battery", "sd_card", "pi_plugs")


def solid_cover_tris():
    """Stock cover without the Pi slot: its top surface has no hole. Design frame."""
    from bittle_platform import build as BP
    return flip_tris(BP.ref_tris("Bittle_Cover.stl"))


def under_cover():
    """Volume under the cover top surface (robot side). Printed parts stay out."""
    return heightfield_solid(solid_cover_tris(), -A - 3, A + 3, Z0 - 2, Z1 + SLIDE + 2, lift=0.0)


def shoulder_tris():
    t = load_stl(os.path.join(PREF, "Bittle_SideShoulder.stl"))
    m = t.copy()
    m[:, :, 0] *= -1
    return np.concatenate([t, m[:, ::-1, :]])


def robot_parts():
    """The robot in the standing pose: Petoi plates (reference STL) and the ROS model parts."""
    from bittle_platform import robot as RB
    sh = stl_manifold("Bittle_SideShoulder.stl", ref=PREF)
    out = dict(shoulder_r=sh, shoulder_l=sh.transform(np.diag([-1.0, 1, 1, 1])[:3, :]),
               front_plate=stl_manifold("Bittle_FrontPlate.stl", ref=PREF))
    R = RB.Robot()
    for n in ("head", "neck_mount", "rear_plate", "hip_servos", "tail"):
        out[n] = R.parts[n]
    for k in ("lf", "rf", "lr", "rr"):
        out[f"leg_{k}"] = R.parts[f"thigh_{k}"] + R.parts[f"shank_{k}"]
    return {k: flip_x(M) for k, M in out.items()}       # design frame


def build_all():
    from bittle_platform import build as BP
    return dict(cover_pegs=flip_x(BP.cover_with_notch() + b3d_to_manifold(build_pegs())), pod_body=build_body(), pod_panel=build_panel(),
                pod_button=build_keycap(), pod_camera_mount=build_camera_mount(), pod_logo_white=build_logo("white"),
                pod_logo_red=build_logo("red"))


def wire_paths():
    return {n: union([mbox(*b["x"], *b["y"], *b["z"]) for b in boxes]) for n, boxes in WIRE_PATHS.items()}


# Endpoints of each wire path: these models may be in it.
PATH_ENDS = {"uart": ("pi_plugs", "biboard_plug", "biboard_header"), "i2s": ("pi_plugs", "amp_ns4168"),
             "mic": ("mic_sph0645",), "speaker": ("amp_ns4168", "speaker")}
# Each wire group starts and ends in these parts.
WIRE_ENDS = {"wires_uart": ("pi_plugs", "biboard_plug"), "wires_amp": ("pi_plugs", "amp_ns4168"),
             "wires_mic": ("pi_plugs", "mic_sph0645"), "wires_splice": ("pi_plugs",), "wires_speaker": ("speaker", "amp_ns4168"),
             "wires_camera": ("camera",)}


def low_mount_models():
    """The head-off mount (base, cradle, pins), its camera and its USB cable (design frame)."""
    cam = union([stl_manifold(f, cam_to_body(True), ref=os.path.join(os.path.dirname(ROOT), "reference"))
                 for f in ("AiCamera250116-down.stl", "AiCamera250116-up.stl")])
    cable = (union([tube(w, r=USB_R, rounded=False) for _, _, _, w in camera_cable_low()]) + rbox("y", *cam_usb_plug(True), 1.0)
             + rbox("y", *pi_usb_plug(), 1.0))
    return build_camera_base_low(), build_camera_cradle_low(), _low_pins(), cam, cable


def check_low(parts, models, robot, low):
    """The head-off mount on the robot without its head."""
    Bs, Cr, pins, cam, cable = low
    vol = lambda a, b: (a ^ b).volume()
    rows = []
    U = under_cover()
    inside = union([X for k, X in models.items() if k not in ("camera", "wires_camera")])
    for n, X in (("pod_body", parts["pod_body"]), ("pod_panel", parts["pod_panel"]), ("cover_pegs", parts["cover_pegs"]), ("under_cover", U),
                 ("parts inside", inside)):
        for a, Y in (("pod_camera_base_low", Bs), ("pod_camera_cradle_low", Cr), ("camera (head off)", cam), ("USB cable (head off)", cable)):
            rows.append((a, n, vol(Y, X)))
    for a, b, A_, B_ in (("pod_camera_base_low", "pod_camera_cradle_low", Bs, Cr), ("pod_camera_base_low", "camera (head off)", Bs, cam),
                         ("pod_camera_cradle_low", "camera (head off)", Cr, cam), ("pins", "pod_camera_base_low", pins, Bs),
                         ("pins", "pod_camera_cradle_low", pins, Cr), ("USB cable (head off)", "head-off mount", cable, Bs + Cr)):
        rows.append((a, b, vol(A_, B_)))
    for n, X in robot.items():
        if n != "head":
            rows.append(("head-off mount + camera + cable", n, vol(Bs + Cr + cam + cable, X)))
    for n, M in (("pod_camera_base_low", Bs), ("pod_camera_cradle_low", Cr)):
        rows.append((n, "loose_pieces", sum(sorted(c.volume() for c in M.decompose())[:-1])))
    rows.append(("camera (head off) lifted 0.3mm (must touch)", "pod_camera_cradle_low", vol(cam.translate([0, 0.3, 0]), Cr)))
    rows.append(("cradle lifted 0.3mm (must touch)", "pins", vol(Cr.translate([0, 0.3, 0]), pins)))
    rows.append(("cradle lowered 0.3mm (must touch)", "pod_camera_base_low", vol(Cr.translate([0, -0.3, 0]), Bs)))
    rows.append(("cradle slid down from 20 mm up (no pins)", "pod_camera_base_low",
                 max(vol(Cr.translate([0, float(dy), 0]), Bs) for dy in (0.5, 2.0, 5.0, 10.0, 15.0, 20.0))))
    rows.append(("pod_camera_base_low lifted 0.3mm (must touch)", "pod_panel", vol(Bs.translate([0, 0.3, 0]), parts["pod_panel"])))
    return rows


def check(parts, models, robot):
    rows = []
    vol = lambda a, b: (a ^ b).volume()
    names = list(parts)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pa, pb = (build_keycap(press=False) if n == "pod_button" else parts[n] for n in (a, b))   # the press fit ribs: checked below
            rows.append((a, b, vol(pa, pb)))
    for a in names:
        for b, M in models.items():
            rows.append((a, b, vol(parts[a], M)))
    U = under_cover()
    ADD = ("pod_body", "pod_panel", "pod_button", "pod_camera_mount")
    for a in ADD:
        rows.append((a, "under_cover", vol(parts[a], U)))
        for b, M in robot.items():
            rows.append((a, b, vol(parts[a], M)))
    for a in names:
        if a.startswith("pod_logo_"):
            continue                                       # a ring and a letter each: they are glued in one by one
        pcs = sorted(c.volume() for c in parts[a].decompose())
        rows.append((a, "loose_pieces", sum(pcs[:-1])))
    mn = list(models)
    for i, a in enumerate(mn):
        for b in mn[i + 1:]:
            if a == "biboard_header" and b == "biboard_plug":
                continue
            if "stack_screws" in (a, b) and {a, b} & {"pizero", "pisugar_s"}:
                continue                                   # the screws hold the boards together
            if a.startswith("wires_") and b.startswith("wires_"):
                continue                                   # wires may touch other wires
            w, o = (a, b) if a.startswith("wires_") else (b, a)
            if w.startswith("wires_") and o in WIRE_ENDS[w]:
                continue                                   # a wire ends in its plug
            rows.append((a, b, vol(models[a], models[b])))
    for w in (m for m in models if m.startswith("wires_")):
        rows.append((w, "cover_pegs", vol(models[w], parts["cover_pegs"])))
        for b, M in robot.items():
            rows.append((w, b, vol(models[w], M)))
    # nothing on the floor over the keyholes (pegs, slide paths, click beams)
    K = union([mbox(k[0], k[1], FLOOR_Y1 + 0.01, KEEP_Y, k[2], k[3]) for k in (keep_zone(px, pz) for px, pz in PEGS)])
    rows.append(("pod_body", "keyhole keep zones", vol(parts["pod_body"], K)))
    # slide path: the empty body at the click bump, half way and at the drop-on place
    from bittle_platform import build as BP
    for s_ in (round(BP.DET_DZ, 2), SLIDE / 2, SLIDE):
        T = parts["pod_body"].translate([0, 0, s_])
        for b, M in (("cover_pegs", parts["cover_pegs"]), ("biboard_header", models["biboard_header"]), ("under_cover", U)):
            rows.append((f"body back {s_:g}mm", b, vol(T, M)))
        for b, M in robot.items():
            rows.append((f"body back {s_:g}mm", b, vol(T, M)))
    # install from the top, in this order; each part goes straight down into the body
    groups = [("speaker", ["speaker"]), ("mic", ["mic_sph0645"]), ("amp", ["amp_ns4168"]), ("stack", list(STACK))]
    placed = parts["pod_body"] + parts["cover_pegs"] + models["biboard_header"]
    for g, ns in groups:
        G = union([models[n] for n in ns])
        yt_ = AMP_Y0 + AMP["h"]                            # the amp tilts in under its nubs
        P_ = placed - union([mbox(-IN_A - 1, AMP_X[0] + 1.2, yt_, yt_ + 2.5, z - 0.2, z + 4.2) for z in AMP_NUBS]) if g == "amp" else placed
        worst = max(vol(G.translate([0, float(dy), 0]), P_) for dy in [0.5, 1, 2, 3, 5] + list(range(8, 41, 4)))
        rows.append((f"install {g} (max over 40 mm down)", "body + parts in", worst))
        placed = placed + G
    # panel: straight down LID_SLIDE behind its place, then forward. The latch hook rides over the rib (checked below).
    Pc = build_panel(with_latch=False) + parts["pod_button"]
    inside = union([models[n] for n in models if n not in ("biboard_header",)])
    inside_nc = union([M for k, M in models.items() if k not in ("biboard_header", "camera", "wires_camera")])   # the camera goes on later
    lever = mbox(*SW_LEVER["x"], *SW_LEVER["y"], *SW_LEVER["z"])
    lever_sw = m3.Manifold.batch_hull([lever.translate([0, 0, -SW_TRAVEL]), lever.translate([0, 0, SW_TRAVEL])])
    fixed = parts["pod_body"] + inside_nc + lever_sw       # the switch in either place
    rows.append(("panel down, LID_SLIDE behind (max over 12 mm)", "body + parts",
                 max(vol(Pc.translate([0, float(dy), LID_SLIDE]), fixed) for dy in (0.2, 0.5, 1, 2, 4, 6, 8, 12))))
    rows.append(("panel slide forward (max over LID_SLIDE)", "body + parts",
                 max(vol(Pc.translate([0, 0, float(dz)]), fixed) for dz in np.arange(0.25, LID_SLIDE + 0.01, 0.25))))
    rib = latch_rib()
    rows.append(("latch hook, panel slid back 0.3mm (must touch)", "rib", vol(latch_hook().translate([0, 0, 0.3]), rib)))
    rows.append(("latch hook lifted 0.8mm, slide", "body", max(vol(latch_hook(0.8).translate([0, 0, float(dz)]), parts["pod_body"])
                                                               for dz in np.arange(0.0, LID_SLIDE + 0.01, 0.25))))
    rows.append(("panel lifted 0.3mm (must touch)", "pod_body", vol(parts["pod_panel"].translate([0, 0.3, 0]), parts["pod_body"])))
    rows.append(("panel lifted 0.3mm at drop place", "pod_body", vol(parts["pod_panel"].translate([0, 0.3, LID_SLIDE]) - latch_hook().translate([0, 0.3, LID_SLIDE]), parts["pod_body"])))
    others = union([M for m, M in models.items() if m != "pisugar_s"])
    # switch: the lever is under the window over its travel (a fingernail reaches its top)
    win = mbox(*SW_WIN["x"], 0, 99, *SW_WIN["z"])
    rows.append(("switch lever over its travel, outside the window (must be 0)", "lever", vol(lever_sw - win, lever_sw)))
    # button: the arm stands BTN gap over the button; pressed BTN press, it pushes the button
    cap = mbox(*BTN["cap"][:2], BTN["cap"][4] - 0.7, BTN["cap"][4], *BTN["cap"][2:4])
    cell = mbox(*BAT["x"], *BAT["y"], *BAT["z"])
    rows.append(("battery moved 0.5mm left (must touch)", "pod_panel", vol(cell.translate([-0.5, 0, 0]), parts["pod_panel"])))
    rows.append(("battery moved 0.5mm up (must touch)", "pod_panel", vol(cell.translate([0, 0.5, 0]), parts["pod_panel"])))
    rows.append(("battery moved 0.5mm down (must touch)", "pod_body", vol(cell.translate([0, -0.5, 0]), parts["pod_body"])))
    rows.append(("button arm at rest", "button", vol(button_arm(), cap)))
    pcb = mbox(*MIC_X, MIC["y0"], MIC["y0"] + MIC["l"], MIC["z0"], MIC["z0"] + MIC["w"])
    for lab, v, P in (("lifted", (0, 0.3, 0), parts["pod_panel"]), ("moved inward", (0.3, 0, 0), parts["pod_body"]),
                      ("moved forward", (0, 0, -0.3), parts["pod_body"]), ("moved rearward", (0, 0, 0.3), parts["pod_body"])):
        rows.append((f"mic board {lab} 0.3mm (must touch)", "pod_panel" if P is parts["pod_panel"] else "pod_body", vol(pcb.translate(list(v)), P)))
    rows.append(("logo inlays in the pocket", "pod_panel", vol(parts["pod_logo_white"] + parts["pod_logo_red"], parts["pod_panel"])))
    rows.append(("button cap ribs in the hole (press fit, must touch)", "pod_panel", vol(build_keycap(), parts["pod_panel"])))
    rows.append(("button cap lifted 0.3mm (must touch)", "pod_panel", vol(parts["pod_button"].translate([0, 0.3, 0]), parts["pod_panel"])))
    rows.append(("camera mount lifted 0.3mm (must touch)", "pod_panel", vol(parts["pod_camera_mount"].translate([0, 0.3, 0]), parts["pod_panel"])))
    rows.append(("camera lifted 0.3mm (must touch)", "pod_camera_mount", vol(models["camera"].translate([0, 0.3, 0]), parts["pod_camera_mount"])))
    # twist lock: drop in at the keyways, turn to the lock; the bumps ride on the lugs (they press 0.1 into the notches)
    Mt, Pn = parts["pod_camera_mount"], parts["pod_panel"]
    bumps = tw_socket_parts("bumps")
    T = TW
    rows.append(("camera mount dropped in at the keyways", "pod_panel", max(vol(tw_turn(Mt, T["twist"]).translate([0, dy, 0]), Pn) for dy in (0.0, 0.5, 1.5, 3.0, 6.0))))
    rows.append(("camera mount over the turn", "panel without the bumps",
                 max(vol(tw_turn(Mt, T["twist"] * f), Pn - bumps) for f in (1.0, 0.75, 0.5, 0.25, 0.1))))
    rows.append(("camera mount over the turn (must touch: the bumps ride on the lugs)", "bumps",
                 min(vol(tw_turn(Mt, T["twist"] * f), bumps) for f in (0.12, 0.06))))
    rows.append(("camera mount locked: bumps in the notches (preload, must touch)", "bumps", vol(Mt, bumps)))
    rows.append(("camera mount turned 180 deg (lens to the rear)", "panel without the bumps", vol(tw_turn(Mt, 180.0), Pn - bumps)))
    rows.append(("camera mount pushed down 0.3mm (must touch: the cone in the countersink)", "panel without the bumps",
                 vol(Mt.translate([0, -0.3, 0]), Pn - bumps - tw_socket_parts("stops"))))
    rows.append(("camera mount turned 2 deg past the lock (must touch the stops)", "pod_panel", vol(tw_turn(Mt, -2.0 * math.copysign(1, T["twist"])), Pn - bumps)))
    inside_c = union([M for k, M in models.items() if k not in ("camera", "wires_camera")])
    rows.append(("camera mount over the turn", "body + parts", max(vol(tw_turn(Mt, T["twist"] * f), parts["pod_body"] + inside_c) for f in (1.0, 0.5, 0.0))))
    rows.append(("camera mount turned 180 deg", "body + parts", vol(tw_turn(Mt, 180.0), parts["pod_body"] + inside_c)))
    for n, (xc, zc_, sx, sz) in PORT_PLUGS.items():
        B = mbox(xc - sx / 2, xc + sx / 2, PORT_TOP + 0.2, 95.0, zc_ - sz / 2, zc_ + sz / 2)
        rows.append((f"plug {n}", "camera, its mount and its cable", vol(B, parts["pod_camera_mount"] + models["camera"]
                                                                        + (models["wires_camera"] if n != "pi_usb" else m3.Manifold()))))
    rows.append(("button arm pressed (must touch)", "button", vol(button_arm(-BTN["press"]), cap)))
    rows.append(("button arm pressed", "parts (not the PiSugar)", vol(button_arm(-BTN["press"]), others)))
    zc = (Z0 + Z1) / 2
    R = parts["pod_panel"].transform(np.array([[-1.0, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 2 * zc]]))
    rows.append(("panel turned 180 (min, Z +-6)", "body + parts",
                 min(vol(R.translate([0, 0, float(dz)]), parts["pod_body"] + inside) for dz in np.arange(-6.0, 6.01, 1.0))))
    # wire paths: free of the printed parts and of every model except the ends of the path
    for n, W in wire_paths().items():
        key = n.split(":")[0]
        for b in ADD:
            rows.append((f"wires {key}", b, vol(W, parts[b])))
        others = union([M for m, M in models.items() if m not in PATH_ENDS[key] and not m.startswith("wires_")])
        rows.append((f"wires {key}", "other parts", vol(W, others)))
    G = PI.GROVE_PLUG
    plug = mbox(-G["x"][1], -G["x"][0], 10.0, G["y_top"], *G["z"])
    rows.append(("Grove plug space (max over the slide)", "pod_body",
                 max(vol(parts["pod_body"].translate([0, 0, s_]), plug) for s_ in (0.0, 1.0, 2.0, 3.5, 5.0, SLIDE))))
    rows.append(("Grove plug space", "wires", vol(plug, union([M for m, M in models.items() if m.startswith("wires_")]))))
    C = mbox(*FRONT_CABLE["x"], *FRONT_CABLE["y"], *FRONT_CABLE["z"])
    rows.append(("Grove cable space, front (robot left)", "pod_body", vol(C, parts["pod_body"])))
    F = mbox(*FINGER["x"], *FINGER["y"], *FINGER["z"])
    rows.append(("finger over the BiBoard plug", "pod_body", vol(F, parts["pod_body"])))
    rows.append(("finger over the BiBoard plug", "other parts", vol(F, union([M for m, M in models.items()
                                                                            if m != "biboard_plug" and not m.startswith("wires_")]))))
    for n, (xc, zc_, sx, sz) in PORT_PLUGS.items():
        B = mbox(xc - sx / 2, xc + sx / 2, PORT_TOP + 0.2, 95.0, zc_ - sz / 2, zc_ + sz / 2)
        for b in ADD:
            rows.append((f"plug {n}", b, vol(B, parts[b])))
    return rows


# The order the parts and the wires go in (the guide and the viewer follow it). The amp cable runs on the floor
# under the stack: it is laid before the stack, and its Pi ends are plugged after the stack is in.
# The amp cable goes in after the BiBoard jumpers: its V wire runs over their Pi ends.
INSTALL = [("part", "speaker"), ("part", "mic_sph0645"), ("part", "amp_ns4168"),
           ("lay", [("speaker", "+"), ("speaker", "-")]),
           ("stack", None),
           ("wire", ("splice", "bclk")), ("wire", ("splice", "lrclk"))] + [("wire", k) for k in SETTLE_ORDER if k[0] == "uart"] + \
          [("lay", [("amp", "G"), ("amp", "V"), ("amp", "BCLK"), ("amp", "LRC"), ("amp", "DIN")]),
           ("plug", ("amp", "G")), ("plug", ("amp", "V")), ("plug", ("amp", "DIN"))] + \
          [("wire", k) for k in SETTLE_ORDER if k[0] == "mic"] + [("plug_dev", k) for k in SETTLE_ORDER if k[0] == "uart"]


def install_checks(parts, models):
    """Each wire is laid from above: lifted 40 mm, it must not touch the parts or the wires already in (its last
    4 mm at each end go into its housings). Each housing slides 6 mm off its pin clear of the parts (loose wires
    push aside)."""
    rows = []
    vol = lambda a, b: (a ^ b).volume()
    routes = {(g, lab): (np.asarray(pts, float) if sm else round_corners(pts)[0]) for g, lab, col, pts, sm in all_routes()}
    stack_parts = union([models[n] for n in ("pizero", "pisugar_s", "stack_screws", "battery", "sd_card")])
    hdr = mbox(*HDR_BASE_X, PI_PLUGS["y"][0], PI_PLUGS["y"][1], *PI_PLUGS["z"])
    mic_board = models["mic_sph0645"] - union([HOUSING_MESH[("mic", k)] for k in range(6)])
    rigid = [parts["pod_body"], models["biboard_header"]]
    wires = []
    def trimmed(P, cut=4.0):
        s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        keep = (s_ > cut) & (s_ < s_[-1] - cut)
        return tube(P[keep], rounded=False) if keep.sum() > 1 else None
    def housing_slide(hk):
        d = {"pi": (1, 0, 0), "mic": (1, 0, 0), "bb": (0, 1, 0)}[hk[0]]
        H = HOUSING_MESH[hk]
        return union([H.translate([d[0] * t, d[1] * t, d[2] * t]) for t in (1.0, 3.0, 6.0)])
    def lay(keys):
        Ts = [t for t in (trimmed(routes[k]) for k in keys) if t is not None]
        T = union(Ts)
        now = union(rigid + wires)
        name = keys[0][0] + " " + "/".join(k[1] for k in keys)
        rows.append((f"lay {name} (lifted 40 mm)", "parts and wires already in",
                     max(vol(T.translate([0, dy, 0]), now) for dy in (0.5, 2.0, 5.0, 10.0, 20.0, 40.0))))
        wires.append(T)
    def push(key, ends=("pi", "dev")):
        for end, hk in wire_housings(*key):
            if end not in ends:
                continue
            rows.append((f"push on {key[0]} {key[1]} housing ({end}, 6 mm)", "parts already in", vol(housing_slide(hk), union(rigid))))
            rigid.append(HOUSING_MESH[hk])
    for kind, key in INSTALL:
        if kind == "part":
            rigid.append(mic_board if key == "mic_sph0645" else models[key])
        elif kind == "stack":
            rigid.append(stack_parts + hdr)
        elif kind == "lay":
            lay(key)
        elif kind == "plug":
            push(key)
        elif kind == "wire":
            lay([key])
            push(key, ("pi",) if key[0] == "uart" else ("pi", "dev"))
        elif kind == "plug_dev":
            push(key, ("dev",))
    return rows


# Masses (g) from the user's table (reference/signal-2026-10-15-12-23-39-844.png): the electronics and the wires.
# The printed parts are about half solid (PRINT_FILL).
# Exploded view: the parts leave in about the reverse build order. In its stage a part makes two moves, one after
# the other: it lifts straight up (the way it went in, out through the open top of the body), then moves aside.
# A Dupont housing always stays on its wire. The Pi stack and its wire harness (the jumpers, the amp cable, the
# splices) leave together: a housing cannot slide off a Pi pin as one rigid piece with its wire (the wire would go
# through the right wall). Lifts grow with the stage, so a part never passes through a part still in place.
EXPLODE_STAGES = 7


def explode_plan(name, sub=""):
    """(stage, first move (dx, dy, dz), second move (dx, dy, dz)) of a display part, or None for a part that stays."""
    if name == "camera":
        return 0, (0, 250, 0), (0, 0, 0)
    if name in ("camera_mount", "pod_camera_mount"):
        return 1, (0, 210, 0), (0, 0, 0)
    if name in ("panel", "pod_panel"):
        return 2, (0, 0, LID_SLIDE), (0, 170, 0)
    if name in ("button", "pod_button", "pod_logo_white", "pod_logo_red"):
        return 2, (0, 0, LID_SLIDE), (0, 170, 0)                         # they stay clicked into the panel
    if name.startswith("wires_"):
        if name == "wires_camera":
            return 0, (0, 250, 0), (0, 0, 0)                      # the USB cable goes with the camera
        if name == "wires_speaker":
            return 4, (0, 45, 0), (-30, 0, 0)                     # the speaker lead goes with the amp
        return 3, (0, 100, 0), (0, 0, 0)                         # the harness, its housings on it, with the Pi
    if name in ("pizero", "pisugar_s", "stack_screws", "battery", "sd_card", "pi_plugs"):
        return 3, (0, 100, 0), (0, 0, 0)                         # one block: the amp cable runs under the battery
    if name == "amp_ns4168":
        return 4, (0, 45, 0), (-30, 0, 0)
    if name == "mic_sph0645":
        return 5, (0, 45, 0), (0, 0, 0)                           # up out of its slots
    if name == "speaker":
        return 6, (0, 45, 0), (0, 0, 30)
    return None


def explode_robot(name, sub=""):
    """explode_plan in the robot frame (the moves along X turn over)."""
    e = explode_plan(name, sub)
    if e is None:
        return None
    return e[0], (-e[1][0], e[1][1], e[1][2]), (-e[2][0], e[2][1], e[2][2])


MASS_G = dict(stack_screws=1.0, pizero=10.0, pisugar_s=10.0, battery=23.5, sd_card=0.4, pi_plugs=5.0, speaker=14.0, amp_ns4168=5.0,
              mic_sph0645=1.3, camera=CAM["mass"], wires_uart=2.4, wires_amp=4.0, wires_mic=4.8, wires_speaker=1.0, wires_camera=2.5,
              wires_splice=0.5, biboard_plug=0.5)
PRINT_FILL = 0.5
PLA_G_MM3 = 1.24e-3


def centroid(M):
    """Volume centroid of a manifold."""
    m = M.to_mesh()
    v = np.asarray(m.vert_properties)[:, :3][np.asarray(m.tri_verts)]
    w = np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2]))
    return (v.sum(1) / 4 * w[:, None]).sum(0) / w.sum()


def balance(parts, models):
    """Mass and center of mass of the add-on (printed parts + electronics), design frame (main() turns X over).
    The robot center is X 0, Z 0: the cover and the shoulder plates are symmetric about it."""
    rows = []
    for n in ("pod_body", "pod_panel", "pod_button", "pod_camera_mount"):
        rows.append((n, parts[n].volume() * PLA_G_MM3 * PRINT_FILL, centroid(parts[n])))
    for n, g in MASS_G.items():
        rows.append((n, g, centroid(models[n])))
    m = sum(r[1] for r in rows)
    c = sum(r[1] * r[2] for r in rows) / m
    return dict(mass_g=round(m, 1), com=[round(float(v), 1) for v in c],
                parts=[dict(name=n, g=round(g, 1), com=[round(float(v), 1) for v in p]) for n, g, p in rows])


def print_orient(name, M, also=None):
    """Rotate to the print orientation and put the part on the bed (Z=0). also: another solid that gets the same
    move (returned as a second value)."""
    if name == "pod_body":
        R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)        # floor down
    elif name == "pod_camera_mount":
        R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)        # standing up: the lugs on the bed
    elif name == "pod_camera_cradle_low":
        R = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]], float)       # on its back end: prisms along Z, the front lips last
    elif name == "pod_camera_base_low":
        R = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)        # on its side, robot +X (the design -X lug) on the bed
    elif name == "pod_button":
        R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)        # upside down, the cap top on the bed
    elif name in ("pod_panel", "pod_logo_white", "pod_logo_red"):
        R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)        # upside down, top on the bed
    else:
        raise ValueError(name)
    M = M.transform(np.hstack([R, np.zeros((3, 1))]))
    lo, hi = M.bounding_box()[:3], M.bounding_box()[3:]
    d = [-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]]
    if also is None:
        return M.translate(d)
    return M.translate(d), also.transform(np.hstack([R, np.zeros((3, 1))])).translate(d)


def logo_blocker():
    """A support blocker over the logo pocket: in the print the pocket is open to the bed and its floor bridges."""
    S = logo_shapes()
    return _logo_place((S["white"] + S["red"]).offset(LOGO["clr"] + 1.0), TOP - LOGO["pocket"] - 0.3, TOP + 0.3)


def write_panel_3mf(panel, path):
    """The panel in its print orientation with a Cura support blocker (anti_overhang_mesh) over the logo pocket, as
    one group. The blocker is not printed."""
    import zipfile
    P, B = print_orient("pod_panel", panel, also=flip_x(logo_blocker()))

    def obj(oid, name, M, settings):
        m = M.to_mesh()
        v = np.asarray(m.vert_properties)[:, :3]
        t = np.asarray(m.tri_verts)
        out = [f'  <object id="{oid}" name="{name}" type="model">']
        if settings:
            out.append("   <metadatagroup>")
            out += [f'    <metadata name="cura:{k}" preserve="1" type="xs:string">{x}</metadata>' for k, x in settings.items()]
            out.append("   </metadatagroup>")
        out.append("   <mesh>\n    <vertices>")
        out += [f'     <vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}" />' for a, b, c in v]
        out.append("    </vertices>\n    <triangles>")
        out += [f'     <triangle v1="{a}" v2="{b}" v3="{c}" />' for a, b, c in t]
        out.append("    </triangles>\n   </mesh>\n  </object>")
        return "\n".join(out)
    model = "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
        " <resources>",
        obj(1, "pod_panel", P, None),
        obj(2, "logo_support_blocker", B, {"anti_overhang_mesh": "True"}),
        '  <object id="3" name="pod_panel_group" type="model">',
        '   <components>\n    <component objectid="1" />\n    <component objectid="2" />\n   </components>',
        "  </object>",
        " </resources>",
        ' <build>\n  <item objectid="3" />\n </build>',
        "</model>"])
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" /></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" />'
            '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def export_assembly(path, models):
    """One STEP file with the robot, the platform and the add-on in place: named, colored parts (no wires).
    Exact B-rep for the pegs; simplified meshes for the rest (0.05 mm for the add-on, 0.15 mm for the
    robot, the cover and the boards)."""
    from build123d import Compound, Color, export_step
    from bittle_platform import build as BP
    mirror_x, mirror_z = np.diag([-1.0, 1, 1, 1])[:3, :], np.diag([1.0, 1, -1, 1])[:3, :]
    meshes = dict(
        shoulder_right=(stl_manifold("Bittle_SideShoulder.stl", ref=PREF), "#f2a71c"),
        shoulder_left=(stl_manifold("Bittle_SideShoulder.stl", ref=PREF).transform(mirror_x), "#f2a71c"),
        front_plate=(stl_manifold("Bittle_FrontPlate.stl", ref=PREF), "#26272b"),
        rear_plate_mirror=(stl_manifold("Bittle_FrontPlate.stl", ref=PREF).transform(mirror_z), "#26272b"),
        cover=(mesh_to_manifold(BP.ref_tris(COVER_STL)), "#26272b"),
        pod_body=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_body.stl"))), "#e9e9e6"),
        pod_panel=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_panel.stl"))), "#e8641b"),
        pod_button=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_button.stl"))), "#e9e9e6"),
        pod_camera_mount=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_camera_mount.stl"))), "#e8641b"),
    )
    cols = dict(camera="#2b2d33", pizero="#2a8c47", pisugar_s="#c4588c", battery="#3a5fa8", sd_card="#222222", pi_plugs="#d83a34",
                biboard_header="#0d0d0d", biboard_plug="#d83a34", speaker="#7a52b8", amp_ns4168="#1a5a8c",
                mic_sph0645="#d83a34")
    for n, col in cols.items():
        meshes[n] = (models[n], col)
    kids = []
    coarse = ("shoulder_right", "shoulder_left", "front_plate", "rear_plate_mirror", "cover", "pizero", "pisugar_s")
    for n, (M, col) in meshes.items():
        S = mesh_solid(M, 0.15 if n in coarse else 0.05)
        S.label, S.color = n, Color(col)
        kids.append(S)
    pegs = BP.pegs()
    pegs.label, pegs.color = "pegs", Color("#26272b")
    kids.append(pegs)
    A_ = Compound(label="bittle_pi_addon_assembly", children=kids)
    export_step(A_, path)
    import zipfile
    zp = os.path.join(os.path.dirname(path), "assembly_step.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(path, os.path.basename(path))
    print(f"assembly: {path} ({os.path.getsize(path) / 1e6:.1f} MB, {len(kids)} parts), zip {os.path.getsize(zp) / 1e6:.1f} MB")


def main(fast=False):
    import json
    from bittle_platform import build as BP
    os.makedirs(OUT, exist_ok=True)
    parts = build_all()
    settle_all(parts, real_models())          # the pack jumpers settle among the parts (the models from the guide routes)
    models = real_models()
    robot = robot_parts()
    for d in ("print", "installed", "models"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    for f in ("pod_tray.stl", "pod_lid.stl", "top_insert.stl"):          # rev 0.15 parts
        for d in ("print", "installed"):
            p = os.path.join(OUT, d, f)
            if os.path.exists(p):
                os.unlink(p)
    printing = {}
    for n, M in parts.items():                     # every output is in the robot frame
        save_stl(flip_x(M), os.path.join(OUT, "installed", f"{n}.stl"))
        if n == "cover_pegs":
            continue            # a platform part: bittle_platform/stl/print/cover_pegs.stl
        P = print_orient(n, flip_x(M))
        save_stl(P, os.path.join(OUT, "print", f"{n}.stl"))
        if n == "pod_panel":
            write_panel_3mf(flip_x(M), os.path.join(OUT, "print", "pod_panel.3mf"))
        regs = BP.overhang_regions(P)
        printing[n] = dict(overhang_mm2=round(sum(r["area"] for r in regs), 1), regions=regs[:8])
        print(f"{n:11s} vol {M.volume():8.0f} mm3  ~{M.volume() * PLA_G_MM3:5.1f} g PLA (solid)   overhang {printing[n]['overhang_mm2']:6.1f} mm2")
        for r in regs[:8]:
            print(f"     {r['area']:6.1f} mm2  flat {r['flat']:5.1f}  at print z {r['z'][0]:.1f}..{r['z'][1]:.1f}  x {r['x'][0]:.1f}..{r['x'][1]:.1f}  y {r['y'][0]:.1f}..{r['y'][1]:.1f}")
    for f in os.listdir(os.path.join(OUT, "models")):
        if f.endswith(".stl"):
            os.unlink(os.path.join(OUT, "models", f))
    for n, M in models.items():
        save_stl(flip_x(M), os.path.join(OUT, "models", f"{n}.stl"))
    os.makedirs(os.path.join(OUT, "models", "parts"), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "models", "parts")):
        os.unlink(os.path.join(OUT, "models", "parts", f))
    disp = []
    for key, sub, label, M, col in build_models()[1]:
        f = f"{key}__{sub}.stl"
        save_stl(flip_x(M), os.path.join(OUT, "models", "parts", f))
        disp.append(dict(model=key, sub=sub, label=label, file=f"models/parts/{f}", color=col, explode=explode_robot(key, sub)))
    json.dump(disp, open(os.path.join(OUT, "models", "parts.json"), "w"), indent=1)       # display: colored sub-parts
    json.dump(dict(stages=EXPLODE_STAGES, parts={n: explode_robot(n) for n in parts}),
              open(os.path.join(OUT, "explode.json"), "w"), indent=1)
    save_stl(flip_x(union(list(wire_paths().values()))), os.path.join(OUT, "models", "wire_paths.stl"))      # display only
    rows = check(parts, models, robot)
    rows += install_checks(parts, models)
    low = low_mount_models()                       # the head-off camera mount: two separate parts
    rows += check_low(parts, models, robot, low)
    for n, M in (("pod_camera_base_low", low[0]), ("pod_camera_cradle_low", low[1])):
        save_stl(flip_x(M), os.path.join(OUT, "installed", f"{n}.stl"))
        P = print_orient(n, flip_x(M))
        save_stl(P, os.path.join(OUT, "print", f"{n}.stl"))
        regs = BP.overhang_regions(P)
        printing[n] = dict(overhang_mm2=round(sum(r["area"] for r in regs), 1), regions=regs[:8])
        print(f"{n:11s} vol {M.volume():8.0f} mm3  ~{M.volume() * PLA_G_MM3:5.1f} g PLA (solid)   overhang {printing[n]['overhang_mm2']:6.1f} mm2")
        for r_ in regs[:8]:
            print(f"     {r_['area']:6.1f} mm2  flat {r_['flat']:5.1f}  at print z {r_['z'][0]:.1f}..{r_['z'][1]:.1f}  x {r_['x'][0]:.1f}..{r_['x'][1]:.1f}  y {r_['y'][0]:.1f}..{r_['y'][1]:.1f}")
    for f in ("pod_camera_mount_low.stl",):
        for d in ("print", "installed"):
            if os.path.exists(os.path.join(OUT, d, f)):
                os.unlink(os.path.join(OUT, d, f))
    save_stl(flip_x(low[2]), os.path.join(OUT, "models", "camera_low_pins.stl"))
    save_stl(flip_x(low[3]), os.path.join(OUT, "models", "camera_low.stl"))
    save_stl(flip_x(low[4]), os.path.join(OUT, "models", "wires_camera_low.stl"))
    wires, cross = wire_report()
    rows.append(("wires: pairs that pass through each other", "-", float(len(cross))))
    rows.append((f"wires: designed bends under {R_BEND - 0.05:.2f} mm, slack bends under {R_SLACK:.2f} mm", "-",
                 float(sum(w["min_bend_r"] < (R_SLACK if (w["group"], w["wire"]) in SETTLED else R_BEND - 0.05) for w in wires))))
    for w in wires:
        k = (w["group"], w["wire"])
        w["slack"] = SLACK_SHAPE.get(k, "")
        w["pack"] = k in PACK_WIRES
        w["len_cm"] = pack_len(k) / 10
        w["from"], w["to"] = WIRE_FROM[k], WIRE_TO[k]
        w["id"] = "wires_" + k[0] + "__" + wire_sub(k[1])
        w["housings"] = [w["id"] + "_" + end for end, _ in wire_housings(*k)]
        w["points"] = [[-p_[0], p_[1], p_[2]] for p_ in w["points"]]          # robot frame
    json.dump(dict(wires=wires, crossings=cross, r_bend=R_BEND, r_slack=R_SLACK, wire_d=2 * WIRE_R, pack_l=PACK_L, long_l=LONG_L,
                   order=[list(k) for k in SETTLE_ORDER]), open(os.path.join(OUT, "wires.json"), "w"), indent=1)
    print("wires: longest", max(w["length_mm"] for w in wires), "mm; smallest bend", min(w["min_bend_r"] for w in wires), "mm; crossings", len(cross))
    bal = balance(parts, models)
    bal["com"][0] = -bal["com"][0]                                          # robot frame
    for b_ in bal["parts"]:
        b_["com"][0] = -b_["com"][0]
    snap = latch_force()
    clicks = BP.detent_force()
    print(f"balance: {bal['mass_g']} g, center of mass x {bal['com'][0]} y {bal['com'][1]} z {bal['com'][2]}")
    twist = tw_force()
    print("panel latch:", snap)
    print("camera socket tabs:", twist)
    print("platform clicks:", clicks)
    print("checks (mm^3, >0.05 shown):")
    for a, b, v in rows:
        if v > 0.05:
            print(f"  {a:34s} x {b:20s} {v:9.2f}")
    json.dump(dict(rows=rows, printing=printing, balance=bal, snap=snap, clicks=clicks, twist=twist),
              open(os.path.join(OUT, "checks.json"), "w"), indent=1)
    if fast:
        return
    from build123d import export_step
    os.makedirs(os.path.join(ROOT, "cad"), exist_ok=True)
    for f in ("pod_tray.step", "top_insert.step"):
        p = os.path.join(ROOT, "cad", f)
        if os.path.exists(p):
            os.unlink(p)
    for n in ("pod_body", "pod_panel", "pod_button", "pod_camera_mount"):
        export_step(mesh_solid(flip_x(parts[n]), 0.02), os.path.join(ROOT, "cad", f"{n}.step"))
    for n, M in (("pod_camera_base_low", low[0]), ("pod_camera_cradle_low", low[1])):
        export_step(mesh_solid(flip_x(M), 0.02), os.path.join(ROOT, "cad", f"{n}.step"))
    export_assembly(os.path.join(ROOT, "cad", "assembly.step"), {n: flip_x(M) for n, M in models.items()})


if __name__ == "__main__":
    main(fast="fast" in sys.argv)
