const SESSION_KEY = "fitagent_session_id";
const PROFILE_KEY = "fitagent_profile";

const profileForm = document.querySelector("#profile-form");
const profileStatus = document.querySelector("#profile-status");
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const chatLog = document.querySelector("#chat-log");
const progressView = document.querySelector("#progress-view");

let sessionId = localStorage.getItem(SESSION_KEY);

function listFromInput(formData, key) {
  const raw = formData.get(key);
  if (!raw) return [];
  return raw.split(",").map((item) => item.trim()).filter(Boolean);
}

function nullableNumber(value) {
  return value === "" || value === null ? null : Number(value);
}

function setSession(id) {
  sessionId = id;
  localStorage.setItem(SESSION_KEY, id);
}

function renderProfile(profile, missingFields = []) {
  profileStatus.textContent = JSON.stringify({ session_id: sessionId, profile, missing_fields: missingFields }, null, 2);
}

function addMessage(role, content, category = "") {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.innerHTML = `<small>${role}${category ? ` · ${category}` : ""}</small>${escapeHtml(content)}`;
  chatLog.appendChild(item);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

async function loadSavedProfile() {
  const cached = localStorage.getItem(PROFILE_KEY);
  if (cached) renderProfile(JSON.parse(cached));
  if (!sessionId) return;
  const response = await fetch(`/api/profiles/${sessionId}`);
  if (response.ok) {
    const data = await response.json();
    renderProfile(data.profile, data.missing_fields);
    localStorage.setItem(PROFILE_KEY, JSON.stringify(data.profile));
  }
}

async function loadHistory() {
  if (!sessionId) return;
  const response = await fetch(`/api/conversations/${sessionId}`);
  if (!response.ok) return;
  const data = await response.json();
  chatLog.innerHTML = "";
  data.messages.forEach((message) => addMessage(message.role, message.content, message.category));
}

async function loadProgress() {
  if (!sessionId) return;
  const response = await fetch(`/api/progress/${sessionId}`);
  if (!response.ok) return;
  const data = await response.json();
  const latest = data.snapshots[data.snapshots.length - 1];
  progressView.textContent = JSON.stringify({
    summary: data.summary,
    latest_snapshot: latest || null,
    events: data.events,
  }, null, 2);
}

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(profileForm);
  const payload = {
    session_id: sessionId,
    age: nullableNumber(formData.get("age")),
    sex: formData.get("sex") || null,
    height_cm: nullableNumber(formData.get("height_cm")),
    weight_kg: nullableNumber(formData.get("weight_kg")),
    activity_level: formData.get("activity_level") || null,
    fitness_level: formData.get("fitness_level") || null,
    current_steps: nullableNumber(formData.get("current_steps")),
    health_conditions: listFromInput(formData, "health_conditions"),
    dietary_restrictions: listFromInput(formData, "dietary_restrictions"),
    fitness_goals: listFromInput(formData, "fitness_goals"),
  };
  const response = await fetch("/api/profiles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    profileStatus.textContent = data.detail || "Could not save profile.";
    return;
  }
  setSession(data.session_id);
  localStorage.setItem(PROFILE_KEY, JSON.stringify(data.profile));
  renderProfile(data.profile, data.missing_fields);
  await loadProgress();
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  addMessage("user", message);
  chatInput.value = "";
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  const data = await response.json();
  if (!response.ok) {
    addMessage("assistant", data.detail || "FitAgent could not answer that request.", "error");
    return;
  }
  setSession(data.session_id);
  addMessage("assistant", data.response, data.category);
  await loadSavedProfile();
  await loadProgress();
});

document.querySelector("#refresh-progress").addEventListener("click", loadProgress);

document.querySelector("#reset-session").addEventListener("click", () => {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(PROFILE_KEY);
  sessionId = null;
  chatLog.innerHTML = "";
  profileStatus.textContent = "No profile saved yet.";
  progressView.textContent = "Submit a profile to start tracking progress.";
});

loadSavedProfile().then(loadHistory).then(loadProgress);
