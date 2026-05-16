const state = {
  agents: [],
  voices: [],
  activeAgent: "orchestrator",
  micOn: false,
};

const panel = document.getElementById("panel");
const dockButton = document.getElementById("dockButton");
const statusDot = document.getElementById("statusDot");
const bridgeStatus = document.getElementById("bridgeStatus");
const conversation = document.getElementById("conversation");
const proofDrawer = document.getElementById("proofDrawer");
const agentSelect = document.getElementById("agentSelect");
const agentName = document.getElementById("agentName");
const voiceSelect = document.getElementById("voiceSelect");
const providerBadge = document.getElementById("providerBadge");
const authGate = document.getElementById("authGate");
const authContinue = document.getElementById("authContinue");

function unlockSession() {
  sessionStorage.setItem("hermesLocalSession", "connected");
  document.body.classList.remove("session-locked");
  authGate.hidden = true;
  document.getElementById("toolInput").focus();
}

function setupAuthGate() {
  if (sessionStorage.getItem("hermesLocalSession") === "connected") {
    document.body.classList.remove("session-locked");
    authGate.hidden = true;
    return;
  }
  authGate.hidden = false;
  authContinue.addEventListener("click", unlockSession);
}

function rememberPanel() {
  const rect = panel.getBoundingClientRect();
  localStorage.setItem("hermesPanel", JSON.stringify({
    left: rect.left,
    top: rect.top,
    width: rect.width,
    height: rect.height,
  }));
}

function clampPanel() {
  if (window.matchMedia("(max-width: 520px)").matches) {
    panel.style.left = "";
    panel.style.top = "";
    panel.style.right = "";
    panel.style.width = "";
    panel.style.height = "";
    return;
  }
  const margin = 8;
  const rect = panel.getBoundingClientRect();
  const width = Math.min(Math.max(340, rect.width), window.innerWidth - margin * 2);
  const height = Math.min(Math.max(520, rect.height), window.innerHeight - margin * 2);
  const left = Math.min(Math.max(margin, rect.left), Math.max(margin, window.innerWidth - width - margin));
  const top = Math.min(Math.max(margin, rect.top), Math.max(margin, window.innerHeight - height - margin));
  panel.style.left = `${left}px`;
  panel.style.top = `${top}px`;
  panel.style.right = "auto";
  panel.style.width = `${width}px`;
  panel.style.height = `${height}px`;
}

function resetPanelPosition() {
  panel.style.left = "";
  panel.style.top = "";
  panel.style.right = "";
  panel.style.width = "";
  panel.style.height = "";
  localStorage.removeItem("hermesPanel");
  clampPanel();
}

function restorePanel() {
  const saved = JSON.parse(localStorage.getItem("hermesPanel") || "null");
  if (!saved) return;
  panel.style.left = `${saved.left}px`;
  panel.style.top = `${saved.top}px`;
  panel.style.right = "auto";
  panel.style.width = `${Math.max(340, saved.width)}px`;
  panel.style.height = `${Math.max(520, saved.height)}px`;
  clampPanel();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

function addMessage(text, type = "system") {
  const item = document.createElement("div");
  item.className = `message ${type}`;
  item.textContent = text;
  conversation.appendChild(item);
  conversation.scrollTop = conversation.scrollHeight;
}

function showProof(payload) {
  proofDrawer.textContent = JSON.stringify(payload, null, 2);
}

function setBridge(ok, text) {
  statusDot.classList.toggle("ok", ok);
  statusDot.classList.toggle("bad", !ok);
  bridgeStatus.textContent = text;
}

async function checkHealth() {
  try {
    const payload = await api("/health");
    setBridge(true, `localhost ${payload.version}`);
    showProof(payload);
    return payload;
  } catch (error) {
    setBridge(false, "bridge offline");
    showProof({error: error.message});
    return null;
  }
}

async function loadVoices() {
  const payload = await api("/api/voices/azure/en");
  state.voices = payload.voices;
  voiceSelect.innerHTML = "";
  for (const voice of state.voices) {
    const option = document.createElement("option");
    option.value = voice.short_name;
    option.textContent = `${voice.short_name} (${voice.gender})`;
    voiceSelect.appendChild(option);
  }
}

async function loadAgents() {
  const payload = await api("/api/agents");
  state.agents = payload.agents;
  agentSelect.innerHTML = "";
  for (const agent of state.agents) {
    const option = document.createElement("option");
    option.value = agent.id;
    option.textContent = agent.display_name;
    agentSelect.appendChild(option);
  }
  selectAgent(state.activeAgent);
}

function selectAgent(id) {
  const agent = state.agents.find((entry) => entry.id === id) || state.agents[0];
  if (!agent) return;
  state.activeAgent = agent.id;
  agentSelect.value = agent.id;
  agentName.value = agent.display_name;
  voiceSelect.value = agent.voice;
  providerBadge.textContent = agent.provider || "local";
}

async function saveActiveAgent() {
  const agent = state.agents.find((entry) => entry.id === state.activeAgent);
  if (!agent) return;
  agent.display_name = agentName.value.trim() || agent.display_name;
  agent.voice = voiceSelect.value;
  await api("/api/agents", {method: "POST", body: JSON.stringify({agents: state.agents})});
  await loadAgents();
  addMessage(`${agent.display_name} voice assignment saved as ${agent.voice}.`);
}

async function runQuickAction(action) {
  const map = {
    "bridge.actions": () => api("/api/actions"),
    "hermes.proof_mcp": () => api("/api/hermes/proof-mcp"),
    "slice.export_preflight": () => api("/api/slice/export-preflight", {method: "POST", body: "{}"}),
    "proof.recent": () => api("/api/proof/recent"),
    "orca.version": () => api("/api/orca/version", {method: "POST", body: "{}"}),
    "slice.dry_run": () => api("/api/slice/dry-run", {method: "POST", body: "{}"}),
  };
  const payload = await map[action]();
  showProof(payload);
  addMessage(`Tool ${action} -> ${payload.status || "ok"}`);
}

function setupDragging() {
  const handle = document.getElementById("dragHandle");
  let drag = null;
  handle.addEventListener("pointerdown", (event) => {
    const rect = panel.getBoundingClientRect();
    drag = {x: event.clientX - rect.left, y: event.clientY - rect.top};
    handle.setPointerCapture(event.pointerId);
  });
  handle.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const left = Math.min(window.innerWidth - 80, Math.max(0, event.clientX - drag.x));
    const top = Math.min(window.innerHeight - 56, Math.max(0, event.clientY - drag.y));
    panel.style.left = `${left}px`;
    panel.style.top = `${top}px`;
    panel.style.right = "auto";
  });
  handle.addEventListener("pointerup", () => {
    drag = null;
    rememberPanel();
  });
  panel.addEventListener("mouseup", rememberPanel);
}

document.getElementById("collapseButton").addEventListener("click", () => {
  panel.hidden = true;
  dockButton.hidden = false;
  document.getElementById("collapseButton").setAttribute("aria-expanded", "false");
  dockButton.setAttribute("aria-expanded", "false");
  dockButton.focus();
});

dockButton.addEventListener("click", () => {
  panel.hidden = false;
  dockButton.hidden = true;
  document.getElementById("collapseButton").setAttribute("aria-expanded", "true");
  dockButton.setAttribute("aria-expanded", "true");
  document.getElementById("toolInput").focus();
});

document.getElementById("micButton").addEventListener("click", (event) => {
  state.micOn = !state.micOn;
  event.currentTarget.textContent = state.micOn ? "live" : "mic";
  event.currentTarget.setAttribute("aria-pressed", String(state.micOn));
  event.currentTarget.setAttribute("aria-label", state.micOn ? "Microphone live" : "Push to talk");
  event.currentTarget.title = state.micOn ? "Microphone live" : "Push to talk";
});

document.getElementById("stopButton").addEventListener("click", () => {
  addMessage("Speech stopped.");
});

document.getElementById("saveAgent").addEventListener("click", saveActiveAgent);
document.getElementById("refreshProof").addEventListener("click", async () => showProof(await api("/api/proof/recent")));
document.getElementById("resetPosition").addEventListener("click", resetPanelPosition);

agentSelect.addEventListener("change", (event) => selectAgent(event.target.value));

document.querySelectorAll(".quick-actions button").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      await runQuickAction(button.dataset.action);
    } catch (error) {
      addMessage(error.message);
      showProof({error: error.message});
    }
  });
});

document.getElementById("toolForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("toolInput");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  addMessage(message, "user");
  try {
    const payload = await api("/api/hermes-agent/tool-request", {method: "POST", body: JSON.stringify({message, agent: state.activeAgent})});
    addMessage(payload.reply);
    showProof(payload);
  } catch (error) {
    addMessage(error.message);
  }
});

setupAuthGate();
restorePanel();
setupDragging();
window.addEventListener("resize", clampPanel);
document.getElementById("dragHandle").addEventListener("keydown", (event) => {
  const step = event.shiftKey ? 32 : 8;
  const keys = {ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step]};
  if (!keys[event.key]) return;
  event.preventDefault();
  const rect = panel.getBoundingClientRect();
  panel.style.left = `${rect.left + keys[event.key][0]}px`;
  panel.style.top = `${rect.top + keys[event.key][1]}px`;
  panel.style.right = "auto";
  clampPanel();
  rememberPanel();
});
Promise.all([loadVoices(), loadAgents(), checkHealth()]).then(() => {
  addMessage("Hermes Agent tool bridge is ready. Run a tool ID like bridge.actions, hermes.proof_mcp, or slice.export_preflight.");
});
