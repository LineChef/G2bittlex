"""Bittle X Pi add-on rev 0.11 (was the Pi pod): stock cover + pegs, pod tray, pod lid.

Frame = Petoi reference STL frame (reference/*.stl):
  X = lateral (+X = robot right), Y = up, Z = length (-Z = head end). mm.

Parts
  cover_pegs : the platform (bittle_platform/): Petoi cover, unchanged, plus 4 pegs.
               Each peg root ends inside the 1.6 mm cover wall, so the inside
               of the cover (BiBoard space, touch FPC) does not change.
  pod_tray   : tray. Keyholes drop over the pegs 7 mm forward of the locked place, slide rearward, click
               (cantilever detents). A notch over the cover slot lets the BiBoard wires in.
               Holds the Pi Zero 2 W + PiSugar 2 stack (over the BiBoard header, between the
               PiSugar button and switch, near the center line), the 3 W speaker (on two pins
               on a wall at the front end), the NS4168 amp (crosswise at the rear) and the
               SPH0645 mic (left side, port to the left). See balance().
  pod_lid    : lofted shell: flat top, haunches over the hips, chamfered nose and rump,
               low side skirt over the cover slot. It snaps onto the tray rim. Its lower edge
               follows the cover and the hip plates (0.4 mm gap). Two port bays in the right
               side: the wall steps in to the port edge of the stack.
Print: every part prints without supports (see check(): overhang rows).

The camera (Petoi AI Vision Module) stays in the head, as Petoi designs it.
"""
import math
import os
import sys

import numpy as np
import manifold3d as m3
from build123d import (
    Axis, Box, Cylinder, Face, Pos, Rot, Wire, Sphere, Cone, extrude, fillet, loft,
    export_stl, Plane, Spline, offset, Kind, RectangleRounded,
)

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))            # the folder that holds bittle_platform/
from bittle_platform import interface as PI          # platform v1.1: cover, pegs, keyholes
REF = os.path.join(ROOT, "reference")                # vendor models (Pi Zero, PiSugar 2)
PREF = os.path.join(os.path.dirname(ROOT), "bittle_platform", "reference")   # Petoi robot parts
OUT = os.path.join(ROOT, "stl")

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------
COVER_STL = PI.COVER_STL
COVER_TOP = PI.COVER_TOP
COVER_INNER_TOP = 23.69    # inner surface under the flat top
COVER_END_Z = 36.95

# Lid shape (outer surface)
ZF, ZR = -40.0, 66.0        # front (speaker) and rear (amp)
T_WALL = 1.6
W_FRONT, W_MAIN = 26.4, 26.4    # upper half widths: front, spine
W_HAUNCH = 33.6                 # half width at the bottom over the hip plates
HAUNCH_Z = (34.0, 40.0, 47.0, 53.0)   # ramp in, full, full, ramp out
W_SKIRT = 32.4                  # half width at the bottom over the cover slot (slot to |x| 30.03)
SKIRT_Z = (-4.0, 8.0)           # ramp in; the skirt joins the haunch
# The lid prints upside down on its flat top. Every overhang is 45 deg or less:
# flat top over the full length, 45 deg chamfers on the top edges, nose and rump,
# straight bottom flare (about 39 deg at the haunches).
H_MAIN = 59.4               # the speaker stands on edge at the front (31 mm tall)
W_BULGE = 30.0              # upper half width over the BiBoard header (Dupont plugs)
BULGE_Z = (9.9, 11.4, 26.1, 27.6)   # blister over the header: steep ends between the button and the switch
R_PLAN_F, R_PLAN_R = 4.0, 8.0
C_NOSE, C_RUMP = 4.0, 4.5   # 45 deg end chamfers on the top
C_TOP = 3.5                 # 45 deg chamfer on the top edges of the cross section
Y_BASE, Y_FLARE = 12.0, (22.0, 31.0)
HUG_GAP = 0.4
LID_MIN_Y = 18.0            # lid edge over the rear (no published rear plate)

# Tray
FLOOR_Y0, FLOOR_Y1 = PI.MOUNT_Y0, PI.MOUNT_Y1   # tray floor = platform mount plate
TRAY_GAP = 0.4              # tray outline = lid inner wall - 0.4
RIM_T, RIM_TOP = 1.2, 31.0
RAIL_TOP = 29.1             # the cell rests on rails above the peg heads
# (side, z, half length) rim snaps. The right snaps are short: the port bays and the cover slot are on that side.
SNAPS = [(-1, -6.0, 5.0), (-1, 30.0, 5.0), (1, -16.6, 2.7), (1, 49.0, 2.8)]
# The lid wall is straight only above Y_FLARE[1] (31), so each bump stands on a rim tab, over that height.
SNAP_Y, SNAP_TAB_TOP = 33.0, 34.6
# Pegs (on the cover) and keyholes (in the tray): platform interface v1.1
PEGS = PI.PEGS
PEG_SHAFT_D, PEG_HEAD_D = PI.PEG_SHAFT_D, PI.PEG_HEAD_D
PEG_ROOT_Y = PI.PEG_ROOT_Y
PEG_HEAD_Y0, PEG_HEAD_Y1 = PI.PEG_HEAD_Y0, PI.PEG_HEAD_Y1
SLIDE = PI.SLIDE            # the tray drops on SLIDE forward (-Z) of its place, then slides rearward (+Z) to lock
KEY_BIG_D, KEY_SLOT_W = PI.KEY_BIG_D, PI.KEY_SLOT_W
DET = PI.DET

# Speaker: NULLLAB 3 W 4 ohm box speaker (user ruler measurements), crosswise:
# ears along X (45 overall, 4 mm holes), body 27 (X) x 30 (Z) x 14.3 tall.
SPK = dict(l=45.0, body_l=27.0, d=31.0, h=14.3, ear_t=1.5, hole_d=4.0, hole_in=4.5, xc=0.0)
SPK["holes_x"] = (SPK["xc"] - SPK["l"] / 2 + SPK["hole_in"], SPK["xc"] + SPK["l"] / 2 - SPK["hole_in"])
# Pins: point-down teardrop (no flat underside on a 9.7 mm horizontal pin). Round top r 1.55, 45 deg sides
# to a point 2.19 below the center. The center is 0.35 over the hole center: the ear rests on the pin top,
# and the point stays 0.16 inside the hole.
SPK_PIN_D = 3.1
SPK_PIN_DY = 0.35
# The ear tabs can be at the rear face of the body or up to half way up its side (not measured).
# The pins reach both: the body can then stand against the wall with the tabs further out on the pins.
SPK_PIN_L = SPK["ear_t"] + SPK["h"] / 2 + 1.0
# Speaker at the front: on edge, ear plate to the rear, sound face to the front. The ear plate
# hangs on two pins on a wall at the front end of the tray. Lid ribs in front of the body hold it on.
# The speaker is the heaviest part after the stack: at the front it balances the add-on (balance()).
TRAY_Z0 = -19.3                             # front end of the tray floor = front face of the wall
TRAY_Z1 = 57.2                              # rear end of the tray floor (under the amp post)
SPK_ZE = TRAY_Z0                            # rear face of the ear plate
SPK_Y0 = FLOOR_Y0                           # bottom of the ear plate: 0.7 over the cover top
SPK_WALL = dict(x=21.0, y1=46.0, t=2.0)     # wall: |X| <= 21, Y from the tray bottom to 46 (2 mm over the pin tops)

# Pi Zero 2 W + PiSugar 2 (1200 mAh) stack.
# "u" = height in the stack frame (Pi PCB bottom at u = -0.5).
BAT_L, BAT_W, BAT_T = 56.0, 29.0, 10.0   # PiSugar repo model2/batt-1200.SLDPRT
BAT_GAP = 0.3
U_PS2_PCB = (-3.0, -2.0)
U_PS2_LOW = -5.6
U_BAT_TOP = U_PS2_LOW - BAT_GAP
U_BAT_BOT = U_BAT_TOP - BAT_T
U_PI_PCB = (-0.5, 0.8)
U_PI_TOP = 23.53 - 18.83 - 0.5
DY = RAIL_TOP - U_BAT_BOT                 # body y = u + DY
# The ports face +X (the side with the cover slot). The stack is 30 wide: GPIO edge at
# STACK_GPIO_X, port edge at STACK_GPIO_X + 30. CSI end at the front, SD end at the rear.
# The stack is the heaviest part (about 42 g): it stands near the center line (balance()).
# The ports are 11 mm inside the right wall. The lid openings stay in the wall.
STACK_GPIO_X = -16.5
# The BiBoard header (z 12.4-25.1) with its Dupont plugs is between the PiSugar
# button (Z_CSI + 21.98) and switch (Z_CSI + 52.25).
Z_CSI = -16.0                             # CSI end, at the front
Z_SD = Z_CSI + 65.0                       # SD card end, over the rear hips
PI_PCB_TOP = U_PI_PCB[1] + DY
PI_TOP = U_PI_TOP + DY
PI_HOLES = [(STACK_GPIO_X + a, Z_SD - b) for a in (3.5, 26.5) for b in (3.5, 61.5)]
SCREW_HEAD = 1.8
HOLD_GAP = 0.5

# PiSugar 2 port-edge features (model2/pisugar2Board.STL), from the CSI end
CHG_FROM_CSI, CHG_U = 11.28, -4.3
BTN_FROM_CSI, BTN_U = 21.98, -4.0
SW_FROM_CSI, SW_U = 52.25, -3.86
CHG_Z, CHG_Y = Z_CSI + CHG_FROM_CSI, CHG_U + DY
BTN_Z, BTN_Y = Z_CSI + BTN_FROM_CSI, BTN_U + DY
SW_Z, SW_Y = Z_CSI + SW_FROM_CSI, SW_U + DY
PORT_FACE_X = STACK_GPIO_X + 30.9
# Port bays: the right lid wall steps in to the port edge of the stack.
# Bay A: PiSugar charge port and button, Pi power and data USB. Bay B: Pi mini-HDMI, PiSugar switch.
# The bay floor is a 45 deg slope (no overhang in the print). The BiBoard header is between the bays.
BAY_X = 15.2          # bay face: 0.45 outside the port faces (X 14.75)
BAY_Y = 37.0          # top of the floor slope at the bay face (charge plug body from Y 37.2)
BAY_TOP = 52.0        # the wall comes down to here over the ports (mini-HDMI top 49.2)
BAYS = [(-11.5, 13.9), (28.8, 44.0)]   # z0, z1: the plug bodies (PORT_PLUGS) + 0.6 for the 1 mm corner radius
# The data USB plug body passes 0.25 mm over the BiBoard Dupont plugs: the bay wall is open over them.
# Top insert: a vent panel in a second color. It goes into a window in the flat top from outside
# and sits flush on a 45 deg seat. Four clips catch under a frame below the window.
# The frame bottom is 3.8 mm over the Pi (wires go over the Pi).
TOP_INS = dict(hx=11.5, z0=0.0, z1=34.0, r=3.0,   # window at the outer face of the top
               seat=0.8,                           # 45 deg seat: the window is 0.8 smaller below it
               frame_t=1.2, frame_y0=53.0,         # frame around the window under the top wall
               clr=0.15, leg_t=0.8, leg_w=5.0, hook=0.6, legs_z=(-9.0, 9.0))   # hook: 0.45 under the frame; leg strain 2.3 %
# Plug bodies for the access check: (Y, Z, width along Z, height), port centers from the models
PORT_PLUGS = dict(charge=(41.2, CHG_Z, 12.0, 8.0), pi_power=(47.1, -5.1, 11.0, 7.5),
                  pi_usb=(47.1, 7.8, 11.0, 7.5), pi_hdmi=(47.5, 36.4, 14.0, 8.5))

# NS4168 amp board on edge, crosswise behind the stack, components to the rear.
# Local frame (amp_place() puts it in the body): PCB x0..x1 with the back face at x 0,
# components on the -X face, length along Z, centered.
AMP = dict(t=1.6, l=38.4, h=22.4, comp=10.0)
AMP_Y0 = FLOOR_Y1 + 0.3                   # amp bottom edge, just over the floor
AMP["x1"], AMP["x0"] = 0.0, -AMP["t"]
AMP["z0"], AMP["z1"] = -AMP["l"] / 2, AMP["l"] / 2
AMP_HOLE_Z = AMP["z1"] - 15.2
AMP_ZB = Z_SD + 0.3 + 1.6 + 0.6          # back face of the PCB: 0.6 behind the rear locators


def amp_place(shape):
    """Local amp frame -> body: turn 90 deg about Y (local -X -> +Z), back face at Z AMP_ZB."""
    return Pos(0, 0, AMP_ZB) * Rot(0, 90, 0) * shape


# SPH0645 mic board (Adafruit 3421 size) on the left side, beside the GPIO edge of the stack,
# on edge, port face to the left (-X), away from the speaker. It stands in a slot in a base on
# the tray floor; a stub on the lid holds its top edge. Local frame (mic_place()): board in the
# XY plane, centered at X 0, Z 0, port face +Z.
MIC = dict(l=16.7, w=12.7, t=1.8, xc=0.0, y0=31.3, slot=3.0, clr=0.15)
MIC["x0"], MIC["x1"] = -MIC["w"] / 2, MIC["w"] / 2
MIC["z0"], MIC["z1"] = -MIC["t"] / 2, MIC["t"] / 2
MIC["y1"] = MIC["y0"] + MIC["l"]
MIC_X, MIC_Z = -20.5, 18.0                # board center in the body


def mic_place(shape):
    """Local mic frame -> body: turn -90 deg about Y (local +Z -> -X), center at (MIC_X, MIC_Z)."""
    return Pos(MIC_X, 0, MIC_Z) * Rot(0, -90, 0) * shape

# Camera cable: the Grove cable of the Petoi AI Vision Module (in the head) comes along the left
# side of the robot and goes through a slot in the left lid wall, behind the speaker and over the
# tray rim, to the Pi I2C pins. Slot for a flat 4-wire cable (about 5 x 1.3), in the straight wall above the flare.
CAM_SLOT = dict(zc=-14.5, w=6.0, y0=32.0, h=2.2)

# Pi slot in Bittle_Cover_with_hole_for_Pi.stl (measured: Bittle_Cover.stl minus it, 0.5 grid)
SLOT = PI.SLOT
# BiBoard 5-pin female header (GND, +5V, TX2, RX2, ..) in the slot; top about 8 mm above
# the cover (photos). Straight Dupont plugs: 14 mm housing, then the wires go up to PLUG_TOP.
HDR = PI.HDR
PLUG_H, PLUG_TOP = 14.0, PI.PLUG_TOP


def ps2_to_body():
    """PiSugar 2 board model frame -> body. The model has the Pi side at -Y."""
    return np.array([[0, 0, 1, STACK_GPIO_X],
                     [0, -1, 0, DY],
                     [1, 0, 0, Z_CSI],
                     [0, 0, 0, 1]], dtype=float)


def pi_to_body():
    """Pi Zero model (PiSugar repo model3 frame) -> body."""
    return np.array([[0, 0, 1, STACK_GPIO_X - 3.08],
                     [0, 1, 0, DY - 18.83 - 0.5],
                     [-1, 0, 0, Z_SD + 6.89],
                     [0, 0, 0, 1]], dtype=float)


# --------------------------------------------------------------------------
# Lid profile functions
# --------------------------------------------------------------------------
def smooth(a, b, v):
    t = min(max((v - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def end_round(z):
    """Plan rounding at the front and rear ends (amount to subtract)."""
    if z < ZF + R_PLAN_F:
        d = ZF + R_PLAN_F - z
        return R_PLAN_F - math.sqrt(max(R_PLAN_F ** 2 - d * d, 0.0))
    if z > ZR - R_PLAN_R:
        d = z - (ZR - R_PLAN_R)
        return R_PLAN_R - math.sqrt(max(R_PLAN_R ** 2 - d * d, 0.0))
    return 0.0


def wu(z):
    a, b, c, d = BULGE_Z
    k = smooth(a, b, z) * (1 - smooth(c, d, z))
    return W_FRONT + (W_MAIN - W_FRONT) * smooth(-8.0, -2.0, z) + (W_BULGE - W_MAIN) * k - end_round(z)


def wb(z):
    a, b, c, d = HAUNCH_Z
    ks = smooth(*SKIRT_Z, z) * (1 - smooth(c, d, z))
    kh = smooth(a, b, z) * (1 - smooth(c, d, z))
    return max(wu(z), wu(z) + (W_SKIRT - wu(z)) * ks + (W_HAUNCH - W_SKIRT) * kh)


def hgt(z):
    return H_MAIN - max(0.0, C_NOSE - (z - ZF)) - max(0.0, C_RUMP - (ZR - z))


def section_pts(z, Wu, Wb, H, c, yb):
    """Polygon, right side up, over the top, down the left: (Wb, yb) ... (-Wb, yb).
    Straight flare from Y_FLARE[0] to Y_FLARE[1], 45 deg top chamfer of size c."""
    right = [(Wb, yb), (Wb, Y_FLARE[0]), (Wu, Y_FLARE[1]), (Wu, H - c), (Wu - c, H)]
    left = [(-x, y) for x, y in reversed(right)]
    return right + left


def section_face(z, Wu, Wb, H, c, yb):
    pts = [(x, y, z) for x, y in section_pts(z, Wu, Wb, H, c, yb)]
    return Face(Wire.make_polygon(pts, close=True))


def erode(f, zs, t):
    """2D erosion (disc radius t) of the region under f(z); f = -inf outside."""
    vals = np.array([f(z) for z in zs])
    out = np.empty_like(vals)
    dz = zs[1] - zs[0]
    k = int(math.ceil(t / dz))
    for i in range(len(zs)):
        best = 1e9
        for j in range(max(0, i - k), min(len(zs), i + k + 1)):
            d = abs(zs[j] - zs[i])
            if d <= t:
                best = min(best, vals[j] - math.sqrt(t * t - d * d))
        out[i] = best
    return out


_INNER = {}


def inner_profile():
    """Eroded (inner surface) profile functions, sampled on a fine z grid."""
    if not _INNER:
        zg = np.linspace(ZF - 3, ZR + 3, 1300)
        inside = lambda f: (lambda z: f(z) if ZF <= z <= ZR else -100.0)
        _INNER["z"] = zg
        _INNER["wu"] = erode(inside(wu), zg, T_WALL)
        _INNER["wb"] = erode(inside(wb), zg, T_WALL)
        _INNER["h"] = erode(inside(hgt), zg, T_WALL)
    return _INNER


def inner_at(z):
    I = inner_profile()
    return (float(np.interp(z, I["z"], I["wu"])), float(np.interp(z, I["z"], I["wb"])),
            float(np.interp(z, I["z"], I["h"])))


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


def tray_outline(y, extra=0.0, zmax=None, zmin=None):
    """Plan face at height y: lid inner wall at the rim height, minus TRAY_GAP + extra."""
    zs = np.linspace(ZF, ZR, 400)
    valid = [z for z in zs if inner_at(z)[0] > 3.0 + TRAY_GAP and inner_at(z)[2] > RIM_TOP + 3]
    zmax = TRAY_Z1 if zmax is None else zmax
    zmin = TRAY_Z0 if zmin is None else zmin
    za, zb = max(valid[0] + TRAY_GAP, zmin) + extra, min(valid[-1] - TRAY_GAP, zmax) - extra
    pts = []
    for z in np.linspace(za, zb, 400):
        w = min(inner_at(min(max(z + dz, valid[0]), valid[-1]))[0] for dz in np.linspace(-1.6, 1.6, 9))   # steep blister ends
        pts.append((z, w - TRAY_GAP - extra))
    right = [(w, y, z) for z, w in pts]
    left = [(-w, y, z) for z, w in reversed(pts)]
    return Face(Wire.make_polygon(right + left, close=True))


def plan_prism(y0, y1, extra=0.0, zmax=None, zmin=None):
    return extrude(tray_outline(y0, extra, zmax, zmin), amount=y1 - y0, dir=(0, 1, 0))


def stadium_x(y, z, x0, x1, w, h):
    """Stadium hole along X: width w (along Z), height h (along Y)."""
    r = h / 2
    s = box(x0, x1, y - r, y + r, z - w / 2 + r, z + w / 2 - r)
    s += cyl_x(y, z - w / 2 + r, x0, x1, r)
    s += cyl_x(y, z + w / 2 - r, x0, x1, r)
    return s


# --------------------------------------------------------------------------
# Parts
# --------------------------------------------------------------------------
def build_pegs():
    """The platform pegs (bittle_platform/build.py)."""
    from bittle_platform import build as BP
    return BP.pegs()


def bay_solid(off=0.0):
    """The open space of the port bays, grown by off. The lid wall is the shell from 0 to T_WALL."""
    prof = Face(Wire.make_polygon([(BAY_X, 100, 0), (BAY_X, BAY_Y, 0), (60, BAY_Y - (60 - BAY_X), 0), (60, 100, 0)], close=True))
    if off:
        prof = offset(prof, off, kind=Kind.ARC)
    S = None
    for z0, z1 in BAYS:
        pts = [(BAY_X, z0), (BAY_X, z1), (60, z1), (60, z0)]      # plan (x, z), made in XY and turned onto XZ
        f = Face(Wire.make_polygon([(x, z, 0) for x, z in pts], close=True))
        f = f.fillet_2d(1.0, [v for v in f.vertices() if v.X < 30])
        if off:
            f = offset(f, off, kind=Kind.ARC)
        b = Rot(90, 0, 0) * extrude(f, amount=100, dir=(0, 0, -1))
        S = b if S is None else S + b
    return S & extrude(prof, amount=100, both=True)


def rrect(y, hx, z0, z1, r):
    """Rounded rectangle in the plane at height y: |x| <= hx, z0..z1."""
    return Pos(0, y, (z0 + z1) / 2) * Rot(90, 0, 0) * RectangleRounded(2 * hx, z1 - z0, r)


def rrect_prism(hx, z0, z1, r, y0, y1):
    return extrude(rrect(y0, hx, z0, z1, r), amount=y1 - y0, dir=(0, 1, 0))


def top_window():
    """The cut in the lid top for the insert: 45 deg seat, then straight through the frame."""
    T, s = TOP_INS, TOP_INS["seat"]
    seat = loft([rrect(H_MAIN, T["hx"], T["z0"], T["z1"], T["r"]),
                 rrect(H_MAIN - s, T["hx"] - s, T["z0"] + s, T["z1"] - s, T["r"] - s)])
    return (seat + rrect_prism(T["hx"], T["z0"], T["z1"], T["r"], H_MAIN - 0.01, H_MAIN + 2)
            + rrect_prism(T["hx"] - s, T["z0"] + s, T["z1"] - s, T["r"] - s, T["frame_y0"] - 1, H_MAIN - s + 0.01))


def top_frame():
    T, s = TOP_INS, TOP_INS["seat"]
    t = T["frame_t"]
    return rrect_prism(T["hx"] - s + t, T["z0"] + s - t, T["z1"] - s + t, T["r"] - s + t, T["frame_y0"], H_MAIN - T_WALL + 0.1)


def build_top_insert():
    """Vent panel: flush top on the 45 deg seat, vent slots, 4 clips under the frame."""
    T, s, c = TOP_INS, TOP_INS["seat"], TOP_INS["clr"]
    hx, z0, z1, r = T["hx"] - c, T["z0"] + c, T["z1"] - c, T["r"] - c
    y_top = H_MAIN - c * (math.sqrt(2) - 1)        # it sits on the seat: 0.06 under the lid top
    ins = loft([rrect(y_top, hx, z0, z1, r), rrect(y_top - s, hx - s, z0 + s, z1 - s, r - s)])
    ins += rrect_prism(hx - s, z0 + s, z1 - s, r - s, H_MAIN - T_WALL, y_top - s + 0.01)
    zc = (T["z0"] + T["z1"]) / 2
    n = int((T["z1"] - T["z0"] - 6.0) // 3.4) + 1
    for i in range(n):          # vent slots, as in the lid before
        zs = zc + (i - (n - 1) / 2) * 3.4
        ins -= box(-8.0, 8.0, H_MAIN - T_WALL - 1, H_MAIN + 1, zs - 0.7, zs + 0.7)
    xo = hx - s                                     # leg outer face: 0.15 from the frame wall
    yb = T["frame_y0"] - 0.1                        # hook catch face: 0.1 under the frame
    for sx in (-1, 1):
        for dz in T["legs_z"]:
            za, zb = zc + dz - T["leg_w"] / 2, zc + dz + T["leg_w"] / 2
            ins += box(*sorted((sx * xo, sx * (xo - T["leg_t"]))), yb - 1.2, H_MAIN - T_WALL + 0.01, za, zb)
            hook = box(*sorted((sx * xo - sx * 0.01, sx * (xo + T["hook"]))), yb - 1.2, yb, za, zb)
            hook -= Pos(sx * (xo + T["hook"]), yb - 1.2, (za + zb) / 2) * Rot(0, 0, 45) * Box(1.7, 1.7, zb - za + 1)   # lead-in
            ins += hook
    return ins


def build_tray():
    t = plan_prism(FLOOR_Y0, FLOOR_Y1)
    rim = plan_prism(FLOOR_Y1, RIM_TOP) - plan_prism(FLOOR_Y1 - 1, RIM_TOP + 1, RIM_T)
    rim -= box(-40, 40, FLOOR_Y1, RIM_TOP + 1, AMP_ZB + AMP["t"], TRAY_Z1 + 1)   # no rim behind the amp: its parts are there
    t += rim
    # cell rails (clear of the peg heads and slide paths)
    zb0, zb1 = Z_SD - 4.5 - BAT_L, Z_SD - 4.5
    for xc in (-6.0, 6.0):     # |X| <= 7.2: clear of the peg heads (X 8.2 to 15.8) and their slide paths
        t += box(xc - 1.0, xc + 1.0, FLOOR_Y1, RAIL_TOP, zb0 + 1, zb1 - 1)
    # corner locators (L shapes) around the PiSugar 2 PCB outline
    c = 0.3
    loc_top = U_PS2_PCB[1] + DY + 0.8
    x0, x1 = STACK_GPIO_X - c, STACK_GPIO_X + 30.0 + c
    z0, z1 = Z_CSI - c, Z_SD + c
    loc = None
    for xe, sx in ((x0, -1), (x1, 1)):
        for ze, sz in ((z0, -1), (z1, 1)):
            for b_ in (box(*sorted((xe, xe - sx * 6.0)), FLOOR_Y1, loc_top, *sorted((ze, ze + sz * 1.6))),
                       box(*sorted((xe, xe + sx * 1.6)), FLOOR_Y1, loc_top, *sorted((ze, ze - sz * 6.0)))):
                loc = b_ if loc is None else loc + b_
    for (px, pz) in PEGS:      # full height cut: no locator part over a peg head or its slide path
        loc -= box(px - 4.3, px + 4.3, FLOOR_Y1 - 1, loc_top + 1, pz - 4.3, pz + SLIDE + 4.3)
    t += loc
    t += amp_place(amp_post())
    t += mic_place(mic_base())
    # keyholes with a cantilever click detent
    for (px, pz) in PEGS:
        t -= keyhole_cut(px, pz)
        t += keyhole_bump(px, pz)
    # notch over the cover slot (floor and rim, open to the side), includes the slide travel
    t -= box(SLOT["x0"] - 0.3, 40.0, FLOOR_Y0 - 1, RIM_TOP + 1, SLOT["z0"] - 0.6, SLOT["z1"] + SLIDE + 0.6)
    t &= plan_prism(FLOOR_Y0 - 1, H_MAIN)   # nothing outside the lid's inner wall
    t += speaker_wall() & plan_prism(FLOOR_Y0 - 1, H_MAIN, zmin=ZF)   # the pins stand in front of the tray
    t -= bay_solid(T_WALL + TRAY_GAP)   # clear of the bay walls of the lid
    for (sx, zc, hl) in SNAPS:   # rim tab and bump: the bump stands 0.8 out of the rim, 0.4 into the lid wall
        w_i = inner_at(zc)[0] - TRAY_GAP
        t += box(*sorted((sx * (w_i - RIM_T), sx * w_i)), RIM_TOP - 0.01, SNAP_TAB_TOP, zc - hl, zc + hl)
        t += teardrop_z(sx * w_i, SNAP_Y, zc - hl + 1, zc + hl - 1, 0.8, 0.8 * math.sqrt(2))   # 45 deg underside
    return t


def keyhole_cut(px, pz):
    """Platform keyhole with the U slit of the detent beam (bittle_platform/build.py)."""
    from bittle_platform import build as BP
    return BP.keyhole_cutter(px, pz)


def keyhole_bump(px, pz):
    from bittle_platform import build as BP
    return BP.detent_bump(px, pz)


def teardrop_x(y, z, x0, x1, r, flat):
    """Pin along X with a teardrop section: round top, 45 deg sides below, flat bottom at y - flat.
    It prints along its length without supports (the part prints with +Y up)."""
    c = cyl_x(y, z, x0, x1, r)
    d = Pos((x0 + x1) / 2, y, z) * Rot(45, 0, 0) * Box(x1 - x0, 2 * r, 2 * r)
    d &= box(x0, x1, y - flat, y - r * math.sqrt(0.5), z - 2 * r, z + 2 * r)   # below the tangent points only
    return c + d


def teardrop_z(x, y, z0, z1, r, flat):
    """Pin along Z with a teardrop section (see teardrop_x)."""
    c = cyl_z(x, y, z0, z1, r)
    d = Pos(x, y, (z0 + z1) / 2) * Rot(0, 0, 45) * Box(2 * r, 2 * r, z1 - z0)
    d &= box(x - 2 * r, x + 2 * r, y - flat, y - r * math.sqrt(0.5), z0, z1)
    return c + d


def speaker_wall():
    """Wall at the front end of the tray with two pins (forward) through the speaker ear holes."""
    W = SPK_WALL
    w = box(-W["x"], W["x"], FLOOR_Y0, W["y1"], SPK_ZE, SPK_ZE + W["t"])
    yc = SPK_Y0 + SPK["d"] / 2 + SPK_PIN_DY
    r = SPK_PIN_D / 2
    zp = SPK_ZE - SPK_PIN_L                                                 # front end of the pin
    for xh in SPK["holes_x"]:
        w += teardrop_z(xh, yc, zp, SPK_ZE + 0.01, r, r * math.sqrt(2))
    return w


def amp_post():
    """Post on the component side of the amp board; two 4.6 mm pins in its 4.7 mm holes."""
    xf = AMP["x0"]
    yb = AMP_Y0
    p = box(xf - 3.5, xf, FLOOR_Y1, yb + AMP["h"] - 1.0, AMP_HOLE_Z - 2.3, AMP_HOLE_Z + 2.3)
    for dy in (3.2, AMP["h"] - 3.2):
        p += teardrop_x(yb + dy, AMP_HOLE_Z, xf - 0.1, AMP["x1"] - 0.8, 2.3, 2.0)    # flat inside the 4.7 hole
        p += Pos(AMP["x1"] - 0.55, yb + dy, AMP_HOLE_Z) * Rot(0, 90, 0) * Cone(2.3, 1.9, 0.5)   # lead-in
    return p


def mic_base():
    """Base on the tray floor with a slot for the bottom edge of the mic board."""
    M, c = MIC, MIC["clr"]
    b = box(M["x0"] - 2.0, M["x1"] + 2.0, FLOOR_Y1 - 0.01, M["y0"] + M["slot"], M["z0"] - 1.8, M["z1"] + 1.8)
    b -= box(M["x0"] - c, M["x1"] + c, M["y0"], M["y0"] + M["slot"] + 1, M["z0"] - c, M["z1"] + c)
    return b


def mic_stub():
    """Stub on the lid top with a slot for the top edge of the mic board (prints from the bed)."""
    M, c = MIC, MIC["clr"]
    s = box(M["xc"] - 3.0, M["xc"] + 3.0, M["y1"] - 2.0, H_MAIN, M["z0"] - 1.8, M["z1"] + 1.8)
    s -= box(M["xc"] - 4.0, M["xc"] + 4.0, M["y1"] - 3.0, M["y1"] + c, M["z0"] - c, M["z1"] + c)
    return s


def lid_stations(z0, z1):
    """Dense stations, denser at the ends and at the profile ramps."""
    base = list(np.arange(z0, z1, 1.5)) + [z1]
    extra = list(np.linspace(z0, z0 + 6, 9)) + list(np.linspace(z1 - 9, z1, 13))
    for a, b in (BULGE_Z[:2], BULGE_Z[2:]):
        extra += list(np.linspace(a - 0.3, b + 0.3, 7))
    zs = sorted(set(round(z, 3) for z in base + extra if z0 <= z <= z1))
    return [z for i, z in enumerate(zs) if i == 0 or z - zs[i - 1] > 0.2]


def lid_solids():
    zs = lid_stations(ZF, ZR)
    outer = loft([section_face(z, wu(z), wb(z), hgt(z), C_TOP, Y_BASE) for z in zs], ruled=True)
    I = inner_profile()
    ok = (I["wu"] > 4) & (I["h"] > Y_FLARE[1] + 4)
    zi0, zi1 = I["z"][ok][0] + 0.05, I["z"][ok][-1] - 0.05
    secs = []
    for z in lid_stations(zi0, zi1):
        w_i, b_i, h_i = inner_at(z)
        secs.append(section_face(z, w_i, b_i, h_i, C_TOP - (2 - math.sqrt(2)) * T_WALL, Y_BASE - 2.0))
    inner = loft(secs, ruled=True)
    return outer, inner


def build_lid():
    """Lid as a manifold mesh: lofted shell, then features (all booleans in manifold3d)."""
    outer, inner = lid_solids()
    O, In = b3d_to_manifold(outer), b3d_to_manifold(inner)
    cuts, adds = [], []
    for (sx, zc, hl) in SNAPS:
        w_i = inner_at(zc)[0] - TRAY_GAP
        cuts.append(cyl_z(sx * w_i, SNAP_Y, zc - hl + 0.4, zc + hl - 0.4, 0.95))
    xa, xb = W_MAIN - T_WALL - 1, W_MAIN + 1
    C = CAM_SLOT     # camera cable slot in the left wall (a 6 mm bridge in the print)
    cuts.append(box(-xb, -xa, C["y0"], C["y0"] + C["h"], C["zc"] - C["w"] / 2, C["zc"] + C["w"] / 2))
    adds.append(top_frame())      # the vents are in the top insert
    # speaker: vertical grille slots in the front end, two ribs in front of the body (0.4 gap)
    zf_ = SPK_ZE - SPK["ear_t"] - SPK["h"]
    for xs in np.arange(-8.5, 8.6, 3.4):
        cuts.append(box(xs - 0.6, xs + 0.6, SPK_Y0 + 6.0, SPK_Y0 + SPK["d"] - 5.0, ZF - 1, zf_ - 0.4))
    for xr in (-11.0, 11.0):     # up to the lid top: no free end that hangs in the print
        adds.append(box(xr - 0.8, xr + 0.8, SPK_Y0 + 4.0, H_MAIN, ZF - 1, zf_ - 0.4))
    # mic: stub over the board, diamond sound holes in the left wall (no overhang in the print)
    adds.append(mic_place(mic_stub()))
    yc = (MIC["y0"] + MIC["y1"]) / 2
    zw = MIC_X + (W_MAIN - T_WALL / 2)       # the left wall in the local mic frame
    for du, dv in [(0, 0)] + [(2.2 * math.cos(math.radians(a)), 2.2 * math.sin(math.radians(a))) for a in range(0, 360, 60)]:
        cuts.append(mic_place(Pos(MIC["xc"] + du, yc + dv, zw) * Rot(0, 0, 45) * Box(0.9, 0.9, T_WALL + 2)))
    # hold-down stubs over the Pi mounting screws
    for (x, z) in PI_HOLES:
        adds.append(cyl_y(x, z, PI_PCB_TOP + SCREW_HEAD + HOLD_GAP, H_MAIN, 1.6))
    lid = O - In
    for c in cuts:
        lid = lid - b3d_to_manifold(c)
    add = None
    for a_ in adds:
        m = b3d_to_manifold(a_)
        add = m if add is None else add + m
    lid = lid + (add ^ O)
    # port bays: cut the bay space, add a wall around it, open the wall at the port edge (below BAY_TOP)
    P, Pg = b3d_to_manifold(bay_solid()), b3d_to_manifold(bay_solid(T_WALL))
    wall = Pg - P
    for z0, z1 in BAYS:
        wall = wall - b3d_to_manifold(box(BAY_X - 3, BAY_X + 0.01, BAY_Y - 4, BAY_TOP, z0, z1))
    wall = wall - b3d_to_manifold(box(SLOT["x0"] - 0.45, SLOT["x1"] + 0.45, 0, PI.PLUG_TOP + 0.4, SLOT["z0"] - 0.4, HDR["z1"] + 0.4))
    lid = (lid - P) + (wall ^ O)
    return lid - b3d_to_manifold(top_window())


# --------------------------------------------------------------------------
# Assembly, checks, export
# --------------------------------------------------------------------------
def real_models():
    pisugar = stl_manifold("pisugar2Board.STL", ps2_to_body())
    pizero = stl_manifold("RaspberryPiZeroW-1.STL", pi_to_body())
    zb0 = Z_SD - 4.5 - BAT_L
    bat = b3d_to_manifold(box(STACK_GPIO_X + 0.5, STACK_GPIO_X + 0.5 + BAT_W,
                              U_BAT_BOT + DY, U_BAT_TOP + DY, zb0, zb0 + BAT_L))
    # NS4168 board: PCB + connectors (NULLLAB drawing and photo), in the local amp frame
    yb, xf = AMP_Y0, AMP["x0"]
    za, zb = AMP["z0"], AMP["z1"]
    amp = box(AMP["x0"], AMP["x1"], yb, yb + AMP["h"], za, zb)
    amp -= cyl_x(yb + 3.2, AMP_HOLE_Z, AMP["x0"] - 1, AMP["x1"] + 1, 2.35)
    amp -= cyl_x(yb + AMP["h"] - 3.2, AMP_HOLE_Z, AMP["x0"] - 1, AMP["x1"] + 1, 2.35)
    amp += box(xf - 6.0, xf, yb + 2.0, yb + 20.0, zb - 6.0, zb)                    # 5-pin PH2.0
    amp += box(xf - AMP["comp"], xf, yb + 12.5, yb + AMP["h"], za, za + 7.5)        # screw terminal
    amp += box(xf - 6.0, xf, yb + 3.0, yb + 11.5, za, za + 6.0)                     # 2-pin PH2.0
    amp += box(xf - 1.8, xf, yb + 7.0, yb + 13.0, za + 13.0, za + 19.0)             # IC
    amp = amp_place(amp)
    mic = box(MIC["x0"], MIC["x1"], MIC["y0"], MIC["y1"], MIC["z0"], MIC["z1"])
    mic += box(MIC["xc"] - 2.0, MIC["xc"] + 2.0, MIC["y0"] + 6.0, MIC["y0"] + 10.0, MIC["z0"] - 1.2, MIC["z0"])   # parts on the back face
    mic = mic_place(mic)
    # speaker on edge: ear plate in the XY plane at the rear, body in front of it
    z0 = SPK_ZE - SPK["ear_t"]
    yc = SPK_Y0 + SPK["d"] / 2
    spk = box(-SPK["l"] / 2, SPK["l"] / 2, SPK_Y0, SPK_Y0 + SPK["d"], z0, SPK_ZE)
    for xh in SPK["holes_x"]:
        spk -= cyl_z(xh, yc, z0 - 1, SPK_ZE + 1, SPK["hole_d"] / 2)
    spk += box(-SPK["body_l"] / 2, SPK["body_l"] / 2, SPK_Y0 + 0.5, SPK_Y0 + SPK["d"] - 0.5, z0 - SPK["h"], z0)
    cov = load_stl(os.path.join(PREF, "Bittle_Cover.stl")).reshape(-1, 3)
    m = (cov[:, 0] > HDR["x0"]) & (cov[:, 0] < HDR["x1"]) & (cov[:, 2] > HDR["z0"]) & (cov[:, 2] < HDR["z1"])
    hdr = b3d_to_manifold(box(HDR["x0"], HDR["x1"], float(cov[m, 1].min()) - 3.0, HDR["top"], HDR["z0"], HDR["z1"]))
    plugs = b3d_to_manifold(box(HDR["x0"], HDR["x1"], HDR["top"], PLUG_TOP, HDR["z0"], HDR["z1"]))
    C = CAM_SLOT     # cable through the slot, over the tray rim
    cam = box(-(W_MAIN + 3), -20.0, C["y0"] + 0.4, C["y0"] + 1.7, C["zc"] - 2.6, C["zc"] + 2.6)
    return dict(pisugar2=pisugar, pizero=pizero, battery=bat, biboard_header=hdr, dupont_plugs=plugs,
                camera_cable=b3d_to_manifold(cam),
                speaker=b3d_to_manifold(spk), mic_sph0645=b3d_to_manifold(mic),
                amp_ns4168=b3d_to_manifold(amp))


def solid_cover_tris():
    """Stock cover without the Pi slot: its top surface has no hole."""
    return load_stl(os.path.join(PREF, "Bittle_Cover.stl"))


def under_cover():
    """Volume under the cover top surface (robot side). Printed parts stay out."""
    return heightfield_solid(solid_cover_tris(), -W_HAUNCH - 3, W_HAUNCH + 3, ZF - 2, ZR + 2, lift=0.0)


def shoulder_tris():
    t = load_stl(os.path.join(PREF, "Bittle_SideShoulder.stl"))
    m = t.copy()
    m[:, :, 0] *= -1
    return np.concatenate([t, m[:, ::-1, :]])


def slot_passage(lid_inner):
    """Free space over the cover slot, up to the tray top, inside the lid. Wires use it."""
    S = SLOT
    cover = mesh_to_manifold(load_stl(os.path.join(PREF, COVER_STL)))
    hdr = b3d_to_manifold(box(HDR["x0"], HDR["x1"], 0.0, HDR["top"], HDR["z0"], HDR["z1"]))
    return (b3d_to_manifold(box(S["x0"], S["x1"], S["y0"], HDR["top"], S["z0"], S["z1"])) ^ lid_inner) - cover - hdr


def build_all():
    cover_tris = load_stl(os.path.join(PREF, COVER_STL))
    cover = mesh_to_manifold(cover_tris)
    cover_pegs = cover + b3d_to_manifold(build_pegs())
    support = np.concatenate([solid_cover_tris(), shoulder_tris(),
                              load_stl(os.path.join(PREF, "Bittle_FrontPlate.stl"))])
    box_ = lambda *a: b3d_to_manifold(box(*a))
    clearance = heightfield_solid(support, -W_HAUNCH - 3, W_HAUNCH + 3, ZF - 2, ZR + 2, lift=HUG_GAP)
    clearance += box_(-27.6, 27.6, 0.0, LID_MIN_Y, COVER_END_Z - 0.5, ZR + 5)
    lid = build_lid() - clearance
    tray = b3d_to_manifold(build_tray())
    return dict(cover_pegs=cover_pegs, pod_tray=tray, pod_lid=lid, top_insert=b3d_to_manifold(build_top_insert()))


def robot_parts():
    sh = stl_manifold("Bittle_SideShoulder.stl", ref=PREF)
    mirror = np.diag([-1.0, 1, 1, 1])
    fp = stl_manifold("Bittle_FrontPlate.stl", ref=PREF)
    rear = np.diag([1.0, 1, -1, 1])
    return dict(shoulder_r=sh, shoulder_l=sh.transform(mirror[:3, :]), front_plate=fp,
                rear_plate_mirror=fp.transform(rear[:3, :]))


def check(parts, models, robot):
    rows = []
    def vol(a, b):
        return (a ^ b).volume()
    printed = dict(parts)
    names = list(printed)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            rows.append((a, b, vol(printed[a], printed[b])))
    for a in names:
        for b, M in models.items():
            rows.append((a, b, vol(printed[a], M)))
    U = under_cover()
    ADD = ("pod_tray", "pod_lid", "top_insert")
    for a in ADD:
        rows.append((a, "under_cover", vol(printed[a], U)))
    for a in ADD:
        for b, M in robot.items():
            rows.append((a, b, vol(printed[a], M)))
    # every printed part must be one piece
    for a in names:
        pcs = sorted(c.volume() for c in printed[a].decompose())
        rows.append((a, "loose_pieces", sum(pcs[:-1])))
    # slide path: tray at the drop-on position and at the detent bump
    for s_ in (SLIDE, DET["bump_dz"]):
        T = printed["pod_tray"].translate([0, 0, -s_])
        rows.append((f"tray fwd {s_:g}mm", "cover_pegs", vol(T, printed["cover_pegs"])))
        rows.append((f"tray fwd {s_:g}mm", "cover_slot", vol(T, models["cover_slot"])))
        rows.append((f"tray fwd {s_:g}mm", "biboard_header", vol(T, models["biboard_header"])))
        rows.append((f"tray fwd {s_:g}mm", "under_cover", vol(T, U)))
        for rn in ("shoulder_r", "shoulder_l"):
            rows.append((f"tray fwd {s_:g}mm", rn, vol(T, robot[rn])))
    # port access: a plug body from each port face straight out to the side
    for n, (yc, zc, w, h) in PORT_PLUGS.items():
        B = b3d_to_manifold(box(15.3, 45.0, yc - h / 2, yc + h / 2, zc - w / 2, zc + w / 2))
        for b in ("pod_lid", "pod_tray"):
            rows.append((f"plug {n}", b, vol(B, printed[b])))
    mn = list(models)
    for i, a in enumerate(mn):
        for b in mn[i + 1:]:
            rows.append((a, b, vol(models[a], models[b])))
    return rows


# Typical masses (g) of the electronics. They are not weighed: put your own values here.
MASS_G = dict(pizero=11.0, pisugar2=8.0, battery=23.0, speaker=20.0, amp_ns4168=4.0,
              mic_sph0645=1.0, dupont_plugs=3.0)
PLA_G_MM3 = 1.24e-3


def centroid(M):
    """Volume centroid of a manifold."""
    m = M.to_mesh()
    v = np.asarray(m.vert_properties)[:, :3][np.asarray(m.tri_verts)]
    w = np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2]))
    return (v.sum(1) / 4 * w[:, None]).sum(0) / w.sum()


def balance(parts, models):
    """Mass and center of mass of the add-on (printed parts + electronics), robot frame.
    The robot center is X 0, Z 0: the cover and the shoulder plates are symmetric about it."""
    rows = []
    for n in ("pod_tray", "pod_lid", "top_insert"):
        rows.append((n, parts[n].volume() * PLA_G_MM3, centroid(parts[n])))
    for n, g in MASS_G.items():
        rows.append((n, g, centroid(models[n])))
    m = sum(r[1] for r in rows)
    c = sum(r[1] * r[2] for r in rows) / m
    return dict(mass_g=round(m, 1), com=[round(float(v), 1) for v in c],
                parts=[dict(name=n, g=round(g, 1), com=[round(float(v), 1) for v in p]) for n, g, p in rows])


def print_orient(name, M):
    """Rotate to the print orientation and put the part on the bed (Z=0)."""
    if name == "pod_tray":
        R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)        # Y up -> Z up
    elif name in ("pod_lid", "top_insert"):
        R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)        # upside down, top on bed
    elif name == "cover_pegs":
        # stand on the rear end, as Petoi prints the stock cover
        R = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float)
    else:
        raise ValueError(name)
    if abs(np.linalg.det(R) - 1) > 1e-6:
        raise ValueError(f"{name}: not a rotation")
    M = M.transform(np.hstack([R, np.zeros((3, 1))]))
    lo, hi = M.bounding_box()[:3], M.bounding_box()[3:]
    M = M.translate([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return M


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


def export_assembly(path):
    """One STEP file with the robot, the platform and the add-on in place: named, colored parts.
    Exact B-rep for the pegs, the tray and the plug; simplified meshes for the rest
    (0.05 mm for the add-on, 0.15 mm for the robot, the cover and the boards)."""
    from build123d import Compound, Color, export_step
    from bittle_platform import build as BP
    mirror_x, mirror_z = np.diag([-1.0, 1, 1, 1])[:3, :], np.diag([1.0, 1, -1, 1])[:3, :]
    meshes = dict(
        shoulder_right=(stl_manifold("Bittle_SideShoulder.stl", ref=PREF), "#f2a71c"),
        shoulder_left=(stl_manifold("Bittle_SideShoulder.stl", ref=PREF).transform(mirror_x), "#f2a71c"),
        front_plate=(stl_manifold("Bittle_FrontPlate.stl", ref=PREF), "#26272b"),
        rear_plate_mirror=(stl_manifold("Bittle_FrontPlate.stl", ref=PREF).transform(mirror_z), "#26272b"),
        cover=(stl_manifold(COVER_STL, ref=PREF), "#26272b"),
        pod_lid=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_lid.stl"))), "#f9bd1a"),
    )
    for n, col in (("pizero", "#2a8c47"), ("pisugar2", "#c4588c"), ("battery", "#3a5fa8"), ("amp_ns4168", "#1a5a8c"),
                   ("speaker", "#7a52b8"), ("mic_sph0645", "#d83a34"), ("biboard_header", "#0d0d0d"), ("dupont_plugs", "#d83a34"),
                   ("camera_cable", "#3a9a3a")):
        meshes[n] = (mesh_to_manifold(load_stl(os.path.join(OUT, "models", f"{n}.stl"))), col)
    kids = []
    coarse = ("shoulder_right", "shoulder_left", "front_plate", "rear_plate_mirror", "cover", "pizero", "pisugar2")
    for n, (M, col) in meshes.items():
        S = mesh_solid(M, 0.15 if n in coarse else 0.05)
        S.label, S.color = n, Color(col)
        kids.append(S)
    for n, shape, col in (("pegs", BP.pegs(), "#26272b"), ("pod_tray", build_tray(), "#cccccf"), ("top_insert", build_top_insert(), "#e8641b")):
        shape.label, shape.color = n, Color(col)
        kids.append(shape)
    A = Compound(label="bittle_pi_addon_assembly", children=kids)
    export_step(A, path)
    import zipfile
    zp = os.path.join(os.path.dirname(path), "assembly_step.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(path, os.path.basename(path))
    print(f"assembly: {path} ({os.path.getsize(path) / 1e6:.1f} MB, {len(kids)} parts), zip {os.path.getsize(zp) / 1e6:.1f} MB")


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = build_all()
    models = real_models()
    models["cover_slot"] = slot_passage(b3d_to_manifold(lid_solids()[1]))
    robot = robot_parts()
    for d in ("print", "installed", "models"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    from bittle_platform import build as BP
    printing = {}
    for n, M in parts.items():
        save_stl(M, os.path.join(OUT, "installed", f"{n}.stl"))
        if n == "cover_pegs":
            continue            # a platform part: bittle_platform/stl/print/cover_pegs.stl
        P = print_orient(n, M)
        save_stl(P, os.path.join(OUT, "print", f"{n}.stl"))
        regs = BP.overhang_regions(P)
        printing[n] = dict(overhang_mm2=round(sum(r["area"] for r in regs), 1), regions=regs[:6])
        print(f"{n:11s} vol {M.volume():8.0f} mm3  ~{M.volume() * 1.24e-3:5.1f} g PLA (solid)   overhang {printing[n]['overhang_mm2']:6.1f} mm2")
        for r in regs[:4]:
            print(f"     {r['area']:6.1f} mm2  flat {r['flat']:5.1f}  at print z {r['z'][0]:.1f}..{r['z'][1]:.1f}  x {r['x'][0]:.1f}..{r['x'][1]:.1f}  y {r['y'][0]:.1f}..{r['y'][1]:.1f}")
    for n, M in models.items():
        save_stl(M, os.path.join(OUT, "models", f"{n}.stl"))
    rows = check(parts, models, robot)
    bal = balance(parts, models)
    print(f"balance: {bal['mass_g']} g, center of mass x {bal['com'][0]} y {bal['com'][1]} z {bal['com'][2]}")
    i = parts["pod_tray"] ^ parts["pod_lid"]
    for c in i.decompose():
        if c.volume() > 0.05:
            print("  tray^lid piece", round(c.volume(), 2), np.round(c.bounding_box(), 1))
    print("interference (mm^3, >0.05 shown):")
    for a, b, v in rows:
        if v > 0.05:
            print(f"  {a:12s} x {b:16s} {v:9.2f}")
    import json
    json.dump(dict(rows=rows, printing=printing, balance=bal), open(os.path.join(OUT, "checks.json"), "w"), indent=1)
    # exact CAD of the parts that are pure B-rep (the lid is cut by the robot mesh: STL only)
    from build123d import export_step
    os.makedirs(os.path.join(ROOT, "cad"), exist_ok=True)
    export_step(build_tray(), os.path.join(ROOT, "cad", "pod_tray.step"))
    export_step(build_top_insert(), os.path.join(ROOT, "cad", "top_insert.step"))
    export_assembly(os.path.join(ROOT, "cad", "assembly.step"))


if __name__ == "__main__":
    main()
