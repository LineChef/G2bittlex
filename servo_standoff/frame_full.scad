// The frame the hip servos anchor to: both side shoulders (the loops at their ends take the servos' screws), joined by the
// front plate and the rear plate. No cover, battery, servos, legs or head. Robot frame: X lateral, Y up, Z along the body
// (-Z = head). Rotated to Z-up for OpenSCAD.
P = "../bittle_platform";
show_plates = true;      // the front and rear plates that join the two shoulders
show_neck_mount = false;
show_cover = true;       // the back cover (with the platform's pegs)
show_battery = false;
show_servos = false;     // the four hip servos
$vpt = [0, 0, 20];      // start with the view framed on the body
$vpr = [60, 0, 320];
$vpd = 330;

rotate([90, 0, 0]) {
    color("#f2a71c") import(str(P, "/reference/Bittle_SideShoulder.stl"));                    // right shoulder
    color("#f2a71c") mirror([1, 0, 0]) import(str(P, "/reference/Bittle_SideShoulder.stl"));  // left shoulder (mirrored)
    if (show_plates) {
        color("#26272b") import(str(P, "/reference/Bittle_FrontPlate.stl"));
        color("#26272b") import(str(P, "/stl/robot/rear_plate.stl"));
    }
    if (show_neck_mount) color("#26272b") import(str(P, "/stl/robot/neck_mount.stl"));
    if (show_cover) color("#34363b") import(str(P, "/stl/installed/cover_pegs.stl"));
    if (show_battery) color("#4a4c52") import(str(P, "/stl/robot/battery.stl"));
    if (show_servos) color("#5b5d63") import(str(P, "/stl/robot/hip_servos.stl"));
}
