"""Bittle X Pi add-on: README.md and bittle_pi_addon_guide.pdf from one content list.

Run pod.py and render.py first, then:  python docs.py
"""
import datetime
import json

import numpy as np
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import pod                                   # noqa: E402
from bittle_platform import docs as PD       # noqa: E402  (writers shared with the platform)
from bittle_platform import interface as PI  # noqa: E402

VERSION = "0.16"
DATE = datetime.date.today().isoformat()
TITLE = f"Bittle X Pi Add-on v{VERSION} - Build Guide"
VIEWER = "https://beetlebugorg.github.io/bittlex/viewer/"
CHECKS = json.load(open(os.path.join(pod.OUT, "checks.json")))


def content():
    pr = CHECKS["printing"]
    S, K = CHECKS["snap"], CHECKS["clicks"]
    MO = json.load(open(os.path.join(pod.OUT, "motion.json")))
    X = []
    h = lambda t: X.append(("h", t))
    p = lambda t: X.append(("p", t))
    tbl = lambda rows, w: X.append(("table", rows, w))
    img = lambda f, w=1.0, cap="": X.append(("img", f, w, cap))
    lst = lambda items: X.append(("list", items))

    p(f"Version {VERSION}, {DATE}. A sample add-on for the Bittle X platform v{PI.VERSION} (../bittle_platform). "
      "It holds a Raspberry Pi Zero 2 W with a PiSugar 2 (1200 mAh), an NS4168 I2S amp with a 3 W speaker, and an SPH0645 I2S mic. "
      "The case is one rounded box (the body) and a snap-in top panel. The body clicks onto the platform pegs, and every part goes in from the top. "
      "No tools, glue, tape or supports are necessary.")
    img("02_addon.png", 0.5, "The add-on on the platform: the mic holes are at the front, the port windows in the panel.")

    h("1. Parts to print")
    tbl([["File (stl/print/)", "Material", "Orientation", "Supports", "Cura profile", "Mass"],
         ["pod_body.stl", "PLA", "floor on the bed", "none", "Bittle Pi Pod - PLA 0.25", f"{pod_mass('pod_body')} g"],
         ["pod_panel.stl", "PLA, second color", "upside down: top on the bed", "none", "Bittle Fine 0.10 for the best top", f"{pod_mass('pod_panel')} g"],
         ["pod_switch.stl", "PLA", "flat side on the bed, tab up", "none", "Bittle Fine 0.10", "0.2 g"],
         ["cover_pegs_foot.stl (../bittle_platform)", "PLA", "stand on the rear end", "none: the foot is the support", "Bittle Cover - PLA 0.25", "11 g"],
         ], [38, 22, 36, 16, 42, 14])
    p(f"Print quality. The body walls are vertical and its floor is on the bed. The only overhangs ({pr['pod_body']['overhang_mm2']:.0f} mm² in total) "
      "are the tops of the two cable notches at the base of the side walls: 8 mm bridges. The front cable notches are 45 deg chamfers. "
      "The grille holes and the mic holes are teardrops (round, with a 45 deg point on top), so they print without bridges. "
      "The panel top edge round ends in a 45 deg chamfer at the bed, the port openings have 45 deg chamfers, and the snap bumps have 45 deg catch faces. "
      f"Its only overhang ({pr['pod_panel']['overhang_mm2']:.0f} mm²) is the 2 mm bridge of the button arm. The slider has a 1.7 mm bridge over the fork. Keep the seam at the rear.")

    h("2. Electronics")
    tbl([["Part", "Place"],
         ["Raspberry Pi Zero 2 W + PiSugar 2, 1200 mAh", "On the long edge over the robot center: ports and PiSugar controls up, GPIO header down to the right, SD card to the front. Two end posts with grooves hold the boards."],
         ["Dupont jumpers", "On the soldered Pi header, 12 pins (section 4). 3 of them go to the BiBoard header in the right well."],
         ["NULLLAB NS4168 I2S amp", "38.4 x 22.4 mm board, on edge along the left wall, parts to the inside, in a slot bar on the floor. "
          "Its PH2.0 connectors are side entry: the I2S cable plugs in at the front end, the speaker at the rear end."],
         ["NULLLAB 3 W 4 ohm speaker", "At the rear, sound to the grille in the rear face. Ear plate 45 x 31 x 1.5 in two side grooves (ruler)."],
         ["HiLetgo SPH0645 I2S mic", "16.7 x 12.7 x 1.8 board at the front wall, port to the front, in two grooves. Solder the wires to the pins at its top edge."],
         ["Head camera cable", "The Grove cable comes out under the front edge of the cover (left side) and runs up to the head. A 45 deg notch in each front bottom corner of the body gives it room."],
         ["Optional cable", "A notch at the base of each side wall lets a cable in from outside."],
         ], [52, 118])

    B = CHECKS["balance"]
    x, y, z = B["com"]
    p(f"Balance. The add-on weighs about {B['mass_g']:.0f} g (printed parts in PLA and typical masses of the electronics, not weighed). "
      f"The Pi stack, the heaviest part, is over the robot center. The speaker is at the rear, away from the mic. "
      f"So the center of mass of the add-on is {z:.1f} mm behind the robot center and {abs(x):.1f} mm {'left' if x < 0 else 'right'} of the center line, "
      f"{y - PI.COVER_TOP:.0f} mm above the cover top. The platform spec recommends {PI.ENVELOPE['com_z_max']:g} mm or less: "
      "with the speaker at the front it is about 7 mm. Put your own masses in MASS_G in pod.py and run pod.py again.")

    h("3. Assembly")
    st = lambda n: f" ([viewer step {n}]({VIEWER}#step={n}))"
    p(f"The 3D viewer shows each step with animation: [{VIEWER}#step=1]({VIEWER}#step=1).")
    lst(["Fit the platform cover in place of the stock cover." + st(2),
         f"Put the empty body on the pegs {PI.SLIDE:g} mm behind its place, grille to the rear. Slide it {PI.SLIDE:g} mm forward until it clicks "
         f"(about {K['lock_N']:g} N). The BiBoard header is now in the notch of the right well." + st(3) + st(4),
         "Push the speaker down into the two side grooves at the rear, body to the rear." + st(5),
         "Push the mic down into the two grooves at the front wall, port to the front." + st(6),
         "Plug the amp cable into the I2S connector at the front end of the amp and the speaker into its rear end. Push the amp down into the slot along the left wall, parts to the inside. Lay the amp cable across the floor in front of the front pegs." + st(7),
         "Push the jumpers onto the Pi header. Push the Pi + PiSugar 2 stack down into the end grooves, over the I2S wires." + st(8),
         "Reach into the right well and push the three Dupont plugs onto the BiBoard header (TX2, RX2, GND). Fold the slack into the right well." + st(9),
         "Put the switch slider on the PiSugar switch lever, fork down." + st(10),
         f"Push the panel straight down until the 4 tabs click (about {S['close_N']:g} N). It fits one way only. The slider tab comes up through its slot." + st(11),
         f"Open: lift the rear edge of the panel at the finger notch (about {S['open_one_end_N']:g} N), then the front. "
         f"Remove: open the panel, pull the BiBoard plug off, slide the body {PI.SLIDE:g} mm rearward and lift it."])
    p("On the top: the port openings are shaped to the plug bodies (plug + 0.4 mm). The Pi power port and the PiSugar charge port share one opening. "
      "The ribbed slider beside the HDMI opening moves the PiSugar power switch (2 mm of slot travel each way; the switch sets the end positions). "
      "The tongue near the front of the panel is a large button: press it to press the PiSugar button.")
    img("04_top.png", 0.42, "The top: HDMI, the switch slider, data USB, charge and Pi power, and the button tongue.")

    h("4. Wiring")
    tbl([["Board pin", "Pi pin", "Signal"],
         ["BiBoard TX2 / RX2 / GND", "10 / 8 / 6", "RXD / TXD / GND (TX and RX cross). BiBoard +5V: not wired"],
         ["Amp V / G", "2 / 14", "5V / GND"],
         ["Mic 3V / GND / SEL", "1 / 9 / 39", "3V3 / GND / GND (left channel)"],
         ["Amp BCLK + mic BCLK", "12 (splice)", "GPIO18: one wire from the pin to a soldered splice, then one wire to each board"],
         ["Amp LRC + mic LRCL", "35 (splice)", "GPIO19: the same, a second splice"],
         ["Amp DIN / mic DOUT", "40 / 38", "GPIO21 / GPIO20"],
         ["Speaker", "-", "amp 2-pin PH2.0 at the rear end of the amp"],
         ], [44, 26, 100])
    p("Pin map from the wiring blueprint (reference/g2-wiring-blueprint.html; that blueprint wins if they differ). "
      "PiSugar 2 touches pins 2, 4, 5 and 6 from below with its pogo pins. Pins 11, 17-20 and 22-24 are kept free for a screen.")
    h("5. Cable routing")
    WR = json.load(open(os.path.join(pod.OUT, "wires.json")))
    ws = WR["wires"]
    p(f"pod.py models every wire ({WR['wire_d']:g} mm) on its route and checks it: no wire touches a printed part or a board, "
      f"no two wires pass through each other ({len(WR['crossings'])} found), and no bend is smaller than {WR['r_bend']:g} mm radius. "
      "The drawings show the routes. The numbers are the rows of the table.")
    img("13_routing_top.png", 0.8, "Top view of the routes. The right well is between the Pi header plugs and the right wall.")
    img("14_routing_side.png", 0.8, "The right well from the right side: the floor lanes of the amp cable, the BiBoard wires at three heights, the mic cable above them.")
    cells = [[str(i), WIRE_FROM[(w["group"], w["wire"])], WIRE_TO[(w["group"], w["wire"])], f"{w['length_mm']:.0f}"]
             for i, w in enumerate(ws, 1)]
    half = (len(cells) + 1) // 2
    rows = [["#", "From", "To", "mm"] * 2]
    for k in range(half):
        rows.append(cells[k] + (cells[k + half] if k + half < len(cells) else ["", "", "", ""]))
    tbl(rows, [7, 27, 27, 11] * 2)
    lst(["Mic wires: bend each wire before you solder it, so it leaves along the back face of the board. Cut them to the route length + 15 mm. "
         "Route: " + ROUTE["mic"] + ".",
         "Amp cable: " + ROUTE["amp"] + ". From the front: DIN in the inner lane, then LRC, BCLK, and G at the wall. V goes up to pin 2 at once. Lay it before the stack goes in.",
         "Splices: the BCLK splice stands in front of the BiBoard notch, the LRCLK splice beside the BiBoard plugs. The Pi wire and the amp wire go into the bottom, the mic wire into the top.",
         "BiBoard wires: " + ROUTE["uart"] + ". Pin 6 (front) goes to GND (rear), so the order turns over: pin 10 runs lowest, pin 6 highest.",
         "Speaker leads: " + ROUTE["speaker"] + ".",
         "Jumpers are longer than the routes. Fold the slack in the right well above the floor lanes, away from the finger space over the BiBoard plugs."])
    img("11_wires_top.png", 0.36, "From the top, panel off: the wires in 3D.")

    h("6. Checks")
    h0, h1 = MO["head"]["free"]
    T = MO["tail"]
    lst([f"Slide: the empty body is clear of the robot at the click point, half way and at the drop-on place. "
         f"The clicks are about {K['lock_N']:g} N to lock and {K['unlock_N']:g} N to unlock (beam strain {K['strain_pct']:g} %).",
         f"Panel tabs: {S['close_N']:g} N to close (4 tabs, 30 deg lead), {S['open_one_end_N']:g} N to open one end (2 tabs, 45 deg catch), "
         f"tab strain {S['strain_pct']:g} %. Turned 180 deg, the panel does not go down.",
         "Install: the speaker, the mic, the amp and the stack each go straight down 40 mm without contact. The panel goes down without contact.",
         "Switch and button: the slider moves 2 mm each way without contact, and its fork pushes the lever after 0.3 mm. "
         "The button arm is 0.2 mm over the button; pressed 0.6 mm, it pushes the button.",
         f"Robot: the head turns from {h0} to {h1} deg without contact. {len(MO['legs']['front']['addon'])} front and "
         f"{len(MO['legs']['rear']['addon'])} rear leg poses (of 504) touch the add-on, only when a thigh swings up over the back. "
         f"The Petoi tail is {T['gap']:g} mm under the add-on, and {T['drop_on_gap']:g} mm at the drop-on place."])
    p("Open items: the BiBoard header height is an estimate (measure it). The speaker size is a ruler measurement. "
      "The mic port is assumed at the board center; the 7 holes cover ±2.2 mm. The SD card is assumed 2.5 mm out of its holder. "
      "To change the SD card, lift the stack out. The Pi power port and the PiSugar charge port are side by side: use one of them at a time.")

    h("7. Files and license")
    tbl([["File", "Content"],
         ["stl/print/", "the parts in print orientation"],
         ["cad/pod_body.step, cad/pod_panel.step", "the parts as STEP (from the mesh)"],
         ["cad/assembly_step.zip", "one STEP file with the robot, the platform and the add-on in place, with named and colored parts"],
         ["stl/installed/, stl/models/", "the parts and the electronics in the robot frame"],
         ["pod.py, motion.py, render.py, docs.py", "dimensions, build and checks; robot motion; pictures; this guide"],
         ], [62, 108])
    p("The printed parts, the drawings and this guide are CC BY 4.0, and the code is MIT (Jeremy Collins). "
      "The Pi Zero and PiSugar 2 fit models are from github.com/PiSugar/PiSugar (GPL-3.0). "
      "The Petoi parts are from github.com/PetoiCamp/NonCodeFiles, without a stated license. "
      "LICENSE.md and ATTRIBUTION.md in the repository give the details.")
    return X


WIRE_FROM = {("uart", "TX2"): "BiBoard TX2", ("uart", "RX2"): "BiBoard RX2", ("uart", "GND"): "BiBoard GND",
             ("amp", "G"): "amp G", ("amp", "V"): "amp V", ("amp", "BCLK"): "amp BCLK", ("amp", "LRC"): "amp LRC", ("amp", "DIN"): "amp DIN",
             ("mic", "SEL"): "mic SEL", ("mic", "LRCL"): "mic LRCL", ("mic", "DOUT"): "mic DOUT", ("mic", "BCLK"): "mic BCLK",
             ("mic", "GND"): "mic GND", ("mic", "3V"): "mic 3V", ("splice", "bclk"): "BCLK splice", ("splice", "lrclk"): "LRCLK splice",
             ("speaker", "+"): "amp speaker +", ("speaker", "-"): "amp speaker -"}
WIRE_TO = {("uart", "TX2"): "pin 10", ("uart", "RX2"): "pin 8", ("uart", "GND"): "pin 6", ("amp", "G"): "pin 14", ("amp", "V"): "pin 2",
           ("amp", "BCLK"): "BCLK splice", ("amp", "LRC"): "LRCLK splice", ("amp", "DIN"): "pin 40", ("mic", "SEL"): "pin 39",
           ("mic", "LRCL"): "LRCLK splice", ("mic", "DOUT"): "pin 38", ("mic", "BCLK"): "BCLK splice", ("mic", "GND"): "pin 9",
           ("mic", "3V"): "pin 1", ("splice", "bclk"): "pin 12", ("splice", "lrclk"): "pin 35", ("speaker", "+"): "speaker +",
           ("speaker", "-"): "speaker -"}
ROUTE = dict(uart="right well: along the floor to the right wall, up, rearward over the BiBoard plugs (each wire at its own height), down into them",
             amp="forward from the plug, down, across the floor in front of the front pegs (under the stack), then rearward in a floor lane of the right well",
             mic="up the back of the mic, right over the front post, rearward down the right well; the lowest wire leaves first",
             splice="short wire in the right well, up into the bottom of the splice sleeve",
             speaker="a pair: up the left side behind the amp, over the ear plate, into the top of the speaker")


def routing_figures():
    """Top view and right-well side view of the wire routes (stl/wires.json), numbered as in the route table."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    W = json.load(open(os.path.join(pod.OUT, "wires.json")))["wires"]
    def parts(a, view):
        boxes = [("battery", pod.BAT["x"], pod.BAT["z"], pod.BAT["y"], "#4a78d8"),
                 ("Pi + PiSugar", pod.PCB_X, (pod.STACK_ZF, pod.STACK_ZR), (pod.STACK_Y0, 60.0), "#2e9b4f"),
                 ("Pi header plugs", (pod.HDR_BASE_X[0], pod.HOUSING_END), pod.PI_PLUGS["z"], pod.PI_PLUGS["y"], "#555"),
                 ("BiBoard plugs", pod.BB_PLUG["x"], (pod.bb_pin_z(0) - 1.25, pod.bb_pin_z(2) + 1.25), pod.BB_PLUG["y"], "#d83a34"),
                 ("amp", (pod.AMP_X[0], pod.AMP_X[1] + 10.0), pod.AMP_Z, (pod.AMP_Y0, pod.AMP_Y0 + pod.AMP["h"]), "#1f5f8f"),
                 ("mic", (-pod.MIC["w"] / 2, pod.MIC["w"] / 2), pod.MIC_Z, (pod.MIC["y0"], pod.MIC["y0"] + pod.MIC["l"]), "#d83a34"),
                 ("speaker", (-pod.SPK["l"] / 2, pod.SPK["l"] / 2), (pod.SPK_ZE, pod.SPK_ZE + pod.SPK["ear_t"] + pod.SPK["h"]),
                  (pod.SPK_Y0, pod.SPK_Y0 + pod.SPK["d"]), "#7a52b8")]
        for name, xr, zr, yr, col in boxes:
            if view == "top":
                a.add_patch(Rectangle((zr[0], xr[0]), zr[1] - zr[0], xr[1] - xr[0], fc=col, alpha=0.18, ec=col, lw=0.6))
                a.text((zr[0] + zr[1]) / 2, (xr[0] + xr[1]) / 2, name, ha="center", va="center", fontsize=6, color=col, alpha=0.9)
            elif xr[1] > 15:
                a.add_patch(Rectangle((zr[0], yr[0]), zr[1] - zr[0], yr[1] - yr[0], fc=col, alpha=0.15, ec=col, lw=0.6))
                a.text((zr[0] + zr[1]) / 2, yr[1] - 1.2, name, ha="center", va="top", fontsize=6, color=col)
        for t in ("bclk", "lrclk"):
            x, z = pod.SPLICE[t]
            if view == "top":
                a.add_patch(Circle((z, x), pod.SPLICE["r"], fc="#222", alpha=0.6))
            else:
                a.add_patch(Rectangle((z - pod.SPLICE["r"], pod.SPLICE["y"][0]), 2 * pod.SPLICE["r"], 6.0, fc="#222", alpha=0.6))
    for view, fn in (("top", "13_routing_top.png"), ("side", "14_routing_side.png")):
        fig, a = plt.subplots(figsize=(7.2, 4.0 if view == "top" else 3.3), dpi=200)
        if view == "top":
            pl = pod.plan(pod.WALL)
            a.plot(np.r_[pl[:, 1], pl[0, 1]], np.r_[pl[:, 0], pl[0, 0]], color="0.4", lw=0.8)
            a.set_xlabel("Z (mm), front at the left"); a.set_ylabel("X (mm), robot right up")
            a.set_title("Wire routes from the top (numbers: route table)", fontsize=8)
        else:
            a.axhline(pod.FLOOR_Y1, color="0.4", lw=0.8); a.axhline(pod.PANEL_IN, color="0.4", lw=0.8, ls="--")
            a.text(-37, pod.PANEL_IN - 1.5, "panel underside", fontsize=6, color="0.4")
            a.set_xlabel("Z (mm), front at the left"); a.set_ylabel("Y (mm), up")
            a.set_title("Right well, seen from the right side (wires with X > 17)", fontsize=8)
        parts(a, view)
        for i, w in enumerate(W, 1):
            P = np.array(w["points"])
            if view == "side":
                keep = P[:, 0] > 17.0
                if not keep.any():
                    continue
                P = np.where(keep[:, None], P, np.nan)
            u, v = (P[:, 2], P[:, 0]) if view == "top" else (P[:, 2], P[:, 1])
            a.plot(u, v, color=w["color"] if w["color"] not in ("#f2f2ef",) else "#999", lw=1.4, solid_capstyle="round")
            ok = ~np.isnan(u)
            j = np.flatnonzero(ok)[len(np.flatnonzero(ok)) // 2]
            a.text(u[j], v[j], str(i), fontsize=5.5, ha="center", va="center",
                   bbox=dict(boxstyle="circle,pad=0.15", fc="white", ec=w["color"] if w["color"] != "#f2f2ef" else "#999", lw=0.6))
        a.set_aspect("equal"); a.tick_params(labelsize=6)
        a.set_xlim(-40, 58)
        if view == "side":
            a.set_ylim(25, 63)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, "doc", fn)); plt.close(fig)


def pod_mass(name):
    M = pod.mesh_to_manifold(pod.load_stl(os.path.join(pod.OUT, "installed", f"{name}.stl")))
    return f"{M.volume() * 1.24e-3:.0f}"


def main():
    PD.DOC = os.path.join(HERE, "doc")
    routing_figures()
    PD.TITLE = TITLE
    PD.DATE = DATE
    X = content()
    PD.write_md(X, os.path.join(HERE, "README.md"))
    PD.FOOTER = f"Bittle X Pi Add-on v{VERSION}"
    PD.write_pdf(X, os.path.join(HERE, "bittle_pi_addon_guide.pdf"))
    print("docs ready")


if __name__ == "__main__":
    main()
