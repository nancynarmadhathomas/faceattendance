// ── Camera ──────────────────────────────────────────────────────
const video = document.getElementById('video');
let stream;
let scanInterval;
let isLoginTriggered = false;
let isVerifying = false;

async function startCamera() {
  const constraints = { 
    video: { 
      width: { ideal: 640 }, 
      height: { ideal: 640 }, 
      facingMode: 'user' 
    } 
  };
  
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Browser does not support camera access or not in a secure context.');
    }
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = stream;
    video.onloadedmetadata = () => video.play();
  } catch(e) {
    console.error("Camera Error:", e);
    // Generic fallback for older browsers or strict environments
    try {
      console.log("Retrying with simple constraints...");
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      video.srcObject = stream;
      video.onloadedmetadata = () => video.play();
    } catch(e2) {
      showToast('Camera access denied. Please allow camera permissions in your browser settings.', 'danger');
    }
  }
  
  // Start auto-scan once camera is active
  if (stream && !scanInterval) {
    scanInterval = setInterval(() => {
      if (!isLoginTriggered && !isVerifying) {
        captureAndVerify();
      }
    }, 1500);
  }
}

function stopCamera() {
  if (stream) stream.getTracks().forEach(t => t.stop());
  if (scanInterval) {
    clearInterval(scanInterval);
    scanInterval = null;
  }
}

// ── Capture ──────────────────────────────────────────────────────
function updateStatus(text, type = 'primary') {
  const lbl = document.getElementById('status-label');
  if (!lbl) return;
  lbl.textContent = text;
  lbl.style.color = type === 'success' ? '#10b981' : (type === 'danger' ? '#ef4444' : '#6366f1');
}

async function captureAndVerify() {
  if (isLoginTriggered || isVerifying) return;
  
  isVerifying = true;
  updateStatus('Analyzing...');
  document.getElementById('register-prompt').style.display = 'none';

  const canvas = document.createElement('canvas');
  canvas.width  = video.videoWidth  || 640;
  canvas.height = video.videoHeight || 640;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const imageData = canvas.toDataURL('image/jpeg', 0.85);

  try {
    const res = await fetch('/api/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: imageData })
    });
    const result = await res.json();

    if (result.success) {
      isLoginTriggered = true;
      stopCamera();
      updateStatus('Login successful', 'success');
      showToast(`✅ Welcome, ${result.name}! Redirecting...`, 'success');
      setTimeout(() => window.location.href = result.redirect, 1000);
    } else {
      updateStatus('Looking for face...');
      
      // Show register prompt if face not registered
      if (result.message && result.message.toLowerCase().includes('not registered')) {
        showToast('❌ ' + result.message, 'danger');
        document.getElementById('register-prompt').style.display = 'block';
      }
      isVerifying = false;
    }
  } catch(e) {
    console.error(e);
    updateStatus('Looking for face...');
    isVerifying = false;
  }
}

// ── Late reason ──────────────────────────────────────────────────
async function submitLateReason() {
  const reason = document.getElementById('late-reason').value.trim();
  if (!reason) { alert('Please select a reason.'); return; }
  const btn = document.getElementById('late-submit-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Submitting...';
  await fetch('/api/late-reason', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ reason })
  });
  window.location.href = window._redirect || '/dashboard';
}


// ── Toast helper ─────────────────────────────────────────────────
function showToast(msg, type='info') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.className = `toast toast-${type} mt-4`;
  t.textContent = msg;
  t.style.display = 'block';
}

startCamera();
