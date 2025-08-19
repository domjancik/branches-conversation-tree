const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');
const player = document.getElementById('player');
const resultEl = document.getElementById('result');

let mediaRecorder;
let chunks = [];

function setStatus(text) { statusEl.textContent = text; }

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = 'audio/webm';
    mediaRecorder = new MediaRecorder(stream, { mimeType });
    chunks = [];

    mediaRecorder.ondataavailable = e => { if (e.data && e.data.size > 0) chunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: mimeType });
      const url = URL.createObjectURL(blob);
      player.src = url;
      await uploadAudio(blob);
    };

    mediaRecorder.start();
    startBtn.disabled = true;
    stopBtn.disabled = false;
    setStatus('Recording...');
  } catch (err) {
    console.error(err);
    alert('Microphone access failed: ' + err);
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    startBtn.disabled = false;
    stopBtn.disabled = true;
    setStatus('Processing...');
  }
}

async function uploadAudio(blob) {
  try {
    const form = new FormData();
    form.append('file', blob, 'recording.webm');

    const resp = await fetch('http://localhost:8000/process-audio', {
      method: 'POST',
      body: form,
    });

    const text = await resp.text();
    try {
      const obj = JSON.parse(text);
      resultEl.textContent = JSON.stringify(obj, null, 2);
    } catch (_) {
      resultEl.textContent = text;
    }
    setStatus('Done');
  } catch (err) {
    console.error(err);
    setStatus('Error: ' + err);
  }
}

startBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);
