// The four wide-foot designs, one on each foot of the Bittle (see wide_foot_part.scad). Estimates, not measured on a robot.
// Robot frame: X lateral (+X = robot right), Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
R = "..";            // the repository root, relative to this file
P = str(R, "/bittle_platform");
use <wide_foot_part.scad>

show_feet = true;
styles = ["M", "M", "M", "M"];     // the design on each foot: left front, right front, left rear, right rear
closeup = true;      // start the view on the left front foot; false: the whole robot

$vpt = closeup ? [-38, 50, -75] : [0, 0, 20];      // OpenSCAD world: robot Z is -Y
$vpr = closeup ? [75, 0, 35] : [60, 0, 320];
$vpd = closeup ? 120 : 330;

// foot center (X, Z) and the lowest Y of each shank, measured from the shank meshes: left front X -34.1, Z -53.1, Y -87.1
feet = [["lf", -1, -53.1], ["rf", 1, -53.1], ["lr", -1, 53.1], ["rr", 1, 53.1]];   // name, side (+X = right), foot Z
foot_x = 34.1;
drop = 3;             // the foot moves down by the thickness of its base, so the stock foot sits on the base
foot_bottom = -87.1 - drop;     // -87.1 is the lowest point of the stock shank

rotate([90, 0, 0]) {
    color("#34363b") import(str(P, "/stl/installed/cover_pegs.stl"));
    color("#f2a71c") import(str(P, "/reference/Bittle_SideShoulder.stl"));
    color("#f2a71c") mirror([1, 0, 0]) import(str(P, "/reference/Bittle_SideShoulder.stl"));
    color("#26272b") import(str(P, "/reference/Bittle_FrontPlate.stl"));
    for (n = ["rear_plate", "neck_mount", "hip_servos"]) color("#26272b") import(str(P, "/stl/robot/", n, ".stl"));
    color("#3a3b40") import(str(P, "/stl/robot/head.stl"));
    color("#3a3b40") import(str(P, "/stl/robot/tail.stl"));
    for (k = ["lf", "rf", "lr", "rr"]) {
        color("#f2a71c") import(str(P, "/stl/robot/thigh_", k, ".stl"));
        color("#2c2d31") import(str(P, "/stl/robot/shank_", k, ".stl"));
    }
    if (show_feet) for (i = [0 : 3]) { f = feet[i];
        // the part: Z up, +X outward. Turn it so its Z is the robot Y; +X outward is -X on the left side.
        translate([f[1] * foot_x, foot_bottom, f[2]]) mirror([f[1] < 0 ? 1 : 0, 0, 0]) rotate([-90, 0, 0]) foot(styles[i]);
    }
}
