"""Build site/: a home page with the package downloads, and a three.js viewer.

The viewer page is web/viewer.html. It goes to site/viewer/ with the
installed-frame STLs (site/viewer/models) and site/viewer/manifest.json.
It uses only the Python standard library and the committed package files,
so GitHub Actions runs it without the CAD tools. Preview with:
  python3 -m http.server 8800 --bind 0.0.0.0 --directory site
"""
import datetime
import json
import os
import shutil
import zipfile

PROJ = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(PROJ, "bittle_pi_addon")
SITE = os.path.join(PROJ, "site", "viewer")
MD = os.path.join(SITE, "models")

# id, label, group, source file, colour, explode offset (dx, dy, dz), extra transform
PARTS = [
    ("lid", "Pod lid", "Printed", "stl/installed/pod_lid.stl", "#9ea0a4", (0, 60, 0), None),
    ("top_insert", "Top vent insert (second color)", "Printed", "stl/installed/top_insert.stl", "#e8641b", (0, 75, 0), None),
    ("tray", "Pod tray", "Printed", "stl/installed/pod_tray.stl", "#cfd2d6", (0, 12, 0), None),
    ("cover", "Platform: cover with pegs", "Printed", "../bittle_platform/stl/installed/cover_pegs.stl", "#34363b", (0, 0, 0), None),
    ("pizero", "Raspberry Pi Zero 2 W", "Components", "stl/models/pizero.stl", "#2e9b4f", (0, 44, 0), None),
    ("pisugar", "PiSugar 2 board", "Components", "stl/models/pisugar2.stl", "#e06aa3", (0, 36, 0), None),
    ("battery", "1200 mAh cell", "Components", "stl/models/battery.stl", "#4a78d8", (0, 28, 0), None),
    ("amp", "NS4168 amp", "Components", "stl/models/amp_ns4168.stl", "#1f5f8f", (0, 26, 22), None),
    ("header", "BiBoard 5-pin header (est. height)", "Robot", "stl/models/biboard_header.stl", "#0d0d0d", (0, 0, 0), None),
    ("plugs", "Dupont plugs + wire space", "Components", "stl/models/dupont_plugs.stl", "#d83a34", (14, 16, 0), None),
    ("slot", "Cover slot passage (wires)", "Components", "stl/models/cover_slot.stl", "#0d0d0d", (0, 0, 0), None),
    ("shoulder_r", "Side shoulder R", "Robot", "../bittle_platform/reference/Bittle_SideShoulder.stl", "#f2a71c", (0, 0, 0), None),
    ("shoulder_l", "Side shoulder L", "Robot", "../bittle_platform/reference/Bittle_SideShoulder.stl", "#f2a71c", (0, 0, 0), "mirror_x"),
    ("front_plate", "Front plate", "Robot", "../bittle_platform/reference/Bittle_FrontPlate.stl", "#26272b", (0, 0, 0), None),
    ("rear_plate", "Rear plate", "Robot", "../bittle_platform/stl/robot/rear_plate.stl", "#26272b", (0, 0, 0), None),
    ("head", "Head (turns)", "Robot", "../bittle_platform/stl/robot/head.stl", "#3a3b40", (0, 0, 0), None),
    ("neck_mount", "Neck servo horn", "Robot", "../bittle_platform/stl/robot/neck_mount.stl", "#26272b", (0, 0, 0), None),
    ("hip_servos", "Hip servos", "Robot", "../bittle_platform/stl/robot/hip_servos.stl", "#26272b", (0, 0, 0), None),
    ("robot_battery", "Robot battery", "Robot", "../bittle_platform/stl/robot/battery.stl", "#4a4c52", (0, 0, 0), None),
    ("tail", "Tail (Petoi model)", "Robot", "../bittle_platform/stl/robot/tail.stl", "#3a3b40", (0, 0, 0), None),
] + [(f"{p}_{k}", f"{n} {k.upper()}", "Robot", f"../bittle_platform/stl/robot/{p}_{k}.stl", c, (0, 0, 0), None)
     for k in ("lf", "rf", "lr", "rr") for p, n, c in (("thigh", "Thigh", "#f2a71c"), ("shank", "Shank", "#2c2d31"))] + [
    ("speaker", "NULLLAB 3 W speaker (front)", "Components", "stl/models/speaker.stl", "#7a52b8", (0, 18, -34), None),
    ("mic", "SPH0645 mic (left)", "Components", "stl/models/mic_sph0645.stl", "#d83a34", (-24, 30, 0), None),
    ("camera_cable", "Camera cable (Grove) path", "Components", "stl/models/camera_cable.stl", "#3a9a3a", (-16, 8, 0), None),
]

# Text for the part card in the viewer: what the part is, how it attaches, downloads (relative to site/viewer/).
PF, AF = "../files/platform/", "../files/addon/"
INFO = {
    "cover": dict(text="The platform. It is the stock Petoi back cover with 4 pegs on its flat top, 24 x 16 mm on the center line. "
                       "The peg roots stop inside the 1.4 mm wall, so the inside of the cover does not change.",
                  attach="It goes on the robot in place of the stock cover.",
                  files=[("Print STL, with foot", PF + "cover_pegs_foot.stl"), ("Pegs STEP", PF + "pegs.step"),
                         ("Platform spec PDF", PF + "bittle_platform_spec.pdf")]),
    "tray": dict(text="The tray of the Pi add-on. It has 4 keyholes with spring beams, a slot base for the mic, two pins for the amp, "
                      "and a front wall with two pins for the speaker. It prints floor down without supports.",
                 attach="Put it on the pegs 7 mm forward of its place, then slide it 7 mm rearward until the beams click.",
                 files=[("Print STL", AF + "pod_tray.stl"), ("STEP", AF + "pod_tray.step")]),
    "lid": dict(text="The lid of the Pi add-on. It has a flat top and 45 deg chamfers, so it prints upside down without supports. "
                     "Two open port bays in the right side bring the wall in to the ports of the Pi and the PiSugar. "
                     "It has openings for the mic, the speaker and the camera cable, and a window for the top insert.",
                attach="Push it down onto the tray rim until the 4 snaps engage. Its lower edge then stops the tray from sliding forward.",
                files=[("Print STL", AF + "pod_lid.stl"), ("Build guide PDF", AF + "bittle_pi_addon_guide.pdf")]),
    "top_insert": dict(text="The vent panel in the top of the lid, printed in a second color. It sits flush on a 45 deg seat. "
                            "Four clips catch under a frame below the window.",
                       attach="Push it into the window in the lid top from outside until the 4 clips click. Push it out from inside to remove it.",
                       files=[("Print STL", AF + "top_insert.stl"), ("STEP", AF + "top_insert.step")]),
    "pizero": dict(text="Raspberry Pi Zero 2 W, on top of the PiSugar 2. Model: PiSugar (GPL-3.0).",
                   attach="It lies in the tray on the PiSugar 2, ports to the right side."),
    "pisugar": dict(text="PiSugar 2 battery board. Its charge port, button and switch face the right side. Model: PiSugar (GPL-3.0).",
                    attach="It is screwed under the Pi. Corner stops in the tray hold the stack."),
    "battery": dict(text="The 1200 mAh cell of the PiSugar 2.",
                    attach="It rests on two rails in the tray, above the peg heads."),
    "amp": dict(text="NULLLAB NS4168 I2S amp, on edge, crosswise behind the stack. Components face the rear.",
                attach="Push it onto the two teardrop pins of the post in the tray."),
    "speaker": dict(text="NULLLAB 3 W 4 ohm speaker. The sound goes out of the front grille of the lid. "
                         "It is the heaviest part after the Pi stack, so it is at the front to balance the add-on.",
                    attach="Hang the ear plate on the two pins of the front wall of the tray. Ribs in the lid hold it on."),
    "mic": dict(text="SPH0645 I2S mic board, on edge on the left side, away from the speaker. The port faces left to 7 holes in the lid.",
                attach="Push it down into the slot of the base. A stub in the lid holds its top edge."),
    "camera_cable": dict(text="The Grove cable of the Petoi AI Vision Module in the head. It goes through a slot in the left lid wall, "
                               "behind the speaker and over the tray rim, to the I2C pins of the Pi.",
                          attach="Put it through the slot before the lid goes on. Leave slack for the head to turn."),
    "header": dict(text="The 5-pin BiBoard header (GND, +5V, TX2, RX2) in the Pi slot of the cover. The height is an estimate.",
                   attach="It is part of the robot."),
    "plugs": dict(text="Straight Dupont plugs on the header and the space for their wires.",
                  attach="Push them onto the header before the lid goes on."),
    "slot": dict(text="The free space in the Pi slot of the cover. The wires use it.", attach=""),
    "shoulder_r": dict(text="Petoi side shoulder, right. Model: Petoi.", attach="Part of the robot."),
    "shoulder_l": dict(text="Petoi side shoulder, left (mirror). Model: Petoi.", attach="Part of the robot."),
    "front_plate": dict(text="Petoi front plate. Model: Petoi.", attach="Part of the robot."),
    "rear_plate": dict(text="Petoi rear plate, from the Petoi ROS model.", attach="Part of the robot."),
    "head": dict(text="The Petoi head on the neck servo. It turns about an axis 30 deg from vertical. "
                      "Use the Head turn slider or the Turn the head button to see it against the lid.", attach="Part of the robot."),
    "tail": dict(text="The Petoi tail (Bittle_tail.stl), at the rear of the cover. It is in the Petoi ROS model. "
                      "If your robot has the tail, it touches the rear of the lid.", attach="Part of the robot."),
    "robot_battery": dict(text="The robot battery under the body.", attach="Part of the robot."),
}

# Build steps: parts that appear, where they start (offset in mm) and where they stop.
STEPS = [
    dict(title="The robot", show=["shoulder_r", "shoulder_l", "front_plate", "rear_plate", "header", "head", "neck_mount", "hip_servos",
                                  "robot_battery", "tail"] + [f"{p}_{k}" for k in ("lf", "rf", "lr", "rr") for p in ("thigh", "shank")], view="iso",
         text="The Bittle X without its back cover: the head is at the front, the tail at the rear. The BiBoard header stands up at the right side."),
    dict(title="Fit the platform", view="iso", show=["cover"], start={"cover": [0, 40, 0]},
         text="Fit the platform cover in place of the stock cover. It has 4 pegs on its top."),
    dict(title="Put the tray on", view="iso", show=["tray"], start={"tray": [0, 35, -7]}, end={"tray": [0, 0, -7]},
         text="Put the tray on the pegs 7 mm forward of its place. The peg heads go through the large holes."),
    dict(title="Slide to lock", view="right", start={"tray": [0, 0, -7]},
         text="Push the tray 7 mm rearward. The spring beams in the floor click past bumps, and the peg heads hold the floor down."),
    dict(title="Mic", view="left", show=["mic"], start={"mic": [0, 30, 0]},
         text="Push the mic board down into the slot at the left side of the tray, port to the left."),
    dict(title="Amp", view="rear", show=["amp"], start={"amp": [0, 0, 22]},
         text="Push the amp onto its two pins behind the stack, components to the rear."),
    dict(title="Speaker", view="front", show=["speaker"], start={"speaker": [0, 0, -30]},
         text="Hang the speaker on the two pins of the front wall, ear plate to the rear."),
    dict(title="Pi stack", view="iso", show=["battery", "pisugar", "pizero"],
         start={"battery": [0, 40, 0], "pisugar": [0, 40, 0], "pizero": [0, 40, 0]},
         text="Put the Pi + PiSugar 2 stack into the tray, battery down, ports to the right."),
    dict(title="Wires", view="iso", show=["plugs", "slot", "camera_cable"], start={"plugs": [0, 20, 0], "camera_cable": [-25, 0, 0]},
         text="Push the Dupont plugs onto the BiBoard header. Route the wires over the Pi. Optional: put the camera cable in from the left side."),
    dict(title="Top insert", view="iso", show=["top_insert"], start={"top_insert": [0, 40, 0]},
         text="Push the vent insert into the window in the lid top until the 4 clips click."),
    dict(title="Lid", view="right", show=["lid"], start={"lid": [0, 45, 0], "top_insert": [0, 45, 0]},
         text="Push the lid down until the 4 snaps engage. The lid also stops the tray from sliding forward. "
              "The ports of the Pi and the PiSugar are in the two bays in the right side."),
]


def main():
    shutil.rmtree(SITE, ignore_errors=True)
    os.makedirs(MD, exist_ok=True)
    shutil.copy2(os.path.join(os.path.dirname(ROOT), "web", "viewer.html"), os.path.join(SITE, "index.html"))
    out = []
    copied = {}
    for pid, label, group, src, color, ex, tf in PARTS:
        path = os.path.join(ROOT, src)
        if not os.path.exists(path):
            print("missing", src)
            continue
        name = copied.get(src)
        if name is None:
            name = os.path.basename(os.path.dirname(src)) + "_" + os.path.basename(src)
            shutil.copy2(path, os.path.join(MD, name))
            copied[src] = name
        out.append(dict(id=pid, label=label, group=group, file="models/" + name,
                        color=color, explode=ex, transform=tf, **INFO.get(pid, {})))
    checks = json.load(open(os.path.join(ROOT, "stl", "checks.json")))["rows"]
    pi = json.load(open(os.path.join(PROJ, "bittle_platform", "interface.json")))
    E = pi["ENVELOPE"]
    meta = dict(
        title="Bittle X Pi Add-on v0.13 on Platform v1.3",
        envelope=dict(width=2 * E["half_w_low"], length=round(E["z"][1] - E["z"][0], 1), top=E["top"],
                      above_cover=round(E["top"] - pi["COVER_TOP"], 1)),
        bounds=dict(x=[-40, 40], z=[-70, 80], y=[-12, 70]),
        checks=[dict(a=a, b=b, v=round(v, 2)) for a, b, v in checks],
    )
    robot = json.load(open(os.path.join(PROJ, "bittle_platform", "stl", "robot", "robot.json")))
    robot["motion"] = json.load(open(os.path.join(ROOT, "stl", "motion.json")))
    json.dump(dict(parts=out, meta=meta, steps=STEPS, robot=robot), open(os.path.join(SITE, "manifest.json"), "w"), indent=1)
    print("site ready:", len(out), "parts")


# --------------------------------------------------------------------------
# Home page: the two packages with their downloads, and a link to the viewer
# --------------------------------------------------------------------------
HOME = os.path.join(PROJ, "site")
LEGAL = ["LICENSE.md", "ATTRIBUTION.md", "LICENSES"]
PACKAGES = [
    dict(key="platform", name="Bittle X Platform v1.3", dir="bittle_platform", zip="bittle_platform_v1.3.zip",
         pdf="bittle_platform_spec.pdf", img="doc/r2_starter.png",
         text="The stock Petoi Bittle X back cover with 4 pegs on its top. Add-ons drop onto the pegs, "
              "slide 7 mm rearward and click into place. No tools, glue or tape are necessary. "
              "The spec gives every number that you need to design an add-on.",
         extra=["interface.json"]),
    dict(key="addon", name="Bittle X Pi Add-on v0.13", dir="bittle_pi_addon", zip="bittle_pi_addon_v0.13.zip",
         pdf="bittle_pi_addon_guide.pdf", img="doc/02_ports_right.png", img2="doc/06_tray_loaded.png",
         text="A sample add-on for the platform: Raspberry Pi Zero 2 W, PiSugar 2 (1200 mAh), NS4168 amp with a 3 W speaker, "
              "and an SPH0645 mic. Three printed parts, all without supports.",
         extra=[]),
]


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def size(path):
    n = os.path.getsize(path)
    return f"{n / 1e6:.1f} MB" if n > 1e6 else f"{n / 1e3:.0f} kB"


def make_zip(P, path):
    """Zip of the package folder with the license files of the repository."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        base = os.path.join(PROJ, P["dir"])
        for d, dirs, files in os.walk(base):
            dirs[:] = sorted(x for x in dirs if x not in ("__pycache__", "tmp"))
            for f in sorted(files):
                if f == "assembly.step":      # local build output; the package has assembly_step.zip
                    continue
                full = os.path.join(d, f)
                z.write(full, os.path.join(P["dir"], os.path.relpath(full, base)))
        for item in LEGAL:
            full = os.path.join(PROJ, item)
            if os.path.isdir(full):
                for f in sorted(os.listdir(full)):
                    z.write(os.path.join(full, f), os.path.join(P["dir"], item, f))
            else:
                z.write(full, os.path.join(P["dir"], item))


def build_home():
    files = os.path.join(HOME, "files")
    shutil.rmtree(files, ignore_errors=True)
    for item in LEGAL:
        src, dst = os.path.join(PROJ, item), os.path.join(HOME, item)
        if os.path.isdir(src):
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    cards = []
    for P in PACKAGES:
        src = os.path.join(PROJ, P["dir"])
        dst = os.path.join(files, P["key"])
        os.makedirs(dst, exist_ok=True)
        links = []

        def put(rel, label, cls=""):
            name = os.path.basename(rel)
            if rel == P["zip"]:
                s_ = os.path.join(dst, name)
                make_zip(P, s_)
            else:
                s_ = os.path.join(src, rel)
                shutil.copy2(s_, os.path.join(dst, name))
            links.append(f'<a class="dl {cls}" href="files/{P["key"]}/{name}" download><span>{esc(label)}</span>'
                         f'<small>{esc(name)} &middot; {size(s_)}</small></a>')
        put(P["pdf"], "Specification (PDF)" if P["key"] == "platform" else "Build guide (PDF)", "primary")
        put(P["zip"], "Full package (zip)", "primary")
        for f in sorted(os.listdir(os.path.join(src, "stl", "print"))):
            put(os.path.join("stl", "print", f), f"Print: {f[:-4]}")
        for f in sorted(os.listdir(os.path.join(src, "cad"))):
            if f == "assembly_step.zip":
                put(os.path.join("cad", f), "CAD: full assembly (STEP, zipped)", "primary")
            elif f.endswith(".step") and f != "assembly.step":
                put(os.path.join("cad", f), f"CAD: {f[:-5]}")
        for f in P["extra"]:
            put(f, f"Data: {f}")
        imgs = [P["img"]] + ([P["img2"]] if P.get("img2") else [])
        figs = ""
        for im in imgs:
            name = os.path.basename(im)
            shutil.copy2(os.path.join(src, im), os.path.join(dst, name))
            figs += f'<img src="files/{P["key"]}/{name}" alt="{esc(P["name"])}" loading="lazy">'
        cards.append(f'''<section class="card">
  <div class="figs">{figs}</div>
  <div class="body">
    <h2>{esc(P["name"])}</h2>
    <p>{esc(P["text"])}</p>
    <div class="links">{"".join(links)}</div>
  </div>
</section>''')
    html = PAGE.replace("{{CARDS}}", "\n".join(cards)).replace("{{DATE}}", datetime.date.today().isoformat())
    open(os.path.join(HOME, "index.html"), "w").write(html)
    print("home ready")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bittle X Platform</title>
<style>
:root { --bg:#f6f5f2; --fg:#1d1d1f; --muted:#5f6368; --card:#ffffff; --line:#e3e1dc; --accent:#e8a317; --accent-fg:#1d1d1f; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#141416; --fg:#ececee; --muted:#a0a3a8; --card:#1e1f22; --line:#2f3035; --accent:#f2b632; --accent-fg:#141416; } }
:root[data-theme="dark"] { --bg:#141416; --fg:#ececee; --muted:#a0a3a8; --card:#1e1f22; --line:#2f3035; --accent:#f2b632; --accent-fg:#141416; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:1040px; margin:0 auto; padding:32px 16px 48px; }
header h1 { margin:0 0 6px; font-size:clamp(1.6rem, 4vw, 2.2rem); letter-spacing:-0.01em; }
header p { margin:0 0 20px; color:var(--muted); max-width:62ch; }
.viewer { display:inline-flex; align-items:center; gap:8px; padding:10px 16px; border-radius:10px; background:var(--accent); color:var(--accent-fg); font-weight:600; text-decoration:none; margin-bottom:28px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden; margin-bottom:24px; display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.1fr); }
.figs { display:grid; gap:1px; background:var(--line); }
.figs img { width:100%; height:100%; object-fit:cover; display:block; background:#f7f7f7; min-height:180px; }
.body { padding:20px 22px; }
.body h2 { margin:0 0 8px; font-size:1.3rem; }
.body p { margin:0 0 16px; color:var(--muted); }
.links { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:8px; }
.dl { display:flex; flex-direction:column; padding:9px 12px; border:1px solid var(--line); border-radius:9px; text-decoration:none; color:var(--fg); min-width:0; }
.dl:hover { border-color:var(--accent); }
.dl span { font-weight:600; font-size:0.93rem; }
.dl small { color:var(--muted); font-size:0.78rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dl.primary { border-color:var(--accent); }
footer { color:var(--muted); font-size:0.85rem; margin-top:12px; }
footer a { color:inherit; }
@media (max-width:760px) { .card { grid-template-columns:1fr; } .figs img { max-height:260px; } }
</style>
</head>
<body>
<main>
<header>
  <h1>Bittle X Platform</h1>
  <p>A peg platform on the stock Petoi Bittle X back cover, and a Raspberry Pi add-on that clicks onto it. Download the documents, the print files and the CAD below.</p>
</header>
<a class="viewer" href="viewer/">Open the 3D viewer &rarr;</a>
{{CARDS}}
<footer>Updated {{DATE}}. Code: MIT. Designs and documents: CC BY 4.0, Jeremy Collins.
The cover, side shoulder and front plate models are by <a href="https://github.com/PetoiCamp/NonCodeFiles">Petoi</a>, published without a stated license.
The Pi Zero and PiSugar 2 fit models are by <a href="https://github.com/PiSugar/PiSugar">PiSugar</a> (GPL-3.0).
See <a href="LICENSE.md">LICENSE.md</a> and <a href="ATTRIBUTION.md">ATTRIBUTION.md</a>.</footer>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
    build_home()
