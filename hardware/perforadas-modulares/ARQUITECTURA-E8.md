# Current E.9 architecture — touch energy meter and 12 V input

The filename is kept for compatibility. E.9 is the current mechanical architecture: the main ESP32 retains acquisition, calibration, energy, alarms, Wi-Fi and publishing. The horizontal LilyGO T4-S3 is a touch terminal that receives already-calculated state over ESP-NOW.

## Physical partition

| Assembly | Size | Responsibility |
|---|---:|---|
| T1 Power | 50 × 40 mm | Input protection and 12 V / 5 V distribution; cut from the user's 60 × 40 mm board |
| U4 buck | reserved 43 × 21 × 14 mm | Separate LM2596 in an integrated snap cradle; generates 5 V |
| T2 Current + VBIAS | 70 × 55 mm | Two SCT channels, burdens and VBIAS |
| T3 Voltage ELV | 55 × 45 mm | ELV-side ZMPT101B conditioning |
| T4 Control | 80 × 65 mm | Main ESP32, acquisition, status LED, Wi-Fi and ESP-NOW |
| T5 Interface + alerts | 65 × 50 mm | 74HCT245, FCOB output and piezo driver; no encoder circuitry |
| Z1 mains | isolated compartment | Fuse, protected terminal and ZMPT101B primary |
| Lid | — | Horizontal LilyGO touch display, status LED, piezo and FCOB; no buttons or encoder |

This partition matches the current CAD and the available T1–T5 schematics. It keeps analog inputs away from the buck, FCOB, piezo and Wi-Fi. The LM2596 is not forced onto the former MT3608 footprint.

## Power tree

The verified panel connector is the purchased CON-156A, 5.5 × 2.5 mm, center positive. The planned external input is isolated 12 V DC.

- Protected 12 V feeds the 12 V FCOB branch.
- U4 LM2596 is adjusted to 5.0 V for the ESP32, LilyGO, 74HCT245 and analog electronics.
- Never connect logic until output voltage, polarity and temperature have been checked under a current-limited load.
- The 43 × 21 × 14 mm LM2596 envelope is conservative. Print its fit coupon and measure the actual module before claiming a final fit.

The E.9 KiCad T1 sheet matches this power tree and all five sheets pass ERC with
zero violations. The CAD and ERC do not constitute electrical approval; adjust
and load-test the exact LM2596 module before connecting the electronics.

## Display and touch contract

The LilyGO is horizontal. The main ESP32 sends a versioned `TelemetryPacket` over ESP-NOW; the LilyGO validates it and shows `NO DATA` after timeout. Only protected 5 V and GND pass to the lid. Do not power the LilyGO simultaneously from the harness and USB-C.

All local navigation, acknowledgement and view selection use touch targets.
SW1, SW2 and ENC1 are absent from E.9. The interface must provide targets at
least 9 mm wide, visible pressed state, timeout/fault feedback and a confirmation
step for destructive resets.

## Mechanical contract

- The enclosure lid uses press-fit magnets and printed alignment features.
- The display backplate, FCOB tray and piezo retainer use sliding or bayonet snap fits.
- Boards use printed standoffs and elastic locating pins.
- The opaque Z1 guard uses blind snap sockets; removal requires deliberate tool access. This has not been certified as a regulatory safety enclosure.
- Electrical terminal screws and connector panel nuts remain intrinsic parts of purchased connectors; no enclosure assembly screw is used.
- Exact fit is accepted only after printing the fit coupons with the final material, nozzle and profile.
