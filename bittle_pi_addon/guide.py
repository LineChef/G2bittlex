"""The build guide: an A4 HTML page set with step renders and cable diagrams, printed to PDF with Chromium.

Run after pod.py (it reads stl/, wires.json and checks.json):  python guide.py
  doc/guide/*.png             step renders (OpenSCAD)
  guide/index.html            the guide (also on the site)
  bittle_pi_addon_guide.pdf   the guide, printed by Chromium (headless)
The PDF and the HTML are committed: the site build (GitHub Actions) only copies them.
"""
import html
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import pod      # noqa: E402
import render   # noqa: E402
import docs     # noqa: E402
from bittle_platform import interface as PI   # noqa: E402

GDIR = os.path.join(HERE, "guide")
IDIR = os.path.join(HERE, "doc", "guide")
WIRES = json.load(open(os.path.join(pod.OUT, "wires.json")))
CHECKS = json.load(open(os.path.join(pod.OUT, "checks.json")))
W = {(w["group"], w["wire"]): w for w in WIRES["wires"]}
VIEWER = docs.VIEWER
E = html.escape

# --------------------------------------------------------------------------
# Step renders: the new parts in their colors, the parts already in place in gray
# --------------------------------------------------------------------------
GRAY = "[0.84,0.86,0.90]"
KEEP = {"body", "cover", "shoulder", "plate", "biboard_header__header"}   # always in their own colors


def keys(*models):
    return [k for k in render.ELEC if k.split("__")[0] in models]


def sub(model, pred):
    return [k for k in render.ELEC if k.split("__")[0] == model and pred(k.split("__")[1])]


ROBOT = ["shoulder", "plate", "cover", "biboard_header__header"]
SPK = keys("speaker")
MIC = keys("mic_sph0645") + sub("wires_mic", lambda s: s.endswith("_dev"))
AMP = keys("amp_ns4168", "wires_speaker")
STACK = keys("pisugar2", "pizero", "battery", "sd_card", "stack_screws", "pi_plugs")
SPLICE = keys("wires_splice")
UART_PI = sub("wires_uart", lambda s: not s.endswith("_dev"))
UART_DEV = sub("wires_uart", lambda s: s.endswith("_dev"))
AMPW = keys("wires_amp")
MICW = sub("wires_mic", lambda s: not s.endswith("_dev"))
PANEL = ["panel", "button", "logo_white", "logo_red"]
CAMERA = keys("camera") + keys("wires_camera")

# OpenSCAD cameras: (target x, y, z in the render frame = robot x, -z, y), tilt, 0, turn, distance.
# Turn 0 looks from the rear, 90 from the robot right, 180 from the front, 270 from the robot left.
CAMS = dict(
    hero="0,12,62,62,0,145,420",
    cover="0,-4,30,56,0,148,240",
    iso="0,-6,40,56,0,148,300",
    rear="0,-10,44,48,0,28,250",
    mic="22,26,44,38,0,318,160",
    amp="26,-8,42,44,0,272,190",
    stack="0,-2,42,40,0,118,250",
    well="-20,0,38,24,0,262,170",
    ampcable="-6,10,38,30,0,240,215",
    micw="-6,10,40,30,0,226,215",
    bbend="-24,20,32,14,0,250,105",
    panel="0,-30,30,50,0,148,300",
    camera="0,14,82,62,0,148,330",
)


def step_scene(present, new, lift=None):
    """present, new: lists of part keys. lift: {key: (dx, dy, dz)} offsets in the robot frame."""
    f = render.files()
    s = ""
    lift = lift or {}
    for k, path in f.items():
        if k not in present and k not in new:
            continue
        col = render.C[k] if (k in new or k in KEEP) else GRAY
        d = lift.get(k, (0, 0, 0))
        s += render.imp(path, col, d)
        if k == "shoulder":
            s += render.imp(path, col, mirror="[1,0,0]")
        if k == "plate":
            s += render.imp(path, col, mirror="[0,0,1]")
    return f"rotate([90,0,0]) {{\n{s}}}\n"


def shot(name, scad, cam, size=(2000, 1300)):
    os.makedirs(IDIR, exist_ok=True)
    src, png = os.path.join(IDIR, name + ".scad"), os.path.join(IDIR, name + ".png")
    open(src, "w").write(scad)
    r = subprocess.run(["openscad", "-o", png, f"--imgsize={size[0]},{size[1]}", f"--camera={cam}", "--colorscheme=Tomorrow",
                        "--backend=manifold", src], capture_output=True, text=True)
    os.unlink(src)
    if r.returncode:
        print(r.stderr[-800:])
    return f"../doc/guide/{name}.png"


# The build steps: title, the parts in place before, the new parts, camera, lift, text (one idea per line), check
STEPS = []


def step(title, new, cam, lines, check=None, lift=None, note=None, only=None):
    """only: show just these parts of the ones already in place (a clear view into a crowded corner)."""
    before = sum((s["new"] for s in STEPS), list(ROBOT))
    if only is not None:
        before = list(ROBOT) + [k for k in before if k in only]
    STEPS.append(dict(title=title, before=before, new=new, cam=cam, lines=lines, check=check, lift=lift, note=note))


def build_steps():
    STEPS.clear()
    S, K = PI.SLIDE, CHECKS["clicks"]
    step("Fit the platform cover", ["cover"], "cover",
         ["Remove the stock back cover of the Bittle X.",
          "Put the platform cover in its place. The Pi slot and the BiBoard header are at the front left.",
          "Pass the BiBoard header up through the slot."])
    step("Click the body on", ["body"], "iso",
         [f"Put the empty body on the pegs, {S:g} mm behind its place, the grille to the rear.",
          f"Push it {S:g} mm forward until it clicks (about {K['lock_N']:g} N).",
          "The BiBoard header now stands in the notch at the front of the left well."],
         check="Turned the wrong way, the body does not go down onto the pegs.")
    step("Speaker", SPK, "rear",
         ["Push the two wings of the speaker down into the side grooves at the rear.",
          "The speaker body goes to the rear, toward the grille."])
    step("Mic", MIC, "mic",
         ["Plug the six mic jumpers onto the mic header. Use 15 cm jumpers on GND and 3V.",
          "Drop the mic into the slots in the post and the ledge on the right wall, near the front.",
          "The port faces the wall. The header is at the front edge, the plugs point into the body."],
         check="The board sits in both slots. A fork under the panel holds its top edge later.")
    step("Amp and speaker lead", AMP, "amp",
         ["Plug the speaker lead into the 2-pin connector at the rear end of the amp.",
          "Plug the flat amp cable into the 5-pin connector at the front end. G is at the top.",
          "Put the bottom edge of the amp into the slot along the right wall, parts to the inside.",
          "Tilt the top edge under the two nubs. Set it with a dab of glue.",
          "Let the amp cable hang out of the top. It goes in after the BiBoard jumpers."])
    step("Pi + PiSugar 2 stack", STACK, "stack",
         ["Push the stack down into the grooves of the two end posts until it stops.",
          "The ports are up, the 40-pin header down and toward the left wall, the SD card at the rear."],
         check="If the stack is not fully down, the panel does not slide on later.")
    step("Splices (BCLK and LRCLK)", SPLICE, "well",
         ["Plug the Pi end of each splice: BCLK on pin 12, LRCLK on pin 35.",
          "The LRCLK sleeve stands beside the BiBoard plugs, the BCLK sleeve at the middle of the left well."],
         note="Each splice is a Y: one Pi end, one mic end, one amp end. See the cable cards.")
    step("BiBoard jumpers: Pi ends", UART_PI, "well",
         ["Push the female end of each BiBoard jumper onto the Pi: TX2 (gray) on pin 10, RX2 (white) on pin 8, GND (black) on pin 6.",
          "Lay the excess of each one in a loop by the left wall.",
          "Leave the male ends free. They go onto the BiBoard last."])
    step("Amp cable", AMPW, "ampcable",
         ["Lay the flat amp cable on edge, as it leaves the plug, G on top. Do not twist it.",
          "It steps down, runs forward to the front wall and across under the mic plugs. Past the front post it turns rearward, "
          "runs across behind the front-left notch, and turns rearward along the left well.",
          "Peel off each wire at its own height: DIN onto pin 40, LRC and BCLK into the free sockets of their splices, G onto pin 14, V onto pin 2."])
    step("Mic jumpers", MICW, "micw",
         ["Run the mic jumpers straight across behind the front wall, then rearward along the left well.",
          "Plug them from the lowest up: 3V on pin 1, GND on pin 9, BCLK and LRCL into their splices, DOUT on pin 38, SEL on pin 39."])
    step("BiBoard ends", UART_DEV, "bbend",
         ["Push the male ends of the three BiBoard jumpers into the BiBoard socket: TX2, RX2, GND.",
          "The two +5V sockets stay empty: the PiSugar powers the Pi."], only=["body"] + STACK + UART_PI,
         note="The other wires are not shown here, for a clear view into the front-left corner.")
    step("Button cap and logo", ["panel", "button", "logo_white", "logo_red"], "panel",
         ["Press the post of the white button cap into the round hole in the panel tongue until the cap sits flat.",
          "Glue the two logo inlays into the pocket in the front right corner of the panel top: the white ring and M at the left, the red ring and J at the right."],
         lift={k: (0, 30, 0) for k in ("panel", "button", "logo_white", "logo_red")}, only=["body"])
    step("Panel", ["panel"], "iso",
         [f"Put the panel down {pod.LID_SLIDE:g} mm behind its place.",
          f"Slide it forward until the latch at the rear clicks (about {CHECKS['snap']['slide_on_N']:g} N).",
          "The PiSugar power switch is under the window beside the HDMI opening. Move it with a fingernail."],
         check="To open: lift the rear edge at the finger notch and slide the panel rearward.")
    step("Camera mount", ["camera_mount"], "camera",
         [f"Turn the camera mount {abs(pod.TW['twist']):g} deg counterclockwise (seen from above). Put it down into the round socket: the lugs go down through the keyways.",
          f"Turn it {abs(pod.TW['twist']):g} deg clockwise until it clicks and stops.",
          "To point the lens to the rear, turn the mount end for end first. It locks the same way."],
         check="To remove: turn it counterclockwise and lift it.")
    step("Camera and USB cable", CAMERA, "camera",
         ["Push the camera case down between the brackets, lens forward, USB port up, until the hooks click over its top.",
          "Plug the USB-C end into the top of the camera and the micro-USB end into the Pi data USB port."])


def renders():
    out = {}
    allp = sum((s["new"] for s in STEPS), list(ROBOT))
    out["hero"] = shot("hero", step_scene([], allp), CAMS["hero"], (2400, 1600))
    open_ = [k for k in allp if k not in PANEL + ["camera_mount"] + CAMERA]
    out["open"] = shot("open", step_scene([], open_), CAMS["stack"], (2000, 1300))
    ex = render.scene(render.ALL, explode=True)
    out["exploded"] = shot("exploded", ex, "0,-9,185,72,0,128,960", (1600, 2000))
    for i, s in enumerate(STEPS, 1):
        out[i] = shot(f"step{i:02d}", step_scene(s["before"], s["new"], s["lift"]), CAMS[s["cam"]])
    return out


# --------------------------------------------------------------------------
# Vector diagrams (SVG)
# --------------------------------------------------------------------------
INK, MUTE, LINE = "#1d1d1f", "#6e6e73", "#d2d2d7"


def _t(x, y, s, size=11, w=400, anchor="start", col=INK, mono=False):
    fam = "JetBrains Mono, monospace" if mono else "Noto Sans, sans-serif"
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{w}" '
            f'text-anchor="{anchor}" fill="{col}">{E(s)}</text>')


def dupont(x, y, male=False, angle_right=True):
    """A Dupont housing (black), 9 x 26 px, its mouth at x. male: a pin sticks out."""
    d = 1 if angle_right else -1
    x0 = x if d > 0 else x - 26
    s = f'<rect x="{x0}" y="{y - 4.5}" width="26" height="9" rx="1.5" fill="#202124"/>'
    if male:
        px = x0 + 26 if d > 0 else x0 - 9
        s += f'<rect x="{px}" y="{y - 1}" width="9" height="2" fill="#c9a227"/>'
    else:
        hx = x0 + 22 if d > 0 else x0 + 1
        s += f'<rect x="{hx}" y="{y - 1.6}" width="3" height="3.2" fill="#6b6b6b"/>'
    return s


def wire(x0, y0, x1, y1, col):
    edge = ' stroke-opacity="1"' if col.lower() not in ("#f2f2ef",) else ""
    outline = f'<path d="M{x0},{y0} C{(x0 + x1) / 2},{y0} {(x0 + x1) / 2},{y1} {x1},{y1}" stroke="#9a9a9e" stroke-width="5" fill="none"/>' \
        if col.lower() in ("#f2f2ef", "#9ea0a4") else ""
    return outline + f'<path d="M{x0},{y0} C{(x0 + x1) / 2},{y0} {(x0 + x1) / 2},{y1} {x1},{y1}" stroke="{col}" stroke-width="3.6" fill="none"{edge}/>'


def cable_card(title, left, rows, right_note="", height=None):
    """left: (kind, label) at the shared end, or None for single wires. rows: [(color, wire name, left label, right label,
    right kind)] kind = 'f', 'm', 'ph', 'sleeve'."""
    n = len(rows)
    h = height or max(62, 22 + n * 18)
    w = 560
    s = f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">'
    ys = [h / 2 + (i - (n - 1) / 2) * 18 for i in range(n)]
    xl, xr = 150, 420
    if left and left[0] == "ph":                           # one PH2.0 plug: every wire leaves it
        y0, y1 = ys[0] - 11, ys[-1] + 11
        s += f'<rect x="{xl - 26}" y="{y0}" width="26" height="{y1 - y0}" rx="3" fill="#efe6d2" stroke="#bfb39a"/>'
        s += _t(xl - 34, h / 2 - 4, left[1], 11, 600, "end") + _t(xl - 34, h / 2 + 11, left[2], 9.5, 400, "end", MUTE)
        for i, (col, name, ll, rl, rk) in enumerate(rows):
            yp = ys[i]
            s += wire(xl, yp, xr, yp, col)
            s += _t(xl + 8, yp - 5, name, 9, 600, col=MUTE)
    else:
        for i, (col, name, ll, rl, rk) in enumerate(rows):
            yp = ys[i]
            s += dupont(xl, yp, male=(ll == "m"), angle_right=False)
            s += _t(xl - 40, yp + 3.5, name, 10.5, 600, "end")
            s += wire(xl, yp, xr, yp, col)
    for i, (col, name, ll, rl, rk) in enumerate(rows):
        yp = ys[i]
        if rk == "sleeve":
            s += f'<rect x="{xr}" y="{yp - 5}" width="22" height="10" rx="5" fill="#f2f2ef" stroke="#9a9a9e"/>'
        else:
            s += dupont(xr, yp, male=(rk == "m"))
        s += _t(xr + (44 if rk != "m" else 48), yp + 4, rl, 11, 500)
    if right_note:
        s += _t(w - 4, h - 6, right_note, 9.5, 400, "end", MUTE)
    return s + "</svg>"


def splice_card():
    """The Y splice: a Pi end, a mic end and an amp end joined in a white sleeve."""
    w, h = 560, 120
    s = f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">'
    for k, (col, name, pin) in enumerate((("#3a6fd8", "BCLK", "pin 12"), ("#2e9b4f", "LRCLK", "pin 35"))):
        y = 34 + k * 52
        s += _t(20, y + 4, name, 11, 700)
        s += dupont(150, y, angle_right=False) + _t(112, y + 4, pin, 10.5, 500, "end")
        s += wire(150, y, 280, y, col)
        s += f'<rect x="280" y="{y - 6}" width="34" height="12" rx="6" fill="#f2f2ef" stroke="#9a9a9e"/>'
        s += wire(314, y, 420, y - 12, col) + wire(314, y, 420, y + 12, col)
        s += dupont(420, y - 12) + _t(462, y - 8, "mic " + ("BCLK" if k == 0 else "LRCL"), 10.5, 500)
        s += dupont(420, y + 12, male=True) + _t(466, y + 16, "amp cable " + ("BCLK" if k == 0 else "LRC"), 10.5, 500)
    return s + "</svg>"


def usb_card():
    w, h = 560, 70
    s = f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">'
    s += '<rect x="96" y="25" width="52" height="20" rx="4" fill="#2b2d33"/><rect x="148" y="31" width="10" height="8" rx="2" fill="#b9bcc2"/>'
    s += _t(88, 39, "USB-C", 11, 600, "end")
    s += '<path d="M96,35 C60,35 60,35 40,35" stroke="none"/>'
    s += '<path d="M158,35 C280,35 300,35 410,35" stroke="#1d1d1f" stroke-width="5" fill="none"/>'
    s += '<rect x="410" y="26" width="48" height="18" rx="4" fill="#2b2d33"/><rect x="458" y="31" width="9" height="8" rx="1.5" fill="#b9bcc2"/>'
    s += _t(476, 39, "micro-USB", 11, 600)
    s += _t(150, 62, "camera, top of the case", 9.5, 400, "middle", MUTE) + _t(440, 62, "Pi data USB port", 9.5, 400, "middle", MUTE)
    return s + "</svg>"


def pi_header_svg():
    """The 2 x 20 header seen from the component face, pin 1 at the SD card end (rear). The used pins are in the
    color of their wire."""
    used = {}
    for (g, lab), w in W.items():
        if w["to"].startswith("pin "):
            used[int(w["to"].split()[1])] = (w["color"], f"{w['from']}")
    for t, n in (("bclk", 12), ("lrclk", 35)):
        used[n] = (W[("splice", t)]["color"], f"{t.upper()} splice")
    names = {1: "3V3", 2: "5V", 4: "5V", 6: "GND", 9: "GND", 14: "GND", 20: "GND", 25: "GND", 30: "GND", 34: "GND", 39: "GND",
             17: "3V3", 8: "TXD", 10: "RXD", 12: "G18", 35: "G19", 38: "G20", 40: "G21"}
    w_, h_ = 640, 250
    s = f'<svg viewBox="0 0 {w_} {h_}" width="100%" xmlns="http://www.w3.org/2000/svg">'
    p0, dx = 40, 28
    s += f'<rect x="{p0 - 16}" y="88" width="{19 * dx + 32}" height="60" rx="4" fill="#1d1d1f"/>'
    for n in range(1, 41):
        col_i = (n - 1) // 2
        x = p0 + col_i * dx
        y = 104 if n % 2 else 132
        c, lab = used.get(n, ("#5f6166", ""))
        s += f'<circle cx="{x}" cy="{y}" r="8" fill="{c}" stroke="{"#9a9a9e" if c.lower() in ("#f2f2ef", "#9ea0a4") else "none"}"/>'
        s += _t(x, y + 3.2, str(n), 7.5, 700, "middle", "#ffffff" if c.lower() not in ("#f2f2ef", "#f0c419", "#9ea0a4") else INK)
        if lab:
            ty = 70 if n % 2 else 168
            s += f'<line x1="{x}" y1="{y + (-9 if n % 2 else 9)}" x2="{x}" y2="{ty + (6 if n % 2 else -10)}" stroke="{LINE}"/>'
            s += (f'<text transform="translate({x + 3},{ty}) rotate(-50)" font-family="Noto Sans" font-size="9.5" font-weight="600" fill="{INK}">'
                  f'{E(lab)}</text>' if n % 2 else
                  f'<text transform="translate({x + 3},{ty}) rotate(50)" font-family="Noto Sans" font-size="9.5" font-weight="600" fill="{INK}">'
                  f'{E(lab)}</text>')
    s += _t(p0 - 16, 240, "Pin 1 is at the SD card end (rear). Odd pins: inner row (top). Even pins: board edge (bottom).", 10, 400, col=MUTE)
    return s + "</svg>"


def board_pins_svg(title, pins, note):
    """pins: [(label, color)] in the order printed on the board, top to bottom."""
    n = len(pins)
    h = 40 + n * 24
    s = f'<svg viewBox="0 0 250 {h}" width="100%" xmlns="http://www.w3.org/2000/svg">'
    s += f'<rect x="20" y="16" width="70" height="{n * 24 + 8}" rx="6" fill="#1f2a36"/>'
    for i, (lab, col) in enumerate(pins):
        y = 32 + i * 24
        s += f'<rect x="78" y="{y - 6}" width="18" height="12" rx="2" fill="#c9a227"/>'
        s += _t(70, y + 4, lab, 10.5, 700, "end", "#ffffff")
        if col:
            s += wire(96, y, 160, y, col) + dupont(160, y)
    s += _t(125, h - 4, note, 9.5, 400, "middle", MUTE)
    return s + "</svg>"


# --------------------------------------------------------------------------
# The pages
# --------------------------------------------------------------------------
CSS = r"""
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font-family: "Noto Sans", sans-serif; color: #1d1d1f; font-size: 9.6pt; line-height: 1.45; background: #e9e9ec; }
.page { width: 210mm; height: 297mm; padding: 16mm 17mm 18mm; position: relative; background: #fff; overflow: hidden;
        page-break-after: always; margin: 0 auto 8mm; }
@media print { body { background: #fff; } .page { margin: 0; } }
.folio { position: absolute; bottom: 9mm; left: 17mm; right: 17mm; display: flex; justify-content: space-between;
         font-size: 7.5pt; color: #8e8e93; letter-spacing: .02em; border-top: .4pt solid #d2d2d7; padding-top: 2.5mm; }
h1 { font-size: 30pt; font-weight: 800; letter-spacing: -.02em; line-height: 1.05; margin: 0 0 3mm; }
h2 { font-size: 17pt; font-weight: 700; letter-spacing: -.01em; margin: 0 0 4mm; }
h3 { font-size: 10.5pt; font-weight: 700; margin: 5mm 0 1.5mm; }
.kicker { font-size: 8pt; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #e8641b; margin-bottom: 2mm; }
.lead { font-size: 11pt; line-height: 1.5; color: #3a3a3c; font-weight: 300; }
.muted { color: #6e6e73; }
.cover { padding: 0; }
.cover .art { position: absolute; inset: 0 0 92mm 0; background: radial-gradient(ellipse at 50% 40%, #ffffff 0%, #eef0f3 70%, #e3e6ea 100%); }
.cover .art img { width: 100%; height: 100%; object-fit: cover; }
.cover .title { position: absolute; left: 17mm; right: 17mm; bottom: 26mm; }
.cover .title h1 { font-size: 40pt; }
.cover .meta { display: flex; gap: 10mm; margin-top: 6mm; font-size: 8.5pt; color: #6e6e73; }
.cover .meta b { display: block; color: #1d1d1f; font-size: 9.5pt; }
.bar { position: absolute; left: 0; right: 0; bottom: 0; height: 6mm; background: linear-gradient(90deg, #e8641b, #f2a71c); }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }
.grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5mm; }
table { width: 100%; border-collapse: collapse; font-size: 8.6pt; }
th { text-align: left; font-weight: 700; font-size: 7.5pt; letter-spacing: .06em; text-transform: uppercase; color: #6e6e73;
     border-bottom: .8pt solid #1d1d1f; padding: 1.6mm 2mm 1.6mm 0; }
td { border-bottom: .4pt solid #e5e5ea; padding: 1.8mm 2mm 1.8mm 0; vertical-align: top; }
td.n { white-space: nowrap; font-variant-numeric: tabular-nums; }
.sw { display: inline-block; width: 9pt; height: 9pt; border-radius: 50%; vertical-align: -1.5pt; margin-right: 1.5mm; border: .5pt solid #b0b0b5; }
.card { border: .5pt solid #d2d2d7; border-radius: 3mm; padding: 3mm 4mm 2mm; margin-bottom: 3.2mm; break-inside: avoid; }
.card h4 { margin: 0 0 .5mm; font-size: 9.6pt; }
.card p { margin: 0 0 1mm; font-size: 8.4pt; color: #3a3a3c; }
.tag { display: inline-block; font-size: 7pt; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; padding: .4mm 1.6mm;
       border-radius: 1.2mm; background: #f2f2f7; color: #3a3a3c; margin-left: 1.5mm; vertical-align: 1pt; }
.tag.o { background: #fde9dc; color: #b34a0f; }
.step { display: grid; grid-template-columns: 1fr; gap: 3mm; margin-bottom: 5mm; break-inside: avoid; }
.step .shot { background: linear-gradient(180deg, #f7f8fa, #eceef1); border-radius: 3mm; overflow: hidden; height: 80mm;
              display: flex; align-items: center; justify-content: center; }
.step .shot img { width: 100%; height: 100%; object-fit: cover; }
.step .head { display: flex; align-items: baseline; gap: 3mm; }
.num { font-size: 22pt; font-weight: 800; color: #e8641b; line-height: 1; min-width: 12mm; }
.step h3 { margin: 0; font-size: 13pt; }
.step ol { margin: 1mm 0 0 15mm; padding: 0; }
.step li { margin: 0 0 1mm; }
.check { margin: 1.5mm 0 0 15mm; font-size: 8.4pt; padding: 1.6mm 3mm; border-left: 2pt solid #2e9b4f; background: #f1f8f3; }
.note { margin: 1.5mm 0 0 15mm; font-size: 8.4pt; padding: 1.6mm 3mm; border-left: 2pt solid #3a6fd8; background: #f0f4fc; }
.full img { width: 100%; border-radius: 3mm; }
.callout { font-size: 8.4pt; padding: 2.5mm 3.5mm; background: #f5f5f7; border-radius: 2.5mm; }
.toc div { display: flex; justify-content: space-between; border-bottom: .4pt dotted #c7c7cc; padding: 1.6mm 0; font-size: 10pt; }
"""


def page(body, n, cls=""):
    return (f'<section class="page {cls}">{body}<div class="folio"><span>Bittle X Pi Add-on v{docs.VERSION} · Build guide</span>'
            f'<span>{n}</span></div></section>')


def swatch(c):
    return f'<span class="sw" style="background:{c}"></span>'


def cover(img):
    return (f'<section class="page cover"><div class="art"><img src="{img}"></div><div class="title">'
            f'<div class="kicker">Build guide</div><h1>Bittle X<br>Pi Add-on</h1>'
            f'<div class="lead">A Raspberry Pi Zero 2 W with a battery, a speaker, a microphone and a camera, in one rounded box '
            f'that clicks onto the back of the Petoi Bittle X.</div>'
            f'<div class="meta"><div><b>Add-on v{docs.VERSION}</b>{docs.DATE}</div><div><b>Platform v{PI.VERSION}</b>pegs on the stock cover</div>'
            f'<div><b>{CHECKS["balance"]["mass_g"]:.0f} g</b>with the electronics</div><div><b>No supports</b>every part prints as is</div></div>'
            f'</div><div class="bar"></div></section>')


def overview(img, n):
    rows = "".join(f"<div><span>{t}</span><span>{p}</span></div>" for t, p in (
        ("What you build", 2), ("Parts to print", 3), ("Electronics and cables", 4), ("Pin maps", 5), ("Assembly", 6),
        ("Wire table", 14), ("Checks, opening and removal", 15)))
    body = (f'<div class="kicker">Overview</div><h2>What you build</h2>'
            f'<div class="grid2"><div><p class="lead">The add-on is a body that clicks onto the platform pegs, a slide-on top panel and '
            f'a camera mount. Every part goes into the body from the top, in the order of this guide. No tools are necessary, '
            f'except a soldering iron for the two splices and a dab of glue for the amp.</p>'
            f'<h3>Directions in this guide</h3><p>Front is the head end of the robot. Left and right are the robot\'s left and right. '
            f'The Pi plugs and the BiBoard header are in the <b>left well</b>. The amp and the mic are on the <b>right wall</b>. '
            f'The speaker is at the rear.</p>'
            f'<h3>Contents</h3><div class="toc">{rows}</div>'
            f'<p class="callout" style="margin-top:5mm">The 3D viewer shows every step with animation: '
            f'<b>{E(VIEWER)}</b></p></div>'
            f'<div class="full"><img src="{img}"></div></div>')
    return page(body, n)


def print_parts(n):
    P = CHECKS["printing"]
    rows = [("pod_body", "Body", "PLA, white", "floor on the bed"), ("pod_panel", "Top panel", "PLA, second color", "upside down: top on the bed"),
            ("pod_button", "Button cap", "PLA, white", "upside down: top on the bed"),
            ("pod_logo_white", "Logo inlay, white", "PLA, white", "top on the bed"), ("pod_logo_red", "Logo inlay, red", "PLA, red", "top on the bed"),
            ("pod_camera_mount", "Camera mount", "PLA, second color", "standing up, lugs on the bed (as in the STL)")]
    # the panel: the 3MF has a support blocker over the logo pocket
    tr = "".join(f"<tr><td><b>{t}</b><br><span class='muted'>stl/print/{f}.stl</span></td><td>{m}</td><td>{o}</td>"
                 f"<td class='n'>{docs.pod_mass(f) if f in ('pod_body', 'pod_panel', 'pod_camera_mount') else '< 1'} g</td></tr>"
                 for f, t, m, o in rows)
    opt = ("<tr><td><b>Head-off camera mount</b> (optional)<br><span class='muted'>pod_camera_base_low, pod_camera_cradle_low</span></td>"
           "<td>PLA</td><td>as in the STLs</td><td class='n'></td></tr>")
    body = (f'<div class="kicker">1</div><h2>Parts to print</h2>'
            f'<p class="lead">Print every part without supports, in the orientation of its file in stl/print/. '
            f'The platform cover is in the platform package (cover_pegs_foot.stl, with a break-off foot).</p>'
            f'<table><tr><th>Part</th><th>Material</th><th>On the bed</th><th>Mass</th></tr>{tr}{opt}</table>'
            f'<h3>Settings</h3><div class="grid2"><p>0.2 mm layers, 0.25 mm first layer. Walls 2 mm: 4 lines of 0.5 mm. '
            f'Small holes print about 0.2 mm under size: the fits allow for it.</p>'
            f'<p>The panel prints top down: its logo pocket and its openings are on the bed. Slice stl/print/pod_panel.3mf: '
            f'it has a support blocker over the logo pocket. The body prints floor down: '
            f'its labels and its route grooves face up.</p></div>'
            f'<h3>Hardware</h3><table><tr><th>Item</th><th>Count</th><th>Use</th></tr>'
            f'<tr><td>Female-to-male Dupont jumper, 10 cm</td><td class="n">3</td><td>BiBoard serial link</td></tr>'
            f'<tr><td>Female-female Dupont jumper, 10 cm</td><td class="n">4 + 2</td><td>mic (4) and the Pi ends of the splices (2)</td></tr>'
            f'<tr><td>Female-female Dupont jumper, 15 cm</td><td class="n">2</td><td>mic GND and 3V</td></tr>'
            f'<tr><td>Female-to-male Dupont jumper, 10 cm</td><td class="n">2</td><td>the amp ends of the splices</td></tr>'
            f'<tr><td>Heat shrink, white</td><td class="n">2</td><td>splice sleeves</td></tr>'
            f'<tr><td>USB-C to micro-USB cable, 15 cm or more</td><td class="n">1</td><td>camera to Pi</td></tr>'
            f'<tr><td>Glue (a dab)</td><td class="n"></td><td>amp; logo inlays</td></tr></table>')
    return page(body, n)


def cables(n):
    amp_rows = [(W[("amp", k)]["color"], k, "", t, "f" if k in ("G", "V", "DIN") else "m") for k, t in
                (("G", "Pi pin 14"), ("V", "Pi pin 2 (5V)"), ("BCLK", "BCLK splice"), ("LRC", "LRCLK splice"), ("DIN", "Pi pin 40"))]
    amp_rows = [(c, k, l, t, "f") for c, k, l, t, _ in amp_rows]
    uart = [(W[("uart", k)]["color"], k, "f", f"BiBoard {k}", "m") for k in ("TX2", "RX2", "GND")]
    uart = [(c, f"Pi pin {W[('uart', k)]['to'].split()[1]}", "f", t, m) for (c, k, l, t, m), k in zip(uart, ("TX2", "RX2", "GND"))]
    mic = [(W[("mic", k)]["color"], k, "f", f"Pi {W[('mic', k)]['to']}" if W[("mic", k)]["to"].startswith("pin") else W[("mic", k)]["to"], "f")
           for k in ("3V", "GND", "BCLK", "DOUT", "LRCL", "SEL")]
    mic = [(c, f"mic {k}", "f", t + (" · 15 cm" if k in ("3V", "GND") else ""), "f") for (c, k, l, t, m) in mic]
    body = (f'<div class="kicker">2</div><h2>Electronics and cables</h2>'
            f'<p class="lead">Each cable below shows its two ends. Some have one plug at one end and many at the other: '
            f'match each end before you plug it in.</p>'
            f'<div class="card"><h4>Amp cable <span class="tag o">1 plug → 5 sockets</span></h4>'
            f'<p>Comes with the NULLLAB NS4168 amp: one 5-pin PH2.0 plug at the amp, five single female Dupont sockets at the other end. '
            f'The wires are bonded flat. Keep the cable on edge: do not twist it.</p>'
            f'{cable_card("", ("ph", "PH2.0 5-pin", "into the amp I2S"), amp_rows)}</div>'
            f'<div class="card"><h4>BiBoard jumpers <span class="tag">3 single jumpers</span> <span class="tag o">female → male</span></h4>'
            f'<p>The female end goes onto the Pi pin. The male end goes into the BiBoard socket, which is female.</p>'
            f'{cable_card("", None, uart)}</div>'
            f'<div class="card"><h4>Mic jumpers <span class="tag">6 single jumpers</span> <span class="tag">female → female</span></h4>'
            f'<p>One per mic pin. BCLK and LRCL end in the free female ends of the splices; cut them to length when you make the splices.</p>'
            f'{cable_card("", None, mic)}</div>'
            f'<div class="grid2"><div class="card"><h4>Splices <span class="tag o">1 → 2</span></h4>'
            f'<p>Each clock signal feeds two boards. Make a Y from three jumper ends: solder, then cover with white heat shrink.</p>'
            f'{splice_card()}</div>'
            f'<div><div class="card"><h4>Speaker lead</h4><p>The 2-wire lead of the speaker ends in a 2-pin PH2.0 plug: it goes into the '
            f'rear end of the amp.</p></div><div class="card"><h4>Camera USB cable</h4><p>USB-C at the camera, micro-USB at the Pi '
            f'data port.</p>{usb_card()}</div></div></div>')
    return page(body, n)


def pin_maps(n):
    mic = [(lab, W[("mic", lab)]["color"]) for lab in ("SEL", "LRCL", "DOUT", "BCLK", "GND", "3V")]
    amp = [(lab, W[("amp", lab)]["color"]) for lab in ("G", "V", "BCLK", "LRC", "DIN")]
    bb = [("TX2", W[("uart", "TX2")]["color"]), ("RX2", W[("uart", "RX2")]["color"]), ("GND", W[("uart", "GND")]["color"]),
          ("+5V", None), ("+5V", None)]
    body = (f'<div class="kicker">3</div><h2>Pin maps</h2>'
            f'<p class="lead">Every pin in use, in the color of its wire.</p>'
            f'<h3>Pi Zero 2 W, 40-pin header</h3>{pi_header_svg()}'
            f'<div class="grid3" style="margin-top:4mm">'
            f'<div><h3>Mic (as mounted)</h3>{board_pins_svg("mic", mic, "SEL at the top, 3V at the bottom")}</div>'
            f'<div><h3>Amp I2S plug</h3>{board_pins_svg("amp", amp, "G at the top (the amp stands upright)")}</div>'
            f'<div><h3>BiBoard socket</h3>{board_pins_svg("bb", bb, "male ends in; +5V stays empty")}</div></div>'
            f'<p class="callout" style="margin-top:4mm">TX and RX cross: BiBoard TX2 goes to Pi RXD (pin 10), BiBoard RX2 to Pi TXD (pin 8). '
            f'SEL to GND puts the mic on the left channel. The PiSugar 2 powers the Pi through its contact pins.</p>')
    return page(body, n)


def step_html(i, s, img):
    lines = "".join(f"<li>{E(t)}</li>" for t in s["lines"])
    chk = f'<div class="check">{E(s["check"])}</div>' if s["check"] else ""
    note = f'<div class="note">{E(s["note"])}</div>' if s["note"] else ""
    return (f'<div class="step"><div class="shot"><img src="{img}"></div><div><div class="head"><div class="num">{i}</div>'
            f'<h3>{E(s["title"])}</h3></div><ol>{lines}</ol>{chk}{note}</div></div>')


def wire_table(n):
    order = [("uart", k) for k in ("TX2", "RX2", "GND")] + [("amp", k) for k in ("G", "V", "BCLK", "LRC", "DIN")] + \
            [("splice", "bclk"), ("splice", "lrclk")] + [("mic", k) for k in ("3V", "GND", "BCLK", "DOUT", "LRCL", "SEL")] + \
            [("speaker", "+"), ("speaker", "-"), ("camera", "USB")]
    tr = "".join(f"<tr><td>{swatch(W[k]['color'])}{E(W[k]['from'])}</td><td>{E(W[k]['to'])}</td>"
                 f"<td>{E(k[0])}</td><td class='n'>{W[k]['length_mm']:.0f} mm</td><td>{E(W[k].get('slack') or '')}</td></tr>" for k in order)
    body = (f'<div class="kicker">5</div><h2>Wire table</h2><p class="lead">Every wire, from end to end. Lengths are between the '
            f'housings, as modeled; a jumper longer than the route lays its excess in the loop shown.</p>'
            f'<table><tr><th>From</th><th>To</th><th>Group</th><th>Length</th><th>Excess</th></tr>{tr}</table>')
    return page(body, n)


def checks_page(n):
    K, S, B = CHECKS["clicks"], CHECKS["snap"], CHECKS["balance"]
    mo = json.load(open(os.path.join(pod.OUT, "motion.json")))
    h0, h1 = mo["head"]["free"]
    body = (f'<div class="kicker">6</div><h2>Checks, opening and removal</h2>'
            f'<div class="grid2"><div><h3>What the model checks</h3><ul>'
            f'<li>No printed part and no board touch, except where a fit is meant to touch.</li>'
            f'<li>Every part goes in from the top, in the order of this guide.</li>'
            f'<li>No two wires pass through each other. No designed bend is tighter than {pod.R_BEND:g} mm.</li>'
            f'<li>The head turns from {h0} to {h1} deg without contact.</li>'
            f'<li>Platform click: about {K["lock_N"]:g} N on, {K["unlock_N"]:g} N off. Panel latch: about {S["slide_on_N"]:g} N.</li>'
            f'<li>Mass {B["mass_g"]:.0f} g; center of mass {abs(B["com"][2]):.1f} mm from the robot center.</li></ul></div>'
            f'<div><h3>Open the panel</h3><p>Lift the rear edge at the finger notch (about {S["lift_N"]:g} N), slide the panel '
            f'{pod.LID_SLIDE:g} mm rearward and lift it.</p>'
            f'<h3>Remove the add-on</h3><p>Open the panel. Pull the three BiBoard plugs off. Slide the body {PI.SLIDE:g} mm rearward and lift it.</p>'
            f'<h3>Change the SD card</h3><p>Open the panel and lift the speaker out of its grooves; the card is at the rear end of the Pi.</p>'
            f'<h3>Files</h3><p class="muted">stl/print: the parts to print. cad/: STEP files. README.md: the full reference. '
            f'Designs CC BY 4.0, code MIT; see LICENSE.md and ATTRIBUTION.md.</p></div></div>')
    return page(body, n)


def build_html(imgs):
    pages = [cover(imgs["hero"]), overview(imgs["exploded"], 2), print_parts(3), cables(4), pin_maps(5)]
    n = 6
    per = 2
    for k in range(0, len(STEPS), per):
        chunk = "".join(step_html(i + 1, STEPS[i], imgs[i + 1]) for i in range(k, min(k + per, len(STEPS))))
        head = '<div class="kicker">4</div><h2>Assembly</h2>' if k == 0 else ""
        pages.append(page(head + chunk, n))
        n += 1
    pages.append(wire_table(n))
    pages.append(checks_page(n + 1))
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Bittle X Pi Add-on build guide</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>')


def main(render_images=True):
    build_steps()
    if render_images:
        imgs = renders()
    else:
        imgs = {k: f"../doc/guide/{k}.png" for k in ("hero", "open", "exploded")}
        imgs.update({i: f"../doc/guide/step{i:02d}.png" for i in range(1, len(STEPS) + 1)})
    os.makedirs(GDIR, exist_ok=True)
    path = os.path.join(GDIR, "index.html")
    open(path, "w").write(build_html(imgs))
    pdf = os.path.join(HERE, "bittle_pi_addon_guide.pdf")
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    r = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                        f"--print-to-pdf={pdf}", "file://" + path], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:])
    print("guide ready:", pdf)


if __name__ == "__main__":
    main("--no-render" not in sys.argv)
