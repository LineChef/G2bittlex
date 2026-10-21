// Minimal feet for the Bittle (concept only): one smooth piece, one color. A short rounded cuff over the
// stock foot, flowing into a flat sole. Estimates, not measured on a robot.
// Four-tooth feet: four small contact teeth instead of a pad. Stability in all four directions with a small footprint.
//   W  whole paw   : a paw from the ground up: domed palm, toe lobes with small claws, a flared wrist
//   P  paw         : a palm pad with four toe pads in an arc at the front, like a paw print
//   Q  cross       : teeth front, back, left, right (24 mm along the body, 26 mm across)
//   R  compact X   : teeth at the four corners of a 17 mm square (22 x 22 mm)
//   S  lifted X    : like R, with the two front teeth raised 1.2 mm so a front tooth does not catch the ground
// Every tooth is a short, tapered wedge with a chamfered tip, low and smooth so it does not snag.
// Stability feet: centered under the foot, no change to the stance.
//   H  wide pad    : a flat 26 x 22 mm sole, a larger contact patch in both directions
//   J  round plate : a round 26 mm sole with grip rings, the same footing whichever way the foot turns
//   K  long pad    : a 34 x 14 mm sole along the body, for fore and aft stability, toe-up
//   L  flex skirt  : a thin 30 mm skirt around a small core that bends to follow uneven ground
// Stance feet (offset outward):
//   E  stance +10  : a short, wide sole (20 x 18 mm) shifted 10 mm outward, toe-up
//   F  round       : a round sole (24 mm across), 3 mm outward
//   G  short ski   : a 30 x 12 mm sole along the body, 4 mm outward, toe-up
// The cuff covers the bottom 10 mm of the stock foot (14 x 12 mm). A flexing tab on each side has a small pin that
// snaps into the hole in the foot (position and size guessed). Printed in PETG or nylon.
// Local frame: Z up, the sole on the bed at Z = 0, X = lateral (+X = outward, away from the body), Y = along the body.
// The toe is +Y (the head end on the robot).
// Set style = "M" for the mech paw (like the robot wolf), "N" for the lion paw, "V" for the slipper foot (like your photos), "W" for the whole-paw foot, "P" for the paw base only, "all" for Q-S side by side, "pads" for H-L, "stance" for E-G, or one letter.
style = "M";
section = false;     // true: cut in half along the body to show the socket

color_main = "#e8641b";

foot_l = 14;         // along the body (Y here)
foot_w = 12;         // across the body (X here)
cap_h = 10;          // how far the cuff covers the foot
clear = 0.3;         // clearance around the foot, per side
wall = 2.0;          // cuff wall
floor_t = 3;         // thickness of the base under the foot
hole_d = 2.5;        // hole in the stock foot (guess)
hole_z = 5;          // height of the hole above the sole's top face (guess)
pin_d = hole_d - 0.4;
pin_in = 1.0;        // how far the pin tip goes into the right arm
tab_w = 7;           // flexing tab in each side wall
slit = 0.6;

in_w = foot_w + 2*clear;
in_l = foot_l + 2*clear;
sock_w = in_w + 2*wall;
sock_l = in_l + 2*wall;
top_z = floor_t + cap_h;

module rrect(l, w, r, h) {       // rounded rectangle, l along Y, w along X, corner radius r, height h
    linear_extrude(h) offset(r) square([w - 2*r, l - 2*r], center = true);
}
module stadium(l, w, h) { rrect(l, w, w/2 - 0.05, h); }       // a rounded oblong: the ends are half circles

module cuff_outer() {            // a short oval cuff, slightly narrower at the top
    hull() {
        translate([0, 0, floor_t - 0.01]) stadium(sock_l, sock_w, 0.01);
        translate([0, 0, top_z - 0.01]) stadium(sock_l - 1.2, sock_w - 1.2, 0.01);
    }
}
module socket_hole() { translate([0, 0, floor_t]) stadium(in_l, in_w, cap_h + 1); }

module slab(off, l, w, r) {      // the flat sole with softly rounded edges
    translate([off, 0, 0]) hull() {
        rrect(l - 2.4, w - 2.4, max(r - 1.2, 0.6), 0.01);
        translate([0, 0, 1.2]) rrect(l, w, r, floor_t - 2.4);
        translate([0, 0, floor_t - 0.01]) rrect(l - 2.4, w - 2.4, max(r - 1.2, 0.6), 0.01);
    }
}
module sole_top(off, l, w) { translate([off, 0, floor_t - 1.2]) rrect(l - 2.4, w - 2.4, 1.6, 0.02); }

module blend(off, l, w) {        // a smooth flow from the sole's top edge up into the cuff
    hull() {
        translate([0, 0, floor_t - 0.01]) stadium(sock_l, sock_w, 2.5);
        sole_top(off, l, w);
    }
}
module toe_wedge(off, l, w) {    // lifts the front 6 mm of the sole's underside
    translate([off, 0, 0]) hull() {
        translate([-w, l/2 - 6, -0.01]) cube([2*w, 0.01, 0.01]);
        translate([-w, l/2 + 0.5, -0.01]) cube([2*w, 0.01, 1.5]);
    }
}

module rect_foot(off, l, w) {
    difference() {
        union() { cuff_outer(); slab(off, l, w, 3); blend(off, l, w); }
        socket_hole();
        toe_wedge(off, l, w);
        tab_slits();
    }
    snap_pins();
}
module round_foot(off, d, rings = false) {
    difference() {
        union() {
            cuff_outer();
            translate([off, 0, 0]) hull() {
                cylinder(d = d - 2.4, h = 0.01, $fn = 64);
                translate([0, 0, 1.2]) cylinder(d = d, h = floor_t - 2.4, $fn = 64);
                translate([0, 0, floor_t - 0.01]) cylinder(d = d - 2.4, h = 0.01, $fn = 64);
            }
            hull() {
                translate([0, 0, floor_t - 0.01]) stadium(sock_l, sock_w, 2.5);
                translate([off, 0, floor_t - 1.2]) cylinder(d = d - 3, h = 0.02, $fn = 64);
            }
        }
        socket_hole();
        tab_slits();
        if (rings) for (r = [d/2 - 3, d/2 - 6]) translate([off, 0, -0.01]) difference() {
            cylinder(r = r + 0.5, h = 0.7, $fn = 64);
            translate([0, 0, -1]) cylinder(r = r - 0.5, h = 3, $fn = 64);
        }
    }
    snap_pins();
}

// a thin skirt around a small core
module skirt_foot(d, core) {
    difference() {
        union() {
            cuff_outer();
            hull() {
                cylinder(d = d, h = 1.2, $fn = 64);
                cylinder(d = core, h = floor_t, $fn = 64);
            }
            hull() {
                translate([0, 0, floor_t - 0.01]) stadium(sock_l, sock_w, 2.5);
                cylinder(d = core - 1, h = floor_t - 0.5, $fn = 64);
            }
        }
        socket_hole();
        tab_slits();
    }
    snap_pins();
}

// four-tooth foot: tips = [x, y, raise] of each tooth tip center
module tooth(x, y, raise = 0, tip = 6.5) {
    hull() {
        translate([0, 0, 0]) stadium(sock_l - 3, sock_w - 3, floor_t);                         // the hub under the cuff
        translate([x, y, raise]) cylinder(d = tip - 1.4, h = 0.01, $fn = 32);                  // chamfered tip, on the ground
        translate([x, y, raise + 0.7]) cylinder(d = tip, h = floor_t - 1.2, $fn = 32);
    }
}
// no cuff: two thin arms rise from the hub, one on each side of the foot. Each has a pin that clips into the hole.
// Bend the arms apart to put the foot on or take it off.
arm_t = 2.4;         // arm thickness
arm_w = 8;           // arm width along the body
arm_top = 2.2;       // the arm reaches this far above the hole center (the pin radius is 1.05)
module clip_arms() {
    // the left arm is fixed and carries a pin that goes all the way through the hole in the foot. The right arm is
    // the latch: bend it outward, slide the foot onto the pin from the right, then let the arm go. The tip of the pin
    // snaps into a blind hole in the right arm.
    z0 = floor_t + hole_z;
    difference() {
        union() {
            for (sx = [-1, 1])
                translate([sx * (in_w/2 + arm_t/2), 0, floor_t + (hole_z + arm_top)/2])
                    hull() {                       // rounded top
                        cube([arm_t, arm_w, hole_z + arm_top - 1], center = true);
                        translate([0, 0, (hole_z + arm_top)/2 - 0.5]) rotate([0, 90, 0]) cylinder(d = arm_w, h = arm_t, center = true, $fn = 24);
                    }
            // the pin: from inside the left arm, across the foot, into the right arm
            translate([-in_w/2 - 0.5, 0, z0]) rotate([0, 90, 0]) cylinder(d = pin_d, h = in_w + 0.5 + pin_in, $fn = 24);
        }
        // living hinge: the right arm is thinned to 0.8 mm at its base so it can fold outward and down
        translate([in_w/2 + 0.8 + (arm_t - 0.8 + 0.2)/2, 0, floor_t + 0.75]) cube([arm_t - 0.8 + 0.2, arm_w + 2, 1.5], center = true);   // removes the outer 1.6 mm, leaves 0.8
        // blind hole in the right arm that catches the tip of the pin (a little larger than the pin)
        translate([in_w/2 + arm_t - 0.01, 0, z0]) rotate([0, -90, 0]) cylinder(d = pin_d + 0.3, h = pin_in + 0.5 + 0.01, $fn = 24);
    }
}
// a very short cuff: a low rim around the toe and heel of the foot. It is open at the sides, where the arms are,
// so the right arm can still fold out.
cuff_h = 4;          // how far the rim rises above the base
cuff_lean = 1.2;     // the cuff leans inward: its outside is this much closer to the foot at the top, per side
module short_cuff() {
    difference() {
        union() {
            stadium(sock_l, sock_w, floor_t);
            hull() {                                    // the outer face leans inward toward the top
                translate([0, 0, floor_t - 0.01]) stadium(sock_l, sock_w, 0.01);
                translate([0, 0, floor_t + cuff_h - 0.01]) stadium(sock_l - 2*cuff_lean, sock_w - 2*cuff_lean, 0.01);
            }
        }
        translate([0, 0, floor_t]) stadium(in_l, in_w, cuff_h + 1);
        for (sx = [-1, 1]) translate([sx * sock_w/2, 0, floor_t + cuff_h/2 + 0.5]) cube([wall*2 + 2, arm_w + 1.6, cuff_h + 1], center = true);
    }
}
// backstop: a taller, thicker wall at the heel, up to 2 mm above the pin. The foot pivots on the pin, and its lower
// rear edge rests on this wall, so it cannot swing backward (toward the heel). Swinging forward is not limited.
back_h = 7;          // how far the backstop rises above the base (the pin is 5 mm above the base)
back_t = 3;          // thickness of the backstop wall
module backstop() {
    intersection() {
        difference() {
            stadium(sock_l + 2, sock_w, floor_t + back_h);
            translate([0, 0, floor_t]) stadium(in_l, in_w, back_h + 1);
        }
        translate([-sock_w, -(sock_l + 2)/2 - 1, 0]) cube([2*sock_w, back_t + 1, floor_t + back_h + 1]);
    }
}
// paw base: a palm pad and four toe pads in an arc at the toe end (+Y)
toe_d = 6.5;
toes = [[-9.5, 6.5], [-3.5, 11.5], [3.5, 11.5], [9.5, 6.5]];
module pad_disc(d, h = floor_t) {            // a round pad with a chamfered bottom edge
    cylinder(d1 = d - 1.2, d2 = d, h = 0.7, $fn = 40);
    translate([0, 0, 0.7 - 0.01]) cylinder(d = d, h = h - 0.7 + 0.01, $fn = 40);
}
module paw_base() {
    translate([0, -2, 0]) scale([1, 0.85, 1]) pad_disc(21);                       // the palm
    for (t = toes) hull() {                                                       // each toe joins the palm
        translate([t[0], t[1], 0]) pad_disc(toe_d);
        translate([t[0] * 0.45, 2.5, 0]) pad_disc(5);
    }
}
// whole-paw foot (style W): domed palm, domed toe lobes with small raised claws, and a flared wrist around the foot.
// The attachment is the same as the other four-tooth feet: the left arm and pin, the folding right arm, the heel backstop.
claw_len = 2.2;      // the claws are blunt and raised off the ground so they do not catch
module paw_dome_base() {
    hull() {                                                          // the palm
        translate([0, -2, 0]) scale([1, 0.85, 1]) pad_disc(21);
        translate([0, -2, floor_t]) scale([1, 0.85, 0.35]) sphere(d = 19, $fn = 40);
    }
    for (t = toes) {
        hull() {                                                      // a toe lobe, joined to the palm
            translate([t[0], t[1], 0]) pad_disc(toe_d);
            translate([t[0], t[1], floor_t]) scale([1, 1, 0.55]) sphere(d = toe_d - 0.6, $fn = 24);
            translate([t[0] * 0.45, 2.5, 0]) pad_disc(5);
        }
        translate([t[0], t[1] + toe_d/2 - 0.8, 1.9]) rotate([-90, 0, 0])      // a blunt claw at the toe tip
            cylinder(d1 = 2.4, d2 = 1.0, h = claw_len, $fn = 16);
    }
}
module paw_wrist() {                                                  // a flared wrist that leans in toward the top
    hull() {
        translate([0, 0, floor_t - 0.01]) stadium(sock_l + 3, sock_w + 4, 0.01);
        translate([0, 0, floor_t + cuff_h + 1 - 0.01]) stadium(sock_l - 2*cuff_lean, sock_w - 2*cuff_lean, 0.01);
    }
}
module paw_foot() {
    difference() {
        union() { paw_dome_base(); paw_wrist(); backstop(); }
        translate([0, 0, floor_t]) stadium(in_l, in_w, 14);                       // the pocket for the foot
        for (sx = [-1, 1]) translate([sx * sock_w/2, 0, floor_t + 6]) cube([16, arm_w + 1.6, 12], center = true);   // room for the arms
    }
    stadium(sock_l - 3, in_w + 2*arm_t, floor_t);        // the plate the foot sits on
    clip_arms();
}

// slipper foot (style V), after the printed foot in your photos: a rounded-rectangle body that is tall at the heel and
// lower toward the toe, with a rectangular window for the foot, open at the top, and three ribs on the toe.
// The foot drops in from above, then a pin goes through one cheek, the hole in the foot and the other cheek.
// The heel wall of the window is the backstop.
rib_n = 3;
module slipper_foot() {
    ow = in_w + 2*arm_t;                                            // outside width: two 2.4 mm cheeks
    z_h = floor_t + hole_z + 3;                                     // heel top
    z_t = floor_t + 3.5;                                            // toe top
    color(color_main) difference() {
        union() {
            hull() {                                                // the body: base, heel top, toe top
                translate([0, 2.5, 0]) rrect(27, ow, 3, 0.01);
                translate([0, -3.5, z_h - 0.01]) rrect(15, ow - 1, 2.5, 0.01);
                translate([0, 12, z_t - 0.01]) rrect(8, ow - 1, 2.5, 0.01);
            }
            for (i = [0 : rib_n - 1]) translate([0, 9.9 + i * 2.3, z_t - 0.05])      // ribs on the toe
                rrect(1.8, ow - 5, 0.7, 1.6);
        }
        translate([0, 0, floor_t]) rrect(in_l, in_w, 1.2, 20);                       // the window for the foot, open at the top
        translate([0, 0, floor_t + hole_z]) rotate([0, 90, 0]) cylinder(d = pin_d + 0.2, h = 30, center = true, $fn = 24);   // pin hole
    }
    color("#2c2d31") translate([0, 0, floor_t + hole_z]) rotate([0, 90, 0]) {       // the pin, with a head on the +X side
        cylinder(d = pin_d, h = ow + 0.5, center = true, $fn = 24);
        translate([0, 0, ow/2 + 0.25]) cylinder(d = 3.6, h = 0.8, $fn = 24);
    }
}

// lion paw (style N): the slipper's attachment (window open at the top, one pin through both cheeks, heel wall as the
// backstop) in a chunky paw: a tall furry wrist at the heel, a big domed palm, four fat toes with claws.
lion_toes = [[-10.5, 7.5], [-4.2, 13], [4.2, 13], [10.5, 7.5]];
lion_td = 8;
module lion_paw() {
    ow = in_w + 2*arm_t;
    z_h = floor_t + hole_z + 3;
    color(color_main) difference() {
        union() {
            hull() {                                                      // the wrist block that holds the window
                translate([0, -1.5, 0]) rrect(in_l + 7, ow, 4, 0.01);
                translate([0, -2.5, z_h - 0.01]) rrect(in_l + 3, ow - 2, 3, 0.01);
            }
            hull() {                                                      // the palm
                translate([0, 0, 0]) scale([1, 0.8, 1]) pad_disc(24);
                translate([0, 0, floor_t]) scale([1, 0.8, 0.35]) sphere(d = 21, $fn = 40);
            }
            for (t = lion_toes) {
                hull() {                                                  // a fat toe, joined to the palm
                    translate([t[0], t[1], 0]) pad_disc(lion_td);
                    translate([t[0], t[1], floor_t]) scale([1, 1, 0.6]) sphere(d = lion_td - 0.6, $fn = 24);
                    translate([t[0] * 0.5, 3, 0]) pad_disc(6);
                }
                translate([t[0], t[1] + lion_td/2 - 0.8, 2.2]) rotate([-90, 0, 0])
                    cylinder(d1 = 2.8, d2 = 1.0, h = 3, $fn = 16);        // a blunt claw
            }
            for (i = [0 : 2]) translate([0, -2.5 - (in_l + 3)/2 - 0.2, 3 + i * 2.6]) rotate([0, 0, 0])
                scale([1, 0.35, 1]) rotate([0, 90, 0]) cylinder(d = 3, h = ow - 3 - i, center = true, $fn = 20);   // fur ridges on the heel
        }
        translate([0, 0, floor_t]) rrect(in_l, in_w, 1.2, 20);                       // the window for the foot, open at the top
        translate([0, 0, floor_t + hole_z]) rotate([0, 90, 0]) cylinder(d = pin_d + 0.2, h = 30, center = true, $fn = 24);
    }
    color("#2c2d31") translate([0, 0, floor_t + hole_z]) rotate([0, 90, 0]) {       // the pin, with a head on the +X side
        cylinder(d = pin_d, h = ow + 0.5, center = true, $fn = 24);
        translate([0, 0, ow/2 + 0.25]) cylinder(d = 3.6, h = 0.8, $fn = 24);
    }
}

// mech paw (style M), after the black feet of the robot wolf in your photo: a chunky rounded boot with a flat sole, a
// rounded toe, a taller heel and a window for the foot, with a pivot ring where the pin goes through.
// Same attachment as V and N: the foot drops into the window, one pin through both cheeks and the hole in the foot.
leg_w = 8;           // the width of the leg at the ankle, which the backstop lip matches: 8 mm in the shank mesh (7 to 9.4 mm over the ankle); your 12 mm foot is wider
module mech_paw() {
    ow = in_w + 2*arm_t + 1;                                         // outside width
    z_h = floor_t + hole_z + 2.2;                                    // heel top: lower, with less material behind the pin
    z_t = floor_t + 5.8;                                             // toe top: higher, so the front is flatter
    color("#26272b") difference() {
        union() {
            hull() {                                                              // softly rounded all round
                translate([0, 2.75, 0]) rrect(24.5 - 2.4, ow - 2.4, 6, 0.01);                // sole edge
                translate([0, 2.75, 1.2]) rrect(24.5, ow, 7.5, 1.6);                         // the full outline, with straight sides
                translate([0, -2.2, z_h - 1.6]) rrect(13 + 1.6, ow - 2 + 1.6, 5.5, 0.01);    // heel top, rounded edge
                translate([0, -2.2, z_h - 0.01]) rrect(13, ow - 2, 5, 0.01);
                translate([0, 8.2, z_t - 1.6]) rrect(12 + 1.6, ow - 2 + 1.6, 6, 0.01);       // toe top, rounded edge
                translate([0, 8.2, z_t - 0.01]) rrect(12, ow - 2, 5.5, 0.01);
            }
            // subtle backstop: a low lip behind the leg, as wide as the leg, following the rounded heel contour of the window
            intersection() {
                difference() {
                    translate([0, 0, z_h - 0.5]) rrect(in_l + 3.6, in_w + 3.6, 2.4, 2.3);
                    translate([0, 0, z_h - 1]) rrect(in_l, in_w, 1.2, 4);
                }
                translate([-leg_w/2, -in_l/2 - 5, z_h - 1]) cube([leg_w, 5 + 0.01, 4]);
            }
            for (sx = [-1, 1]) translate([sx * (ow/2 - 0.3), 0, floor_t + hole_z]) rotate([0, 90, 0])
                cylinder(d = 7, h = 0.9, center = true, $fn = 32);                  // the pivot rings
        }
        translate([0, 0, floor_t]) rrect(in_l, in_w, 1.2, 20);                       // the window for the foot
        translate([0, 0, floor_t + hole_z]) rotate([0, 90, 0]) cylinder(d = pin_d + 0.2, h = 30, center = true, $fn = 24);
        translate([0, 6.2, z_t + 0.4]) cube([ow - 4, 0.7, 2], center = true);      // a crease across the toe base (0.6 mm deep, not through the sides)
        for (gx = [-4.6, 0, 4.6]) hull() {                                            // three grooves split the toe into four
            translate([gx, 6.6, z_t + 0.35]) sphere(d = 1.9, $fn = 16);
            translate([gx, 13.6, z_t + 0.35]) sphere(d = 1.9, $fn = 16);
            translate([gx, 14.7, z_t - 0.9]) sphere(d = 1.9, $fn = 16);
            translate([gx, 15.4, z_t - 2.6]) sphere(d = 1.9, $fn = 16);
            translate([gx, 15.6, z_t - 4.8]) sphere(d = 1.9, $fn = 16);
        }
    }
    color("#c9ccd1") translate([0, 0, floor_t + hole_z]) rotate([0, 90, 0]) {       // the pin, with a head on the +X side
        cylinder(d = pin_d, h = ow + 1.2, center = true, $fn = 24);
        translate([0, 0, ow/2 + 0.6]) cylinder(d = 3.8, h = 0.8, $fn = 24);
    }
}

module teeth_foot(tips, paw = false) {
    union() {
        short_cuff();
        backstop();
        if (paw) paw_base();
        else for (t = tips) tooth(t[0], t[1], t[2]);
        stadium(sock_l - 3, in_w + 2*arm_t, floor_t);        // the plate the foot sits on
        clip_arms();
    }
}
module teeth_foot_cuff(tips) {
    difference() {
        union() {
            cuff_outer();
            hull() {
                translate([0, 0, floor_t - 0.01]) stadium(sock_l, sock_w, 2.5);
                stadium(sock_l - 3, sock_w - 3, floor_t - 0.5);
            }
            for (t = tips) tooth(t[0], t[1], t[2]);
        }
        socket_hole();
        tab_slits();
    }
    snap_pins();
}

// a flexing tab in each side wall (a U-shaped slit, attached at the bottom) with a snap pin on its inside face
module tab_slits() {
    zb = floor_t + 1.5; zt = top_z - 0.8;
    for (sx = [-1, 1]) {
        for (sy = [-1, 1]) translate([sx * sock_w/2, sy * (tab_w/2 + slit/2), (zb + zt)/2]) cube([6, slit, zt - zb], center = true);
        translate([sx * sock_w/2, 0, zt - slit/2]) cube([6, tab_w + 2*slit, slit], center = true);
    }
}
module snap_pins() {
    for (sx = [-1, 1])
        translate([sx * in_w/2, 0, floor_t + hole_z]) rotate([0, -sx * 90, 0])
            cylinder(d1 = pin_d, d2 = pin_d - 0.8, h = pin_len, $fn = 24);
}

module foot(s = "E") {
    // M, N and V set their own colors (body and pin), so they are not inside the one-color wrapper
    if (s == "M") mech_paw();
    else if (s == "N") lion_paw();
    else if (s == "V") slipper_foot();
    else color(color_main) {
        if (s == "E") rect_foot(10, 20, 18);
        else if (s == "G") rect_foot(4, 30, 12);
        else if (s == "F") round_foot(3, 24);
        else if (s == "H") rect_foot(0, 26, 22);
        else if (s == "J") round_foot(0, 26, true);
        else if (s == "K") rect_foot(0, 34, 14);
        else if (s == "L") skirt_foot(30, 18);
        else if (s == "W") paw_foot();
        else if (s == "P") teeth_foot([], true);
        else if (s == "Q") teeth_foot([[10.5, 0, 0], [-10.5, 0, 0], [0, 9.5, 0], [0, -9.5, 0]]);
        else if (s == "R") teeth_foot([[8.5, 8.5, 0], [-8.5, 8.5, 0], [8.5, -8.5, 0], [-8.5, -8.5, 0]]);
        else teeth_foot([[8.5, 8.5, 1.2], [-8.5, 8.5, 1.2], [8.5, -8.5, 0], [-8.5, -8.5, 0]]);
    }
}

module label(t) { color("#9a9a96") translate([-8, -26, 0]) linear_extrude(0.6) text(t, size = 5); }

module show() {
    if (style == "all") for (i = [0 : 2]) translate([i * 44, 0, 0]) {
        foot(["Q", "R", "S"][i]);
        label(["Q  cross", "R  compact X", "S  lifted X"][i]);
    }
    else if (style == "pads") for (i = [0 : 3]) translate([i * 44, 0, 0]) {
        foot(["H", "J", "K", "L"][i]);
        label(["H  wide pad", "J  round plate", "K  long pad", "L  flex skirt"][i]);
    }
    else if (style == "stance") for (i = [0 : 2]) translate([i * 44, 0, 0]) {
        foot(["E", "F", "G"][i]);
        label(["E  stance +10", "F  round", "G  short ski"][i]);
    }
    else foot(style);
}

if (section) intersection() { show(); translate([-60, -60, -1]) cube([260, 60, 60]); }   // keep Y < 0
else show();
