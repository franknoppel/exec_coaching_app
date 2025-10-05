// Extract coach_id from URL
const params = new URLSearchParams(window.location.search);
const coachId = params.get("coach_id");

const profileDiv = document.getElementById("coachProfile");
const coacheeList = document.getElementById("coacheeList");
const sessionList = document.getElementById("sessionList");
const editBtn = document.getElementById("editProfileBtn");
const saveBtn = document.getElementById("saveProfileBtn");

// -----------------------------------
// Load coach profile
// -----------------------------------
async function loadCoachProfile() {
  try {
    const res = await fetch(`/coach/${coachId}`);
    const coach = await res.json();

    profileDiv.innerHTML = `
      <div class="card p-3">
        <h5>${coach.firstname} ${coach.lastname}</h5>
        <p><strong>Email:</strong> ${coach.email}</p>
        <p><strong>Qualifications:</strong> ${coach.qualifications || "-"}</p>
        <p><strong>Profile:</strong> ${coach.profile || "-"}</p>
        <p><strong>Status:</strong> ${coach.status ? "Active" : "Inactive"}</p>
      </div>
    `;

    // Fill modal form
    document.getElementById("coach_firstname").value = coach.firstname;
    document.getElementById("coach_lastname").value = coach.lastname;
    document.getElementById("coach_email").value = coach.email;
    document.getElementById("coach_qualifications").value = coach.qualifications || "";
    document.getElementById("coach_profile").value = coach.profile || "";
    document.getElementById("coach_status").value = coach.status ? "true" : "false";

  } catch (err) {
    console.error("Profile load error:", err);
  }
}

// -----------------------------------
// Save coach profile edits
// -----------------------------------
saveBtn.addEventListener("click", async () => {
  const formData = new FormData();
  formData.append("coach_firstname", document.getElementById("coach_firstname").value);
  formData.append("coach_lastname", document.getElementById("coach_lastname").value);
  formData.append("coach_email", document.getElementById("coach_email").value);
  formData.append("coach_qualifications", document.getElementById("coach_qualifications").value);
  formData.append("coach_profile", document.getElementById("coach_profile").value);
  formData.append("coach_status", document.getElementById("coach_status").value);
  const photoFile = document.getElementById("coach_photo").files[0];
  if (photoFile) formData.append("coach_photo", photoFile);

  try {
    const res = await fetch(`/coach/${coachId}`, {
      method: "PUT",
      body: formData,
    });

    if (!res.ok) throw new Error("Failed to update profile");

    const data = await res.json();
    console.log("Profile updated:", data);
    alert("✅ Profile saved!");
    loadCoachProfile();

    const modal = bootstrap.Modal.getInstance(document.getElementById("profileModal"));
    modal.hide();
  } catch (err) {
    console.error(err);
    alert("❌ Error saving profile");
  }
});

// -----------------------------------
// Load coachees for this coach
// -----------------------------------
async function loadCoachees() {
  try {
    const res = await fetch(`/coach/${coachId}/coachees`);
    const coachees = await res.json();

    if (!coachees.length) {
      coacheeList.innerHTML = `<p class="text-muted">No coachees assigned yet.</p>`;
      return;
    }

    coacheeList.innerHTML = coachees
      .map(
        (c) => `
      <div class="col-md-4">
        <div class="card mb-3 p-3">
          <h6>${c.firstname} ${c.lastname}</h6>
          <p class="small">${c.email}</p>
          <span class="badge ${c.status ? "bg-success" : "bg-secondary"}">${c.status ? "Active" : "Inactive"}</span>
        </div>
      </div>`
      )
      .join("");
  } catch (err) {
    console.error("Error loading coachees:", err);
  }
}

// -----------------------------------
// Load sessions
// -----------------------------------
async function loadSessions() {
  try {
    const res = await fetch(`/coach/${coachId}/sessions`);
    const sessions = await res.json();

    if (!sessions.length) {
      sessionList.innerHTML = `<li class="list-group-item text-muted">No sessions available.</li>`;
      return;
    }

    sessionList.innerHTML = sessions
      .map(
        (s) => `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <strong>${s.topic}</strong><br>
          <small>${s.date}</small>
        </div>
        <span class="badge ${s.status === "completed" ? "bg-success" : "bg-warning"}">${s.status}</span>
      </li>`
      )
      .join("");
  } catch (err) {
    console.error("Session load error:", err);
  }
}

// -----------------------------------
// Logout
// -----------------------------------
document.getElementById("logoutBtn").addEventListener("click", () => {
  window.location.href = "/";
});

// -----------------------------------
// Initialize dashboard
// -----------------------------------
loadCoachProfile();
loadCoachees();
loadSessions();
