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
    // Clear previous results
    resultEl.textContent = '';
    
    // Request microphone with specific constraints
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100
      } 
    });
    
    // Try different mime types for broader browser support
    let mimeType = 'audio/webm';
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = 'audio/mp4';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/wav';
      }
    }
    
    mediaRecorder = new MediaRecorder(stream, { mimeType });
    chunks = [];

    mediaRecorder.ondataavailable = e => { 
      if (e.data && e.data.size > 0) {
        chunks.push(e.data);
        console.log('Audio chunk received:', e.data.size, 'bytes');
      }
    };
    
    mediaRecorder.onstop = async () => {
      console.log('Recording stopped, total chunks:', chunks.length);
      const blob = new Blob(chunks, { type: mimeType });
      console.log('Final audio blob size:', blob.size, 'bytes');
      
      if (blob.size === 0) {
        setStatus('Error: No audio recorded');
        return;
      }
      
      const url = URL.createObjectURL(blob);
      player.src = url;
      await uploadAudio(blob);
    };

    mediaRecorder.onerror = (e) => {
      console.error('MediaRecorder error:', e.error);
      setStatus('Recording error: ' + e.error);
    };

    // Start recording with 1 second intervals
    mediaRecorder.start(1000);
    startBtn.disabled = true;
    stopBtn.disabled = false;
    setStatus('Recording... (speak now)');
    
    console.log('Recording started with mime type:', mimeType);
  } catch (err) {
    console.error('Recording failed:', err);
    alert('Microphone access failed: ' + err.message + '\n\nPlease ensure:\n1. Microphone is connected\n2. Browser has microphone permission\n3. Page is served over HTTPS or localhost');
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
    // Add timestamp to ensure unique filename and avoid server caching
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    form.append('file', blob, `recording_${timestamp}.webm`);

    const resp = await fetch('http://localhost:8000/process-audio', {
      method: 'POST',
      body: form,
      // Disable browser caching
      cache: 'no-cache',
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    });

    if (!resp.ok) {
      throw new Error(`Server error: ${resp.status} ${resp.statusText}`);
    }

    const text = await resp.text();
    try {
      const obj = JSON.parse(text);
      resultEl.textContent = JSON.stringify(obj, null, 2);
      console.log('Processing result:', obj);
    } catch (_) {
      resultEl.textContent = text;
      console.log('Raw server response:', text);
    }
    setStatus('Done');
  } catch (err) {
    console.error('Upload failed:', err);
    setStatus('Error: ' + err.message);
  }
}

startBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);
