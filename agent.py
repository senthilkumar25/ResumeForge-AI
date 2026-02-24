# =========================================================
# resume_agent.py (ENHANCED - NO FLOW CHANGE)
# =========================================================

import os
from pydoc import doc
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
import time
from collections import deque
from langchain_google_genai import ChatGoogleGenerativeAI
import html



# =========================================================
# LLM FACTORY (Groq + Gemini)
# =========================================================

def get_llm(provider: str, api_key: str, rpm: int, model: str):

    if not api_key:
        raise ValueError(f"{provider} API Key is required")

    limiter = APIRateLimiter(rpm)

    if provider.lower() == "groq":
        llm = ChatGroq(
            model=model,
            groq_api_key=api_key,
            temperature=0.2

        )

    elif provider.lower() == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.2
        )

    else:
        raise ValueError("Provider must be either 'groq' or 'gemini'")

    return llm, limiter


# =========================================================
# RATE LIMITER
# =========================================================

class APIRateLimiter:
    def __init__(self, rpm: int):
        self.rpm = rpm
        self.calls = deque()

    def wait_if_needed(self):
        current_time = time.time()

        # Remove old timestamps
        while self.calls and current_time - self.calls[0] > 60:
            self.calls.popleft()

        if len(self.calls) >= self.rpm:
            sleep_time = 60 - (current_time - self.calls[0])
            if sleep_time > 0:
                print(f"Rate limit reached. Sleeping for {int(sleep_time)} seconds...")
                time.sleep(sleep_time)

        self.calls.append(time.time())

# =========================================================
# STATE
# =========================================================

class ResumeState(TypedDict):
    structured_resume: Optional[Dict]
    resume_text: Optional[str]
    user_info: Optional[Dict]
    job_description: str
    ats_score: Optional[Dict]
    gap_questions: Optional[list]
    user_answers: Optional[Dict]
    provider: str
    api_key: str
    rpm: int
    model: str  

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

4. SKILLS STRUCTURE (ROLE-ADAPTIVE):

   - Detect industry/domain from Job Description.
   - Create domain-specific skill categories dynamically.
   - Examples:

        For Finance:
            "Financial Analysis": [...]
            "Accounting Tools": [...]
            "Regulatory Compliance": [...]

        For Banking:
            "Credit Risk Management": [...]
            "Core Banking Systems": [...]

        For Marketing:
            "Digital Marketing": [...]
            "Campaign Strategy": [...]

        For Tech:
            "Programming Languages": [...]
            "Cloud & DevOps": [...]

   - DO NOT force technical categories for non-tech roles.
   - Skills must align with JD industry.

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

8.EXPERIENCE BULLET RULE (CRITICAL):

    - Experience description MUST be a list of bullet points.
    - Provide 3 to 6 bullet points per role.
    - Each bullet must:
        • Start with strong action verb
        • Be 20–40 words
        • Include measurable impact if possible
    - DO NOT return paragraph descriptions.

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
      "description": [
  "Bullet 1",
  "Bullet 2",
  "Bullet 3"
     ]
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
- DO NOT use markdown formatting like **bold**, *, or backticks.
- If a section has no data, return empty list.
"""

    llm, limiter = get_llm(
    state["provider"],
    state["api_key"],
    state["rpm"],
     state["model"]
)
    print("Invoking LLM with prompt:", state["resume_text"][:500])  # Print the first 500 characters of the prompt for debugging
    limiter.wait_if_needed()
    response = llm.invoke(prompt)
    print(3,response.content)
    parsed = safe_json_parse(response.content)

    if not parsed:
        raise ValueError(
            "LLM returned invalid or truncated JSON. "
            "Increase max tokens or reduce prompt size."
        )

    state["structured_resume"] = parsed
    return state

# =========================================================
# NODE 2 — ADVANCED ATS SCORE
# =========================================================

def ats_score_node(state: ResumeState):

    resume_text = json.dumps(state["structured_resume"])
    jd_text = state["job_description"]

    llm, limiter = get_llm(
        state["provider"],
        state["api_key"],
        state["rpm"],
         state["model"]
    )

    # -------- LLM KEYWORD EXTRACTION --------
    jd_keywords, resume_keywords = extract_quality_keywords_llm(
        resume_text,
        jd_text,
        llm,
        limiter
    )

    if jd_keywords:
        keyword_score = int(
            (len(jd_keywords & resume_keywords) / len(jd_keywords)) * 100
        )
    else:
        keyword_score = 0

    # -------- QUANT SCORE --------
    quant_score = calculate_quant_score(resume_text)

    # -------- SEMANTIC RELEVANCE SCORE --------
    relevance_prompt = f"""
Rate resume relevance to JD from 0 to 100.
Return ONLY integer.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}
"""

    limiter.wait_if_needed()
    relevance_response = llm.invoke(relevance_prompt)

    try:
        relevance_score = int(re.findall(r"\d+", relevance_response.content)[0])
        relevance_score = max(0, min(100, relevance_score))
    except:
        relevance_score = 50

    # -------- FINAL WEIGHTING --------
    overall = int(
        (keyword_score * 0.4) +
        (quant_score * 0.2) +
        (relevance_score * 0.4)
    )

    state["ats_score"] = {
        "keyword_match_score": keyword_score,
        "quantification_score": quant_score,
        "semantic_relevance_score": relevance_score,
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
    llm, limiter = get_llm(
    state["provider"],
    state["api_key"],
    state["rpm"],
     state["model"]
)

    limiter.wait_if_needed()
    response = llm.invoke(prompt)
    print("Gap LLM Output:", response.content[:500])
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

    llm, limiter = get_llm(
    state["provider"],
    state["api_key"],
    state["rpm"],
     state["model"]
)

    limiter.wait_if_needed()
    response = llm.invoke(prompt)
    print(1,response.content)
    parsed = safe_json_parse(response.content)

    if not parsed:
        raise ValueError(
            "LLM returned invalid or truncated JSON. "
            "Increase max tokens or reduce prompt size."
        )

    state["structured_resume"] = parsed
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

# =========================================================
# LLM QUALITY KEYWORD EXTRACTION
# =========================================================

def extract_quality_keywords_llm(resume_text, jd_text, llm, limiter):

    prompt = f"""
You are an ATS keyword intelligence engine.

Extract ONLY high-impact technical and domain-specific keywords.

Rules:
- Extract only skill-based, tool-based, framework-based, role-based keywords.
- Ignore generic words like 'team', 'communication', 'experience'.
- Include multi-word phrases like:
  - Machine Learning
  - Credit Risk Modeling
  - Kubernetes Deployment
  - SQL Optimization

Return STRICT JSON:

{{
 "jd_keywords": [],
 "resume_keywords": []
}}

JOB DESCRIPTION:
{jd_text}

RESUME:
{resume_text}
"""

    limiter.wait_if_needed()
    response = llm.invoke(prompt)
    print(2,response.content)
    data = safe_json_parse(response.content)

    return (
        set(data.get("jd_keywords", [])),
        set(data.get("resume_keywords", []))
    )

def extract_missing_keywords(structured_resume, jd_text, provider, api_key, rpm,model):

    llm, limiter = get_llm(provider, api_key, rpm,model)

    resume_text = json.dumps(structured_resume)

    jd_keywords, resume_keywords = extract_quality_keywords_llm(
        resume_text,
        jd_text,
        llm,
        limiter
    )

    missing = list(jd_keywords - resume_keywords)

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

def initial_build(uploaded_file=None,user_info=None,job_description="", provider="groq",api_key="", rpm=30, model="openai/gpt-oss-120b"):

    resume_text = ""

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf(uploaded_file.read())
        elif uploaded_file.type == "text/plain":
            resume_text = uploaded_file.read().decode("utf-8")
    print("Extracted Resume Text:", resume_text[:500])

    resume_text = clean_text(resume_text)
    print("Extracted Resume Text:", resume_text[:500])

    result = graph_initial.invoke({
    "resume_text": resume_text,
    "user_info": user_info,
    "job_description": job_description,
    "provider": provider,
    "api_key": api_key,
    "rpm": rpm,
    "model": model
    })
    print("State_result",result["structured_resume"])


    # Additional Analysis Layer
    level, inference = generate_match_insight(result["ats_score"])
    missing = extract_missing_keywords(
    result["structured_resume"],
    job_description,
    provider,
    api_key,
    rpm,
    model
)

    result["additional_analysis"] = {
        "match_level": level,
        "inference": inference,
        "missing_keywords": missing
    }

    return result


def update_resume(    existing_resume, user_answers, job_description,provider="groq",api_key="",rpm=30,model="openai/gpt-oss-120b"):

    result = graph_update.invoke({
    "structured_resume": existing_resume,
    "user_answers": user_answers,
    "job_description": job_description,
    "provider": provider,
    "api_key": api_key,
    "rpm": rpm,
    "model": model
     })
    level, inference = generate_match_insight(result["ats_score"])
    missing = extract_missing_keywords(
    result["structured_resume"],
    job_description,
    provider,
    api_key,
    rpm,model
   )

    result["additional_analysis"] = {
        "match_level": level,
        "inference": inference,
        "missing_keywords": missing
    }

    return result


# =========================================================
# TEMPLATE + PDF SUPPORT (NEW)
# =========================================================


def sanitize_for_docx(data):
    if isinstance(data, dict):
        return {k: sanitize_for_docx(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_docx(v) for v in data]
    elif isinstance(data, str):
        return html.escape(data)
    else:
        return data

def generate_docx(structured_resume, template_name="Classic"):

    template_map = {
        "Classic": "templates/classic.docx",
        "Modern": "templates/modern.docx",
        "Minimal": "templates/minimal.docx"
    }

    template_path = template_map.get(template_name, "templates/classic.docx")

    doc = DocxTemplate(template_path)
    safe_data = sanitize_for_docx(structured_resume)
    doc.render(safe_data)
    # doc.render(structured_resume)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer


# =========================================================
# SMART PDF GENERATOR (WINDOWS + WEBSITE SUPPORT)
# =========================================================




def generate_pdf_from_docx(docx_buffer, environment="website"):

    import os
    import tempfile
    import subprocess

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        tmp_docx.write(docx_buffer.read())
        tmp_docx_path = tmp_docx.name

    pdf_path = tmp_docx_path.replace(".docx", ".pdf")

    try:

        # ======================================================
        # WEBSITE / LINUX MODE (LibreOffice)
        # ======================================================
        if environment == "website":
            try:
                subprocess.run([
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    tmp_docx_path,
                    "--outdir", os.path.dirname(tmp_docx_path)
                ], check=True)
            except FileNotFoundError:
                raise Exception(
                    "LibreOffice (soffice) not found. "
                    "Install LibreOffice or switch to Windows mode."
                )

        # ======================================================
        # WINDOWS MODE (MS Word COM)
        # ======================================================
        elif environment == "windows":
            try:
                import pythoncom
                import win32com.client

                pythoncom.CoInitialize()

                word = win32com.client.Dispatch("Word.Application")
                doc = word.Documents.Open(tmp_docx_path)
                doc.SaveAs(pdf_path, FileFormat=17)
                doc.Close()
                word.Quit()

                pythoncom.CoUninitialize()

            
            except Exception as e:
                raise Exception(
                    f"MS Word conversion failed. "
                    f"Ensure Microsoft Word is installed.\n\n{str(e)}"
                )

        else:
            raise ValueError("Invalid environment selected.")

        # ======================================================
        # READ GENERATED PDF
        # ======================================================
        if not os.path.exists(pdf_path):
            raise Exception("PDF file was not created.")

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        return pdf_bytes

    finally:
        # Always clean temp DOCX
        if os.path.exists(tmp_docx_path):
            os.remove(tmp_docx_path)

        # Clean PDF if exists
        if os.path.exists(pdf_path):
            os.remove(pdf_path)