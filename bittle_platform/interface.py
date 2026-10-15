"""Bittle X platform interface, version 1.0. All numbers for add-on design are here.

The platform is the stock Petoi Bittle X back cover (Bittle_Cover_with_hole_for_Pi.stl)
with 4 pegs on its flat top. Add-ons drop onto the pegs, slide, and click.

This file is the single source of numbers. build.py makes the parts, the checks,
interface.json, SPEC.md and the PDF from it. ../pod.py reads it too.

Frame (the Petoi reference STL frame), units mm:
  X = lateral, +X = robot right side.
  Y = up.
  Z = length, -Z = head end (front), +Z = rear.
  Origin: on the robot center line, at the middle of the cover length.
"""

VERSION = "1.3"

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
PEGS = [(12.0, -8.0), (12.0, 8.0), (-12.0, -8.0), (-12.0, 8.0)]   # (X, Z) centers: 24 x 16, centered
PEG_SHAFT_D = 4.0
PEG_HEAD_D = 7.0
PEG_HEAD_Y0, PEG_HEAD_Y1 = 27.7, 28.9      # head underside, head top
PEG_HEAD_CHAMFER = 0.5                      # 45 deg on the head top edge
PEG_ROOT_Y = 24.3                           # the shaft starts inside the 1.4 mm cover wall
PEG_COLLAR_D = 5.6                          # root collar, Y COVER_TOP-0.3 .. COVER_TOP+0.4
PEG_COLLAR_Y1 = COVER_TOP + 0.4

# --------------------------------------------------------------------------
# Mount plate of an add-on (the part of the add-on that touches the pegs)
# --------------------------------------------------------------------------
MOUNT_Y0 = 26.0                 # bottom face of the mount plate (0.31 over the collar, 0.41 over the logo)
MOUNT_Y1 = 27.5                 # top face of the plate where the peg heads pass (0.2 under the heads)
MOUNT_T = MOUNT_Y1 - MOUNT_Y0   # 1.5
HEAD_CLEAR_Y = PEG_HEAD_Y1 + 0.5   # keep add-on material above this Y over the head sweep (29.4)

# Keyhole, one for each peg, in the plate. The add-on drops on SLIDE forward (-Z)
# of its locked place, then slides SLIDE rearward (+Z) to lock.
SLIDE = 7.0
KEY_BIG_D = 8.4                 # drop-in hole, center at (px, pz + SLIDE) in add-on coordinates
KEY_SLOT_W = 5.2                # slot from (px, pz) to (px, pz + SLIDE), round end at (px, pz)
# Detent: cantilever beam on the +X side of each slot, made by a U slit (fixed only at the root).
# The 4 bumps push the add-on to -X until the pegs touch the -X slot sides. The bump then
# stands DET_TRAVEL into the peg path -> beam travel 0.3. Strain 1.5*d*t/a^2 = 1.1 %.
# v1.3: slot 5.2, drop-in hole 8.4 (0.6 and 0.7 gap each side). The v1.2 tray was still too tight.
#   bump_in follows the slot width, so the beam travel stays 0.3. Arm 7.0: the beam root
#   stays 1 mm clear of the larger drop-in hole of the keyhole in front.
# v1.1: arm 7.6 (was 10). Beam 1.2 = 3 extrusion widths.
DET_TRAVEL = 0.3
DET = dict(beam_w=1.2, slit_w=0.8, bump_r=1.0, bump_in=round(KEY_SLOT_W - PEG_SHAFT_D + DET_TRAVEL, 3),
           bump_dz=2.7, arm=7.0)

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
