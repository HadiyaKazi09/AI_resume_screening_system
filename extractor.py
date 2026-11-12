import os
import re

import pdfplumber
from docx import Document

# ---- OCR setup (optional) ----
try:
    import pytesseract

    for _p in (r"C:\Program Files\Tesseract-OCR\tesseract.exe",
               r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
        if os.path.exists(_p):
            pytesseract.pytesseract.tesseract_cmd = _p
            break
    pytesseract.get_tesseract_version()
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

EMAIL_RE = re.compile(r"[\w\.\-+]+@[\w\.\-]+\.\w+")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-()]{8,}\d)")


def _docx_text(file):
    """Read paragraphs and tables from a Word (.docx) resume."""
    doc = Document(file)
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def _pdf_text(file):
    pages, ocr_used = [], False
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) < 30 and OCR_AVAILABLE:
                try:
                    image = page.to_image(resolution=200).original
                    text = pytesseract.image_to_string(image)
                    ocr_used = True
                except Exception:
                    text = ""
            pages.append(text)
    return "\n".join(pages), ocr_used


def extract_text(file):
    """Return (text, ocr_used) for a PDF or DOCX resume."""
    name = getattr(file, "name", "").lower()
    if name.endswith(".docx"):
        try:
            return _docx_text(file), False
        except Exception:
            return "", False
    return _pdf_text(file)


def extract_email(text):
    match = EMAIL_RE.search(text)
    return match.group() if match else "Not found"


def extract_phone(text):
    for match in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if 10 <= len(digits) <= 13:
            return match.group().strip()
    return "Not found"


def extract_name(text, filename):
    """Guess the name from the first few lines; fall back to the file name."""
    skip = {"resume", "curriculum", "vitae", "cv", "profile"}
    for line in text.splitlines()[:6]:
        line = line.strip()
        words = line.split()
        if 1 < len(words) <= 4 and all(w.replace(".", "").isalpha() for w in words):
            if not skip & {w.lower() for w in words}:
                return line.title()
    return filename.rsplit(".", 1)[0]