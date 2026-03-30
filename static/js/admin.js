// ── Tabs ─────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.remove('hidden');
  
  // Find the button that was clicked and activate it
  const btn = Array.from(document.querySelectorAll('.nav-btn')).find(b => b.innerText.toLowerCase().includes(name.toLowerCase()));
  if (btn) btn.classList.add('active');
}

// ── Table search ─────────────────────────────
function filterTable(bodyId, query) {
  const q = query.toLowerCase();
  document.querySelectorAll(`#${bodyId} tr`).forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// ── Meeting Modal ─────────────────────────────
function showMeetingModal() {
  document.getElementById('m-date').value = new Date().toISOString().slice(0,10);
  document.getElementById('meeting-modal').classList.remove('hidden');
}

async function saveMeeting() {
  const title = document.getElementById('m-title').value.trim();
  const date  = document.getElementById('m-date').value;
  const time  = document.getElementById('m-time').value;
  const errEl = document.getElementById('meeting-err');

  if (!title || !date || !time) {
    errEl.textContent = 'Title, date and time are required.';
    errEl.style.display = 'block';
    return;
  }
  errEl.style.display = 'none';

  const res = await fetch('/api/admin/meeting', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      title, date, time,
      description: document.getElementById('m-desc').value.trim(),
      employee_id: document.getElementById('m-emp').value || null
    })
  });
  const r = await res.json();
  if (r.success) {
    document.getElementById('meeting-modal').classList.add('hidden');
    location.reload();
  }
}

// ── Delete Meeting ────────────────────────────
async function deleteMeeting(id) {
  if (!confirm('Delete this meeting?')) return;
  await fetch(`/api/admin/meeting/${id}`, { method:'DELETE' });
  const card = document.getElementById('mcard-' + id);
  if (card) card.remove();
}

// ── Delete Employee ───────────────────────────
async function deleteEmployee(id) {
  if (!confirm(`Delete employee ${id} and all their records?`)) return;
  await fetch(`/api/admin/employee/${id}`, { method:'DELETE' });
  const row = document.getElementById('erow-' + id);
  if (row) row.remove();
}

// ── Leave Actions ─────────────────────────────
async function leaveAction(id, action) {
  const label = action === 'approve' ? 'Approve' : 'Reject';
  if (!confirm(`${label} this leave request?`)) return;
  const res  = await fetch(`/api/admin/leave/${id}/${action}`, { method:'POST' });
  const data = await res.json();
  if (data.success) {
    const row = document.getElementById('lrow-' + id);
    if (row) {
      row.cells[6].innerHTML = action === 'approve'
        ? '<span class="badge badge-present">Approved</span>'
        : '<span class="badge badge-absent">Rejected</span>';
      row.cells[7].innerHTML = '<span class="text-muted" style="font-size:.8rem">—</span>';
    }
  }
}

// Init Lucide icons
lucide.createIcons();
