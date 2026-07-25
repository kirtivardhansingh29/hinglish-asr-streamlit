"""
Hinglish ASR — Streamlit Web Interface
=======================================

Project : ESP32-S3 Edge Hinglish ASR

Backend : Modal Serverless (FastAPI)
GitHub  : https://github.com/kirtivardhansingh29/hinglish-asr-streamlit
"""

import streamlit as st
import requests
import time
import io
import base64
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
PRIMARY_API  = "https://ahamkirtivardhansingh--hinglish-asr-api-fastapi-app-dev.modal.run/transcribe"
FALLBACK_API = "https://dhruv-04--esp32-whisper-hinglish-fastapi-app.modal.run/transcribe"
API_TIMEOUT  = 60
MAX_FILE_MB  = 25

st.set_page_config(
    page_title="Hinglish ASR · Kirti Vardhan Singh",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 740px; }

/* ── Hero ── */
.hero { margin-bottom: 4px; }
.hero-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px; letter-spacing: 3px;
    color: #8a8680; text-transform: uppercase; margin-bottom: 6px;
}
.hero-title {
    font-size: 32px; font-weight: 600;
    color: #1a1816; letter-spacing: -0.5px; line-height: 1.1;
    margin: 0 0 6px 0;
}
.hero-subtitle {
    font-size: 13px; color: #5a5650; line-height: 1.6; margin-bottom: 0;
}
.hero-author {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: #9a9690; letter-spacing: 1px; margin-top: 8px;
}
.hero-author span { color: #2a2826; font-weight: 500; }

/* ── Model pill ── */
.model-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f0ece4; border: 1px solid #d4d0c8;
    border-radius: 3px; padding: 4px 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px; letter-spacing: 1px; color: #3a3630;
    margin-top: 10px; margin-right: 6px;
}
.model-dot { width: 6px; height: 6px; border-radius: 50%; background: #62DE61; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0; border-bottom: 1px solid #d4d0c8;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; letter-spacing: 1.5px;
    padding: 10px 20px; color: #8a8680;
    border-bottom: 2px solid transparent;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #1a1816 !important;
    border-bottom: 2px solid #1a1816 !important;
    background: transparent !important;
}

/* ── Divider ── */
.thin-divider { height: 1px; background: #e0dcd4; margin: 18px 0; }

/* ── Mic recorder embed ── */
.recorder-wrap {
    background: #f8f6f2; border: 1px solid #e0dcd4;
    border-radius: 6px; padding: 0; overflow: hidden;
}

/* ── Result ── */
.result-box {
    background: #ffffff; border: 1.5px solid #2a2826;
    border-radius: 4px; padding: 18px 20px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 16px; font-weight: 300; line-height: 1.8;
    color: #1a1816; min-height: 64px; word-break: break-word;
}
.meta-row {
    display: flex; justify-content: space-between;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px; color: #9a9690;
    letter-spacing: 0.5px; margin-top: 6px;
    flex-wrap: wrap; gap: 4px;
}
.ep-primary  { color: #1565c0; }
.ep-fallback { color: #e65100; }

/* ── Chips ── */
.chip {
    display: inline-block; padding: 3px 10px;
    border-radius: 2px; font-family: 'IBM Plex Mono', monospace;
    font-size: 9px; letter-spacing: 1px; font-weight: 500;
}
.chip-info  { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.chip-ok    { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }

/* ── History ── */
.history-entry { border-left: 2px solid #e0dcd4; padding: 6px 0 6px 14px; margin-bottom: 10px; }
.history-text  { font-size: 13px; color: #1a1816; line-height: 1.6; }
.history-meta  { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #9a9690; margin-top: 2px; }

/* ── Status indicator ── */
.status-bar {
    display: flex; align-items: center; gap: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px; color: #8a8680; letter-spacing: 1px;
    padding: 8px 0; margin-bottom: 4px;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-green  { background: #62DE61; }
.dot-orange { background: #ffaa00; animation: pulse-dot 1s ease-in-out infinite; }
.dot-red    { background: #ff4444; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "history": [], "last_result": None, "last_engine": None,
    "last_duration": None, "error_msg": None, "total_calls": 0,
    "recording_status": "idle",  # idle | recording | processing
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# TRANSCRIPTION — primary → fallback with auto-retry
# ─────────────────────────────────────────────────────────────────────────────
FALLBACK_STATUSES = {429, 503, 502}

def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    def post(url):
        files = {"file": (filename, io.BytesIO(audio_bytes), "audio/webm")}
        return requests.post(url, files=files, timeout=API_TIMEOUT)

    t0 = time.time()
    try:
        res   = post(PRIMARY_API)
        engine = "primary"
    except requests.Timeout:
        try:
            res    = post(FALLBACK_API)
            engine = "fallback"
        except requests.Timeout:
            return {"text": None, "engine": None, "duration_s": None,
                    "error": "Both endpoints timed out (60s). Modal may be cold-starting — try again in 30s."}
        except Exception as e:
            return {"text": None, "engine": None, "duration_s": None, "error": str(e)}
    except Exception as e:
        return {"text": None, "engine": None, "duration_s": None, "error": str(e)}

    if engine == "primary" and res.status_code in FALLBACK_STATUSES:
        try:
            res    = post(FALLBACK_API)
            engine = "fallback"
        except Exception:
            pass

    duration = round(time.time() - t0, 2)

    if not res.ok:
        try:    body = res.json().get("detail", res.text[:120])
        except: body = res.text[:120]
        return {"text": None, "engine": engine, "duration_s": duration,
                "error": f"HTTP {res.status_code}: {body}"}
    try:
        data = res.json()
    except:
        return {"text": None, "engine": engine, "duration_s": duration,
                "error": "Invalid JSON from API."}

    text = data.get("transcription") or data.get("text") or data.get("result") or str(data)
    return {"text": text, "engine": engine, "duration_s": duration, "error": None}


def handle_result(result, source_label):
    st.session_state.total_calls += 1
    if result["error"]:
        st.session_state.error_msg   = result["error"]
        st.session_state.last_result = None
    else:
        st.session_state.error_msg     = None
        st.session_state.last_result   = result["text"]
        st.session_state.last_engine   = result["engine"]
        st.session_state.last_duration = result["duration_s"]
        st.session_state.history.append({
            "text": result["text"], "engine": result["engine"],
            "duration": result["duration_s"], "source": source_label,
            "time": datetime.now().strftime("%H:%M:%S"),
        })


# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">ESP32-S3 · Edge ASR </div>
  <div class="hero-title">Hinglish ASR</div>
  <div class="hero-subtitle">
    Automatic Speech Recognition for <strong>code-mixed Hindi-English (Hinglish)</strong> speech —
    record live in your browser or upload an audio file.
    Powered by <strong></strong> on Modal serverless GPU.
  </div>
  <div class="hero-author">by <span></span> · B.Tech IT · GCET · 2025</div>
  <div style="margin-top:10px">
    <span class="model-pill"><span class="model-dot"></span></span>
    <span class="model-pill"><span class="model-dot"></span>modal serverless</span>
    <span class="model-pill"><span class="model-dot"></span>hinglish · hi-IN + en</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TABS — Browser Mic  |  Upload File
# ─────────────────────────────────────────────────────────────────────────────
tab_mic, tab_upload = st.tabs(["🎙  LIVE RECORD", "📁  UPLOAD FILE"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BROWSER MICROPHONE (real-time via HTML5 MediaRecorder + st.components)
# ══════════════════════════════════════════════════════════════════════════════
with tab_mic:
    st.markdown("")
    st.markdown(
        "Record directly in your browser — speak naturally in **Hinglish** "
        "(mix of Hindi and English). Click **Start Recording**, speak, then **Stop & Transcribe**."
    )
    st.caption("Works best in Chrome or Edge · Mic permission required · No data stored")
    st.markdown("")

    # ── Embed HTML5 recorder ──────────────────────────────────────────────────
    # Uses MediaRecorder API to capture audio, encodes to base64,
    # then sends back to Streamlit via st.components postMessage / query params.
    # The audio blob is passed to the Python transcription function.

    recorder_html = """
    <div style="background:#f8f6f2;border:1px solid #e0dcd4;border-radius:6px;padding:24px 20px;font-family:'IBM Plex Sans',sans-serif;">

      <div id="status" style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:2px;color:#8a8680;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
        <div id="status-dot" style="width:7px;height:7px;border-radius:50%;background:#ccc;flex-shrink:0"></div>
        <span id="status-text">READY · CLICK START TO RECORD</span>
      </div>

      <div style="display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap;">
        <button id="btn-start" onclick="startRec()"
          style="background:#1a1816;color:#f0ece4;border:none;border-radius:3px;padding:10px 22px;
                 font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1.5px;
                 cursor:pointer;transition:opacity 0.2s;">
          ⏺ START RECORDING
        </button>
        <button id="btn-stop" onclick="stopRec()" disabled
          style="background:#f0ece4;color:#8a8680;border:1px solid #d4d0c8;border-radius:3px;
                 padding:10px 22px;font-family:'IBM Plex Mono',monospace;font-size:10px;
                 letter-spacing:1.5px;cursor:not-allowed;">
          ⏹ STOP
        </button>
        <span id="timer" style="font-family:'IBM Plex Mono',monospace;font-size:18px;
              font-weight:300;color:#1a1816;letter-spacing:2px;">00:00</span>
      </div>

      <canvas id="waveform" width="680" height="44"
        style="width:100%;height:44px;background:transparent;display:block;margin-bottom:12px;">
      </canvas>

      <div id="result-section" style="display:none;">
        <div style="height:1px;background:#e0dcd4;margin:12px 0;"></div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:2px;color:#8a8680;margin-bottom:6px;">RECORDING READY</div>
        <audio id="preview" controls style="width:100%;height:36px;margin-bottom:10px;"></audio>
        <button id="btn-transcribe" onclick="sendAudio()"
          style="width:100%;background:#1a1816;color:#f0ece4;border:none;border-radius:3px;
                 padding:11px;font-family:'IBM Plex Mono',monospace;font-size:10px;
                 letter-spacing:2px;cursor:pointer;">
          TRANSCRIBE WITH WHISPER →
        </button>
      </div>

      <!-- Hidden form to send audio data back to Streamlit -->
      <input type="hidden" id="audio-data" />
      <input type="hidden" id="audio-ready" value="0" />
    </div>

    <script>
    let mediaRec = null, chunks = [], stream = null;
    let recSecs = 0, timerInterval = null, wvFrame = null;
    let audioctx = null, analyser = null, dataArr = null;
    let audioBlob = null;

    const btnStart   = document.getElementById('btn-start');
    const btnStop    = document.getElementById('btn-stop');
    const btnTrans   = document.getElementById('btn-transcribe');
    const timerEl    = document.getElementById('timer');
    const statusDot  = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const resultSec  = document.getElementById('result-section');
    const preview    = document.getElementById('preview');
    const canvas     = document.getElementById('waveform');
    const ctx        = canvas.getContext('2d');

    function setStatus(state, msg) {
      const colors = { idle:'#ccc', recording:'#ff4444', ready:'#62DE61', processing:'#ffaa00' };
      statusDot.style.background = colors[state] || '#ccc';
      if (state === 'recording') statusDot.style.animation = 'none';
      statusText.textContent = msg;
    }

    async function startRec() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
        });
      } catch(e) {
        setStatus('idle', 'MIC PERMISSION DENIED — ALLOW IN BROWSER SETTINGS');
        return;
      }

      chunks = []; recSecs = 0; audioBlob = null;
      resultSec.style.display = 'none';

      // Waveform analyser
      try {
        audioctx = new (window.AudioContext || window.webkitAudioContext)();
        const src = audioctx.createMediaStreamSource(stream);
        analyser  = audioctx.createAnalyser(); analyser.fftSize = 256;
        dataArr   = new Uint8Array(analyser.frequencyBinCount);
        src.connect(analyser);
      } catch(e) { analyser = null; }

      const mime = ['audio/webm;codecs=opus','audio/webm','audio/ogg']
        .find(m => MediaRecorder.isTypeSupported(m)) || '';
      try { mediaRec = new MediaRecorder(stream, mime ? {mimeType:mime} : {}); }
      catch(e) { mediaRec = new MediaRecorder(stream); }

      mediaRec.ondataavailable = e => { if(e.data?.size > 0) chunks.push(e.data); };
      mediaRec.onstop = onStop;
      mediaRec.start(100);

      // UI
      btnStart.disabled = true; btnStart.style.opacity = '0.4';
      btnStop.disabled  = false; btnStop.style.cursor = 'pointer';
      btnStop.style.background = '#2a2826'; btnStop.style.color = '#f0ece4';
      btnStop.style.borderColor = '#2a2826';
      setStatus('recording', 'RECORDING · SPEAK NOW IN HINGLISH');

      // Timer
      timerInterval = setInterval(() => {
        recSecs++;
        timerEl.textContent = pad(Math.floor(recSecs/60)) + ':' + pad(recSecs%60);
        if (recSecs >= 30) stopRec();
      }, 1000);

      drawWave();
    }

    function stopRec() {
      clearInterval(timerInterval);
      cancelAnimationFrame(wvFrame);
      if (mediaRec && mediaRec.state !== 'inactive') mediaRec.stop();
      if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
      if (audioctx) { audioctx.close(); audioctx = null; }
      analyser = null;
      btnStart.disabled = false; btnStart.style.opacity = '1';
      btnStop.disabled  = true;
      btnStop.style.background = '#f0ece4'; btnStop.style.color = '#8a8680';
      btnStop.style.borderColor = '#d4d0c8'; btnStop.style.cursor = 'not-allowed';
      // clear waveform
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    function onStop() {
      audioBlob = new Blob(chunks, { type: chunks[0]?.type || 'audio/webm' });
      preview.src = URL.createObjectURL(audioBlob);
      resultSec.style.display = 'block';
      setStatus('ready', 'RECORDING COMPLETE · ' + timerEl.textContent + ' · READY TO TRANSCRIBE');
    }

    function sendAudio() {
      if (!audioBlob) return;
      setStatus('processing', 'ENCODING AUDIO...');
      btnTrans.textContent = 'ENCODING...';
      btnTrans.disabled = true;

      const reader = new FileReader();
      reader.onload = () => {
        // Send base64 to Streamlit via URL param trick using query string
        const b64 = reader.result.split(',')[1];
        // Store in sessionStorage so Streamlit JS component can read it
        window.parent.postMessage({
          type: 'streamlit:setComponentValue',
          value: b64
        }, '*');
        setStatus('processing', 'SENT TO STREAMLIT · TRANSCRIBING...');
      };
      reader.readAsDataURL(audioBlob);
    }

    function drawWave() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = '#2a2826'; ctx.lineWidth = 1.5;
      ctx.beginPath();
      const w = canvas.width, h = canvas.height, mid = h / 2;
      if (analyser && dataArr) {
        analyser.getByteTimeDomainData(dataArr);
        const step = w / dataArr.length;
        for (let i = 0; i < dataArr.length; i++) {
          const y = mid + (dataArr[i] / 128 - 1) * mid * 0.8;
          i === 0 ? ctx.moveTo(0, y) : ctx.lineTo(i * step, y);
        }
      } else {
        const t = Date.now() / 300;
        for (let x = 0; x < w; x++) {
          const y = mid + Math.sin(x/18+t)*7 + Math.sin(x/8+t*1.4)*4;
          x === 0 ? ctx.moveTo(0, y) : ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
      if (mediaRec && mediaRec.state === 'recording') wvFrame = requestAnimationFrame(drawWave);
    }

    const pad = n => String(n).padStart(2, '0');
    </script>
    """

    # Render recorder component and capture returned base64 audio
    import streamlit.components.v1 as components
    audio_b64 = components.html(recorder_html, height=320, scrolling=False)

    st.markdown("")
    st.info(
        "**How to use:** Click **⏺ START RECORDING** → speak in Hinglish → click **⏹ STOP** → "
        "preview your recording → click **TRANSCRIBE WITH WHISPER →**\n\n"
        "The audio is sent to your Modal Whisper endpoint for transcription.",
        icon="ℹ️"
    )

    # ── Alternative: manual upload of recorded audio for mic tab ─────────────
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    st.markdown("##### Or paste / upload your recorded audio below")
    st.caption("If the recorder above doesn't work in your browser, record using your phone's Voice Memo app and upload here.")

    mic_file = st.file_uploader(
        "Upload recorded audio",
        type=["wav", "mp3", "m4a", "ogg", "webm", "flac", "opus"],
        key="mic_upload",
        label_visibility="collapsed",
    )
    if mic_file:
        st.audio(mic_file)
        if st.button("Transcribe with Whisper →", type="primary",
                     use_container_width=True, key="mic_transcribe"):
            with st.spinner("Sending to Whisper via Modal… (~3–30s depending on cold start)"):
                result = transcribe(mic_file.getvalue(), filename=mic_file.name)
            handle_result(result, "mic-upload")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FILE UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.markdown("")
    st.markdown(
        "Upload any Hinglish audio file. Supports recordings from phones, "
        "laptops, ESP32-S3, or any other source."
    )
    st.caption("WAV · MP3 · M4A · OGG · WEBM · FLAC · OPUS · Max 25 MB")
    st.markdown("")

    uploaded = st.file_uploader(
        "Drop audio file here or click to browse",
        type=["wav", "mp3", "m4a", "ogg", "webm", "flac", "opus"],
        label_visibility="collapsed",
        key="file_upload",
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
                f'<span class="chip chip-ok">{file_mb:.2f} MB</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")

    btn_off = uploaded is None
    if st.button("Transcribe with Whisper →", type="primary",
                 disabled=btn_off, use_container_width=True, key="file_transcribe"):
        with st.spinner("Sending to Whisper via Modal… (~3–30s on first call)"):
            result = transcribe(uploaded.getvalue(), filename=uploaded.name)
        handle_result(result, "file-upload")
        st.rerun()

    if btn_off:
        st.caption("Upload an audio file above to enable transcription.")


# ─────────────────────────────────────────────────────────────────────────────
# RESULT — shown below both tabs
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)

if st.session_state.error_msg:
    st.markdown("#### ❌ Transcription Failed")
    st.error(st.session_state.error_msg)
    st.caption("Modal cold starts can take 15–30s. Try again — the second call is always faster.")

elif st.session_state.last_result:
    st.markdown("#### ✅ Transcription")
    engine_label = (
        '<span class="ep-primary">primary · kirti · ahamkirtivardhansingh</span>'
        if st.session_state.last_engine == "primary"
        else '<span class="ep-fallback">fallback · dhruv · dhruv-04</span>'
    )
    st.markdown(
        f'<div class="result-box">{st.session_state.last_result}</div>'
        f'<div class="meta-row">'
        f'<span>openai whisper large-v3-turbo · modal gpu · {engine_label}</span>'
        f'<span>{st.session_state.last_duration}s</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.text_area("", value=st.session_state.last_result, height=72,
                 label_visibility="collapsed", key="copy_area")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇ Download .txt", data=st.session_state.last_result,
                           file_name="transcription.txt", mime="text/plain",
                           use_container_width=True)
    with c2:
        if st.button("✕ Clear", use_container_width=True):
            st.session_state.last_result = None
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎙 Hinglish ASR")
    st.markdown("**Kirti Vardhan Singh**  \nB.Tech IT · GCET · AKTU  \n2025")
    st.markdown('<div style="height:1px;background:#e0dcd4;margin:12px 0"></div>', unsafe_allow_html=True)

    st.markdown("### Model")
    st.markdown(
        "**OpenAI Whisper**  \n`large-v3-turbo`  \n\n"
        "Multilingual model with strong Hinglish performance. "
        "Handles Hindi-English code-switching natively."
    )
    st.markdown('<div style="height:1px;background:#e0dcd4;margin:12px 0"></div>', unsafe_allow_html=True)

    st.markdown("### Endpoints")
    st.markdown(
        "**Primary** *(Kirti)*  \n"
        "`ahamkirtivardhansingh`  \n"
        "`hinglish-asr-api`  \n\n"
        "**Fallback** *(Dhruv)*  \n"
        "`dhruv-04`  \n"
        "`esp32-whisper-hinglish`  \n\n"
        "Auto-switches on `429` / `503`."
    )
    st.markdown('<div style="height:1px;background:#e0dcd4;margin:12px 0"></div>', unsafe_allow_html=True)

    st.markdown("### Session")
    st.metric("API calls", st.session_state.total_calls)
    st.markdown('<div style="height:1px;background:#e0dcd4;margin:12px 0"></div>', unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown("### History")
        for entry in reversed(st.session_state.history[-8:]):
            tag = "primary" if entry["engine"] == "primary" else "fallback"
            st.markdown(
                f'<div class="history-entry">'
                f'<div class="history-text">{entry["text"][:100]}{"…" if len(entry["text"])>100 else ""}</div>'
                f'<div class="history-meta">{entry["time"]} · {entry["source"]} · {entry["duration"]}s · {tag}</div>'
                f'</div>', unsafe_allow_html=True,
            )
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<p style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;color:#9a9690;text-align:center;margin-top:8px;">'
    'Hinglish ASR · OpenAI Whisper large-v3-turbo · Modal Serverless · '
    'Kirti Vardhan Singh · GCET · AKTU · 2025'
    '</p>',
    unsafe_allow_html=True,
)
