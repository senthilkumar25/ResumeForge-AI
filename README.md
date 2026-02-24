🚀 ResumeForge AI
Intelligent ATS Optimization Engine
<p align="center">  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" /> <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" /> <img src="https://img.shields.io/badge/Streamlit-App-ff4b4b?style=for-the-badge&logo=streamlit" /> <img src="https://img.shields.io/badge/LangGraph-Agentic-purple?style=for-the-badge" /> <img src="https://img.shields.io/badge/LLM-Groq%20%7C%20Gemini-orange?style=for-the-badge" /> </p> <p align="center"> <b>Agentic Resume Intelligence powered by Hybrid ATS Scoring & Semantic Alignment</b> </p>
🧠 Overview

ResumeForge AI is a full-stack, LLM-powered resume optimization system designed to maximize Applicant Tracking System (ATS) compatibility using structured validation, semantic reasoning, and hybrid scoring intelligence.

Unlike traditional resume builders that rely on keyword stuffing, ResumeForge AI treats resume optimization as an agentic workflow, ensuring:

📊 Measurable impact enforcement

🔎 Context-aware job alignment

⚖️ Balanced keyword + semantic scoring

🔁 Iterative improvement with score tracking

It doesn’t just rewrite resumes — it analyzes, scores, identifies skill gaps, and continuously refines alignment with job descriptions.

✨ Core Capabilities
🎯 Hybrid ATS Scoring Engine

A multi-dimensional scoring framework combining:

🔑 Keyword Match Score – High-impact skill overlap

📈 Quantification Score – Detection of measurable outcomes

🧠 Semantic Relevance Score – LLM-based contextual alignment

⚠️ Missing Skill Detection – Gap analysis against JD

Overall ATS Score =
(Keyword × 0.4) +
(Quantification × 0.2) +
(Semantic × 0.4)

This ensures resumes are optimized both syntactically (keywords) and semantically (context).

🔄 Agentic Optimization Workflow (LangGraph)

ResumeForge AI is built as a deterministic state machine:

1️⃣ Generate Structured Resume
2️⃣ Compute ATS Score
3️⃣ Identify Missing High-Impact Skills
4️⃣ Generate Strategic Gap Questions
5️⃣ Apply Improvements
6️⃣ Re-score & Compare Before/After

This creates a feedback-driven optimization loop.

🧠 Intelligent Resume Structuring

Converts unstructured PDF/TXT resumes into structured JSON

Enforces strict no-hallucination policy

Removes markdown noise and formatting artifacts

Validates schema before scoring

🌍 Multi-LLM Architecture

Supports multiple providers:

🟠 Groq (Llama 3 / GPT-OSS models)

🔵 Google Gemini

Includes:

Dynamic provider switching

RPM-based rate limiting

Clean abstraction layer

🖥️ Cross-Platform PDF Engine

Built for both local and cloud environments:

🪟 Windows → MS Word (docx2pdf)

☁️ Cloud → Pure Python (ReportLab fallback)

🛡️ Automatic fail-safe conversion

No environment lock-in.

🏗️ Architecture
Layer	Technology
🎨 Frontend	Streamlit
🧠 Orchestration	LangChain + LangGraph
🤖 LLM Providers	Groq / Gemini
📄 Resume Parsing	PyMuPDF
📦 PDF Engine	docx2pdf + ReportLab
🔍 Validation	Regex + JSON sanitation

The system treats resume optimization as a structured state transition graph rather than a single LLM call.

🎯 Designed For

ResumeForge AI dynamically adapts skill categorization based on Job Description context and supports:

👨‍💻 Developers

📊 Data Scientists

💼 Accountants

🏦 Banking & Finance Professionals

📈 Marketing & Sales

🧑‍💼 HR & Operations

🎓 MBA Graduates & Freshers

⚡ Quick Start
1️⃣ Clone Repository
git clone https://github.com/your-username/ResumeForge-AI.git
cd ResumeForge-AI
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Configure API Keys
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
4️⃣ Run Application
streamlit run app.py
🚀 Why ResumeForge AI?

Most resume tools:

Insert buzzwords

Inflate metrics

Ignore contextual alignment

ResumeForge AI enforces:

✔ Truth validation
✔ Quantified achievements
✔ Context-aware semantic scoring
✔ Iterative optimization
✔ Structured ATS intelligence

It is built not as a resume writer — but as a resume intelligence engine.

Website: https://resume-deep-ai-agent.onrender.com/
