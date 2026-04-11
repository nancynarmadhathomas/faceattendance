/**
 * FaceAttend Unified Notification System
 * Replaces native alert(), confirm(), and prompt()
 */

const Notifications = {
  // ── Toast Logic ──────────────────────────────────────────
  showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Select icon based on type
    let iconName = 'check-circle';
    if (type === 'error') iconName = 'alert-octagon';
    if (type === 'warning') iconName = 'alert-triangle';
    if (type === 'info') iconName = 'info';

    toast.innerHTML = `
      <i data-lucide="${iconName}"></i>
      <div class="toast-msg">${message}</div>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    // Auto-hide after 3s
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px) scale(0.95)';
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  },

  // ── Confirmation Modal Logic ──────────────────────────────
  showConfirm(message, onConfirm, onCancel) {
    let overlay = document.getElementById('confirm-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'confirm-overlay';
      overlay.className = 'confirm-overlay';
      overlay.innerHTML = `
        <div class="confirm-modal">
          <div class="confirm-modal-icon">
            <i data-lucide="help-circle" style="width:32px;height:32px"></i>
          </div>
          <h3>Are you sure?</h3>
          <p id="confirm-text"></p>
          <div class="confirm-modal-actions">
            <button id="btn-confirm-cancel" class="btn-cancel">Cancel</button>
            <button id="btn-confirm-ok" class="btn-confirm">Confirm</button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
    }

    const textEl = overlay.querySelector('#confirm-text');
    const cancelBtn = overlay.querySelector('#btn-confirm-cancel');
    const okBtn = overlay.querySelector('#btn-confirm-ok');

    textEl.textContent = message;
    overlay.classList.add('show');
    if (window.lucide) lucide.createIcons();

    // Clean up previous listeners if any (reusing element)
    const newOkBtn = okBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newOkBtn, okBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

    newOkBtn.addEventListener('click', () => {
      overlay.classList.remove('show');
      if (onConfirm) onConfirm();
    });

    newCancelBtn.addEventListener('click', () => {
      overlay.classList.remove('show');
      if (onCancel) onCancel();
    });
  }
};

// Global shortcuts
window.showToast = Notifications.showToast;
window.showConfirm = Notifications.showConfirm;
