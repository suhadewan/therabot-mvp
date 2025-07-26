Rapid-Build Specification — Option 1: Streamlit + OpenAI Chatbot MVP

(Target: functional public web app in ≤ 3 h)

⸻

1 . Objective

Deploy a mental-health support chatbot (non-clinical, youth focus) at a public URL with zero infra maintenance, using Streamlit Community Cloud and the OpenAI Chat Completions API.

⸻

2 . Deliverables

#	Deliverable	Acceptance Criteria
D1	GitHub repo mental-health-bot-mvp	Contains all code, docs, and CI badge; runs pytest and flake8 clean locally.
D2	Public Streamlit URL	Loads in <3 s on average; banner disclaimer visible; chat works end-to-end.
D3	README.md	“One-command” local run + deploy steps; env vars listed.
D4	System prompt file system_prompt.txt	Matches lines 21-41 of the PDF (verbatim).
D5	Content-style guard rules in guardrails.py	Enforce ≤ 50 words, 2-3 sentences, follow-up question.
D6	Security & Moderation middleware	Rejects or flags content that trips OpenAI Moderation API.
D7	CI/CD	GitHub Action: lint → unit tests → auto-deploy to Streamlit.


⸻

3 . Stack & Services

Layer	Tech / Service	Rationale
Front-end + UI	Streamlit (v1.35 +)	Python-native, instant hosting, built-in session state.
LLM API	OpenAI gpt-4o-mini	Fast & low-cost; can switch model id via env var.
Storage (opt)	Streamlit st.session_state (in-memory)	No DB needed for MVP; add Supabase later.
CI/CD	GitHub Actions + Streamlit Cloud	Free and frictionless.
Testing	pytest, pytest-asyncio	Basic unit tests for helper functions.
Code quality	flake8, black, isort	Consistent style.
Secrets	Streamlit Secrets / GitHub Encrypted Secrets	No keys in code.


⸻

4 . Functional Requirements
	1.	Chat Interface
	•	Single-column chat (Streamlit st.chat_input, st.chat_message).
	•	Scrollback preserved per session.
	2.	LLM Call Flow

[system prompt] + [previous messages] + user input ─► OpenAI
◄── assistant response (streamed) ─► UI


	3.	Style Guardrails — every assistant message:
	•	≤ 50 words, max 3 sentences.
	•	Ends with one follow-up question.
	•	If violation detected, regenerate once with lower temperature.
	4.	Safety Banner — top of page:
“⚠️ This tool is not medical advice. If you need immediate help call 1098 or a licensed professional.”
	5.	Rate Limiting
	•	Max 20 requests / IP / hr (simple in-memory counter).

⸻

5 . Non-Functional Requirements

Aspect	Target
Latency	<2 s model latency 95p for ≤ 200 tokens.
Availability	≥99 % (leverages Streamlit Cloud SLA).
Cost	<$10 per 1 000 chats at 120 tokens avg.
Security	No PII stored; HTTPS enforced; keys kept out of repo.
Maintainability	Functions ≤50 LOC; docstrings + type hints.
Accessibility	Meets WCAG AA; all text selectable, high contrast.


⸻

6 . Architecture & File Layout

mental-health-bot-mvp/
├── app.py               # Streamlit entry-point
├── system_prompt.txt    # PDF lines 21-41
├── guardrails.py        # length & style enforcement
├── moderation.py        # wrapper for OpenAI Moderation API
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example
├── tests/
│   └── test_guardrails.py
├── .github/
│   └── workflows/ci.yml
└── README.md

app.py (key modules)

from guardrails import enforce_style
from moderation import safe_to_send
import streamlit as st, openai, os

openai.api_key = os.getenv("OPENAI_API_KEY")
SYSTEM_PROMPT = open("system_prompt.txt").read()

if "history" not in st.session_state:
    st.session_state.history = [{"role":"system","content":SYSTEM_PROMPT}]

st.title("Youth Support Chatbot 🇮🇳")
user_msg = st.chat_input("Type here…")

if user_msg and safe_to_send(user_msg):
    st.session_state.history.append({"role":"user","content":user_msg})
    with st.chat_message("assistant"):
        resp = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
            messages=st.session_state.history,
            stream=True,
            temperature=0.7,
            max_tokens=120,
        )
        answer = "".join(chunk.choices[0].delta.get("content","") for chunk in resp)
        answer = enforce_style(answer)
        st.write(answer)
    st.session_state.history.append({"role":"assistant","content":answer})


⸻

7 . Task Breakdown & Time-box

Task	Owner	Est.	Notes
T1	Repo scaffold & virtualenv	10 min	
T2	Implement app.py basic chat	20 min	
T3	Write guardrails.py and tests	25 min	
T4	Add moderation wrapper	10 min	
T5	Banner & rate limit	10 min	
T6	Manual smoke test	10 min	
T7	Prepare requirements.txt, README.md	10 min	
T8	GitHub Action CI (lint + tests)	15 min	
T9	Create Streamlit app & secrets	10 min	Build time ~10 min (parallel).

Total ≈ 2 h — buffer 1 h for bug-fix and model quota issues.

⸻

8 . Security & Compliance Notes
	•	Secrets: Use .streamlit/secrets.toml locally; Streamlit Cloud’s Secret Manager in prod.
	•	Data retention: No logs persisted yet; add explicit consent before enabling analytics.
	•	Coppa/Under-18: Since minors are users, no personal data stored.
	•	OpenAI Terms: Comply with usage policy; implement moderation as above.

⸻

9 . CI/CD Pipeline (.github/workflows/ci.yml)

name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: {python-version: '3.11'}
    - run: pip install -r requirements.txt
    - run: flake8 .
    - run: pytest

Enable “Auto-deploy” in Streamlit Cloud so a green main branch triggers rebuild.

⸻

10 . Future Enhancements (post-MVP)
	•	Supabase for chat transcripts & analytics dashboard.
	•	Prompt versioning via LangChain guardrails.
	•	Multilingual support (Hindi, Tamil) with langchain_experimental/chat_models.
	•	OAuth (Google) to throttle abusive users.
	•	Escalation flow — if user expresses self-harm, surface hotline card + email transcript to counsellor.

⸻

11 . Hand-off Checklist
	•	GitHub repo shared with org.
	•	README local run confirmed.
	•	Streamlit URL shared with product owner.
	•	Check OpenAI usage dashboard for quota spike.
	•	Open ticket for “Phase 2” enhancements.

⸻

