// USB OBS desk controller - parametric enclosure (OpenSCAD)
// Units: mm. Origin = outer front-left corner at floor level (z = 0).
// Parts: tray (base, walls up to the seam) and lid (flat plate resting on the walls).
// Retention: 2 M2.5 screws into bosses on the right side only (see DIMENSIONS.md section 6, open issue).
// All dimensions match enclosure/DIMENSIONS.md. [A] = assumption. [S] = secondary-source value.
//
// Export (NOT run in the authoring session; see VERIFICATION.md):
//   openscad -D 'part="tray"'     -o tray.stl    case.scad
//   openscad -D 'part="lid"'      -o lid.stl     case.scad
//   openscad -D 'part="exploded"' -o preview.stl case.scad   (display only, do not print)

part = "assembly";      // "tray" | "lid" | "assembly" | "exploded"
$fn = 40;

// ---- Walls and cavity
wall      = 2.0;                 // [A]
floor_t   = 2.0;                 // [A]
lid_t     = 2.0;                 // [A]
in_w      = 76.0;
in_d      = 52.0;
out_w     = in_w + 2*wall;       // 80
out_d     = in_d + 2*wall;       // 56
seam_z    = 15.5;                // lid underside = wall top
clear     = 0.3;

// ---- Pico 2: 21 (X) x 51 (Y) x 1 mm PCB. Holes dia 2.1, pattern 11.4 (X) x 47 (Y) [S]
pico_w = 21.0; pico_l = 51.0; pico_pcb_t = 1.0;
pico_x0 = wall + 2.0;            // PCB left edge (global X) = 4
pico_y0 = wall + 0.5;            // PCB front edge (global Y) = 2.5; USB end at front
pico_pcb_z = floor_t + 4.0;      // PCB bottom z = 6.0 [A]
pico_hole_d = 2.1;
pico_hole_x = [pico_x0 + (pico_w - 11.4)/2, pico_x0 + (pico_w - 11.4)/2 + 11.4];
pico_hole_y = [pico_y0 + 2.0, pico_y0 + 2.0 + 47.0];
usb_w = 9.6; usb_h = 4.0;        // [A]
usb_zc = pico_pcb_z + pico_pcb_t + 1.3;   // [A] plug centre, about 8.3

// ---- OLED Adafruit 938: PCB 35.6 x 33 x 6.2, holes 30.5 x 28 dia 2.5 [S]
oled_w = 35.6; oled_d = 33.0; oled_t = 6.2;
oled_x0 = wall + 26.0; oled_y0 = wall + 9.5;    // (28, 11.5)
oled_hole_d = 2.5;
oled_pcb_z = floor_t + 6.5;      // PCB bottom z = 8.5 [A]
win_w = 30.0; win_d = 16.0;      // [A]

// ---- Keypad board: 11 x 36 x 1.6; 6x6 switch body 4.3 high [A]
kp_w = 11.0; kp_d = 36.0; kp_t = 1.6;
kp_x0 = wall + 63.0; kp_y0 = wall + 8.0;        // (65, 10)
kp_pcb_z = floor_t + 1.0;        // PCB bottom z = 3.0 [A]; switch top = 3.0 + 1.6 + 4.3 = 8.9
btn_xy = [[wall + 68.5, wall + 14.0], [wall + 68.5, wall + 38.0]];   // REC, SCENE (global)
led_xy = [wall + 68.5, wall + 26.0];
btn_hole_d = 10.4;               // [A]
led_hole_d = 5.2;                // [A]

// ---- Screw bosses (right side, clear of keypad board y 10..46)
boss_od = 5.0; boss_id = 2.1;
boss_xy = [[75.5, 4.5], [75.5, 49.5]];
lid_screw_d = 2.7;               // clearance hole in lid for M2.5

// ---- Helpers
module rbox(w, d, h, r=3) {
    hull() for (x=[r, w-r], y=[r, d-r]) translate([x, y, 0]) cylinder(r=r, h=h);
}
module post(od, id, h) {
    difference() { cylinder(d=od, h=h); translate([0,0,-1]) cylinder(d=id, h=h+2); }
}

// ---- Tray
module tray() {
    difference() {
        rbox(out_w, out_d, seam_z);
        translate([wall, wall, floor_t]) cube([in_w, in_d, 100]);
        translate([pico_x0 + pico_w/2 - usb_w/2, -1, usb_zc - usb_h/2]) cube([usb_w, wall + 2, usb_h]);
    }
    for (x = pico_hole_x) for (y = pico_hole_y)
        translate([x, y, floor_t]) post(5, pico_hole_d, pico_pcb_z - floor_t);
    for (dx=[0, 30.5]) for (dy=[0, 28.0])
        translate([oled_x0 + 2.55 + dx, oled_y0 + 2.5 + dy, floor_t]) post(5, oled_hole_d, oled_pcb_z - floor_t);
    for (y = [kp_y0 + 2, kp_y0 + kp_d - 2])
        translate([kp_x0 + kp_w/2, y, floor_t]) post(4, 2.1, kp_pcb_z - floor_t);
    for (p = boss_xy) translate([p[0], p[1], floor_t]) post(boss_od, boss_id, seam_z - floor_t);
}

// ---- Lid: flat plate, bottom at z = 0 (local), placed on the walls at seam_z
module lid() {
    difference() {
        rbox(out_w, out_d, lid_t);
        translate([oled_x0 + oled_w/2 - win_w/2, oled_y0 + oled_d/2 - win_d/2, -1])
            cube([win_w, win_d, lid_t + 2]);
        for (p = btn_xy) translate([p[0], p[1], -1]) cylinder(d=btn_hole_d, h=lid_t + 2);
        translate([led_xy[0], led_xy[1], -1]) cylinder(d=led_hole_d, h=lid_t + 2);
        for (p = boss_xy) translate([p[0], p[1], -1]) cylinder(d=lid_screw_d, h=lid_t + 2);
    }
}

module lid_on_tray() { translate([0, 0, seam_z]) lid(); }

module proxy_pcb(x, y, z, l, w, t, col) { color(col) translate([x, y, z]) cube([l, w, t]); }

if (part == "tray") tray();
else if (part == "lid") lid();
else if (part == "exploded") {
    tray();
    translate([0, 0, 12]) lid_on_tray();
    proxy_pcb(pico_x0, pico_y0, pico_pcb_z, pico_w, pico_l, pico_pcb_t, "green");
    proxy_pcb(oled_x0, oled_y0, oled_pcb_z, oled_w, oled_d, oled_t, "navy");
    proxy_pcb(kp_x0, kp_y0, kp_pcb_z, kp_w, kp_d, kp_t, "gray");
}
else { tray(); lid_on_tray(); }
