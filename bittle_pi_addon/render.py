"""Render PNG views of the pod with OpenSCAD.

The model frame is Y-up. Every scene is wrapped in rotate([90,0,0]) so that
OpenSCAD shows it Z-up (front of the robot = +Y on screen axes).
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pod  # noqa: E402

ROOT = pod.ROOT
STL = pod.OUT
REF = pod.PREF
RDIR = os.path.join(ROOT, "doc")
TMP = os.path.join(ROOT, "stl", "tmp")

C = dict(
    lid="[0.98,0.74,0.10]", tray="[0.80,0.80,0.82]", cover="[0.20,0.20,0.22]",
    shoulder="[0.95,0.66,0.12]", plate="[0.13,0.13,0.14]", pizero="[0.16,0.55,0.28]",
    pisugar="[0.86,0.40,0.62]", battery="[0.30,0.48,0.85]", hdr="[0.05,0.05,0.05]",
     mic="[0.85,0.2,0.2]", amp="[0.10,0.35,0.55]", plugs="[0.85,0.20,0.20]", spk="[0.45,0.30,0.70]",
)


def imp(path, color, dy=0.0, dz=0.0, mirror=None):
    m = f"mirror({mirror}) " if mirror else ""
    return f'translate([0,{dy},{dz}]) {m}color({color}) import("{path}");\n'


def files(cut=None):
    """Return {name: path} for all scene meshes, optionally cut by a plane."""
    src = {
        "cover": f"{STL}/installed/cover_pegs.stl",
        "tray": f"{STL}/installed/pod_tray.stl",
        "lid": f"{STL}/installed/pod_lid.stl",
        "mic": f"{STL}/models/mic_sph0645.stl",
        "pizero": f"{STL}/models/pizero.stl",
        "pisugar": f"{STL}/models/pisugar2.stl",
        "amp": f"{STL}/models/amp_ns4168.stl",
        "plugs": f"{STL}/models/dupont_plugs.stl",
        "spk": f"{STL}/models/speaker.stl",
        "battery": f"{STL}/models/battery.stl",
        "hdr": f"{STL}/models/biboard_header.stl",
        "shoulder": f"{REF}/Bittle_SideShoulder.stl",
        "plate": f"{REF}/Bittle_FrontPlate.stl",
    }
    if not cut:
        return src
    os.makedirs(TMP, exist_ok=True)
    normal, off = cut
    out = {}
    for k, p in src.items():
        M = pod.mesh_to_manifold(pod.load_stl(p))
        parts = [M]
        if k == "shoulder":
            parts.append(M.transform(np.diag([-1.0, 1, 1, 1])[:3, :]))
        if k == "plate":
            parts.append(M.transform(np.diag([1.0, 1, -1, 1])[:3, :]))
        for i, P in enumerate(parts):
            Q = P.trim_by_plane(normal, off)
            if Q.is_empty():
                continue
            path = f"{TMP}/{k}_{i}_{abs(hash((tuple(normal), off))) % 10**6}.stl"
            pod.save_stl(Q, path)
            out[f"{k}#{i}"] = path
    return out


def scene(show, cut=None, explode=0.0, robot=True):
    f = files(cut)
    s = ""
    for key, path in f.items():
        k = key.split("#")[0]
        if k not in show:
            continue
        dy = 0.0
        if explode:
            dy = {"lid": 3.4, "pizero": 1.6, "pisugar": 1.6, "battery": 1.6,
                  "amp": 1.6, "plugs": 0.0, "spk": 1.6, "tray": 0.5, "mic": 1.6}.get(k, 0.0) * explode
        if cut:
            s += imp(path, C[k], dy=dy)
        else:
            s += imp(path, C[k], dy=dy)
            if k == "shoulder" and robot:
                s += imp(path, C[k], mirror="[1,0,0]")
            if k == "plate" and robot:
                s += imp(path, C[k], mirror="[0,0,1]")
    return f"rotate([90,0,0]) {{\n{s}}}\n"


def render(name, scad, cam, size=(1400, 1000), ortho=False):
    os.makedirs(RDIR, exist_ok=True)
    src = os.path.join(RDIR, name + ".scad")
    png = os.path.join(RDIR, name + ".png")
    open(src, "w").write(scad)
    args = ["openscad", "-o", png, f"--imgsize={size[0]},{size[1]}", f"--camera={cam}",
            "--colorscheme=Tomorrow", "--backend=manifold"]
    if ortho:
        args.append("--projection=o")
    r = subprocess.run(args + [src], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
    os.unlink(src)
    return png


ALL = ["cover", "tray", "lid", "mic", "pizero", "pisugar", "battery", "hdr", "plugs", "amp", "spk", "shoulder", "plate"]
NOLID = [k for k in ALL if k != "lid"]
ROBOT = ["cover", "shoulder", "plate"]

JOBS = {
    # name: (show, cut, explode, camera, ortho)
    "02_ports_right": (ALL, None, 0, "0,-17.0,8,62,0,128,300", False),
    "06_tray_loaded": (NOLID, None, 0, "0,-17.0,8,52,0,220,280", False),
    "08_section_center": (ALL, ((-1.0, 0, 0), 0.0), 0, "0,-9.0,6,90,0,90,280", True),
}


def main(which=None):
    for name, (show, cut, ex, cam, ortho) in JOBS.items():
        if which and not any(w in name for w in which):
            continue
        print(render(name, scene(show, cut, ex), cam, ortho=ortho))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
