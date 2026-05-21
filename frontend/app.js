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

const form = document.getElementById("load-form");
const submitBtn = document.getElementById("submit-btn");
const resetBtn = document.getElementById("reset-btn");
const resultCard = document.getElementById("result-card");
const resultContent = document.getElementById("result-content");
const routeCard = document.getElementById("route-card");
const routeSelect = document.getElementById("route-select");
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

let currentLoad = null;
let currentClassification = null;
let currentRouteCheck = null;

async function init() {
  await loadRoutes();
  await refreshSavedJobs();
}
init();

async function loadRoutes() {
  try {
    const r = await fetch(`${API_BASE}/routes`);
    if (!r.ok) throw new Error("Failed to load routes");
    const routes = await r.json();
    routeSelect.innerHTML = '<option value="">Select a route...</option>' +
      routes.map(rt => `<option value="${rt.id}">${escapeHtml(rt.label)}</option>`).join("");
  } catch (err) {
    routeSelect.innerHTML = '<option value="">Failed to load routes</option>';
  }
}

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

// Saved jobs dropdown toggle
savedJobsToggle.addEventListener("click", (e) => {
  e.stopPropagation();
  const isOpen = !savedJobsPanel.hidden;
  if (isOpen) {
    closeSavedJobsPanel();
  } else {
    savedJobsPanel.hidden = false;
    savedJobsToggle.classList.add("open");
  }
});

// Close dropdown if clicking outside
document.addEventListener("click", (e) => {
  if (!savedJobsDropdown.contains(e.target) && !savedJobsPanel.hidden) {
    closeSavedJobsPanel();
  }
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
      // Try to restore the route dropdown selection if route id matches
      if (job.route_check.route_id) {
        routeSelect.value = job.route_check.route_id;
      }
    } else {
      routeResultCard.hidden = true;
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
  } catch (err) {
    showError(err.message || "Something went wrong");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Classify load";
  }
});

checkRouteBtn.addEventListener("click", async () => {
  if (!currentLoad) { showError("Classify a load first."); return; }
  const routeId = routeSelect.value;
  if (!routeId) { showError("Pick a route."); return; }
  hideError();
  checkRouteBtn.disabled = true;
  checkRouteBtn.textContent = "Checking...";
  try {
    const r = await fetch(`${API_BASE}/check-route`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...currentLoad, route_id: routeId }),
    });
    if (!r.ok) {
      const errBody = await r.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP ${r.status}`);
    }
    const data = await r.json();
    currentRouteCheck = data;
    renderRouteCheck(data);
  } catch (err) {
    showError(err.message || "Route check failed");
  } finally {
    checkRouteBtn.disabled = false;
    checkRouteBtn.textContent = "Check route";
  }
});

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
  currentLoad = null;
  currentClassification = null;
  currentRouteCheck = null;
});

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
      <span>${data.distance_km} km</span>
      <span>Via: ${escapeHtml(data.typical_via)}</span>
    </div>
    <div class="route-summary">
      <span>${data.summary.blockers} blocker${data.summary.blockers === 1 ? '' : 's'}</span>
      <span>${data.summary.warnings} warning${data.summary.warnings === 1 ? '' : 's'}</span>
      <span>${data.summary.info} info</span>
    </div>
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

console.log("NZ Heavy Haulage Permits — frontend ready");
console.log("Device ID:", DEVICE_ID);
