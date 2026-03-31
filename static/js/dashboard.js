// ── Dashboard State & Timer ──────────────────────────────────────────
let timerInterval = null;

function updateDashboardUI(data) {
  if (!data) return;
  const state = window.DASHBOARD_STATE = { ...window.DASHBOARD_STATE, ...data };
  
  // 1. Sidebar Status (Added back for simple Logged In/Out state)
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
      if (state.working_hours > 0) {
        btnContainer.innerHTML = `<div class="badge-pill badge-muted">Clocked out · ${state.check_out_time || '--:--'}</div>`;
      } else {
        btnContainer.innerHTML = '<button id="checkin-btn" onclick="doCheckin()" class="btn-checkout" style="background:linear-gradient(135deg,#10b981,#059669);color:#fff;border-color:transparent"><i data-lucide="clock" style="width:14px;height:14px;vertical-align:middle;margin-right:4px"></i>Clock In</button>';
      }
    } else {
      btnContainer.innerHTML = '<button id="checkout-btn" onclick="doCheckout()" class="btn-checkout"><i data-lucide="log-out" style="width:14px;height:14px;vertical-align:middle;margin-right:4px"></i>Clock Out</button>';
    }
  }

  // 2. Banner Stat (Keep for now unless asked to remove)
  const pill = document.getElementById('today-status-pill');
  if (pill) {
    pill.className = `pill pill-${state.status}`;
    pill.textContent = state.status.charAt(0).toUpperCase() + state.status.slice(1);
  }
  const timeVal = document.getElementById('checkin-time-val');
  if (timeVal) timeVal.textContent = state.check_in_time || '--:--:--';

  // 3. Working Hours Timer Logic
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
