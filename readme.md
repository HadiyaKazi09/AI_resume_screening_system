# AI-Based Resume Screening and Candidate Skill-Matching System

An NLP-based tool that helps HR screen resumes. It reads PDF and Word resumes,
compares each candidate's skills with a job description, and ranks candidates
by skill match.

## Features
- Load resumes from a folder, a ZIP file or a normal upload (PDF and DOCX)
- Skill extraction with spaCy PhraseMatcher, with skill aliases
- Simple match %, weighted match % and TF-IDF text similarity
- Ranking table, chart, matched and missing skills
- PDF report for each candidate, CSV export, SQLite history
- Optional OCR for scanned PDFs (needs Tesseract)

## Tech stack
Python, Streamlit, spaCy, scikit-learn, pdfplumber, python-docx, SQLite, ReportLab, Plotly

## How to run
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

## Project structure
- `app.py`: web interface and dashboard
- `loader.py`: folder, ZIP and upload loading
- `extractor.py`: text extraction, OCR, contact details
- `skills.py`: skill extraction
- `matcher.py`: scoring
- `database.py`: SQLite storage
- `report.py`: candidate PDF report
- `skills_list.csv`: skill dictionary

Author: Hadiya Kazi (MCA, REVA University), CynuxEra internship project