// Exploration: splined spacers (hip_spacer_part.scad) on each hip axis that widen the stance. Best-guess sizes, not measured on a robot.
// Each ring sits between the servo and the thigh, and the thigh and shank move out by t (the stance is 2*t wider).
// Robot frame: X lateral, Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
R = "..";            // the repository root, relative to this file
P = str(R, "/bittle_platform");
A = str(R, "/bittle_pi_addon");
use <hip_spacer_part.scad>

t = 4;            // spacer thickness
spacer_od = 10;   // guess: about the servo's brass collar
spacer_id = 2.4;  // M2 screw clearance
servo_face = 45;  // |X| where the servo body ends and the thigh starts, near the hip axis (estimate from the meshes)
show_addon = true;
closeup = true;   // start the view on the left front hip; false: the whole robot
show_spacers = true;

$vpt = closeup ? [-52, 50, 0] : [0, 0, 20];      // viewport target (OpenSCAD world: robot Z is -Y)
$vpr = closeup ? [70, 0, 30] : [60, 0, 320];
$vpd = closeup ? 110 : 330;

hips = [["lf", -1, -52.5], ["rf", 1, -52.5], ["lr", -1, 52.5], ["rr", 1, 52.5]];   // name, side (+X = right), hip Z; hip axis Y = 0

rotate([90, 0, 0]) {
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
    for (n = ["rear_plate", "neck_mount", "hip_servos"]) color("#26272b") import(str(P, "/stl/robot/", n, ".stl"));
    color("#3a3b40") import(str(P, "/stl/robot/head.stl"));
    color("#3a3b40") import(str(P, "/stl/robot/tail.stl"));
    color("#4a4c52") import(str(P, "/stl/robot/battery.stl"));
    for (h = hips) {
        k = h[0]; s = h[1];
        translate([s * t, 0, 0]) {                       // thigh and shank move out by t
            color("#f2a71c") import(str(P, "/stl/robot/thigh_", k, ".stl"));
            color("#2c2d31") import(str(P, "/stl/robot/shank_", k, ".stl"));
        }
        if (show_spacers)
            translate([0, 0, h[2]]) mirror([s < 0 ? 1 : 0, 0, 0]) translate([servo_face, 0, 0]) rotate([0, 90, 0]) spacer_part(t, spacer_od, spacer_id);
    }
}
