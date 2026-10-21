// The hip spacer, alone. Z axis, servo side at Z = 0, leg side up.
//   servo side: a female splined socket, like the gear cup in the leg, that the servo's splined shaft fits into
//   leg side:   a male splined stub, like the servo's shaft, that fits into the white gear in the leg
//   an M2 screw goes through the whole spacer (clearance hole) and ties the servo, spacer and gear together
// From your servo specs: 25T spline, 5.0 mm shaft, M2 screw. Best guesses, not measured: the tooth depth and shape,
// how far the shaft reaches, the 10 mm body, and the socket clearance.
shaft_d = 5.0;      // outside diameter of the servo's splined shaft (tooth tips), from the servo specs you gave
tooth_n = 25;       // tooth count (25T), from the servo specs you gave
tooth_h = 0.35;     // tooth depth
reach = 3.5;        // how far the shaft sticks out of the servo, and how far the male stub reaches into the leg gear
fit = 0.15;         // radial clearance of the female socket over the shaft

// spline outline: n trapezoid teeth between the root radius and the tip radius
function spline_pts(r_tip, h, n) = [for (i = [0 : n - 1], a = [
        [0, r_tip - h], [0.15, r_tip], [0.5, r_tip], [0.65, r_tip - h]])
    let (ang = (i + a[0]) * 360 / n) [cos(ang) * a[1], sin(ang) * a[1]]];

module spline_2d(r_tip) { polygon(spline_pts(r_tip, tooth_h, tooth_n)); }

module spacer_part(t = 4, od = 10, screw_d = 2.4) {
    color("#e8641b") difference() {
        union() {
            cylinder(d = od, h = t, $fn = 64);                                          // body between the servo and the leg
            translate([0, 0, t - 0.01]) linear_extrude(reach + 0.01) spline_2d(shaft_d / 2);     // male stub
        }
        translate([0, 0, -0.01]) linear_extrude(reach + 0.01) spline_2d(shaft_d / 2 + fit);       // female socket
        translate([0, 0, -1]) cylinder(d = screw_d, h = t + reach + 2, $fn = 32);                // M2 screw
    }
}

// section = true: cut the part in half to show the socket, the stub and the screw hole
section = false;
if (section) intersection() { spacer_part(); translate([-10, 0, -1]) cube([20, 10, 20]); }
else spacer_part();
