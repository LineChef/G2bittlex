// The two side shoulders, each 0.2 in (5.08 mm) wider, with the material added in the center. Each shoulder is cut along its
// middle (a plane at X = cut_x, halfway across its 15.8 mm width). The inner half moves in by 0.1 in and the outer half moves out by
// 0.1 in, so both sides get wider, and the gap is filled with the shoulder's own cross-section at the cut. Nothing else on the
// shoulder changes. The servo seats and screw holes are on the outer half, so they move out by 0.1 in, and the legs with them.
// Robot frame: X lateral (+X = robot right), Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
P = "../bittle_platform";
SH = str(P, "/reference/Bittle_SideShoulder.stl");     // the right shoulder; the left one is its mirror image

add = 5.08;          // the added width: 0.2 in
cut_x = 35.8;        // |X| of the cut: halfway across the shoulder (it spans 27.9 to 43.7)
mark_slice = true;   // draw the added slice in orange so you can see it (each shoulder is one piece either way)

$vpt = [0, 0, 20];      // start with the view framed on the shoulders
$vpr = [60, 0, 320];
$vpd = 330;

// the shoulder's cross-section at the cut, extruded across the gap: from cut_x - add/2 to cut_x + add/2
module slice() {
    translate([cut_x - add/2, 0, 0]) rotate([0, -90, 0]) translate([0, 0, -add - 0.02]) linear_extrude(add + 0.04)
        projection(cut = true) rotate([0, 90, 0]) translate([-cut_x, 0, 0]) import(SH);
}
module shoulder_wider() {
    union() {
        translate([-add/2, 0, 0]) render() intersection() { import(SH); translate([0, -100, -100]) cube([cut_x, 200, 200]); }                  // inner half, moved in
        translate([add/2, 0, 0]) render() intersection() { import(SH); translate([cut_x - 0.01, -100, -100]) cube([100, 200, 200]); }          // outer half, moved out
        slice();
    }
}

one_shoulder = false;   // true: only the right shoulder, without the orange marker (used for checking the solid)
if (one_shoulder) rotate([90, 0, 0]) shoulder_wider();
else rotate([90, 0, 0]) for (s = [-1, 1]) mirror([s < 0 ? 1 : 0, 0, 0]) {
    color("#f2a71c") shoulder_wider();
    if (mark_slice) color("#e8641b") slice();
}
