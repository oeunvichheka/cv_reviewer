import streamlit as st
from openai import OpenAI
import json
 
# ── API client ──────────────────────────────────────
# In Streamlit Cloud, secrets are stored in the dashboard.
# Locally, set the env variable or use st.secrets.

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

 
# ── System prompts (unchanged from CLI version) ─────
SYSTEM_PROMPT = """
You are an expert career coach and professional CV reviewer.
Respond ONLY with a JSON object in this exact format:
{"strengths":["...","...","..."],
 "improvements":["...","...","..."],
 "overall_score":7,
 "score_reason":"One sentence explanation"}
Every point must reference a specific CV detail. Return valid JSON only.
"""
 
COVER_LETTER_PROMPT = """
You are an expert cover letter writer.
Write a 200-280 word cover letter using specific CV achievements.
Open with a strong, specific first sentence. Return the letter text only.
"""
 
# ── Core functions (unchanged from CLI version) ─────
def analyse_cv(cv_text):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":f"Analyse this CV:\n\n{cv_text}"}
        ],
        temperature=0.3
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return None
 
def generate_cover_letter(cv_text, analysis, role):
    msg = (f'Target role: {role}\n'
           f'Strengths: {analysis["strengths"]}\n'
           f'CV: {cv_text}')
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"system","content":COVER_LETTER_PROMPT},
                  {"role":"user","content":msg}],
        temperature=0.7
    )
    return resp.choices[0].message.content
 
# ── Streamlit UI ────────────────────────────────────
st.set_page_config(page_title="Smart CV Reviewer", page_icon="🎯")
st.title("🎯 Smart CV Reviewer")
st.caption("Powered by GPT-4o")
 
# ── Session state initialisation ────────────────────
# Must happen before any widget renders.
# These variables persist across Streamlit reruns.
if "analysis"     not in st.session_state: st.session_state.analysis     = None
if "cover_letter" not in st.session_state: st.session_state.cover_letter = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "cv_text"      not in st.session_state: st.session_state.cv_text      = ""
if "role"         not in st.session_state: st.session_state.role         = ""
 
# ── Phase 1 & 2: Input + Analysis ───────────────────
with st.expander("📋 Enter your CV and target role", expanded=True):
    cv_input = st.text_area("Paste your CV here", height=250,
                            placeholder="")
    role_input = st.text_input("Target job role",
                              placeholder="")
    analyse_btn = st.button(" Analyse CV", type="primary",
                           disabled=not (cv_input and role_input))
 
if analyse_btn:
    with st.spinner("Analysing your CV..."):
        st.session_state.analysis = analyse_cv(cv_input)
        st.session_state.cv_text  = cv_input
        st.session_state.role     = role_input
    if st.session_state.analysis:
        with st.spinner("Generating cover letter..."):
            st.session_state.cover_letter = generate_cover_letter(
                cv_input, st.session_state.analysis, role_input)
        # Reset chat when a new CV is analysed
        st.session_state.chat_history = []
 
# ── Display analysis results ─────────────────────────
if st.session_state.analysis:
    a = st.session_state.analysis
    score = a.get('overall_score', '?')
    reason = a.get('score_reason', '')
    st.metric('CV Score', f'{score} / 10', reason)
    st.divider()
 
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Strengths")
        for s in a.get('strengths', []):
            st.markdown(f"• {s}")
    with col2:
        st.subheader("🔧 Improvements")
        for imp in a.get('improvements', []):
            st.markdown(f"• {imp}")
    st.divider()
    st.subheader("📝 Cover Letter")
    st.write(st.session_state.cover_letter)
 
    # ── Phase 3: Multi-turn refinement chat ──────────
    st.divider()
    st.subheader("Search for an answer")
    st.caption("Ask the AI to adjust anything: shorten the letter, change tone, rewrite a section.")
 
    # Display past chat messages
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])
 
    # Chat input at the bottom
    if prompt := st.chat_input("What would you like to implementation?"):
        # Show user message immediately
        st.chat_message('user').write(prompt)
        st.session_state.chat_history.append(
            {"role":"user","content":prompt})
 
        # Build full context for the API
        context = (
            f"CV Analysis: {json.dumps(st.session_state.analysis)}\n"
            f"Cover Letter:\n{st.session_state.cover_letter}\n"
            f"Original CV:\n{st.session_state.cv_text}"
        )
        messages = [
            {"role":"system",
             "content":"You are a career coach. Context:\n" + context},
            *st.session_state.chat_history
        ]
        resp = client.chat.completions.create(
            model="gpt-4o", messages=messages, temperature=0.5)
        reply = resp.choices[0].message.content
 
        st.chat_message('assistant').write(reply)
        st.session_state.chat_history.append(
            {"role":"assistant","content":reply})


 
# Streamlit will open a browser tab automatically:
#   Local URL:   http://localhost:8501
#   Network URL: http://192.168.x.x:8501
