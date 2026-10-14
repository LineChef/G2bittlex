# Attribution

## Petoi Bittle X parts

Source: Petoi, https://github.com/PetoiCamp/NonCodeFiles, folder
`stl/Bittle & BittleX`, last changed in commit d467ed3a23 (2025-06-18).
The files here are byte-identical copies of the files at that commit.

Petoi publishes these files without a stated license. They are not covered
by the licenses of this repository. All rights stay with Petoi.

| File in this repository | Petoi file |
|---|---|
| `bittle_platform/reference/Bittle_Cover_with_hole_for_Pi.stl` | `BittleCover/Bittle_Cover_with_hole_for_Pi.stl` |
| `bittle_platform/reference/Bittle_Cover.stl` | `BittleCover/Bittle_Cover.stl` |
| `bittle_platform/reference/Bittle_SideShoulder.stl` | `Bittle_SideShoulder.stl` |
| `bittle_platform/reference/Bittle_FrontPlate.stl` | `Bittle_FrontPlate.stl` |

Files made from the Petoi parts:

- `cover_pegs.stl` (in `bittle_platform/stl/print/`, `bittle_platform/stl/installed/`
  and `bittle_pi_addon/stl/installed/`): Bittle_Cover_with_hole_for_Pi.stl
  with 4 pegs added. The print version is rotated to the print orientation.
- `bittle_platform/stl/installed/keepout.stl`: a clearance volume above the
  cover, the side shoulders and the front plate.
- `bittle_pi_addon/stl/models/cover_slot.stl`: the free space in the Pi slot
  of the cover.
- The 3D viewer on the site loads the side shoulder and the front plate
  (also mirrored as the rear plate).

## PiSugar and Raspberry Pi Zero models

Source: PiSugar, https://github.com/PiSugar/PiSugar, commit 61a5e2083f
(2022-01-18). License: GPL-3.0 (`LICENSES/GPL-3.0.txt`). The files here
are byte-identical copies of the files at that commit.

| File in this repository | PiSugar file |
|---|---|
| `bittle_pi_addon/reference/pisugar2Board.STL` | `model2/pisugar2Board.STL` |
| `bittle_pi_addon/reference/RaspberryPiZeroW-1.STL` | `model3/RaspberryPiZeroW-1.STL` |

Files made from them, also under GPL-3.0: `bittle_pi_addon/stl/models/pisugar2.stl`
and `bittle_pi_addon/stl/models/pizero.stl`. These are the same meshes moved
and rotated into the robot frame by `bittle_pi_addon/pod.py`. They are fit
references. The printed parts do not contain them.

## Other component models

The models of the NS4168 amp, the speaker, the SPH0645 mic, the battery,
the BiBoard header and the Dupont plugs in `bittle_pi_addon/stl/models/`
are boxes drawn by `pod.py` from measurements. They are CC BY 4.0 with the
other designs.
