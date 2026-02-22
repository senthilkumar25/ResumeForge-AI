# =========================================================
# resume_agent.py (ENHANCED - NO FLOW CHANGE)
# =========================================================

import os
import re
import json
import ast
import fitz
import tempfile
from io import BytesIO
from typing import TypedDict, Optional, Dict
from dotenv import load_dotenv
from docxtpl import DocxTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
import subprocess
import tempfile

# =========================================================
# ENV + LLM
# =========================================================
def get_llm(groq_key):
    if not groq_key:
        raise ValueError("Groq API Key is required")

    return ChatGroq(
        model="openai/gpt-oss-120b",
        groq_api_key=groq_key,
        temperature=0.2
    )

# =========================================================
# STATE
# =========================================================

class ResumeState(TypedDict):
    resume_text: Optional[str]
    user_info: Optional[Dict]
    job_description: str
    structured_resume: Optional[Dict]
    ats_score: Optional[Dict]
    gap_questions: Optional[list]
    user_answers: Optional[Dict]
    groq_key: str   

# =========================================================
# UTILITIES
# =========================================================

def extract_text_from_pdf(file_bytes):
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in pdf:
        text += page.get_text()
    return text

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def safe_json_parse(text):
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except:
        try:
            return ast.literal_eval(match.group(0))
        except:
            return {}

# =========================================================
# ATS SCORING (UNCHANGED)
# =========================================================

def extract_keywords(text):
    return set(re.findall(r"\b[A-Za-z]{4,}\b", text.lower()))

def calculate_keyword_score(resume_text, jd_text):
    resume_words = extract_keywords(resume_text)
    jd_words = extract_keywords(jd_text)
    if not jd_words:
        return 0
    return int((len(resume_words & jd_words) / len(jd_words)) * 100)

def calculate_quant_score(resume_text):
    numbers = re.findall(r"\d+%|\d+\+?|\₹\d+", resume_text)
    return min(len(numbers) * 10, 100)

# =========================================================
# NODE 1 — GENERATE RESUME (UNCHANGED)
# =========================================================

def generate_resume_node(state: ResumeState):

    prompt = f"""
You are a Senior Executive Resume Strategist, ATS Optimization Expert, and Truth-Validation Auditor.

MISSION:
Create a HIGH-IMPACT, ATS-OPTIMIZED, KPI-DRIVEN resume aligned precisely with the Job Description.

CRITICAL RULES (VERY IMPORTANT):

1. STRICT NO-HALLUCINATION POLICY:
   - DO NOT invent skills, tools, certifications, projects, or achievements.
   - Only use information from:
        a) USER INFO
        b) EXISTING RESUME
   - If a JD mentions a skill NOT present in user data,
     DO NOT automatically add it.
   - Instead, ask a confirmation question in gap analysis.

2. SKILL VALIDATION:
   - Only include skills that are explicitly present in user resume or user info.
   - If unsure whether user has a skill, DO NOT include it.
   - Missing but important JD skills must be converted into questions.

3. KPI ENFORCEMENT:
   - Convert responsibilities into measurable achievements.
   - Use realistic conservative metrics.
   - Do NOT fabricate unrealistic numbers.

4. TECHNICAL SKILLS STRUCTURE:
   - Generate role-specific dynamic skill categories.
   - Use intelligent grouping.
   - Structure as key-value pairs.
   - Example:
        "technical_skills": {{
            "Programming Languages": ["Python", "SQL"],
            "Machine Learning": ["XGBoost", "Scikit-learn"]
        }}

5. PROFESSIONAL STRUCTURE:
   - Executive tone
   - ATS friendly formatting
   - Strong action verbs
   - Concise but impact-driven

6. ORDERING:
   - Skills must be ordered by JD relevance.
   - Most relevant skills appear first.

7. GAP QUESTIONS RULE:
   - Ask ONLY 5 to 10 HIGH-IMPACT questions.
   - Questions must be strategic.
   - Focus only on:
        • Missing KPIs
        • Missing leadership impact
        • Missing measurable outcomes
        • Important JD skill confirmations
        • High-value certifications or tools

   - Do NOT ask trivial questions.
   - Do NOT exceed 10 questions.
   - Minimum 5, Maximum 10.

INTERNAL STRATEGY (Do NOT output this reasoning):
1. Extract JD required skills & keywords.
2. Compare with user resume.
3. Identify confirmed skills.
4. Identify unconfirmed JD skills → convert to confirmation questions.
5. Strengthen measurable achievements.
6. Build dynamic technical skill categories.

PROJECT & OPEN SOURCE DEPTH ENFORCEMENT (CRITICAL):

For each project and open source contribution:

1. Provide 3 to 5 bullet points.
2. Each bullet must be 2 to 3 complete sentences.
3. Each bullet must clearly describe:
    • The business or technical problem
    • The solution or architecture approach
    • Technologies or frameworks used
    • The measurable or qualitative impact

4. Avoid short, generic statements such as:
    - "Built a web app."
    - "Implemented ML model."
    - "Created automation script."

5. Each bullet must demonstrate:
    - Problem-solving ability
    - Technical reasoning
    - Decision-making context
    - Engineering depth

6. Minimum 20–30 words per bullet.
7. Maximum 60 words per bullet.
8. Use strong action verbs and executive tone.
9. Do NOT fabricate metrics.
10. If insufficient information exists, expand context realistically but DO NOT invent tools or skills not mentioned in resume.

If a description is too short, expand it before returning JSON.

INPUTS:

JOB DESCRIPTION:
{state["job_description"]}

USER INFO:
{state["user_info"]}

EXISTING RESUME:
{state["resume_text"]}

RETURN STRICT JSON ONLY IN THIS FORMAT:

{{
  "name": "",
  "title": "",
  "location": "",
  "phone": "",
  "email": "",
  "linkedin": "",
  "github": "",
  "website": "",

  "summary": "",

  "experience": [
    {{
      "position": "",
      "company": "",
      "duration": "",
      "description": ""
    }}
  ],

  "education": [
    {{
      "degree": "",
      "institution": "",
      "duration": "",
      "details": ""
    }}
  ],

  "open_source": [
  {{
  "title": "",
  "description": [
    "Bullet 1",
    "Bullet 2"
  ],
  "link": ""
}}],

"projects": [
  {{
    "title": "",
    "description": [
      "Bullet 1",
      "Bullet 2",
      "Bullet 3"
    ] }}
],

  "technical_skills": {{
    "Dynamic Skill Category": ["skill1", "skill2"]
  }},

  "certifications": [],

  "gap_questions": []
}}

STRICT REQUIREMENTS:

- Return ONLY valid JSON.
- Do NOT include explanations.
- Do NOT include markdown.
- Do NOT include commentary.
- If a section has no data, return empty list.
"""

    llm = get_llm(state["groq_key"]) 
    response = llm.invoke(prompt)
    state["structured_resume"] = safe_json_parse(response.content)
    return state

# =========================================================
# NODE 2 — ATS SCORE (UNCHANGED)
# =========================================================

def ats_score_node(state: ResumeState):

    resume_text = json.dumps(state["structured_resume"])
    jd_text = state["job_description"]

    keyword_score = calculate_keyword_score(resume_text, jd_text)
    quant_score = calculate_quant_score(resume_text)
    overall = int((keyword_score * 0.6) + (quant_score * 0.4))

    state["ats_score"] = {
        "keyword_match_score": keyword_score,
        "quantification_score": quant_score,
        "overall_ats_score": overall
    }

    return state

# =========================================================
# NODE 3 & 4 (UNCHANGED)
# =========================================================

def gap_analysis_node(state: ResumeState):
    prompt = f"""
You are an ATS Resume Intelligence Auditor and Truth Validator.

GOAL:
Ask 5 to 10 high-impact, strategic questions to improve ATS score.

RULES:

1. Ask ONLY between 5 and 10 questions.
2. Prioritize:
   - Missing measurable KPIs
   - Missing leadership signals
   - Confirmation of important JD skills
   - Certifications that improve ranking
   - Quantification gaps
3. If JD mentions a skill NOT present in resume,
   ask confirmation question:
   Example:
   "Do you have experience with Kubernetes? If yes, describe usage."

4. DO NOT:
   - Invent missing information
   - Ask trivial questions
   - Exceed 10 questions
   - Ask vague questions

Resume:
{state["structured_resume"]}

Job Description:
{state["job_description"]}

Return STRICT JSON:

{{ "questions": [] }}
"""
    llm = get_llm(state["groq_key"]) 
    response = llm.invoke(prompt)
    data = safe_json_parse(response.content)
    state["gap_questions"] = data.get("questions", [])
    return state


def update_resume_node(state: ResumeState):

    prompt = f"""
You are an Elite Resume Optimization Specialist.

Enhance the resume using user answers.

JOB DESCRIPTION:
{state["job_description"]}

CURRENT RESUME:
{state["structured_resume"]}

USER ANSWERS:
{state["user_answers"]}

Return STRICT JSON only.
"""

    llm = get_llm(state["groq_key"]) 
    response = llm.invoke(prompt)
    state["structured_resume"] = safe_json_parse(response.content)
    return state

# =========================================================
# GRAPHS (UNCHANGED)
# =========================================================

builder1 = StateGraph(ResumeState)
builder1.add_node("generate_resume", generate_resume_node)
builder1.add_node("ats_score", ats_score_node)
builder1.add_node("gap_analysis", gap_analysis_node)

builder1.set_entry_point("generate_resume")
builder1.add_edge("generate_resume", "ats_score")
builder1.add_edge("ats_score", "gap_analysis")
builder1.add_edge("gap_analysis", END)

graph_initial = builder1.compile()

builder2 = StateGraph(ResumeState)
builder2.add_node("update_resume", update_resume_node)
builder2.add_node("ats_score", ats_score_node)

builder2.set_entry_point("update_resume")
builder2.add_edge("update_resume", "ats_score")
builder2.add_edge("ats_score", END)

graph_update = builder2.compile()

# =========================================================
# ADDITIONAL ANALYSIS (NEW FEATURE)
# =========================================================

def extract_missing_keywords(structured_resume, jd_text):

    resume_text = json.dumps(structured_resume).lower()
    jd_words = set(re.findall(r"\b[A-Za-z]{4,}\b", jd_text.lower()))
    resume_words = set(re.findall(r"\b[A-Za-z]{4,}\b", resume_text))

    generic = {"with", "have", "from", "this", "that", "will", "able"}
    missing = [w for w in jd_words - resume_words if w not in generic]

    return missing[:15]


def generate_match_insight(ats_score):

    overall = ats_score["overall_ats_score"]

    if overall >= 80:
        return "Highly Reliable Match", "Your qualifications strongly align with the JD. High shortlisting probability."
    elif overall >= 65:
        return "Strong Match", "Most JD requirements are covered, but KPI/keyword optimization can improve ranking."
    elif overall >= 50:
        return "Moderate Match", "Several requirements are matched, but noticeable skill gaps exist."
    elif overall >= 35:
        return "Partial Match", "Your experience partially overlaps with job expectations."
    else:
        return "Totally Contrast", "Your profile significantly differs from the JD expectations."

# =========================================================
# PUBLIC FUNCTIONS (ENHANCED)
# =========================================================

def initial_build(uploaded_file=None, user_info=None, job_description="", groq_key=""):

    resume_text = ""

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf(uploaded_file.read())
        elif uploaded_file.type == "text/plain":
            resume_text = uploaded_file.read().decode("utf-8")

    resume_text = clean_text(resume_text)

    result = graph_initial.invoke({
    "resume_text": resume_text,
    "user_info": user_info,
    "job_description": job_description,
    "groq_key": groq_key
     })

    # Additional Analysis Layer
    level, inference = generate_match_insight(result["ats_score"])
    missing = extract_missing_keywords(result["structured_resume"], job_description)

    result["additional_analysis"] = {
        "match_level": level,
        "inference": inference,
        "missing_keywords": missing
    }

    return result


def update_resume(existing_resume, user_answers, job_description,groq_key):

    result = graph_update.invoke({
        "structured_resume": existing_resume,
        "user_answers": user_answers,
        "job_description": job_description,
        "groq_key": groq_key 
    })
    level, inference = generate_match_insight(result["ats_score"])
    missing = extract_missing_keywords(result["structured_resume"], job_description)

    result["additional_analysis"] = {
        "match_level": level,
        "inference": inference,
        "missing_keywords": missing
    }

    return result


# =========================================================
# TEMPLATE + PDF SUPPORT (NEW)
# =========================================================

def generate_docx(structured_resume, template_name="Classic"):

    template_map = {
        "Classic": "templates/classic.docx",
        "Modern": "templates/modern.docx",
        "Minimal": "templates/minimal.docx"
    }

    template_path = template_map.get(template_name, "templates/classic.docx")

    doc = DocxTemplate(template_path)
    doc.render(structured_resume)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer


def generate_pdf_from_docx(docx_buffer):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        tmp_docx.write(docx_buffer.read())
        tmp_docx_path = tmp_docx.name

    # Convert DOCX to PDF using LibreOffice (Linux safe)
    subprocess.run([
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        tmp_docx_path,
        "--outdir", os.path.dirname(tmp_docx_path)
    ], check=True)

    pdf_path = tmp_docx_path.replace(".docx", ".pdf")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    os.remove(tmp_docx_path)
    os.remove(pdf_path)

    return pdf_bytes


