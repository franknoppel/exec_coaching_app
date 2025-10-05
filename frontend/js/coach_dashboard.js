// Extract coach_id from URL
const params = new URLSearchParams(window.location.search);
const coachId = params.get("coach_id");

// Elements
const profileDiv = document.getElementById("coachProfile");
const coacheeList = document.getElementById("coacheeList");
const sessionList = document.getElementById("sessionList");
const assignmentList = document.getElementById("assignmentList");

// --------------------------------------
// Load Coach Profile
// --------------------------------------
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
    document.getElementById("coach_firstname").value = coach.firstname;
    document.getElementById("coach_lastname").value = coach.lastname;
    document.getElementById("coach_email").value = coach.email;
    document.getElementById("coach_qualifications").value = coach.qualifications || "";
    document.getElementById("coach_profile").value = coach.profile || "";
    document.getElementById("coach_status").value = coach.status ? "true" : "false";
  } catch (err) {
    console.error("Error loading coach:", err);
  }
}

// --------------------------------------
// Save Coach Profile
// --------------------------------------
document.getElementById("saveProfileBtn").addEventListener("click", async () => {
  const formData = new FormData();
  formData.append("coach_firstname", document.getElementById("coach_firstname").value);
  formData.append("coach_lastname", document.getElementById("coach_lastname").value);
  formData.append("coach_email", document.getElementById("coach_email").value);
  formData.append("coach_qualifications", document.getElementById("coach_qualifications").value);
  formData.append("coach_profile", document.getElementById("coach_profile").value);
  formData.append("coach_status", document.getElementById("coach_status").value);
  const photoFile = document.getElementById("coach_photo").files[0];
  if (photoFile) formData.append("coach_photo", photoFile);

  const res = await fetch(`/coach/${coachId}`, { method: "PUT", body: formData });
  if (res.ok) {
    alert("✅ Profile updated");
    loadCoachProfile();
    bootstrap.Modal.getInstance(document.getElementById("profileModal")).hide();
  } else alert("❌ Failed to update");
});

// --------------------------------------
// Load Coachees
// --------------------------------------
async function loadCoachees() {
  try {
    const res = await fetch(`/coach/${coachId}/coachees`);
    const coachees = await res.json();
    if (!coachees.length) {
      coacheeList.innerHTML = `<p class="text-muted">No coachees yet.</p>`;
      return;
    }
    coacheeList.innerHTML = coachees.map(c => `
      <div class="col-md-4">
        <div class="card p-3 mb-3">
          <h6>${c.firstname} ${c.lastname}</h6>
          <p class="small text-muted">${c.email}</p>
          <div class="d-flex justify-content-between">
            <button class="btn btn-outline-primary btn-sm" onclick="viewCoachee(${c.id})">View</button>
            <button class="btn btn-outline-danger btn-sm" onclick="removeCoachee(${c.id})">Remove</button>
          </div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading coachees:", err);
  }
}

// --------------------------------------
// Add Coachee
// --------------------------------------
document.getElementById("addCoacheeBtn").addEventListener("click", async () => {
  const email = document.getElementById("newCoacheeEmail").value.trim();
  if (!email) return alert("Please enter a coachee email.");

  // Placeholder: backend endpoint for add-coachee needed
  alert(`(Future) Add coachee by email: ${email}`);
  document.getElementById("newCoacheeEmail").value = "";
  bootstrap.Modal.getInstance(document.getElementById("addCoacheeModal")).hide();
  loadCoachees();
});

// --------------------------------------
// Remove Coachee
// --------------------------------------
async function removeCoachee(coacheeId) {
  if (!confirm("Remove this coachee?")) return;
  // Placeholder for backend endpoint
  alert(`(Future) Removed coachee ID ${coacheeId}`);
  loadCoachees();
}

// --------------------------------------
// View Coachee Details
// --------------------------------------
async function viewCoachee(coacheeId) {
  try {
    const res = await fetch(`/coachee/${coacheeId}`);
    const c = await res.json();

    document.getElementById("coacheeDetailName").innerText = `${c.firstname} ${c.lastname}`;
    document.getElementById("coacheeDetailInfo").innerHTML = `
      <p><strong>Email:</strong> ${c.email}</p>
      <p><strong>Organization:</strong> ${c.org || "-"}</p>
      <p><strong>Background:</strong> ${c.background || "-"}</p>
      <p><strong>Goals:</strong> ${c.goals || "-"}</p>
    `;

    // Sessions
    const sessionsRes = await fetch(`/coachee/${coacheeId}/sessions`);
    const sessions = await sessionsRes.json();
    document.getElementById("coacheeSessionList").innerHTML =
      sessions.length
        ? sessions.map(s => `<li class="list-group-item">${s.date} - ${s.topic}</li>`).join("")
        : `<li class="list-group-item text-muted">No sessions</li>`;

    // Assignments
    const assRes = await fetch(`/coachee/${coacheeId}/assignments`);
    const assignments = await assRes.json();
    document.getElementById("coacheeAssignmentList").innerHTML =
      assignments.length
        ? assignments.map(a => `
          <li class="list-group-item d-flex justify-content-between">
            <div>
              <strong>${a.description}</strong><br>
              <small>Due: ${a.duedate}</small>
            </div>
            <span class="badge ${a.status === "completed" ? "bg-success" : "bg-warning"}">${a.status}</span>
          </li>`).join("")
        : `<li class="list-group-item text-muted">No assignments</li>`;

    new bootstrap.Modal(document.getElementById("coacheeDetailModal")).show();
  } catch (err) {
    console.error("Error viewing coachee:", err);
  }
}

// --------------------------------------
// Load Sessions
// --------------------------------------
async function loadSessions() {
  const res = await fetch(`/coach/${coachId}/sessions`);
  const sessions = await res.json();
  sessionList.innerHTML = sessions.length
    ? sessions.map(s => `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        <div><strong>${s.topic}</strong><br><small>${s.date}</small></div>
        <span class="badge ${s.status === "completed" ? "bg-success" : "bg-warning"}">${s.status}</span>
      </li>`).join("")
    : `<li class="list-group-item text-muted">No sessions found</li>`;
}

// --------------------------------------
// Load Assignments
// --------------------------------------
async function loadAssignments() {
  // Placeholder: fetch open assignments from backend
  assignmentList.innerHTML = `<li class="list-group-item text-muted">Assignments feature coming soon</li>`;
}

// --------------------------------------
// Logout
// --------------------------------------
document.getElementById("logoutBtn").addEventListener("click", () => {
  window.location.href = "/";
});

// --------------------------------------
// Initialize
// --------------------------------------
loadCoachProfile();
loadCoachees();
loadSessions();
loadAssignments();
