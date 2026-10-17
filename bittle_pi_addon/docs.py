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

VERSION = "0.23"
DATE = datetime.date.today().isoformat()
TITLE = f"Bittle X Pi Add-on v{VERSION} - Build Guide"
VIEWER = "https://beetlebugorg.github.io/bittlex/viewer/"
CHECKS = json.load(open(os.path.join(pod.OUT, "checks.json")))


def usb_len():
    return next(w["length_mm"] for w in json.load(open(os.path.join(pod.OUT, "wires.json")))["wires"] if w["group"] == "camera")


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
      "It holds a Raspberry Pi Zero 2 W with a PiSugar 2 (1200 mAh), an NS4168 I2S amp with a 3 W speaker, an SPH0645 I2S mic and the Petoi AI Vision Module. "
      "The case is one rounded box (the body) and a slide-on top panel. The body clicks onto the platform pegs, and every part goes in from the top. "
      "No tools or supports are necessary; a dab of glue sets the amp.")
    img("02_addon.png", 0.5, "The add-on on the platform: the port windows in the panel. The mic holes are in the right side, near the front.")

    h("1. Parts to print")
    tbl([["File (stl/print/)", "Material", "Orientation", "Mass"],
         ["pod_body.stl", "PLA", "floor on the bed", f"{pod_mass('pod_body')} g"],
         ["pod_panel.stl", "PLA, second color", "upside down: top on the bed", f"{pod_mass('pod_panel')} g"],
         ["pod_button.stl", "PLA, white", "upside down: top on the bed", "0.1 g"],
         ["pod_logo_white.stl, pod_logo_red.stl", "PLA, white and red", "top on the bed (as in the STL)", "0.1 g each"],
         ["pod_camera_mount.stl", "PLA, second color", "on its back end (as in the STL)", f"{pod_mass('pod_camera_mount')} g"],
         ["cover_pegs_foot.stl (../bittle_platform)", "PLA", "stand on the rear end", "11 g"],
         ["Head off (optional): pod_camera_base_low.stl", "PLA, second color", "upside down (as in the STL)", f"{pod_mass('pod_camera_base_low')} g"],
         ["Head off (optional): pod_camera_cradle_low.stl", "PLA, white", "on its rear edges (as in the STL)", f"{pod_mass('pod_camera_cradle_low')} g"],
         ], [62, 34, 58, 16])
    p("Print every part with the Cura profile \"Bittle X\" (../cura/Bittle_X.curaprofile; 0.20 mm layers, no supports, 6-line brim). "
      "../cura/install_profiles.py installs it, and a copy with the size compensation of each spool that the tolerance app measured "
      "(\"Bittle X - <spool>\"). No part needs supports.")
    p(f"Print quality. The body and panel walls are 2.0 mm: with the offsets of the body profile, Cura slices 4 full lines of 0.5 mm. "
      "The body walls are vertical and its floor is on the bed. The only overhangs "
      f"({pr['pod_body']['overhang_mm2']:.0f} mm² in total) are the flat undersides of the two amp nubs (1.5 x 4 mm). "
      "The grille holes and the mic holes are teardrops (round, with a 45 deg point on top), so they print without bridges. "
      "The panel top edge round ends in a 45 deg chamfer at the bed, the port openings have 45 deg chamfers, and the lid hooks and the lugs in the body have 45 deg faces. The latch tongue bends along the layers of the panel. "
      f"Its overhangs ({pr['pod_panel']['overhang_mm2']:.0f} mm²) are short bridges at the button arm and the lid hooks. "
      "The camera mount has short bridges at the clip hooks and a 45 deg chin; the hooks over the case are 45 deg wedges. "
      "The cradle of the head-off mount stands on its dovetail tabs: its floor is a 30 mm bridge 1.4 mm over the bed. Keep the seam at the rear.")

    h("2. Electronics")
    tbl([["Part", "Place"],
         ["Raspberry Pi Zero 2 W + PiSugar 2, 1200 mAh", f"On the long edge over the robot center, {pod.STACK_DX:g} mm left of the center line so the battery is near it: ports and PiSugar controls up, "
          "GPIO header down to the left (toward the BiBoard), SD card to the rear. Two end posts hold the boards in one groove, the same depth for both boards; "
          "the M2.5 screw heads go down channels in the posts. The pin-fin heatsink on the SoC points into the left well (14 x 14 x 6.5 mm, estimated)."],
         ["Dupont jumpers", "Female-female jumpers: 3 to the BiBoard, 6 to the mic (2 of them through the splices). 10 cm, but 15 cm for the mic GND and 3V."],
         ["NULLLAB NS4168 I2S amp", "38.4 x 22.4 mm board, on edge along the right wall, parts to the inside, in a slot bar on the floor, "
          "upright with its screw terminal at the top. Two nubs hold its top edge. "
          "Its PH2.0 connectors are side entry: the I2S cable plugs in at the front end, the speaker at the rear end."],
         ["NULLLAB 3 W 4 ohm speaker", f"At the rear, sound to the grille in the rear face. Body {pod.SPK['body_l']:g} wide, {pod.SPK['h']:g} deep. Two tapered wings ({pod.SPK['l']:g} across, "
          f"{pod.SPK['ear_t']:g} thick) at the middle of the body depth stand in two side grooves."],
         ["HiLetgo SPH0645 I2S mic", f"{pod.MIC['w']:g} x {pod.MIC['l']:g} board, high on the right wall near the front, port to the wall (holes in the right side). "
          "Its straight 6-pin header is along its front edge: the plugs point inward, and the wires go straight across behind the front wall. "
          "3V is the lowest pin, SEL the highest. It drops into a slot in a post (rear edge) and a ledge (bottom edge); a fork under the panel holds its top edge. No tools."],
         ["Petoi AI Vision Module", "In its Petoi case, vertical on the camera mount at the front of the panel, lens forward over the head, USB port at the top. "
          f"It stands {abs(pod.CAM['cx']):g} mm right of the center line: it is then clear of the PiSugar charge port and the Pi power port. "
          "Two side brackets hold the case; a hook on each snaps over a top corner of the case, clear of the USB port. The case cannot lift out."],
         ["USB cable, USB-C to micro-USB", f"From the USB-C port in the top of the camera, an arch rearward over the panel, down into the Pi data USB port. "
          f"Modeled length {usb_len():.0f} mm between the plugs."],
         ], [52, 118])

    B = CHECKS["balance"]
    x, y, z = B["com"]
    p(f"Balance. The add-on weighs {B['mass_g']:.0f} g with the camera (weighed parts; printed parts at 50 % fill). "
      f"Its center of mass is {z:.1f} mm behind the robot center and {abs(x):.1f} mm {'left' if x < 0 else 'right'} of the center line, "
      f"{y - PI.COVER_TOP:.0f} mm above the cover top. With the add-on, the center of mass of the robot is about 4 mm behind the midpoint "
      "of the front and rear paws (110 mm apart), and on the center line. The side is the limit when the robot tips: keep heavy parts low. "
      "Put your own masses in MASS_G in pod.py and run pod.py again.")

    h("3. Assembly")
    st = lambda n: f" ([viewer step {n}]({VIEWER}#step={n}))"
    p(f"The 3D viewer shows each step with animation: [{VIEWER}#step=1]({VIEWER}#step=1). "
      "Labels are cut into the inside of the body: MIC, AMP, SPEAKER and BIBOARD where each part goes, PIN 1 and PIN 40 at the ends "
      "of the Pi header, and grooves in the floor for the amp cable lanes and the mic wire run.")
    lst(["Fit the platform cover in place of the stock cover." + st(2),
         f"Put the empty body on the pegs {PI.SLIDE:g} mm behind its place, grille to the rear. Slide it {PI.SLIDE:g} mm forward until it clicks "
         f"(about {K['lock_N']:g} N). The BiBoard header is now in the notch at the front of the left well." + st(3) + st(4),
         "Push the speaker down into the two side grooves at the rear, body to the rear." + st(5),
         "Plug the six mic jumpers onto the mic header: 15 cm jumpers on GND and 3V. Drop the mic into the slots in the post and the ledge "
         "on the right wall near the front, port to the wall, header at the front. The panel holds it later." + st(6),
         "Plug the amp cable into the I2S connector at the front end of the amp and the speaker into its rear end. Put the bottom edge of the amp into the slot along the right wall, "
         "parts to the inside, tilt its top edge under the two nubs, and set it with a dab of glue. "
         "Lay the flat amp cable across the floor in front of the front pegs, into the left well, G at the rear." + st(7),
         "Push the Pi + PiSugar 2 stack down into the end grooves, over the amp cable." + st(8),
         "Plug the wires one at a time, in the order of section 5: the amp cable, the splices, the Pi ends of the BiBoard jumpers, the mic jumpers, "
         "then the BiBoard ends. The viewer has one step for each wire." + st(9) + st(21),
         "Press the post of the white button cap into the round hole in the panel tongue until the cap sits flat. It stays in the panel. "
         "Glue the two logo inlays into the pocket in the panel top, behind the camera: the white ring and M at the left, the red ring and J at the right." + st(22),
         f"Put the panel down {pod.LID_SLIDE:g} mm behind its place, then slide it forward until the latch clicks (about {S['slide_on_N']:g} N). "
         "The hooks under the panel go under the lugs in the walls." + st(23),
         "Push the two clip legs of the camera mount down through the window until they click. "
         "Push the camera case down between the brackets, lens forward and USB port up, until the hooks click over its top." + st(24) + st(25),
         "Plug the USB-C end of the cable into the top of the camera and the micro-USB end into the Pi data USB port. "
         "The cable arches rearward over the panel." + st(26),
         f"Open: lift the rear edge of the panel at the finger notch (about {S['lift_N']:g} N), slide the panel {pod.LID_SLIDE:g} mm rearward and lift it. "
         f"Remove: open the panel, pull the BiBoard plugs off, slide the body {PI.SLIDE:g} mm rearward and lift it."])
    p("On the top: the port openings are shaped to the plug bodies (plug + 0.4 mm). The Pi power port and the PiSugar charge port share one opening, behind the camera. "
      "The window beside the HDMI opening shows the PiSugar power switch: move its lever with a fingernail. "
      "The tongue in the middle of the panel is a large button: press it to press the PiSugar button.")
    img("04_top.png", 0.42, "The top: the camera, charge and Pi power, data USB, the button tongue, the switch window and HDMI.")
    p("Head off (optional). Without the Petoi head, the camera can stand lower, in front of the body: pod_camera_base_low clips into the "
      "camera window as the camera mount does, and its front plate hangs down the front of the body. Slide the two dovetail tabs of pod_camera_cradle_low "
      "down into its grooves until the cradle sits on the top of the base. Push a 1.75 mm filament piece through the pin hole on each side. "
      "Push the camera down into the cradle until the hooks click. Plug the USB cable into the top of the camera and into the Pi data USB port.")
    img("17_camera_low.png", 0.42, "Head off: the camera lower and in front of the body.")

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
    pack = [w for w in ws if w.get("pack")]
    p(f"The BiBoard and mic wires are female-female jumpers from a pack of {WR['pack_l'] / 10:g} cm wires; the mic GND and 3V jumpers are {WR['long_l'] / 10:g} cm. The amp keeps its own cable, "
      "and the two splices are cut from pack jumpers. pod.py models every wire "
      f"({WR['wire_d']:g} mm) at its real length and checks it: no wire touches a printed part or a board, no two wires pass through each "
      f"other ({len(WR['crossings'])} found), and no bend is smaller than {WR['r_bend']:g} mm radius ({WR['r_slack']:g} mm in the slack). "
      "A pack jumper is longer than its route, so its excess is an arch or a coil (a service loop) in free space. "
      "The pages below show each module: its pins, then its wires in the case.")
    for i, mod in enumerate(MODULES):
        img(f"15_wiring_{i}.png", 0.95, "")
    cells = []
    for i, w in enumerate(ws, 1):
        key = (w["group"], w["wire"])
        extra = f" ({w['slack']})" if w.get("pack") else ""
        cells.append([str(i), WIRE_FROM[key], WIRE_TO[key] + extra, f"{w['length_mm']:.0f}"])
    half = (len(cells) + 1) // 2
    rows = [["#", "From", "To (excess)", "mm"] * 2]
    for k in range(half):
        rows.append(cells[k] + (cells[k + half] if k + half < len(cells) else ["", "", "", ""]))
    tbl(rows, [6, 24, 34, 8] * 2)
    order = [tuple(k) for k in WR["order"]]
    num = {(w["group"], w["wire"]): i for i, w in enumerate(ws, 1)}
    p("Plug the jumpers one at a time, in this order. Each wire goes to its place before the next one, so the later wires lie over the earlier ones:")
    lst([f"#{num[k]}: {WIRE_FROM[k]} to {WIRE_TO[k]}" + (f". Put its excess in a {[w for w in ws if (w['group'], w['wire']) == k][0]['slack']} as in the drawing."
                                                          if k in {(w['group'], w['wire']) for w in pack} else ". Cut to length.")
         for k in order] + ["Last, push the BiBoard ends of #%d, #%d and #%d onto the BiBoard header." % tuple(num[k] for k in order if k[0] == "uart")])
    lst(["The mic has a straight header along its front edge. Plug the six mic jumpers onto it before the mic goes in. "
         "Mic wires: " + ROUTE["mic"] + ".",
         "Amp cable: " + ROUTE["amp"] + ". Lay it before the stack goes in. Its own excess (not measured) folds in the right gallery over the amp.",
         "Splices: the LRCLK splice stands beside the BiBoard plugs, the BCLK splice at the middle of the left well.",
         "The BiBoard wires go in first, from the lowest: TX2, RX2, then GND. Their BiBoard ends go on last: a Pi housing for the mic slides off its pin past them.",
         "The mic wires go in from the lowest of the stack: 3V, GND, BCLK, DOUT, LRCL, then SEL."])
    img("11_wires_top.png", 0.36, "From the top, panel off: the wires in 3D.")
    img("16_camera_cable.png", 0.42, "The USB cable of the camera: from the top of the camera, over the panel, into the Pi data USB port.")

    h("6. Checks")
    h0, h1 = MO["head"]["free"]
    T = MO["tail"]
    lst([f"Slide: the empty body is clear of the robot at the click point, half way and at the drop-on place. "
         f"The clicks are about {K['lock_N']:g} N to lock and {K['unlock_N']:g} N to unlock (beam strain {K['strain_pct']:g} %).",
         f"Panel: it goes down {pod.LID_SLIDE:g} mm behind its place and slides forward without contact. "
         f"The latch tongue lifts {S['lift_mm']:g} mm over the rib: about {S['slide_on_N']:g} N to slide on, {S['lift_N']:g} N to lift, strain {S['strain_pct']:g} %. "
         "Lifted 0.3 mm, the hooks touch the lugs. Turned 180 deg, the panel does not go down.",
         "Install: the speaker and the stack each go straight down 40 mm without contact. The mic drops into its slots; the post, the ledge, a stop and the panel fork hold it on every side. "
         "The amp tilts in under its nubs. "
         "Each wire, in its order, goes in from 40 mm above without contact with the parts and wires already in place "
         "(small contacts of 2 to 3 mm³ stay where a wire slides under a loose service loop). Each Dupont housing slides off its pin without contact.",
         "Camera: the case goes into the mount without contact and is clear of the port plugs. Lifted 0.3 mm, its top hits the hooks. "
         "The brackets spread 4.8 mm as the case goes in (about 0.5 % strain). "
         "The clip leg hooks catch 0.8 mm under the frame on a 10 deg barb, so a pull pushes them out; the legs bend to 1.9 % strain. "
         "The USB cable touches no part and no other wire. The head turns without contact with the mount and the cable.",
         "Head-off mount: the base, the cradle, the camera and its cable touch no part of the robot without its head. "
         "The cradle slides down into the grooves without contact; the pins stop it from lifting.",
         "Switch and button: the switch lever is under the window over its full travel. "
         "The button arm is 0.2 mm over the button; pressed 0.6 mm, it pushes the button.",
         f"Robot: the head turns from {h0} to {h1} deg without contact. {len(MO['legs']['front']['addon'])} front and "
         f"{len(MO['legs']['rear']['addon'])} rear leg poses (of 504) touch the add-on, only when a thigh swings up over the back. "
         f"The Petoi tail is {T['gap']:g} mm under the add-on, and {T['drop_on_gap']:g} mm at the drop-on place."])
    p("Open items: the BiBoard header height is an estimate (measure it). The speaker size is a ruler measurement. "
      "The mic port is assumed at the board center; the 7 holes cover ±2.2 mm. The SD card is assumed 2.5 mm out of its holder. "
      "The heatsink and the screw heads (4.6 x 1.8 mm) are estimates. The camera hooks catch the top of the case of the STL. "
      "To change the SD card, lift the stack out. The Pi power port and the PiSugar charge port are side by side: use one of them at a time.")

    h("7. Files and license")
    tbl([["File", "Content"],
         ["stl/print/", "the parts in print orientation"],
         ["cad/*.step", "the parts as STEP (from the mesh)"],
         ["cad/assembly_step.zip", "one STEP file with the robot, the platform and the add-on in place, with named and colored parts"],
         ["stl/installed/, stl/models/", "the parts and the electronics in the robot frame"],
         ["pod.py, motion.py, render.py, docs.py", "dimensions, build and checks; robot motion; pictures; this guide"],
         ], [62, 108])
    p("The printed parts, the drawings and this guide are CC BY 4.0, and the code is MIT (Jeremy Collins). "
      "The Pi Zero and PiSugar 2 fit models are from github.com/PiSugar/PiSugar (GPL-3.0). "
      "The Petoi parts are from github.com/PetoiCamp/NonCodeFiles, without a stated license. "
      "LICENSE.md and ATTRIBUTION.md in the repository give the details.")
    return X


WIRE_FROM, WIRE_TO = pod.WIRE_FROM, pod.WIRE_TO
MX = lambda r: (-r[1], -r[0])          # pod.py numbers are in its design frame (X turned over): to the robot frame
ROUTE = dict(uart="left well: up out of the BiBoard plugs to the left wall, rearward (each wire at its own height), down, into the Pi header",
             amp="a flat cable: forward out of the plug, it rolls to lie flat as it goes down, then flat across the floor in front of the front pegs (under the stack), G at the rear and DIN at the front; in the left well each wire goes rearward in its own floor lane, and DIN goes up at once",
             mic="straight inward out of the mic plugs, across behind the front wall in front of the stack, "
                 "then rearward as a flat stack in the left well beside the BiBoard plugs; each wire stays at the height of its pin",
             splice="short wire in the left well, up into the bottom of the splice sleeve",
             speaker="a pair: up the right side behind the amp, over the ear plate, into the top of the speaker")


def routing_figures():
    """Top view and right-well side view of the wire routes (stl/wires.json), numbered as in the route table."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    W = json.load(open(os.path.join(pod.OUT, "wires.json")))["wires"]
    def parts(a, view):
        boxes = [("battery", MX(pod.BAT["x"]), pod.BAT["z"], pod.BAT["y"], "#4a78d8"),
                 ("Pi + PiSugar", MX(pod.PCB_X), (pod.STACK_ZF, pod.STACK_ZR), (pod.STACK_Y0, 60.0), "#2e9b4f"),
                 ("Pi header plugs", MX((pod.HDR_BASE_X[0], pod.HOUSING_END)), pod.PI_PLUGS["z"], pod.PI_PLUGS["y"], "#555"),
                 ("BiBoard plugs", MX(pod.BB_PLUG["x"]), sorted((pod.bb_pin_z(0) + 1.25, pod.bb_pin_z(2) - 1.25)), pod.BB_PLUG["y"], "#d83a34"),
                 ("amp", MX((pod.AMP_X[0], pod.AMP_X[1] + 10.0)), pod.AMP_Z, (pod.AMP_Y0, pod.AMP_Y0 + pod.AMP["h"]), "#1f5f8f"),
                 ("mic", MX(pod.MIC_X), (pod.MIC["z0"], pod.MIC["z0"] + pod.MIC["w"]), (pod.MIC["y0"], pod.MIC["y0"] + pod.MIC["l"]), "#d83a34"),
                 ("speaker", (-pod.SPK["l"] / 2, pod.SPK["l"] / 2), (pod.SPK_ZE, pod.SPK_ZE + pod.SPK["ear_t"] + pod.SPK["h"]),
                  (pod.SPK_Y0, pod.SPK_Y0 + pod.SPK["d"]), "#7a52b8")]
        for name, xr, zr, yr, col in boxes:
            if view == "top":
                a.add_patch(Rectangle((zr[0], xr[0]), zr[1] - zr[0], xr[1] - xr[0], fc=col, alpha=0.18, ec=col, lw=0.6))
                a.text((zr[0] + zr[1]) / 2, (xr[0] + xr[1]) / 2, name, ha="center", va="center", fontsize=6, color=col, alpha=0.9)
            elif xr[0] < -15:
                a.add_patch(Rectangle((zr[0], yr[0]), zr[1] - zr[0], yr[1] - yr[0], fc=col, alpha=0.15, ec=col, lw=0.6))
                a.text((zr[0] + zr[1]) / 2, yr[1] - 1.2, name, ha="center", va="top", fontsize=6, color=col)
        for t in ("bclk", "lrclk"):
            x, z = pod.SPLICE[t]
            x = -x
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
            a.set_title("Left well, seen from the left side (wires with X < -17)", fontsize=8)
        parts(a, view)
        for i, w in enumerate(W, 1):
            P = np.array(w["points"])
            if view == "side":
                keep = P[:, 0] < -17.0
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


# Wiring guide for each module: (title, wire groups, connector pins in order (label, Pi pin or splice), note)
MODULES = [
    ("BiBoard serial link", ("uart",), "BiBoard header", [("TX2", 10), ("RX2", 8), ("GND", 6), ("+5V", None), ("+5V", None)],
     "TX and RX cross. The +5V pins are not wired: the PiSugar 2 powers the Pi."),
    ("Amp: I2S and power", ("amp", "splice"), "amp I2S plug", [("G", 14), ("V", 2), ("BCLK", "bclk"), ("LRC", "lrclk"), ("DIN", 40)],
     "BCLK and LRC go to the splices: one wire from Pi pin 12 (35) feeds the amp and the mic."),
    ("Mic", ("mic", "splice"), "mic pins", [("3V", 1), ("GND", 9), ("BCLK", "bclk"), ("DOUT", 38), ("LRCL", "lrclk"), ("SEL", 39)],
     "SEL to GND sets the left channel. BCLK and LRCL go to the splices."),
    ("Speaker", ("speaker",), "amp speaker plug", [("+", "spk+"), ("-", "spk-")],
     "A two-wire lead from the 2-pin plug at the rear end of the amp to the speaker."),
]
SPLICE_PIN = dict(bclk=12, lrclk=35)


def _fonts():
    import matplotlib
    from matplotlib import font_manager
    for f in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf", "NotoSansMono-Regular.ttf"):
        path = os.path.join("/usr/share/fonts/noto", f)
        if os.path.exists(path):
            font_manager.fontManager.addfont(path)
    matplotlib.rcParams.update({"font.family": "Noto Sans", "font.size": 7, "axes.titlesize": 8, "axes.titleweight": "medium",
                                "axes.edgecolor": "#c8ccd2", "axes.linewidth": 0.6})


def _wire_col(c):
    return "#a9adb3" if c.lower() in ("#f2f2ef", "#ffffff") else c


def _rpath(pts, r=0.45):
    P, _ = pod.round_corners([(x, y, 0.0) for x, y in pts], r)
    return P[:, 0], P[:, 1]


def module_figure(mod, path):
    """One block for each module: the pin diagram (its connector to the Pi header) and its routes in the case."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import patheffects as pe
    from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
    _fonts()
    title, groups, conn, pins, note = mod
    g0 = groups[0]
    W = json.load(open(os.path.join(pod.OUT, "wires.json")))["wires"]
    col_of = {(w["group"], w["wire"]): _wire_col(w["color"]) for w in W}
    casing = [pe.Stroke(linewidth=3.6, foreground="white"), pe.Normal()]
    ink, mute, line = "#1b1f27", "#6b717b", "#c9cdd3"
    fig = plt.figure(figsize=(7.4, 5.0), dpi=220)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.1], width_ratios=[1.0, 1.0], hspace=0.22, wspace=0.06,
                          left=0.02, right=0.98, top=0.93, bottom=0.02)
    fig.text(0.02, 0.965, title, fontsize=10.5, fontweight="bold", color=ink, va="center")
    fig.text(0.98, 0.965, note, fontsize=6.6, color=mute, va="center", ha="right")
    # ---- pin diagram
    a = fig.add_subplot(gs[0, :])
    a.set_axis_off()
    a.set_xlim(-14.5, 52.5)
    a.set_ylim(-8.4, 11.4)
    X0, PITCH, Y_ODD, Y_EVEN, H = 13.0, 1.95, 5.0, 3.0, 0.78
    px = lambda n: X0 + ((n - 1) // 2) * PITCH
    py = lambda n: Y_ODD if n % 2 else Y_EVEN
    cy = [1.1 - 1.45 * i for i in range(len(pins))]
    used_all = {int(v.split()[1]) for v in WIRE_TO.values() if v.startswith("pin ")}
    if g0 != "speaker":
        mine = {}
        for lab, t in pins:
            if t is not None:
                mine[SPLICE_PIN[t] if isinstance(t, str) else t] = col_of[(g0, lab)]
        a.add_patch(FancyBboxPatch((X0 - 1.3, Y_EVEN - 1.3), 19 * PITCH + 2.6, Y_ODD - Y_EVEN + 2.6,
                                   boxstyle="round,pad=0,rounding_size=0.5", fc="#26292f", ec="none", zorder=1))
        for n in range(1, 41):
            fill = mine.get(n)
            fc = fill if fill else ("#3c4048" if n in used_all else "#2f3239")
            a.add_patch(FancyBboxPatch((px(n) - H, py(n) - H), 2 * H, 2 * H, boxstyle="round,pad=0,rounding_size=0.22",
                                       fc=fc, ec="white" if fill else "#454a53", lw=0.8 if fill else 0.5, zorder=2))
            a.text(px(n), py(n), str(n), ha="center", va="center", fontsize=5.6, zorder=3,
                   color="white" if fill else "#8d939c", fontweight="bold" if fill else "normal")
        a.text(X0 - 1.6, Y_ODD, "odd", ha="right", va="center", fontsize=5.6, color=mute)
        a.text(X0 - 1.6, Y_EVEN, "even", ha="right", va="center", fontsize=5.6, color=mute)
        n_odd = sum(1 for _, t in pins if t is not None and (SPLICE_PIN[t] if isinstance(t, str) else t) % 2)
        ycap = Y_ODD + 2.4 + 0.6 * n_odd
        a.text(X0 - 1.3, ycap + 1.0, "Pi Zero 2 W header, as it stands in the case", fontsize=7, color=ink, fontweight="medium")
        a.text(X0 - 1.3, ycap, "pin 1 at the SD card end (rear), even row at the board edge (down)", fontsize=6, color=mute)
    # connector
    a.add_patch(FancyBboxPatch((-13.8, cy[-1] - 1.0), 8.2, cy[0] - cy[-1] + 2.0, boxstyle="round,pad=0,rounding_size=0.6",
                               fc="#f4f5f7", ec=line, lw=0.8, zorder=1))
    a.text(-13.8, cy[0] + 1.6, conn, fontsize=7, color=ink, fontweight="medium")
    odd_j = 0
    for (lab, t), y in zip(pins, cy):
        col = col_of.get((g0, lab), "#b9bdc4") if t is not None else "#b9bdc4"
        a.text(-13.0, y, lab, va="center", fontsize=7.2, fontweight="medium", color=ink, zorder=3)
        a.add_patch(Circle((-6.6, y), 0.42, fc=col if t is not None else "white", ec=col, lw=0.9, zorder=4))
        if t is None:
            a.text(-5.7, y, "not wired", va="center", fontsize=6, color="#9aa0a8")
            continue
        if g0 == "speaker":
            xs, ys = [-6.2, 28.0], [y, y]
            a.plot(xs, ys, color=col, lw=2.4, solid_capstyle="round", path_effects=casing, zorder=3)
            a.add_patch(Circle((28.4, y), 0.42, fc=col, ec=col, zorder=4))
            a.text(29.4, y, "speaker " + lab, va="center", fontsize=7.2, color=ink)
            continue
        n = SPLICE_PIN[t] if isinstance(t, str) else t
        if n % 2 == 0:                                     # even pins: along the lane, up into the pin
            pts = [(-6.2, y), (px(n), y), (px(n), Y_EVEN - H)]
            node = (px(n), y)
        else:                                              # odd pins: up at the left, over the header, down into the pin
            xt, yt = X0 - 4.6 - 0.7 * odd_j, Y_ODD + 1.6 + 0.6 * odd_j
            odd_j += 1
            pts = [(-6.2, y), (xt, y), (xt, yt), (px(n), yt), (px(n), Y_ODD + H)]
            node = (px(n), yt)
        xs, ys = _rpath(pts)
        a.plot(xs, ys, color=col, lw=2.2, solid_capstyle="round", path_effects=casing, zorder=5)
        if isinstance(t, str):                             # the splice joins this wire, the Pi wire and the other board
            other = "mic" if g0 == "amp" else "amp"
            sgn = -1 if node[0] > 38 else 1                  # near the right edge: the stub and the label go to the left
            ex, ey = node[0] + sgn * 2.6, node[1] + (-1.2 if n % 2 == 0 else 0.9)
            a.plot([node[0], ex], [node[1], ey], color=col, lw=1.6, ls=(0, (2, 1.2)), zorder=4)
            a.add_patch(Circle(node, 0.5, fc="#1b1f27", ec="white", lw=0.9, zorder=6))
            a.text(ex + sgn * 0.3, ey, f"splice, to the {other}", va="center", ha="left" if sgn > 0 else "right", fontsize=5.8, color=mute)
    # ---- route views
    mineW = [w for w in W if w["group"] in groups]
    allP = np.concatenate([np.array(w["points"]) for w in mineW])
    side_x = (lambda P: P[:, 0] < -17.0) if g0 != "speaker" else (lambda P: P[:, 0] > 9.0)
    for ci, view in enumerate(("top", "side")):
        b = fig.add_subplot(gs[1, ci])
        b.set_xticks([]); b.set_yticks([])
        for sp in b.spines.values():
            sp.set_visible(False)
        if view == "top":
            pl = pod.plan(pod.WALL)
            b.fill(pl[:, 1], pl[:, 0], fc="#fafbfc", ec="#b3b8c0", lw=0.9, zorder=0)
            b.set_title("From the top, panel off (front at the left)", loc="left", color=ink, fontsize=7.4)
        else:
            b.add_patch(Rectangle((pod.ZF_IN, pod.FLOOR_Y1), pod.ZR_IN - pod.ZF_IN, pod.PANEL_IN - pod.FLOOR_Y1, fc="#fafbfc", ec="#b3b8c0", lw=0.9, zorder=0))
            b.set_title(("Left well, seen from the left" if g0 != "speaker" else "Right side, seen from the right") + " (front at the left)",
                        loc="left", color=ink, fontsize=7.4)
        _parts(b, view, left=(g0 == "speaker"))
        for w in W:
            P = np.array(w["points"])
            if view == "side":
                P = np.where(side_x(P)[:, None], P, np.nan)
            u, v = (P[:, 2], P[:, 0]) if view == "top" else (P[:, 2], P[:, 1])
            if w["group"] in groups:
                b.plot(u, v, color=_wire_col(w["color"]), lw=2.0, solid_capstyle="round", zorder=4, path_effects=casing)
                ok = np.flatnonzero(~np.isnan(u))
                if not len(ok):
                    continue
                if view == "side" and w["group"] != "speaker" and side_x(np.array(w["points"])[-1:])[0]:
                    k = ok[-1]
                    lbl = WIRE_TO[(w["group"], w["wire"])].replace("pin ", "")
                    if not lbl.endswith("splice"):
                        b.annotate(lbl, (u[k], v[k]), xytext=(0, -7), textcoords="offset points", ha="center", fontsize=5.4,
                                   color=ink, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=_wire_col(w["color"]), lw=0.6), zorder=6)
            else:
                b.plot(u, v, color="#e1e4e8", lw=1.0, zorder=2)
        b.set_aspect("equal")
        if view == "top":
            b.set_xlim(-39, 57); b.set_ylim(-31, 31)
        else:
            Q = allP[side_x(allP)]
            z0, z1 = (Q[:, 2].min() - 6, Q[:, 2].max() + 6) if len(Q) else (-39, 57)
            b.set_xlim(max(z0, -39), min(z1, 57)); b.set_ylim(26, 63)
    fig.savefig(path)
    plt.close(fig)


def _parts(a, view, left=False):
    """Light silhouettes of the parts, for the route views (side views: the parts on that side)."""
    from matplotlib.patches import FancyBboxPatch
    boxes = [("battery", MX(pod.BAT["x"]), pod.BAT["z"], pod.BAT["y"]),
             ("Pi + PiSugar", MX(pod.PCB_X), (pod.STACK_ZF, pod.STACK_ZR), (pod.STACK_Y0, 60.0)),
             ("Pi header", MX((pod.HDR_BASE_X[0], pod.HOUSING_END)), pod.PI_PLUGS["z"], pod.PI_PLUGS["y"]),
             ("BiBoard", MX(pod.BB_PLUG["x"]), sorted((pod.bb_pin_z(0) + 1.25, pod.bb_pin_z(2) - 1.25)), pod.BB_PLUG["y"]),
             ("amp", MX((pod.AMP_X[0], pod.AMP_X[1] + 10.0)), pod.AMP_Z, (pod.AMP_Y0, pod.AMP_Y0 + pod.AMP["h"])),
             ("mic", MX(pod.MIC_X), (pod.MIC["z0"], pod.MIC["z0"] + pod.MIC["w"]), (pod.MIC["y0"], pod.MIC["y0"] + pod.MIC["l"])),
             ("speaker", (-pod.SPK["l"] / 2, pod.SPK["l"] / 2), (pod.SPK_ZE, pod.SPK_ZE + pod.SPK["ear_t"] + pod.SPK["h"]),
              (pod.SPK_Y0, pod.SPK_Y0 + pod.SPK["d"]))]
    for t in ("bclk", "lrclk"):
        x, z = pod.SPLICE[t]
        x = -x
        r, (y0, y1) = pod.SPLICE["r"], pod.SPLICE["y"]
        rect = (z - r, x - r, 2 * r, 2 * r) if view == "top" else (z - r, y0, 2 * r, y1 - y0)
        if view == "top" or not left:
            a.add_patch(FancyBboxPatch(rect[:2], rect[2], rect[3], boxstyle="round,pad=0,rounding_size=0.6", fc="#2a2d33", ec="white",
                                       lw=0.6, zorder=5))
    for name, xr, zr, yr in boxes:
        if view == "top":
            r = (zr[0], xr[0], zr[1] - zr[0], xr[1] - xr[0])
        elif (xr[1] > 9 if left else xr[0] < -15):
            r = (zr[0], yr[0], zr[1] - zr[0], yr[1] - yr[0])
        else:
            continue
        a.add_patch(FancyBboxPatch(r[:2], r[2], r[3], boxstyle="round,pad=0,rounding_size=0.8", fc="#eceef1", ec="#d3d7dc", lw=0.5, zorder=1))
        a.text(r[0] + r[2] / 2, r[1] + r[3] / 2, name, ha="center", va="center", fontsize=5.6, color="#8a9099", zorder=1, clip_on=True)


def pod_mass(name):
    M = pod.mesh_to_manifold(pod.load_stl(os.path.join(pod.OUT, "installed", f"{name}.stl")))
    return f"{M.volume() * 1.24e-3:.0f}"


def main():
    PD.DOC = os.path.join(HERE, "doc")
    routing_figures()
    for i, mod in enumerate(MODULES):
        module_figure(mod, os.path.join(HERE, "doc", f"15_wiring_{i}.png"))
    PD.TITLE = TITLE
    PD.DATE = DATE
    X = content()
    PD.write_md(X, os.path.join(HERE, "README.md"))
    PD.FOOTER = f"Bittle X Pi Add-on v{VERSION}"
    PD.write_pdf(X, os.path.join(HERE, "bittle_pi_addon_guide.pdf"))
    print("docs ready")


if __name__ == "__main__":
    main()
