const $ = (id) => document.getElementById(id);

const recordBtn = $("btn-record");
const saveBtn = $("btn-save");
const deleteBtn = $("btn-delete");
const fileInput = $("file");
const statusEl = $("status");
const errorEl = $("error");
const textEl = $("text");
const savedEl = $("saved");
const player = $("player");
const recentEl = $("recent");

let mediaRecorder = null;
let chunks = [];
let recording = false;
let savedId = null;

function showError(message) {
  errorEl.textContent = message || "";
  errorEl.classList.toggle("hidden", !message);
}

function setSavedId(id) {
  savedId = id || null;
  deleteBtn.disabled = !savedId;
}

async function loadRecent() {
  const response = await fetch("/api/recent");
  const payload = await response.json();
  recentEl.innerHTML = "";
  const records = payload.records || [];
  if (!records.length) {
    recentEl.innerHTML = "<li class='muted'>محتوای فعالی نیست.</li>";
    return;
  }
  records.forEach((row) => {
    const item = document.createElement("li");
    const label = document.createElement("span");
    const preview = (row.text_body || "").slice(0, 80);
    const kind = row.content_kind_code === "VOICE" ? "صوت" : "متن";
    label.textContent = `#${row.id} [${kind}] ${preview}`;
    if (row.content_kind_code === "VOICE" && row.storage_key) {
      const clip = document.createElement("audio");
      clip.controls = true;
      clip.src = `/api/audio/${row.id}`;
      item.append(label, clip);
    } else {
      item.append(label);
    }
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "حذف";
    button.addEventListener("click", () => deleteById(row.id));
    item.append(button);
    recentEl.appendChild(item);
  });
}

async function deleteById(id) {
  showError("");
  const response = await fetch("/api/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  });
  const payload = await response.json();
  if (payload.status !== "success") {
    showError(payload.message || "حذف شکست خورد");
    return;
  }
  if (savedId === id) {
    setSavedId(null);
    savedEl.textContent = `حذف شد. شناسه ${id}`;
  }
  await loadRecent();
}

let lastAudio = null;

async function transcribeBlob(blob) {
  lastAudio = blob;
  showError("");
  statusEl.textContent = "در حال تبدیل صدا به متن…";
  saveBtn.disabled = true;
  const url = URL.createObjectURL(blob);
  player.src = url;
  player.classList.remove("hidden");
  const response = await fetch("/api/transcribe", {
    method: "POST",
    headers: { "Content-Type": blob.type || "audio/webm" },
    body: blob,
  });
  const payload = await response.json();
  if (payload.status !== "success") {
    throw new Error(payload.message || "تبدیل صدا شکست خورد");
  }
  textEl.value = payload.transcribed_text || "";
  saveBtn.disabled = !textEl.value.trim();
  statusEl.textContent = "تبدیل انجام شد.";
}

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  chunks = [];
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size) chunks.push(event.data);
  };
  mediaRecorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
    try {
      await transcribeBlob(blob);
    } catch (err) {
      showError(err.message);
      statusEl.textContent = "تبدیل انجام نشد.";
    }
  };
  mediaRecorder.start();
  recording = true;
  recordBtn.textContent = "توقف ضبط";
  statusEl.textContent = "در حال ضبط…";
}

function stopRecording() {
  if (mediaRecorder && recording) {
    mediaRecorder.stop();
  }
  recording = false;
  recordBtn.textContent = "شروع ضبط";
}

recordBtn.addEventListener("click", async () => {
  showError("");
  try {
    if (recording) {
      stopRecording();
      return;
    }
    await startRecording();
  } catch (err) {
    showError("دسترسی به میکروفون داده نشد.");
  }
});

fileInput.addEventListener("change", async () => {
  const file = fileInput.files && fileInput.files[0];
  if (!file) return;
  try {
    await transcribeBlob(file);
  } catch (err) {
    showError(err.message);
    statusEl.textContent = "تبدیل انجام نشد.";
  }
});

textEl.addEventListener("input", () => {
  saveBtn.disabled = !textEl.value.trim();
});

saveBtn.addEventListener("click", async () => {
  showError("");
  savedEl.textContent = "";
  if (!lastAudio) {
    showError("برای ذخیره، اول صوت را ضبط یا انتخاب کنید.");
    return;
  }
  const form = new FormData();
  form.append("text", textEl.value);
  form.append("audio", lastAudio, lastAudio.name || "recording.webm");
  const response = await fetch("/api/save", {
    method: "POST",
    body: form,
  });
  const payload = await response.json();
  if (payload.status !== "success") {
    showError(payload.message || "ذخیره شکست خورد");
    return;
  }
  savedEl.textContent = `ذخیره شد. شناسه ${payload.id} (${payload.content_kind === "VOICE" ? "متن و صوت" : "متن"})`;
  setSavedId(payload.id);
  await loadRecent();
});

deleteBtn.addEventListener("click", async () => {
  if (!savedId) return;
  await deleteById(savedId);
});

loadRecent();
