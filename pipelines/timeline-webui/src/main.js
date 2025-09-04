// Timeline WebUI main logic
// - Directory picker (File System Access API)
// - Optional recursive scan with limit
// - Extract start time via media metadata (EXIF for images) or fallback to file.lastModified
// - Get duration for audio/video using HTML media elements (loadedmetadata)
// - Render timeline on canvas with zoom/pan via top control row

import exifr from 'https://cdn.jsdelivr.net/npm/exifr/dist/lite.esm.js';

const canvas = document.getElementById('timeline');
const ctx = canvas.getContext('2d');

const btnPickDir = document.getElementById('pickDir');
const chkRecursive = document.getElementById('recursive');
const inpLimit = document.getElementById('limit');
const inpImgWidth = document.getElementById('imgWidth');
const inpRows = document.getElementById('rows');
const rngZoom = document.getElementById('zoom');
const info = document.getElementById('info');

const TOP_CTRL_H = 36; // first row reserved for view control
const ROW_H = 18;      // row height per file line
const ROW_GAP = 2;     // gap between rows

// Media categorization by extension
const imageExt = new Set(['jpg','jpeg','png','gif','webp','bmp','tiff','tif','heic','heif']);
const audioExt = new Set(['mp3','m4a','aac','flac','ogg','opus','wav','aiff']);
const videoExt = new Set(['mp4','mov','mkv','webm','avi','m4v']);

/** @typedef {{
 *  name: string,
 *  path: string,
 *  type: 'image'|'audio'|'video'|'unknown',
 *  startMs: number, // epoch ms
 *  durationMs: number, // 0 for images/unknown
 * }} TimelineItem
 */

/** @type {TimelineItem[]} */
let items = [];

const state = {
  viewStartMs: Date.now() - 12 * 3600_000, // default window around now
  msPerPx: 60_000, // 1 minute per pixel
  dragging: false,
  dragStartX: 0,
  dragStartViewStartMs: 0,
  dpr: window.devicePixelRatio || 1,
  maxRows: 300,
  imgBarPx: 16, // fixed image width in px (at current scale)
};

function nowMs() { return Date.now(); }

function extOf(name) {
  const i = name.lastIndexOf('.');
  return i >= 0 ? name.slice(i+1).toLowerCase() : '';
}

function classifyByName(name) {
  const e = extOf(name);
  if (imageExt.has(e)) return 'image';
  if (audioExt.has(e)) return 'audio';
  if (videoExt.has(e)) return 'video';
  return 'unknown';
}

async function* walkDirectory(dirHandle, recursive = true, basePath = '') {
  for await (const [name, entry] of dirHandle.entries()) {
    const path = basePath ? `${basePath}/${name}` : name;
    if (entry.kind === 'file') {
      yield { handle: entry, path };
    } else if (entry.kind === 'directory' && recursive) {
      yield* walkDirectory(entry, recursive, path);
    }
  }
}

async function getFileInfo(fileHandle, path) {
  const file = await fileHandle.getFile();
  const name = file.name;
  const type = classifyByName(name);
  const fallbackStart = file.lastModified; // fallback to file modified time

  let startMs = fallbackStart;
  let durationMs = 0;

  try {
    if (type === 'image') {
      // Attempt EXIF DateTimeOriginal
      const exif = await exifr.parse(file, { tiff: true, ifd0: true, exif: true });
      const dt = exif?.DateTimeOriginal || exif?.CreateDate || exif?.ModifyDate;
      if (dt instanceof Date && !Number.isNaN(dt.getTime())) {
        startMs = dt.getTime();
      }
      durationMs = 0; // fixed size for images
    } else if (type === 'audio') {
      durationMs = await getMediaDuration(file, 'audio');
      // Creation time metadata cross-browser is messy; fallback is fine for now
    } else if (type === 'video') {
      durationMs = await getMediaDuration(file, 'video');
      // Creation time metadata for video requires container parsing; fallback for now
    } else {
      // unknown: leave duration 0, start fallback
    }
  } catch (e) {
    // Swallow per-file errors; keep fallbacks
    console.warn('Metadata error for', name, e);
  }

  return /** @type {TimelineItem} */({ name, path, type, startMs, durationMs });
}

function getMediaDuration(file, kind) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement(kind); // 'audio' or 'video'
    el.preload = 'metadata';
    const cleanup = () => {
      URL.revokeObjectURL(url);
      el.remove();
    };
    const done = (sec) => {
      cleanup();
      // guard against Infinity/NaN
      if (!isFinite(sec) || sec < 0) return resolve(0);
      resolve(sec * 1000);
    };
    el.onloadedmetadata = () => done(el.duration);
    el.onerror = () => done(0);
    // timeout in case some codecs cannot load
    const to = setTimeout(() => { done(0); }, 8000);
    el.onloadedmetadata = () => { clearTimeout(to); done(el.duration); };
    el.onerror = () => { clearTimeout(to); done(0); };
    el.src = url;
    // not adding to DOM; media elements can load metadata off-DOM
  });
}

function fitViewToItems() {
  if (items.length === 0) return;
  const minStart = items.reduce((m, it) => Math.min(m, it.startMs), Infinity);
  const maxEnd = items.reduce((m, it) => Math.max(m, it.durationMs ? (it.startMs + it.durationMs) : it.startMs), -Infinity);
  if (!isFinite(minStart) || !isFinite(maxEnd)) return;

  const margin = 0.05 * (maxEnd - minStart || 86_400_000);
  const viewStart = minStart - margin;
  const viewSpan = (maxEnd - minStart || 86_400_000) + 2 * margin;

  const cssW = canvas.clientWidth || 1200;
  state.msPerPx = viewSpan / cssW;
  state.viewStartMs = viewStart;
}

function setZoomFromSlider(val) {
  // slider value -6..6 maps exponentially to scale (so zooming feels natural)
  // base msPerPx ~ 60_000 at 0, halve/double per unit
  const base = 60_000; // 1 min/px
  const factor = Math.pow(2, -val); // increase val => zoom in (smaller ms/px)
  state.msPerPx = base * factor;
  render();
}

function resizeCanvas() {
  const dpr = state.dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || window.innerWidth;
  const cssH = canvas.clientHeight || (window.innerHeight - 140);
  canvas.width = Math.max(1, Math.floor(cssW * dpr));
  canvas.height = Math.max(1, Math.floor(cssH * dpr));
  render();
}

function drawGridAndTicks() {
  const { width, height } = canvas;
  const dpr = state.dpr;
  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width / dpr, height / dpr);

  // Top control background
  ctx.fillStyle = '#141824';
  ctx.fillRect(0, 0, width / dpr, TOP_CTRL_H);

  // Horizontal grid lines
  ctx.strokeStyle = '#2a2e39';
  ctx.lineWidth = 1;

  const rows = Math.min(state.maxRows, items.length);
  for (let r = 0; r <= rows; r++) {
    const y = TOP_CTRL_H + r * (ROW_H + ROW_GAP);
    ctx.beginPath();
    ctx.moveTo(0, y + 0.5);
    ctx.lineTo(width / dpr, y + 0.5);
    ctx.stroke();
  }

  // Time axis ticks at the top
  const pxW = width / dpr;
  const msPerPx = state.msPerPx;
  const viewStart = state.viewStartMs;

  // Choose tick every N minutes/hours/days based on scale
  const ms = [
    60_000, 5*60_000, 15*60_000, 30*60_000, // minutes
    60*60_000, 2*60*60_000, 6*60*60_000, 12*60*60_000, // hours
    24*60*60_000, 7*24*60*60_000 // days
  ];
  const targetPx = 120;
  let tickMs = ms[0];
  for (const candidate of ms) {
    if (candidate / msPerPx >= targetPx) { tickMs = candidate; break; }
    tickMs = candidate;
  }

  // find first tick >= viewStart aligned to tickMs
  const firstTick = Math.ceil(viewStart / tickMs) * tickMs;
  ctx.fillStyle = '#cbd5e1';
  ctx.strokeStyle = '#3b4152';

  for (let t = firstTick; ; t += tickMs) {
    const x = (t - viewStart) / msPerPx;
    if (x > pxW + 40) break;
    if (x >= -40) {
      // tick
      ctx.beginPath();
      ctx.moveTo(x + 0.5, 0);
      ctx.lineTo(x + 0.5, TOP_CTRL_H);
      ctx.stroke();
      // label
      ctx.fillStyle = '#9aa0a6';
      ctx.font = '12px system-ui';
      const d = new Date(t);
      const label = formatTickLabel(d, tickMs);
      ctx.fillText(label, x + 4, 12);
      ctx.fillStyle = '#cbd5e1';
    }
    if (t - viewStart > pxW * msPerPx) break;
  }

  ctx.restore();
}

function formatTickLabel(d, tickMs) {
  const y = d.getFullYear();
  const M = String(d.getMonth()+1).padStart(2,'0');
  const D = String(d.getDate()).padStart(2,'0');
  const h = String(d.getHours()).padStart(2,'0');
  const m = String(d.getMinutes()).padStart(2,'0');
  if (tickMs >= 24*60*60_000) return `${y}-${M}-${D}`;
  if (tickMs >= 60*60_000) return `${M}-${D} ${h}:00`;
  return `${h}:${m}`;
}

function renderBars() {
  const dpr = state.dpr;
  ctx.save();
  ctx.scale(dpr, dpr);

  const msPerPx = state.msPerPx;
  const viewStart = state.viewStartMs;

  const rows = Math.min(state.maxRows, items.length);
  for (let i = 0; i < rows; i++) {
    const it = items[i];
    const y = TOP_CTRL_H + i * (ROW_H + ROW_GAP) + 1;
    const x = (it.startMs - viewStart) / msPerPx;
    const w = it.type === 'image' ? state.imgBarPx : Math.max(2, (it.durationMs || 0) / msPerPx);

    // choose color by type
    ctx.fillStyle = it.type === 'image' ? '#8ab4f8'
                  : it.type === 'audio' ? '#34d399'
                  : it.type === 'video' ? '#f59e0b'
                  : '#f87171';

    // draw bar
    ctx.fillRect(Math.floor(x), y, Math.ceil(w), ROW_H - 2);

    // label (file name) if there is room
    if (w > 40) {
      ctx.fillStyle = '#0d0f14';
      ctx.font = '12px system-ui';
      ctx.fillText(it.name, Math.floor(x) + 4, y + 13);
    }
  }

  ctx.restore();
}

function render() {
  drawGridAndTicks();
  renderBars();
  updateInfo();
}

function updateInfo() {
  const spanMs = (canvas.clientWidth || 1) * state.msPerPx;
  const start = new Date(state.viewStartMs);
  const end = new Date(state.viewStartMs + spanMs);
  info.textContent = `${items.length} items | View: ${start.toLocaleString()} → ${end.toLocaleString()} | ${Math.round(state.msPerPx)} ms/px`;
}

// Interaction: pan and zoom
canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const y = e.clientY - rect.top;
  if (y <= TOP_CTRL_H) {
    state.dragging = true;
    state.dragStartX = e.clientX;
    state.dragStartViewStartMs = state.viewStartMs;
  }
});

window.addEventListener('mouseup', () => { state.dragging = false; });
window.addEventListener('mousemove', (e) => {
  if (!state.dragging) return;
  const dx = e.clientX - state.dragStartX; // pixels
  const dt = dx * state.msPerPx; // ms
  state.viewStartMs = state.dragStartViewStartMs - dt;
  render();
});

canvas.addEventListener('wheel', (e) => {
  const rect = canvas.getBoundingClientRect();
  const y = e.clientY - rect.top;
  const shouldZoom = e.ctrlKey || e.metaKey || y <= TOP_CTRL_H;
  if (!shouldZoom) return; // allow page scroll otherwise
  e.preventDefault();
  const zoomFactor = Math.exp(-e.deltaY * 0.0015); // smooth zoom
  // Zoom around mouse x
  const mouseX = e.clientX - rect.left;
  const pivotMs = state.viewStartMs + mouseX * state.msPerPx;
  const newMsPerPx = Math.max(1, Math.min(30 * 24 * 3600_000, state.msPerPx / zoomFactor));
  const newViewStart = pivotMs - mouseX * newMsPerPx;
  state.msPerPx = newMsPerPx;
  state.viewStartMs = newViewStart;
  // update slider approx
  rngZoom.value = String(Math.log2(60_000 / state.msPerPx));
  render();
}, { passive: false });

rngZoom.addEventListener('input', () => {
  const val = Number(rngZoom.value);
  setZoomFromSlider(val);
});

inpImgWidth.addEventListener('input', () => {
  state.imgBarPx = Math.max(2, Number(inpImgWidth.value) || 16);
  render();
});

inpRows.addEventListener('input', () => {
  state.maxRows = Math.max(10, Number(inpRows.value) || 300);
  render();
});

window.addEventListener('resize', resizeCanvas);

btnPickDir.addEventListener('click', async () => {
  try {
    const handle = await showDirectoryPicker({ mode: 'read' });
    await loadDirectory(handle, chkRecursive.checked, Number(inpLimit.value) || 500);
  } catch (e) {
    if (e?.name !== 'AbortError') console.warn('Directory picking cancelled or failed', e);
  }
});

async function loadDirectory(dirHandle, recursive, limit) {
  items = [];
  render();
  const max = Math.max(1, limit);
  let count = 0;

  const queue = [];
  for await (const entry of walkDirectory(dirHandle, recursive)) {
    if (count >= max) break;
    queue.push(entry);
    count++;
  }

  const results = [];
  const concurrency = 4;
  let idx = 0;
  async function worker() {
    while (idx < queue.length) {
      const i = idx++;
      const { handle, path } = queue[i];
      try {
        const info = await getFileInfo(handle, path);
        results.push(info);
      } catch (e) {
        console.warn('Failed to process', path, e);
      }
      if (results.length % 25 === 0) {
        infoEl(`${results.length}/${queue.length} processed…`);
        render();
      }
    }
  }
  const workers = Array.from({ length: Math.min(concurrency, queue.length) }, () => worker());
  await Promise.all(workers);

  results.sort((a,b) => a.startMs - b.startMs);
  items = results;
  fitViewToItems();
  render();
}

function infoEl(text) {
  info.textContent = text;
}

// Initial sizing and render
resizeCanvas();
render();

