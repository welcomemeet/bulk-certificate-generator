from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def safe_filename(value: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in " -_" else "_" for c in value)
    return "_".join(cleaned.split())


def generate_certificate(
    output_path: Path,
    recipient_name: str,
    course_name: str,
    event_name: str,
    issuer_name: str,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(output_path), pagesize=landscape(A4))
    width, height = landscape(A4)

    # Single predefined certificate design.
    pdf.setLineWidth(3)
    pdf.rect(15 * mm, 15 * mm, width - 30 * mm, height - 30 * mm)
    pdf.setLineWidth(1)
    pdf.rect(20 * mm, 20 * mm, width - 40 * mm, height - 40 * mm)

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 55 * mm, "CERTIFICATE OF COMPLETION")

    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(width / 2, height - 75 * mm, "This certificate is proudly presented to")

    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(width / 2, height - 95 * mm, recipient_name)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2,
        height - 115 * mm,
        f"for successfully completing: {course_name}",
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        width / 2,
        height - 132 * mm,
        f"Event: {event_name}",
    )

    pdf.line(55 * mm, 42 * mm, 115 * mm, 42 * mm)
    pdf.line(width - 115 * mm, 42 * mm, width - 55 * mm, 42 * mm)

    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(85 * mm, 35 * mm, issuer_name)
    pdf.drawCentredString(width - 85 * mm, 35 * mm, "Authorized Signature")

    pdf.showPage()
    pdf.save()

    return output_path
