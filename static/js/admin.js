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

async function toggleNotifications() {
  const menu = document.getElementById('notificationDropdown');
  if (!menu) return;
  menu.classList.toggle('show');
}

// Close dropdowns on outside click
window.addEventListener('click', (e) => {
  if (!e.target.closest('.dropdown-container') && !e.target.closest('.admin-menu')) {
    document.querySelectorAll('.notification-dropdown, .admin-dropdown').forEach(m => m.classList.remove('show'));
  }
});

// ── Toasts ─────────────────────────────────────
function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.innerText = message;
  toast.className = "toast show " + type;

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

// ── Table filtering (Employees Page Legacy) ─────
function filterTable(bodyId, query) {
  const q = query.toLowerCase();
  document.querySelectorAll(`#${bodyId} tr`).forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

function filterMeetings(query) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll('.meeting-card').forEach(card => {
    const text = card.innerText.toLowerCase();
    card.style.display = text.includes(q) ? '' : 'none';
  });
}

// ── Meeting Functions ──────────────────────────
function showMeetingModal() {
  document.getElementById('meeting-modal').classList.add('show');
}

function toggleMeetingFields() {
  const type = document.getElementById('m-type').value;
  document.getElementById('m-link-group').style.display = type === 'Virtual' ? 'block' : 'none';
  document.getElementById('m-loc-group').style.display = type === 'Physical' ? 'block' : 'none';
}

async function saveMeeting() {
  const title = document.getElementById('m-title').value;
  const date  = document.getElementById('m-date').value;
  const time  = document.getElementById('m-time').value;
  const emp   = document.getElementById('m-emp').value;
  const desc  = document.getElementById('m-desc').value;
  const mType = document.getElementById('m-type').value;
  const link  = document.getElementById('m-link').value;
  const loc   = document.getElementById('m-loc').value;

  if (!title || !date || !time) {
    showToast('Title, date, and time are required.', 'error');
    return;
  }

  try {
    const res = await fetch('/api/admin/meeting', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        title, date, time, 
        user_id: emp, description: desc,
        type: mType, link: link, location: loc
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Meeting scheduled successfully');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.message || 'Failed to schedule', 'error');
    }
  } catch (err) {
    showToast('Network error while scheduling.', 'error');
  }
}

// ── Employee Functions ─────────────────────────
function showEmployeeModal() {
  document.getElementById('employee-modal').classList.add('show');
}

async function saveEmployee() {
  const eid   = document.getElementById('e-id').value;
  const ename = document.getElementById('e-name').value;
  const email = document.getElementById('e-email').value;
  const role  = document.getElementById('e-role').value;

  if (!eid || !ename) {
    showToast('User ID and Name are required.', 'error');
    return;
  }

  try {
    const res = await fetch('/api/admin/add-employee', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: eid, name: ename, email: email, role: role })
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
// ── Actions ─────────────────────────────────────
async function leaveAction(user_id, from_date, action) {
  try {
    const res = await fetch(`/api/admin/leave/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user_id, from_date: from_date })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Leave request processed');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast('Failed to process leave', 'error');
    }
  } catch (err) {
    showToast('Network error', 'error');
  }
}

async function deleteEmployee(id) {
  showConfirm(`Are you sure you want to delete employee ${id}?`, async () => {
    try {
      const res = await fetch(`/api/admin/employee/${id}`, { method:'DELETE' });
      const data = await res.json();
      if (data.success) {
        showToast('Employee deleted successfully');
        document.getElementById(`erow-${id}`)?.remove();
      } else {
        showToast(data.error || 'Delete failed', 'error');
      }
    } catch (err) {
      showToast('Network error during delete', 'error');
    }
  });
}

async function deleteMeeting(id, event) {
  if (event) event.stopPropagation();
  showConfirm('Are you sure you want to delete this meeting?', async () => {
    try {
      const res = await fetch(`/api/meetings/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        showToast('Meeting deleted');
        // Remove card immediately
        const card = document.getElementById(`meeting-card-${id}`);
        if (card) {
          card.style.opacity = '0';
          card.style.transform = 'scale(0.95)';
          card.style.transition = 'all 0.3s ease';
          setTimeout(() => card.remove(), 300);
        }
      } else {
        showToast(data.error || 'Failed to delete meeting', 'error');
      }
    } catch (err) {
      showToast('Network error while deleting meeting.', 'error');
    }
  });
}

// ── Theme Management ──────────────────────────
function setAdminTheme(theme) {
  if (theme === 'light') {
    document.body.classList.add('light-mode');
    document.body.classList.remove('dark-mode');
    localStorage.setItem('admin-theme', 'light');
    const icon = document.getElementById('theme-icon');
    if (icon) icon.setAttribute('data-lucide', 'moon');
  } else {
    document.body.classList.add('dark-mode');
    document.body.classList.remove('light-mode');
    localStorage.setItem('admin-theme', 'dark');
    const icon = document.getElementById('theme-icon');
    if (icon) icon.setAttribute('data-lucide', 'sun');
  }
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

function toggleAdminTheme() {
  const isLight = document.body.classList.contains('light-mode');
  setAdminTheme(isLight ? 'dark' : 'light');
}

// Initial theme setup (will be called in DOMContentLoaded)
function initTheme() {
  const savedTheme = localStorage.getItem('admin-theme') || 'dark';
  setAdminTheme(savedTheme);
}

// Init icons
lucide.createIcons();

// ── PDF Export ────────────────────────────────
function getVisibleTableData(tableId) {
  const table = document.querySelector(tableId);
  if (!table) return null;
  
  const headers = [];
  table.querySelectorAll('thead th').forEach(th => {
    if (th.innerText.toLowerCase() !== 'actions') {
      headers.push(th.innerText);
    }
  });
  
  const rows = [];
  table.querySelectorAll('tbody tr').forEach(tr => {
    if (tr.style.display !== 'none') {
      const rowData = [];
      tr.querySelectorAll('td').forEach((td, index) => {
        // Skip action column
        const header = table.querySelectorAll('thead th')[index];
        if (header && header.innerText.toLowerCase() !== 'actions') {
          rowData.push(td.innerText.split('\n')[0]); // Take main text, remove subtext
        }
      });
      if (rowData.length > 0) rows.push(rowData);
    }
  });
  
  return { headers, rows };
}

async function exportDashboardToPDF() {
  const { jsPDF } = window.jspdf;
  const container = document.querySelector('.admin-main');
  if (!container) {
    showToast("Export target container not found", "error");
    return;
  }

  // Determine Context-Aware Filename & Title
  const path = window.location.pathname;
  let filename = 'admin_report.pdf';
  let reportTitle = 'Administrative Report';

  if (path.includes('attendance')) { 
      filename = 'attendance_report.pdf'; 
      reportTitle = 'Attendance History Report'; 
  } else if (path.includes('employees')) { 
      filename = 'employees_report.pdf'; 
      reportTitle = 'Employee Directory Report'; 
  } else if (path.includes('meetings')) { 
      filename = 'meetings_report.pdf'; 
      reportTitle = 'Meetings & Schedule Report'; 
  } else if (path.includes('leaves')) { 
      filename = 'leaves_report.pdf'; 
      reportTitle = 'Leave Requests & Status Report'; 
  } else if (path.includes('analytics')) { 
      filename = 'analytics_report.pdf'; 
      reportTitle = 'Analytics Dashboard Report'; 
  } else if (path.includes('projects')) { 
      filename = 'projects_report.pdf'; 
      reportTitle = 'Project Assignments Report'; 
  } else if (path.includes('db')) {
      filename = 'database_view_report.pdf';
      reportTitle = 'System Database View';
  }

  // UI Feedback: Loading State
  const btn = document.querySelector('button[onclick="exportDashboardToPDF()"]');
  const originalContent = btn ? btn.innerHTML : 'Export PDF';
  if (btn) {
    btn.innerHTML = '<i data-lucide="loader" class="spin"></i> Generating Full Report...';
    if (window.lucide) lucide.createIcons();
    btn.disabled = true;
  }

  try {
    // Capture the entire scrollable area
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#0f172a', // Preserve dark theme background
      scrollY: -window.scrollY,
      windowWidth: container.scrollWidth,
      windowHeight: container.scrollHeight
    });

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('l', 'mm', 'a4'); // Landscape A4
    
    const imgProps = pdf.getImageProperties(imgData);
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const imgHeight = (imgProps.height * pdfWidth) / imgProps.width;
    
    let heightLeft = imgHeight;
    let position = 0;

    // Add high-resolution image to PDF, splitting into pages if necessary
    pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
    heightLeft -= pdfHeight;

    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
      heightLeft -= pdfHeight;
    }

    pdf.save(filename);
    showToast(`${reportTitle} exported successfully`);

  } catch (err) {
    console.error("PDF Export Error:", err);
    showToast("Failed to generate PDF report", "error");
  } finally {
    if (btn) {
      btn.innerHTML = originalContent;
      btn.disabled = false;
      if (window.lucide) lucide.createIcons();
    }
  }
}

// ── Real-time Clock ───────────────────────────
function updateClock() {
    const timeEl = document.getElementById('live-time');
    const dateEl = document.getElementById('live-date');
    if (!timeEl || !dateEl) return;

    const now = new Date();
    
    // Time format: 14:05:22
    timeEl.textContent = now.toLocaleTimeString('en-GB', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
    });

    // Date format: THU, 09 APRIL 2026
    dateEl.textContent = now.toLocaleDateString('en-GB', { 
        weekday: 'short', 
        day: '2-digit', 
        month: 'long', 
        year: 'numeric' 
    }).toUpperCase();
}

// Initialize clock, theme, and modals
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    
    // Theme consistency
    initTheme();

    if (window.lucide) lucide.createIcons();

    // Ensure modals are at body level for absolute overlay reliability
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        document.body.appendChild(modal);
    });

    // Admin Dropdown Toggle
    const adminBtn = document.getElementById('adminBtn');
    const adminDropdown = document.getElementById('adminDropdown');
    
    if (adminBtn && adminDropdown) {
        adminBtn.onclick = function(e) {
            e.stopPropagation();
            adminDropdown.classList.toggle('show');
        };
        
        window.addEventListener('click', function(e) {
            if (!e.target.closest('.admin-menu')) {
                adminDropdown.classList.remove('show');
            }
        });
    }
});
