const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000"
  : "https://nz-permits.onrender.com";

function getDeviceId() {
  let id = localStorage.getItem("nz_permits_device_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("nz_permits_device_id", id);
  }
  return id;
}
const DEVICE_ID = getDeviceId();

// Element references
const form = document.getElementById("load-form");
const submitBtn = document.getElementById("submit-btn");
const resetBtn = document.getElementById("reset-btn");
const resultCard = document.getElementById("result-card");
const resultContent = document.getElementById("result-content");
const routeCard = document.getElementById("route-card");
const routeInput = document.getElementById("route-input");
const routeInputToggle = document.getElementById("route-input-toggle");
const routeOptions = document.getElementById("route-options");
const checkRouteBtn = document.getElementById("check-route-btn");
const routeResultCard = document.getElementById("route-result-card");
const routeResultContent = document.getElementById("route-result-content");
const saveJobCard = document.getElementById("save-job-card");
const saveJobBtn = document.getElementById("save-job-btn");
const errorCard = document.getElementById("error-card");
const errorMessage = document.getElementById("error-message");
const savedJobsDropdown = document.getElementById("saved-jobs-dropdown");
const savedJobsToggle = document.getElementById("saved-jobs-toggle");
const savedJobsCountLabel = document.getElementById("saved-jobs-count-label");
const savedJobsPanel = document.getElementById("saved-jobs-panel");
const savedJobsList = document.getElementById("saved-jobs-list");
const saveModal = document.getElementById("save-modal");
const saveJobNameInput = document.getElementById("save-job-name");
const saveCancelBtn = document.getElementById("save-cancel-btn");
const saveConfirmBtn = document.getElementById("save-confirm-btn");

// State
let currentLoad = null;
let currentClassification = null;
let currentRouteCheck = null;
let allRoutes = [];           // [{id, label, via, distance_km}]
let selectedRouteId = null;   // null = custom text route; string = picked pre-defined route

// ===== Init =====
async function init() {
  await loadRoutes();
  await refreshSavedJobs();
}
init();

async function loadRoutes() {
  try {
    const r = await fetch(`${API_BASE}/routes`);
    if (!r.ok) throw new Error("Failed to load routes");
    allRoutes = await r.json();
  } catch (err) {
    allRoutes = [];
  }
}

// ===== Saved jobs dropdown =====
async function refreshSavedJobs() {
  try {
    const r = await fetch(`${API_BASE}/jobs?device_id=${encodeURIComponent(DEVICE_ID)}`);
    if (!r.ok) throw new Error("Failed to load saved jobs");
    const jobs = await r.json();
    renderSavedJobs(jobs);
  } catch (err) {
    savedJobsDropdown.hidden = true;
  }
}

function renderSavedJobs(jobs) {
  if (jobs.length === 0) {
    savedJobsDropdown.hidden = true;
    savedJobsPanel.hidden = true;
    savedJobsToggle.classList.remove("open");
    return;
  }
  savedJobsDropdown.hidden = false;
  savedJobsCountLabel.textContent = `Saved jobs (${jobs.length})`;
  savedJobsList.innerHTML = jobs.map(j => {
    const created = new Date(j.created_at);
    const dateStr = created.toLocaleDateString("en-NZ", { day: "numeric", month: "short" });
    const li = j.load_input;
    const meta = `${li.width_m}×${li.height_m}×${li.length_m}m · ${(li.weight_kg / 1000).toFixed(1)}t · ${dateStr}`;
    return `
      <div class="saved-job" data-job-id="${j.id}">
        <div class="saved-job-info">
          <div class="saved-job-name">${escapeHtml(j.name)}</div>
          <div class="saved-job-meta">${escapeHtml(meta)}</div>
        </div>
        <div class="saved-job-actions">
          <button type="button" class="secondary load-btn" data-job-id="${j.id}">Load</button>
          <button type="button" class="delete-btn" data-job-id="${j.id}">×</button>
        </div>
      </div>
    `;
  }).join("");
  savedJobsList.querySelectorAll(".load-btn").forEach(btn => {
    btn.addEventListener("click", () => { loadJob(btn.dataset.jobId); closeSavedJobsPanel(); });
  });
  savedJobsList.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", (e) => { e.stopPropagation(); deleteJob(btn.dataset.jobId); });
  });
}

savedJobsToggle.addEventListener("click", (e) => {
  e.stopPropagation();
  const isOpen = !savedJobsPanel.hidden;
  if (isOpen) closeSavedJobsPanel();
  else {
    savedJobsPanel.hidden = false;
    savedJobsToggle.classList.add("open");
  }
});

document.addEventListener("click", (e) => {
  if (!savedJobsDropdown.contains(e.target) && !savedJobsPanel.hidden) closeSavedJobsPanel();
});

function closeSavedJobsPanel() {
  savedJobsPanel.hidden = true;
  savedJobsToggle.classList.remove("open");
}

async function loadJob(jobId) {
  hideError();
  try {
    const r = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!r.ok) throw new Error("Failed to load job");
    const job = await r.json();
    const li = job.load_input;
    document.getElementById("width").value = li.width_m;
    document.getElementById("height").value = li.height_m;
    document.getElementById("length").value = li.length_m;
    if (li.weight_kg % 1000 === 0 && li.weight_kg >= 1000) {
      document.getElementById("weight").value = li.weight_kg / 1000;
      document.getElementById("weight-unit").value = "t";
    } else {
      document.getElementById("weight").value = li.weight_kg;
      document.getElementById("weight-unit").value = "kg";
    }
    document.getElementById("indivisible").checked = li.indivisible !== false;
    currentLoad = li;
    currentClassification = job.classification;
    currentRouteCheck = job.route_check;
    renderClassification(job.classification);
    routeCard.hidden = false;
    if (job.route_check) {
      renderRouteCheck(job.route_check);
      if (job.route_check.route_id) {
        const r = allRoutes.find(x => x.id === job.route_check.route_id);
        if (r) {
          routeInput.value = r.label;
          selectedRouteId = r.id;
        } else {
          routeInput.value = job.route_check.route_label || "";
          selectedRouteId = null;
        }
      } else {
        routeInput.value = job.route_check.route_label || "";
        selectedRouteId = null;
      }
    } else {
      routeResultCard.hidden = true;
      routeInput.value = "";
      selectedRouteId = null;
    }
    saveJobCard.hidden = false;
  } catch (err) {
    showError(err.message || "Failed to load job");
  }
}

async function deleteJob(jobId) {
  if (!confirm("Delete this job?")) return;
  try {
    const r = await fetch(`${API_BASE}/jobs/${jobId}?device_id=${encodeURIComponent(DEVICE_ID)}`, { method: "DELETE" });
    if (!r.ok) throw new Error("Failed to delete job");
    await refreshSavedJobs();
  } catch (err) {
    showError(err.message || "Failed to delete job");
  }
}

// ===== Route combobox =====
function openRouteOptions(filter = "") {
  const f = (filter || "").trim().toLowerCase();
  const matches = f
    ? allRoutes.filter(r => r.label.toLowerCase().includes(f) || (r.via || "").toLowerCase().includes(f))
    : allRoutes.slice();

  let html = "";
  if (matches.length > 0) {
    html += matches.map(r => `
      <li data-route-id="${r.id}" data-route-label="${escapeAttr(r.label)}">
        ${escapeHtml(r.label)}
        <span class="option-via">${escapeHtml(r.via || "")}</span>
      </li>
    `).join("");
  } else {
    html += `<li class="no-match">No common route matches — your text will be checked as a free-text route</li>`;
  }
  if (f) {
    html += `<li class="custom-option" data-route-id="" data-route-label="${escapeAttr(filter)}">Use what I typed: "${escapeHtml(filter)}"</li>`;
  }
  routeOptions.innerHTML = html;
  routeOptions.hidden = false;

  routeOptions.querySelectorAll("li[data-route-id]").forEach(li => {
    li.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const id = li.dataset.routeId;
      const label = li.dataset.routeLabel;
      routeInput.value = label;
      selectedRouteId = id || null;
      routeOptions.hidden = true;
    });
  });
}

function closeRouteOptions() {
  routeOptions.hidden = true;
}

routeInput.addEventListener("focus", () => openRouteOptions(routeInput.value));
routeInput.addEventListener("input", () => {
  // Once user types, they're going off-script — clear selectedRouteId
  selectedRouteId = null;
  openRouteOptions(routeInput.value);
});
routeInput.addEventListener("blur", () => {
  // Delay so mousedown on an option fires first
  setTimeout(closeRouteOptions, 120);
});
routeInputToggle.addEventListener("mousedown", (e) => {
  e.preventDefault();
  if (routeOptions.hidden) {
    routeInput.focus();
    openRouteOptions(routeInput.value);
  } else {
    closeRouteOptions();
  }
});

// ===== Classification flow =====
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  routeCard.hidden = true;
  routeResultCard.hidden = true;
  saveJobCard.hidden = true;
  submitBtn.disabled = true;
  submitBtn.textContent = "Checking...";

  const rawWeight = parseFloat(document.getElementById("weight").value);
  const unit = document.getElementById("weight-unit").value;
  const weightKg = unit === "t" ? Math.round(rawWeight * 1000) : Math.round(rawWeight);

  const payload = {
    width_m: parseFloat(document.getElementById("width").value),
    height_m: parseFloat(document.getElementById("height").value),
    length_m: parseFloat(document.getElementById("length").value),
    weight_kg: weightKg,
    indivisible: document.getElementById("indivisible").checked,
  };

  try {
    const r = await fetch(`${API_BASE}/classify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const errBody = await r.json().catch(() => ({}));
      throw new Error(errBody.detail?.[0]?.msg || `HTTP ${r.status}`);
    }
    const data = await r.json();
    currentLoad = payload;
    currentClassification = data;
    currentRouteCheck = null;
    renderClassification(data);
    routeCard.hidden = false;
    saveJobCard.hidden = false;
    routeInput.value = "";
    selectedRouteId = null;
  } catch (err) {
    showError(err.message || "Something went wrong");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Classify load";
  }
});

// ===== Route check =====
checkRouteBtn.addEventListener("click", async () => {
  if (!currentLoad) { showError("Classify a load first."); return; }
  const text = routeInput.value.trim();
  if (!text) { showError("Type or pick a route."); return; }
  hideError();
  checkRouteBtn.disabled = true;
  checkRouteBtn.textContent = "Checking...";

  try {
    let data;
    if (selectedRouteId) {
      const r = await fetch(`${API_BASE}/check-route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...currentLoad, route_id: selectedRouteId }),
      });
      if (!r.ok) {
        const errBody = await r.json().catch(() => ({}));
        throw new Error(errBody.detail || `HTTP ${r.status}`);
      }
      data = await r.json();
    } else {
      const r = await fetch(`${API_BASE}/check-route-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...currentLoad, route_text: text }),
      });
      if (!r.ok) {
        const errBody = await r.json().catch(() => ({}));
        throw new Error(errBody.detail?.[0]?.msg || errBody.detail || `HTTP ${r.status}`);
      }
      data = await r.json();
    }
    currentRouteCheck = data;
    renderRouteCheck(data);
  } catch (err) {
    showError(err.message || "Route check failed");
  } finally {
    checkRouteBtn.disabled = false;
    checkRouteBtn.textContent = "Check route";
  }
});

// ===== Reset =====
resetBtn.addEventListener("click", () => {
  document.getElementById("width").value = 6.5;
  document.getElementById("height").value = 5.2;
  document.getElementById("length").value = 14.0;
  document.getElementById("weight").value = 28;
  document.getElementById("weight-unit").value = "t";
  document.getElementById("indivisible").checked = true;
  resultCard.hidden = true;
  routeCard.hidden = true;
  routeResultCard.hidden = true;
  saveJobCard.hidden = true;
  hideError();
  routeInput.value = "";
  selectedRouteId = null;
  currentLoad = null;
  currentClassification = null;
  currentRouteCheck = null;
});

// ===== Save job =====
saveJobBtn.addEventListener("click", () => {
  if (!currentLoad || !currentClassification) return;
  const li = currentLoad;
  const cat = currentClassification.category_label || "Load";
  const routeBit = currentRouteCheck ? ` — ${currentRouteCheck.route_label}` : "";
  const defaultName = `${li.width_m}×${li.height_m}×${li.length_m}m · ${(li.weight_kg / 1000).toFixed(1)}t · ${cat}${routeBit}`;
  saveJobNameInput.value = defaultName;
  saveModal.hidden = false;
  saveJobNameInput.focus();
  saveJobNameInput.select();
});

saveCancelBtn.addEventListener("click", () => { saveModal.hidden = true; });

saveConfirmBtn.addEventListener("click", async () => {
  const name = saveJobNameInput.value.trim();
  if (!name) { saveJobNameInput.focus(); return; }
  saveConfirmBtn.disabled = true;
  saveConfirmBtn.textContent = "Saving...";
  try {
    const r = await fetch(`${API_BASE}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_id: DEVICE_ID,
        name: name,
        load_input: currentLoad,
        classification: currentClassification,
        route_check: currentRouteCheck,
      }),
    });
    if (!r.ok) throw new Error("Failed to save job");
    saveModal.hidden = true;
    await refreshSavedJobs();
  } catch (err) {
    showError(err.message || "Failed to save job");
  } finally {
    saveConfirmBtn.disabled = false;
    saveConfirmBtn.textContent = "Save";
  }
});

saveJobNameInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") saveConfirmBtn.click();
  if (e.key === "Escape") saveCancelBtn.click();
});

// ===== Rendering =====
function renderClassification(data) {
  const pilots = formatPilots(data.pilots);
  resultContent.innerHTML = `
    <div class="status-banner badge-${data.permit_status}">
      ${escapeHtml(data.permit_status_label)}
    </div>
    <dl class="result-summary">
      <dt>Dimension category</dt>
      <dd>${escapeHtml(data.category_label)}</dd>
      <dt>Overdimension</dt>
      <dd>${data.overdimension ? "Yes" : "No"}</dd>
      <dt>Overweight</dt>
      <dd>${data.overweight ? "Yes" : "No"}</dd>
      <dt>Engineering assessment</dt>
      <dd>${data.requires_engineering_assessment ? "Yes — Cat 4B" : "No"}</dd>
      <dt>Pilots required</dt>
      <dd>${pilots}</dd>
    </dl>
    ${data.notes && data.notes.length > 0 ? `
      <div class="notes">
        <h3>Notes & requirements</h3>
        <ul>${data.notes.map(n => `<li>${escapeHtml(n)}</li>`).join("")}</ul>
      </div>
    ` : ""}
  `;
  resultCard.hidden = false;
}

function renderRouteCheck(data) {
  const matchedKeywordsHtml = data.matched_keywords && data.matched_keywords.length > 0
    ? `<div class="matched-keywords">Matched: ${data.matched_keywords.map(k => `<code>${escapeHtml(k)}</code>`).join(" ")}</div>`
    : "";
  const issuesHtml = data.issues.length === 0
    ? `<div class="route-clear">✓ No known issues for this load on this route</div>`
    : `<div class="issue-list">
         ${data.issues.map(i => `
           <div class="issue severity-${i.severity}">
             <div class="issue-title">
               <span class="issue-severity-tag">${i.severity}</span>
               ${escapeHtml(i.title)}
             </div>
             <div class="issue-description">${escapeHtml(i.description)}</div>
           </div>
         `).join("")}
       </div>`;
  routeResultContent.innerHTML = `
    <div class="route-summary">
      <span>${escapeHtml(data.route_label)}</span>
      ${data.distance_km ? `<span>${data.distance_km} km</span>` : ""}
      <span>${escapeHtml(data.typical_via)}</span>
    </div>
    <div class="route-summary">
      <span>${data.summary.blockers} blocker${data.summary.blockers === 1 ? '' : 's'}</span>
      <span>${data.summary.warnings} warning${data.summary.warnings === 1 ? '' : 's'}</span>
      <span>${data.summary.info} info</span>
    </div>
    ${matchedKeywordsHtml}
    ${issuesHtml}
  `;
  routeResultCard.hidden = false;
}

function formatPilots(pilots) {
  if (pilots.front_count === 0 && pilots.rear_count === 0) return "None";
  const parts = [];
  if (pilots.front_count > 0) {
    const cls = pilots.front_class.replace("_", " ").toUpperCase();
    parts.push(`${pilots.front_count} × ${cls} front`);
  }
  if (pilots.rear_count > 0) {
    const cls = pilots.rear_class.replace("_", " ").toUpperCase();
    parts.push(`${pilots.rear_count} × ${cls} rear`);
  }
  return parts.join(", ");
}

function hideError() { errorCard.hidden = true; }
function showError(message) {
  errorMessage.textContent = message;
  errorCard.hidden = false;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}
function escapeAttr(text) {
  return String(text).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

console.log("NZ Heavy Haulage Permits — frontend ready (combobox route input)");
console.log("Device ID:", DEVICE_ID);
