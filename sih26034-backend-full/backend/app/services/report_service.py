"""
services/report_service.py
Generates a PDF compliance report for one inspection using ReportLab.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage

from app.core.config import settings


def generate_report_pdf(inspection, declarations, violations) -> str:
    os.makedirs(settings.report_dir, exist_ok=True)
    output_path = os.path.join(settings.report_dir, f"inspection_{inspection.id}_report.pdf")

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []

    story.append(Paragraph("Legal Metrology Compliance Report", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"Inspection ID: {inspection.id}", styles["Normal"]))
    story.append(Paragraph(f"Product: {inspection.product_name or 'N/A'}", styles["Normal"]))
    story.append(Paragraph(f"Status: {inspection.status}", styles["Normal"]))
    story.append(Paragraph(f"Score: {inspection.score}", styles["Normal"]))
    story.append(Paragraph(f"Date: {inspection.created_at}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    if inspection.image_path and os.path.exists(inspection.image_path):
        # ReportLab's Image flowable loads the file lazily during doc.build(),
        # not at construction time, so we must validate with PIL up front -
        # wrapping the Image() call itself in try/except does NOT catch a
        # corrupt/unsupported file.
        try:
            with PILImage.open(inspection.image_path) as im:
                im.verify()
            story.append(Image(inspection.image_path, width=8 * cm, height=8 * cm))
            story.append(Spacer(1, 0.5 * cm))
        except Exception:
            story.append(Paragraph("(Package image could not be embedded.)", styles["Normal"]))
            story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Extracted Declarations", styles["Heading2"]))
    decl_table_data = [["Field", "Detected Value", "Confidence"]]
    for d in declarations:
        decl_table_data.append([d.field_name, d.detected_value or "-", f"{d.confidence:.2f}"])
    decl_table = Table(decl_table_data, colWidths=[5 * cm, 8 * cm, 3 * cm])
    decl_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(decl_table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Violations", styles["Heading2"]))
    if violations:
        viol_table_data = [["Field", "Severity", "Reason", "Rule Reference"]]
        for v in violations:
            viol_table_data.append([v.field_name, v.severity, v.reason, v.rule_reference or "-"])
        viol_table = Table(viol_table_data, colWidths=[3.5 * cm, 2.5 * cm, 6 * cm, 4 * cm])
        viol_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c0392b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(viol_table)
    else:
        story.append(Paragraph("No violations detected.", styles["Normal"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Note: This report reflects automated, machine-checkable analysis only. "
        "Final legal compliance determination requires review by an authorized "
        "Legal Metrology enforcement official.",
        styles["Italic"],
    ))

    doc.build(story)
    return output_path
