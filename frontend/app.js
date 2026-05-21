const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "http://localhost:8000" : "https://nz-permits.onrender.com";

const form = document.getElementById("load-form");
const submitBtn = document.getElementById("submit-btn");
const resultCard = document.getElementById("result-card");
const resultContent = document.getElementById("result-content");
const errorCard = document.getElementById("error-card");
const errorMessage = document.getElementById("error-message");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideResult();
  hideError();
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
    renderResult(data);
  } catch (err) {
    showError(err.message || "Something went wrong");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Classify load";
  }
});

function renderResult(data) {
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

function hideResult() { resultCard.hidden = true; }
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

document.getElementById("reset-btn").addEventListener("click", () => {
  document.getElementById("width").value = 6.5;
  document.getElementById("height").value = 5.2;
  document.getElementById("length").value = 14.0;
  document.getElementById("weight").value = 28;
  document.getElementById("weight-unit").value = "t";
  document.getElementById("indivisible").checked = true;
  hideResult();
  hideError();
});

console.log("NZ Heavy Haulage Permits — frontend ready");
