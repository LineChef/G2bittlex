# Bittle X Pi Add-on v0.19 - Build Guide

Version 0.19, 2026-10-15. A sample add-on for the Bittle X platform v3.1 (../bittle_platform). It holds a Raspberry Pi Zero 2 W with a PiSugar 2 (1200 mAh), an NS4168 I2S amp with a 3 W speaker, an SPH0645 I2S mic and the Petoi AI Vision Module. The case is one rounded box (the body) and a snap-in top panel. The body clicks onto the platform pegs, and every part goes in from the top. No tools, glue, tape or supports are necessary.

![The add-on on the platform: the mic holes are at the front, the port windows in the panel.](doc/02_addon.png)


## 1. Parts to print

| File (stl/print/) | Material | Orientation | Mass |
|---|---|---|---|
| pod_body.stl | PLA | floor on the bed | 34 g |
| pod_panel.stl | PLA, second color | upside down: top on the bed | 13 g |
| pod_switch.stl | PLA, white | flat side on the bed, tab up | 0.2 g |
| pod_button.stl | PLA, white | upside down: top on the bed | 0.1 g |
| pod_camera_mount.stl | PLA, second color | on its back end (as in the STL) | 4 g |
| cover_pegs_foot.stl (../bittle_platform) | PLA | stand on the rear end | 11 g |

Print every part with the Cura profile "Bittle X" (../cura/Bittle_X.curaprofile; 0.20 mm layers, no supports, 6-line brim). ../cura/install_profiles.py installs it, and a copy with the size compensation of each spool that the tolerance app measured ("Bittle X - <spool>"). No part needs supports.

Print quality. The body and panel walls are 2.0 mm: with the offsets of the body profile, Cura slices 4 full lines of 0.5 mm. The body walls are vertical and its floor is on the bed. The only overhangs ({pr['pod_body']['overhang_mm2']:.0f} mm² in total) are the tops of the two cable notches at the base of the side walls: 8 mm bridges. The front cable notches are 45 deg chamfers. The grille holes and the mic holes are teardrops (round, with a 45 deg point on top), so they print without bridges. The panel top edge round ends in a 45 deg chamfer at the bed, the port openings have 45 deg chamfers, and the snap bumps have 45 deg catch faces. Its only overhang (28 mm²) is the 2 mm bridge of the button arm. The slider has a 1.7 mm bridge over the fork. The camera mount has a 9.5 mm bridge at the HDMI notch, short bridges at the clip hooks, and a 45 deg chin. Keep the seam at the rear.


## 2. Electronics

| Part | Place |
|---|---|
| Raspberry Pi Zero 2 W + PiSugar 2, 1200 mAh | On the long edge over the robot center, 4.9 mm right of the center line so the battery is near it: ports and PiSugar controls up, GPIO header down to the right, SD card to the front. Two end posts with grooves hold the boards. The pin-fin heatsink on the SoC points into the right well (14 x 14 x 6.5 mm, estimated). |
| Dupont jumpers | 10 cm female-female jumpers from a pack: 3 to the BiBoard, 6 to the mic (2 of them through the splices). |
| NULLLAB NS4168 I2S amp | 38.4 x 22.4 mm board, on edge along the left wall, parts to the inside, in a slot bar on the floor. Its PH2.0 connectors are side entry: the I2S cable plugs in at the front end, the speaker at the rear end. |
| NULLLAB 3 W 4 ohm speaker | At the rear, sound to the grille in the rear face. The ear plate (45 x 31 x 1.5, ruler) is at the middle of the body depth and stands in two side grooves. |
| HiLetgo SPH0645 I2S mic | 12.7 x 16.7 x 1.8 board at the front wall, port to the front. A 6-pin right-angle header along its right edge points into the right well. |
| Petoi AI Vision Module | In its Petoi case, upright on the camera mount at the front of the panel, lens forward over the head. It is upside down, so that its Grove socket is on the left, clear of the HDMI opening: turn the image 180 deg in software. Two U brackets hold the ends of the case; a ridge on each snaps into the pocket in the end of the case. |
| Grove cable, 10 cm | From the socket in the rear face of the camera, down through a slot in the panel, forward under the panel between the amp and the battery, down the front left corner in an S fold, to the Grove plug on the BiBoard. The plug comes up through the floor opening over the notch in the platform cover. |
| Optional cable | A notch at the base of each side wall lets a cable in from outside. |

Balance. The add-on weighs 126 g with the camera (weighed parts; printed parts at 50 % fill). Its center of mass is 3.1 mm behind the robot center and 0.2 mm right of the center line, 23 mm above the cover top. With the add-on, the center of mass of the robot is about 4 mm behind the midpoint of the front and rear paws (110 mm apart), and on the center line. Standing, the robot tips only past these angles: 31 deg nose down, 27 deg nose up and 19 deg to the side. The side is the limit: keep heavy parts low. Put your own masses in MASS_G in pod.py and run pod.py again.


## 3. Assembly

The 3D viewer shows each step with animation: [https://beetlebugorg.github.io/bittlex/viewer/#step=1](https://beetlebugorg.github.io/bittlex/viewer/#step=1).

1. Fit the platform cover in place of the stock cover. ([viewer step 2](https://beetlebugorg.github.io/bittlex/viewer/#step=2))
2. Put the empty body on the pegs 7 mm behind its place, grille to the rear. Slide it 7 mm forward until it clicks (about 3.2 N). The BiBoard header is now in the notch of the right well. ([viewer step 3](https://beetlebugorg.github.io/bittlex/viewer/#step=3)) ([viewer step 4](https://beetlebugorg.github.io/bittlex/viewer/#step=4))
3. Push a 10 cm Grove cable onto the Grove plug of the BiBoard through the floor opening at the front left. Lay its excess as an S fold in the front left corner and let the free end hang out of the top. ([viewer step 5](https://beetlebugorg.github.io/bittlex/viewer/#step=5))
4. Push the speaker down into the two side grooves at the rear, body to the rear. ([viewer step 6](https://beetlebugorg.github.io/bittlex/viewer/#step=6))
5. Plug the six mic jumpers onto the mic header. Push the mic down into its grooves at the front wall, port to the front. ([viewer step 7](https://beetlebugorg.github.io/bittlex/viewer/#step=7))
6. Plug the amp cable into the I2S connector at the front end of the amp and the speaker into its rear end. Push the amp down into the slot along the left wall, parts to the inside. Lay the amp cable across the floor in front of the front pegs, into the right well. ([viewer step 8](https://beetlebugorg.github.io/bittlex/viewer/#step=8))
7. Push the Pi + PiSugar 2 stack down into the end grooves, over the amp cable. ([viewer step 9](https://beetlebugorg.github.io/bittlex/viewer/#step=9))
8. Plug the wires one at a time, in the order of section 5: the BiBoard jumpers, the amp cable, the splices, then the mic jumpers. The viewer has one step for each wire. ([viewer step 10](https://beetlebugorg.github.io/bittlex/viewer/#step=10)) ([viewer step 22](https://beetlebugorg.github.io/bittlex/viewer/#step=22))
9. Slide the switch slider into the rails under the panel from their rear end until it clicks. Slide the white button cap onto the panel tongue until it clicks. They stay in the panel. ([viewer step 23](https://beetlebugorg.github.io/bittlex/viewer/#step=23))
10. Pass the free end of the Grove cable up through the slot at the front left of the panel. Then push the panel straight down until the 4 tabs click (about 9.1 N). It fits one way only. The slider fork goes over the switch lever and the button cap comes over the PiSugar button. ([viewer step 24](https://beetlebugorg.github.io/bittlex/viewer/#step=24))
11. Push the two clip legs of the camera mount down through the window in the front of the panel until they click. Push the camera case down into the brackets until it clicks, lens forward. Plug the Grove cable into the socket in its rear face. ([viewer step 25](https://beetlebugorg.github.io/bittlex/viewer/#step=25)) ([viewer step 26](https://beetlebugorg.github.io/bittlex/viewer/#step=26))
12. Open: lift the rear edge of the panel at the finger notch (about 8 N), then the front. Remove: open the panel, pull the BiBoard plugs off, slide the body 7 mm rearward and lift it.

On the top: the port openings are shaped to the plug bodies (plug + 0.4 mm). The Pi power port and the PiSugar charge port share one opening. The ribbed slider beside the HDMI opening moves the PiSugar power switch (2 mm of slot travel each way; the switch sets the end positions). The tongue near the front of the panel is a large button: press it to press the PiSugar button.

![The top: HDMI, the switch slider, data USB, charge and Pi power, and the button tongue.](doc/04_top.png)


## 4. Wiring

| Board pin | Pi pin | Signal |
|---|---|---|
| BiBoard TX2 / RX2 / GND | 10 / 8 / 6 | RXD / TXD / GND (TX and RX cross). BiBoard +5V: not wired |
| Amp V / G | 2 / 14 | 5V / GND |
| Mic 3V / GND / SEL | 1 / 9 / 39 | 3V3 / GND / GND (left channel) |
| Amp BCLK + mic BCLK | 12 (splice) | GPIO18: one wire from the pin to a soldered splice, then one wire to each board |
| Amp LRC + mic LRCL | 35 (splice) | GPIO19: the same, a second splice |
| Amp DIN / mic DOUT | 40 / 38 | GPIO21 / GPIO20 |
| Speaker | - | amp 2-pin PH2.0 at the rear end of the amp |

Pin map from the wiring blueprint (reference/g2-wiring-blueprint.html; that blueprint wins if they differ). PiSugar 2 touches pins 2, 4, 5 and 6 from below with its pogo pins. Pins 11, 17-20 and 22-24 are kept free for a screen.


## 5. Cable routing

The BiBoard and mic wires are female-female jumpers from a pack of 10 cm wires. The amp keeps its own cable, and the two splices are cut from pack jumpers. pod.py models every wire (1.4 mm) at its real length and checks it: no wire touches a printed part or a board, no two wires pass through each other (0 found), and no bend is smaller than 2 mm radius (1.35 mm in the slack). A pack jumper is longer than its route, so its excess is an arch or a coil (a service loop) in free space. The pages below show each module: its pins, then its wires in the case.

![](doc/15_wiring_0.png)

![](doc/15_wiring_1.png)

![](doc/15_wiring_2.png)

![](doc/15_wiring_3.png)

| # | From | To (excess) | mm | # | From | To (excess) | mm |
|---|---|---|---|---|---|---|---|
| 1 | BiBoard TX2 | pin 10 (arch) | 98 | 12 | mic BCLK | BCLK splice | 39 |
| 2 | BiBoard RX2 | pin 8 (1-turn loop on a 10 mm stem) | 98 | 13 | mic GND | pin 9 (2-turn loop on a 10 mm stem) | 98 |
| 3 | BiBoard GND | pin 6 (1-turn loop) | 100 | 14 | mic 3V | pin 1 (3-turn loop on a 5 mm stem) | 96 |
| 4 | amp G | pin 14 | 103 | 15 | BCLK splice | pin 12 | 14 |
| 5 | amp V | pin 2 | 72 | 16 | LRCLK splice | pin 35 | 5 |
| 6 | amp BCLK | BCLK splice | 96 | 17 | amp speaker + | speaker + | 43 |
| 7 | amp LRC | LRCLK splice | 111 | 18 | amp speaker - | speaker - | 43 |
| 8 | amp DIN | pin 40 | 106 | 19 | camera Grove SCL | BiBoard Grove SCL | 100 |
| 9 | mic SEL | pin 39 (arch) | 99 | 20 | camera Grove SDA | BiBoard Grove SDA | 101 |
| 10 | mic LRCL | LRCLK splice | 57 | 21 | camera Grove VCC | BiBoard Grove VCC | 102 |
| 11 | mic DOUT | pin 38 (1-turn loop) | 98 | 22 | camera Grove GND | BiBoard Grove GND | 103 |

Plug the jumpers one at a time, in this order. Each wire goes to its place before the next one, so the later wires lie over the earlier ones:

1. #1: BiBoard TX2 to pin 10. Put its excess in a arch as in the drawing.
2. #2: BiBoard RX2 to pin 8. Put its excess in a 1-turn loop on a 10 mm stem as in the drawing.
3. #3: BiBoard GND to pin 6. Put its excess in a 1-turn loop as in the drawing.
4. #14: mic 3V to pin 1. Put its excess in a 3-turn loop on a 5 mm stem as in the drawing.
5. #13: mic GND to pin 9. Put its excess in a 2-turn loop on a 10 mm stem as in the drawing.
6. #12: mic BCLK to BCLK splice. Cut to length.
7. #11: mic DOUT to pin 38. Put its excess in a 1-turn loop as in the drawing.
8. #10: mic LRCL to LRCLK splice. Cut to length.
9. #9: mic SEL to pin 39. Put its excess in a arch as in the drawing.

1. The mic has a right-angle header along its right edge. Plug the six mic jumpers onto it before the mic goes into its grooves.
2. Amp cable: forward from the plug, down, across the floor in front of the front pegs (under the stack), then rearward in a floor lane of the right well. Lay it before the stack goes in. Its own excess (not measured) folds in the left gallery over the amp.
3. Splices: the BCLK splice stands in front of the BiBoard notch, the LRCLK splice beside the BiBoard plugs.
4. The BiBoard wires go in first, from the lowest: TX2, RX2, then GND. The wires after them lie over them.

![From the top, panel off: the wires in 3D.](doc/11_wires_top.png)

![The Grove cable of the camera, panel off: down through the panel slot, then an S fold to the BiBoard.](doc/16_camera_cable.png)


## 6. Checks

1. Slide: the empty body is clear of the robot at the click point, half way and at the drop-on place. The clicks are about 3.2 N to lock and 3.2 N to unlock (beam strain 0.9 %).
2. Panel tabs: 9.1 N to close (4 tabs, 30 deg lead), 8 N to open one end (2 tabs, 45 deg catch), tab strain 1.19 %. Turned 180 deg, the panel does not go down.
3. Install: the speaker, the mic, the amp and the stack each go straight down 40 mm without contact. The panel goes down without contact. Each wire, in its order, goes in from 40 mm above without contact with the parts and wires already in place (small contacts of 1 to 2 mm³ stay where a wire slides under a loose service loop). Each Dupont housing slides off its pin without contact.
4. Camera: the case goes into the mount without contact and is clear of the HDMI plug. Lifted 8 mm, it hits the ridges. The ridges need 0.5 mm of bracket flex (about 4 N each, 0.4 % strain); the clip legs bend to 1.3 % strain. The Grove cable touches no part and no other wire. The head turns without contact with the mount.
5. Switch and button: the slider moves 2 mm each way without contact, and its fork pushes the lever after 0.3 mm. The button arm is 0.2 mm over the button; pressed 0.6 mm, it pushes the button.
6. Robot: the head turns from -85 to 85 deg without contact. 6 front and 22 rear leg poses (of 504) touch the add-on, only when a thigh swings up over the back. The Petoi tail is 3.2 mm under the add-on, and 0.05 mm at the drop-on place.

Open items: the BiBoard header height is an estimate (measure it). The speaker size is a ruler measurement. The mic port is assumed at the board center; the 7 holes cover ±2.2 mm. The SD card is assumed 2.5 mm out of its holder. The heatsink size is estimated. To change the SD card, lift the stack out. The Pi power port and the PiSugar charge port are side by side: use one of them at a time.


## 7. Files and license

| File | Content |
|---|---|
| stl/print/ | the parts in print orientation |
| cad/pod_body.step, cad/pod_panel.step | the parts as STEP (from the mesh) |
| cad/assembly_step.zip | one STEP file with the robot, the platform and the add-on in place, with named and colored parts |
| stl/installed/, stl/models/ | the parts and the electronics in the robot frame |
| pod.py, motion.py, render.py, docs.py | dimensions, build and checks; robot motion; pictures; this guide |

The printed parts, the drawings and this guide are CC BY 4.0, and the code is MIT (Jeremy Collins). The Pi Zero and PiSugar 2 fit models are from github.com/PiSugar/PiSugar (GPL-3.0). The Petoi parts are from github.com/PetoiCamp/NonCodeFiles, without a stated license. LICENSE.md and ATTRIBUTION.md in the repository give the details.

