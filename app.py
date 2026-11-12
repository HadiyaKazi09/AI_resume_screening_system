import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from extractor import OCR_AVAILABLE, extract_email, extract_name, extract_phone, extract_text
from loader import browse_folder, files_from_folder, files_from_zip
from matcher import match_skills, recommendation, text_similarity, weighted_match
from report import build_report
from skills import extract_skills, skill_type

st.set_page_config(page_title="AI Resume Screening", layout="wide")
db.init_db()

# ------------------------------------------------------------------ Sidebar
st.sidebar.header("Settings")
tech_w = st.sidebar.slider("Technical skill weight", 1, 5, 3)
soft_w = st.sidebar.slider("Soft skill weight", 1, 5, 1)
min_match = st.sidebar.slider("Show candidates with weighted match % of at least", 0, 100, 0)
st.sidebar.caption("Weights are applied when you click 'Screen Candidates'.")
if OCR_AVAILABLE:
    st.sidebar.success("OCR enabled: scanned PDFs are supported")
else:
    st.sidebar.warning("OCR not installed: scanned PDFs will be skipped")


def weight_of(skill):
    return soft_w if skill_type(skill) == "soft" else tech_w


def pick_folder():
    chosen = browse_folder()
    if chosen:
        st.session_state["folder_path"] = chosen


st.title("AI-Based Resume Screening System")
tab_screen, tab_history = st.tabs(["Screen Resumes", "History"])

# ---------------------------------------------------------------- Screen tab
with tab_screen:
    job_title = st.text_input("Job title", "Python Developer")
    job_desc = st.text_area("Paste the job description", height=200)

    mode = st.radio("How do you want to add resumes?",
                    ["Select a folder", "Upload ZIP file", "Upload PDF/DOCX files"], horizontal=True)
    files = []

    if mode == "Select a folder":
        col_path, col_btn = st.columns([5, 1])
        with col_path:
            st.text_input("Folder path (all PDF and Word resumes inside will be screened)",
                          key="folder_path", placeholder=r"C:\project\sample_resumes")
        with col_btn:
            st.write("")
            st.write("")
            st.button("Browse...", on_click=pick_folder)
        include_sub = st.checkbox("Include sub-folders")
        folder = st.session_state.get("folder_path", "").strip()
        if folder:
            try:
                files = files_from_folder(folder, include_sub)
                st.success(f"{len(files)} resume file(s) found in this folder.")
            except Exception as e:
                st.error(str(e))
    elif mode == "Upload ZIP file":
        zip_file = st.file_uploader("Upload a ZIP file containing resumes (PDF or DOCX)", type="zip")
        if zip_file:
            files = files_from_zip(zip_file)
            st.success(f"{len(files)} resume file(s) found in the ZIP.")
    else:
        files = st.file_uploader("Upload resumes (PDF or DOCX)", type=["pdf", "docx"],
                                 accept_multiple_files=True)

    max_files = int(st.number_input("Maximum number of resumes to screen", 1, 1000, 50))
    if len(files) > max_files:
        st.info(f"{len(files)} files found. Only the first {max_files} will be screened.")
        files = files[:max_files]

    if files:
        with st.expander(f"Show the {len(files)} file(s) to be screened"):
            st.write([f.name for f in files])

    if st.button("Screen Candidates", type="primary"):
        if not job_desc.strip() or not files:
            st.warning("Please enter a job description and add at least one resume.")
        else:
            required = extract_skills(job_desc)
            if not required:
                st.error("No known skills found in the job description. Add skills to skills_list.csv.")
            else:
                results = []
                progress = st.progress(0, text="Screening resumes...")
                for i, f in enumerate(files, start=1):
                    progress.progress(i / len(files), text=f"Screening {i} of {len(files)}: {f.name}")
                    text, ocr_used = extract_text(f)
                    if not text.strip():
                        st.warning(f"{f.name}: no text found (scanned file without OCR, or empty). Skipped.")
                        continue
                    candidate_skills = extract_skills(text)
                    matched, missing, simple_pct = match_skills(required, candidate_skills)
                    w_pct = weighted_match(required, matched, weight_of)
                    result = {
                        "file": f.name,
                        "name": extract_name(text, f.name),
                        "email": extract_email(text),
                        "phone": extract_phone(text),
                        "all_skills": candidate_skills,
                        "matched": matched,
                        "missing": missing,
                        "match_pct": simple_pct,
                        "weighted_pct": w_pct,
                        "similarity": text_similarity(text, job_desc),
                        "recommendation": recommendation(w_pct),
                        "ocr": ocr_used,
                    }
                    results.append(result)
                    db.save_result(job_title, result)
                progress.empty()

                # unique labels even if two files belong to the same person
                names = [r["name"] for r in results]
                for r in results:
                    r["label"] = r["name"] if names.count(r["name"]) == 1 else f'{r["name"]} ({r["file"]})'

                st.session_state["results"] = results
                st.session_state["required"] = required
                st.session_state["job_title"] = job_title

    if st.session_state.get("results"):
        required = st.session_state["required"]
        saved_title = st.session_state["job_title"]
        ranked = sorted(
            [r for r in st.session_state["results"] if r["weighted_pct"] >= min_match],
            key=lambda r: r["weighted_pct"], reverse=True,
        )

        st.subheader("Required skills")
        st.write(", ".join(f"{s} ({skill_type(s)})" for s in required))

        if not ranked:
            st.info("No candidates meet the minimum match % set in the sidebar.")
        else:
            df = pd.DataFrame(
                [
                    {
                        "Candidate": r["label"],
                        "Name": r["name"],
                        "File": r["file"],
                        "Email": r["email"],
                        "Phone": r["phone"],
                        "Weighted Match %": r["weighted_pct"],
                        "Simple Match %": r["match_pct"],
                        "Text Similarity %": r["similarity"],
                        "Matched": len(r["matched"]),
                        "Missing": len(r["missing"]),
                        "Recommendation": r["recommendation"],
                        "Scanned (OCR)": "Yes" if r["ocr"] else "No",
                    }
                    for r in ranked
                ]
            )
            df.index = df.index + 1

            st.subheader(f"Candidate ranking ({len(df)} candidates)")
            st.dataframe(df.drop(columns=["Candidate"]), width="stretch")

            fig = px.bar(
                df.head(15), x="Candidate", y="Weighted Match %", range_y=[0, 100],
                text="Weighted Match %", color="Recommendation",
                color_discrete_map={"Strong fit": "#2ecc71", "Moderate fit": "#f1c40f",
                                    "Low fit": "#e74c3c"},
                title="Top candidates by weighted skill match (top 15 shown)",
            )
            st.plotly_chart(fig, width="stretch")

            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button("Download ranking (CSV)",
                                   df.drop(columns=["Candidate"]).to_csv(index=False),
                                   file_name="screening_report.csv", mime="text/csv")
            with col_b:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as zf:
                    for r in ranked[:20]:
                        safe = r["label"].replace(" ", "_").replace("/", "_")
                        zf.writestr(f"report_{safe}.pdf", build_report(r, saved_title, required))
                st.download_button("Download reports of top 20 candidates (ZIP)", zip_buf.getvalue(),
                                   file_name="candidate_reports.zip", mime="application/zip")

            st.subheader("Candidate details")
            choice = st.selectbox("Select a candidate", [r["label"] for r in ranked])
            r = next(x for x in ranked if x["label"] == choice)

            m1, m2, m3 = st.columns(3)
            m1.metric("Weighted match", f'{r["weighted_pct"]}%')
            m2.metric("Simple match", f'{r["match_pct"]}%')
            m3.metric("Recommendation", r["recommendation"])

            col1, col2 = st.columns(2)
            with col1:
                st.success("Matched skills: " + (", ".join(r["matched"]) or "None"))
            with col2:
                st.error("Missing skills: " + (", ".join(r["missing"]) or "None"))
            st.info("All skills found in resume: " + (", ".join(r["all_skills"]) or "None"))

            st.download_button(
                "Download this candidate's report (PDF)",
                build_report(r, saved_title, required),
                file_name=f"report_{r['name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
            )

# --------------------------------------------------------------- History tab
with tab_history:
    st.subheader("Previous screenings")
    history = db.load_results()
    if history.empty:
        st.write("No screenings saved yet.")
    else:
        st.dataframe(history, width="stretch")