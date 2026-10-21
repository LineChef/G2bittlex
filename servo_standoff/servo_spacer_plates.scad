// Separate servo spacer plates (saved design): two flat plates per hip servo, one under each of the servo's own tabs, each
// with an M2 hole. The plates have the same footprint as the servo's tabs, so they sit flush with them. The middle is open,
// so the servo body still passes through the frame. The servo and the leg move out by t, and the screws are t longer.
// Stack at each tab: frame, then the plate, then the servo's own tab, then the screw head.
// Concept: estimates, not measured on a robot. Robot frame: X lateral (+X = robot right), Y up, Z along the body
// (-Z = head). Rotated to Z-up for OpenSCAD.
R = "..";            // the repository root, relative to this file
P = str(R, "/bittle_platform");
A = str(R, "/bittle_pi_addon");

t = 4;               // plate thickness: each servo and leg moves out by t, the stance is 2*t wider
seat_x = 34.5;       // |X| of the frame face that the servo's own tabs sit on (the servo mesh flange is at |X| 34.5 to 38)
// the servo flange outline, from the servo mesh (the smallest rectangle around it): 32.5 x 12.2 mm, its long axis turned 30 deg
// from the body's length. The plates have the same footprint as the servo's tabs, so they are flush.
fl_l = 32.5; fl_w = 12.2;
tilt = 30;
hole_off = fl_l/2 - 1.8;     // the M2 holes are this far from the flange center along its long axis (about 2 mm from the ends)
body_half = 12;              // half the length of the servo body, which has to pass through the frame (23 to 25 mm long)
body_gap = 0.3;              // clearance between the body and the plates
ear_t = 3.5;         // thickness of the servo's own tab in the mesh (the real one is thinner, 1 to 2 mm)
screw_d = 2;         // M2
screw_hole = 2.4;    // M2 clearance
head_d = 4.2; head_h = 1.4;
into_frame = 5;      // how far the screw goes into the frame (estimate)
explode = 0;         // pull frame, plate, servo tab and screw apart to see the order (try 6)
show_addon = true;
show_plates = true;
show_tab = false;    // the servo mesh already has its own tabs; true draws an extra tab over them to mark the stack
show_screws = true;
closeup = true;      // start the view on the left front servo; false: the whole robot

close_rot = [70, 0, -70];     // viewing angle of the close-up
close_dist = 110;
$vpt = closeup ? [-44, 52, 3] : [0, 0, 20];      // OpenSCAD world: robot Z is -Y
$vpr = closeup ? close_rot : [60, 0, 320];
$vpd = closeup ? close_dist : 330;

// name, side (+X = right), flange center Z, tilt of the long axis from Z toward +Y (the rear servos are the mirror image)
hips = [["lf", -1, -47.3, tilt], ["rf", 1, -47.3, tilt], ["lr", -1, 47.3, -tilt], ["rr", 1, 47.3, -tilt]];
flange_y = 3.0;

// one hip servo from the combined hip_servos.stl: keep the quarter that holds this hip
module servo(side, zc) {
    intersection() {
        import(str(P, "/stl/robot/hip_servos.stl"));
        translate([side < 0 ? -60 : 0, -30, zc < 0 ? -80 : 0]) cube([60, 60, 80]);
    }
}

// the plates, in their own frame: X = thickness (0..t, outward), the long axis along Z, centered on the flange center.
// The flange outline minus the strip where the servo body goes through leaves one plate at each end.
module plate() {
    color("#e8641b") difference() {
        rotate([0, 90, 0]) linear_extrude(t) offset(r = 2) square([fl_l - 4, fl_w - 4], center = true);
        translate([-1, -fl_w, -(body_half + body_gap)]) cube([t + 2, 2*fl_w, 2*(body_half + body_gap)]);   // the opening for the body
        for (sgn = [-1, 1]) translate([-1, 0, sgn * hole_off]) rotate([0, 90, 0]) cylinder(d = screw_hole, h = t + 2, $fn = 24);
    }
}
// the servo's tab (one at each end of the flange), drawn only when show_tab is true
module tab() {
    color("#26272b") difference() {
        rotate([0, 90, 0]) linear_extrude(ear_t) offset(r = 2) square([fl_l - 4, fl_w - 4], center = true);
        translate([-1, -fl_w, -(body_half + body_gap)]) cube([ear_t + 2, 2*fl_w, 2*(body_half + body_gap)]);
        for (sgn = [-1, 1]) translate([-1, 0, sgn * hole_off]) rotate([0, 90, 0]) cylinder(d = screw_hole, h = ear_t + 2, $fn = 24);
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
    color("#f2a71c") import(str(P, "/reference/Bittle_SideShoulder.stl"));
    color("#f2a71c") mirror([1, 0, 0]) import(str(P, "/reference/Bittle_SideShoulder.stl"));
    color("#26272b") import(str(P, "/reference/Bittle_FrontPlate.stl"));
    for (n = ["rear_plate", "neck_mount"]) color("#26272b") import(str(P, "/stl/robot/", n, ".stl"));
    color("#3a3b40") import(str(P, "/stl/robot/head.stl"));
    color("#3a3b40") import(str(P, "/stl/robot/tail.stl"));
    color("#4a4c52") import(str(P, "/stl/robot/battery.stl"));
    for (h = hips) {
        k = h[0]; s = h[1]; zc = h[2]; ang = h[3];
        translate([s * (t + 2*explode), 0, 0]) {            // the servo, thigh and shank move out together
            color("#26272b") servo(s, zc);
            color("#f2a71c") import(str(P, "/stl/robot/thigh_", k, ".stl"));
            color("#2c2d31") import(str(P, "/stl/robot/shank_", k, ".stl"));
        }
        // rotate([-ang, 0, 0]) turns the local Z axis toward +Y by ang
        translate([0, flange_y, zc]) rotate([-ang, 0, 0]) mirror([s < 0 ? 1 : 0, 0, 0]) translate([seat_x, 0, 0]) {
            if (show_plates) { translate([explode, 0, 0]) plate(); if (show_tab) translate([t + 2*explode, 0, 0]) tab(); }
            if (show_screws) for (sgn = [-1, 1]) translate([0, 0, sgn * hole_off]) long_screw();
        }
    }
}

rotate([90, 0, 0]) scene();
