import os, base64, subprocess, json, uuid
from datetime import datetime, date
from flask import (Flask, render_template, request, jsonify,
                   session, redirect, url_for, Response)
from flask_cors import CORS
import numpy as np
from deepface import DeepFace
import db

app = Flask(__name__)
app.secret_key = 'face_attendance_secret_2026'
CORS(app, supports_credentials=True)

@app.template_filter('b64encode')
def b64encode_filter(s):
    if not s: return ""
    return base64.b64encode(s).decode('utf-8')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------------------------------------------
# DeepFace Native Face Engine Helpers
# ---------------------------------------------------------------------------
def generate_embedding(image_path):
    # --- STEP 1: FAST DETECTION (RUST) ---
    crop_path = image_path.replace('.jpg', '_crop.jpg')
    rust_bin = os.path.join('rust-face-engine', 'target', 'debug', 'rust-face-engine.exe')
    if not os.path.exists(rust_bin):
        # Fallback if binary not built
        rust_bin = "rust-face-engine.exe" 

    try:
        # Run Rust face detection
        cmd = [rust_bin, "detect", "--image", image_path, "--output", crop_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            res_json = json.loads(result.stdout)
            if res_json.get('success') and os.path.exists(crop_path):
                # SUCCESS: Face detected and cropped by Rust
                # --- STEP 2: ACCURATE VERIFICATION (DEEPFACE) ---
                # Use enforce_detection=False because Rust already detected/cropped it
                objs = DeepFace.represent(img_path=crop_path, model_name="ArcFace", enforce_detection=False)
                if len(objs) > 0:
                    embedding = objs[0]['embedding']
                    return {'success': True, 'embedding': embedding, 'method': 'hybrid'}
    except Exception as e:
        print(f"Hybrid detection failed or timed out: {e}")

    # --- FALLBACK: Standard DeepFace (if Rust fails or isn't built) ---
    try:
        objs = DeepFace.represent(img_path=image_path, model_name="ArcFace", enforce_detection=False)
        if len(objs) == 0:
            return {'success': False, 'message': 'Face not detected. Please align face.'}
        embedding = objs[0]['embedding']
        return {'success': True, 'embedding': embedding, 'method': 'deepface_only'}
    except Exception as e:
        return {'success': False, 'message': str(e)}


def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def compare_with_db(current_emb):
    """Return best matching employee or None. Balanced 0.55 ArcFace threshold."""
    employees = db.get_all_embeddings()
    best, best_dist = None, -1.0
    for emp in employees:
        emb = emp['face_embedding']
        if not emb:
            continue
        try:
            db_emb = json.loads(emb) if isinstance(emb, str) else emb
            dist = cosine_similarity(current_emb, db_emb)
            # 0.55 is a balanced threshold for ArcFace cosine similarity
            if dist > 0.55 and dist > best_dist:
                best_dist = dist
                best = emp
        except Exception:
            continue
    return best


# ---------------------------------------------------------------------------
# Attendance helpers
# ---------------------------------------------------------------------------
CUTOFF = (9, 30)   # 09:30 AM


def determine_status():
    now = datetime.now()
    if (now.hour, now.minute) <= CUTOFF:
        return 'Present'
    return 'Late'


# ---------------------------------------------------------------------------
# Routes — Pages
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    tab = request.args.get('tab', 'overview')
    return _render_employee_dashboard(tab)

@app.route('/project-work')
def project_work_page():
    return _render_employee_dashboard('project-work')

def _render_employee_dashboard(tab):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    emp = db.get_employee(session['user_id'])
    if not emp:
        session.clear()
        return redirect(url_for('index'))
        
    user_id      = session['user_id']
    history      = db.get_attendance_history(user_id)
    today_str    = __import__('datetime').date.today().isoformat()
    
    today_rec = None
    if history:
        if history[0].get('date') == today_str:
            today_rec = history[0]
    
    meetings     = db.get_meetings_for_employee(user_id)
    leave_reqs   = db.get_leave_requests_by_employee(user_id)
    monthly      = db.get_monthly_stats(user_id)
    leave_bal    = db.get_leave_balance(user_id)
    upcoming     = db.get_upcoming_meetings(user_id)
    notifs       = db.get_notifications(user_id)
    analytics    = db.get_employee_analytics(user_id)
    projects     = db.get_projects_for_employee(user_id)
    project_tasks = db.get_employee_project_tasks(user_id)
    latest       = history[0] if history else None

    return render_template('dashboard.html',
                           active_tab=tab,
                           emp=emp,
                           today=today_rec,
                           latest=latest,
                           history=history,
                           meetings=meetings,
                           leave_reqs=leave_reqs,
                           monthly=monthly,
                           leave_bal=leave_bal,
                           upcoming=upcoming,
                           notifs=notifs,
                           analytics=analytics,
                           projects=projects,
                           project_tasks=project_tasks,
                           today_date=today_str,
                           today_str=today_str,
                           fmt_time=db.fmt_time,
                           fmt_date=db.fmt_date)


@app.route('/attendance')
def attendance_nav():
    if 'user_id' not in session: return redirect(url_for('index'))
    return redirect(url_for('dashboard', tab='attendance'))

@app.route('/meetings')
def meetings_nav():
    if 'user_id' not in session: return redirect(url_for('index'))
    return redirect(url_for('dashboard', tab='meetings'))

@app.route('/leave-request')
def leave_nav():
    if 'user_id' not in session: return redirect(url_for('index'))
    return redirect(url_for('dashboard', tab='leave-sec'))



@app.route('/admin')
@app.route('/admin/<tab>')
def admin(tab='attendance'):
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return redirect(url_for('index'))
        
    # Sanitize and default
    active_tab = (tab or 'attendance').strip().lower()
    allowed = ['attendance', 'employees', 'meetings', 'leaves', 'reports', 'activity', 'analytics']
    if active_tab not in allowed:
        return redirect(url_for('admin', tab='attendance'))

    stats       = db.get_stats()
    employees   = db.get_all_employees()
    attend      = db.get_today_attendance()
    recent      = db.get_recent_attendance(10)
    meetings    = db.get_all_meetings()
    all_emps    = db.get_all_employees()
    leave_reqs  = db.get_all_leave_requests()
    admin_info  = db.get_employee(session.get('user_id'))

    # New Analytics Data (Only for Analytics tab)
    is_analytics = (active_tab == 'analytics')
    admin_analytics = db.get_admin_analytics('month') if is_analytics else {}
    details = db.get_admin_detailed_stats() if is_analytics else {}
    top_performers = db.get_top_performers() if is_analytics else []
    
    # Enrichment for attendance-only dashboard
    if is_analytics:
        details['live_status'] = db.get_live_status_analytics()
        details['avg_hours_analytics'] = db.get_avg_working_hours_analytics()
        details['frequent_late_analytics'] = db.get_frequent_late_analytics()
        details['leave_type_analytics'] = db.get_leave_type_analytics()
    
    return render_template('admin_dashboard.html',
                           active_tab=active_tab,
                           stats=stats,
                           admin_info=admin_info,
                           employees=employees,
                           attend=attend,
                           recent=recent,
                           meetings=meetings,
                           all_emps=all_emps,
                           leave_reqs=leave_reqs,
                           admin_analytics=admin_analytics,
                           details=details,
                           top_performers=top_performers,
                           fmt_time=db.fmt_time,
                           fmt_date=db.fmt_date)


@app.route('/admin/employee-profile/<user_id>')
def admin_employee_profile(user_id):
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return redirect(url_for('index'))
    
    emp = db.get_employee(user_id)
    if not emp:
        return redirect(url_for('admin', tab='employees'))
        
    admin_info = db.get_employee(session.get('user_id'))
    today_rec = db.get_today_record(user_id)
    analytics = db.get_employee_analytics(user_id)
    projects = db.get_employee_project_tasks(user_id)
    leaves = db.get_leave_requests_by_employee(user_id)
    leave_bal = db.get_leave_balance(user_id)
    
    # Calculate project counts
    proj_stats = {
        'total': len(projects),
        'accepted': len([p for p in projects if p.get('status') == 'accepted']),
        'pending': len([p for p in projects if p.get('status') == 'pending'])
    }
    
    # Get last leave date
    last_leave_date = None
    if leaves:
        last_leave_date = leaves[0].get('from_date')

    return render_template('admin_employee_profile.html',
                           emp=emp,
                           admin_info=admin_info,
                           today=today_rec,
                           analytics=analytics,
                           projects=projects,
                           proj_stats=proj_stats,
                           leaves=leaves,
                           leave_bal=leave_bal,
                           last_leave_date=last_leave_date,
                           fmt_date=db.fmt_date)


@app.route('/admin/db')
@app.route('/admin/db/<table_name>')
def admin_db(table_name='users'):
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return redirect(url_for('index'))
    
    # Map user-friendly name to actual table name
    actual_table = table_name
    if table_name == 'leaves':
        actual_table = 'leave_requests'
        
    columns, data = db.get_table_data(actual_table)
    admin_info = db.get_employee(session.get('user_id'))
    
    return render_template('admin_db.html', 
                           active_tab='db',
                           table_name=table_name,
                           columns=columns, 
                           data=data, 
                           admin_info=admin_info)


@app.route('/admin/projects')
def admin_projects():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return redirect(url_for('index'))
    projects = db.get_admin_project_list()
    employees = db.get_all_employees()
    admin_info = db.get_employee(session.get('user_id'))
    return render_template('admin_projects.html', 
                           projects=projects, 
                           employees=employees,
                           admin_info=admin_info)

@app.route('/admin/projects/create', methods=['POST'])
def admin_project_create():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return redirect(url_for('index'))
    data = {
        'title': request.form.get('title'),
        'members_wanted': request.form.get('members_wanted'),
        'deadline': request.form.get('deadline'),
        'created_by': session.get('user_id')
    }
    db.create_project_assignment(data)
    return redirect(url_for('admin_projects'))

@app.route('/employee/project/respond', methods=['POST'])
def employee_project_respond():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    data = request.json or {}
    project_id = data.get('project_id')
    status = data.get('status') # accepted, declined
    
    db.update_project_interest_status(project_id, session['user_id'], status)
    
    # Notify admin with specific choice
    uname = session.get('user_name', session.get('user_id', 'Employee'))
    db.add_notification('admin', f"{uname} {status} project assignment")
    
    return jsonify({'success': True})

@app.route('/api/project/details/<int:pid>')
def api_project_details(pid):
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    details = db.get_project_details(pid, session['user_id'])
    if details:
        return jsonify({
            'success': True,
            'title': details['title'],
            'members_wanted': details['members_wanted'],
            'deadline': str(details['deadline']),
            'status': details['user_status']
        })
    return jsonify({'success': False, 'message': 'Project not found'}), 404


# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------
@app.route('/face-image/<user_id>', methods=['GET'])
def get_face_image(user_id):
    emp = db.get_employee(user_id)
    if not emp or not emp.get('face_image'):
        return '', 404
    return Response(emp['face_image'], mimetype='image/jpeg')
@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.json or {}
    img_b64 = data.get('image', '')
    if ',' in img_b64:
        img_b64 = img_b64.split(',')[1]

    # Save temp image
    tmp = os.path.join(UPLOAD_FOLDER, f'tmp_{uuid.uuid4().hex}.jpg')
    try:
        raw = base64.b64decode(img_b64)
        with open(tmp, 'wb') as f:
            f.write(raw)

        emb_res = generate_embedding(tmp)
        if not emb_res.get('success'):
            return jsonify({'success': False, 'message': emb_res.get('message', 'Could not generate embedding')})

        match = compare_with_db(emb_res['embedding'])
        if not match:
            return jsonify({'success': False, 'message': 'Face not registered'})

        user_id = match['user_id']

        # Get user_id and fetch true role exactly as requested
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        role = row[0] if (row and row[0]) else 'employee'
        conn.close()
        
        # LOG LOGIN EVENT TO SQL SERVER
        db.log_login_event(user_id)

        session['user_id'] = user_id
        session['user_name'] = match['name']
        session['role'] = role

        if role == 'admin':
            redirect_to = url_for('admin')
        else:
            redirect_to = url_for('dashboard')

        return jsonify({
            'success':  True,
            'name':     match['name'],
            'redirect': redirect_to
        })
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


@app.route('/api/late-reason', methods=['POST'])
def api_late_reason():
    if 'user_id' not in session:
        return jsonify({'success': False})
    reason = (request.json or {}).get('reason', '')
    db.update_late_reason(session['user_id'], reason)
    return jsonify({'success': True})


@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    """Dashboard Clock In — employee is already in session."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    user_id = session['user_id']
    # Prevent duplicate check-ins
    existing = db.get_today_record(user_id)
    if existing:
        return jsonify({'success': False, 'message': 'Already checked in today'})
    now = datetime.now()
    status = determine_status()
    db.log_checkin(user_id, status=status)
    return jsonify({
        'success':        True,
        'late':           status == 'Late',
        'status':         status,
        'checked_in':     True,
        'check_in_time':  now.strftime('%H:%M:%S'),
        'working_hours':  0
    })


@app.route('/api/register', methods=['POST'])
def api_register():
    data    = request.json or {}
    user_id = (data.get('user_id') or '').strip()
    name    = (data.get('name') or '').strip()

    # Validate required fields
    if not user_id or not name:
        return jsonify({'success': False, 'message': 'User ID and Name are required.'})

    # Pre-check: user_id already exists?
    if db.get_employee(user_id):
        return jsonify({
            'success': False,
            'message': f'User ID "{user_id}" is already registered. Use a different ID or go back to Login.'
        })

    img_b64 = data.get('image', '')
    if ',' in img_b64:
        img_b64 = img_b64.split(',')[1]

    tmp_path = os.path.join(UPLOAD_FOLDER, f'tmp_{uuid.uuid4().hex}.jpg')
    try:
        raw = base64.b64decode(img_b64)
        with open(tmp_path, 'wb') as f:
            f.write(raw)

        emb_res = generate_embedding(tmp_path)
        if not emb_res.get('success'):
            return jsonify({'success': False, 'message': emb_res.get('message', 'Face embedding failed.')})

        db.register_employee({
            'user_id':        user_id,
            'title':          data.get('title', ''),
            'name':           name,
            'email':          data.get('email', ''),
            'role':           data.get('role', 'employee'),
            'password':       data.get('password', ''),
            'face_embedding': json.dumps(emb_res['embedding']),
            'face_image':     raw
        })

    except Exception as e:
        err = str(e).lower()
        if 'unique' in err or 'duplicate' in err:
            return jsonify({'success': False,
                            'message': f'User ID "{user_id}" is already taken. Please use a different ID.'})
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    # FIX: Registration only — no auto login, no attendance marking
    return jsonify({
        'success':  True,
        'redirect': url_for('index')
    })




@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    now = datetime.now()
    hours = db.log_checkout(session['user_id'])
    
    return jsonify({
        'success':       True,
        'checked_in':    False,
        'check_out_time': now.strftime('%H:%M:%S'),
        'working_hours': hours,
        'status':        'absent'
    })


@app.route('/api/meetings', methods=['GET'])
def api_meetings():
    if 'user_id' not in session:
        return jsonify([])
    meetings = db.get_meetings_for_employee(session['user_id'])
    return jsonify(meetings)


@app.route('/logout')
def logout():
    if session.get('user_id') and session.get('user_id') != 'admin':
        db.log_checkout(session['user_id'])
    session.clear()
    return redirect(url_for('index'))


# ── Leave Requests ──────────────────────────────────────────────────────────
@app.route('/api/leave-request', methods=['POST'])
def api_submit_leave():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.json or {}
    leave_type = (data.get('leave_type') or '').strip()
    from_date  = (data.get('from_date') or '').strip()
    to_date    = (data.get('to_date') or '').strip()
    reason     = (data.get('reason') or '').strip()
    if not leave_type or not from_date or not to_date:
        return jsonify({'success': False, 'message': 'Leave type, from date and to date are required.'})
    db.create_leave_request({
        'user_id':    session['user_id'],
        'leave_type':  leave_type,
        'from_date':   from_date,
        'to_date':     to_date,
        'reason':      reason
    })
    # Feature 3: Send notification to Admin
    db.add_notification('admin', f"{session.get('user_name', session['user_id'])} requested leave")
    return jsonify({'success': True})


@app.route('/api/leave-requests', methods=['GET'])
def api_my_leave_requests():
    if 'user_id' not in session:
        return jsonify([])
    return jsonify(db.get_leave_requests_by_employee(session['user_id']))
@app.route('/api/admin/leave/approve', methods=['POST'])
def api_approve_leave():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False})
    
    data = request.json or {}
    uid = data.get('user_id')
    fdate = data.get('from_date')
    
    db.update_leave_status(uid, fdate, 'Approved')
    db.add_notification(uid, "Leave Approved")
    
    return jsonify({'success': True})


@app.route('/api/admin/leave/reject', methods=['POST'])
def api_reject_leave():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False})
    
    data = request.json or {}
    uid = data.get('user_id')
    fdate = data.get('from_date')
    
    db.update_leave_status(uid, fdate, 'Rejected')
    db.add_notification(uid, "Leave Rejected")
    
    return jsonify({'success': True})
# ── Admin Operations ────────────────────────────────────────────────────────
@app.route('/api/admin/meeting', methods=['POST'])
def api_create_meeting():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.json or {}
    if not data.get('title') or not data.get('date') or not data.get('time'):
        return jsonify({'success': False, 'message': 'Title, date, and time are required.'})
    user_id = (data.get('user_id') or '').strip()
    db.create_meeting({
        'title':       data['title'],
        'date':        data['date'],
        'time':        data['time'],
        'description': data.get('description', ''),
        'user_id':     user_id if user_id else None,
        'created_by':  session.get('user_id')
    })
    
    # Send notification to assigned user
    if user_id:
        db.add_notification(user_id, f"New meeting scheduled: {data['title']}")
        
    return jsonify({'success': True})

@app.route('/api/admin/meeting/delete', methods=['DELETE'])
def api_delete_meeting():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False}), 403
    
    data = request.json or {}
    title = data.get('title')
    mdate = data.get('date')
    uid = data.get('user_id')
    
    db.delete_meeting(title, mdate, uid)
    return jsonify({'success': True})

@app.route('/api/admin/employee/<user_id>', methods=['DELETE'])
def api_delete_employee(user_id):
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False}), 403
    db.delete_employee(user_id)
    return jsonify({'success': True})
@app.route('/api/admin/add-employee', methods=['POST'])
def api_add_employee():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.json or {}
    user_id = (data.get('user_id') or '').strip()
    name   = (data.get('name') or '').strip()
    email  = (data.get('email') or '').strip()
    role   = data.get('role', 'employee')
    if not user_id or not name:
        return jsonify({'success': False, 'message': 'User ID and Name are required.'})
    try:
        db.register_employee({
            'user_id': user_id,
            'name': name,
            'email': email,
            'role': role,
            'password': 'password123',
            'face_embedding': None,
            'face_image': None
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/meeting/respond', methods=['POST'])
def api_meeting_respond():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    data = request.json or {}
    mid = data.get('meeting_id')
    status = data.get('status')
    reason = data.get('reason')
    
    if not mid or not status:
        return jsonify({'success': False, 'message': 'Meeting ID and status required.'})
        
    db.save_meeting_response(mid, session['user_id'], status, reason)
    
    # Feature 2: Admin Notification
    uname = session.get('user_name', session['user_id'])
    msg = f"{uname} {status} meeting"
    if status == 'declined' and reason:
        msg = f"{uname} declined meeting - Reason: {reason}"
    elif status == 'tentative':
        msg = f"{uname} marked tentative"
    elif status == 'accepted':
        msg = f"{uname} accepted meeting"
        
    db.add_notification('admin', msg)
    
    return jsonify({'success': True})

# --- End of custom routes ---

# --- Stale routes removed ---

# ---------------------------------------------------------------------------
# Routes — Flutter Helpers (Read-Only)
# ---------------------------------------------------------------------------
@app.route('/api/dashboard-data', methods=['GET'])
def api_dashboard_data():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    user_id = session['user_id']
    emp = db.get_employee(user_id)
    if not emp:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Convert binary image to base64 for Flutter
    face_image = None
    if emp.get('face_image'):
        face_image = base64.b64encode(emp['face_image']).decode('utf-8')

    # Fetch history for synchronization
    history = db.get_attendance_history(user_id)
    today_str = __import__('datetime').date.today().isoformat()
    
    data = {
        'success':    True,
        'employee':   {
            'user_id':    emp['user_id'],
            'name':        emp['name'],
            'email':       emp.get('email'),
            'role':        emp.get('role'),
            'created_at':  emp.get('created_at').isoformat() if emp.get('created_at') else None,
            'face_image':  face_image
        },
        'today':      history[0] if (history and history[0].get('date') == today_str) else None,
        'history':    history,
        'leave_bal':  db.get_leave_balance(user_id),
        'upcoming':   db.get_upcoming_meetings(user_id),
        'notifications': db.get_notifications(user_id)
    }
    
    return jsonify(data)


@app.route('/api/admin-dashboard-data', methods=['GET'])
def api_admin_dashboard_data():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = {
        'success':    True,
        'stats':      db.get_stats(),
        'employees':   db.get_all_employees(),
        'attend_today': db.get_today_attendance(),
        'recent_att':  db.get_recent_attendance(10),
        'meetings':    db.get_all_meetings(),
        'leave_reqs':  db.get_all_leave_requests()
    }
    return jsonify(data)


@app.route('/api/admin/analytics')
def api_admin_analytics():
    if session.get('role') != 'admin' and session.get('user_id') != 'admin':
        return jsonify({'success': False})
    
    a_type = request.args.get('type', 'trend')
    if a_type == 'performance':
        return jsonify(db.get_employee_performance())
        
    time_range = request.args.get('range', 'today')
    return jsonify(db.get_admin_analytics(time_range))

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, port=5000)
