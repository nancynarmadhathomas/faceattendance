// ── Dashboard Search ──────────────────────────
function searchDashboard(query) {
  const q = query.toLowerCase().trim();
  
  // 1. Today's Attendance Table
  document.querySelectorAll('#today-table tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });

  // 2. Recent Activity Feed
  document.querySelectorAll('#activity-feed .feed-item').forEach(item => {
    const text = item.innerText.toLowerCase();
    item.style.display = text.includes(q) ? 'flex' : 'none';
  });

  // 3. Late Employees Table
  document.querySelectorAll('#late-table tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });

  // 4. Employees Table (if active)
  document.querySelectorAll('#emp-table tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

// ── Dropdowns ──────────────────────────────────
function toggleDropdown(id) {
  const menu = document.getElementById(id);
  if (!menu) return;

  // Close others
  document.querySelectorAll('.dropdown-menu').forEach(m => {
    if (m.id !== id) m.classList.remove('show');
  });
  menu.classList.toggle('show');
}

// Close dropdowns on outside click
window.addEventListener('click', (e) => {
  if (!e.target.closest('.dropdown-container')) {
    document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.remove('show'));
  }
});

// ── Toasts ─────────────────────────────────────
function showToast(msg, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? 'check-circle' : 'alert-circle';
  const finalMsg = type === 'success' ? 'Action completed successfully' : (msg || 'Action failed');
  
  toast.innerHTML = `
    <i data-lucide="${icon}" style="width:20px;height:20px"></i>
    <div class="toast-msg">${finalMsg}</div>
  `;
  
  container.appendChild(toast);
  lucide.createIcons();

  // Auto-hide
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px) scale(0.95)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── Table filtering (Employees Page Legacy) ─────
function filterTable(bodyId, query) {
  const q = query.toLowerCase();
  document.querySelectorAll(`#${bodyId} tr`).forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// ── Meeting Functions ──────────────────────────
function showMeetingModal() {
  document.getElementById('meeting-modal').classList.remove('hidden');
}

async function saveMeeting() {
  const title = document.getElementById('m-title').value;
  const date  = document.getElementById('m-date').value;
  const time  = document.getElementById('m-time').value;
  const emp   = document.getElementById('m-emp').value;
  const desc  = document.getElementById('m-desc').value;

  if (!title || !date || !time) {
    showToast('Failed', 'error');
    return;
  }

  try {
    const res = await fetch('/api/admin/meeting', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, date, time, employee_id: emp, description: desc })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast('Failed', 'error');
    }
  } catch (err) {
    showToast('Failed', 'error');
  }
}

// ── Employee Functions ─────────────────────────
function showEmployeeModal() {
  document.getElementById('employee-modal').classList.remove('hidden');
}

async function saveEmployee() {
  const eid   = document.getElementById('e-id').value;
  const ename = document.getElementById('e-name').value;
  const email = document.getElementById('e-email').value;
  const role  = document.getElementById('e-role').value;

  if (!eid || !ename) {
    showToast('Employee ID and Name are required.', 'error');
    return;
  }

  try {
    const res = await fetch('/api/admin/add-employee', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_id: eid, name: ename, email: email, role: role })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Success');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.message || 'Failed', 'error');
    }
  } catch (err) {
    showToast('Network error while adding employee.', 'error');
  }
}

// ── Actions ─────────────────────────────────────
async function leaveAction(id, action) {
  try {
    const res  = await fetch(`/api/admin/leave/${id}/${action}`, { method:'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('Success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast('Failed', 'error');
    }
  } catch (err) {
    showToast('Failed', 'error');
  }
}

async function deleteEmployee(id) {
  if (!confirm(`Are you sure you want to delete employee ${id}?`)) return;
  try {
    const res = await fetch(`/api/admin/employee/${id}`, { method:'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Success');
      document.getElementById(`erow-${id}`)?.remove();
    } else {
      showToast('Failed', 'error');
    }
  } catch (err) {
    showToast('Failed', 'error');
  }
}

async function deleteMeeting(id) {
  if (!confirm('Are you sure you want to delete this meeting?')) return;
  try {
    const res = await fetch(`/api/admin/meeting/${id}`, { method:'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Success');
      document.getElementById(`mcard-${id}`)?.remove();
    } else {
      showToast('Failed', 'error');
    }
  } catch (err) {
    showToast('Failed', 'error');
  }
}

// ── Theme Toggle ──────────────────────────────
const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    const icon = themeToggle.querySelector('i');
    icon.setAttribute('data-lucide', isLight ? 'sun' : 'moon');
    lucide.createIcons();
  });
  
  if (localStorage.getItem('theme') === 'light') {
    document.body.classList.add('light-theme');
    themeToggle.querySelector('i').setAttribute('data-lucide', 'sun');
  }
}

// Init icons
lucide.createIcons();
