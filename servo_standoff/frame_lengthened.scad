// A longer frame: a 0.2 in (5.08 mm) slice added to the center of each side shoulder. The shoulder is cut at its middle
// (Z = 0), the front half moves forward and the rear half moves back by half the slice each, and the gap is filled with the
// shoulder's own cross-section at the cut, extended to the new length. Nothing else on the shoulder changes, so there is no
// contour to follow. The front and rear legs, servos and plates move with their ends of the frame. The lid, battery and
// add-on stay where they are in the middle.
// Robot frame: X lateral (+X = robot right), Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
R = "..";            // the repository root, relative to this file
P = str(R, "/bittle_platform");
A = str(R, "/bittle_pi_addon");
SH = str(P, "/reference/Bittle_SideShoulder.stl");     // the right shoulder; the left one is its mirror image

add = 5.08;          // the added length: 0.2 in
mark_slice = true;   // draw the added slice in orange so you can see it (the shoulder is one piece either way)
show_robot = true;   // the servos, legs, plates, lid and add-on; false: the shoulders alone
show_addon = true;
closeup = false;     // true: start the view on the middle of the left shoulder

$vpt = closeup ? [-36, 0, 3] : [0, 0, 20];      // OpenSCAD world: robot Z is -Y
$vpr = closeup ? [70, 0, -50] : [60, 0, 320];
$vpd = closeup ? 120 : 330;

half = add / 2;

// one shoulder as a single solid: the front half and the rear half moved apart, with the slice between them
module slice() {
    linear_extrude(height = add + 0.02, center = true) projection(cut = true) import(SH);     // the cross-section at Z = 0
}
module shoulder_longer() {
    union() {
        translate([0, 0, -half]) render() intersection() { import(SH); translate([-100, -100, -100]) cube([200, 200, 100.01]); }   // front half
        translate([0, 0, half]) render() intersection() { import(SH); translate([-100, -100, -0.01]) cube([200, 200, 100.01]); }    // rear half
        slice();
    }
}

module servo(side, zc) {
    intersection() {
        import(str(P, "/stl/robot/hip_servos.stl"));
        translate([side < 0 ? -60 : 0, -30, zc < 0 ? -80 : 0]) cube([60, 60, 80]);
    }
}

module scene() {
    for (s = [-1, 1]) mirror([s < 0 ? 1 : 0, 0, 0]) {
        color("#f2a71c") shoulder_longer();
        if (mark_slice) color("#e8641b") slice();
    }
    if (show_robot) {
        translate([0, 0, -half]) {                                       // the front end moves forward
            color("#26272b") import(str(P, "/reference/Bittle_FrontPlate.stl"));
            color("#26272b") import(str(P, "/stl/robot/neck_mount.stl"));
            color("#3a3b40") import(str(P, "/stl/robot/head.stl"));
        }
        translate([0, 0, half]) {                                        // the rear end moves back
            color("#26272b") import(str(P, "/stl/robot/rear_plate.stl"));
            color("#3a3b40") import(str(P, "/stl/robot/tail.stl"));
        }
        color("#34363b") import(str(P, "/stl/installed/cover_pegs.stl"));
        color("#4a4c52") import(str(P, "/stl/robot/battery.stl"));
        if (show_addon) {
            color("#f2f2ef") import(str(A, "/stl/installed/pod_body.stl"));
            color("#e8641b") import(str(A, "/stl/installed/pod_panel.stl"));
            color("#f2f2ef") import(str(A, "/stl/installed/pod_button.stl"));
            color("#e8641b") import(str(A, "/stl/installed/pod_camera_mount.stl"));
        }
        for (h = [["lf", -1, -47.3], ["rf", 1, -47.3], ["lr", -1, 47.3], ["rr", 1, 47.3]])
            translate([0, 0, h[2] < 0 ? -half : half]) {                 // each leg moves with its end of the frame
                color("#26272b") servo(h[1], h[2]);
                color("#f2a71c") import(str(P, "/stl/robot/thigh_", h[0], ".stl"));
                color("#2c2d31") import(str(P, "/stl/robot/shank_", h[0], ".stl"));
            }
    }
}

rotate([90, 0, 0]) scene();
