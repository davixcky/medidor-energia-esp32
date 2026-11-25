# Energy meter E.9 — horizontal LilyGO, touch UI and 12 V input

The folder name is historical. This is the current mechanical model: a 280 × 180 × 70 mm printed enclosure with a horizontal LilyGO T4-S3, no physical user buttons, no encoder, no glue and no enclosure assembly screws.

## Current design

- The flush LilyGO glass is retained from inside by an open sliding backplate with printed keyhole features.
- The removable lid closes with four press-fit magnet pairs and printed alignment stops; there is no hinge. A smooth 19 mm fingertip scallop in the front wall gives access under the lid without adding a handle.
- The LED bar uses a captive printed tray and hex diffuser. The strip’s adhesive is not required.
- The piezo uses an integrated cup and bayonet retainer.
- Perfboards locate on printed standoffs and elastic pins.
- The opaque mains guard uses blind snap sockets and deliberate tool-assisted removal. This is not evidence of regulatory certification.
- Intrinsic terminal screws, trimmers and connector panel nuts remain part of purchased components; they are not enclosure fasteners.
- The verified panel power connector is CON-156A, 5.5 × 2.5 mm, center positive. E.9 plans 12 V input and a separate LM2596 buck adjusted to 5.0 V.

The 43 × 21 × 14 mm LM2596 space is conservative because the exact module has not been identified or measured. Do not claim a final fit until its coupon passes with the real part.

## External connector map

- Left wall: two panel-mounted 3.5 mm female sockets for the two SCT current-clamp plugs. Their metal panel rings and threaded bodies are part of the purchased connectors.
- Right wall: one CON-156A 5.5 × 2.5 mm center-positive barrel jack for the 12 V DC supply. This feeds the protected 12 V rail and the LM2596 buck stage.
- Rear wall: one PG7 cable gland for the separately guarded mains-voltage sensing cable. It is not the power-supply input.
- Internal service access: the ESP32 USB-C connector remains inside under the removable magnetic lid. The enclosure has no approximate or oversized USB opening; routine firmware updates should use OTA.

The connector openings and retainers are represented in the CAD, but production fit still depends on passing the corresponding printed coupons with the exact purchased parts.

## Regenerate

```sh
sh 3d/revision-e7/regenerar.sh cad
sh 3d/revision-e7/regenerar.sh bambu
sh 3d/revision-e7/regenerar.sh json
sh 3d/revision-e7/regenerar.sh vistas
sh 3d/revision-e7/regenerar.sh validar-renders
```

The still images are the current visual reference. Old videos are intentionally not regenerated.

## Main outputs

- `medidor-E7-perforadas.FCStd` and `.step`: editable CAD and neutral export.
- `stl/`: enclosure, lid, mains guard, FCOB tray/diffuser, screen backplate and piezo bayonet ring.
- `bambu/E9-completo-generado.3mf`: generated five-plate Bambu Studio project. Plate 1 is the mandatory fit-test set; plates 4 and 5 use Tree Hybrid support with small-overhang filtering disabled, three 0.25 mm interface layers, a 0.10 mm top gap and a 12 mm brim because the one-piece body and lid must stand on edge on the 256 × 256 mm P2S bed.
- `bambu/E9-*.3mf`: individual native 3MF projects generated from the same STL files. Files with other names are treated as user projects and are not overwritten.
- `pruebas-de-ajuste/`: ten fit coupons, including the LilyGO stack, CON-156A, 3.5 mm jacks, magnets, LM2596 cradle and mains-guard snap.
- `medidor-E7-{cerrado,abierto,planta,trasera,tapa-interior,difusor,cierre-magnetico}.png`: current Blender stills.
- `medidor-E9-entradas-SCT.png` and `medidor-E9-alimentacion-12V.png`: external connector inspection views.
- `medidor-E9-ruta-alimentacion-interior.png`: visible power chain from the barrel-jack solder lugs to protected input J1, and the removable T1 ↔ LM2596 input/output harnesses.
- `medidor-E8-pantalla-soporte-explotado.png`: screwless screen assembly order.
- `validacion-3d.json`: CAD checks and known limitations.
- `validacion-renders.json`: render integrity and freshness checks.
- `medidas-componentes.json`: dimension evidence and unresolved measurements.
- `BEST-PRACTICES.md`: project-specific touch, power, fit and safety practices.

## Fit-test order

Open `bambu/E9-completo-generado.3mf` and print **only plate 1** first, using the same material, nozzle and process intended for the enclosure. Do not start plates 4 and 5 until the purchased components pass their coupons.

1. Measure every purchased part with calipers and compare it with `medidas-componentes.json`.
2. Test rigid sliding fits, snap retention and removal without forcing the component.
3. Record the accepted clearance and update the CAD source.
4. Regenerate CAD, STL, Bambu projects and stills.
5. Only then print the full enclosure.

The coupons cover geometry, not electrical safety. In particular, the mains guard does not validate creepage, clearance, insulation, flammability or tool-access rules.

The ESP32 USB-C is intentionally internal and is reached after removing the magnetic lid. Firmware updates should normally use OTA. A future external USB-C port requires a specific measured snap-in panel extension; a bare opening aligned approximately with the board connector is not acceptable.

## Electrical construction status

The E.9 T1 KiCad schematic now represents the 12 V input, protected 12 V rail,
separate LM2596 input/output harnesses and regulated 5 V distribution used by
the CAD. All five sheets pass KiCad ERC with zero violations. This is a design
consistency check, not approval of a physical build: verify polarity, adjust U4
to 5.0 V with all loads disconnected, then test it under a current-limited load.
