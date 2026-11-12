import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_report(r, job_title, required):
    """Return a candidate-level PDF report as bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=45, rightMargin=45,
                            topMargin=45, bottomMargin=45)
    base = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=base["Title"], fontSize=18, alignment=0)
    h2 = ParagraphStyle("h2", parent=base["Heading2"], fontSize=12, spaceBefore=12)
    body = ParagraphStyle("b", parent=base["Normal"], fontSize=10, leading=14)

    rows = [
        ["Candidate", r["name"]],
        ["Email", r["email"]],
        ["Phone", r["phone"]],
        ["Job title", job_title],
        ["Weighted skill match", f'{r["weighted_pct"]}%'],
        ["Simple skill match", f'{r["match_pct"]}%'],
        ["Text similarity", f'{r["similarity"]}%'],
        ["Recommendation", r["recommendation"]],
        ["Scanned PDF (OCR used)", "Yes" if r.get("ocr") else "No"],
    ]
    table = Table(rows, colWidths=[150, 340])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    def joined(items):
        return escape(", ".join(items)) if items else "None"

    story = [
        Paragraph("Candidate Screening Report", title),
        Paragraph(f"Generated on {datetime.now():%Y-%m-%d %H:%M}", body),
        Spacer(1, 10), table,
        Paragraph("Required skills (from job description)", h2), Paragraph(joined(required), body),
        Paragraph("Matched skills", h2), Paragraph(joined(r["matched"]), body),
        Paragraph("Missing skills", h2), Paragraph(joined(r["missing"]), body),
        Paragraph("All skills found in resume", h2), Paragraph(joined(r["all_skills"]), body),
        Paragraph("How the score is calculated", h2),
        Paragraph("Simple match = matched skills / required skills x 100. Weighted match gives "
                  "technical skills a higher weight than soft skills. Text similarity is a TF-IDF "
                  "cosine similarity between the resume and the job description. "
                  "This report supports HR decisions and is not a final hiring decision.", body),
    ]
    doc.build(story)
    return buf.getvalue()