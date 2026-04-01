// ── Dashboard State & Timer ──────────────────────────────────────────
let timerInterval = null;

function formatTime(timeVal) {
  if (!timeVal || timeVal === '--:--' || timeVal === '--:--:--') return '--:--';
  try {
    // If it's already in a recognizable format like HH:MM:SS or HH:MM
    let [h, m] = timeVal.split(':');
    h = parseInt(h);
    const ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12;
    h = h ? h : 12; // the hour '0' should be '12'
    return `${h.toString().padStart(2, '0')}:${m} ${ampm}`;
  } catch (e) {
    return timeVal;
  }
}

function updateDashboardUI(data) {
  if (!data) return;
  const state = window.DASHBOARD_STATE = { ...window.DASHBOARD_STATE, ...data };
  
  // 1. Sidebar Status
  const sidebar = document.getElementById('sidebar-status');
  if (sidebar) {
    if (state.checked_in) {
      sidebar.innerHTML = '<span style="width:10px;height:10px;background:#10b981;border-radius:50%;display:inline-block"></span> Logged In';
      sidebar.style.color = '#10b981';
    } else {
      sidebar.innerHTML = '<span style="width:10px;height:10px;background:#94a3b8;border-radius:50%;display:inline-block"></span> Logged Out';
      sidebar.style.color = '#94a3b8';
    }
  }

  // 2. Action Buttons
  const btnContainer = document.getElementById('action-btn-container');
  if (btnContainer) {
    if (!state.checked_in) {
      if (state.working_hours > 0 || state.check_out_time) {
        btnContainer.innerHTML = `<div class="badge-pill badge-muted">Clocked out · ${formatTime(state.check_out_time)}</div>`;
      } else {
        btnContainer.innerHTML = '<button id="checkin-btn" onclick="doCheckin()" class="btn-checkout" style="background:linear-gradient(135deg,#10b981,#059669);color:#fff;border-color:transparent"><i data-lucide="clock" style="width:14px;height:14px;vertical-align:middle;margin-right:4px"></i>Clock In</button>';
      }
    } else {
      btnContainer.innerHTML = '<button id="checkout-btn" onclick="doCheckout()" class="btn-checkout"><i data-lucide="log-out" style="width:14px;height:14px;vertical-align:middle;margin-right:4px"></i>Clock Out</button>';
    }
  }

  // 3. Banner & Status
  const pill = document.getElementById('today-status-pill');
  if (pill) {
    const status = state.checked_in ? 'present' : (state.working_hours > 0 ? 'present' : (state.status || 'absent'));
    pill.className = `pill pill-${status}`;
    pill.textContent = status.charAt(0).toUpperCase() + status.slice(1);
  }
  
  const timeVal = document.getElementById('checkin-time-val');
  if (timeVal) timeVal.textContent = formatTime(state.check_in_time);

  const outTimeVal = document.getElementById('checkout-time-val');
  if (outTimeVal) outTimeVal.textContent = formatTime(state.check_out_time);

  // 4. Working Hours Timer Logic
  if (state.checked_in && state.check_in_time) {
    startWorkingHoursTimer(state.check_in_time);
  } else {
    stopWorkingHoursTimer();
    const liveHrs = document.getElementById('live-hours');
    if (liveHrs) liveHrs.textContent = (state.working_hours || 0) + 'h';
  }

  if (window.lucide) lucide.createIcons();
}

function startWorkingHoursTimer(checkInTimeStr) {
  stopWorkingHoursTimer();
  const liveHrs = document.getElementById('live-hours');
  const progBar = document.getElementById('work-progress-bar');
  const progLabel = document.getElementById('progress-label');

  // Parse Today's date + checkInTimeStr
  const now = new Date();
  const timeParts = checkInTimeStr.split(':');
  const checkInDate = new Date();
  checkInDate.setHours(parseInt(timeParts[0]), parseInt(timeParts[1]), parseInt(timeParts[2] || 0), 0);

  timerInterval = setInterval(() => {
    const current = new Date();
    const diffMs = current - checkInDate;
    if (diffMs < 0) return;
    
    const diffHrs = diffMs / (1000 * 60 * 60);
    const displayHrs = diffHrs.toFixed(2);
    
    if (liveHrs) liveHrs.textContent = displayHrs + 'h';
    if (progLabel) progLabel.textContent = `${displayHrs} / 9 hrs`;
    
    if (progBar) {
      const pct = Math.min(100, (diffHrs / 9 * 100));
      progBar.style.width = pct + '%';
      if (pct >= 90) progBar.style.background = 'var(--success)';
      else if (pct >= 50) progBar.style.background = 'var(--accent)';
      else progBar.style.background = 'var(--warn)';
    }
  }, 1000);
}

function stopWorkingHoursTimer() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = null;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    if (window.DASHBOARD_STATE) {
        updateDashboardUI(window.DASHBOARD_STATE);
    }
});

// ── Theme Toggle ──────────────────────────────────────────────────
const THEME_KEY = 'dash_theme';

function applyTheme(theme) {
  document.body.setAttribute('data-theme', theme);
  const icon  = document.getElementById('theme-icon');
  const label = document.getElementById('theme-label');
  if (theme === 'light') {
    if (icon)  icon.innerHTML  = '<i data-lucide="moon" style="width:14px;height:14px"></i>';
    if (label) label.textContent = 'Dark Mode';
  } else {
    if (icon)  icon.innerHTML  = '<i data-lucide="sun" style="width:14px;height:14px"></i>';
    if (label) label.textContent = 'Light Mode';
  }
  localStorage.setItem(THEME_KEY, theme);
  if (window.lucide) lucide.createIcons();
}

function toggleTheme() {
  const current = document.body.getAttribute('data-theme') || 'dark';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

// Apply saved theme immediately
(function() {
  const saved = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(saved);
})();

// Live clock + date
(function tick() {
  const now = new Date();
  const t = document.getElementById('live-time');
  const d = document.getElementById('live-date');
  if (t) t.textContent = now.toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  if (d) d.textContent = now.toLocaleDateString('en-US', { weekday:'short', year:'numeric', month:'short', day:'numeric' });
  setTimeout(tick, 1000);
})();

// Section navigation
function showSection(id, el) {
  document.querySelectorAll('.dash-section').forEach(s => s.classList.add('hidden'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const sec = document.getElementById(id);
  if (sec) sec.classList.remove('hidden');
  if (el) el.classList.add('active');
}

// Clock in
async function doCheckin() {
  const btn = document.getElementById('checkin-btn');
  if (!btn) return;
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.textContent = '⏳ ...';
  
  try {
    const res  = await fetch('/api/checkin', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      if (data.late) {
        document.getElementById('late-modal').classList.remove('hidden');
      }
      updateDashboardUI(data);
      // Optional toast
      console.log('Clocked in successfully');
    } else {
      alert('❌ ' + (data.message || 'Clock-in failed.'));
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  } catch (e) {
    alert('Server error. Please try again.');
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

// Global late reason confirmation
async function confirmLateReason() {
  const select = document.getElementById('late-reason-select');
  const reason = select ? select.value : '';
  
  if (!reason) {
    alert('⚠️ Please select a reason for late arrival.');
    return;
  }

  const btn = document.getElementById('late-confirm-btn');
  const originalText = btn ? btn.textContent : 'Confirm';
  if (btn) {
    btn.disabled = true;
    btn.textContent = '⏳ Submitting...';
  }

  try {
    const res = await fetch('/api/late-reason', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });
    const data = await res.json();
    
    if (data.success) {
      console.log('Late reason captured:', reason);
      document.getElementById('late-modal').classList.add('hidden');
      // Success feedback (optional toast could go here)
    } else {
      alert('❌ Failed to save reason. Please try again.');
    }
  } catch (e) {
    console.error('Error in confirmLateReason:', e);
    alert('Server error. Please try again.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }
}

// Clock out
async function doCheckout() {
  const btn = document.getElementById('checkout-btn');
  if (!btn) return;
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.textContent = '⏳ ...';
  
  try {
    const res = await fetch('/api/checkout', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      updateDashboardUI(data);
      alert('✅ Clocked out! You worked ' + data.working_hours + ' hour(s) today.');
    } else {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  } catch (e) {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

// FAB Toggle Logic
function toggleFAB() {
  const panel = document.getElementById('fab-panel');
  const icon = document.getElementById('fab-icon');
  if (!panel || !icon) return;

  const isActive = panel.classList.toggle('active');
  if (isActive) {
    icon.setAttribute('data-lucide', 'x');
  } else {
    icon.setAttribute('data-lucide', 'plus');
  }
  if (window.lucide) lucide.createIcons();
}

// Close FAB when clicking outside
document.addEventListener('click', (e) => {
  const container = document.querySelector('.fab-container');
  const panel = document.getElementById('fab-panel');
  if (container && !container.contains(e.target)) {
    if (panel && panel.classList.contains('active')) {
      toggleFAB();
    }
  }
});

// Poll meetings
async function pollMeetings() {
  try {
    const res = await fetch('/api/meetings');
    const meets = await res.json();
    const today = new Date().toISOString().slice(0, 10);
    const count = meets.filter(m => m.meeting_date === today).length;
    const badge = document.querySelector('.nav-badge');
    if (badge && count > 0) badge.textContent = count;
  } catch (e) {}
}
setInterval(pollMeetings, 30000);

// Leave Request
async function submitLeaveRequest() {
  const leaveType = document.getElementById('leave-type').value;
  const fromDate  = document.getElementById('leave-from').value;
  const toDate    = document.getElementById('leave-to').value;
  const reason    = document.getElementById('leave-reason').value.trim();
  const msgEl     = document.getElementById('leave-msg');
  const btn       = document.getElementById('leave-submit-btn');

  if (!leaveType || !fromDate || !toDate) {
    msgEl.className = 'toast toast-danger';
    msgEl.textContent = '⚠️ Please fill Leave Type, From Date and To Date.';
    msgEl.style.display = 'block';
    return;
  }
  btn.disabled = true;
  btn.textContent = '⏳ Submitting...';
  
  try {
    const res  = await fetch('/api/leave-request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ leave_type: leaveType, from_date: fromDate, to_date: toDate, reason })
    });
    if ((await res.json()).success) {
      msgEl.className = 'toast toast-success';
      msgEl.textContent = '✅ Leave request submitted successfully!';
      msgEl.style.display = 'block';
      setTimeout(() => location.reload(), 1500);
    }
  } catch(e) {}
  btn.disabled = false;
  btn.textContent = '📨 Submit Request';
}

// ── Meeting Responses ──────────────────────────────────────────
let current_meeting_id = null;

async function respondMeeting(meeting_id, status, reason = null) {
  try {
    const res = await fetch('/api/meeting/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meeting_id, status, reason })
    });
    const result = await res.json();
    if (result.success) {
      location.reload();
    } else {
      alert('❌ Failed to save response.');
    }
  } catch (e) {
    alert('Server error. Please try again.');
  }
}

function openDeclineModal(meeting_id) {
  current_meeting_id = meeting_id;
  document.getElementById('decline-reason').value = '';
  document.getElementById('decline-modal').classList.remove('hidden');
}

async function submitDecline() {
  const reason = document.getElementById('decline-reason').value.trim();
  if (!reason) {
    alert('Please enter a reason for declining.');
    return;
  }
  await respondMeeting(current_meeting_id, 'declined', reason);
  document.getElementById('decline-modal').classList.add('hidden');
}

// ── Projects ───────────────────────────────────────────────────────
async function respondProject(project_id, response) {
  try {
    const res = await fetch('/api/project/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id, response })
    });
    const result = await res.json();
    if (result.success) {
      alert(`Response: ${response} saved!`);
      location.reload();
    } else {
      alert('❌ Failed to save response.');
    }
  } catch (e) {
    alert('Server error. Please try again.');
  }
}

function handleNotificationClick(text, type, projectId, el) {
  const msg = text.toLowerCase();
  
  // 1. Meeting Notifications
  if (msg.includes('meeting')) {
    window.location.href = '/meetings';
    return;
  }
  
  // 2. Leave Notifications
  if (msg.includes('leave')) {
    window.location.href = '/leave-request';
    return;
  }
  
  // 3. Project Notifications
  if (msg.includes('project')) {
    window.location.href = '/project-work';
    return;
  }
  
  // 4. Attendance & Late Notifications
  if (msg.includes('late') || msg.includes('attendance') || msg.includes('clock in') || msg.includes('clock out')) {
    window.location.href = '/attendance';
    return;
  }
  
  // 5. Employee Notifications
  if (msg.includes('employee')) {
    window.location.href = '/employees';
    return;
  }
  
  // Default fallback: expand project info if it's a project and hasn't navigated
  if (projectId) {
    const infoDiv = document.getElementById(`inline-project-${projectId}`);
    if (infoDiv) {
      infoDiv.classList.toggle('hidden');
      if (!infoDiv.classList.contains('hidden')) {
        if (typeof loadProjectDetailsInline === 'function') {
          loadProjectDetailsInline(projectId);
        }
      }
    }
  } else {
    window.location.href = '/dashboard';
  }
}



