const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000"
  : "https://nz-permits.onrender.com";

// Element references
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
const errorCard = document.getElementById("error-card");
const errorMessage = document.getElementById("error-message");

let currentLoad = null;
let routesLoaded = false;

// Load routes on page start
async function loadRoutes() {
  try {
    const response = await fetch(`${API_BASE}/routes`);
    if (!response.ok) throw new Error("Failed to load routes");
    const routes = await response.json();
    routeSelect.innerHTML = '<option value="">Select a route...</option>' +
      routes.map(r => `<option value="${r.id}">${escapeHtml(r.label)}</option>`).join("");
    routesLoaded = true;
  } catch (err) {
    routeSelect.innerHTML = '<option value="">Failed to load routes</option>';
  }
}
loadRoutes();

// Load classification submit
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  routeCard.hidden = true;
  routeResultCard.hidden = true;
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
    const response = await fetch(`${API_BASE}/classify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail?.[0]?.msg || `HTTP ${response.status}`);
    }
    const data = await response.json();
    currentLoad = payload;
    renderClassification(data);
    routeCard.hidden = false;
  } catch (err) {
    showError(err.message || "Something went wrong");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Classify load";
  }
});

// Route check button
checkRouteBtn.addEventListener("click", async () => {
  if (!currentLoad) {
    showError("Classify a load first.");
    return;
  }
  const routeId = routeSelect.value;
  if (!routeId) {
    showError("Pick a route.");
    return;
  }
  hideError();
  checkRouteBtn.disabled = true;
  checkRouteBtn.textContent = "Checking...";

  try {
    const response = await fetch(`${API_BASE}/check-route`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...currentLoad, route_id: routeId }),
    });
    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP ${response.status}`);
    }
    const data = await response.json();
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
  hideError();
  currentLoad = null;
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
    ${data.notes.length > 0 ? `
      <div class="notes">
        <h3>Notes & requirements</h3>
        <ul>
          ${data.notes.map(n => `<li>${escapeHtml(n)}</li>`).join("")}
        </ul>
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
  div.textContent = text;
  return div.innerHTML;
}

console.log("NZ Heavy Haulage Permits — frontend ready (with route check)");
