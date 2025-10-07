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
  formData.append("coach_title", document.getElementById("coach_title").value);
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
// Add / Remove / View Coachee handlers
// --------------------------------------
// When opening Add Coachee modal, populate organization dropdown
document.querySelectorAll('[data-bs-target="#addCoacheeModal"]').forEach(btn => {
  btn.addEventListener('click', async () => {
    try {
      const res = await fetch('/coachee_organizations');
      const orgs = res.ok ? await res.json() : [];
      const sel = document.getElementById('new_coachee_org');
      sel.innerHTML = `<option value="">-- Select organization --</option>` + orgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
    } catch (err) {
      console.warn('Failed to load coachee orgs', err);
    }
  });
});

// Create Coachee: POST /coachee and then link to coach via /coach/{coachId}/add_coachee
document.getElementById('createCoacheeBtn').addEventListener('click', async () => {
  const form = new FormData();
  form.append('coachee_firstname', document.getElementById('new_coachee_firstname').value);
  form.append('coachee_lastname', document.getElementById('new_coachee_lastname').value);
  form.append('coachee_email', document.getElementById('new_coachee_email').value);
  const orgVal = document.getElementById('new_coachee_org').value;
  if (orgVal) form.append('coachee_org', orgVal);
  form.append('coachee_background', document.getElementById('new_coachee_background').value);
  form.append('coachee_edu', document.getElementById('new_coachee_edu').value);
  form.append('coachee_challenges', document.getElementById('new_coachee_challenges').value);
  form.append('coachee_goals', document.getElementById('new_coachee_goals').value);
  form.append('coachee_status', document.getElementById('new_coachee_status').value === 'true');
  const photo = document.getElementById('new_coachee_photo').files[0];
  if (photo) form.append('coachee_photo', photo);

  try {
    const res = await fetch('/coachee', { method: 'POST', body: form });
    const data = await res.json();
  if (!res.ok) return (console.debug('create coachee failed', data), showToast('❌ ' + (data.detail || 'Failed to create coachee'), 'danger'));

    // Link to coach (existing endpoint links by email)
    const linkForm = new FormData();
    linkForm.append('email', data.email);
    const linkRes = await fetch(`/coach/${coachId}/add_coachee`, { method: 'POST', body: linkForm });
    if (!linkRes.ok) {
      console.debug('link coachee failed', await linkRes.text());
      showToast('⚠️ Coachee created but could not be linked to coach', 'warning');
    } else {
      showToast('✅ Coachee created and linked', 'success');
    }
    bootstrap.Modal.getInstance(document.getElementById('addCoacheeModal')).hide();
    loadCoachees();
    console.debug('coachee created', data);
  } catch (err) {
    console.error('Error creating coachee', err);
    showToast('❌ Error creating coachee', 'danger');
  }
});

// Helper to refresh both organization selects (create modal and edit modal)
async function refreshCoacheeOrgSelects(selectNewId) {
  try {
    const res = await fetch('/coachee_organizations');
    const orgs = res.ok ? await res.json() : [];
    const newSel = document.getElementById('new_coachee_org');
    if (newSel) newSel.innerHTML = `<option value="">-- Select organization --</option>` + orgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
    const editSel = document.getElementById('coachee_org');
    if (editSel) editSel.innerHTML = `<option value="">-- Select organization --</option>` + orgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
    // if a specific id is provided, try to select it
    if (selectNewId) {
      if (newSel) newSel.value = selectNewId;
      if (editSel) editSel.value = selectNewId;
    }
  } catch (err) {
    console.warn('Failed to refresh org selects', err);
  }
}

// Wire Add Org button on the Create Coachee modal
const addNewOrgBtn = document.getElementById('addNewCoacheeOrgBtn');
if (addNewOrgBtn) {
  addNewOrgBtn.addEventListener('click', async () => {
  const name = prompt('Organization name (required):');
  if (!name) return showToast('Organization name required', 'warning');
  const email = prompt('Organization email (optional):');
    try {
      const form = new FormData();
      try {
        const res = await fetch(`/coach/${coachId}/coachees`);
        let coachees = await res.json();
        if (!coachees.length) {
          coacheeList.innerHTML = `<p class="text-muted">No coachees yet.</p>`;
          return;
        }
        // Always sort: active first, then by name, then inactive by name
        coachees.sort((a, b) => {
          if (a.status === b.status) {
            const nameA = (a.firstname + ' ' + a.lastname).toLowerCase();
            const nameB = (b.firstname + ' ' + b.lastname).toLowerCase();
            return nameA.localeCompare(nameB);
          }
          return b.status - a.status; // true (active) first
        });
        coacheeList.innerHTML = '<div class="row" id="coacheeCardRow"></div>';
        const cardRow = document.getElementById('coacheeCardRow');
        cardRow.innerHTML = coachees.map(c => {
          const statusDot = `<span title="${c.status ? 'Active' : 'Inactive'}" style="display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:middle;background:${c.status ? '#28a745' : '#adb5bd'};"></span>`;
          return `
          <div class="col-md-4">
            <div class="card p-3 mb-3">
              <div class="d-flex align-items-center">
                ${c.photo ? `<img src="${c.photo}" class="rounded-circle me-2" style="width:48px;height:48px;object-fit:cover">` : `<div class="rounded-circle bg-secondary me-2" style="width:48px;height:48px"></div>`}
                <div>
                  <h6 class="mb-0">${statusDot}${c.firstname} ${c.lastname}</h6>
                  <small class="text-muted">${c.org_name || ''}</small>
                  ${c.summary ? `<div class="text-muted small mt-1" id="coachee-summary-${c.id}">${c.summary}</div>` : ''}
                  ${c.next_session ? `<div class="small"><a href="#" class="text-primary" data-action="open-session" data-session-id="${c.next_session.id}">Next: ${c.next_session.date} — ${c.next_session.topic}</a></div>` : ''}
                    ${c.last_session ? `<div class="small"><a href="#" class="text-primary" data-action="open-session" data-session-id="${c.last_session.id}">Last: ${c.last_session.date} — ${c.last_session.topic}</a></div>` : ''}
                </div>
              </div>
              <p class="small text-muted mt-2">${c.email}</p>
              <div class="d-flex justify-content-between">
                <button class="btn btn-outline-primary btn-sm" data-action="view" data-id="${c.id}">View</button>
                <div>
                  <button class="btn btn-outline-secondary btn-sm me-1" data-action="regenerate" data-id="${c.id}">Regenerate</button>
                  <button class="btn btn-outline-danger btn-sm" data-action="remove" data-id="${c.id}">Remove</button>
                </div>
              </div>
            </div>
          </div>
        `;
        }).join("");
      } catch (err) {
        coacheeList.innerHTML = `<p class="text-danger">Error loading coachees.</p>`;
      }
      const orgs = orgRes.ok ? await orgRes.json() : [];
      const sel = document.getElementById('coachee_org');
      sel.innerHTML = `<option value="">-- Select organization --</option>` + orgs.map(o => `<option value="${o.id}" ${o.id == c.org ? 'selected' : ''}>${o.name}</option>`).join('');
    } catch (err) {
      console.warn('Failed to load organizations', err);
    }

    // Wire the add-org button in the modal
    const addOrgBtn = document.getElementById('addCoacheeOrgBtn');
    if (addOrgBtn) {
      addOrgBtn.addEventListener('click', async () => {
        const name = prompt('Organization name (required):');
        if (!name) return alert('Organization name required');
        const email = prompt('Organization email (optional):');
        try {
          const form = new FormData();
          form.append('name', name);
          if (email) form.append('email', email);
          const res = await fetch('/coachee_organizations', { method: 'POST', body: form });
          const data = await res.json();
          if (!res.ok) return alert('❌ ' + (data.detail || 'Failed to create organization'));
          // refresh both selects (modal and create form)
          await refreshCoacheeOrgSelects(data.id);
          // select the newly created org in modal
          const sel = document.getElementById('coachee_org');
          if (sel) sel.value = data.id;
          alert('✅ Organization created');
        } catch (err) {
          console.error('Error creating organization', err);
          alert('❌ Error creating organization');
        }
      });
    }

    // Photo preview handler
    const photoInput = document.getElementById('coachee_photo_input');
    photoInput.addEventListener('change', (ev) => {
      const f = ev.target.files && ev.target.files[0];
      const preview = document.getElementById('coachee_photo_preview');
      if (!f) { preview.innerHTML = c.photo ? `<img src="${c.photo}" style="max-width:120px;max-height:120px;object-fit:cover">` : ''; return; }
      const reader = new FileReader();
      reader.onload = () => { preview.innerHTML = `<img src="${reader.result}" style="max-width:120px;max-height:120px;object-fit:cover">`; };

// Delegate clicks on coachee session list to open session detail modal
document.getElementById('coacheeSessionList').addEventListener('click', (e) => {
  const editBtn = e.target.closest('button[data-action="edit"]');
  if (editBtn) {
    const sessionId = editBtn.getAttribute('data-session-id');
    // Find the session's status (completed or scheduled)
    const li = editBtn.closest('li[data-session-id]');
    const badge = li ? li.querySelector('.badge') : null;
    const isCompleted = badge && badge.classList.contains('bg-success');
    if (isCompleted) {
      if (!confirm('You are editing a completed session. Are you sure you want to continue?')) return;
    }
    return viewSession(sessionId, { editable: true });
  }
  const openEl = e.target.closest('[data-action="open"]');
  if (openEl) {
    const li = openEl.closest('li[data-session-id]');
    if (!li) return;
    const id = li.getAttribute('data-session-id');
    if (id) viewSession(id, { editable: false });
  }
});

async function viewSession(sessionId, opts = {}) {
  try {
    const res = await fetch(`/session/${sessionId}`);
    if (!res.ok) throw new Error('Failed to load session');
    const s = await res.json();
    document.getElementById('sessionDetailTitle').innerText = s.topic || 'Session';
    // Add delete button for future sessions, and edit warning for past sessions
    const footer = document.querySelector('#sessionDetailModal .modal-footer');
    let deleteBtn = document.getElementById('deleteSessionBtn');
    if (!deleteBtn) {
      deleteBtn = document.createElement('button');
      deleteBtn.id = 'deleteSessionBtn';
      deleteBtn.className = 'btn btn-danger me-auto';
      deleteBtn.innerText = 'Delete Session';
      footer.prepend(deleteBtn);
    }
    // Hide by default
    deleteBtn.style.display = 'none';
    // Determine if session is in the future
    let isFuture = false;
    if (s.date) {
      const sessionDate = new Date(toDatetimeLocalValue(s.date));
      isFuture = sessionDate > new Date();
    }
    if (isFuture) {
      deleteBtn.style.display = '';
      deleteBtn.onclick = async () => {
        if (!confirm('Are you sure you want to delete this future session? This cannot be undone.')) return;
        const res = await fetch(`/session/${sessionId}`, { method: 'DELETE' });
        if (res.ok) {
          showToast('Session deleted', 'success');
          bootstrap.Modal.getInstance(document.getElementById('sessionDetailModal')).hide();
          // Optionally refresh coachee card or session list
          loadCoachees();
        } else {
          showToast('Failed to delete session', 'danger');
        }
      };
    }
    // If editing a past session, show a warning and require confirmation before saving
    if (opts.editable && !isFuture) {
      const saveBtn = document.getElementById('saveSessionBtn');
      saveBtn.onclick = async (e) => {
        e.preventDefault();
        if (!confirm('You are editing a past session. Are you sure you want to continue?')) return;
        saveSessionHandler(e);
      };
    } else if (opts.editable) {
      // For future sessions, normal save
      document.getElementById('saveSessionBtn').onclick = saveSessionHandler;
    }
    // date: show plain text when read-only, show datetime-local input when editable
    if (opts.editable) {
      document.getElementById('sessionDetailDate').innerHTML = `<input id="session_date_input" type="datetime-local" class="form-control" value="${toDatetimeLocalValue(s.date)}">`;
    } else {
      document.getElementById('sessionDetailDate').innerText = s.date || '';
    }
    // Populate fields; when editable true, make them textareas for editing
    if (opts.editable) {
      document.getElementById('sessionDetailTopic').innerHTML = `<textarea id="session_topic_input" class="form-control">${s.topic || ''}</textarea>`;
      document.getElementById('sessionDetailNotes').innerHTML = `<textarea id="session_notes_input" class="form-control" style="min-height:120px">${s.coach_notes || ''}</textarea>`;
      document.getElementById('sessionDetailApproach').innerHTML = `<textarea id="session_approach_input" class="form-control" style="min-height:80px">${s.coach_approach || ''}</textarea>`;
      document.getElementById('sessionDetailGoals').innerHTML = `<textarea id="session_goals_input" class="form-control">${s.goals || ''}</textarea>`;
      document.getElementById('sessionDetailNextSteps').innerHTML = `<textarea id="session_next_input" class="form-control">${s.next_steps || ''}</textarea>`;
      // Always clear and inject the file input for attachments
      const attDiv = document.getElementById('sessionDetailAttachments');
      attDiv.innerHTML = '';
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.id = 'session_attachments_input';
      fileInput.className = 'form-control';
      fileInput.multiple = true;
      attDiv.appendChild(fileInput);
      // Fallback debug message if file input is not visible
      setTimeout(() => {
        if (!document.getElementById('session_attachments_input')) {
          const fallback = document.createElement('div');
          fallback.style.color = 'red';
          fallback.innerText = 'Attachment upload field failed to render (JS error or DOM issue)';
          attDiv.appendChild(fallback);
        }
      }, 500);
      const existingDiv = document.createElement('div');
      existingDiv.id = 'session_existing_attachments';
      existingDiv.className = 'mt-2';
      attDiv.appendChild(existingDiv);
      // Show existing attachments as links with remove option
      if (s.attachments) {
        const parts = s.attachments.split(',').map(p => p.trim()).filter(Boolean);
        parts.forEach((p, idx) => {
          const div = document.createElement('div');
          div.className = 'd-flex align-items-center mb-1';
          div.innerHTML = `<a href="${p}" target="_blank">${p.split('/').pop() || p}</a> <button type="button" class="btn btn-sm btn-link text-danger ms-2" data-idx="${idx}" title="Remove">✕</button>`;
          existingDiv.appendChild(div);
        });
        // Remove attachment handler
        existingDiv.querySelectorAll('button[data-idx]').forEach(btn => {
          btn.onclick = function() {
            const idx = parseInt(this.dataset.idx);
            parts.splice(idx, 1);
            existingDiv.innerHTML = '';
            parts.forEach((p, i) => {
              const div = document.createElement('div');
              div.className = 'd-flex align-items-center mb-1';
              div.innerHTML = `<a href="${p}" target="_blank">${p.split('/').pop() || p}</a> <button type="button" class="btn btn-sm btn-link text-danger ms-2" data-idx="${i}" title="Remove">✕</button>`;
              existingDiv.appendChild(div);
            });
          };
        });
      }
      // Add status select
      const statusVal = s.status || 'open';
      document.getElementById('sessionDetailStatus')?.remove();
      const statusDiv = document.createElement('div');
      statusDiv.className = 'mt-3';
      statusDiv.id = 'sessionDetailStatus';
      statusDiv.innerHTML = `<label class="form-label">Status</label><select id="session_status_input" class="form-select"><option value="open" ${statusVal==='open'?'selected':''}>Open</option><option value="completed" ${statusVal==='completed'?'selected':''}>Completed</option></select>`;
      document.getElementById('sessionDetailModal').querySelector('.modal-body').appendChild(statusDiv);
      document.getElementById('saveSessionBtn').style.display = '';
      // store current session id on button
      document.getElementById('saveSessionBtn').dataset.sessionId = sessionId;
    } else {
      document.getElementById('sessionDetailTopic').innerText = s.topic || '';
      document.getElementById('sessionDetailNotes').innerText = s.coach_notes || '';
      document.getElementById('sessionDetailApproach').innerText = s.coach_approach || '';
      document.getElementById('sessionDetailGoals').innerText = s.goals || '';
      document.getElementById('sessionDetailNextSteps').innerText = s.next_steps || '';
      document.getElementById('saveSessionBtn').style.display = 'none';
      // Always render attachments section in read-only mode
      const att = document.getElementById('sessionDetailAttachments');
      att.innerHTML = '';
      if (s.attachments) {
        // attachments stored as comma-separated paths
        const parts = s.attachments.split(',').map(p => p.trim()).filter(Boolean);
        if (parts.length > 0) {
          parts.forEach(p => {
            const a = document.createElement('a');
            a.href = p;
            a.target = '_blank';
            a.className = 'd-block';
            a.innerText = p.split('/').pop() || p;
            att.appendChild(a);
          });
        } else {
          att.innerHTML = '<span class="text-muted">No attachments.</span>';
        }
      } else {
        att.innerHTML = '<span class="text-muted">No attachments.</span>';
      }
    }
    new bootstrap.Modal(document.getElementById('sessionDetailModal')).show();
  } catch (err) {
    console.error('Error loading session', err);
    alert('❌ Could not load session');
  }
}

// Save session edits (button in modal)

async function saveSessionHandler(e) {
  const btn = e.target;
  const sessionId = btn.dataset.sessionId;
  if (!sessionId) return showToast('No session loaded', 'warning');
  try {
    const form = new FormData();
    form.append('session_topic', document.getElementById('session_topic_input').value);
    // include date/time if present (convert T -> space to match backend expectation)
    const dateEl = document.getElementById('session_date_input');
    if (dateEl && dateEl.value) {
      // validate: warn if date is in the past
      const chosen = new Date(dateEl.value);
      const now = new Date();
      if (chosen < now) {
        if (!confirm('The scheduled date/time is in the past. Do you want to continue and save it?')) return;
      }
      const serverDate = dateEl.value.replace('T', ' ');
      form.append('session_date', serverDate);
    }
    form.append('session_coachnotes', document.getElementById('session_notes_input').value);
    form.append('session_coachapproach', document.getElementById('session_approach_input').value);
    form.append('session_goals', document.getElementById('session_goals_input').value);
    form.append('session_nextsteps', document.getElementById('session_next_input').value);
    // Add status
    const statusEl = document.getElementById('session_status_input');
    if (statusEl) form.append('session_status', statusEl.value);
    // Attachments: collect files and current attachment list
    const fileInput = document.getElementById('session_attachments_input');
    if (fileInput && fileInput.files.length > 0) {
      for (let i = 0; i < fileInput.files.length; i++) {
        form.append('new_attachments', fileInput.files[i]);
      }
    }
    // If user removed attachments, send the updated list
    const existingLinks = document.querySelectorAll('#session_existing_attachments a');
    const updatedPaths = Array.from(existingLinks).map(a => a.getAttribute('href')).filter(Boolean);
    if (existingLinks.length > 0) {
      form.append('session_attachments', updatedPaths.join(','));
    }
    const res = await fetch(`/session/${sessionId}?coach_id=${encodeURIComponent(coachId)}`, { method: 'PUT', body: form });
    const data = await res.json();
    if (!res.ok) return showToast('❌ ' + (data.detail || 'Failed to update session'), 'danger');
    showToast('✅ Session updated', 'success');
    // close modal and refresh coachee view to show updated session
    bootstrap.Modal.getInstance(document.getElementById('sessionDetailModal')).hide();
    // update the single session list item in the coachee modal to avoid a full re-fetch
    const coacheeId = document.getElementById('coacheeDetailName').dataset.coacheeId;
    if (coacheeId) updateSessionListItem(sessionId, data);
  } catch (err) {
    console.error('Error saving session', err);
    showToast('❌ Could not save session', 'danger');
  }
}

function makeSessionSummary(s) {
  const txt = (s.coach_notes || s.goals || s.topic || '').toString();
  if (!txt) return '';
  return txt.length > 120 ? txt.slice(0, 117) + '...' : txt;
}

function updateSessionListItem(sessionId, updated) {
  try {
    const li = document.querySelector(`#coacheeSessionList li[data-session-id="${sessionId}"]`);
    if (!li) return;
    let badgeLabel = '';
    let badgeClass = '';
    if (updated.status === 'completed') {
      badgeLabel = 'completed';
      badgeClass = 'bg-success';
    } else {
      const now = new Date();
      const sessionDate = new Date(toDatetimeLocalValue(updated.date));
      if (sessionDate > now) {
        badgeLabel = 'scheduled';
        badgeClass = 'bg-info';
      } else {
        badgeLabel = 'needs reschedule';
        badgeClass = 'bg-warning';
      }
    }
    const editable = `<button class="btn btn-sm btn-outline-primary mt-2" data-action="edit" data-session-id="${sessionId}">Edit</button>`;
    const summary = makeSessionSummary(updated);
    li.innerHTML = `
      <div style="cursor:pointer" class="flex-grow-1" data-action="open"> <strong>${updated.date}</strong> — ${updated.topic || ''}<div class="small text-muted">${summary}</div></div>
      <div class="ms-2 text-end">
        <div><span class="badge ${badgeClass}">${badgeLabel}</span></div>
        ${editable}
      </div>
    `;
  } catch (err) {
    console.warn('Failed to update session list item', err);
  }
}

// --------------------------------------
// Load Sessions
// --------------------------------------
async function loadSessions() {
  try {
    const res = await fetch(`/coach/${coachId}/sessions`);
    const sessions = await res.json();
    if (!sessions.length) {
      sessionList.innerHTML = `<li class="list-group-item text-muted">No sessions yet.</li>`;
      return;
    }
    sessionList.innerHTML = sessions.map(s => `
      <li class="list-group-item">${s.date} - ${s.topic}</li>
    `).join("");
  } catch (err) {
    sessionList.innerHTML = `<li class="list-group-item text-danger">Error loading sessions.</li>`;
  }
}

// --------------------------------------
// Load Assignments
// --------------------------------------
async function loadAssignments() {
  try {
    const res = await fetch(`/coach/${coachId}/assignments`);
    const assignments = await res.json();
    if (!assignments.length) {
      assignmentList.innerHTML = `<li class="list-group-item text-muted">No assignments yet.</li>`;
      return;
    }
    assignmentList.innerHTML = assignments.map(a => `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        <span>${a.title}</span>
        <span class="badge bg-primary">${a.status}</span>
      </li>
    `).join("");
  } catch (err) {
    assignmentList.innerHTML = `<li class="list-group-item text-danger">Error loading assignments.</li>`;
  }
}

// Initial load

// Save coachee changes
document.getElementById('saveCoacheeBtn').addEventListener('click', async () => {
  const idText = document.getElementById('coacheeDetailName').dataset.coacheeId;
  const coacheeId = idText || null;
  if (!coacheeId) return alert('No coachee loaded');
  try {
    const form = new FormData();
    form.append('coachee_firstname', document.getElementById('coachee_firstname').value);
    form.append('coachee_lastname', document.getElementById('coachee_lastname').value);
    form.append('coachee_email', document.getElementById('coachee_email').value);
    form.append('coachee_background', document.getElementById('coachee_background').value);
  form.append('coachee_edu', document.getElementById('coachee_edu').value);
  form.append('coachee_challenges', document.getElementById('coachee_challenges').value);
    form.append('coachee_goals', document.getElementById('coachee_goals').value);
    form.append('coachee_status', document.getElementById('coachee_status').value === 'true');
    const orgVal = document.getElementById('coachee_org').value;
    if (orgVal) form.append('coachee_org', orgVal);
    const photoFile = document.getElementById('coachee_photo_input').files[0];
    if (photoFile) form.append('coachee_photo', photoFile);
    const res = await fetch(`/coachee/${coacheeId}`, { method: 'PUT', body: form });
    if (res.ok) {
      alert('✅ Coachee updated');
      bootstrap.Modal.getInstance(document.getElementById('coacheeDetailModal')).hide();
      loadCoachees();
    } else {
      alert('❌ Failed to update coachee');
    }
  } catch (err) {
    console.error('Error saving coachee', err);
    alert('❌ Error saving coachee');
  }
});
loadCoachProfile();
loadCoachees();
loadSessions();
loadAssignments();

// --- Debug overlay (visible when needed) ---
const debugToggle = document.getElementById('debugToggle');
const debugOverlay = document.getElementById('debugOverlay');
const debugClose = document.getElementById('debugClose');
const debugRefresh = document.getElementById('debugRefresh');
const debugSummary = document.getElementById('debugSummary');
const debugRaw = document.getElementById('debugRaw');

async function fetchDebug(coachIdParam) {
  const id = coachIdParam || coachId || 1;
  debugSummary.innerText = 'Loading...';
  debugRaw.innerText = '';
  try {
    const res = await fetch(`/debug/coach_dashboard?coach_id=${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error('Failed to fetch debug');
    const j = await res.json();
    debugSummary.innerHTML = `<div><strong>Coach:</strong> ${j.coach.firstname} ${j.coach.lastname} (${j.coach.id})</div><div><strong>Coachees:</strong> ${j.coachees.length}</div><div><strong>Sessions:</strong> ${j.sessions.length}</div><div><strong>Assignments:</strong> ${j.assignments.length}</div>`;
    debugRaw.innerText = JSON.stringify(j, null, 2);
  } catch (err) {
    debugSummary.innerText = 'Error fetching debug: ' + err.message;
  }
}

debugToggle.addEventListener('click', () => {
  debugOverlay.style.display = debugOverlay.style.display === 'none' ? '' : 'none';
  if (debugOverlay.style.display !== 'none') fetchDebug();
});
debugClose.addEventListener('click', () => debugOverlay.style.display = 'none');
debugRefresh.addEventListener('click', () => fetchDebug());

// Delegate click events for coachee list (handles View / Remove / Regenerate)
if (coacheeList) {
  coacheeList.addEventListener('click', (e) => {
    // allow clicks on any element that carries a data-action attribute (not only buttons)
    const el = e.target.closest('[data-action]');
    if (!el) return;
    const action = el.dataset.action;
    // support either data-id (coachee id) or data-session-id for session buttons
    const id = el.dataset.id || el.getAttribute('data-session-id');
    console.debug('coacheeList click', { action, id, tag: el.tagName, target: e.target });
    if (action === 'view') return viewCoachee(id);
    if (action === 'remove') return removeCoachee(id);
    if (action === 'regenerate') return regenerateSummary(id);
    if (action === 'open-session') return viewSession(id, { editable: true });
  });
}

// Expose handlers globally for any legacy inline onclick attributes or cached scripts
window.viewCoachee = viewCoachee;
window.removeCoachee = removeCoachee;
// Provide a safe helper to open the Add Coachee modal (some older code expected an element id that doesn't exist)
window.addCoachee = async () => {
  const modalEl = document.getElementById('addCoacheeModal');
  if (modalEl) return new bootstrap.Modal(modalEl).show();
  // fallback: try to click a button that opens it
  const btn = document.querySelector('[data-bs-target="#addCoacheeModal"]');
  if (btn) return btn.click();
};

async function regenerateSummary(coacheeId) {
  try {
    const res = await fetch(`/coachee/${coacheeId}/regenerate_summary`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed');
    const data = await res.json();
    // update card summary if present
    const el = document.getElementById(`coachee-summary-${coacheeId}`);
    if (el) {
      if (data.summary) el.innerText = data.summary;
      else el.innerText = '';
    }
    // If modal open for this coachee, update its summary area as well
    const nameEl = document.getElementById('coacheeDetailName');
    if (nameEl && nameEl.dataset.coacheeId == coacheeId) {
      const modalBody = document.getElementById('coacheeDetailInfo');
      const existing = document.getElementById('coachee_summary_block');
      if (existing) existing.remove();
      const node = document.createElement('div');
      node.id = 'coachee_summary_block';
      node.className = 'mb-3';
      node.innerHTML = `<label class="form-label">Summary</label><div class="form-control" style="min-height:40px">${data.summary || ''}</div>`;
      modalBody.prepend(node);
    }
    alert('✅ Summary regenerated');
  } catch (err) {
    console.error('Error regenerating summary', err);
    alert('❌ Could not regenerate summary');
  }
}

// Modal-level regenerate button
document.getElementById('regenerateSummaryBtn').addEventListener('click', async () => {
  const nameEl = document.getElementById('coacheeDetailName');
  const coacheeId = nameEl && nameEl.dataset && nameEl.dataset.coacheeId;
  if (!coacheeId) return alert('No coachee loaded');
  try {
    const res = await fetch(`/coachee/${coacheeId}/regenerate_summary`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed');
    const data = await res.json();
    // show in modal
    const summaryBlock = document.getElementById('coachee_summary_block');
    const summaryContent = document.getElementById('coachee_summary_content');
    if (data.summary) {
      summaryContent.innerText = data.summary;
      summaryBlock.style.display = '';
    } else {
      summaryContent.innerText = '';
      summaryBlock.style.display = 'none';
    }
    // update card
    const cardEl = document.getElementById(`coachee-summary-${coacheeId}`);
    if (cardEl) cardEl.innerText = data.summary || '';
    alert('✅ Summary regenerated');
  } catch (err) {
    console.error('Error regenerating summary', err);
    alert('❌ Could not regenerate summary');
  }
});



