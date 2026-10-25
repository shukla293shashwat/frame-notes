import html
import os
import tempfile
import time

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question
from core.llm_provider import required_api_key_name, selected_provider

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Frame Notes | Meeting intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── Root Variables ── */
:root {
    --bg: #151e1b;
    --surface: #1d2925;
    --surface-2: #26352f;
    --border: #394a42;
    --accent: #d47b53;
    --accent-glow: #f0ad83;
    --accent-2: #a9bd92;
    --text: #f1ede3;
    --text-muted: #aeb7aa;
    --success: #a9c797;
    --warning: #f59e0b;
    --danger: #ef4444;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg) !important;
}

/* Animated grid background */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        linear-gradient(rgba(212, 123, 83, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212, 123, 83, 0.035) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Newsreader', Georgia, serif !important;
    color: var(--text) !important;
}

/* ── Hero Title ── */
.hero-title {
    font-family: 'Newsreader', Georgia, serif;
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(135deg, #f1ede3 0%, var(--accent-glow) 55%, var(--accent-2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.8rem;
    color: var(--text-muted);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}

.card:hover {
    border-color: var(--accent);
}

.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, var(--accent), var(--accent-2));
}

.card-title {
    font-family: 'Newsreader', Georgia, serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-content {
    font-size: 0.875rem;
    line-height: 1.7;
    color: var(--text);
    white-space: pre-wrap;
}

/* ── Accent Badge ── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.badge-purple { background: rgba(212,123,83,0.18); color: var(--accent-glow); border: 1px solid rgba(212,123,83,0.35); }
.badge-cyan   { background: rgba(169,189,146,0.14); color: var(--accent-2);    border: 1px solid rgba(169,189,146,0.32); }
.badge-green  { background: rgba(169,199,151,0.14); color: var(--success);    border: 1px solid rgba(169,199,151,0.32); }

/* ── Input & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(212,123,83,0.18) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), #a95d3b) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Newsreader', Georgia, serif !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
    text-transform: uppercase !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(212,123,83,0.28) !important;
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
}

/* ── Progress / Status ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-2);
    border-radius: 8px;
    margin: 0.4rem 0;
    border: 1px solid var(--border);
    font-size: 0.8rem;
}

.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-active   { background: var(--accent-glow); box-shadow: 0 0 8px var(--accent-glow); animation: pulse 1.5s infinite; }
.dot-done     { background: var(--success); }
.dot-pending  { background: var(--border); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* ── Chat ── */
.chat-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

.chat-msg {
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.chat-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

.chat-bubble {
    display: inline-block;
    padding: 0.6rem 1rem;
    border-radius: 10px;
    font-size: 0.85rem;
    line-height: 1.6;
    max-width: 90%;
}

.user-label  { color: var(--accent-glow); }
.bot-label   { color: var(--accent-2); }

.user-bubble { background: rgba(212,123,83,0.14); border: 1px solid rgba(212,123,83,0.24); align-self: flex-end; }
.bot-bubble  { background: rgba(169,189,146,0.1);  border: 1px solid rgba(169,189,146,0.2);   align-self: flex-start; }

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Transcript box ── */
.transcript-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    font-size: 0.82rem;
    line-height: 1.8;
    max-height: 300px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Stale Streamlit elements ── */
.stProgress > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-muted) !important; font-size: 0.8rem !important; }

/* scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size:1.6rem">FN<br>Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">VIDEO INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">New session</span>', unsafe_allow_html=True)
    input_method = st.segmented_control(
        "Media source",
        ["YouTube link", "Upload media"],
        default="YouTube link",
        key="media_input_method",
    )
    source = ""
    uploaded_media = None
    if input_method == "YouTube link":
        source = st.text_input("YouTube URL or local file path", placeholder="Paste a YouTube link")
    else:
        uploaded_media = st.file_uploader(
            "Choose an audio or video file",
            type=["mp3", "mp4", "m4a", "wav", "webm", "mpeg", "mpga", "ogg", "flac", "aac", "mov", "mkv"],
            max_upload_size=100,
            help="Upload a file up to 100 MB. On the deployed app, use this option when YouTube blocks a link.",
        )

    language_label = st.segmented_control("Transcript language", ["English", "Hinglish"], default="English")
    language = language_label.lower()

    run_btn = st.button("Create notes", icon=":material/auto_awesome:", type="primary", width="stretch")

    if st.session_state.pipeline_done:
        st.markdown("---")
        st.markdown('<span class="badge badge-green">Pipeline Status</span>', unsafe_allow_html=True)
        for step, icon, label in [
            ("audio",      "🔊", "Audio Processing"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Extraction"),
            ("rag",        "🧠", "RAG Engine"),
        ]:
            render_step_bar(label, step, icon)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Frame Notes</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Turn long conversations into clear next steps</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip() and uploaded_media is None:
        st.error("Enter a YouTube URL or choose an audio/video file to upload.")
    elif required_api_key_name() and not os.getenv(required_api_key_name()):
        st.error("Add the required API key for the selected provider to the project .env file, then restart the app. Local Ollama mode does not require a key. See README.md for setup steps.")
    elif language == "hinglish" and not os.getenv("SARVAM_API_KEY"):
        st.error("Add your SARVAM_API_KEY to the project .env file to use Hinglish transcription.")
    elif source.strip() and not source.startswith(("http://", "https://")) and not os.path.isfile(source):
        st.error("That file path could not be found. Enter the full path to an audio or video file.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        temporary_upload_path = None
        try:
            with progress_placeholder.container():
                st.info("⚙️ Pipeline running — see sidebar for live status…")

            update_step("audio", "active")
            processing_source = source
            if uploaded_media is not None:
                suffix = os.path.splitext(uploaded_media.name)[1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(uploaded_media.getvalue())
                    temporary_upload_path = temp_file.name
                processing_source = temporary_upload_path
            chunks = process_input(processing_source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            error_text = str(e)
            if "429" in error_text or "rate limit" in error_text.lower() or "rate_limited" in error_text.lower():
                progress_placeholder.error(
                    "The selected AI provider is temporarily rate-limiting requests. The app retries automatically; "
                    "if this message remains, wait a few minutes and run the analysis again. "
                    "Your transcript is still local and was not lost."
                )
            else:
                if "403" in error_text and source.startswith(("http://", "https://")):
                    progress_placeholder.error(
                        "YouTube blocked this download from the hosted app. Choose Upload media in the sidebar "
                        "and upload the video or audio file instead."
                    )
                else:
                    progress_placeholder.error(f"❌ Error: {e}")
        finally:
            if temporary_upload_path and os.path.exists(temporary_upload_path):
                try:
                    os.remove(temporary_upload_path)
                except OSError:
                    pass

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title banner
    st.markdown(f"""
    <div class="card">
        <div class="card-title">SESSION TITLE</div>
        <div style="font-family:'Newsreader',Georgia,serif;font-size:1.4rem;font-weight:700;color:var(--text)">
            {html.escape(str(r['title']))}
        </div>
    </div>""", unsafe_allow_html=True)

    # Top row: summary + transcript
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Summary</div>
            <div class="card-content">{html.escape(str(r['summary']))}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("Full transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{html.escape(str(r["transcript"]))}</div>', unsafe_allow_html=True)

    # Second row: action items | decisions | questions
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Action items</div>
            <div class="card-content">{html.escape(str(r['action_items']))}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Key decisions</div>
            <div class="card-content">{html.escape(str(r['key_decisions']))}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Open questions</div>
            <div class="card-content">{html.escape(str(r['open_questions']))}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Newsreader\',Georgia,serif;font-size:1.2rem;font-weight:700;margin-bottom:1rem">Ask the conversation</div>', unsafe_allow_html=True)

    # Chat history display
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{html.escape(str(msg['content']))}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">Frame Notes</span>
                    <div class="chat-bubble bot-bubble">{html.escape(str(msg['content']))}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript</div>
        </div>""", unsafe_allow_html=True)

    # Chat input
    chat_col1, chat_col2 = st.columns([5, 1], gap="small", vertical_alignment="bottom")
    with chat_col1:
        user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed")
    with chat_col2:
        send_btn = st.button("Ask", icon=":material/arrow_upward:", type="primary", width="stretch")

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("Clear chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Empty state
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5rem 2rem;text-align:center">
        <div style="font-family:'Newsreader',Georgia,serif;font-size:2.25rem;color:var(--accent);margin-bottom:1rem">FN</div>
        <div style="font-family:'Newsreader',Georgia,serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.5rem">
            Your next clear summary starts here.
        </div>
        <div style="color:var(--text-muted);font-size:0.85rem;max-width:380px;line-height:1.7">
            Add a recording or video link. Frame Notes turns the conversation into a useful summary, decisions, and follow-ups you can act on.
        </div>
        <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-purple">Transcript</span>
            <span class="badge badge-cyan">Meeting notes</span>
            <span class="badge badge-green">Ask questions</span>
        </div>
    </div>""", unsafe_allow_html=True)





