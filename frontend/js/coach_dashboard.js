// If you use tokens, set/get them here (or rely on cookies in Codespaces)
const API = {
  token: () => localStorage.getItem("token") || sessionStorage.getItem("token"),
  async request(path, { method="GET", headers={}, body=null } = {}) {
    const h = { ...headers };
    const t = API.token();
    if (t) h["Authorization"] = `Bearer ${t}`;
    const opts = { method, headers: h, credentials: "include" };

    if (body instanceof FormData) {
      opts.body = body; // browser sets multipart headers for us
    } else if (body) {
      h["Content-Type"] = h["Content-Type"] || "application/json";
      opts.body = JSON.stringify(body);
    }

    const res = await fetch(path, opts);
    if (!res.ok) {
      let msg;
      try { msg = await res.text(); } catch { msg = res.statusText; }
      throw new Error(`${res.status} ${msg}`);
    }

    const ct = res.headers.get("content-type") || "";
    return ct.includes("application/json") ? res.json() : res.text();
  }
};

// ---- Coach Profile ----
async function loadCoachProfile() {
  // If your backend route is different (e.g., /api/me), change it here.
  const p = await API.request("/api/coach/profile");

  const nameEl = document.getElementById("coachName");
  const emailEl = document.getElementById("coachEmail");
  const bioEl = document.getElementById("coachBio");
  const photoEl = document.getElementById("coachPhoto");

  if (nameEl) nameEl.textContent = p.name || "";
  if (emailEl) emailEl.textContent = p.email || "";
  if (bioEl) bioEl.textContent = p.bio || "";

  if (photoEl) {
    if (p.photo_url) {
      photoEl.src = p.photo_url;
      photoEl.style.display = "block";
    } else {
      photoEl.removeAttribute("src");
      photoEl.style.display = "none";
    }
  }

  // Pre-fill form for quick edit
  const form = document.getElementById("profileForm");
  if (form) {
    form.name.value = p.name || "";
    form.bio.value = p.bio || "";
  }
}

function bindProfileForm() {
  const form = document.getElementById("profileForm");
  const result = document.getElementById("profileResult");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    try {
      const data = await API.request("/api/coach/profile", { method: "POST", body: fd });
      if (result) { result.style.display = "block"; setTimeout(()=>result.style.display="none", 1500); }
      // update UI live
      await loadCoachProfile();
    } catch (err) {
      alert("Saving profile failed: " + err.message);
    }
  });
}

// ---- Coachees ----
async function loadCoachees() {
  const data = await API.request("/api/coachees");
  const el = document.getElementById("coachees");
  if (!el) return;
  el.innerHTML = (data.items || []).map(c => `
    <div class="list-group-item d-flex justify-content-between align-items-center">
      <span>${c.name}</span>
      <div class="d-flex gap-2">
        <a href="#" data-id="${c.id}" class="btn btn-sm btn-outline-secondary sessions">Sessions</a>
        <button data-id="${c.id}" class="btn btn-sm btn-danger remove">Remove</button>
      </div>
    </div>
  `).join("") || `<div class="text-muted">No coachees yet.</div>`;
}

function bindCoacheeActions() {
  // Add
  const addForm = document.getElementById("addForm");
  if (addForm) {
    addForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = new FormData(addForm).get("name");
      if (!name) return;
      await API.request(`/api/coachees?name=${encodeURIComponent(name)}`, { method: "POST" });
      addForm.reset();
      loadCoachees();
    });
  }

  // Remove / sessions
  document.addEventListener("click", async (e) => {
    const rm = e.target.closest(".remove");
    const ss = e.target.closest(".sessions");
    if (rm && rm.dataset.id) {
      e.preventDefault();
      await API.request(`/api/coachees/${rm.dataset.id}`, { method: "DELETE" });
      loadCoachees();
    }
    if (ss && ss.dataset.id) {
      e.preventDefault();
      const data = await API.request(`/api/coachees/${ss.dataset.id}/sessions`);
      alert(`Sessions for coachee ${ss.dataset.id}:\n` + JSON.stringify(data.items ?? [], null, 2));
    }
  });
}

// ---- Boot ----
document.addEventListener("DOMContentLoaded", async () => {
  bindProfileForm();
  bindCoacheeActions();

  try { await loadCoachProfile(); } catch (e) { console.warn("profile load:", e.message); }
  try { await loadCoachees(); } catch (e) { console.warn("coachees load:", e.message); }
});
