"""Bittle X Pi add-on rev 0.16: one-piece body with a snap-in top panel.

Frame = Petoi reference STL frame (reference/*.stl):
  X = lateral (+X = robot right), Y = up, Z = length (-Z = head end). mm.

Parts
  cover_pegs : the platform (bittle_platform/): Petoi cover, unchanged, plus 4 pegs.
  pod_body   : a rounded box (squircle plan, vertical walls, flat floor). The floor is the platform
               mount plate: teardrop keyholes drop over the pegs 7 mm behind the locked place,
               slide forward, click. To remove it, slide it 7 mm rearward and lift it.
               The floor is flat: it does not follow the robot, so the cover and the pegs stay in view.
               Inside, every part goes in from the top: the mic (front wall), the Pi Zero 2 W +
               PiSugar 2 stack on its long edge (ports up, over the robot center), the speaker
               (rear, sound to the rear grille) and the NS4168 amp (left gallery).
               The BiBoard header comes up through a notch in the floor, in the right well.
  pod_panel  : the top, with the soft top edge and openings shaped to the plug bodies. Four spring tabs
               click into pockets in the front and rear walls. Forks under the panel hold the stack,
               the speaker and the amp down. A spring tongue over the PiSugar button is a large button.
  pod_switch : a large slider for the PiSugar power switch: a fork on the lever, a tab through the panel.
Order: fit the platform cover, click the empty body on, put the parts in, plug in the wires, put the
slider on the switch lever, click the panel on.
Print: the body and the slider print flat side down, the panel prints upside down on its top. No supports.

The camera (Petoi AI Vision Module) stays in the head, as Petoi designs it.
"""
import math
import os
import sys

import numpy as np
import manifold3d as m3
from build123d import Box, Cylinder, Pos, Rot, export_stl

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))            # the folder that holds bittle_platform/
from bittle_platform import interface as PI          # platform v3.0: cover, pegs, keyholes
REF = os.path.join(ROOT, "reference")                # vendor models (Pi Zero, PiSugar 2)
PREF = os.path.join(os.path.dirname(ROOT), "bittle_platform", "reference")   # Petoi robot parts
OUT = os.path.join(ROOT, "stl")

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------
COVER_STL = PI.COVER_STL
COVER_TOP = PI.COVER_TOP
COVER_END_Z = 36.95
HUG_GAP = 0.4

# Body: a squircle plan (|x/a|^n corners), the same outline from the floor to the top.
A = 29.6                    # half width: the BiBoard plug (X to 27.27) is inside the right wall
Z0, Z1 = -37.8, 56.2        # front and rear faces
R_PLAN, NEXP = 13.0, 5.0    # plan corner size and squircle exponent
WALL = 1.8
IN_A, ZF_IN, ZR_IN = A - WALL, Z0 + WALL, Z1 - WALL     # inner faces: 27.8, -36.0, 54.4
FLOOR_Y0, FLOOR_Y1 = PI.MOUNT_Y0, PI.MOUNT_Y1          # the floor is the platform mount plate
SEAM = 57.2                 # top of the body walls = bottom of the panel
TOP = 63.2                  # panel top: 0.3 over the highest port
RT = 4.0                    # round on the top edge; the last 45 deg of it is a chamfer (the bed edge in the print)
PANEL_T = 1.6
PANEL_IN = TOP - PANEL_T    # 61.6, underside of the panel top

# Pegs (on the cover) and keyholes (in the floor): platform interface v3.0
PEGS = PI.PEGS
SLIDE = PI.SLIDE            # the body drops on SLIDE rearward (+Z) of its place, then slides forward (-Z) to lock
DET = PI.DET
# No part may stand on the floor over a peg, its slide path or its click beams below this Y.
KEEP_Y = PI.HEAD_CLEAR_Y + 0.1


def keep_zone(px, pz):
    """Floor area of one keyhole: the drop-in hole, the slot, the click beams. (x0, x1, z0, z1)"""
    return (px - 5.6, px + 5.6, pz - SLIDE - PI.PEG_HEAD_D / 2 - 1.5, pz + PI.tip_len(PI.PEG_HEAD_D, PI.HEAD_TIP_DEG) + 0.6)


# Pi Zero 2 W + PiSugar 2 (1200 mAh) stack, on its long edge: the boards are vertical (normal +X),
# the ports and the PiSugar controls are up, the GPIO header is at the bottom with the Dupont plugs to
# the right (+X). The SD card end is at the front. The models are first put in the flat frame of
# rev 0.15 (FLAT_*), then turned with STAND.
FLAT_GPIO_X, FLAT_Z_CSI, FLAT_DY = -16.5, -16.0, 45.0
FLAT_Z_SD = FLAT_Z_CSI + 65.0
PI_PCB_TOP_X = 1.5                         # the Pi component face
STACK_Y0 = 30.0                            # GPIO edge of the boards (2.5 over the floor)
STACK_ZF = -29.2                           # SD end of the boards (front)
STACK_ZR = STACK_ZF + 65.0                 # CSI end (rear); the CSI connector stands 0.9 behind it
STAND = np.array([[0, 1, 0, PI_PCB_TOP_X - (FLAT_DY + 0.8)],
                  [1, 0, 0, STACK_Y0 - FLAT_GPIO_X],
                  [0, 0, -1, STACK_ZF + FLAT_Z_SD],
                  [0, 0, 0, 1]], dtype=float)
BAT = dict(x=(-15.2, -5.2), y=(STACK_Y0 + 0.5, STACK_Y0 + 29.5), z=(STACK_ZF + 4.5, STACK_ZF + 60.5))   # PiSugar repo batt-1200
PCB_X = (-2.3, 1.5)                        # PiSugar PCB back face .. Pi PCB component face
# The user's Pi has a soldered 2x20 male header with Dupont jumpers on it (photos reference/signal-*.jpeg).
HDR_ZC = STACK_ZF + 32.5                   # header center along the board
PI_PLUGS = dict(x=(PI_PCB_TOP_X + 0.1, PI_PCB_TOP_X + 0.1 + 2.5 + 14.0), y=(STACK_Y0 + 0.96, STACK_Y0 + 6.04),
                z=(HDR_ZC - 25.4, HDR_ZC + 25.4))     # header plastic 2.5 + plug housings 14; the model PCB face is at X 1.6
# End posts: vertical grooves for the two PCB ends; the bottom of the groove is the stop.
POST = dict(x=(-4.6, 5.1), top=50.0, clr=0.25, depth=2.15)
POST_F = (STACK_ZF - 2.8, STACK_ZF + POST["depth"] + 0.1)     # front post: the SD card stands out about 2.5 in front of the board
POST_R = (STACK_ZR - 2.4, STACK_ZR + 2.0)                     # rear post: the CSI connector stands out 0.9
SD = dict(x=(1.3, 3.35), y=(34.75, 55.25))                    # SD holder on the Pi component face (model) + clearance
SD_CARD = dict(x=(1.3, 3.1), y=(39.0, 52.0), out=2.9)         # card: 11 wide, about 2.5 out of the holder (not measured)
CSI = dict(x=(0.0, 3.05), y=(33.5, 56.5), out=1.15)           # CSI connector (model) + clearance

# Ports (from the models): PiSugar charge, button, switch; Pi power, data USB, mini-HDMI. All up.
# The Pi power port and the PiSugar charge port are side by side: plug in one of them at a time.
PORT_PLUGS = dict(                 # (x center, z center, x size, z size) of the plug body
    hdmi=(3.25, STACK_ZF + 12.65, 8.5, 14.0),
    pi_usb=(2.9, STACK_ZF + 41.6, 7.5, 11.0),
    pi_power=(2.9, STACK_ZF + 54.1, 7.5, 11.0),
    charge=(-3.6, STACK_ZF + 53.7, 8.0, 12.0),
)
PORT_TOP = 61.3                    # highest port face
# Port openings in the panel: each one is the plug body + PORT_CLR, with round corners and a 45 deg
# chamfer on the top edge. The Pi power and the PiSugar charge openings join.
PORT_CLR, PORT_R, PORT_CHAMFER = 0.4, 1.0, 0.5
# Forks under the panel over the top edge of the boards (where no port is)
STACK_FORKS = [STACK_ZF + 25.4, STACK_ZF + 61.0]   # z0 of each fork, 2 long
FORK = dict(len=2.0, lip=1.85, clr_y=0.1)
# Power switch: the PiSugar slide switch lever (model: X -3.66..-2.66, Y 59.5..60.9, 1.3 long in Z) is
# 0.9 above the board edge. A slider part rests on it: a fork goes over the lever, a 5.5 x 5 tab stands
# 2 mm out of a slot in the panel. The lever travel is not measured: the slot gives +-2.0.
SW_LEVER = dict(x=(-3.66, -2.66), y=(59.5, 60.9), z=(STACK_ZF + 12.1, STACK_ZF + 13.4))
SW = dict(zc=STACK_ZF + 12.75, travel=2.0, body_x=(-12.0, -2.45), body_y=(60.15, 61.45), body_hz=2.45,
          notch_x=(-3.9, -2.4), notch_hz=0.85, notch_y=61.0,
          tab_x=(-9.9, -4.6), tab_hz=2.5, tab_top=TOP + 2.0, tab_chamfer=0.8, slot_clr=0.1)
# Button: a spring tongue in the panel top over the PiSugar button (model: X -3.8..-2.8, top Y 60.2).
# The tongue is 1.0 thick (thinned from below). An arm under its free end stands 0.2 over the button.
BTN = dict(x=(-10.5, -4.5), z=(6.5, 16.5), t=1.0, slit=0.6, cap=(-3.8, -2.8, 12.89, 14.75, 60.2),
           arm_x=(-6.5, -2.5), arm_z=(12.8, 14.8), gap=0.2, press=0.6)

# BiBoard 5-pin female header in the cover slot (GND, +5V, TX2, RX2, ..). Straight Dupont plugs.
SLOT = PI.SLOT
HDR = PI.HDR
BB_PLUG = dict(x=(HDR["x0"], HDR["x1"]), y=(HDR["top"], HDR["top"] + 14.0), z=(HDR["z0"], HDR["z1"]))
HDR_NOTCH = dict(x=(23.9, IN_A + 0.01), z=(HDR["z0"] - SLIDE - 0.8, HDR["z1"] + 0.8))   # floor notch: header + slide

# Speaker: NULLLAB 3 W 4 ohm box speaker (user ruler measurements). Ear plate 45 x 31 x 1.5 (X, Y, Z),
# body 27 x 30 x 14.3 behind it. It stands at the rear, sound face to the rear grille. The two ends of
# the ear plate go down into vertical grooves.
SPK = dict(l=45.0, body_l=27.0, d=31.0, h=14.3, ear_t=1.5, hole_d=4.0, hole_in=4.5)
SPK_ZE = 38.2                              # front face of the ear plate
SPK_Y0 = FLOOR_Y1 + 0.1
SPK_GROOVE = dict(x_in=21.25, clr=0.25, lip=1.5, top=56.5, clr_y=0.4)

# NS4168 amp board (38.4 x 22.4 x 1.6) on edge in the left gallery, along Z. The PCB is 0.5 from the
# left wall, the parts face the battery (+X). The bottom edge stands in a slot in a bar on the floor.
AMP = dict(t=1.6, l=38.4, h=22.4, comp=10.0)
AMP_X = (-IN_A + 0.5, -IN_A + 0.5 + AMP["t"])   # -27.3 .. -25.7
AMP_Y0 = 28.5
AMP_Z = (-9.0, -9.0 + AMP["l"])                  # I2S 5-pin PH2.0 at the front end, speaker 2-pin PH2.0 and the screw terminal at the rear end
AMP_FORKS = [2.0, 12.0]                          # z0 of the panel forks over the amp top edge (2.5 long)
# Board layout from the NULLLAB photo (u from the I2S end, v down from the top edge, mm). The PH2.0 headers are
# side entry: the plugs go in along the board, from the ends. ph=height of the PH headers over the PCB.
AMP_L = dict(ph5=(0.75, 6.8, 3.8, 17.4), ph2=(29.0, 35.7, 9.1, 17.0), term=(29.0, 36.8, 0.75, 7.6), ic=(17.7, 24.0, 7.2, 13.6),
             holes=[(15.2, 2.65), (15.2, 19.3)], hole_d=4.7, ph=5.0, term_h=8.5, plug_out=3.7)

# SPH0645 mic board (Adafruit 3421 size, 16.7 x 12.7 x 1.8) at the front wall, centered, port face to
# the front, the 6 pins (SEL, LRCL, DOUT, BCLK, GND, 3V) along the top edge. Its two sides go down into
# grooves. Sound holes in the front face.
MIC = dict(w=16.7, l=12.7, t=1.8, y0=29.0, clr=0.1)
MIC_Z = (ZF_IN + 0.4, ZF_IN + 0.4 + MIC["t"])     # -35.6 .. -33.8
MIC_PORT_Y = MIC["y0"] + MIC["l"] / 2            # port assumed at the board center (not measured)

# Panel snaps: four spring tabs, two on the front wall and two on the rear wall. Each tab hangs from
# the panel and has a bump that clicks into a pocket in the wall. The catch face is 45 deg (the print
# limit), the lead face 30 deg from vertical. snap_force() gives the forces.
TAB = dict(x=17.5, b=4.0, t=0.9, y_end=52.6, e=0.6, y_catch=55.2, flat=0.3, catch=45.0, lead=30.0, gap=0.15)
# Side lips under the panel: they locate the panel in X on the side walls.
LIPS_Z = [(-26.0, -16.0), (18.0, 26.0)]
LIP = dict(t=1.2, y0=54.2, gap=0.15)
# Finger notch in the rear wall under the seam: lift the rear edge of the panel here.
NOTCH = dict(hw=7.0, h=1.5, d=1.0)
# Camera cable: the Grove cable of the Petoi AI Vision Module comes along the side of the robot and
# goes in through a notch at the base of the right wall (a matching notch on the left), to the Pi header.
CAM_NOTCH = dict(z=(-15.0, -7.0), y1=28.6)
# Grille in the rear face, mic holes in the front face
GRILLE = dict(x=np.arange(-13.5, 13.6, 3.0), y=np.arange(33.0, 51.1, 3.0), d=1.6)

# Wire paths (check(): no printed part and no other electronics in them). Dupont jumper wire is about 1.4 mm.
WIRE_PATHS = {
    "uart: Pi header to BiBoard plug": [dict(x=(18.2, 27.6), y=(31.0, 54.0), z=(-16.5, 30.0))],
    "i2s: under the stack to the amp": [dict(x=(-15.4, 18.0), y=(27.6, 29.8), z=(-26.3, -18.6)),
                                        dict(x=(-25.0, -15.6), y=(27.6, 47.0), z=(-18.6, -12.2))],
    "mic: over the mic to the right well": [dict(x=(-7.1, 7.1), y=(42.3, 52.0), z=(-33.6, -32.2)),
                                            dict(x=(-7.1, 21.0), y=(50.6, 54.0), z=(-33.6, -29.9)),
                                            dict(x=(5.6, 21.0), y=(37.0, 54.0), z=(-29.9, -22.3))],
    "speaker: amp rear end to the speaker": [dict(x=(-24.5, -18.5), y=(33.5, 52.0), z=(31.6, 36.2)),
                                             dict(x=(-21.0, -11.0), y=(52.0, 61.0), z=(33.0, 36.2)),
                                             dict(x=(-14.0, -6.0), y=(59.0, 61.0), z=(36.2, 44.0))],
    "camera: notch to the Pi header": [dict(x=(18.2, IN_A - 0.2), y=(FLOOR_Y1 + 0.1, 36.5), z=(-15.0, -9.0))],
}
WIRE_R = 0.7
# Space for a finger tip over the BiBoard plug (panel off)
FINGER = dict(x=(6.0, IN_A - 0.2), y=(37.0, SEAM), z=(11.0, 27.0))


def flat_ps2():
    """PiSugar 2 board model frame -> the flat frame of rev 0.15. The model has the Pi side at -Y."""
    return np.array([[0, 0, 1, FLAT_GPIO_X], [0, -1, 0, FLAT_DY], [1, 0, 0, FLAT_Z_CSI], [0, 0, 0, 1]], dtype=float)


def flat_pi():
    """Pi Zero model (PiSugar repo model3 frame) -> the flat frame of rev 0.15."""
    return np.array([[0, 0, 1, FLAT_GPIO_X - 3.08], [0, 1, 0, FLAT_DY - 18.83 - 0.5],
                     [-1, 0, 0, FLAT_Z_SD + 6.89], [0, 0, 0, 1]], dtype=float)


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


def plan(inset, n=64):
    """Closed plan outline (x, z) of the body, moved inset along the normal from the outer face.
    Counterclockwise seen from +Y. The same points for every inset: lofts between plans are clean."""
    a, z0, z1, r = A, Z0, Z1, R_PLAN
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
    return prism_y(plan(0.0), FLOOR_Y0, SEAM)


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


def stack_posts():
    """Front and rear posts with vertical grooves for the two board ends. The groove bottom is the stop."""
    c, (x0, x1) = POST["clr"], POST["x"]
    groove = lambda za, zb: mbox(PCB_X[0] - c, PCB_X[1] + c, STACK_Y0 - 0.15, 99, za, zb)
    f = mbox(x0, x1, FLOOR_Y1 - 0.01, POST["top"], *POST_F)
    f -= groove(STACK_ZF - c, POST_F[1] + 1)
    f -= mbox(*SD["x"], *SD["y"], STACK_ZF - c, POST_F[1] + 1)
    f -= mbox(*SD_CARD["x"], *SD_CARD["y"], STACK_ZF - SD_CARD["out"], POST_F[1] + 1)
    r = mbox(x0, x1, FLOOR_Y1 - 0.01, POST["top"], *POST_R)
    r -= groove(POST_R[0] - 1, STACK_ZR + c)
    r -= mbox(*CSI["x"], *CSI["y"], POST_R[0] - 1, STACK_ZR + CSI["out"])
    return f + r


def mic_posts():
    """Two posts with grooves for the sides of the mic board, and a base under it. The front wall is in front of it."""
    M, c = MIC, MIC["clr"]
    hw = M["w"] / 2
    za, zb = ZF_IN - 0.5, MIC_Z[1] + c + 1.5
    p = mbox(-hw - 2.25, hw + 2.25, FLOOR_Y1 - 0.01, M["y0"] - c, za, zb)            # base
    for sx in (-1, 1):
        p += mbox(*sorted((sx * (hw - 0.5), sx * (hw + 2.25))), FLOOR_Y1 - 0.01, M["y0"] + M["l"] + 0.3, za, zb)
    return p - mbox(-hw - c, hw + c, M["y0"] - c, 99, ZF_IN, MIC_Z[1] + c)


def amp_base():
    """Bar on the floor along the left wall with a slot for the bottom edge of the amp board."""
    c = 0.15
    b = mbox(-IN_A - 0.5, AMP_X[1] + 1.55, FLOOR_Y1 - 0.01, 30.0, *AMP_Z)
    return b - mbox(AMP_X[0] - c, AMP_X[1] + c, AMP_Y0 - 0.15, 31.0, AMP_Z[0] - 1, AMP_Z[1] + 1)


def bump_cs(e, grow=0.0):
    """Snap bump profile (u, y) on a tab face: u = out of the tab into the wall pocket."""
    T = TAB
    yt = T["y_catch"]
    y1 = yt - e / math.tan(math.radians(T["catch"]))
    y2 = y1 - T["flat"]
    y3 = y2 - e / math.tan(math.radians(T["lead"]))
    cs = _cs([(-0.3, yt), (0.0, yt), (e, y1), (e, y2), (0.0, y3), (-0.3, y3)])
    return cs.offset(grow, m3.JoinType.Round) if grow else cs


def tab_bump(sz, x, e, grow=0.0, w=None):
    """The bump profile on the tab face of the front (sz -1) or rear (sz +1) wall, along X over the width w."""
    w = TAB["b"] if w is None else w
    zf = (ZR_IN - TAB["gap"]) if sz > 0 else (ZF_IN + TAB["gap"])     # tab outer face
    pts = [(y, zf + sz * u) for u, y in np.asarray(bump_cs(e, grow).to_polygons()[0])]
    return prism_x(pts, x - w / 2, x + w / 2)


def tabs():
    """The four spring tabs of the panel, with their bumps."""
    T = TAB
    out = []
    for sz in (-1, 1):
        zf = (ZR_IN - T["gap"]) if sz > 0 else (ZF_IN + T["gap"])
        for sx in (-1, 1):
            x = sx * T["x"]
            out.append(mbox(x - T["b"] / 2, x + T["b"] / 2, T["y_end"], PANEL_IN + 0.01, *sorted((zf, zf - sz * T["t"]))))
            out.append(tab_bump(sz, x, T["e"]))
    return union(out)


def pockets():
    """Pockets in the front and rear walls for the tab bumps (0.15 clearance, 45 deg roof)."""
    return union([tab_bump(sz, sx * TAB["x"], TAB["e"], grow=0.15, w=TAB["b"] + 1.0) for sz in (-1, 1) for sx in (-1, 1)])


def keyhole_cut(px, pz):
    from bittle_platform import build as BP
    return b3d_to_manifold(BP.keyhole_cutter(px, pz))


def keyhole_bump(px, pz):
    from bittle_platform import build as BP
    return b3d_to_manifold(BP.detent_bump(px, pz))


def build_body():
    O = body_outer()
    B = O - prism_y(plan(WALL), FLOOR_Y1, SEAM + 1)
    B += (speaker_posts() + stack_posts() + mic_posts() + amp_base()) ^ O
    for px, pz in PEGS:
        B -= keyhole_cut(px, pz)
    for px, pz in PEGS:
        B += keyhole_bump(px, pz)
    N = HDR_NOTCH
    B -= mbox(*N["x"], FLOOR_Y0 - 1, 30.0, *N["z"])                       # the BiBoard header comes up here
    for sx in (-1, 1):                                                     # camera cable notches
        B -= mbox(*sorted((sx * (IN_A - 2.0), sx * (A + 1))), FLOOR_Y0 - 1, CAM_NOTCH["y1"], *CAM_NOTCH["z"])
    B -= pockets()
    nt = _cs([(NOTCH["hw"] + NOTCH["h"] * math.cos(t), SEAM + NOTCH["h"] * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 16)]
             + [(-NOTCH["hw"] - NOTCH["h"] * math.cos(t), SEAM - NOTCH["h"] * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 16)])
    B -= nt.extrude(NOTCH["d"] + 1).translate([0, 0, Z1 - NOTCH["d"]])   # finger notch
    holes = [teardrop_z(ZR_IN - 0.5, Z1 + 0.5, GRILLE["d"] / 2, x, y) for x in GRILLE["x"] for y in GRILLE["y"]]
    for a in [None] + list(range(0, 360, 60)):                             # mic holes around the port
        dx, dy = (0.0, 0.0) if a is None else (2.2 * math.cos(math.radians(a)), 2.2 * math.sin(math.radians(a)))
        holes.append(teardrop_z(Z0 - 0.5, ZF_IN + 0.5, 0.5, dx, MIC_PORT_Y + dy, n=12))
    B -= union(holes)
    return B


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
        f = mbox(xa - FORK["lip"], xb + FORK["lip"], 58.6, PANEL_IN + 0.01, z0, z0 + FORK["len"])
        out.append(f - mbox(xa, xb, 0, STACK_Y0 + 30.0 + FORK["clr_y"], z0 - 1, z0 + FORK["len"] + 1))
    G = SPK_GROOVE                                         # over the ends of the speaker ear plate
    za, zb = SPK_ZE - G["clr"], SPK_ZE + SPK["ear_t"] + G["clr"]
    for sx in (-1, 1):
        f = mbox(*sorted((sx * 15.5, sx * 18.5)), 58.0, PANEL_IN + 0.01, za - G["lip"], zb + G["lip"])
        out.append(f - mbox(*sorted((sx * 15.0, sx * 19.0)), 0, SPK_Y0 + SPK["d"] + G["clr_y"], za, zb))
    for z0 in AMP_FORKS:                                   # over the top edge of the amp board
        f = mbox(-IN_A + 0.15, AMP_X[1] + 1.55, 50.0, PANEL_IN + 0.01, z0, z0 + 2.5)
        out.append(f - mbox(-IN_A - 1, AMP_X[1] + 0.15, 0, AMP_Y0 + AMP["h"] + 0.3, z0 - 1, z0 + 3.5))
    return union(out)


def side_lips():
    out = []
    for sx in (-1, 1):
        for z0, z1 in LIPS_Z:
            out.append(mbox(*sorted((sx * (IN_A - LIP["gap"] - LIP["t"]), sx * (IN_A - LIP["gap"]))), LIP["y0"], PANEL_IN + 0.01, z0, z1))
    return union(out)


def port_openings():
    """Openings for the plug bodies: plug + PORT_CLR, round corners, a 45 deg chamfer at the top face."""
    out = []
    for xc, zc, sx, sz in PORT_PLUGS.values():
        x0, x1 = xc - sx / 2 - PORT_CLR, xc + sx / 2 + PORT_CLR
        z0, z1 = zc - sz / 2 - PORT_CLR, zc + sz / 2 + PORT_CLR
        low = prism_y(rrect_pts(x0, x1, z0, z1, PORT_R), PANEL_IN - 1, TOP - PORT_CHAMFER)
        c = PORT_CHAMFER
        high = prism_y(rrect_pts(x0 - c, x1 + c, z0 - c, z1 + c, PORT_R + c), TOP, TOP + 1)
        out.append(m3.Manifold.batch_hull([low, high]))
    return union(out)


def switch_slot():
    S = SW
    c = S["slot_clr"]
    return prism_y(rrect_pts(S["tab_x"][0] - c, S["tab_x"][1] + c, S["zc"] - S["tab_hz"] - S["travel"] - c,
                             S["zc"] + S["tab_hz"] + S["travel"] + c, 1.0), PANEL_IN - 1, TOP + 1)


def build_switch(dz=0.0):
    """Slider for the PiSugar power switch, in place on the lever (dz: moved along Z)."""
    S = SW
    zc = S["zc"]
    b = mbox(*S["body_x"], *S["body_y"], zc - S["body_hz"], zc + S["body_hz"])
    b -= mbox(*S["notch_x"], S["body_y"][0] - 1, S["notch_y"], zc - S["notch_hz"], zc + S["notch_hz"])     # fork over the lever
    t = prism_y(rrect_pts(S["tab_x"][0], S["tab_x"][1], zc - S["tab_hz"], zc + S["tab_hz"], 1.0), S["body_y"][1] - 0.01,
                S["tab_top"] - S["tab_chamfer"])
    c = S["tab_chamfer"]
    top = prism_y(rrect_pts(S["tab_x"][0] + c, S["tab_x"][1] - c, zc - S["tab_hz"] + c, zc + S["tab_hz"] - c, 0.4),
                  S["tab_top"] - 0.01, S["tab_top"])
    t = m3.Manifold.batch_hull([t, top])
    for k in (-1, 0, 1):                                   # finger ribs across the tab
        t -= mbox(S["tab_x"][0] - 1, S["tab_x"][1] + 1, S["tab_top"] - 0.4, S["tab_top"] + 1, zc + 1.4 * k - 0.3, zc + 1.4 * k + 0.3)
    return (b + t).translate([0, 0, dz])


def button_cuts():
    """U slit around the tongue and the thinning under it."""
    B = BTN
    (x0, x1), (z0, z1), w = B["x"], B["z"], B["slit"]
    u = mbox(x0 - w, x1 + w, PANEL_IN - 1, TOP + 1, z0 + 0.01, z1 + w) - mbox(x0, x1, PANEL_IN - 2, TOP + 2, z0 - 1, z1)
    thin = mbox(x0, x1, PANEL_IN - 1, TOP - B["t"], z0 - 0.01, z1)
    return u + thin


def button_arm(dy=0.0):
    """Arm under the free end of the tongue: down from the tongue, then across over the button."""
    B = BTN
    y_low = B["cap"][4] + B["gap"]
    v = mbox(B["arm_x"][0], B["x"][1] - 0.2, y_low, TOP - B["t"] + 0.01, *B["arm_z"])
    h = mbox(B["arm_x"][0], B["arm_x"][1], y_low, y_low + 0.8, *B["arm_z"])
    return (v + h).translate([0, dy, 0])


def build_panel(with_tabs=True):
    P = panel_outer() - prism_y(plan(WALL), SEAM - 1, PANEL_IN)
    P -= port_openings() + switch_slot() + button_cuts()
    P += panel_forks() + side_lips() + button_arm()
    if with_tabs:
        P += tabs()
    return P


def snap_force():
    """Panel tabs: cantilever k = 3EI/L^3, wedge faces with friction. Forces in N."""
    T, mu = TAB, PI.MU_PLA
    y_crest = T["y_catch"] - T["e"] / math.tan(math.radians(T["catch"])) - T["flat"] / 2
    L = PANEL_IN - y_crest
    k = 3 * PI.E_PLA * (T["b"] * T["t"] ** 3 / 12) / L ** 3
    d = T["e"] - T["gap"]                                 # the tab bends this much as the bump passes the wall face
    F = k * d
    phi = math.atan(mu)
    push = F * math.tan(math.radians(T["lead"]) + phi)
    pull = F * math.tan(math.radians(T["catch"]) + phi)
    return dict(tab_k_N_per_mm=round(k, 2), tab_travel=round(d, 2), push_one_tab_N=round(push, 1), pull_one_tab_N=round(pull, 1),
                close_N=round(4 * push, 1), open_one_end_N=round(2 * pull, 1),
                strain_pct=round(100 * 1.5 * T["t"] * d / L ** 2, 2))


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


def chaikin(pts, k=2):
    """Round the corners of a polyline (the end points stay)."""
    P = np.asarray(pts, float)
    for _ in range(k):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            Q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        Q.append(P[-1])
        P = np.array(Q)
    return P


def tube(pts, r=WIRE_R, smooth=2):
    """A wire along a polyline: hulls of spheres at the points."""
    P = chaikin(pts, smooth) if smooth else np.asarray(pts, float)
    S = [m3.Manifold.sphere(r, 10).translate(list(p)) for p in P]
    return union([m3.Manifold.batch_hull([a, b]) for a, b in zip(S[:-1], S[1:])])


# Pi header: 2x20, pin 1 at the SD card end (front), odd pins in the inner row, even pins at the board edge (down).
HDR_BASE_X = (PI_PCB_TOP_X + 0.1, PI_PCB_TOP_X + 2.6)
HOUSING_END = HDR_BASE_X[1] + 14.0                  # Dupont housing: 2.5 x 2.5 x 14
EXIT_X = HOUSING_END + 1.5


def pin_yz(n):
    k = (n - 1) // 2
    return STACK_Y0 + 3.5 + (1.27 if n % 2 else -1.27), HDR_ZC - 25.4 + 1.27 + 2.54 * k


def bb_pin_z(k):
    """BiBoard header pin k (0 = GND, 1 = +5V, 2 = TX2, 3 = RX2): order assumed from the front."""
    return HDR["z0"] + 1.27 + 2.54 * k


BB_X = (HDR["x0"] + HDR["x1"]) / 2
AMP_PLUG_Y = [AMP_Y0 + AMP["h"] - v for v in (6.6, 8.6, 10.6, 12.6, 14.6)]   # G, V, BCLK, LRCLK, DIN
AMP_PLUG_Z0 = AMP_Z[0] - AMP_L["plug_out"] + AMP_L["ph5"][0]                  # front face of the I2S plug
MIC_HOLE_Y = MIC["y0"] + MIC["l"] - 1.27                                      # solder holes along the top edge
MIC_HOLE_X = [-6.35 + 2.54 * k for k in range(6)]                            # SEL, LRCL, DOUT, BCLK, GND, 3V


def to_pin(n, via):
    """End of a wire route: via points, then straight into the housing of Pi pin n."""
    y, z = pin_yz(n)
    return list(via) + [(EXIT_X + 0.8, y, z), (EXIT_X, y, z), (HOUSING_END, y, z)]


# Wires: (group, label, color, Pi pin, points from the far end to the Pi header). Pins: see the wiring table.
def wire_routes():
    W = []
    # UART to the BiBoard: Pi GND 6 -> GND, TX 8 -> RX2, RX 10 -> TX2. Up from the header plugs, over, down into the BiBoard plugs.
    for i, (n, k, col, lab) in enumerate(((6, 0, "#1d1d1f", "GND"), (8, 3, "#2e9b4f", "TX > RX2"), (10, 2, "#f2f2ef", "RX < TX2"))):
        y, z = pin_yz(n)
        zb = bb_pin_z(k)
        pts = [(BB_X, BB_PLUG["y"][1], zb), (BB_X, 46.5 + i, zb), (22.0, 50.5 - i, (z + zb) / 2 + 2)]
        W.append(("uart", lab, col, to_pin(n, pts)))
    # I2S + power to the amp: from the I2S plug at the front end of the amp, down to the floor, across under the
    # stack in front of the front pegs, up the right well to the header.
    for i, (n, col, lab) in enumerate(((9, "#1d1d1f", "GND"), (2, "#d83a34", "5V"), (12, "#f0c419", "BCLK"),
                                       (35, "#e8641b", "LRCLK"), (40, "#3a6fd8", "DIN"))):
        y, z = pin_yz(n)
        zc = -19.2 - 1.6 * i
        pts = [(-23.2, AMP_PLUG_Y[i], AMP_PLUG_Z0), (-23.2, AMP_PLUG_Y[i], -14.6), (-21.0, 28.3, zc), (-14.0, 28.3, zc),
               (19.0, 28.3, zc), (20.6, 28.6, zc + 1.0), (20.6, y - 1.0, z)]
        W.append(("amp", lab, col, to_pin(n, pts)))
    # Mic: from the solder holes on the back face, up in front of the front post, over it, into the right well.
    for k, n, col, lab in ((1, 35, "#e8641b", "LRCL"), (2, 38, "#8e5bd8", "DOUT"), (3, 12, "#f0c419", "BCLK"),
                           (4, 14, "#1d1d1f", "GND"), (5, 1, "#d83a34", "3V")):
        y, z = pin_yz(n)
        x = MIC_HOLE_X[k]
        pts = [(x, MIC_HOLE_Y, MIC_Z[1]), (x, MIC_HOLE_Y, -33.0), (x, 51.4, -33.0), (8.2 + 0.5 * k, 52.6, -30.3),
               (21.0 - 0.5 * k, 46.0, -24.0), (21.0, y + 2.0, z)]
        W.append(("mic", lab, col, to_pin(n, pts)))
    # Camera (Grove): in through the right notch on the floor, up to the header. Outside, it goes along the robot side.
    for i, (n, col, lab) in enumerate(((20, "#1d1d1f", "GND"), (17, "#d83a34", "3V3"), (3, "#f2f2ef", "SDA"), (5, "#f0c419", "SCL"))):
        y, z = pin_yz(n)
        zc = CAM_NOTCH["z"][1] - 1.5 - 1.6 * i
        pts = [(36.0, 23.5, zc), (31.5, 27.3, zc), (27.6, 27.6, zc), (25.2, 28.4, zc), (22.6, 28.6, zc), (21.4, y - 1.5, z)]
        W.append(("camera", lab, col, to_pin(n, pts)))
    return W


def speaker_leads():
    """The two speaker leads: from the top of the speaker body, over the ear plate, down the left gallery
    into the 2-pin plug at the rear end of the amp."""
    out = []
    zp = AMP_Z[0] + AMP_L["ph2"][1] + AMP_L["plug_out"]           # rear face of the 2-pin plug
    for i, (col, lab) in enumerate((("#d83a34", "+"), ("#1d1d1f", "-"))):
        y_p = AMP_Y0 + AMP["h"] - 12.05 + (i - 0.5) * 2.0
        pts = [(-23.2, y_p, zp), (-23.2, y_p, zp + 1.8), (-20.6, 51.5, 34.7), (-15.0, 59.8 - 0.0 * i, 35.2 + 0.0 * i),
               (-11.0 + 1.6 * i, 59.8, 41.2), (-10.0 + 1.6 * i, 59.3, 43.2), (-10.0 + 1.6 * i, SPK_Y0 + SPK["d"] - 0.5, 44.0)]
        out.append(("speaker", lab, col, pts))
    return out


def build_models():
    """The electronics in place. Returns (models for the checks, display parts: (model, sub, label, mesh, color))."""
    D = []
    def add(key, sub, label, M, col):
        D.append((key, sub, label, M, col))
        return M
    pisugar = add("pisugar2", "board", "PiSugar 2 board", stl_manifold("pisugar2Board.STL", STAND @ flat_ps2()), "#e06aa3")
    pizero = add("pizero", "board", "Raspberry Pi Zero 2 W", stl_manifold("RaspberryPiZeroW-1.STL", STAND @ flat_pi()), "#2e9b4f")
    # battery: a pouch cell with round edges, a seal flap at the front end, and two leads to the PiSugar 2 (lead place estimated)
    bx, by, bz = BAT["x"], BAT["y"], BAT["z"]
    cell = add("battery", "cell", "1200 mAh cell", rbox("z", bx[0], bx[1], by[0], by[1], bz[0] + 2.5, bz[1], 1.6), "#b9bcc2")
    xm = (bx[0] + bx[1]) / 2
    flap = add("battery", "flap", "cell seal", rbox("z", xm - 0.5, xm + 0.5, by[0] + 1.5, by[1] - 1.5, bz[0], bz[0] + 2.6, 0.45), "#d9b34a")
    leads = [add("battery", f"lead{i}", "cell lead", tube([(xm + d, 34.0, bz[0] + 0.3), (xm + d, 34.0, bz[0] - 0.6), (-6.6, 34.5 + d, bz[0] - 0.4),
                                                             (-5.5, 34.5 + d, bz[0] + 2.5)], 0.5), c)
             for i, (d, c) in enumerate(((-0.7, "#d83a34"), (0.7, "#1d1d1f")))]
    bat = cell + flap + union(leads)
    # microSD card: the part out of the holder (about 2.5 mm, not measured)
    card = add("sd_card", "card", "microSD card", rbox("x", 1.85, 2.85, 39.5, 50.5, STACK_ZF - 2.5, STACK_ZF - 0.05, 0.8), "#26272b")
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
                  for y, z in (pin_yz(n) for n in range(1, 41) if n not in used_pins)])
    add("pi_plugs", "pins", "header pins", pins, "#d9b34a")
    hous = union([rbox("x", HDR_BASE_X[1], HOUSING_END, y - 1.25, y + 1.25, z - 1.25, z + 1.25, 0.25, 8)
                   for y, z in (pin_yz(n) for n in sorted(used_pins))])
    add("pi_plugs", "housings", "Dupont housings", hous, "#3a3b40")
    pi_plugs = base + pins + hous
    # BiBoard header (female, 5 pins) and three male Dupont plugs on GND, TX2, RX2
    cov = load_stl(os.path.join(PREF, "Bittle_Cover.stl")).reshape(-1, 3)
    m = (cov[:, 0] > HDR["x0"]) & (cov[:, 0] < HDR["x1"]) & (cov[:, 2] > HDR["z0"]) & (cov[:, 2] < HDR["z1"])
    hdr = mbox(HDR["x0"], HDR["x1"], float(cov[m, 1].min()) - 3.0, HDR["top"], HDR["z0"], HDR["z1"])
    hdr -= union([mbox(BB_X - 0.5, BB_X + 0.5, HDR["top"] - 3.0, HDR["top"] + 1, bb_pin_z(k) - 0.5, bb_pin_z(k) + 0.5) for k in range(5)])
    add("biboard_header", "header", "BiBoard 5-pin header (est. height)", hdr, "#0d0d0d")
    bb = union([rbox("y", BB_X - 1.25, BB_X + 1.25, BB_PLUG["y"][0], BB_PLUG["y"][1], bb_pin_z(k) - 1.25, bb_pin_z(k) + 1.25, 0.25, 8)
                for k in (0, 2, 3)])
    add("biboard_plug", "housings", "Dupont plugs on the BiBoard header", bb, "#3a3b40")
    # NS4168 amp (NULLLAB photo and drawing): u along the board from the front (I2S) end, v down from the top edge
    L = AMP_L
    x0, x1 = AMP_X
    yt = AMP_Y0 + AMP["h"]
    zu = lambda u: AMP_Z[0] + u
    yv = lambda v: yt - v
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
    # SPH0645 mic board (Adafruit 3421): PCB, mic part on the back face, solder holes along the top edge, port hole
    M = MIC
    pcb_z = (MIC_Z[0], MIC_Z[0] + 1.6)
    mp = rbox("z", -M["w"] / 2, M["w"] / 2, M["y0"], M["y0"] + M["l"], *pcb_z, 0.8)
    mp -= mcyl("z", MIC_Z[0] - 1, MIC_Z[1] + 1, 0.4, 0.0, MIC_PORT_Y, 12)
    mp -= union([mcyl("z", MIC_Z[0] - 1, MIC_Z[1] + 1, 0.5, x, MIC_HOLE_Y, 12) for x in MIC_HOLE_X])
    add("mic_sph0645", "pcb", "SPH0645 mic board", mp, "#22303f")
    pads = union([mcyl("z", pcb_z[1] - 0.01, pcb_z[1] + 0.05, 0.85, x, MIC_HOLE_Y, 16) for x in MIC_HOLE_X])
    pads -= union([mcyl("z", MIC_Z[0] - 1, MIC_Z[1] + 1, 0.5, x, MIC_HOLE_Y, 12) for x in MIC_HOLE_X])
    add("mic_sph0645", "pads", "mic solder pads", pads, "#d9b34a")
    can = mbox(-1.75, 1.75, MIC_PORT_Y - 1.33, MIC_PORT_Y + 1.33, pcb_z[1] - 0.01, pcb_z[1] + 1.0)
    add("mic_sph0645", "mic", "SPH0645 mic", can, "#c8c8c8")
    mic = mp + pads + can
    # speaker: black ear plate with two holes; round-edged box behind it; the sound face (rear) has a grille
    z0, z1 = SPK_ZE, SPK_ZE + SPK["ear_t"]
    yc = SPK_Y0 + SPK["d"] / 2
    plate = rbox("z", -SPK["l"] / 2, SPK["l"] / 2, SPK_Y0, SPK_Y0 + SPK["d"], z0, z1, 2.0)
    plate -= union([mcyl("z", z0 - 1, z1 + 1, SPK["hole_d"] / 2, xh, yc) for xh in (-SPK["l"] / 2 + SPK["hole_in"], SPK["l"] / 2 - SPK["hole_in"])])
    add("speaker", "plate", "speaker ear plate", plate, "#26272b")
    ze = z1 + SPK["h"]
    body = rbox("z", -SPK["body_l"] / 2, SPK["body_l"] / 2, SPK_Y0 + 0.5, SPK_Y0 + SPK["d"] - 0.5, z1 - 0.01, ze, 3.0)
    body -= rbox("z", -SPK["body_l"] / 2 + 2.5, SPK["body_l"] / 2 - 2.5, SPK_Y0 + 3.0, SPK_Y0 + SPK["d"] - 3.0, ze - 0.6, ze + 1, 2.0)
    add("speaker", "body", "NULLLAB 3 W speaker", body, "#3a3b40")
    mesh = rbox("z", -SPK["body_l"] / 2 + 2.5, SPK["body_l"] / 2 - 2.5, SPK_Y0 + 3.0, SPK_Y0 + SPK["d"] - 3.0, ze - 0.6, ze - 0.4, 2.0)
    mesh -= union([mcyl("z", ze - 1, ze + 1, 0.45, x, y, 8) for x in np.arange(-9.0, 9.1, 1.5) for y in np.arange(SPK_Y0 + 4.5, SPK_Y0 + SPK["d"] - 4.4, 1.5)])
    add("speaker", "grille", "speaker grille", mesh, "#5a5b60")
    spk = plate + body + mesh
    models = dict(pizero=pizero, pisugar2=pisugar, battery=bat, sd_card=card, pi_plugs=pi_plugs,
                  biboard_header=hdr, biboard_plug=bb, speaker=spk, amp_ns4168=amp, mic_sph0645=mic)
    # wires
    groups = {}
    for g, lab, col, pts in W + speaker_leads():
        T = add(f"wires_{g}", lab.split()[0].lower().replace("+", "pos").replace("-", "neg"), f"{g} wire {lab}", tube(pts), col)
        groups[g] = groups.get(g, []) + [T]
    for g, Ts in groups.items():
        models[f"wires_{g}"] = union(Ts)
    return models, D


def real_models():
    return build_models()[0]


STACK = ("pizero", "pisugar2", "battery", "sd_card", "pi_plugs")


def solid_cover_tris():
    """Stock cover without the Pi slot: its top surface has no hole."""
    return load_stl(os.path.join(PREF, "Bittle_Cover.stl"))


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
    return out


def build_all():
    cover = mesh_to_manifold(load_stl(os.path.join(PREF, COVER_STL)))
    return dict(cover_pegs=cover + b3d_to_manifold(build_pegs()), pod_body=build_body(), pod_panel=build_panel(),
                pod_switch=build_switch())


def wire_paths():
    return {n: union([mbox(*b["x"], *b["y"], *b["z"]) for b in boxes]) for n, boxes in WIRE_PATHS.items()}


# Endpoints of each wire path: these models may be in it.
PATH_ENDS = {"uart": ("pi_plugs", "biboard_plug", "biboard_header"), "i2s": ("pi_plugs", "amp_ns4168"),
             "mic": ("mic_sph0645",), "speaker": ("amp_ns4168", "speaker"), "camera": ("pi_plugs",)}
# Each wire group starts and ends in these parts.
WIRE_ENDS = {"wires_uart": ("pi_plugs", "biboard_plug"), "wires_amp": ("pi_plugs", "amp_ns4168"),
             "wires_mic": ("pi_plugs", "mic_sph0645"), "wires_camera": ("pi_plugs",), "wires_speaker": ("speaker", "amp_ns4168")}


def check(parts, models, robot):
    rows = []
    vol = lambda a, b: (a ^ b).volume()
    names = list(parts)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            rows.append((a, b, vol(parts[a], parts[b])))
    for a in names:
        for b, M in models.items():
            rows.append((a, b, vol(parts[a], M)))
    U = under_cover()
    ADD = ("pod_body", "pod_panel", "pod_switch")
    for a in ADD:
        rows.append((a, "under_cover", vol(parts[a], U)))
        for b, M in robot.items():
            rows.append((a, b, vol(parts[a], M)))
    for a in names:
        pcs = sorted(c.volume() for c in parts[a].decompose())
        rows.append((a, "loose_pieces", sum(pcs[:-1])))
    mn = list(models)
    for i, a in enumerate(mn):
        for b in mn[i + 1:]:
            if a == "biboard_header" and b == "biboard_plug":
                continue
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
        worst = max(vol(G.translate([0, float(dy), 0]), placed) for dy in [0.5, 1, 2, 3, 5] + list(range(8, 41, 4)))
        rows.append((f"install {g} (max over 40 mm down)", "body + parts in", worst))
        placed = placed + G
    # panel: straight down over the last 12 mm without the tabs; the tabs flex into the wall (snap_force())
    Pc = build_panel(with_tabs=False)
    inside = union([models[n] for n in models if n not in ("biboard_header",)])
    rows.append(("panel close (max over 12 mm down)", "body + parts",
                 max(vol(Pc.translate([0, float(dy), 0]), parts["pod_body"] + inside + parts["pod_switch"]) for dy in (0.2, 0.5, 1, 2, 4, 6, 8, 12))))
    # switch: the slider moves +-travel in the slot; the fork pushes the lever
    lever = mbox(*SW_LEVER["x"], *SW_LEVER["y"], *SW_LEVER["z"])
    others = union([M for m, M in models.items() if m != "pisugar2"])
    for dz in (-SW["travel"], SW["travel"]):
        S_ = build_switch(dz)
        rows.append((f"switch slider {dz:+g}mm", "pod_panel", vol(S_, parts["pod_panel"])))
        rows.append((f"switch slider {dz:+g}mm", "parts (not the PiSugar)", vol(S_, others)))
        swept = m3.Manifold.batch_hull([lever, lever.translate([0, 0, dz])])        # the fork pushes the lever along
        rows.append((f"switch slider {dz:+g}mm", "pisugar2 (not the lever)", vol(S_, models["pisugar2"] - swept)))
    rows.append(("switch fork at rest", "lever", vol(build_switch(), lever)))
    rows.append(("switch fork moved 0.3mm (must touch)", "lever", min(vol(build_switch(d), lever) for d in (-0.3, 0.3))))
    # button: the arm stands BTN gap over the button; pressed BTN press, it pushes the button
    cap = mbox(*BTN["cap"][:2], BTN["cap"][4] - 0.7, BTN["cap"][4], *BTN["cap"][2:4])
    rows.append(("button arm at rest", "button", vol(button_arm(), cap)))
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
    F = mbox(*FINGER["x"], *FINGER["y"], *FINGER["z"])
    rows.append(("finger over the BiBoard plug", "pod_body", vol(F, parts["pod_body"])))
    rows.append(("finger over the BiBoard plug", "other parts", vol(F, union([M for m, M in models.items()
                                                                            if m != "biboard_plug" and not m.startswith("wires_")]))))
    for n, (xc, zc_, sx, sz) in PORT_PLUGS.items():
        B = mbox(xc - sx / 2, xc + sx / 2, PORT_TOP + 0.2, 95.0, zc_ - sz / 2, zc_ + sz / 2)
        for b in ADD:
            rows.append((f"plug {n}", b, vol(B, parts[b])))
    return rows


# Typical masses (g) of the electronics. They are not weighed: put your own values here.
MASS_G = dict(pizero=11.0, pisugar2=8.0, battery=23.0, speaker=20.0, amp_ns4168=4.0,
              mic_sph0645=1.0, pi_plugs=3.0, biboard_plug=1.0)
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
    for n in ("pod_body", "pod_panel", "pod_switch"):
        rows.append((n, parts[n].volume() * PLA_G_MM3, centroid(parts[n])))
    for n, g in MASS_G.items():
        rows.append((n, g, centroid(models[n])))
    m = sum(r[1] for r in rows)
    c = sum(r[1] * r[2] for r in rows) / m
    return dict(mass_g=round(m, 1), com=[round(float(v), 1) for v in c],
                parts=[dict(name=n, g=round(g, 1), com=[round(float(v), 1) for v in p]) for n, g, p in rows])


def print_orient(name, M):
    """Rotate to the print orientation and put the part on the bed (Z=0)."""
    if name in ("pod_body", "pod_switch"):
        R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)        # floor (slider body) down
    elif name == "pod_panel":
        R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)        # upside down, top on the bed
    else:
        raise ValueError(name)
    M = M.transform(np.hstack([R, np.zeros((3, 1))]))
    lo, hi = M.bounding_box()[:3], M.bounding_box()[3:]
    return M.translate([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])


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
        cover=(stl_manifold(COVER_STL, ref=PREF), "#26272b"),
        pod_body=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_body.stl"))), "#e9e9e6"),
        pod_panel=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_panel.stl"))), "#e8641b"),
        pod_switch=(mesh_to_manifold(load_stl(os.path.join(OUT, "installed", "pod_switch.stl"))), "#e9e9e6"),
    )
    cols = dict(pizero="#2a8c47", pisugar2="#c4588c", battery="#3a5fa8", sd_card="#222222", pi_plugs="#d83a34",
                biboard_header="#0d0d0d", biboard_plug="#d83a34", speaker="#7a52b8", amp_ns4168="#1a5a8c",
                mic_sph0645="#d83a34")
    for n, col in cols.items():
        meshes[n] = (models[n], col)
    kids = []
    coarse = ("shoulder_right", "shoulder_left", "front_plate", "rear_plate_mirror", "cover", "pizero", "pisugar2")
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
    for n, M in parts.items():
        save_stl(M, os.path.join(OUT, "installed", f"{n}.stl"))
        if n == "cover_pegs":
            continue            # a platform part: bittle_platform/stl/print/cover_pegs.stl
        P = print_orient(n, M)
        save_stl(P, os.path.join(OUT, "print", f"{n}.stl"))
        regs = BP.overhang_regions(P)
        printing[n] = dict(overhang_mm2=round(sum(r["area"] for r in regs), 1), regions=regs[:8])
        print(f"{n:11s} vol {M.volume():8.0f} mm3  ~{M.volume() * PLA_G_MM3:5.1f} g PLA (solid)   overhang {printing[n]['overhang_mm2']:6.1f} mm2")
        for r in regs[:8]:
            print(f"     {r['area']:6.1f} mm2  flat {r['flat']:5.1f}  at print z {r['z'][0]:.1f}..{r['z'][1]:.1f}  x {r['x'][0]:.1f}..{r['x'][1]:.1f}  y {r['y'][0]:.1f}..{r['y'][1]:.1f}")
    for f in os.listdir(os.path.join(OUT, "models")):
        if f.endswith(".stl"):
            os.unlink(os.path.join(OUT, "models", f))
    for n, M in models.items():
        save_stl(M, os.path.join(OUT, "models", f"{n}.stl"))
    os.makedirs(os.path.join(OUT, "models", "parts"), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "models", "parts")):
        os.unlink(os.path.join(OUT, "models", "parts", f))
    disp = []
    for key, sub, label, M, col in build_models()[1]:
        f = f"{key}__{sub}.stl"
        save_stl(M, os.path.join(OUT, "models", "parts", f))
        disp.append(dict(model=key, sub=sub, label=label, file=f"models/parts/{f}", color=col))
    json.dump(disp, open(os.path.join(OUT, "models", "parts.json"), "w"), indent=1)       # display: colored sub-parts
    save_stl(union(list(wire_paths().values())), os.path.join(OUT, "models", "wire_paths.stl"))      # display only
    rows = check(parts, models, robot)
    bal = balance(parts, models)
    snap = snap_force()
    clicks = BP.detent_force()
    print(f"balance: {bal['mass_g']} g, center of mass x {bal['com'][0]} y {bal['com'][1]} z {bal['com'][2]}")
    print("panel snaps:", snap)
    print("platform clicks:", clicks)
    print("checks (mm^3, >0.05 shown):")
    for a, b, v in rows:
        if v > 0.05:
            print(f"  {a:34s} x {b:20s} {v:9.2f}")
    json.dump(dict(rows=rows, printing=printing, balance=bal, snap=snap, clicks=clicks),
              open(os.path.join(OUT, "checks.json"), "w"), indent=1)
    if fast:
        return
    from build123d import export_step
    os.makedirs(os.path.join(ROOT, "cad"), exist_ok=True)
    for f in ("pod_tray.step", "top_insert.step"):
        p = os.path.join(ROOT, "cad", f)
        if os.path.exists(p):
            os.unlink(p)
    for n in ("pod_body", "pod_panel", "pod_switch"):
        export_step(mesh_solid(parts[n], 0.02), os.path.join(ROOT, "cad", f"{n}.step"))
    export_assembly(os.path.join(ROOT, "cad", "assembly.step"), models)


if __name__ == "__main__":
    main(fast="fast" in sys.argv)
