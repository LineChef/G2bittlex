"""Bittle X Pi add-on rev 0.7 (was the Pi pod): stock cover + pegs, pod tray, pod lid, plug.

Frame = Petoi reference STL frame (reference/*.stl):
  X = lateral (+X = robot right), Y = up, Z = length (-Z = head end). mm.

Parts
  cover_pegs : the platform (bittle_platform/): Petoi cover, unchanged, plus 4 pegs.
               Each peg root ends inside the 1.6 mm cover wall, so the inside
               of the cover (BiBoard space, touch FPC) does not change.
  pod_tray   : tray. Keyholes drop over the pegs 7 mm forward of the locked place, slide rearward, click
               (cantilever detents). A notch over the cover slot lets the BiBoard wires in.
               Holds the Pi Zero 2 W + PiSugar 2 stack (over the BiBoard header, between the
               PiSugar button and switch), the NS4168 amp, the SPH0645 mic (front left, port
               forward) and the 3 W speaker (on two pins on a wall at the rear end).
  pod_lid    : lofted shell: low front, rising spine, haunches over the hips, chamfered rump,
               low side skirt over the cover slot. It snaps onto the tray rim. Its lower edge
               follows the cover and the hip plates (0.4 mm gap).
Print: every part prints without supports (see check(): overhang rows).
  usb_plug   : optional TPU plug for the micro-USB charge window.

The camera (Petoi AI Vision Module) stays in the head, as Petoi designs it.
"""
import math
import os
import sys

import numpy as np
import manifold3d as m3
from build123d import (
    Axis, Box, Cylinder, Face, Pos, Rot, Wire, Sphere, Cone, extrude, fillet, loft,
    export_stl, Plane, Spline, offset,
)

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))            # the folder that holds bittle_platform/
from bittle_platform import interface as PI          # platform v1.0: cover, pegs, keyholes
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
ZF, ZR = -21.2, 76.5        # front and rear (the speaker is behind the stack)
T_WALL = 1.6
W_FRONT, W_MAIN = 26.4, 26.4    # upper half widths: front, spine
W_HAUNCH = 33.6                 # half width at the bottom over the hip plates
HAUNCH_Z = (34.0, 40.0, 47.0, 53.0)   # ramp in, full, full, ramp out
W_SKIRT = 32.4                  # half width at the bottom over the cover slot (slot to |x| 30.03)
SKIRT_Z = (-4.0, 8.0)           # ramp in; the skirt joins the haunch
# The lid prints upside down on its flat top. Every overhang is 45 deg or less:
# flat top over the full length, 45 deg chamfers on the top edges, nose and rump,
# straight bottom flare (about 39 deg at the haunches).
H_MAIN = 54.6               # 2 mm over rev 0.3: the plug wires cross over the Pi
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
SNAPS = [(-1, -6.0), (-1, 30.0), (1, -6.0), (1, 40.0)]   # (side, z) rim bumps; right rim is cut over the cover slot
# Pegs (on the cover) and keyholes (in the tray): platform interface v1.0
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
SPK_PIN_D = SPK["hole_d"] - 0.5
# Speaker in the rump: on edge, ear plate to the front, sound face to the rear. The ear plate
# hangs on two pins on a wall at the rear end of the tray. Lid ribs behind the body hold it on.
TRAY_Z1 = 54.0                              # rear end of the tray floor
SPK_ZE = 56.0                               # front face of the ear plate = rear face of the wall
SPK_Y0 = 20.5                               # bottom of the ear plate (below the tray floor, behind the tray)
SPK_WALL = dict(x=21.0, y1=40.0)            # wall: |X| <= 21, Y from the tray bottom to 40

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
STACK_GPIO_X = (W_MAIN - T_WALL) - 0.4 - 1.25 - 30.0
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
USB_W, USB_H = 11.5, 7.5
SW_W, SW_H = 7.5, 3.0

# NS4168 amp board on edge, left of the stack (plane normal = X). PCB x0..x1,
# components on the -X face (x0 side). 5-pin connector edge at the rear.
AMP = dict(t=1.6, l=38.4, h=22.4, comp=10.0, z0=-1.7)   # post behind the rear keyholes
AMP_Y0 = 29.3                             # amp bottom edge: over the peg heads (top 28.9)
AMP["x1"] = STACK_GPIO_X - 0.95
AMP["x0"] = AMP["x1"] - AMP["t"]
AMP["z1"] = AMP["z0"] + AMP["l"]
AMP_HOLE_Z = AMP["z1"] - 15.2
# SPH0645 mic board (Adafruit 3421 size) at the front left, on edge, port face forward (-Z).
# It stands in a slot in a base on the tray floor; a stub on the lid holds its top edge.
# The base stays 0.6 clear of the left-front detent beam (X >= -9.8).
MIC = dict(l=16.7, w=12.7, t=1.8, xc=-17.9, z0=-16.6, y0=31.3, slot=3.0, clr=0.15)
MIC["x0"], MIC["x1"] = MIC["xc"] - MIC["w"] / 2, MIC["xc"] + MIC["w"] / 2
MIC["z1"] = MIC["z0"] + MIC["t"]
MIC["y1"] = MIC["y0"] + MIC["l"]

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


def tray_outline(y, extra=0.0, zmax=None):
    """Plan face at height y: lid inner wall at the rim height, minus TRAY_GAP + extra."""
    zs = np.linspace(ZF, ZR, 400)
    valid = [z for z in zs if inner_at(z)[0] > 3.0 + TRAY_GAP and inner_at(z)[2] > RIM_TOP + 3]
    zmax = TRAY_Z1 if zmax is None else zmax
    za, zb = valid[0] + TRAY_GAP + extra, min(valid[-1] - TRAY_GAP, zmax) - extra
    pts = []
    for z in np.linspace(za, zb, 400):
        w = min(inner_at(min(max(z + dz, valid[0]), valid[-1]))[0] for dz in np.linspace(-1.6, 1.6, 9))   # steep blister ends
        pts.append((z, w - TRAY_GAP - extra))
    right = [(w, y, z) for z, w in pts]
    left = [(-w, y, z) for z, w in reversed(pts)]
    return Face(Wire.make_polygon(right + left, close=True))


def plan_prism(y0, y1, extra=0.0, zmax=None):
    return extrude(tray_outline(y0, extra, zmax), amount=y1 - y0, dir=(0, 1, 0))


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


def build_tray():
    t = plan_prism(FLOOR_Y0, FLOOR_Y1)
    rim = plan_prism(FLOOR_Y1, RIM_TOP) - plan_prism(FLOOR_Y1 - 1, RIM_TOP + 1, RIM_T)
    t += rim
    for (sx, zc) in SNAPS:
        w_i = inner_at(zc)[0] - TRAY_GAP
        t += cyl_z(sx * w_i, 29.5, zc - 4, zc + 4, 0.8)
    # cell rails (clear of the peg heads and slide paths)
    zb0, zb1 = Z_SD - 4.5 - BAT_L, Z_SD - 4.5
    for xc in (STACK_GPIO_X + 27.35, STACK_GPIO_X + 10.35):
        t += box(xc - 1.0, xc + 1.0, FLOOR_Y1, RAIL_TOP, zb0 + 1, zb1 - 1)
    # corner locators (L shapes) around the PiSugar 2 PCB outline
    c = 0.3
    loc_top = U_PS2_PCB[1] + DY + 0.8
    x0, x1 = STACK_GPIO_X - c, STACK_GPIO_X + 30.0 + c
    z0, z1 = Z_CSI - c, Z_SD + c
    for xe, sx in ((x0, -1), (x1, 1)):
        for ze, sz in ((z0, -1), (z1, 1)):
            if sx > 0 and sz < 0:   # front port corner: over the cover slot notch
                continue
            t += box(*sorted((xe, xe - sx * 6.0)), FLOOR_Y1, loc_top, *sorted((ze, ze + sz * 1.0)))
            if sx < 0 and sz < 0:   # front GPIO corner: the amp is next to it
                continue
            t += box(*sorted((xe, xe + sx * 1.2)), FLOOR_Y1, loc_top, *sorted((ze, ze - sz * 6.0)))
            t += box(*sorted((xe, xe - sx * 0.25)), FLOOR_Y1 + 3, loc_top, *sorted((ze - sz * 3.0, ze - sz * 4.0)))
    t += amp_post()
    t += mic_base()
    # keyholes with a cantilever click detent
    for (px, pz) in PEGS:
        t -= keyhole_cut(px, pz)
        t += keyhole_bump(px, pz)
    # notch over the cover slot (floor and rim, open to the side), includes the slide travel
    t -= box(SLOT["x0"] - 0.3, 40.0, FLOOR_Y0 - 1, RIM_TOP + 1, SLOT["z0"] - 0.6, SLOT["z1"] + SLIDE + 0.6)
    t &= plan_prism(FLOOR_Y0 - 1, H_MAIN)   # nothing outside the lid's inner wall
    t += speaker_wall() & plan_prism(FLOOR_Y0 - 1, H_MAIN, zmax=ZR)
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
    """Wall at the rear end of the tray with two pins through the speaker ear holes."""
    W = SPK_WALL
    w = box(-W["x"], W["x"], FLOOR_Y0, W["y1"], TRAY_Z1 - 0.01, SPK_ZE)
    yc = SPK_Y0 + SPK["d"] / 2
    r = SPK_PIN_D / 2
    for xh in SPK["holes_x"]:
        w += teardrop_z(xh, yc, SPK_ZE - 0.01, SPK_ZE + SPK["ear_t"] + 0.6, r, SPK["hole_d"] / 2 - 0.1)
        w += Pos(xh, yc, SPK_ZE + SPK["ear_t"] + 0.9) * Cone(r, r - 0.3, 0.6)    # lead-in
    return w


def amp_post():
    """Post on the component side of the amp board; two pins in its 4.7 mm holes."""
    xf = AMP["x0"]
    yb = AMP_Y0
    p = box(xf - 3.5, xf, FLOOR_Y1, yb + AMP["h"] - 1.0, AMP_HOLE_Z - 2.3, AMP_HOLE_Z + 2.3)
    for dy in (3.2, AMP["h"] - 3.2):
        p += teardrop_x(yb + dy, AMP_HOLE_Z, xf - 0.1, AMP["x1"] - 0.3, 2.25, 2.0)   # flat inside the 4.7 hole
        for k in range(3):   # crush ribs for a friction fit
            a = math.radians(90 + 120 * k)
            p += cyl_x(yb + dy + 2.25 * math.sin(a), AMP_HOLE_Z + 2.25 * math.cos(a), xf, AMP["x1"] - 0.3, 0.25)
    return p


def mic_base():
    """Base on the tray floor with a slot for the bottom edge of the mic board. The slot is open
    at the left end (over the rim) and closed at the right end (0.6 clear of the detent beam)."""
    M, c = MIC, MIC["clr"]
    b = box(-(W_MAIN - T_WALL - TRAY_GAP), -10.4, FLOOR_Y1 - 0.01, M["y0"] + M["slot"], M["z0"] - 1.2, M["z1"] + 1.2)
    b -= box(M["x0"] - 2.0, M["x1"] + c, M["y0"], M["y0"] + M["slot"] + 1, M["z0"] - c, M["z1"] + c)
    return b


def mic_stub():
    """Stub on the lid top with a slot for the top edge of the mic board (prints from the bed)."""
    M, c = MIC, MIC["clr"]
    s = box(M["xc"] - 3.0, M["xc"] + 3.0, M["y1"] - 2.0, H_MAIN, M["z0"] - 1.2, M["z1"] + 1.2)
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
    for (sx, zc) in SNAPS:
        w_i = inner_at(zc)[0] - TRAY_GAP
        cuts.append(cyl_z(sx * w_i, 29.5, zc - 4.6, zc + 4.6, 0.95))
    xa, xb = W_MAIN - T_WALL - 1, W_MAIN + 1
    cuts.append(stadium_x(CHG_Y, CHG_Z, xa, xb, USB_W, USB_H))
    cuts.append(stadium_x(SW_Y, SW_Z, xa, xb, SW_W, SW_H))
    # PiSugar 2 tap button flexure, hinge at the top
    z0, z1 = BTN_Z - 3.0, BTN_Z + 3.0
    yb, yt = BTN_Y - 3.0, BTN_Y + 4.0
    cuts.append(box(xa, xb, yb - 0.5, yt, z0 - 0.5, z0))
    cuts.append(box(xa, xb, yb - 0.5, yt, z1, z1 + 0.5))
    cuts.append(box(xa, xb, yb - 0.5, yb, z0 - 0.5, z1 + 0.5))
    adds.append(box(PORT_FACE_X + 0.3, W_MAIN - T_WALL + 0.3, BTN_Y - 1.5, BTN_Y + 1.5, BTN_Z - 1.5, BTN_Z + 1.5))
    # vent: lateral slots in the top over the Pi (Pi SoC near the stack center)
    bz0, bz1 = Z_CSI + 18.0, Z_CSI + 48.0
    n = int((bz1 - bz0 - 6.0) // 3.4) + 1
    for i in range(n):
        zc = bz0 + 3.0 + i * 3.4
        cuts.append(box(-11.0, 11.0, 38.0, 60.0, zc - 0.7, zc + 0.7))
    # speaker: vertical grille slots in the rear end, two ribs behind the body (0.4 gap)
    zb_ = SPK_ZE + SPK["ear_t"] + SPK["h"]
    for xs in np.arange(-8.5, 8.6, 3.4):
        cuts.append(box(xs - 0.6, xs + 0.6, SPK_Y0 + 6.0, SPK_Y0 + SPK["d"] - 5.0, zb_ + 0.4, ZR + 1))
    for xr in (-11.0, 11.0):     # up to the lid top: no free end that hangs in the print
        adds.append(box(xr - 0.8, xr + 0.8, SPK_Y0 + 4.0, H_MAIN, zb_ + 0.4, ZR + 1))
    # mic: stub over the board, diamond sound holes in the front wall (no overhang in the print)
    adds.append(mic_stub())
    yc = (MIC["y0"] + MIC["y1"]) / 2
    for du, dv in [(0, 0)] + [(2.2 * math.cos(math.radians(a)), 2.2 * math.sin(math.radians(a))) for a in range(0, 360, 60)]:
        cuts.append(Pos(MIC["xc"] + du, yc + dv, ZF + T_WALL / 2) * Rot(0, 0, 45) * Box(0.9, 0.9, T_WALL + 3))
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
    return lid


def build_plug():
    clr = 0.1
    w, h = USB_W - 2 * clr, USB_H - 2 * clr
    xw = W_MAIN
    body = stadium_x(CHG_Y, CHG_Z, xw - T_WALL - 0.4, xw + 0.45, w, h)
    flange = stadium_x(CHG_Y, CHG_Z, xw + 0.25, xw + 1.05, w + 2.4, h + 2.4)
    tab = box(xw + 0.25, xw + 1.05, CHG_Y - 1.2, CHG_Y + 1.2, CHG_Z - w / 2 - 6.0, CHG_Z - w / 2 - 1.0)
    return body + flange + tab


# --------------------------------------------------------------------------
# Assembly, checks, export
# --------------------------------------------------------------------------
def real_models():
    pisugar = stl_manifold("pisugar2Board.STL", ps2_to_body())
    pizero = stl_manifold("RaspberryPiZeroW-1.STL", pi_to_body())
    zb0 = Z_SD - 4.5 - BAT_L
    bat = b3d_to_manifold(box(STACK_GPIO_X + 0.5, STACK_GPIO_X + 0.5 + BAT_W,
                              U_BAT_BOT + DY, U_BAT_TOP + DY, zb0, zb0 + BAT_L))
    # NS4168 board: PCB + connectors on the +X face (NULLLAB drawing and photo)
    # turned 180 deg about the vertical axis: components on -X, 5-pin connector at the rear
    yb, xf = AMP_Y0, AMP["x0"]
    za, zb = AMP["z0"], AMP["z1"]
    amp = box(AMP["x0"], AMP["x1"], yb, yb + AMP["h"], za, zb)
    amp -= cyl_x(yb + 3.2, AMP_HOLE_Z, AMP["x0"] - 1, AMP["x1"] + 1, 2.35)
    amp -= cyl_x(yb + AMP["h"] - 3.2, AMP_HOLE_Z, AMP["x0"] - 1, AMP["x1"] + 1, 2.35)
    amp += box(xf - 6.0, xf, yb + 2.0, yb + 20.0, zb - 6.0, zb)                    # 5-pin PH2.0
    amp += box(xf - AMP["comp"], xf, yb + 12.5, yb + AMP["h"], za, za + 7.5)        # screw terminal
    amp += box(xf - 6.0, xf, yb + 3.0, yb + 11.5, za, za + 6.0)                     # 2-pin PH2.0
    amp += box(xf - 1.8, xf, yb + 7.0, yb + 13.0, za + 13.0, za + 19.0)             # IC
    mic = box(MIC["x0"], MIC["x1"], MIC["y0"], MIC["y1"], MIC["z0"], MIC["z1"])
    mic += box(MIC["xc"] - 2.0, MIC["xc"] + 2.0, MIC["y0"] + 6.0, MIC["y0"] + 10.0, MIC["z1"], MIC["z1"] + 1.2)   # parts on the back
    # speaker on edge: ear plate in the XY plane at the front, body behind it
    z1 = SPK_ZE + SPK["ear_t"]
    yc = SPK_Y0 + SPK["d"] / 2
    spk = box(-SPK["l"] / 2, SPK["l"] / 2, SPK_Y0, SPK_Y0 + SPK["d"], SPK_ZE, z1)
    for xh in SPK["holes_x"]:
        spk -= cyl_z(xh, yc, SPK_ZE - 1, z1 + 1, SPK["hole_d"] / 2)
    spk += box(-SPK["body_l"] / 2, SPK["body_l"] / 2, SPK_Y0 + 0.5, SPK_Y0 + SPK["d"] - 0.5, z1, z1 + SPK["h"])
    cov = load_stl(os.path.join(PREF, "Bittle_Cover.stl")).reshape(-1, 3)
    m = (cov[:, 0] > HDR["x0"]) & (cov[:, 0] < HDR["x1"]) & (cov[:, 2] > HDR["z0"]) & (cov[:, 2] < HDR["z1"])
    hdr = b3d_to_manifold(box(HDR["x0"], HDR["x1"], float(cov[m, 1].min()) - 3.0, HDR["top"], HDR["z0"], HDR["z1"]))
    plugs = b3d_to_manifold(box(HDR["x0"], HDR["x1"], HDR["top"], PLUG_TOP, HDR["z0"], HDR["z1"]))
    return dict(pisugar2=pisugar, pizero=pizero, battery=bat, biboard_header=hdr, dupont_plugs=plugs,
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
    support = np.concatenate([solid_cover_tris(), shoulder_tris()])
    box_ = lambda *a: b3d_to_manifold(box(*a))
    clearance = heightfield_solid(support, -W_HAUNCH - 3, W_HAUNCH + 3, ZF - 2, ZR + 2, lift=HUG_GAP)
    clearance += box_(-27.6, 27.6, 0.0, LID_MIN_Y, COVER_END_Z - 0.5, ZR + 5)
    lid = build_lid() - clearance
    tray = b3d_to_manifold(build_tray())
    plug = b3d_to_manifold(build_plug())
    return dict(cover_pegs=cover_pegs, pod_tray=tray, pod_lid=lid, usb_plug=plug)


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
    for a in ("pod_tray", "pod_lid", "usb_plug"):
        rows.append((a, "under_cover", vol(printed[a], U)))
    for a in ("pod_tray", "pod_lid", "usb_plug"):
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
    mn = list(models)
    for i, a in enumerate(mn):
        for b in mn[i + 1:]:
            rows.append((a, b, vol(models[a], models[b])))
    return rows


def print_orient(name, M):
    """Rotate to the print orientation and put the part on the bed (Z=0)."""
    if name == "pod_tray":
        R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)        # Y up -> Z up
    elif name == "pod_lid":
        R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)        # upside down, top on bed
    elif name == "cover_pegs":
        # stand on the rear end, as Petoi prints the stock cover
        R = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float)
    else:   # usb_plug: flange (+X side) on the bed
        R = np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]], float)
    if abs(np.linalg.det(R) - 1) > 1e-6:
        raise ValueError(f"{name}: not a rotation")
    M = M.transform(np.hstack([R, np.zeros((3, 1))]))
    lo, hi = M.bounding_box()[:3], M.bounding_box()[3:]
    M = M.translate([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return M


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
    i = parts["pod_tray"] ^ parts["pod_lid"]
    for c in i.decompose():
        if c.volume() > 0.05:
            print("  tray^lid piece", round(c.volume(), 2), np.round(c.bounding_box(), 1))
    print("interference (mm^3, >0.05 shown):")
    for a, b, v in rows:
        if v > 0.05:
            print(f"  {a:12s} x {b:16s} {v:9.2f}")
    import json
    json.dump(dict(rows=rows, printing=printing), open(os.path.join(OUT, "checks.json"), "w"), indent=1)
    # exact CAD of the parts that are pure B-rep (the lid is cut by the robot mesh: STL only)
    from build123d import export_step
    os.makedirs(os.path.join(ROOT, "cad"), exist_ok=True)
    export_step(build_tray(), os.path.join(ROOT, "cad", "pod_tray.step"))
    export_step(build_plug(), os.path.join(ROOT, "cad", "usb_plug.step"))


if __name__ == "__main__":
    main()
