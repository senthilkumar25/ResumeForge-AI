import streamlit as st
import json
from agent import (
    initial_build,
    update_resume,
    generate_docx,
    generate_pdf_from_docx
)

st.set_page_config(layout="wide")
st.title("🚀 AI Resume Builder (Interactive ATS Optimizer Pro)")

# ======================================================
# SESSION STATE
# ======================================================

def init_session():
    defaults = {
        "resume_data": None,
        "questions": None,
        "ats_score": None,
        "ats_score_before": None,
        "additional_analysis": None,
        "job_description": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ======================================================
# RESET BUTTON
# ======================================================

if st.sidebar.button("🔄 Reset Session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ======================================================
# INPUT SECTION
# ======================================================

st.sidebar.header("📌 Candidate Information")

uploaded_resume = st.sidebar.file_uploader("Upload Resume", type=["pdf", "txt"])

# ======================================================
# LLM CONFIGURATION
# ======================================================

st.sidebar.header("🤖 LLM Configuration")

provider = st.sidebar.selectbox(
    "Select LLM Provider",
    ["Groq", "Gemini"]
)
# -------------------------
# MODEL LIST PER PROVIDER
# -------------------------

groq_models =["openai/gpt-oss-120b","whisper-large-v3-turbo","whisper-large-v3-turbo","llama-3.3-70b-versatile","Other"]

gemini_models = ["gemini-2.5-flash","gemini-3-flash-preview","gemini-2.5-flash-lite","gemma-3-27b-it","Other"]
if provider == "Groq":
    model_choice = st.sidebar.selectbox(
        "Select Groq Model",
        groq_models
    )
else:
    model_choice = st.sidebar.selectbox(
        "Select Gemini Model",
        gemini_models
    )

# If user selects "Other"
if model_choice == "Other":
    custom_model = st.sidebar.text_input(
        "Enter Custom Model Name"
    )
    selected_model = custom_model
else:
    selected_model = model_choice

st.sidebar.caption("⚠ Larger models support longer resumes and reduce JSON truncation risk.")

api_key = st.sidebar.text_input(
    f"Enter {provider} API Key",
    type="password"
)

rpm = st.sidebar.number_input(
    "Requests Per Minute (RPM Limit)",
    min_value=1,
    max_value=60,
    value=5 if provider == "Gemini" else 30
)

name = st.sidebar.text_input("Name")
email = st.sidebar.text_input("Email")
phone = st.sidebar.text_input("Phone")
summary = st.sidebar.text_area("Professional Summary")
skills = st.sidebar.text_area(
    "Core Skills / Functional Skills (comma separated)",
    help="Example: Financial Modeling, Risk Analysis, Python, CRM, SAP, Taxation, etc."
)
education = st.sidebar.text_area("Education")
projects = st.sidebar.text_area("Projects")

st.header("📄 Job Description")
job_description = st.text_area("Paste Job Description", height=200)
st.session_state.job_description = job_description

template_choice = st.selectbox(
    "Select Resume Template",
    ["Classic", "Modern", "Minimal"]
)
# ======================================================
# PDF ENVIRONMENT CONFIG
# ======================================================

st.sidebar.header("📄 PDF Generation Mode")

environment = st.sidebar.selectbox(
    "Select Runtime Environment",
    ["Windows (Local Machine)", "Website (Linux/Cloud)"]
)

if environment.startswith("Windows"):
    runtime_env = "windows"
else:
    runtime_env = "website"
# ======================================================
# GENERATE RESUME
# ======================================================

if not job_description:
    st.warning("Please paste Job Description before generating.")


if st.button("🚀 Generate Optimized Resume"):
   with st.spinner("Analyzing JD and Optimizing Resume..."):

        user_info = {
            "name": name,
            "email": email,
            "phone": phone,
            "summary": summary,
            "skills": skills,
            "education": education,
            "projects": projects
        }

        result = initial_build(uploaded_resume,user_info,job_description, provider.lower(),api_key,rpm,selected_model)

        st.session_state.resume_data = result["structured_resume"]
        st.session_state.questions = result["gap_questions"]
        st.session_state.ats_score = result["ats_score"]
        st.session_state.additional_analysis = result.get("additional_analysis")

# ======================================================
# ATS SCORE VISUALIZATION
# ======================================================

def score_color(score):
    if score >= 80:
        return "green"
    elif score >= 65:
        return "orange"
    else:
        return "red"

if st.session_state.ats_score:

    st.subheader("📊 ATS Performance Dashboard")

    overall = st.session_state.ats_score["overall_ats_score"]
    keyword = st.session_state.ats_score["keyword_match_score"]
    quant = st.session_state.ats_score["quantification_score"]
    semantic = st.session_state.ats_score.get("semantic_relevance_score", 0)


    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Overall ATS Score", overall)
    col2.metric("Keyword Match", keyword)
    col3.metric("Quantification", quant)
    col4.metric("Semantic Relevance", semantic)

    st.progress(overall / 100)

# ======================================================
# INTELLIGENCE SECTION
# ======================================================

if st.session_state.additional_analysis:

    analysis = st.session_state.additional_analysis

    st.subheader("🎯 JD Alignment Intelligence")

    st.success(f"Match Level: {analysis['match_level']}")
    st.info(analysis["inference"])

    if analysis["missing_keywords"]:
        st.warning("High-Impact Missing Skills From JD")

        for skill in analysis["missing_keywords"]:
            st.markdown(f"- 🔹 {skill}")
    else:
        st.success("No major JD keywords missing.")

# ======================================================
# GAP QUESTIONS
# ======================================================

if st.session_state.questions:

    st.subheader("📌 Improve Your Resume Further")

    answers = {}
    for q in st.session_state.questions:
        answers[q] = st.text_input(q)

    if st.button("✨ Apply Improvements"):

        st.session_state.ats_score_before = st.session_state.ats_score

        with st.spinner("Enhancing resume..."):

            updated = update_resume(st.session_state.resume_data,answers,st.session_state.job_description,provider.lower(), api_key,rpm,selected_model)
            st.session_state.resume_data = updated["structured_resume"]
            st.session_state.ats_score = updated["ats_score"]
            st.session_state.additional_analysis = updated.get("additional_analysis")

        st.success("Resume Updated Successfully!")

# ======================================================
# BEFORE VS AFTER
# ======================================================

if st.session_state.ats_score_before and st.session_state.ats_score:

    st.subheader("📈 ATS Improvement Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Before",
            st.session_state.ats_score_before["overall_ats_score"]
        )

    with col2:
        st.metric(
            "After",
            st.session_state.ats_score["overall_ats_score"]
        )

# ======================================================
# STRUCTURED RESUME PREVIEW + EDIT
# ======================================================

if st.session_state.resume_data is not None:

    st.subheader("📄 Structured Resume Editor")

    edited_json = st.text_area(
        "Edit JSON if needed",
        json.dumps(st.session_state.resume_data, indent=2),
        height=400
    )

    if st.button("🔁 Recalculate ATS Score"):
        try:
            updated_resume = json.loads(edited_json)
            st.session_state.resume_data = updated_resume

            updated = update_resume(updated_resume, {}, st.session_state.job_description,provider.lower(),api_key,rpm,selected_model)

            st.session_state.ats_score = updated["ats_score"]
            st.success("ATS Recalculated Successfully!")

        except:
            st.error("Invalid JSON format.")

# ======================================================
# DOWNLOAD SECTION
# ======================================================

if st.session_state.resume_data is not None:

    st.subheader("⬇ Download Final Resume")

    if st.button("Confirm & Generate Files"):

        with st.spinner("Generating files..."):

            doc_file = generate_docx(
                st.session_state.resume_data,
                template_choice
            )

            pdf_file = generate_pdf_from_docx(doc_file, runtime_env)

        st.download_button(
            "Download DOCX",
            data=doc_file,
            file_name="Final_ATS_Resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        st.download_button(
            "Download PDF",
            data=pdf_file,
            file_name="Final_ATS_Resume.pdf",
            mime="application/pdf"
        )