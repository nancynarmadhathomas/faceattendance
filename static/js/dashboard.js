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

// Apply saved theme immediately (before paint to avoid flash)
(function() {
  const saved = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(saved);
})();

// Live clock + date
(function tick() {

  const now = new Date();
  const t = document.getElementById('live-time');
  const d = document.getElementById('live-date');
  if (t) t.textContent = now.toLocaleTimeString('en-US',
    { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  if (d) d.textContent = now.toLocaleDateString('en-US',
    { weekday:'short', year:'numeric', month:'short', day:'numeric' });
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
  btn.disabled = true;
  btn.textContent = '⏳ Clocking in...';
  try {
    const res  = await fetch('/api/checkin', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      if (data.late) {
        // Show late-reason modal — do NOT reload yet
        document.getElementById('late-modal').classList.remove('hidden');
      } else {
        alert('✅ Clocked in! Status: Present');
        location.reload();
      }
    } else {
      alert('❌ ' + (data.message || 'Clock-in failed.'));
      btn.disabled = false;
      btn.textContent = '⏰ Clock In';
    }
  } catch (e) {
    alert('Server error. Please try again.');
    btn.disabled = false;
    btn.textContent = '⏰ Clock In';
  }
}

// Confirm late reason after clock-in
async function confirmLateReason() {
  const reason = document.getElementById('late-reason-select').value;
  if (!reason) { alert('Please select a reason.'); return; }
  const btn = document.getElementById('late-confirm-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Saving...';
  try {
    await fetch('/api/late-reason', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });
  } catch(e) {}
  location.reload();
}

// Clock out
async function doCheckout() {
  const btn = document.getElementById('checkout-btn');
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = '⏳ Clocking out...';
  try {
    const res = await fetch('/api/checkout', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      alert('✅ Clocked out! You worked ' + data.working_hours + ' hour(s) today.');
      location.reload();
    } else {
      btn.disabled = false;
      btn.textContent = '🏃 Clock Out';
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = '🏃 Clock Out';
  }
}

// Poll meetings every 30s for real-time updates
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

// ── Leave Request ─────────────────────────────────────────────────
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
  if (toDate < fromDate) {
    msgEl.className = 'toast toast-danger';
    msgEl.textContent = '⚠️ To Date cannot be before From Date.';
    msgEl.style.display = 'block';
    return;
  }

  btn.disabled = true;
  btn.textContent = '⏳ Submitting...';
  msgEl.style.display = 'none';

  try {
    const res  = await fetch('/api/leave-request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ leave_type: leaveType, from_date: fromDate, to_date: toDate, reason })
    });
    const data = await res.json();
    if (data.success) {
      msgEl.className = 'toast toast-success';
      msgEl.textContent = '✅ Leave request submitted successfully!';
      msgEl.style.display = 'block';
      // Reset form
      document.getElementById('leave-type').value = '';
      document.getElementById('leave-from').value = '';
      document.getElementById('leave-to').value   = '';
      document.getElementById('leave-reason').value = '';
      setTimeout(() => location.reload(), 1500);
    } else {
      msgEl.className = 'toast toast-danger';
      msgEl.textContent = '❌ ' + (data.message || 'Submission failed.');
      msgEl.style.display = 'block';
    }
  } catch(e) {
    msgEl.className = 'toast toast-danger';
    msgEl.textContent = '❌ Server error. Please try again.';
    msgEl.style.display = 'block';
  }

  btn.disabled = false;
  btn.textContent = '📨 Submit Request';
}
