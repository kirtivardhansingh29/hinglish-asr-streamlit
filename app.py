"""
Hinglish ASR — Live Caption Streamlit App
==========================================
Real-time Hinglish speech transcription via chunked audio recording.
Audio is captured in the browser, sent to the ASR API every few seconds,
and displayed as live captions with latency stats.
"""

import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hinglish ASR — Live Captions",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — hide Streamlit chrome, inject fonts
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400&display=swap');
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FULL APP — rendered as a single self-contained HTML component
# All logic (MediaRecorder, chunked fetch, caption rendering) lives here.
# The component fills the viewport so it feels like a standalone app.
# ─────────────────────────────────────────────────────────────────────────────

API_ENDPOINT = "https://dhruv-kum-photos--esp32-whisper-hinglish-fastapi-app.modal.run/transcribe"
CHUNK_MS     = 4000   # record 4s → send → caption → repeat

APP_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
/* ── Reset ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg:       #0d0d0d;
  --surface:  #141414;
  --surface2: #1c1c1c;
  --border:   #262626;
  --text:     #f0ede8;
  --dim:      #6b6b6b;
  --mid:      #9a9a9a;
  --accent:   #5a9fff;
  --live:     #4ade80;
  --live-dim: #14532d;
  --warn:     #fb923c;
  --mono:     'JetBrains Mono', monospace;
  --sans:     'Space Grotesk', sans-serif;
}}
html, body {{
  height: 100%; background: var(--bg);
  color: var(--text); font-family: var(--sans);
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}}
body {{ display: flex; flex-direction: column; height: 100vh; }}

/* ── Top bar ── */
.topbar {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 32px; border-bottom: 1px solid var(--border);
  flex-shrink: 0; background: var(--bg);
}}
.brand {{ font-size: 14px; font-weight: 600; letter-spacing: -0.2px; }}
.badges {{ display: flex; gap: 8px; align-items: center; }}
.badge {{
  font-family: var(--mono); font-size: 9px; letter-spacing: 1.5px;
  color: var(--dim); background: var(--surface2);
  border: 1px solid var(--border); border-radius: 3px;
  padding: 3px 8px; text-transform: uppercase;
}}
.status-row {{ display: flex; align-items: center; gap: 6px; }}
.sdot {{
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--border); transition: background 0.3s; flex-shrink: 0;
}}
.sdot.live {{ background: var(--live); box-shadow: 0 0 6px var(--live); animation: pl 1.5s ease-in-out infinite; }}
.sdot.proc {{ background: var(--accent); box-shadow: 0 0 6px var(--accent); animation: pl 0.6s ease-in-out infinite; }}
.sdot.err  {{ background: var(--warn); }}
@keyframes pl {{ 0%,100%{{opacity:1}} 50%{{opacity:0.35}} }}
.slbl {{ font-family: var(--mono); font-size: 9px; letter-spacing: 1px; color: var(--dim); text-transform: uppercase; }}
.slbl.live {{ color: var(--live); }}
.slbl.proc {{ color: var(--accent); }}

/* ── Main ── */
.main {{
  flex: 1; display: flex; flex-direction: column;
  max-width: 960px; width: 100%; margin: 0 auto;
  padding: 0 32px; min-height: 0;
}}

/* ── Caption stage ── */
.stage {{
  flex: 1; display: flex; flex-direction: column;
  justify-content: flex-end; padding: 32px 0 24px;
  position: relative; min-height: 0;
}}
.ghost {{
  position: absolute; inset: 0; display: flex;
  flex-direction: column; align-items: center;
  justify-content: center; gap: 14px;
  transition: opacity 0.4s; pointer-events: none;
}}
.ghost.hidden {{ opacity: 0; }}
.ghost-icon {{
  width: 52px; height: 52px; border-radius: 50%;
  border: 1.5px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; color: var(--dim);
}}
.ghost-txt {{ font-size: 13px; color: var(--dim); text-align: center; line-height: 1.7; }}
.ghost-txt strong {{ color: var(--mid); font-weight: 500; }}

.hist-wrap {{ display: flex; flex-direction: column; gap: 0; margin-bottom: 6px; }}
.hist-line {{
  font-size: 18px; font-weight: 300; color: var(--dim);
  line-height: 1.6; letter-spacing: -0.1px; padding: 1px 0;
  transition: opacity 0.5s;
}}
.caption-cur {{
  font-size: 30px; font-weight: 400; color: var(--text);
  line-height: 1.45; letter-spacing: -0.3px; min-height: 44px;
}}
.word-new {{
  display: inline-block;
  animation: wi 0.22s ease-out forwards;
}}
@keyframes wi {{ from{{opacity:0;transform:translateY(5px)}} to{{opacity:1;transform:translateY(0)}} }}
.caret {{
  display: inline-block; width: 2px; height: 1em;
  background: var(--accent); margin-left: 3px;
  vertical-align: text-bottom;
  animation: cb 0.9s step-end infinite;
}}
@keyframes cb {{ 0%,100%{{opacity:1}} 50%{{opacity:0}} }}
.caret.off {{ display: none; }}

/* ── Waveform ── */
.wv-wrap {{
  height: 48px; position: relative;
  margin: 0 0 18px; overflow: hidden; border-radius: 4px;
}}
canvas {{ width: 100%; height: 100%; display: block; }}
.wv-fade {{
  position: absolute; inset: 0;
  background: linear-gradient(90deg, var(--bg) 0%, transparent 48px, transparent calc(100% - 48px), var(--bg) 100%);
  pointer-events: none;
}}

/* ── Stats strip ── */
.stats {{
  display: flex; gap: 20px; align-items: center;
  padding: 10px 0 14px; border-top: 1px solid var(--border);
}}
.stat {{ display: flex; flex-direction: column; gap: 2px; }}
.sval {{
  font-family: var(--mono); font-size: 20px; font-weight: 300;
  color: var(--text); letter-spacing: -0.5px; line-height: 1;
}}
.slabel {{ font-family: var(--mono); font-size: 8px; letter-spacing: 1.5px; color: var(--dim); text-transform: uppercase; }}
.sdivider {{ width: 1px; height: 28px; background: var(--border); }}
.lat-pill {{
  margin-left: auto; font-family: var(--mono); font-size: 9px;
  letter-spacing: 1px; color: var(--dim); background: var(--surface2);
  border: 1px solid var(--border); border-radius: 3px; padding: 4px 10px;
}}
.lat-pill.fast {{ color: var(--live); border-color: var(--live-dim); background: var(--live-dim); }}
.lat-pill.slow {{ color: var(--warn); }}

/* ── Controls ── */
.controls {{
  padding: 18px 0 24px; border-top: 1px solid var(--border);
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}}
.btn-rec {{
  display: flex; align-items: center; gap: 10px;
  background: var(--text); color: var(--bg);
  border: none; border-radius: 4px; cursor: pointer;
  padding: 13px 28px; font-family: var(--sans);
  font-size: 13px; font-weight: 600;
  transition: background 0.15s; user-select: none; flex-shrink: 0;
}}
.btn-rec:hover {{ background: #dedad4; }}
.btn-rec.on {{
  background: transparent; color: var(--text);
  border: 1.5px solid var(--border);
}}
.btn-rec.on:hover {{ border-color: var(--mid); }}
.rdot {{
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--bg); flex-shrink: 0; transition: background 0.2s;
}}
.btn-rec.on .rdot {{ background: var(--live); animation: pl 0.8s ease-in-out infinite; }}
.btn-sec {{
  background: transparent; border: 1px solid var(--border);
  color: var(--mid); border-radius: 4px;
  padding: 12px 20px; font-family: var(--sans);
  font-size: 13px; cursor: pointer; transition: all 0.15s;
}}
.btn-sec:hover {{ border-color: var(--mid); color: var(--text); }}
.btn-sec:disabled {{ opacity: 0.3; cursor: not-allowed; }}
.view-toggle {{
  margin-left: auto; display: flex;
  border: 1px solid var(--border); border-radius: 4px; overflow: hidden;
}}
.vbtn {{
  background: transparent; border: none;
  color: var(--dim); font-family: var(--mono);
  font-size: 9px; letter-spacing: 1.5px; text-transform: uppercase;
  padding: 10px 14px; cursor: pointer; transition: all 0.15s;
}}
.vbtn.on {{ background: var(--surface2); color: var(--text); }}

/* ── Panels ── */
.tx-panel, .log-panel {{
  display: none; border-top: 1px solid var(--border);
  padding: 14px 0; max-height: 200px; overflow-y: auto;
  flex-direction: column; gap: 0;
}}
.tx-panel.open, .log-panel.open {{ display: flex; }}
.tx-panel::-webkit-scrollbar, .log-panel::-webkit-scrollbar {{ width: 3px; }}
.tx-panel::-webkit-scrollbar-thumb, .log-panel::-webkit-scrollbar-thumb {{ background: var(--border); }}
.tx-row {{
  display: grid; grid-template-columns: 52px 1fr;
  gap: 12px; padding: 7px 0;
  border-bottom: 1px solid var(--border);
}}
.tx-row:last-child {{ border-bottom: none; }}
.tx-t {{ font-family: var(--mono); font-size: 9px; color: var(--dim); padding-top: 2px; }}
.tx-s {{ font-size: 13px; color: var(--mid); line-height: 1.6; }}
.log-line {{ font-family: var(--mono); font-size: 9px; letter-spacing: 0.3px; line-height: 2.1; }}
.log-line.ok    {{ color: var(--live); }}
.log-line.warn  {{ color: var(--warn); }}
.log-line.debug {{ color: var(--accent); }}
.log-line.info  {{ color: var(--dim); }}

/* ── Toast ── */
.toast {{
  position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
  background: var(--surface2); border: 1px solid var(--warn);
  color: var(--warn); font-family: var(--mono); font-size: 10px;
  padding: 10px 20px; border-radius: 4px; display: none;
  z-index: 999; white-space: nowrap; letter-spacing: 0.3px;
  animation: ti 0.2s ease-out;
}}
.toast.show {{ display: block; }}
@keyframes ti {{ from{{opacity:0;transform:translateX(-50%) translateY(8px)}} to{{opacity:1;transform:translateX(-50%) translateY(0)}} }}
</style>
</head>
<body>

<!-- Top bar -->
<div class="topbar">
  <div class="badges">
    <span class="brand">Hinglish ASR</span>
    <span class="badge">ESP32-S3</span>
    <span class="badge">Live Captions</span>
  </div>
  <div class="status-row">
    <div class="sdot" id="sd"></div>
    <span class="slbl" id="sl">Idle</span>
  </div>
</div>

<!-- Main -->
<div class="main">

  <!-- Caption stage -->
  <div class="stage" id="stage">
    <div class="ghost" id="ghost">
      <div class="ghost-icon">🎙</div>
      <div class="ghost-txt">
        Press <strong>Start Recording</strong> and speak<br>
        Hindi, English, or Hinglish — captions appear live
      </div>
    </div>
    <div class="hist-wrap" id="hist"></div>
    <div class="caption-cur" id="cap">
      <span class="caret off" id="caret"></span>
    </div>
  </div>

  <!-- Waveform -->
  <div class="wv-wrap">
    <canvas id="wv"></canvas>
    <div class="wv-fade"></div>
  </div>

  <!-- Stats -->
  <div class="stats">
    <div class="stat"><div class="sval" id="sv-time">0:00</div><div class="slabel">Duration</div></div>
    <div class="sdivider"></div>
    <div class="stat"><div class="sval" id="sv-words">0</div><div class="slabel">Words</div></div>
    <div class="sdivider"></div>
    <div class="stat"><div class="sval" id="sv-segs">0</div><div class="slabel">Segments</div></div>
    <span class="lat-pill" id="lat">— ms</span>
  </div>

  <!-- Controls -->
  <div class="controls">
    <button class="btn-rec" id="brec" onclick="handleRec()">
      <span class="rdot"></span>
      <span id="blbl">Start Recording</span>
    </button>
    <button class="btn-sec" id="bclr" onclick="clearAll()" disabled>Clear</button>
    <div class="view-toggle">
      <button class="vbtn on" id="v-cap" onclick="setView('cap')">Caption</button>
      <button class="vbtn"    id="v-tx"  onclick="setView('tx')">Full</button>
      <button class="vbtn"    id="v-log" onclick="setView('log')">Log</button>
    </div>
  </div>

  <!-- Panels -->
  <div class="tx-panel"  id="tx-panel"></div>
  <div class="log-panel" id="log-panel"></div>

</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
// ─────────────────────────────────────────────────────────────────────────────
// CONFIG — injected from Python
// ─────────────────────────────────────────────────────────────────────────────
const API      = '{API_ENDPOINT}';
const CHUNK_MS = {CHUNK_MS};
const MAX_HIST = 4;

// ─────────────────────────────────────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────────────────────────────────────
let recording = false, stream = null, mediaRec = null;
let audioctx = null, analyser = null, pcmBuf = null;
let wvFrame = null, clockTimer = null, chunkTimer = null;
let recStart = null, totalWords = 0, totalSegs = 0;
let histLines = [], currentView = 'cap';

// ─────────────────────────────────────────────────────────────────────────────
// ELEMENTS
// ─────────────────────────────────────────────────────────────────────────────
const brec    = document.getElementById('brec');
const blbl    = document.getElementById('blbl');
const bclr    = document.getElementById('bclr');
const capEl   = document.getElementById('cap');
const caretEl = document.getElementById('caret');
const histEl  = document.getElementById('hist');
const ghostEl = document.getElementById('ghost');
const sdEl    = document.getElementById('sd');
const slEl    = document.getElementById('sl');
const latEl   = document.getElementById('lat');
const txPanel = document.getElementById('tx-panel');
const logPanel= document.getElementById('log-panel');
const toast   = document.getElementById('toast');
const canvas  = document.getElementById('wv');
const ctx     = canvas.getContext('2d');

// ─────────────────────────────────────────────────────────────────────────────
// STATUS
// ─────────────────────────────────────────────────────────────────────────────
function setStatus(cls, lbl) {{
  sdEl.className = 'sdot ' + cls;
  slEl.className = 'slbl ' + cls;
  slEl.textContent = lbl;
}}

// ─────────────────────────────────────────────────────────────────────────────
// RECORD
// ─────────────────────────────────────────────────────────────────────────────
async function handleRec() {{
  if (recording) {{ stopRec(); return; }}
  await startRec();
}}

async function startRec() {{
  try {{
    stream = await navigator.mediaDevices.getUserMedia({{
      audio: {{ sampleRate: 16000, channelCount: 1,
               echoCancellation: true, noiseSuppression: true }}
    }});
  }} catch(e) {{
    showToast('Mic denied — allow microphone in browser settings');
    return;
  }}
  try {{
    audioctx = new (window.AudioContext || window.webkitAudioContext)();
    const src = audioctx.createMediaStreamSource(stream);
    analyser  = audioctx.createAnalyser(); analyser.fftSize = 512;
    pcmBuf    = new Uint8Array(analyser.frequencyBinCount);
    src.connect(analyser);
  }} catch(_) {{ analyser = null; }}

  recording = true; recStart = Date.now();
  brec.classList.add('on'); blbl.textContent = 'Stop';
  bclr.disabled = true;
  ghostEl.classList.add('hidden');
  caretEl.classList.remove('off');
  setStatus('live', 'Live');
  clockTimer = setInterval(() => {{
    const s = Math.floor((Date.now() - recStart) / 1000);
    document.getElementById('sv-time').textContent =
      Math.floor(s/60) + ':' + String(s%60).padStart(2,'0');
  }}, 500);
  startChunk();
  drawWave();
  addLog('ok', 'Recording started');
}}

function startChunk() {{
  if (!recording) return;
  let chunks = [];
  const mime = ['audio/webm;codecs=opus','audio/webm','audio/ogg']
    .find(m => MediaRecorder.isTypeSupported(m)) || '';
  try {{ mediaRec = new MediaRecorder(stream, mime ? {{mimeType:mime}} : {{}}); }}
  catch(_) {{ mediaRec = new MediaRecorder(stream); }}
  mediaRec.ondataavailable = e => {{ if (e.data?.size > 0) chunks.push(e.data); }};
  mediaRec.onstop = () => {{
    const blob = new Blob(chunks, {{type: chunks[0]?.type || 'audio/webm'}});
    sendChunk(blob);
  }};
  mediaRec.start(100);
  chunkTimer = setTimeout(() => {{
    if (mediaRec && mediaRec.state !== 'inactive') mediaRec.stop();
  }}, CHUNK_MS);
}}

function stopRec() {{
  recording = false;
  clearInterval(clockTimer); clearTimeout(chunkTimer);
  if (mediaRec && mediaRec.state !== 'inactive') mediaRec.stop();
  if (stream) {{ stream.getTracks().forEach(t => t.stop()); stream = null; }}
  if (audioctx) {{ audioctx.close(); audioctx = null; }}
  cancelAnimationFrame(wvFrame); analyser = null; pcmBuf = null;
  brec.classList.remove('on'); blbl.textContent = 'Start Recording';
  bclr.disabled = false;
  caretEl.classList.add('off');
  setStatus('', 'Ready');
  flatLine();
  addLog('ok', 'Recording stopped');
}}

// ─────────────────────────────────────────────────────────────────────────────
// SEND CHUNK → API
// ─────────────────────────────────────────────────────────────────────────────
async function sendChunk(blob) {{
  if (blob.size < 800) {{
    addLog('debug', 'Chunk too small (' + blob.size + 'B) — silence skipped');
    if (recording) startChunk();
    return;
  }}
  setStatus('proc', 'Processing…');
  addLog('debug', 'Chunk: ' + Math.round(blob.size/1024) + 'KB');
  const t0 = Date.now();
  const fd  = new FormData();
  fd.append('file', blob, 'chunk.webm');
  try {{
    const ctrl = new AbortController();
    const to   = setTimeout(() => ctrl.abort(), 30000);
    const res  = await fetch(API, {{method:'POST', body:fd, signal:ctrl.signal}});
    clearTimeout(to);
    const ms = Date.now() - t0;
    updateLat(ms);
    if (!res.ok) {{
      const body = await res.text().catch(() => '');
      addLog('warn', 'HTTP ' + res.status + ' — ' + body.slice(0,80));
      showToast('API error ' + res.status);
    }} else {{
      const data = await res.json();
      const text = (data.transcription || data.text || data.result || '').trim();
      if (text) {{
        pushCaption(text, ms);
        addLog('ok', '[' + ms + 'ms] ' + text);
      }} else {{
        addLog('debug', 'Empty — silence');
      }}
    }}
  }} catch(err) {{
    if (err.name === 'AbortError') {{
      addLog('warn', 'Timeout after 30s');
      showToast('API timeout — skipping chunk');
    }} else {{
      addLog('warn', err.message);
    }}
  }}
  if (recording) {{ setStatus('live','Live'); startChunk(); }}
}}

// ─────────────────────────────────────────────────────────────────────────────
// CAPTIONS
// ─────────────────────────────────────────────────────────────────────────────
function pushCaption(text, ms) {{
  const wc = text.split(/\s+/).filter(Boolean).length;
  totalWords += wc; totalSegs++;
  document.getElementById('sv-words').textContent = totalWords;
  document.getElementById('sv-segs').textContent  = totalSegs;

  const ts = new Date().toLocaleTimeString('en-IN',
    {{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
  addTxRow(ts, text);

  const prev = capEl.getAttribute('data-text') || '';
  if (prev.trim()) {{
    histLines.push(prev.trim());
    if (histLines.length > MAX_HIST) histLines.shift();
    renderHist();
  }}
  renderCap(text);
  capEl.setAttribute('data-text', text);
  bclr.disabled = false;
}}

function renderHist() {{
  histEl.innerHTML = '';
  histLines.forEach((l, i) => {{
    const d = document.createElement('div');
    d.className = 'hist-line';
    d.textContent = l;
    const age = histLines.length - 1 - i;
    d.style.opacity  = Math.max(0.08, 0.38 - age * 0.07);
    d.style.fontSize = Math.max(14, 18 - age) + 'px';
    histEl.appendChild(d);
  }});
}}

function renderCap(text) {{
  capEl.innerHTML = '';
  text.split(/(\s+)/).forEach((w, i) => {{
    const s = document.createElement('span');
    if (/\s/.test(w)) {{ s.textContent = w; }}
    else {{
      s.className = 'word-new';
      s.textContent = w;
      s.style.animationDelay = (i * 0.038) + 's';
    }}
    capEl.appendChild(s);
  }});
  capEl.appendChild(caretEl);
}}

// ─────────────────────────────────────────────────────────────────────────────
// WAVEFORM
// ─────────────────────────────────────────────────────────────────────────────
function drawWave() {{
  const dpr = window.devicePixelRatio || 1;
  canvas.width  = canvas.offsetWidth  * dpr;
  canvas.height = canvas.offsetHeight * dpr;
  ctx.scale(dpr, dpr);
  const w = canvas.offsetWidth, h = canvas.offsetHeight, mid = h / 2;
  ctx.clearRect(0, 0, w, h);
  if (analyser && pcmBuf) {{
    analyser.getByteTimeDomainData(pcmBuf);
    ctx.strokeStyle = '#5a9fff'; ctx.lineWidth = 1.5;
    ctx.shadowColor = '#5a9fff'; ctx.shadowBlur = 4;
    ctx.beginPath();
    const step = w / pcmBuf.length;
    for (let i = 0; i < pcmBuf.length; i++) {{
      const y = mid + (pcmBuf[i] / 128 - 1) * mid * 0.85;
      i === 0 ? ctx.moveTo(0, y) : ctx.lineTo(i * step, y);
    }}
    ctx.stroke(); ctx.shadowBlur = 0;
  }} else {{
    const t = Date.now() / 400;
    ctx.strokeStyle = '#262626'; ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x < w; x++) {{
      const y = mid + Math.sin(x/20+t)*4 + Math.sin(x/9+t*1.3)*2;
      x===0 ? ctx.moveTo(0,y) : ctx.lineTo(x,y);
    }}
    ctx.stroke();
  }}
  if (recording) wvFrame = requestAnimationFrame(drawWave);
}}

function flatLine() {{
  const w = canvas.offsetWidth || 800, h = canvas.offsetHeight || 48;
  ctx.clearRect(0,0,w,h);
  ctx.strokeStyle = '#262626'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0,h/2); ctx.lineTo(w,h/2); ctx.stroke();
}}

// ─────────────────────────────────────────────────────────────────────────────
// LATENCY
// ─────────────────────────────────────────────────────────────────────────────
function updateLat(ms) {{
  latEl.textContent = ms + 'ms';
  latEl.className   = 'lat-pill' + (ms < 8000 ? ' fast' : ' slow');
}}

// ─────────────────────────────────────────────────────────────────────────────
// VIEWS
// ─────────────────────────────────────────────────────────────────────────────
function setView(v) {{
  currentView = v;
  ['cap','tx','log'].forEach(id => {{
    document.getElementById('v-'+id).classList.toggle('on', id===v);
  }});
  txPanel.classList.toggle('open',  v==='tx');
  logPanel.classList.toggle('open', v==='log');
}}

// ─────────────────────────────────────────────────────────────────────────────
// PANELS
// ─────────────────────────────────────────────────────────────────────────────
function addTxRow(ts, text) {{
  const d = document.createElement('div');
  d.className = 'tx-row';
  d.innerHTML = `<div class="tx-t">${{ts}}</div><div class="tx-s">${{text}}</div>`;
  txPanel.appendChild(d);
  txPanel.scrollTop = txPanel.scrollHeight;
}}

function addLog(type, msg) {{
  const ts = new Date().toLocaleTimeString('en-IN');
  const d  = document.createElement('div');
  d.className = 'log-line ' + type;
  d.textContent = '[' + ts + '] ' + msg;
  logPanel.appendChild(d);
  logPanel.scrollTop = logPanel.scrollHeight;
}}

// ─────────────────────────────────────────────────────────────────────────────
// CLEAR
// ─────────────────────────────────────────────────────────────────────────────
function clearAll() {{
  histLines = []; histEl.innerHTML = '';
  txPanel.innerHTML = ''; logPanel.innerHTML = '';
  capEl.innerHTML = ''; capEl.appendChild(caretEl);
  capEl.removeAttribute('data-text');
  totalWords = 0; totalSegs = 0;
  document.getElementById('sv-words').textContent = '0';
  document.getElementById('sv-segs').textContent  = '0';
  document.getElementById('sv-time').textContent  = '0:00';
  latEl.textContent = '— ms'; latEl.className = 'lat-pill';
  ghostEl.classList.remove('hidden');
  bclr.disabled = true;
}}

// ─────────────────────────────────────────────────────────────────────────────
// TOAST
// ─────────────────────────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg) {{
  toast.textContent = msg; toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}}

// ─────────────────────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────────────────────
flatLine();
window.addEventListener('resize', () => {{ if (!recording) flatLine(); }});
addLog('ok', 'System ready');
addLog('info', 'API: ' + API.split('//')[1].split('/')[0]);
addLog('info', 'Chunk: ' + CHUNK_MS + 'ms · Max history: ' + MAX_HIST + ' lines');
</script>
</body>
</html>
"""

# Render the full app as an HTML component filling the viewport
components.html(APP_HTML, height=780, scrolling=False)
