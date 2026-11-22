#!/usr/bin/env python3
"""Build readable schematic + BOM PDF packets for the E.9 perfboards.

Run after ``generar_kicad_perforadas.py`` and the KiCad PDF exports.  Each
packet contains the board schematic followed immediately by its exact BOM.
The combined construction pack interleaves T1 schematic, T1 BOM, ... T5 BOM,
then appends the off-board/panel BOM.
"""
from pathlib import Path
import csv
import subprocess

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware" / "perforadas-modulares"
KICAD = HW / "kicad"
BOM = HW / "bom-por-tarjeta"
OUT = HW / "construction-packets"


def rows_for(assembly):
    with (BOM / f"BOM-{assembly}.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_bom_page(assembly, output):
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("bom", parent=styles["BodyText"], fontName="Helvetica",
                            fontSize=8.2, leading=9.7, alignment=TA_LEFT)
    head = ParagraphStyle("head", parent=normal, fontName="Helvetica-Bold",
                          textColor=colors.white, fontSize=8.5)
    title = "Off-board, panel and guarded Z1 BOM" if assembly == "OFFBOARD" else f"{assembly} component list"
    doc = SimpleDocTemplate(str(output), pagesize=landscape(A4),
                            leftMargin=12*mm, rightMargin=12*mm,
                            topMargin=10*mm, bottomMargin=10*mm)
    story = [Paragraph(title, styles["Title"]),
             Paragraph("Use the reference labels on the preceding schematic to find each component here. "
                       "Quantity means mounted quantity, not spare-purchase quantity.", normal),
             Spacer(1, 4*mm)]
    data = [[Paragraph(x, head) for x in
             ("Reference", "Qty", "Component / value", "Purchase status", "Mounting / verification")]]
    for row in rows_for(assembly):
        data.append([
            Paragraph(row["References"], normal),
            Paragraph(row["Quantity"], normal),
            Paragraph(row["Description"], normal),
            Paragraph(row["Purchase status"], normal),
            Paragraph(row["Mounting / verification"], normal),
        ])
    table = Table(data, repeatRows=1,
                  colWidths=[34*mm, 12*mm, 75*mm, 42*mm, 105*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263746")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#80909c")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#eef2f4")]),
    ]))
    story.append(table)
    doc.build(story)


def merge(output, inputs):
    subprocess.run(["pdfunite", *map(str, inputs), str(output)], check=True)


def main():
    OUT.mkdir(exist_ok=True)
    combined = []
    for board in ("T1", "T2", "T3", "T4", "T5"):
        schematic = KICAD / f"medidor-{board.lower()}.pdf"
        bom_page = OUT / f"{board}-BOM.pdf"
        packet = OUT / f"{board}-schematic-and-BOM.pdf"
        if not schematic.exists():
            raise SystemExit(f"Missing {schematic}; export the KiCad PDFs first")
        make_bom_page(board, bom_page)
        merge(packet, [schematic, bom_page])
        combined.extend((schematic, bom_page))

    offboard = OUT / "OFFBOARD-BOM.pdf"
    make_bom_page("OFFBOARD", offboard)
    combined.append(offboard)
    merge(HW / "medidor-E9-construction-pack.pdf", combined)
    print(HW / "medidor-E9-construction-pack.pdf")


if __name__ == "__main__":
    main()
