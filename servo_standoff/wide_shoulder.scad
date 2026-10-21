// Wide side shoulder (bittle-wide-shoulder.pdf): the Petoi side shoulder with a 10 mm collar under the servo seats. The shoulder is
// cut at X = cut_x, just inside the screw-hole pads. The inner part (the joints to the chassis and the plates) stays where it is. The
// outer part (servo seats, screw holes) moves out by collar, and the gap is filled with the shoulder's own cross-section at the cut.
// The servos and legs sit 10 mm farther out on each side.
// Robot frame: X lateral (+X = robot right), Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
P = "../bittle_platform";
SH = str(P, "/reference/Bittle_SideShoulder.stl");     // the right shoulder; the left one is its mirror image

collar = 10;         // how far the servos move out on each side
cut_x = 33.0;        // |X| of the cut: inside the pads, which span 33.25 to 35.75
mark_collar = true;  // draw the collar in orange so you can see it (each shoulder is one piece either way)

$vpt = [0, 0, 20];
$vpr = [60, 0, 320];
$vpd = 330;

module collar_slice() {
    translate([cut_x, 0, 0]) rotate([0, -90, 0]) translate([0, 0, -collar - 0.02]) linear_extrude(collar + 0.04)
        projection(cut = true) rotate([0, 90, 0]) translate([-cut_x, 0, 0]) import(SH);
}
module wide_shoulder() {
    union() {
        render() intersection() { import(SH); translate([0, -100, -100]) cube([cut_x, 200, 200]); }
        translate([collar, 0, 0]) render() intersection() { import(SH); translate([cut_x - 0.01, -100, -100]) cube([100, 200, 200]); }
        collar_slice();
    }
}

one_shoulder = false;   // true: only the right shoulder, without the marker (used for exporting and checking)
if (one_shoulder) rotate([90, 0, 0]) wide_shoulder();
else rotate([90, 0, 0]) for (s = [-1, 1]) mirror([s < 0 ? 1 : 0, 0, 0]) {
    color("#f2a71c") wide_shoulder();
    if (mark_collar) color("#e8641b") collar_slice();
}
