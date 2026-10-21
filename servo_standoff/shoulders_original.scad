// The two outer pieces of the frame, the left and right side shoulders, exactly as Petoi made them: no changes.
// It is one file (Bittle_SideShoulder.stl); the left shoulder is its mirror image. Placed as they are on the robot.
// Robot frame: X lateral (+X = robot right), Y up, Z along the body (-Z = head). Rotated to Z-up for OpenSCAD.
P = "../bittle_platform";
$vpt = [0, 0, 20];      // start with the view framed on the shoulders
$vpr = [60, 0, 320];
$vpd = 330;
rotate([90, 0, 0]) {
    color("#f2a71c") import(str(P, "/reference/Bittle_SideShoulder.stl"));                    // right shoulder
    color("#f2a71c") mirror([1, 0, 0]) import(str(P, "/reference/Bittle_SideShoulder.stl"));  // left shoulder (mirrored)
}
