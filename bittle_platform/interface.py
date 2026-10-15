"""Bittle X platform interface, version 1.0. All numbers for add-on design are here.

The platform is the stock Petoi Bittle X back cover (Bittle_Cover_with_hole_for_Pi.stl)
with 4 teardrop pegs on its flat top. Add-ons drop onto the pegs, slide, and click.
v2.0 is not compatible with v1.x: reprint the cover and the add-on plate.

This file is the single source of numbers. build.py makes the parts, the checks,
interface.json, SPEC.md and the PDF from it. ../pod.py reads it too.

Frame (the Petoi reference STL frame), units mm:
  X = lateral, +X = robot right side.
  Y = up.
  Z = length, -Z = head end (front), +Z = rear.
  Origin: on the robot center line, at the middle of the cover length.
"""

VERSION = "2.0"

# --------------------------------------------------------------------------
# Stock cover (measured from the Petoi STL)
# --------------------------------------------------------------------------
COVER_STL = "Bittle_Cover_with_hole_for_Pi.stl"
COVER_TOP = 25.29               # Y of the flat top surface
COVER_INNER_AT_PEGS = 23.89     # Y of the inner surface under the pegs
COVER_FLAT = dict(x=(-15.37, 15.37), z=(-21.37, 21.37))   # flat area of the top
COVER_END_Z = (-36.95, 36.95)
LOGO = dict(x=(-9.14, 9.14), z=(-7.85, 7.80), top=25.59)  # raised Petoi logo, 0.3 high
SLOT = dict(x0=24.25, x1=27.75, y0=19.5, z0=11.75, z1=25.75)   # Pi slot in the cover top
# BiBoard 5-pin female header in the slot (GND, +5V, TX2, RX2, ..). Height is a photo estimate.
HDR = dict(x0=24.73, x1=27.27, z0=12.4, z1=25.1, top=29.1)
PLUG_TOP = 48.0                 # Y of free space for straight Dupont plugs and wires on the header

# --------------------------------------------------------------------------
# Pegs (part of the platform)
# --------------------------------------------------------------------------
# v2.0: teardrop pegs. The head is a teardrop with the point to the front (-Z, toward the robot head).
# The drop-in holes have the same shape, so an add-on goes on in one direction only: turned 180 deg,
# the round side of each hole is where the point of the head is.
# The shaft and the collar are teardrops with the point to the rear (+Z). The cover prints standing
# on its rear end, so these points are down and the shaft and the collar print without overhangs.
PEGS = [(12.0, -10.0), (12.0, 10.0), (-12.0, -10.0), (-12.0, 10.0)]   # (X, Z) centers: 24 x 20, centered
TIP_DEG = 45.0                  # half angle of the teardrop point
HEAD_TIP = -1.0                 # the head point is toward -Z; the shaft and collar points are toward +Z
HEAD_TIP_DEG = 30.0             # a long head point: turned 180 deg, about 3 mm of it is over the plate
PEG_SHAFT_D = 4.0               # round part of the shaft teardrop
PEG_HEAD_D = 7.0                # round part of the head teardrop
PEG_HEAD_Y0, PEG_HEAD_Y1 = 27.8, 29.0      # head underside, head top
PEG_HEAD_CHAMFER = 0.5                      # 45 deg on the head top edge
PEG_ROOT_Y = 24.3                           # the shaft starts inside the 1.4 mm cover wall
PEG_COLLAR_D = 5.6                          # root collar, Y COVER_TOP-0.3 .. COVER_TOP+0.4
PEG_COLLAR_Y1 = COVER_TOP + 0.4


def tip_len(d, deg=TIP_DEG):
    """Distance from the center of a teardrop (round part d, half angle deg) to its point."""
    import math
    return d / 2 / math.sin(math.radians(deg))


# --------------------------------------------------------------------------
# Mount plate of an add-on (the part of the add-on that touches the pegs)
# --------------------------------------------------------------------------
MOUNT_Y0 = 26.0                 # bottom face of the mount plate (0.31 over the collar, 0.41 over the logo)
MOUNT_Y1 = 27.5                 # top face of the plate where the peg heads pass (0.3 under the heads)
MOUNT_T = MOUNT_Y1 - MOUNT_Y0   # 1.5
HEAD_CLEAR_Y = PEG_HEAD_Y1 + 0.5   # keep add-on material above this Y over the head sweep (29.5)

# Keyhole, one for each peg, in the plate. The add-on drops on SLIDE forward (-Z)
# of its locked place, then slides SLIDE rearward (+Z) to lock.
SLIDE = 7.0
KEY_HOLE_GAP = 0.45             # drop-in hole = the head teardrop + this gap, center at (px, pz + SLIDE)
KEY_SLOT_GAP = 0.35             # slot = the shaft + this gap each side, from (px, pz) to (px, pz + SLIDE)
KEY_SLOT_W = PEG_SHAFT_D + 2 * KEY_SLOT_GAP      # 4.7
# The front end of the slot is round. Its center is KEY_SLOT_GAP behind the peg, so a peg
# at (px, pz) touches it at the front: this is the stop of the locked place.
# Click (detent): two cantilever beams, one on each side of the slot, made by U slits
# (fixed only at the root, toward the front). Each beam has a round bump at its free end.
# The bumps hold the shaft against the front stop and center it in X: the add-on does not rattle.
# Shaft between the bumps: beam travel = travel. With a 1.2 x 1.5 beam, arm 7.0, PLA (E 2400):
# about 4 N peak to slide the add-on on or off (all 8 beams), strain 1.1 % (build.py: detent_force()).
DET = dict(beam_w=1.2, slit_w=0.8, arm=7.5, bump_r=1.5, travel=0.35, preload=0.05, free_end=1.2)
E_PLA = 2400.0                  # MPa, for the detent force estimate
MU_PLA = 0.3                    # PLA on PLA friction, for the detent force estimate

# --------------------------------------------------------------------------
# Envelope (checked with the pod; outside this, check the robot yourself)
# --------------------------------------------------------------------------
ENVELOPE = dict(
    z=(-40.0, 66.0),            # front and rear limits used by the pod
    half_w_low=33.6,            # max |X| at the bottom edge over the hip plates (lid hugs the shoulders, 0.4 gap)
    half_w_high=26.4,           # max |X| above Y 31 (pod spine)
    top=59.4,                   # pod top; no robot limit, but a high mass makes the robot less stable
    com_z_max=10.0,             # keep the add-on center of mass within this distance of Z 0 (robot center)
    hug_gap=0.4,                # gap to the cover and the shoulder plates
)
