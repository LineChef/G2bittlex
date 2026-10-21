// One hip servo (left front) from the repo's hip_servos.stl, alone, to look at its shape.
// Robot frame: X lateral (the output shaft points to -X), Y up, Z along the body. Rotated to Z-up for OpenSCAD.
P = "../bittle_platform";
rotate([90, 0, 0]) color("#4a4c52") intersection() {
    import(str(P, "/stl/robot/hip_servos.stl"));
    translate([-60, -30, -80]) cube([60, 60, 80]);
}
