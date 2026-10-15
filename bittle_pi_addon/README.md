# Bittle X Pi Add-on v0.16 - Build Guide

Version 0.16, 2026-10-15. A sample add-on for the Bittle X platform v3.0 (../bittle_platform). It holds a Raspberry Pi Zero 2 W with a PiSugar 2 (1200 mAh), an NS4168 I2S amp with a 3 W speaker, and an SPH0645 I2S mic. The case is one rounded box (the body) and a snap-in top panel. The body clicks onto the platform pegs, and every part goes in from the top. No tools, glue, tape or supports are necessary.

![The add-on on the platform: the mic holes are at the front, the port windows in the panel.](doc/02_addon.png)


## 1. Parts to print

| File (stl/print/) | Material | Orientation | Supports | Cura profile | Mass |
|---|---|---|---|---|---|
| pod_body.stl | PLA | floor on the bed | none | Bittle Pi Pod - PLA 0.25 | 33 g |
| pod_panel.stl | PLA, second color | upside down: top on the bed | none | Bittle Fine 0.10 for the best top | 13 g |
| pod_switch.stl | PLA | flat side on the bed, tab up | none | Bittle Fine 0.10 | 0.2 g |
| cover_pegs_foot.stl (../bittle_platform) | PLA | stand on the rear end | none: the foot is the support | Bittle Cover - PLA 0.25 | 11 g |

Print quality. The body walls are vertical and its floor is on the bed. The only overhangs (29 mm² in total) are the tops of the two camera cable notches at the base of the side walls: 8 mm bridges. The grille holes and the mic holes are teardrops (round, with a 45 deg point on top), so they print without bridges. The panel top edge round ends in a 45 deg chamfer at the bed, the port openings have 45 deg chamfers, and the snap bumps have 45 deg catch faces. Its only overhang (4 mm²) is the 2 mm bridge of the button arm. The slider has a 1.7 mm bridge over the fork. Keep the seam at the rear.


## 2. Electronics

| Part | Place |
|---|---|
| Raspberry Pi Zero 2 W + PiSugar 2, 1200 mAh | On the long edge over the robot center: ports and PiSugar controls up, GPIO header down to the right, SD card to the front. Two end posts with grooves hold the boards. |
| Dupont jumpers | On the soldered Pi header. 4 of them go to the BiBoard header (GND, +5V, TX2, RX2) in the right well. |
| NULLLAB NS4168 I2S amp | 38.4 x 22.4 mm board, on edge along the left wall, parts to the inside, in a slot bar on the floor. |
| NULLLAB 3 W 4 ohm speaker | At the rear, sound to the grille in the rear face. Ear plate 45 x 31 x 1.5 in two side grooves (ruler). |
| HiLetgo SPH0645 I2S mic | 16.7 x 12.7 x 1.8 board at the front wall, port to the front, in two grooves. |
| Petoi AI Vision Module (optional) | Stays in the head. Its Grove cable comes along the robot side and in through the notch at the base of the right wall. |

Balance. The add-on weighs about 117 g (printed parts in PLA and typical masses of the electronics, not weighed). The Pi stack, the heaviest part, is over the robot center. The speaker is at the rear, away from the mic. So the center of mass of the add-on is 13.2 mm behind the robot center and 2.5 mm left of the center line, 19 mm above the cover top. The platform spec recommends 10 mm or less: with the speaker at the front it is about 7 mm. Put your own masses in MASS_G in pod.py and run pod.py again.


## 3. Assembly

The 3D viewer shows each step with animation: [https://beetlebugorg.github.io/bittlex/viewer/#step=1](https://beetlebugorg.github.io/bittlex/viewer/#step=1).

1. Fit the platform cover in place of the stock cover. ([viewer step 2](https://beetlebugorg.github.io/bittlex/viewer/#step=2))
2. Put the empty body on the pegs 7 mm behind its place, grille to the rear. Slide it 7 mm forward until it clicks (about 4.2 N). The BiBoard header is now in the notch of the right well. ([viewer step 3](https://beetlebugorg.github.io/bittlex/viewer/#step=3)) ([viewer step 4](https://beetlebugorg.github.io/bittlex/viewer/#step=4))
3. Push the speaker down into the two side grooves at the rear, body to the rear. ([viewer step 5](https://beetlebugorg.github.io/bittlex/viewer/#step=5))
4. Push the mic down into the two grooves at the front wall, port to the front. ([viewer step 6](https://beetlebugorg.github.io/bittlex/viewer/#step=6))
5. Lay the I2S wires (amp and mic) across the floor behind the rear pegs. Push the amp down into the slot along the left wall, parts to the inside. ([viewer step 7](https://beetlebugorg.github.io/bittlex/viewer/#step=7))
6. Push the jumpers onto the Pi header. Push the Pi + PiSugar 2 stack down into the end grooves, over the I2S wires. ([viewer step 8](https://beetlebugorg.github.io/bittlex/viewer/#step=8))
7. Reach into the right well and push the Dupont plug onto the BiBoard header. Fold the slack into the right well. ([viewer step 9](https://beetlebugorg.github.io/bittlex/viewer/#step=9))
8. Put the switch slider on the PiSugar switch lever, fork down. ([viewer step 10](https://beetlebugorg.github.io/bittlex/viewer/#step=10))
9. Push the panel straight down until the 4 tabs click (about 9.1 N). It fits one way only. The slider tab comes up through its slot. ([viewer step 11](https://beetlebugorg.github.io/bittlex/viewer/#step=11))
10. Open: lift the rear edge of the panel at the finger notch (about 8 N), then the front. Remove: open the panel, pull the BiBoard plug off, slide the body 7 mm rearward and lift it.

On the top: the port openings are shaped to the plug bodies (plug + 0.4 mm). The Pi power port and the PiSugar charge port share one opening. The ribbed slider beside the HDMI opening moves the PiSugar power switch (2 mm of slot travel each way; the switch sets the end positions). The tongue near the front of the panel is a large button: press it to press the PiSugar button.

![The top: HDMI, the switch slider, data USB, charge and Pi power, and the button tongue.](doc/04_top.png)

![The body without the panel: the stack on its edge, the plug block on the Pi header, the speaker at the rear.](doc/06_open.png)


## 4. Wiring

| Signal | Pi Zero 2 W | To |
|---|---|---|
| UART TX / RX | GPIO14 pin 8 / GPIO15 pin 10 | BiBoard RX2 / TX2 |
| GND | pin 6 | BiBoard GND |
| I2S BCLK | GPIO18 pin 12 | amp BCLK and mic BCLK |
| I2S LRCLK | GPIO19 pin 35 | amp LRCLK and mic LRCL |
| I2S out / in | GPIO21 pin 40 / GPIO20 pin 38 | amp DIN / mic DOUT (mic SEL to GND) |
| Power | 5V pin 2, 3V3 pin 1, GND pin 9 | amp 5V, mic 3V. Do not connect BiBoard 5V to the Pi. |
| Speaker | - | amp + / - to the speaker |
| Camera I2C (Grove) | SDA GPIO2 pin 3, SCL GPIO3 pin 5, 3V3 pin 17, GND pin 14 | AI Vision Module Grove: SDA, SCL, VCC, GND |

Wire paths. pod.py keeps five paths free of all parts (yellow in the viewer). BiBoard wires: in the right well, from the Pi header plugs to the BiBoard plug. I2S wires: a 2.2 mm space on the floor under the stack, behind the rear pegs, to the amp. Mic wires: over the mic to the right well. Speaker wires: over the amp to the speaker. Camera cable: from the right notch to the front end of the Pi header. A finger tip (21 x 16 mm) reaches the BiBoard plug from the top: nothing is in that space.


## 5. Checks

1. Slide: the empty body is clear of the robot at the click point, half way and at the drop-on place. The clicks are about 4.2 N to lock and 4.2 N to unlock (beam strain 1.12 %).
2. Panel tabs: 9.1 N to close (4 tabs, 30 deg lead), 8 N to open one end (2 tabs, 45 deg catch), tab strain 1.19 %. Turned 180 deg, the panel does not go down.
3. Install: the speaker, the mic, the amp and the stack each go straight down 40 mm without contact. The panel goes down without contact.
4. Switch and button: the slider moves 2 mm each way without contact, and its fork pushes the lever after 0.3 mm. The button arm is 0.2 mm over the button; pressed 0.6 mm, it pushes the button.
5. Robot: the head turns from -85 to 85 deg without contact. 6 front and 22 rear leg poses (of 504) touch the add-on, only when a thigh swings up over the back. The Petoi tail is 3.2 mm under the add-on, and 0.05 mm at the drop-on place.

Open items: the BiBoard header height is an estimate (measure it). The speaker size is a ruler measurement. The mic port is assumed at the board center; the 7 holes cover ±2.2 mm. The SD card is assumed 2.5 mm out of its holder. To change the SD card, lift the stack out. The Pi power port and the PiSugar charge port are side by side: use one of them at a time.


## 6. Files and license

| File | Content |
|---|---|
| stl/print/ | the parts in print orientation |
| cad/pod_body.step, cad/pod_panel.step | the parts as STEP (from the mesh) |
| cad/assembly_step.zip | one STEP file with the robot, the platform and the add-on in place, with named and colored parts |
| stl/installed/, stl/models/ | the parts and the electronics in the robot frame |
| pod.py, motion.py, render.py, docs.py | dimensions, build and checks; robot motion; pictures; this guide |

The printed parts, the drawings and this guide are CC BY 4.0, and the code is MIT (Jeremy Collins). The Pi Zero and PiSugar 2 fit models are from github.com/PiSugar/PiSugar (GPL-3.0). The Petoi parts are from github.com/PetoiCamp/NonCodeFiles, without a stated license. LICENSE.md and ATTRIBUTION.md in the repository give the details.

