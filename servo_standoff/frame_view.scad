// The side shoulder frame (Petoi's Bittle_SideShoulder.stl), alone. It is one file: the robot uses it on both sides.
// Frame of the file: X lateral, Y up, Z along the body. Rotated to Z-up for OpenSCAD.
P = "../bittle_platform";
rotate([90, 0, 0]) color("#f2a71c") import(str(P, "/reference/Bittle_SideShoulder.stl"));
