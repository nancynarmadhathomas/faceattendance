let stream, _redirect = '/dashboard';

// Role selector
function selectRole(role) {
  document.getElementById('emp_role').value = role;
  const empCard   = document.getElementById('role-employee');
  const adminCard = document.getElementById('role-admin');
  if (role === 'employee') {
    empCard.style.background   = 'var(--primary-glow)';
    empCard.style.borderColor  = 'var(--primary)';
    adminCard.style.background = 'var(--surface2)';
    adminCard.style.borderColor= 'var(--border)';
  } else {
    adminCard.style.background  = 'rgba(139,92,246,.15)';
    adminCard.style.borderColor = '#8b5cf6';
    empCard.style.background    = 'var(--surface2)';
    empCard.style.borderColor   = 'var(--border)';
  }
}

function goStep2() {
  const id   = document.getElementById('emp_id').value.trim();
  const name = document.getElementById('emp_name').value.trim();
  const pass = document.getElementById('emp_pass').value;
  if (!id || !name || !pass) { alert('Please fill required fields (ID, Name, Password).'); return; }

  document.getElementById('step1').classList.add('hidden');
  document.getElementById('step2').classList.remove('hidden');
  document.getElementById('s1').classList.remove('active'); document.getElementById('s1').classList.add('done');
  document.getElementById('s2').classList.add('active');
  startCamera();
}

function goStep1() {
  stopCamera();
  document.getElementById('step2').classList.add('hidden');
  document.getElementById('step1').classList.remove('hidden');
  document.getElementById('s1').classList.add('active'); document.getElementById('s1').classList.remove('done');
  document.getElementById('s2').classList.remove('active');
}

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
    const video = document.getElementById('video');
    video.srcObject = stream;
    video.onloadedmetadata = () => video.play();
  } catch(e) {
    console.error("Camera Error:", e);
    // Generic fallback for older browsers or strict environments
    try {
      console.log("Retrying with simple constraints...");
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      const video = document.getElementById('video');
      video.srcObject = stream;
      video.onloadedmetadata = () => video.play();
    } catch(e2) {
      showRegToast('Camera access denied. Please allow camera permissions in your browser settings.', 'danger');
    }
  }
}

function stopCamera() {
  if (stream) stream.getTracks().forEach(t => t.stop());
}

async function submitRegister() {
  const btn = document.getElementById('reg-btn');
  btn.disabled = true; btn.textContent = '⏳ Registering...';

  const video  = document.getElementById('video');
  const canvas = document.createElement('canvas');
  canvas.width  = video.videoWidth  || 640;
  canvas.height = video.videoHeight || 640;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const imageData = canvas.toDataURL('image/jpeg', 0.85);

  const payload = {
    user_id:     document.getElementById('emp_id').value.trim(),
    title:       document.getElementById('emp_title').value,
    name:        document.getElementById('emp_name').value.trim(),
    email:       document.getElementById('emp_email').value.trim(),
    department:  '',
    password:    document.getElementById('emp_pass').value,
    role:        document.getElementById('emp_role').value,
    image:       imageData
  };

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      stopCamera();
      // FIX: Show success message then redirect to LOGIN page only
      showRegToast('✅ Registration Successful! Please login with your face.', 'success');
      setTimeout(() => window.location.href = result.redirect, 2000);
    } else {
      showRegToast('❌ ' + (result.message || 'Registration failed.'), 'danger');
      btn.disabled = false; btn.textContent = '📷 Capture & Register';
    }
  } catch(e) {
    showRegToast('Server error. Please try again.', 'danger');
    btn.disabled = false; btn.textContent = '📷 Capture & Register';
  }
}

function showRegToast(msg, type='info') {
  const t = document.getElementById('reg-toast');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  t.style.display = 'block';
}
