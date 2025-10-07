// Coach Dashboard JavaScript
// Clean implementation for session management with file uploads

// ---- Get coach ID from URL ----
const urlParams = new URLSearchParams(window.location.search);
const coachId = urlParams.get('coach_id');

if (!coachId) {
  alert('No coach ID provided. Redirecting to login.');
  window.location.href = 'index.html';
}

// ---- Modal utilities ----
function showModal(html) {
  const container = document.getElementById('modalContainer');
  const backdrop = document.getElementById('modalBackdrop');
  
  container.innerHTML = html;
  const modal = container.querySelector('.modal');
  
  backdrop.classList.add('show');
  modal.classList.add('show');
  
  // Close on backdrop click
  backdrop.onclick = () => closeModal();
  
  // Close on close button click
  const closeBtn = modal.querySelector('.btn-close');
  if (closeBtn) {
    closeBtn.onclick = () => closeModal();
  }
  
  // Close on cancel button click
  const cancelBtns = modal.querySelectorAll('[data-bs-dismiss="modal"]');
  cancelBtns.forEach(btn => {
    btn.onclick = () => closeModal();
  });
}

function closeModal() {
  const container = document.getElementById('modalContainer');
  const backdrop = document.getElementById('modalBackdrop');
  
  const modals = container.querySelectorAll('.modal');
  modals.forEach(m => m.classList.remove('show'));
  backdrop.classList.remove('show');
  
  setTimeout(() => {
    container.innerHTML = '';
  }, 300);
}

// ---- Load coach profile ----
async function loadCoachProfile() {
  try {
    const response = await fetch(`/coach/${coachId}`);
    const coach = await response.json();
    
    document.getElementById('coachName').textContent = `${coach.firstname} ${coach.lastname}`;
    document.getElementById('coachEmail').textContent = coach.email;
    document.getElementById('coachBio').textContent = coach.profile || 'No bio available';
    
    if (coach.photo) {
      const photoEl = document.getElementById('coachPhoto');
      photoEl.src = coach.photo;
      photoEl.style.display = 'block';
    }
  } catch (error) {
    console.error('Error loading coach profile:', error);
  }
}

// ---- Load coachees ----
async function loadCoachees() {
  try {
    const response = await fetch(`/coach/${coachId}/coachees`);
    const coachees = await response.json();
    
    const coacheeList = document.getElementById('coachees');
    
    if (!coachees || coachees.length === 0) {
      coacheeList.innerHTML = '<p style="padding: 15px;" class="text-muted">No coachees yet.</p>';
      return;
    }
    
    // Sort: active first (by name), then inactive (by name)
    const activeCoachees = coachees.filter(c => c.status).sort((a, b) => 
      `${a.firstname} ${a.lastname}`.localeCompare(`${b.firstname} ${b.lastname}`)
    );
    const inactiveCoachees = coachees.filter(c => !c.status).sort((a, b) => 
      `${a.firstname} ${a.lastname}`.localeCompare(`${b.firstname} ${b.lastname}`)
    );
    const sortedCoachees = [...activeCoachees, ...inactiveCoachees];
    
    coacheeList.innerHTML = sortedCoachees.map(c => `
      <div class="list-group-item d-flex justify-content-between" style="align-items: center;">
        <div>
          <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; background-color: ${c.status ? '#28a745' : '#6c757d'};"></span>
          <strong>${c.firstname} ${c.lastname}</strong>
          <small class="text-muted" style="margin-left: 10px;">${c.email}</small>
        </div>
        <button class="btn btn-sm btn-outline-primary" onclick="viewCoacheeSessions(${c.id}, '${c.firstname} ${c.lastname}')">Sessions</button>
      </div>
    `).join('');
  } catch (error) {
    console.error('Error loading coachees:', error);
  }
}

// ---- View coachee sessions ----
async function viewCoacheeSessions(coacheeId, coacheeName) {
  try {
    const response = await fetch(`/coachee/${coacheeId}/sessions?coach_id=${coachId}`);
    const sessions = await response.json();
    
    // Show modal with sessions
    showSessionsModal(coacheeId, coacheeName, sessions);
  } catch (error) {
    console.error('Error loading sessions:', error);
    alert('Failed to load sessions');
  }
}

// ---- Show sessions modal ----
function showSessionsModal(coacheeId, coacheeName, sessions) {
  const modalHTML = `
    <div class="modal">
      <div class="modal-header">
        <h5>Sessions for ${coacheeName}</h5>
        <button class="btn-close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="d-flex justify-content-between mb-3" style="align-items: center;">
          <h6 style="margin: 0;">Session List</h6>
          <button class="btn btn-sm btn-primary" onclick="showAddSessionForm(${coacheeId}, '${coacheeName}')">
            Add New Session
          </button>
        </div>
        <div>
          ${sessions.length === 0 ? '<p class="text-muted">No sessions yet.</p>' : 
            sessions.map(s => `
              <div class="card" style="margin-bottom: 10px;">
                <div class="card-body">
                  <div class="d-flex justify-content-between" style="align-items: start;">
                    <div>
                      <h6 style="margin: 0 0 5px 0;">${s.topic || 'No topic'}</h6>
                      <small class="text-muted">${s.date}</small>
                      ${s.attachments ? `<div style="margin-top: 10px;">
                        <strong>Attachments:</strong><br>
                        ${s.attachments.split(',').map(url => {
                          const filename = url.split('/').pop();
                          return `<a href="${url}" target="_blank" style="display: block;">${filename}</a>`;
                        }).join('')}
                      </div>` : ''}
                    </div>
                    <div class="d-flex gap-2">
                      <button class="btn btn-sm btn-outline-secondary" onclick="viewSessionDetail(${s.id})">View</button>
                      <button class="btn btn-sm btn-outline-primary" onclick="editSession(${s.id}, ${coacheeId})">Edit</button>
                      <button class="btn btn-sm btn-outline-danger" onclick="deleteSession(${s.id}, ${coacheeId}, '${coacheeName}')">Delete</button>
                    </div>
                  </div>
                </div>
              </div>
            `).join('')
          }
        </div>
      </div>
    </div>
  `;
  
  showModal(modalHTML);
}

// ---- Show add session form ----
function showAddSessionForm(coacheeId, coacheeName) {
  const now = new Date();
  const defaultDate = `${String(now.getMonth() + 1).padStart(2, '0')}/${String(now.getDate()).padStart(2, '0')}/${now.getFullYear()} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  
  const modalHTML = `
    <div class="modal">
      <div class="modal-header">
        <h5>Add Session for ${coacheeName}</h5>
        <button class="btn-close">&times;</button>
      </div>
      <div class="modal-body">
        <form id="addSessionForm" enctype="multipart/form-data">
          <input type="hidden" name="coachee_id" value="${coacheeId}">
          
          <div class="mb-3">
            <label class="form-label">Date & Time</label>
            <input type="text" class="form-control" name="date" required 
              placeholder="MM/DD/YYYY HH:MM" value="${defaultDate}">
          </div>
          
          <div class="mb-3">
            <label class="form-label">Topic</label>
            <input type="text" class="form-control" name="topic" placeholder="Session topic">
          </div>
          
          <div class="mb-3">
            <label class="form-label">Notes</label>
            <textarea class="form-control" name="notes" rows="3"></textarea>
          </div>
          
          <div class="mb-3">
            <label class="form-label">Approach</label>
            <textarea class="form-control" name="approach" rows="2"></textarea>
          </div>
          
          <div class="mb-3">
            <label class="form-label">Goals</label>
            <textarea class="form-control" name="goals" rows="2"></textarea>
          </div>
          
          <div class="mb-3">
            <label class="form-label">Next Steps</label>
            <textarea class="form-control" name="nextsteps" rows="2"></textarea>
          </div>
          
          <div class="mb-3">
            <label class="form-label">Attachments</label>
            <input type="file" class="form-control" name="attachments" multiple>
            <small class="text-muted">You can select multiple files</small>
          </div>
          
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="submit" class="btn btn-primary">Create Session</button>
          </div>
        </form>
      </div>
    </div>
  `;
  
  showModal(modalHTML);
  
  // Handle form submission
  document.getElementById('addSessionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    try {
      const response = await fetch(`/session?coach_id=${coachId}`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        closeModal();
        // Reload sessions list
        viewCoacheeSessions(coacheeId, coacheeName);
      } else {
        alert('Failed to create session');
      }
    } catch (error) {
      console.error('Error creating session:', error);
      alert('Failed to create session');
    }
  });
}

// ---- View session detail ----
async function viewSessionDetail(sessionId) {
  try {
    const response = await fetch(`/session/${sessionId}`);
    const session = await response.json();
    
    const modalHTML = `
      <div class="modal">
        <div class="modal-header">
          <h5>Session Details</h5>
          <button class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <strong>Date:</strong> ${session.date}
          </div>
          <div class="mb-3">
            <strong>Topic:</strong> ${session.topic || 'N/A'}
          </div>
          <div class="mb-3">
            <strong>Notes:</strong><br>
            ${session.notes || 'No notes'}
          </div>
          <div class="mb-3">
            <strong>Approach:</strong><br>
            ${session.approach || 'N/A'}
          </div>
          <div class="mb-3">
            <strong>Goals:</strong><br>
            ${session.goals || 'N/A'}
          </div>
          <div class="mb-3">
            <strong>Next Steps:</strong><br>
            ${session.nextsteps || 'N/A'}
          </div>
          ${session.attachments ? `
            <div class="mb-3">
              <strong>Attachments:</strong><br>
              ${session.attachments.split(',').map(url => {
                const filename = url.split('/').pop();
                return `<a href="${url}" target="_blank" style="display: block;">${filename}</a>`;
              }).join('')}
            </div>
          ` : ''}
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    `;
    
    showModal(modalHTML);
  } catch (error) {
    console.error('Error loading session detail:', error);
    alert('Failed to load session details');
  }
}

// ---- Edit session ----
async function editSession(sessionId, coacheeId) {
  try {
    const response = await fetch(`/session/${sessionId}`);
    const session = await response.json();
    
    const modalHTML = `
      <div class="modal">
        <div class="modal-header">
          <h5>Edit Session</h5>
          <button class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <form id="editSessionForm" enctype="multipart/form-data">
            <input type="hidden" name="session_id" value="${sessionId}">
            
            <div class="mb-3">
              <label class="form-label">Date & Time</label>
              <input type="text" class="form-control" name="date" required value="${session.date}">
            </div>
            
            <div class="mb-3">
              <label class="form-label">Topic</label>
              <input type="text" class="form-control" name="topic" value="${session.topic || ''}">
            </div>
            
            <div class="mb-3">
              <label class="form-label">Notes</label>
              <textarea class="form-control" name="notes" rows="3">${session.notes || ''}</textarea>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Approach</label>
              <textarea class="form-control" name="approach" rows="2">${session.approach || ''}</textarea>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Goals</label>
              <textarea class="form-control" name="goals" rows="2">${session.goals || ''}</textarea>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Next Steps</label>
              <textarea class="form-control" name="nextsteps" rows="2">${session.nextsteps || ''}</textarea>
            </div>
            
            ${session.attachments ? `
              <div class="mb-3">
                <label class="form-label">Existing Attachments</label>
                <div id="existingAttachments">
                  ${session.attachments.split(',').map((url, idx) => {
                    const filename = url.split('/').pop();
                    return `
                      <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <input type="checkbox" checked data-url="${url}" id="attach_${idx}" style="margin-right: 8px;">
                        <label for="attach_${idx}">${filename}</label>
                      </div>
                    `;
                  }).join('')}
                </div>
                <small class="text-muted">Uncheck to remove</small>
              </div>
            ` : ''}
            
            <div class="mb-3">
              <label class="form-label">Add New Attachments</label>
              <input type="file" class="form-control" name="attachments" multiple>
            </div>
            
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary">Save Changes</button>
            </div>
          </form>
        </div>
      </div>
    `;
    
    showModal(modalHTML);
    
    // Handle form submission
    document.getElementById('editSessionForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData(e.target);
      
      // Collect checked attachments
      const checkedAttachments = [];
      document.querySelectorAll('#existingAttachments input[type="checkbox"]:checked').forEach(cb => {
        checkedAttachments.push(cb.dataset.url);
      });
      
      if (checkedAttachments.length > 0) {
        formData.append('existing_attachments', checkedAttachments.join(','));
      }
      
      try {
        const response = await fetch(`/session/${sessionId}?coach_id=${coachId}`, {
          method: 'PUT',
          body: formData
        });
        
        if (response.ok) {
          closeModal();
          // Reload the coachee's sessions
          const coacheeResponse = await fetch(`/coachee/${coacheeId}`);
          const coachee = await coacheeResponse.json();
          viewCoacheeSessions(coacheeId, `${coachee.firstname} ${coachee.lastname}`);
        } else {
          alert('Failed to update session');
        }
      } catch (error) {
        console.error('Error updating session:', error);
        alert('Failed to update session');
      }
    });
  } catch (error) {
    console.error('Error loading session for edit:', error);
    alert('Failed to load session');
  }
}

// ---- Delete session ----
async function deleteSession(sessionId, coacheeId, coacheeName) {
  if (!confirm('Are you sure you want to delete this session?')) {
    return;
  }
  
  try {
    const response = await fetch(`/session/${sessionId}?coach_id=${coachId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      // Reload sessions list
      viewCoacheeSessions(coacheeId, coacheeName);
    } else {
      alert('Failed to delete session');
    }
  } catch (error) {
    console.error('Error deleting session:', error);
    alert('Failed to delete session');
  }
}

// ---- Initialize on page load ----
document.addEventListener('DOMContentLoaded', () => {
  loadCoachProfile();
  loadCoachees();
});
