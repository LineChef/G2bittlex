"""Bittle X Pi add-on: README.md and bittle_pi_addon_guide.pdf from one content list.

Run pod.py and render.py first, then:  python docs.py
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import pod                                   # noqa: E402
from bittle_platform import docs as PD       # noqa: E402  (writers shared with the platform)
from bittle_platform import interface as PI  # noqa: E402

VERSION = "0.11"
DATE = datetime.date.today().isoformat()
TITLE = f"Bittle X Pi Add-on v{VERSION} - Build Guide"
VIEWER = "https://beetlebugorg.github.io/bittlex/viewer/"
CHECKS = json.load(open(os.path.join(pod.OUT, "checks.json")))


def content():
    pr = CHECKS["printing"]
    X = []
    h = lambda t: X.append(("h", t))
    p = lambda t: X.append(("p", t))
    tbl = lambda rows, w: X.append(("table", rows, w))
    img = lambda f, w=1.0, cap="": X.append(("img", f, w, cap))
    lst = lambda items: X.append(("list", items))

    p(f"Version {VERSION}, {DATE}. A sample add-on for the Bittle X platform v{PI.VERSION} (../bittle_platform). "
      "It carries a Raspberry Pi Zero 2 W with a PiSugar 2 (1200 mAh), an NS4168 I2S amp with a 3 W speaker, and an SPH0645 I2S mic. "
      "It clicks onto the platform pegs. No tools, glue, tape or supports are necessary.")
    img("02_ports_right.png", 0.72, "The add-on on the platform, right side: the two port bays.")

    h("1. Parts to print")
    tbl([["File (stl/print/)", "Material", "Orientation", "Supports", "Cura profile", "Mass"],
         ["pod_tray.stl", "PLA or PETG", "floor on the bed", "none", "Bittle Pi Pod - PLA 0.25", f"{pod_mass('pod_tray')} g"],
         ["pod_lid.stl", "PLA", "upside down: flat top on the bed", "none", "Bittle Pi Pod 0.25, or Bittle Fine 0.10 for the best surface", f"{pod_mass('pod_lid')} g"],
         ["cover_pegs.stl (../bittle_platform)", "PLA", "stand on the rear end", "tree, from the bed", "Bittle Cover - PLA 0.25", "11 g"],
         ], [38, 20, 34, 16, 44, 14])
    p("Print quality. Every surface of the add-on parts is at 45 deg or less from vertical, or is a short bridge:")
    lst([f"Tray: {pr['pod_tray']['overhang_mm2']:.0f} mm² of overhang in total. These are the flat bottoms (1.0 wide) of the amp pins. The speaker pins have a 45 deg point at the bottom.",
         f"Lid: {pr['pod_lid']['overhang_mm2']:.0f} mm² in total. These are the tops (in the print) of the camera cable slot (a 6 mm bridge) and the speaker grille slots. The profiles have the bridge settings on. The floors of the port bays are 45 deg slopes.",
         "The mic holes in the left lid wall are diamonds, so they print clean without a bridge.",
         "The slots for the mic board and the speaker ear plate are vertical in the print. They have no ceilings.",
         "Keep the seam at the back (the profiles do this)."])

    h("2. Electronics")
    tbl([["Part", "Notes"],
         ["Raspberry Pi Zero 2 W", "No header. Solder the wires to the pads, flat along the GPIO edge."],
         ["PiSugar 2, 1200 mAh", "Under the Pi (pogo pins and its screws). The charge port, button and switch face the right side."],
         ["NULLLAB NS4168 I2S amp", "38.4 x 22.4 mm board, on edge, crosswise behind the stack, on two pins. Components to the rear."],
         ["NULLLAB 3 W 4 ohm speaker", "Ear plate 45 x 31 x 1.5, body 27 x 30 x 14.3 (ruler). On two pins at the front, sound to the front grille."],
         ["HiLetgo SPH0645 I2S mic", "16.7 x 12.7 x 1.8 board, on edge on the left side, beside the GPIO edge of the Pi, port to the left. Solder the wires at the top edge."],
         ["5 Dupont jumpers", "Straight plugs on the BiBoard header (GND, +5V, TX2, RX2) in the cover slot."],
         ["Petoi AI Vision Module (optional)", "Stays in the head. Its Grove cable goes along the left side of the robot and through the slot in the left lid wall to the Pi."],
         ], [50, 120])

    B = CHECKS["balance"]
    x, y, z = B["com"]
    p(f"Balance. The add-on weighs about {B['mass_g']:.0f} g: the printed parts in PLA and typical masses of the electronics. "
      f"Its center of mass is {z:.1f} mm behind the robot center, {x:.1f} mm right of the center line and {y - PI.COVER_TOP:.0f} mm above the cover top. "
      "The speaker at the front balances the Pi stack. The masses are not weighed: put your own values in MASS_G in pod.py and run pod.py again.")

    h("3. Assembly")
    st = lambda n: f" ([viewer step {n}]({VIEWER}#step={n}))"
    p(f"The 3D viewer shows each step with animation: [{VIEWER}#step=1]({VIEWER}#step=1). "
      "Each step below has a link to its view.")
    lst(["Print the platform cover and fit it on the robot in place of the stock cover." + st(2),
         "Solder the wires to the Pi, the amp and the mic (section 4).",
         f"Put the tray on the cover {PI.SLIDE:g} mm forward of its place, over the pegs. Push it {PI.SLIDE:g} mm rearward until it clicks." + st(3) + st(4),
         "Push the mic board down into the slot at the left side of the tray, port to the left, wire pads at the top." + st(5),
         "Push the amp onto its two pins behind the stack, components to the rear." + st(6),
         f"Hang the speaker on the two pins of the front wall, ear plate to the rear. Do this after the tray is locked: {PI.SLIDE:g} mm forward, the speaker hits the head." + st(7),
         "Put the Pi + PiSugar 2 stack into the tray, battery down, ports to the right." + st(8),
         "Push the Dupont plugs onto the BiBoard header. Route the wires over the Pi." + st(9),
         "Optional camera: put the Grove cable through the slot in the left lid wall, behind the speaker. Solder its wires to the Pi (section 4). Leave slack for the head to turn.",
         "Push the lid down until the 4 snaps engage. The lid also stops the tray from sliding forward." + st(10),
         f"To remove: pull the lid up, lift the speaker off its pins, slide the tray {PI.SLIDE:g} mm forward and lift it."])
    img("06_tray_loaded.png", 0.56, "The tray without the lid: the speaker (front), the stack on the center line, the mic (left) and the amp (rear).")
    img("08_section_center.png", 0.56, "Section on the center line (right: front). The speaker hangs on the front pins. The amp stands behind the stack.")

    h("4. Wiring")
    tbl([["Signal", "Pi Zero 2 W", "To"],
         ["UART TX / RX", "GPIO14 pin 8 / GPIO15 pin 10", "BiBoard RX2 / TX2"],
         ["GND", "pin 6", "BiBoard GND"],
         ["I2S BCLK", "GPIO18 pin 12", "amp BCLK and mic BCLK"],
         ["I2S LRCLK", "GPIO19 pin 35", "amp LRCLK and mic LRCL"],
         ["I2S out / in", "GPIO21 pin 40 / GPIO20 pin 38", "amp DIN / mic DOUT (mic SEL to GND)"],
         ["Power", "5V pin 2, 3V3 pin 1, GND pin 9", "amp 5V, mic 3V. Do not connect BiBoard 5V to the Pi."],
         ["Speaker", "-", "amp + / - to the speaker"],
         ["Camera I2C (Grove)", "SDA GPIO2 pin 3, SCL GPIO3 pin 5, 3V3 pin 17, GND pin 14", "AI Vision Module Grove: SDA, SCL, VCC, GND"],
         ], [30, 62, 78])

    h("5. Files")
    tbl([["File", "Content"],
         ["stl/print/", "the parts in print orientation"],
         ["cad/pod_tray.step", "exact CAD (the lid is a mesh: its lower edge follows the robot)"],
         ["cad/assembly_step.zip", "one STEP file with the robot, the platform and the add-on in place, with named and colored parts. Unzip it and open it in FreeCAD or other CAD software"],
         ["stl/installed/, stl/models/", "the parts and the electronics in the robot frame"],
         ["pod.py", "all dimensions, the build and the checks (fit, slide path, loose pieces, overhang)"],
         ["render.py, docs.py", "the pictures and this guide"],
         ], [62, 108])
    p("Ports. The stack is on the center line for balance, so its port edge is 11 mm inside the body side. "
      "The lid has two open port bays in its right side: the wall steps in to 0.45 mm from the port faces. "
      "The front bay has the PiSugar charge port and button and the Pi power and data USB ports. "
      "The rear bay has the Pi mini-HDMI port and the PiSugar switch. "
      "The bays take plug bodies of 11 x 7.5 mm (micro-USB) and 14 x 8.5 mm (mini-HDMI). "
      "To remove the SD card, remove the lid and lift the stack out (the wires stay on): the amp is 0.2 mm behind the card.")
    MO = json.load(open(os.path.join(pod.OUT, "motion.json")))
    h0, h1 = MO["head"]["free"]
    p(f"Robot motion. The 3D viewer has the full robot (Petoi ROS model) with sliders for the head, the hips and the knees. "
      f"The head turns from {h0} to {h1} deg without contact. Past that, the bottom of the head touches the lid front. "
      "The legs touch the add-on only when a thigh swings up over the back. "
      "The Petoi tail, if your robot has it, touches the rear of the lid.")
    p("Open items: the speaker sound face is assumed opposite the ears. The mic port is assumed at the board center; "
      "the 7 holes cover ±2.2 mm. The camera supply voltage is not checked: if the module needs 5 V, use pin 4. The PiSugar 2 LEDs are between the two boards and are not visible with the lid on. The BiBoard header height is an estimate.")

    h("6. License")
    p("The printed parts, the drawings and this guide are CC BY 4.0, and the code is MIT (Jeremy Collins). "
      "The Pi Zero and PiSugar 2 fit models are from github.com/PiSugar/PiSugar (GPL-3.0). "
      "The Petoi parts are from github.com/PetoiCamp/NonCodeFiles, without a stated license. "
      "LICENSE.md and ATTRIBUTION.md in the repository give the details.")
    return X


def pod_mass(name):
    M = pod.mesh_to_manifold(pod.load_stl(os.path.join(pod.OUT, "installed", f"{name}.stl")))
    return f"{M.volume() * 1.24e-3:.0f}"


def main():
    PD.DOC = os.path.join(HERE, "doc")
    PD.TITLE = TITLE
    PD.DATE = DATE
    X = content()
    PD.write_md(X, os.path.join(HERE, "README.md"))
    PD.FOOTER = f"Bittle X Pi Add-on v{VERSION}"
    PD.write_pdf(X, os.path.join(HERE, "bittle_pi_addon_guide.pdf"))
    print("docs ready")


if __name__ == "__main__":
    main()
