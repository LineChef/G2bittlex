// Separate spacers in the shape of the frame: each spacer has the outline of the frame's own pad around a servo screw hole
// (the frame's shape within 6 mm of the hole), 4 mm thick, with the hole continuing through. It goes between the frame and the
// servo's tab, so each hip servo (and its leg) sits t farther out. Four spacers per side, one per screw. They can be printed
// separately or fused to the frame as pads. The shoulder, plates and lid are not changed. The servo and leg move out by t,
// and the M2 screws are t longer.
// The hole positions (1.6 mm, 28.4 mm apart along each loop at 30 deg to the body) and the seat face (|X| 35.9) are measured on
// the shoulder mesh. The rest is estimated.
// Robot frame: X lateral (+X = robot right), Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
R = "..";            // the repository root, relative to this file
P = str(R, "/bittle_platform");
A = str(R, "/bittle_pi_addon");
SH = str(P, "/reference/Bittle_SideShoulder.stl");     // the right shoulder; the left one is its mirror image

t = 4;               // how far each pad extends outward: each servo and leg moves out by t, the stance is 2*t wider
seat_x = 35.9;       // |X| of the face where the servo tab seats: the frame's pad ends here (measured: the holes are in material up to X 35.9)
sec_x = 35.5;        // |X| where the frame's shape around the hole is taken from (inside the pad)
pad_r = 6;           // the pad takes the frame's shape within this radius of the hole
ear_t = 3.5;         // thickness of the servo's tab in the mesh (the real one is 1 to 2 mm)
screw_d = 2;         // M2
head_d = 4.2; head_h = 1.4;
into_frame = 5;      // how far the screw goes into the frame (estimate)
// the four screw holes in the right shoulder (Z, Y), measured on the mesh: 1.6 mm holes, 28.4 mm apart along each loop, at
// 30 deg to the body; the left shoulder is the mirror image
holes_front = [[-59.6, -4.1], [-35.0, 10.1]];
holes_rear = [[59.6, -4.1], [35.0, 10.1]];
highlight = true;    // draw the spacers in orange so they stand out; false: the same color as the frame
explode = 0;         // pull the servo and screw away from the pad to see the order (try 6)
show_addon = true;
show_pads = true;
show_screws = true;
closeup = true;      // start the view on the left front servo; false: the whole robot

close_rot = [70, 0, -70];     // viewing angle of the close-up
close_dist = 110;
$vpt = closeup ? [-44, 52, 3] : [0, 0, 20];      // OpenSCAD world: robot Z is -Y
$vpr = closeup ? close_rot : [60, 0, 320];
$vpd = closeup ? close_dist : 330;

// name, side (+X = right), center Z of the servo, the holes of that end
hips = [["lf", -1, -47.3, holes_front], ["rf", 1, -47.3, holes_front], ["lr", -1, 47.3, holes_rear], ["rr", 1, 47.3, holes_rear]];

// one hip servo from the combined hip_servos.stl: keep the quarter that holds this hip
module servo(side, zc) {
    intersection() {
        import(str(P, "/stl/robot/hip_servos.stl"));
        translate([side < 0 ? -60 : 0, -30, zc < 0 ? -80 : 0]) cube([60, 60, 80]);
    }
}

// the frame's own shape around one hole, extended outward by t (right shoulder frame, absolute X)
module pad(hz, hy) {
    color(highlight ? "#e8641b" : "#f2a71c")
    translate([seat_x, 0, 0]) rotate([0, -90, 0]) translate([0, 0, -t]) linear_extrude(t)
        intersection() {
            translate([hz, hy]) circle(r = pad_r, $fn = 48);
            projection(cut = true) rotate([0, 90, 0]) translate([-sec_x, 0, 0]) import(SH);
        }
}
module long_screw() {    // local: head at +X, the shank goes toward the frame (-X); explode pulls the head out
    color("#bbbbbb") {
        translate([ear_t + t + 3*explode, 0, 0]) rotate([0, 90, 0]) cylinder(d = head_d, h = head_h, $fn = 24);
        translate([-into_frame, 0, 0]) rotate([0, 90, 0]) cylinder(d = screw_d, h = into_frame + ear_t + t + 3*explode + 0.1, $fn = 16);
    }
}

module scene() {
    color("#34363b") import(str(P, "/stl/installed/cover_pegs.stl"));
    if (show_addon) {
        color("#f2f2ef") import(str(A, "/stl/installed/pod_body.stl"));
        color("#e8641b") import(str(A, "/stl/installed/pod_panel.stl"));
        color("#f2f2ef") import(str(A, "/stl/installed/pod_button.stl"));
        color("#e8641b") import(str(A, "/stl/installed/pod_camera_mount.stl"));
    }
    color("#f2a71c") import(SH);
    color("#f2a71c") mirror([1, 0, 0]) import(SH);
    color("#26272b") import(str(P, "/reference/Bittle_FrontPlate.stl"));
    for (n = ["rear_plate", "neck_mount"]) color("#26272b") import(str(P, "/stl/robot/", n, ".stl"));
    color("#3a3b40") import(str(P, "/stl/robot/head.stl"));
    color("#3a3b40") import(str(P, "/stl/robot/tail.stl"));
    color("#4a4c52") import(str(P, "/stl/robot/battery.stl"));
    for (h = hips) {
        k = h[0]; s = h[1]; zc = h[2]; hl = h[3];
        translate([s * (t + 2*explode), 0, 0]) {            // the servo, thigh and shank move out together
            color("#26272b") servo(s, zc);
            color("#f2a71c") import(str(P, "/stl/robot/thigh_", k, ".stl"));
            color("#2c2d31") import(str(P, "/stl/robot/shank_", k, ".stl"));
        }
        mirror([s < 0 ? 1 : 0, 0, 0]) for (hole = hl) {
            if (show_pads) pad(hole[0], hole[1]);
            if (show_screws) translate([seat_x, hole[1], hole[0]]) long_screw();
        }
    }
}

rotate([90, 0, 0]) scene();
