// The side shoulders with the added material built in as one piece, so each shoulder is a single solid. With ring = true there
// is one ring around each whole opening: the frame's own cross-section around the opening, extended outward by t, with the
// screw holes continuing through. With ring = false there are four small pads, one around each screw hole. Nothing else on the frame changes. The servos and legs sit t farther out.
// The hole positions and the seat face (|X| 35.9) are measured on the shoulder mesh. The rest is estimated.
// Robot frame: X lateral (+X = robot right), Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
R = "..";            // the repository root, relative to this file
P = str(R, "/bittle_platform");
A = str(R, "/bittle_pi_addon");
SH = str(P, "/reference/Bittle_SideShoulder.stl");     // the right shoulder; the left one is its mirror image

t = 4;               // how far the pads extend outward: each servo and leg moves out by t, the stance is 2*t wider
seat_x = 35.9;       // |X| of the face where the servo tab seats (measured on the shoulder mesh)
sec_x = 35.5;        // |X| where the frame's shape around the hole is taken from (inside the pad)
pad_r = 6;           // the pad takes the frame's shape within this radius of the hole
ear_t = 3.5;         // thickness of the servo's tab in the mesh
screw_d = 2; head_d = 4.2; head_h = 1.4;
into_frame = 5;
// the screw holes in the right shoulder (Z, Y), measured on the mesh (1.6 mm); the left shoulder is the mirror image
holes_right = [[-59.6, -4.1], [-35.0, 10.1], [59.6, -4.1], [35.0, 10.1]];
ring = true;         // true: one ring of material around each whole opening, the exact shape of the frame there; false: four small pads
mark_pads = true;    // true: draw the pads in orange over the frame so you can see where they are (the frame is one piece either way)
show_robot = false;  // true: add the servos, legs, plates and lid; false: the shoulders alone
show_screws = true;
closeup = false;     // true: start the view on the left front servo

$vpt = closeup ? [-44, 52, 3] : [0, 0, 20];      // OpenSCAD world: robot Z is -Y
$vpr = closeup ? [70, 0, -70] : [60, 0, 320];
$vpd = closeup ? 110 : 330;

// the frame's own shape around one hole, extended outward by t (right shoulder frame, absolute X)
module pad(hz, hy) {
    translate([seat_x - 0.01, 0, 0]) rotate([0, -90, 0]) translate([0, 0, -t - 0.01]) linear_extrude(t + 0.01)
        intersection() {
            translate([hz, hy]) circle(r = pad_r, $fn = 48);
            projection(cut = true) rotate([0, 90, 0]) translate([-sec_x, 0, 0]) import(SH);
        }
}
// a ring around one whole opening: the frame's own cross-section around that opening, taken at sec_x, extended outward by t.
// z0..z1 is the Z range of the loop; the ring has the same outline as the loop and the same screw holes.
module ring_at(z0, z1) {
    translate([seat_x - 0.01, 0, 0]) rotate([0, -90, 0]) translate([0, 0, -t - 0.01]) linear_extrude(t + 0.01)
        intersection() {
            translate([z0, -12]) square([z1 - z0, 30]);
            projection(cut = true) rotate([0, 90, 0]) translate([-sec_x, 0, 0]) import(SH);
        }
}
module added_material() {
    if (ring) { ring_at(-64, -28); ring_at(28, 64); }       // front loop and rear loop
    else for (h = holes_right) pad(h[0], h[1]);
}
// one shoulder as a single solid: the shoulder plus the added material
module shoulder_one_piece() {
    union() {
        import(SH);
        added_material();
    }
}
module long_screw() {
    color("#bbbbbb") {
        translate([ear_t + t, 0, 0]) rotate([0, 90, 0]) cylinder(d = head_d, h = head_h, $fn = 24);
        translate([-into_frame, 0, 0]) rotate([0, 90, 0]) cylinder(d = screw_d, h = into_frame + ear_t + t + 0.1, $fn = 16);
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
        color("#f2a71c") shoulder_one_piece();
        if (mark_pads) color("#e8641b") added_material();
        if (show_screws && show_robot) for (h = holes_right) translate([seat_x, h[1], h[0]]) long_screw();
    }
    if (show_robot) {
        color("#26272b") import(str(P, "/reference/Bittle_FrontPlate.stl"));
        for (n = ["rear_plate", "neck_mount"]) color("#26272b") import(str(P, "/stl/robot/", n, ".stl"));
        color("#34363b") import(str(P, "/stl/installed/cover_pegs.stl"));
        color("#4a4c52") import(str(P, "/stl/robot/battery.stl"));
        for (h = [["lf", -1, -47.3], ["rf", 1, -47.3], ["lr", -1, 47.3], ["rr", 1, 47.3]]) translate([h[1] * t, 0, 0]) {
            color("#26272b") servo(h[1], h[2]);
            color("#f2a71c") import(str(P, "/stl/robot/thigh_", h[0], ".stl"));
            color("#2c2d31") import(str(P, "/stl/robot/shank_", h[0], ".stl"));
        }
    }
}

rotate([90, 0, 0]) scene();
