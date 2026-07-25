"""
Hinglish ASR — Streamlit Web Interface
=======================================
Author : Kirti Vardhan Singh
GitHub : https://github.com/kirtivardhansingh29/hinglish-asr-streamlit
"""

import streamlit as st
import requests
import time
import io
from datetime import datetime

PRIMARY_API  = "https://ahamkirtivardhansingh--hinglish-asr-api-fastapi-app-dev.modal.run/transcribe"
FALLBACK_API = "https://dhruv-04--esp32-whisper-hinglish-fastapi-app.modal.run/transcribe"
API_TIMEOUT  = 60
MAX_FILE_MB  = 25

st.set_page_config(page_title="Hinglish ASR", page_icon="🎙️", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 720px; }
.device-badge { font-family: 'IBM Plex Mono', monospace; font-size: 10px; letter-spacing: 3px; color: #8a8680; text-transform: uppercase; }
.result-box { background: #ffffff; border: 1.5px solid #2a2826; border-radius: 4px; padding: 18px 20px; font-family: 'IBM Plex Sans', sans-serif; font-size: 17px; font-weight: 300; line-height: 1.75; color: #1a1816; min-height: 72px; word-break: break-word; }
.meta-row { display: flex; justify-content: space-between; font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #9a9690; letter-spacing: 0.5px; margin-top: 8px; flex-wrap: wrap; gap: 4px; }
.chip { display: inline-block; padding: 3px 10px; border-radius: 2px; font-family: 'IBM Plex Mono', monospace; font-size: 10px; letter-spacing: 1px; font-weight: 500; }
.chip-info { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.thin-divider { height: 1px; background: #e0dcd4; margin: 20px 0; }
.history-entry { border-left: 2px solid #e0dcd4; padding: 8px 0 8px 14px; margin-bottom: 12px; }
.history-text { font-size: 14px; color: #1a1816; line-height: 1.6; }
.history-meta { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #9a9690; margin-top: 3px; }
.ep-primary { color: #1565c0; }
.ep-fallback { color: #e65100; }
</style>
""", unsafe_allow_html=True)

def init_state():
    defaults = {"history": [], "last_result": None, "last_engine": None,
                "last_duration": None, "error_msg": None, "total_calls": 0}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

FALLBACK_STATUSES = {429, 503, 502}

def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    def post(url):
        files = {"file": (filename, io.BytesIO(audio_bytes), "audio/webm")}
        return requests.post(url, files=files, timeout=API_TIMEOUT)

    t0 = time.time()
    try:
        res = post(PRIMARY_API)
        engine = "primary"
    except requests.Timeout:
        try:
            res = post(FALLBACK_API)
            engine = "fallback"
        except requests.Timeout:
            return {"text": None, "engine": None, "duration_s": None,
                    "error": "Both endpoints timed out after 60s. Modal may be cold-starting — try again."}
        except Exception as e:
            return {"text": None, "engine": None, "duration_s": None, "error": str(e)}
    except Exception as e:
        return {"text": None, "engine": None, "duration_s": None, "error": str(e)}

    if engine == "primary" and res.status_code in FALLBACK_STATUSES:
        try:
            res = post(FALLBACK_API)
            engine = "fallback"
        except Exception:
            pass

    duration = round(time.time() - t0, 2)

    if not res.ok:
        try:
            body = res.json().get("detail", res.text[:120])
        except Exception:
            body = res.text[:120]
        return {"text": None, "engine": engine, "duration_s": duration,
                "error": f"HTTP {res.status_code}: {body}"}

    try:
        data = res.json()
    except Exception:
        return {"text": None, "engine": engine, "duration_s": duration,
                "error": "Invalid JSON response from API."}

    text = data.get("transcription") or data.get("text") or data.get("result") or str(data)
    return {"text": text, "engine": engine, "duration_s": duration, "error": None}


# ── Header ──
st.markdown('<p class="device-badge">ESP32-S3 · whisper-large-v3-turbo · Modal</p>', unsafe_allow_html=True)
st.title("Hinglish ASR")
st.markdown("Automatic Speech Recognition for **code-mixed Hindi-English (Hinglish)** audio. Upload a recording — the system transcribes using OpenAI Whisper deployed on Modal.")
st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)

# ── Upload ──
st.markdown("#### Upload Audio")
col_info, col_fmt = st.columns([2, 1])
with col_info:
    st.caption("Supports WAV, MP3, M4A, OGG, WEBM, FLAC · Max 25 MB")
with col_fmt:
    st.caption("Best: 16 kHz · Mono · WAV")

uploaded = st.file_uploader(
    label="Drop audio file here",
    type=["wav", "mp3", "m4a", "ogg", "webm", "flac", "opus"],
    label_visibility="collapsed",
)

if uploaded:
    st.audio(uploaded, format=uploaded.type or "audio/wav")
    file_mb = len(uploaded.getvalue()) / (1024 * 1024)
    if file_mb > MAX_FILE_MB:
        st.error(f"File too large ({file_mb:.1f} MB). Maximum is {MAX_FILE_MB} MB.")
        uploaded = None
    else:
        st.markdown(
            f'<span class="chip chip-info">{uploaded.name}</span> '
            f'<span class="chip chip-info">{file_mb:.2f} MB</span>',
            unsafe_allow_html=True,
        )

st.markdown("")
btn_disabled = uploaded is None
transcribe_btn = st.button("Transcribe →", type="primary", disabled=btn_disabled, use_container_width=True)
if btn_disabled:
    st.caption("Upload an audio file above to enable transcription.")

# ── Transcribe ──
if transcribe_btn and uploaded:
    with st.spinner("Transcribing… this may take 10–30s on first call (cold start)"):
        result = transcribe(uploaded.getvalue(), filename=uploaded.name)
    st.session_state.total_calls += 1
    if result["error"]:
        st.session_state.error_msg   = result["error"]
        st.session_state.last_result = None
    else:
        st.session_state.last_result   = result["text"]
        st.session_state.last_engine   = result["engine"]
        st.session_state.last_duration = result["duration_s"]
        st.session_state.error_msg     = None
        st.session_state.history.append({
            "text": result["text"], "engine": result["engine"],
            "duration": result["duration_s"], "file": uploaded.name,
            "time": datetime.now().strftime("%H:%M:%S"),
        })

# ── Result ──
if st.session_state.error_msg:
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### Result")
    st.error(f"**Transcription failed**\n\n{st.session_state.error_msg}")
    st.caption("Try again — Modal cold starts can cause timeouts on the first call.")

elif st.session_state.last_result:
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### Result")
    engine_label = (
        '<span class="ep-primary">primary · kirti</span>'
        if st.session_state.last_engine == "primary"
        else '<span class="ep-fallback">fallback · dhruv</span>'
    )
    st.markdown(
        f'<div class="result-box">{st.session_state.last_result}</div>'
        f'<div class="meta-row">'
        f'<span>modal · whisper-large-v3-turbo · {engine_label}</span>'
        f'<span>{st.session_state.last_duration}s</span></div>',
        unsafe_allow_html=True,
    )
    st.text_area("Copy transcription", value=st.session_state.last_result, height=80, label_visibility="collapsed")
    col_dl, col_clear = st.columns([1, 1])
    with col_dl:
        st.download_button("Download .txt", data=st.session_state.last_result,
                           file_name="transcription.txt", mime="text/plain", use_container_width=True)
    with col_clear:
        if st.button("Clear result", use_container_width=True):
            st.session_state.last_result = None
            st.rerun()

# ── Sidebar ──
with st.sidebar:
    st.markdown("### Session")
    st.metric("API calls this session", st.session_state.total_calls)
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    st.markdown("### Endpoints")
    st.markdown("**Primary** *(Kirti)*\n\n`...fastapi-app-dev.modal.run`\n\n**Fallback** *(Dhruv)*\n\n`...esp32-whisper...modal.run`\n\nFallback activates automatically on 429/503.")
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    st.markdown("### Info")
    st.markdown("- Model: `whisper-large-v3-turbo`\n- Language: Hinglish (hi-IN + en)\n- Backend: Modal serverless\n- Cold start: ~15–30s\n- Warm: ~3–8s")
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    if st.session_state.history:
        st.markdown("### History")
        for entry in reversed(st.session_state.history):
            st.markdown(
                f'<div class="history-entry">'
                f'<div class="history-text">{entry["text"][:120]}{"…" if len(entry["text"]) > 120 else ""}</div>'
                f'<div class="history-meta">{entry["time"]} · {entry["file"]} · {entry["duration"]}s · {entry["engine"]}</div>'
                f'</div>', unsafe_allow_html=True,
            )
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()

# ── Footer ──
st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<p style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#9a9690;text-align:center;">'
    'Hinglish ASR · ESP32-S3 · Kirti Vardhan Singh · GCET · AKTU · 2025</p>',
    unsafe_allow_html=True,
)
