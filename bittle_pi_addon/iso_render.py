"""Line-art PNGs of the add-on in the style of the beetlebug.org explode viewer, light and dark.

Run after pod.py:  python iso_render.py [name ...]
  doc/iso/<name>-light.png, doc/iso/<name>-dark.png   transparent background
  hero          the finished build on the robot
  exploded      every part out of the open top (pod.py explode_plan)
  stepNN        one figure per step of the build guide (guide.py STEPS): the parts of the step in the accent,
                exploded along their insert direction, with a dashed guide line from their place
  top, open, wires, camera_low   figures for README.md and the site home page
The page iso/render.html draws each figure with three.js (iso/node_modules, from iso/package.json: npm install)
and the look of web/lineart.js, which the viewer also uses. Headless Chromium runs the page.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, PROJ)
import build_site as BS   # noqa: E402  (part list, finishes, tags; standard library only)
import guide              # noqa: E402  (the build steps)
import pod                # noqa: E402
from bittle_platform import interface as PI   # noqa: E402

OUT = os.path.join(HERE, "doc", "iso")
THEMES = ("light", "dark")

# View directions in the Y-up model frame (X right, Y up, +Z rear). The site uses (1.3, 1.5, 1.0) in its Z-up frame
# for this project: from the front right, above.
ISO = (1.3, 1.0, -1.5)
DIRS = dict(iso=ISO, high=(1.0, 1.9, -1.3), rear=(0.7, 1.9, -1.4), mic=(-1.0, 1.7, 0.9), amp=(-1.4, 1.8, -0.5),
            well=(-1.5, 1.25, 0.35), front_left=(-1.2, 1.6, -1.1), top=(0.35, 2.4, -0.9))


# --------------------------------------------------------------------------
# Parts: the viewer part list (build_site.py) and the head-off camera parts
# --------------------------------------------------------------------------
def part_table():
    parts = {}
    for pid, label, group, src, color, ex, tf in BS.PARTS:
        path = os.path.normpath(os.path.join(HERE, src))
        if os.path.exists(path):
            parts[pid] = dict(file=os.path.relpath(path, PROJ), finish=BS.finish(pid, group), tag=BS.tag(pid, label),
                              transform=tf, explode=ex)
    low = dict(camera_base_low=("stl/installed/pod_camera_base_low.stl", "print", "Head-off base"),
               camera_cradle_low=("stl/installed/pod_camera_cradle_low.stl", "print", "Cradle"),
               camera_low_pins=("stl/models/camera_low_pins.stl", "buy", "Pins"),
               camera_low=("stl/models/camera_low.stl", "dark", "Camera"),
               wires_camera_low=("stl/models/wires_camera_low.stl", "dark", "USB cable"))
    for pid, (src, fin, t) in low.items():
        parts[pid] = dict(file=os.path.relpath(os.path.join(HERE, src), PROJ), finish=fin, tag=t, transform=None, explode=None)
    return parts


PARTS = part_table()
ROBOT = [p[0] for p in BS.PARTS if p[2] == "Robot" and not p[0].startswith("biboard_header")]
TRUNK = ["shoulder_r", "shoulder_l", "front_plate", "rear_plate", "biboard_header__header"]
PRINTED = ["cover", "body", "panel", "button", "logo_white", "logo_red", "camera_mount"]
INSIDE = [k for k in PARTS if "__" in k and not k.startswith(("camera__", "wires_camera", "biboard_header"))]
CAMERA = ["camera__case", "wires_camera__usb", "wires_camera__plug_cam", "wires_camera__plug_pi"]
ALL = ROBOT + PRINTED + ["biboard_header__header"] + INSIDE + CAMERA
PANEL = ["panel", "button", "logo_white", "logo_red"]


def ids(keys):
    """guide.py part keys to viewer ids (the guide uses one shoulder and one plate mesh, mirrored)."""
    out = []
    for k in keys:
        out += dict(shoulder=["shoulder_r", "shoulder_l"], plate=["front_plate", "rear_plate"]).get(k, [k])
    return [k for k in out if k in PARTS]


# --------------------------------------------------------------------------
# The build steps (guide.py): how each step moves its parts in, and the view
# --------------------------------------------------------------------------
UP = lambda h, back=0.0: (0.0, h, back)      # noqa: E731  up h mm, back mm toward the rear (+Z)
TWIST_PIVOT = (-pod.TW["c"][0], 0.0, pod.TW["c"][1])   # the socket axis in the robot frame (pod.py designs with X turned over)
TWIST = abs(pod.TW["twist"])                              # the mount goes in turned this far counterclockwise (from above)

# title: (offset of the new parts, view, extra moving parts, ghost the body, show the robot trunk)
MOVES = {
    "Fit the platform cover": (UP(45), "iso", [], False, True),
    "Click the body on": (UP(40, PI.SLIDE), "iso", [], False, True),
    "Speaker": (UP(45), "rear", [], False, True),
    "Mic": (UP(42), "mic", [], False, True),
    "Amp and speaker lead": (UP(48), "amp", [], False, True),
    "Pi + PiSugar 2 stack": (UP(55), "high", [], False, True),
    "Splices (BCLK and LRCLK)": (UP(34), "well", [], True, False),
    "BiBoard jumpers: Pi ends": (UP(34), "well", [], True, False),
    "Amp cable": (UP(34), "well", [], True, False),
    "Mic jumpers": (UP(34), "well", [], True, False),
    "BiBoard ends": (UP(34), "front_left", [], True, False),
    "Button cap and logo": (UP(18), "iso", [], False, False),
    "Panel": (UP(40, pod.LID_SLIDE), "iso", ["button", "logo_white", "logo_red"], False, True),
    "Camera mount": (UP(40), "iso", [], False, True),
    "Camera and USB cable": (UP(55), "iso", [], False, True),
}
# One tag for all the parts of a step (else one tag for each name)
STEP_TAG = {"Mic": "Mic", "Pi + PiSugar 2 stack": "Pi + PiSugar 2", "Panel": "Top panel"}


def step_jobs():
    guide.build_steps()
    jobs = []
    for i, s in enumerate(guide.STEPS, 1):
        off, view, extra, ghost, trunk = MOVES[s["title"]]
        before, new = ids(s["before"]), ids(s["new"])
        if s["title"] == "Button cap and logo":       # the panel alone, the cap and the inlays over it
            before, new = ["panel"], ["button", "logo_white", "logo_red"]
        move = new + [k for k in extra if k not in new]
        show = [k for k in dict.fromkeys(before + new) if trunk or k not in TRUNK]
        if not trunk:
            show = [k for k in show if k not in ("shoulder_r", "shoulder_l", "front_plate", "rear_plate")]
        job = dict(name=f"step{i:02d}", show=show, focus=move, offset={k: off for k in move},
                   ghost=["body"] if ghost else [], dir=DIRS[view], width=2000, height=1250)
        if s["title"] in STEP_TAG:
            job["tag"] = {k: STEP_TAG[s["title"]] for k in move}
        if "camera_mount" in move:
            job["turn"] = {"camera_mount": TWIST}
            job["pivot"] = {"camera_mount": list(TWIST_PIVOT)}
        if ghost:                                    # wire steps: fit to the body and the wires
            job["frame"] = ["body"] + move
        jobs.append(job)
    return jobs


def figure_jobs():
    ex = {}
    for k in ALL:
        e = PARTS[k]["explode"]
        if e:
            ex[k] = [a + b for a, b in zip(e[1], e[2])]
    open_ = ROBOT + ["cover", "body", "biboard_header__header"] + INSIDE
    low = ([k for k in ROBOT if k not in ("head", "neck_mount")] + [k for k in PRINTED if k != "camera_mount"] +
           ["biboard_header__header"] + INSIDE + ["camera_base_low", "camera_cradle_low", "camera_low_pins", "camera_low", "wires_camera_low"])
    return [
        dict(name="hero", show=ALL, dir=ISO, width=1500, height=2000),
        dict(name="exploded", show=ALL, offset=ex, dir=ISO, width=1600, height=2200),
        dict(name="top", show=[k for k in ALL if k not in ROBOT], dir=DIRS["top"], width=1600, height=1300,
             frame=["body", "panel", "camera_mount", "camera__case", "wires_camera__usb"]),
        dict(name="open", show=open_, dir=ISO, width=1600, height=1600),
        dict(name="wires", show=["cover", "body"] + INSIDE, ghost=["body"], dir=DIRS["well"], width=1600, height=1300,
             frame=["body"]),
        dict(name="camera_low", show=low, dir=ISO, width=1500, height=1800),
    ]


# --------------------------------------------------------------------------
# Render: a local server for the page, the STLs and the PNGs it posts back
# --------------------------------------------------------------------------
def run(jobs):
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(os.path.join(HERE, "iso", "node_modules", "three")):
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=os.path.join(HERE, "iso"), check=True)
    full = []
    for j in jobs:
        for t in THEMES:
            full.append(dict(j, name=f"{j['name']}-{t}", theme=t, tag_scale=3.0))
    cfg = json.dumps(dict(parts=PARTS, jobs=full)).encode()
    done = threading.Event()
    saved = []

    class H(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=PROJ, **k)

        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path == "/iso/jobs.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(cfg)))
                self.end_headers()
                self.wfile.write(cfg)
                return
            super().do_GET()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n)
            if self.path.startswith("/iso/save/"):
                name = os.path.basename(self.path)
                path = os.path.join(OUT, name)
                open(path, "wb").write(body)
                saved.append(path)
            elif self.path == "/iso/done":
                done.set()
            self.send_response(204)
            self.end_headers()

        def guess_type(self, path):
            return "text/javascript" if path.endswith(".js") else super().guess_type(path)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/bittle_pi_addon/iso/render.html"
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    prof = tempfile.mkdtemp(prefix="iso_chrome_")
    p = subprocess.Popen([chrome, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist",
                          "--no-first-run", "--no-default-browser-check", f"--user-data-dir={prof}", "--remote-debugging-port=0",
                          "--window-size=800,600", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ok = done.wait(timeout=60 + 20 * len(full))
    finally:
        p.terminate()
        p.wait(timeout=20)
        srv.shutdown()
        shutil.rmtree(prof, ignore_errors=True)
    if not ok:
        raise SystemExit(f"iso render timed out after {len(saved)} of {len(full)} images")
    crop(saved)
    return saved


def crop(paths, margin=24):
    """Cut each PNG to its drawn area plus a margin (the background is transparent)."""
    from PIL import Image
    for path in paths:
        im = Image.open(path)
        box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
        if box:
            x0, y0, x1, y1 = box
            im.crop((max(x0 - margin, 0), max(y0 - margin, 0), min(x1 + margin, im.width), min(y1 + margin, im.height))).save(path, optimize=True)


def main(which=None):
    jobs = figure_jobs() + step_jobs()
    if which:
        jobs = [j for j in jobs if any(w in j["name"] for w in which)]
    for p in run(jobs):
        print(os.path.relpath(p, HERE))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
