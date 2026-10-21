"""Clearance check for the wide feet (wide_foot_part.scad styles A-D) against the Bittle's own parts.

Run:  ../.venv/bin/python foot_clearance.py
The robot is posed with bittle_platform/robot.py (angles in degrees from the standing pose, + = toward the head).
The pad moves with its shank. Three checks, each against the stock shank as the baseline:
  1. pad vs the body and the thigh, over a hip x knee grid (a pose counts only if the stock foot does not collide there)
  2. pad vs the front/rear pad on the same side, as the legs swing toward each other (hip swing +a on the rear leg
     and -a on the front leg)
  3. pad vs the other leg's shank on the same side, same swing
There is no gait table in this repository. The hip and knee ranges below are assumptions: set WALK_HIP and
WALK_KNEE to the angles of the gait you use.
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
import manifold3d as m3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "bittle_platform"))
import meshutil as MU      # noqa: E402
import robot as RB         # noqa: E402

OPENSCAD = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
WALK_HIP = range(-30, 31, 10)
WALK_KNEE = range(-30, 31, 10)
SWING = range(0, 61, 5)
FOOT_X, FOOT_BOTTOM, FOOT_Z = 34.1, -87.1 - 3, 53.1     # foot center and the lowest Y of the stock shank (wide_feet.scad)
STYLES = sys.argv[1] if len(sys.argv) > 1 else "EFG"      # e.g. python foot_clearance.py EFG


def pad_mesh(style, tmp):
    out = os.path.join(tmp, f"foot_{style}.stl")
    subprocess.run([OPENSCAD, "-o", out, "-D", f'style="{style}"', os.path.join(HERE, "wide_foot_part.scad")],
                   check=True, capture_output=True)
    return MU.load_stl(out)


def place(tris, k):
    """The pad in the standing pose for leg k (lf, rf, lr, rr), from the local frame of wide_foot_part.scad."""
    side = -1 if k[0] == "l" else 1
    fz = -FOOT_Z if k[1] == "f" else FOOT_Z
    v = tris.reshape(-1, 3)
    p = np.stack([side * (FOOT_X + v[:, 0]), FOOT_BOTTOM + v[:, 2], fz - v[:, 1]], axis=1)
    t = p.reshape(-1, 3, 3)
    if side < 0:                       # the mirror flips the triangle winding
        t = t[:, ::-1, :]
    return MU.mesh_to_manifold(t)


def hit(a, b, tol=0.3):
    return (a ^ b).volume() > tol


def main():
    R = RB.Robot()
    body = R.parts["rear_plate"] + R.parts["neck_mount"]
    body += MU.mesh_to_manifold(MU.load_stl(os.path.join(ROOT, "bittle_platform", "stl", "installed", "cover_pegs.stl")))
    fp = MU.load_stl(os.path.join(ROOT, "bittle_platform", "reference", "Bittle_FrontPlate.stl"))
    sh = MU.load_stl(os.path.join(ROOT, "bittle_platform", "reference", "Bittle_SideShoulder.stl"))
    body += MU.mesh_to_manifold(fp) + MU.mesh_to_manifold(sh) + MU.mesh_to_manifold(sh[:, ::-1, :] * np.array([-1, 1, 1]))
    with tempfile.TemporaryDirectory() as tmp:
        pads = {s: pad_mesh(s, tmp) for s in STYLES}
        for style in STYLES:
            print(f"\n=== style {style} ===")
            # 1. pad vs the body and the thigh, over the walking grid, left front and left rear legs
            for k in ("lf", "lr"):
                P = place(pads[style], k)
                th, sk = R.parts[f"thigh_{k}"], R.parts[f"shank_{k}"]
                bad = []
                for a in WALK_HIP:
                    for b in WALK_KNEE:
                        ang = {f"hip_{k}": a, f"knee_{k}": b}
                        Pm = P.transform(R.matrix(f"shank_{k}", ang))
                        Tm = th.transform(R.matrix(f"thigh_{k}", ang))
                        Sm = sk.transform(R.matrix(f"shank_{k}", ang))
                        base = hit(Sm, body) or hit(Sm, Tm)
                        if (hit(Pm, body) or hit(Pm, Tm)) and not base:
                            bad.append((a, b))
                print(f"  {k}: {len(bad)} of {len(WALK_HIP) * len(WALK_KNEE)} grid poses collide with the body or thigh"
                      + (f", e.g. hip/knee {bad[:4]}" if bad else ""))
            # 2 and 3. front and rear leg on the same side swing toward each other
            for side in ("l", "r"):
                f, r = side + "f", side + "r"
                Pf, Pr = place(pads[style], f), place(pads[style], r)
                Sf, Sr = R.parts[f"shank_{f}"], R.parts[f"shank_{r}"]
                first = None
                for a in SWING:
                    Mf = R.matrix(f"shank_{f}", {f"hip_{f}": -a, f"knee_{f}": 0})
                    Mr = R.matrix(f"shank_{r}", {f"hip_{r}": +a, f"knee_{r}": 0})
                    pf, pr = Pf.transform(Mf), Pr.transform(Mr)
                    if hit(pf, pr) or hit(pf, Sr.transform(Mr)) or hit(pr, Sf.transform(Mf)):
                        first = a
                        break
                print(f"  {side} side, legs swinging toward each other: "
                      + (f"first contact at {first} deg each" if first is not None else f"no contact up to {SWING[-1]} deg each"))
        # the stock foot, same test, as the baseline
        print("\n=== stock feet, same swing test ===")
        for side in ("l",):
            f, r = side + "f", side + "r"
            Sf, Sr = R.parts[f"shank_{f}"], R.parts[f"shank_{r}"]
            first = None
            for a in SWING:
                Mf = R.matrix(f"shank_{f}", {f"hip_{f}": -a, f"knee_{f}": 0})
                Mr = R.matrix(f"shank_{r}", {f"hip_{r}": +a, f"knee_{r}": 0})
                if hit(Sf.transform(Mf), Sr.transform(Mr)):
                    first = a
                    break
            print(f"  {side} side: " + (f"first contact at {first} deg each" if first is not None else f"no contact up to {SWING[-1]} deg each"))


if __name__ == "__main__":
    main()
