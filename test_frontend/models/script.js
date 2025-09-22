const chatEl = document.getElementById('chat');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendText');
const recordBtn = document.getElementById('recordBtn');

function addMessage(content, fromUser = true) {
  const div = document.createElement('div');
  div.className = `msg ${fromUser ? 'user' : 'bot'}`;
  div.textContent = content;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

/* ---------- Texto ---------- */
sendBtn.addEventListener('click', async () => {
  const txt = textInput.value.trim();
  if (!txt) return;
  addMessage(txt, true);
  textInput.value = '';

  try {
    const resp = await fetch('http://127.0.0.1:8000/azusena_api/query/text', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query: txt})
    });
    const data = await resp.json();
    addMessage(data.response ?? JSON.stringify(data), false);
  } catch (e) {
    addMessage('Error al contactar el API', false);
  }
});

/* ---------- Voz ---------- */
let mediaRecorder;
let audioChunks = [];

recordBtn.addEventListener('click', async () => {
  if (recordBtn.dataset.recording === 'true') {
    mediaRecorder.stop();
    recordBtn.textContent = '🎤 Grabar';
    recordBtn.dataset.recording = 'false';
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, {type:'audio/webm'});
    const form = new FormData();
    form.append('audio_file', audioBlob, 'voice.webm');

    addMessage('[Grabación enviada]', true);

    try {
      const resp = await fetch('http://127.0.0.1:8000/azusena_api/query/voice', {
        method: 'POST',
        body: form
      });
      const data = await resp.json();
      addMessage(data.response ?? JSON.stringify(data), false);
    } catch (e) {
      addMessage('Error al contactar el API de voz', false);
    }
  };

  mediaRecorder.start();
  recordBtn.textContent = '⏹️ Detener';
  recordBtn.dataset.recording = 'true';
});
