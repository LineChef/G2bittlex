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
    ("panel", "Top panel (second color)", "Printed", "stl/installed/pod_panel.stl", "#e8641b", (0, 45, 0), None),
    ("switch", "Power switch slider", "Printed", "stl/installed/pod_switch.stl", "#f2f2ef", (0, 52, 0), None),
    ("button", "Button cap", "Printed", "stl/installed/pod_button.stl", "#f2f2ef", (0, 52, 0), None),
    ("camera_mount", "Camera mount", "Printed", "stl/installed/pod_camera_mount.stl", "#e8641b", (0, 70, 0), None),
    ("body", "Add-on body", "Printed", "stl/installed/pod_body.stl", "#f2f2ef", (0, 10, 0), None),
    ("cover", "Platform: cover with pegs", "Printed", "../bittle_platform/stl/installed/cover_pegs.stl", "#34363b", (0, 0, 0), None),
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
     for k in ("lf", "rf", "lr", "rr") for p, n, c in (("thigh", "Thigh", "#f2a71c"), ("shank", "Shank", "#2c2d31"))]

# Electronics and wires: colored sub-parts from pod.py (stl/models/parts.json). ALIAS: pod.py model -> viewer id.
ALIAS = dict(camera="camera", pizero="pizero", pisugar2="pisugar", battery="battery", sd_card="sd_card", pi_plugs="pi_plugs", amp_ns4168="amp",
             speaker="speaker", mic_sph0645="mic", biboard_header="header", biboard_plug="bb_plug")
# Exploded view (pod.py explode_plan): a stage (reverse build order), a lift out of the open top, then a move aside.
EXPLODE = json.load(open(os.path.join(ROOT, "stl", "explode.json")))
PARTS = [p[:5] + (EXPLODE["parts"].get(os.path.basename(p[3])[:-4]),) + p[6:] for p in PARTS]
GROUPS = {}
for _d in json.load(open(os.path.join(ROOT, "stl", "models", "parts.json"))):
    _a = ALIAS.get(_d["model"], "wires")
    _id = _d["model"] + "__" + _d["sub"]
    GROUPS.setdefault(_a, []).append(_id)
    PARTS.append((_id, _d["label"][0].upper() + _d["label"][1:], "Robot" if _a == "header" else "Wires" if _a == "wires" else "Components",
                  "stl/" + _d["file"], _d["color"], _d.get("explode"), None))


def expand(ids):
    """Viewer ids of a step: a model name stands for all its sub-parts."""
    out = []
    for i in ids:
        out += GROUPS.get(i, [i])
    return out


# Text for the part card in the viewer: what the part is, how it attaches, downloads (relative to site/viewer/).
PF, AF = "../files/platform/", "../files/addon/"
INFO = {
    "cover": dict(text="The platform. It is the stock Petoi back cover with 4 teardrop pegs on its flat top, 24 x 20 mm on the center line. "
                       "The keyholes in an add-on have the same teardrop shape, so the add-on goes on one way only. "
                       "The peg roots stop inside the 1.4 mm wall, so the inside of the cover does not change.",
                  attach="It goes on the robot in place of the stock cover.",
                  files=[("Print STL, with foot", PF + "cover_pegs_foot.stl"), ("Pegs STEP", PF + "pegs.step"),
                         ("Platform spec PDF", PF + "bittle_platform_spec.pdf")]),
    "body": dict(text="The body of the Pi add-on: one rounded box with a flat floor. The floor has the 4 teardrop keyholes, each with two "
                      "spring beams that center the peg. Inside: grooves for the speaker, the Pi stack and the mic, and a slot bar for the amp. "
                      "The BiBoard header comes up through a notch in the floor, in the right well. "
                      "It prints floor down without supports.",
                 attach="Click it on empty: put it on the pegs 7 mm behind its place, grille to the rear, then slide it 7 mm forward until it clicks. "
                        "To remove it, unplug the BiBoard plug, then slide it 7 mm rearward and lift it.",
                 files=[("Print STL", AF + "pod_body.stl"), ("STEP (mesh)", AF + "pod_body.step")]),
    "panel": dict(text="The top panel, in a second color. It has the soft top edge and openings shaped to each plug body. "
                       "A spring tongue over the PiSugar button is a large button. "
                       "Four spring tabs click into pockets in the front and rear walls. Forks under it hold the Pi stack, the speaker and the amp down. "
                       "It prints upside down on its top without supports.",
                  attach="Push it straight down until the 4 tabs click (about 9 N). It fits one way only. "
                         "To open, lift the rear edge at the finger notch (about 8 N), then the front.",
                  files=[("Print STL", AF + "pod_panel.stl"), ("STEP (mesh)", AF + "pod_panel.step"),
                         ("Build guide PDF", AF + "bittle_pi_addon_guide.pdf")]),
    "switch": dict(text="A large slider for the small PiSugar 2 power switch. Its tab stands 2 mm out of a slot in the panel. "
                        "Its body rides in two dovetail rails under the panel; a fork goes over the switch lever. 2 mm of travel each way: the switch sets the end positions.",
                   attach="Put it into the rails at their rear end (no lips there) and slide it forward until it clicks, before the panel goes on.",
                   files=[("Print STL", AF + "pod_switch.stl")]),
    "button": dict(text="The white button cap for the PiSugar button. It slides onto the spring tongue in the panel along a 45 deg dovetail "
                        "and clicks over a small bump. Press it: the tongue and the arm under it press the PiSugar button.",
                   attach="Slide it onto the tongue from the slit end until it clicks, before the panel goes on.",
                   files=[("Print STL", AF + "pod_button.stl")]),
    "camera_mount": dict(text="The camera mount: a 2 mm base on the front of the panel with a chin over its front edge, two U brackets that hold "
                              "the ends of the camera case (outside the width of the head), and two clip legs through a window in the panel. "
                              "A 45 deg ridge on each bracket snaps into the pocket in each end of the case. It stays clear of the HDMI opening and the switch.",
                         attach="Push its two clip legs down through the window in the panel until they click. Then push the camera case down into the brackets until it clicks.",
                         files=[("Print STL", AF + "pod_camera_mount.stl")]),
    "camera": dict(text="The Petoi AI Vision Module in its Petoi case, upright on the front of the add-on, lens forward over the head (15 g). "
                        "It is upside down, so that its Grove socket is on the left, clear of the HDMI opening: turn the image 180 deg in software. "
                        "A 10 cm Grove cable goes from the socket down through a slot in the panel to the Grove plug on the BiBoard.",
                   attach="Push it down into the brackets of the camera mount until it clicks, lens forward. Then plug the Grove cable into the socket in its rear face."),
    "pizero": dict(text="Raspberry Pi Zero 2 W, on its long edge: ports up, GPIO header down, SD card to the front. Model: PiSugar (GPL-3.0).",
                   attach="With the PiSugar 2 it slides down into the grooves of the two end posts."),
    "pisugar": dict(text="PiSugar 2 battery board. Its charge port, button and switch are at the top. Model: PiSugar (GPL-3.0).",
                    attach="It is screwed to the Pi. The two boards go into the end grooves together."),
    "battery": dict(text="The 1200 mAh cell of the PiSugar 2, on the left side of the stack.",
                    attach="It is fixed to the PiSugar 2. It stands 1.5 mm above the peg heads."),
    "pi_plugs": dict(text="The soldered 2x20 Pi header with Dupont housings on the 12 pins in use (pin map: the wiring blueprint).",
                     attach="Push the jumpers onto the Pi header before the stack goes in."),
    "amp": dict(text="NULLLAB NS4168 I2S amp, on edge along the left wall. Its parts face the battery.",
                attach="Push its bottom edge down into the slot of the bar on the floor. Forks under the panel hold its top edge."),
    "speaker": dict(text="NULLLAB 3 W 4 ohm speaker at the rear. The sound goes out of the grille in the rear face.",
                    attach="Push the ends of the ear plate down into the two side grooves, body to the rear."),
    "mic": dict(text="SPH0645 I2S mic board at the front wall, away from the speaker. The port faces 7 holes in the front face. "
                     "A right-angle header along its right edge points into the right well.",
                attach="Plug the six jumpers onto its header, then push it down into its groove and slot, port to the front."),
    "header": dict(text="The 5-pin BiBoard header (TX2, RX2, GND, +5V, +5V) in the Pi slot of the cover. The height is an estimate.",
                   attach="It is part of the robot."),
    "bb_plug": dict(text="Three straight Dupont plugs on the BiBoard header (TX2, RX2, GND), inside the right wall. +5V is not wired.",
                    attach="Plug it in from the top after the body is on the robot (the panel is off)."),
    "sd_card": dict(text="The microSD card. About 2.5 mm of it stands out of the holder at the front end of the Pi (not measured).",
                    attach="To change it, lift the stack out."),
    "wires": dict(text="The jumper wires (1.4 mm), on the routes that pod.py checks: no wire touches a printed part or another board. "
                       "BCLK (pin 12) and LRCLK (pin 35) each go to a soldered splice (black sleeve) and on to the mic and the amp. "
                       "The jumpers are longer than shown: fold the slack into the right well.",
                  attach="Each jumper goes from its Pi header pin to the part. See the wiring table in the guide."),
    "wire_paths": dict(text="The free paths for the wires: the BiBoard wires in the right well, the I2S wires under the stack to the amp, "
                            "the mic wires over the mic, the speaker wires over the amp, and the camera cable from the right notch. "
                            "The check in pod.py keeps every part out of them.",
                       attach="Lay the wires in these paths before the panel goes on."),
    "shoulder_r": dict(text="Petoi side shoulder, right. Model: Petoi.", attach="Part of the robot."),
    "shoulder_l": dict(text="Petoi side shoulder, left (mirror). Model: Petoi.", attach="Part of the robot."),
    "front_plate": dict(text="Petoi front plate. Model: Petoi.", attach="Part of the robot."),
    "rear_plate": dict(text="Petoi rear plate, from the Petoi ROS model.", attach="Part of the robot."),
    "head": dict(text="The Petoi head on the neck servo. It turns about an axis 30 deg from vertical. "
                      "Use the Head turn slider or the Turn the head button to see it against the add-on.", attach="Part of the robot."),
    "tail": dict(text="The Petoi tail (Bittle_tail.stl), at the rear of the cover. It is in the Petoi ROS model. "
                      "It is 3.2 mm under the add-on, and 0.05 mm at the drop-on place.", attach="Part of the robot."),
    "robot_battery": dict(text="The robot battery under the body.", attach="Part of the robot."),
}

# One build step for each wire (the plug order of the guide, stl/wires.json)
WIRES = json.load(open(os.path.join(ROOT, "stl", "wires.json")))
_W = {(w["group"], w["wire"]): (i, w) for i, w in enumerate(WIRES["wires"], 1)}


STACK = ["battery", "pisugar", "pizero", "sd_card", "pi_plugs"]


def _wire_step(key, title=None, text=""):
    """One wire step. The wire comes in with its Dupont housings; a wire laid before (the amp cable) or a housing
    plugged before (the mic end) is already in place and only glows."""
    i, w = _W[key]
    laid = key[0] == "amp"
    new = [h for h in w["housings"] if not h.endswith("_dev") or key[0] != "mic"]
    if not laid:
        new = [w["id"]] + new
    glow = [w["id"]] + list(w["housings"])
    if w.get("pack"):
        text = text or f"Plug a 10 cm jumper from {w['from']} to the Pi {w['to']}. Lay its excess in {('an' if w['slack'][0] in 'aeiou' else 'a')} {w['slack']} as shown."
    return dict(title=title or f"{w['from']} \u2192 {'Pi ' if w['to'].startswith('pin') else ''}{w['to']}", view="build" if laid else "wires",
                show=new, highlight=glow, ghost=["body", "panel"] + (STACK[:4] if laid else []), start={k: [0, 22, 0] for k in new},
                text=(text or f"Plug {w['from']} onto the Pi {w['to']}.") + f" (Wire {i} in the route table of the guide.)")


CAM_CABLE = [f"wires_camera__{k}" for k in ("scl", "sda", "vcc", "gnd", "plug_bb")]
AMP_CABLE = [_W[("amp", k)][1]["id"] for k in ("G", "V", "BCLK", "LRC", "DIN")]
MIC_ENDS = [h for w in WIRES["wires"] if w["group"] == "mic" for h in w["housings"] if h.endswith("_dev")]
SPLICE_IDS = ["wires_splice__sleeves", "wires_splice__bclk", "wires_splice__bclk_pi", "wires_splice__lrclk", "wires_splice__lrclk_pi"]

WIRE_STEPS = [_wire_step(tuple(k)) for k in WIRES["order"] if tuple(k)[0] == "uart"] + [
    _wire_step(("amp", "G"), text="Amp cable G: from the floor in front of the front pegs, in the outer lane of the right well, onto Pi pin 14."),
    _wire_step(("amp", "V"), text="Amp cable V: up from the floor onto Pi pin 2 (5V)."),
    _wire_step(("amp", "DIN"), text="Amp cable DIN: rearward in the inner lane, onto Pi pin 40."),
    dict(title="Splices", view="wires", ghost=["body", "panel"], highlight=SPLICE_IDS + ["wires_amp__bclk", "wires_amp__lrc"],
         show=SPLICE_IDS, start={k: [0, 22, 0] for k in SPLICE_IDS},
         text="The BCLK and LRCLK splices: a short wire from Pi pin 12 (35) and the amp cable BCLK (LRC) go into the bottom of each sleeve. "
              "The BCLK splice stands in front of the BiBoard notch, the LRCLK splice beside the BiBoard plugs."),
] + [_wire_step(tuple(k)) for k in WIRES["order"] if tuple(k)[0] == "mic"]

# Build steps: parts that appear, where they start (offset in mm) and where they stop.
STEPS = [
    dict(title="The robot", show=["shoulder_r", "shoulder_l", "front_plate", "rear_plate", "header", "head", "neck_mount", "hip_servos",
                                  "robot_battery", "tail"] + [f"{p}_{k}" for k in ("lf", "rf", "lr", "rr") for p in ("thigh", "shank")], view="iso",
         text="The Bittle X without its back cover: the head is at the front, the tail at the rear. The BiBoard header stands up at the right side."),
    dict(title="Fit the platform", view="iso", show=["cover"], start={"cover": [0, 40, 0]},
         text="Fit the platform cover in place of the stock cover. It has 4 pegs on its top."),
    dict(title="Put the body on", view="build", show=["body"], start={"body": [0, 35, 7]}, end={"body": [0, 0, 7]},
         text="Put the empty body on the pegs 7 mm behind its place, grille to the rear. "
              "The teardrop peg heads go through the teardrop holes. Turned the wrong way, the body does not go down."),
    dict(title="Slide to lock", view="build", start={"body": [0, 0, 7]},
         text="Push the body 7 mm forward until it clicks (about 4 N). Two spring beams at each peg push the peg into a V stop, which centers it. "
              "The BiBoard header is now in the notch of the right well."),
    dict(title="Camera cable", view="buildfront", show=CAM_CABLE, highlight=CAM_CABLE, start={k: [0, 40, 0] for k in CAM_CABLE},
         text="Push a 10 cm Grove cable onto the Grove plug of the BiBoard through the floor opening at the front left. "
              "Lay its excess as an S fold in the front left corner and let its free end hang out of the top."),
    dict(title="Speaker", view="build", show=["speaker"], start={"speaker": [0, 40, 0]},
         text="Push the speaker down into the two side grooves at the rear, body to the rear (to the grille)."),
    dict(title="Mic", view="buildfront", show=["mic"] + MIC_ENDS, start={k: [0, 40, 0] for k in ["mic"] + MIC_ENDS},
         text="Plug the six 10 cm jumpers onto the mic header. Then push the mic down into its groove at the front wall, port to the front."),
    dict(title="Amp", view="build", show=["amp", "wires_speaker__pos", "wires_speaker__neg"] + AMP_CABLE,
         start={k: [0, 40, 0] for k in ["amp", "wires_speaker__pos", "wires_speaker__neg"] + AMP_CABLE},
         text="Plug the speaker lead into the 2-pin connector at the rear end of the amp and the amp cable into the I2S connector at its front end. "
              "Push the bottom edge of the amp down into the slot along the left wall, parts to the inside. "
              "Lay the amp cable across the floor in front of the front pegs and into the right well. The stack goes on top of it."),
    dict(title="Pi stack", view="build", show=STACK, start={k: [0, 45, 0] for k in STACK},
         text="Push the Pi + PiSugar 2 stack down into the end grooves: ports up, header down to the right, SD card to the front. "
              "Then plug the wires one at a time, as the next steps show."),
] + WIRE_STEPS + [
    dict(title="Slider and button into the panel", view="build", show=["panel", "switch", "button"], highlight=["switch", "button"],
         start={"panel": [0, 35, 0], "switch": [0, 47, 8], "button": [0, 47, 6]}, end={"panel": [0, 35, 0], "switch": [0, 35, 0], "button": [0, 35, 0]},
         text="Before the panel goes on: slide the switch slider into the rails under the panel from their rear end until it clicks, "
              "and slide the white button cap onto the tongue until it clicks. They stay in the panel."),
    dict(title="Panel", view="build", show=["panel"], start={"panel": [0, 35, 0], "switch": [0, 35, 0], "button": [0, 35, 0]},
         text="Pass the free end of the Grove cable up through the slot at the front left of the panel. "
              "Then push the panel straight down until the 4 tabs click. The slider tab comes up through its slot. The forks under the panel hold "
              "the stack, the speaker and the amp. The ports are in the shaped openings, and the tongue near the front is the PiSugar button. "
              "To open, lift the rear edge at the finger notch."),
    dict(title="Camera mount", view="iso", show=["camera_mount"], highlight=["camera_mount"], start={"camera_mount": [0, 30, 0]},
         text="Push the two clip legs of the camera mount down through the window in the front of the panel until they click."),
    dict(title="Camera", view="iso", show=["camera", "wires_camera__plug_cam"], highlight=["camera", "wires_camera__plug_cam"],
         start={"camera": [0, 40, 0], "wires_camera__plug_cam": [0, 0, 20]},
         text="Push the camera case down into the two brackets until the ridges click into its end pockets, lens forward. "
              "Then plug the Grove cable into the socket in its rear face."),
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
        info = INFO.get(pid) or INFO.get(next((a for a, ids in GROUPS.items() if pid in ids), ""), {})
        out.append(dict(id=pid, label=label, group=group, file="models/" + name,
                        color=color, explode=(ex or [0, [0, 0, 0], [0, 0, 0]]), transform=tf, **info))
    checks = json.load(open(os.path.join(ROOT, "stl", "checks.json")))["rows"]
    pi = json.load(open(os.path.join(PROJ, "bittle_platform", "interface.json")))
    E = pi["ENVELOPE"]
    meta = dict(
        title="Bittle X Pi Add-on v0.18 on Platform v3.1",
        explode_stages=EXPLODE["stages"],
        envelope=dict(width=2 * E["half_w_low"], length=round(E["z"][1] - E["z"][0], 1), top=E["top"],
                      above_cover=round(E["top"] - pi["COVER_TOP"], 1)),
        bounds=dict(x=[-40, 40], z=[-70, 80], y=[-12, 70]),
        checks=[dict(a=a, b=b, v=round(v, 2)) for a, b, v in checks],
    )
    robot = json.load(open(os.path.join(PROJ, "bittle_platform", "stl", "robot", "robot.json")))
    robot["motion"] = json.load(open(os.path.join(ROOT, "stl", "motion.json")))
    steps = []
    for st in STEPS:
        st = dict(st)
        if "show" in st:
            st["show"] = expand(st["show"])
        for k in ("highlight", "ghost"):
            if k in st:
                st[k] = expand(st[k])
        for k in ("start", "end"):
            if k in st:
                st[k] = {i: v for key, v in st[k].items() for i in expand([key])}
        steps.append(st)
    json.dump(dict(parts=out, meta=meta, steps=steps, robot=robot), open(os.path.join(SITE, "manifest.json"), "w"), indent=1)
    print("site ready:", len(out), "parts")


# --------------------------------------------------------------------------
# Home page: the two packages with their downloads, and a link to the viewer
# --------------------------------------------------------------------------
HOME = os.path.join(PROJ, "site")
LEGAL = ["LICENSE.md", "ATTRIBUTION.md", "LICENSES"]
PACKAGES = [
    dict(key="platform", name="Bittle X Platform v3.1", dir="bittle_platform", zip="bittle_platform_v3.1.zip",
         pdf="bittle_platform_spec.pdf", img="doc/r2_starter.png",
         text="The stock Petoi Bittle X back cover with 4 pegs on its top. Add-ons drop onto the pegs, "
              "slide 7 mm forward and click into place. No tools, glue or tape are necessary. "
              "The spec gives every number that you need to design an add-on.",
         extra=["interface.json"]),
    dict(key="addon", name="Bittle X Pi Add-on v0.18", dir="bittle_pi_addon", zip="bittle_pi_addon_v0.18.zip",
         pdf="bittle_pi_addon_guide.pdf", img="doc/02_addon.png", img2="doc/06_open.png",
         text="A sample add-on for the platform: Raspberry Pi Zero 2 W, PiSugar 2 (1200 mAh), NS4168 amp with a 3 W speaker, "
              "and an SPH0645 mic, in a rounded box with a snap-in top panel and a large power switch. Three printed parts, all without supports.",
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
