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

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------------------------------------------
# DeepFace Native Face Engine Helpers
# ---------------------------------------------------------------------------
def generate_embedding(image_path):
    try:
        # Lower strictness on detection to be more lenient with alignment/lighting
        objs = DeepFace.represent(img_path=image_path, model_name="ArcFace", enforce_detection=False)
        if len(objs) == 0:
            return {'success': False, 'message': 'Face not detected. Please align face.'}
            
        embedding = objs[0]['embedding']
        return {'success': True, 'embedding': embedding}
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
    if 'employee_id' not in session:
        return redirect(url_for('index'))
    emp = db.get_employee(session['employee_id'])
    if not emp:
        session.clear()
        return redirect(url_for('index'))
    uid          = session['employee_id']
    today_rec    = db.get_today_record(uid)
    history      = db.get_attendance_history(uid)
    meetings     = db.get_meetings_for_employee(uid)
    leave_reqs   = db.get_leave_requests_by_employee(uid)
    monthly      = db.get_monthly_stats(uid)
    leave_bal    = db.get_leave_balance(uid)
    upcoming     = db.get_upcoming_meetings(uid)
    notifs       = db.get_notifications(uid)
    analytics    = db.get_employee_analytics(uid)
    return render_template('dashboard.html',
                           emp=emp,
                           today=today_rec,
                           history=history,
                           meetings=meetings,
                           leave_reqs=leave_reqs,
                           monthly=monthly,
                           leave_bal=leave_bal,
                           upcoming=upcoming,
                           notifs=notifs,
                           analytics=analytics,
                           today_date=__import__('datetime').date.today().isoformat(),
                           fmt_time=db.fmt_time,
                           fmt_date=db.fmt_date)



@app.route('/admin')
@app.route('/admin/<tab>')
def admin(tab='attendance'):
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
        return redirect(url_for('index'))
        
    # Sanitize and default
    active_tab = (tab or 'attendance').strip().lower()
    if active_tab not in ['attendance', 'employees', 'meetings', 'leaves', 'reports', 'activity']:
        return redirect(url_for('admin', tab='attendance'))

    stats       = db.get_stats()
    employees   = db.get_all_employees()
    attend      = db.get_today_attendance()
    recent      = db.get_recent_attendance(10)
    meetings    = db.get_all_meetings()
    all_emps    = db.get_all_employees()
    leave_reqs  = db.get_all_leave_requests()
    
    return render_template('admin_dashboard.html',
                           active_tab=tab,
                           stats=stats,
                           employees=employees,
                           attend=attend,
                           recent=recent,
                           meetings=meetings,
                           all_emps=all_emps,
                           leave_reqs=leave_reqs,
                           fmt_time=db.fmt_time,
                           fmt_date=db.fmt_date)


# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------
@app.route('/face-image/<emp_id>', methods=['GET'])
def get_face_image(emp_id):
    emp = db.get_employee(emp_id)
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

        emp_id = match['employee_id']

        # Get employee_id and fetch true role exactly as requested
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE employee_id = ?", (emp_id,))
        row = c.fetchone()
        role = row[0] if (row and row[0]) else 'employee'
        conn.close()
        
        # LOG LOGIN EVENT TO SQL SERVER
        db.log_login_event(emp_id)

        session['employee_id'] = emp_id
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
    if 'employee_id' not in session:
        return jsonify({'success': False})
    reason = (request.json or {}).get('reason', '')
    db.update_late_reason(session['employee_id'], reason)
    return jsonify({'success': True})


@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    """Dashboard Clock In — employee is already in session."""
    if 'employee_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    emp_id = session['employee_id']
    # Prevent duplicate check-ins
    existing = db.get_today_record(emp_id)
    if existing:
        return jsonify({'success': False, 'message': 'Already checked in today'})
    status = determine_status()
    db.log_checkin(emp_id, status=status)
    return jsonify({
        'success': True,
        'late':    status == 'Late',
        'status':  status
    })


@app.route('/api/register', methods=['POST'])
def api_register():
    data   = request.json or {}
    emp_id = (data.get('employee_id') or '').strip()
    name   = (data.get('name') or '').strip()

    # Validate required fields
    if not emp_id or not name:
        return jsonify({'success': False, 'message': 'Employee ID and Name are required.'})

    # Pre-check: employee_id already exists?
    if db.get_employee(emp_id):
        return jsonify({
            'success': False,
            'message': f'Employee ID "{emp_id}" is already registered. Use a different ID or go back to Login.'
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
            'employee_id':    emp_id,
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
                            'message': f'Employee ID "{emp_id}" is already taken. Please use a different ID.'})
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
    if 'employee_id' not in session:
        return jsonify({'success': False})
    hours = db.log_checkout(session['employee_id'])
    return jsonify({'success': True, 'working_hours': hours})


@app.route('/api/meetings', methods=['GET'])
def api_meetings():
    if 'employee_id' not in session:
        return jsonify([])
    meetings = db.get_meetings_for_employee(session['employee_id'])
    return jsonify(meetings)


@app.route('/api/admin/meeting', methods=['POST'])
def api_create_meeting():
    data = request.json or {}
    db.create_meeting({
        'title':       data.get('title', 'Untitled'),
        'description': data.get('description', ''),
        'date':        data.get('date'),
        'time':        data.get('time'),
        'employee_id': data.get('employee_id'),
        'created_by':  session.get('user_id', 'admin')
    })
    return jsonify({'success': True})


@app.route('/api/admin/meeting/<int:mid>', methods=['DELETE'])
def api_delete_meeting(mid):
    db.delete_meeting(mid)
    return jsonify({'success': True})


@app.route('/api/admin/employee/<emp_id>', methods=['DELETE'])
def api_delete_employee(emp_id):
    db.delete_employee(emp_id)
    return jsonify({'success': True})





@app.route('/logout')
def logout():
    if session.get('employee_id') and session.get('employee_id') != 'admin':
        db.log_checkout(session['employee_id'])
    session.clear()
    return redirect(url_for('index'))


# ── Leave Requests ──────────────────────────────────────────────────────────
@app.route('/api/leave-request', methods=['POST'])
def api_submit_leave():
    if 'employee_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.json or {}
    leave_type = (data.get('leave_type') or '').strip()
    from_date  = (data.get('from_date') or '').strip()
    to_date    = (data.get('to_date') or '').strip()
    reason     = (data.get('reason') or '').strip()
    if not leave_type or not from_date or not to_date:
        return jsonify({'success': False, 'message': 'Leave type, from date and to date are required.'})
    db.create_leave_request({
        'employee_id': session['employee_id'],
        'leave_type':  leave_type,
        'from_date':   from_date,
        'to_date':     to_date,
        'reason':      reason
    })
    return jsonify({'success': True})


@app.route('/api/leave-requests', methods=['GET'])
def api_my_leave_requests():
    if 'employee_id' not in session:
        return jsonify([])
    return jsonify(db.get_leave_requests_by_employee(session['employee_id']))


@app.route('/api/admin/leave/<int:lid>/approve', methods=['POST'])
def api_approve_leave(lid):
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
        return jsonify({'success': False})
    db.update_leave_status(lid, 'Approved')
    return jsonify({'success': True})


@app.route('/api/admin/leave/<int:lid>/reject', methods=['POST'])
def api_reject_leave(lid):
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
        return jsonify({'success': False})
    db.update_leave_status(lid, 'Rejected')
    return jsonify({'success': True})
# ── Admin Operations ────────────────────────────────────────────────────────
@app.route('/api/admin/meeting', methods=['POST'])
def api_create_meeting():
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.json or {}
    if not data.get('title') or not data.get('date') or not data.get('time'):
        return jsonify({'success': False, 'message': 'Title, date, and time are required.'})
    db.create_meeting({
        'title':       data['title'],
        'date':        data['date'],
        'time':        data['time'],
        'description': data.get('description', ''),
        'employee_id': data.get('employee_id'),
        'created_by':  session.get('employee_id')
    })
    return jsonify({'success': True})

@app.route('/api/admin/meeting/<int:mid>', methods=['DELETE'])
def api_delete_meeting(mid):
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
        return jsonify({'success': False}), 403
    db.delete_meeting(mid)
    return jsonify({'success': True})

@app.route('/api/admin/employee/<emp_id>', methods=['DELETE'])
def api_delete_employee(emp_id):
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
        return jsonify({'success': False}), 403
    db.delete_employee(emp_id)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Routes — Flutter Helpers (Read-Only)
# ---------------------------------------------------------------------------
@app.route('/api/dashboard-data', methods=['GET'])
def api_dashboard_data():
    if 'employee_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    uid = session['employee_id']
    emp = db.get_employee(uid)
    if not emp:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Convert binary image to base64 for Flutter
    face_image = None
    if emp.get('face_image'):
        face_image = base64.b64encode(emp['face_image']).decode('utf-8')

    data = {
        'success':    True,
        'employee':   {
            'employee_id': emp['employee_id'],
            'name':        emp['name'],
            'email':       emp.get('email'),
            'role':        emp.get('role'),
            'created_at':  emp.get('created_at').isoformat() if emp.get('created_at') else None,
            'face_image':  face_image
        },
        'today':      db.get_today_record(uid),
        'history':    db.get_attendance_history(uid),
        'meetings':   db.get_meetings_for_employee(uid),
        'leave_reqs': db.get_leave_requests_by_employee(uid),
        'monthly':    db.get_monthly_stats(uid),
        'leave_bal':  db.get_leave_balance(uid),
        'upcoming':   db.get_upcoming_meetings(uid),
        'notifications': db.get_notifications(uid)
    }
    return jsonify(data)


@app.route('/api/admin-dashboard-data', methods=['GET'])
def api_admin_dashboard_data():
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
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
    if session.get('role') != 'admin' and session.get('employee_id') != 'admin':
        return jsonify({'success': False})
    time_range = request.args.get('range', 'today')
    data = db.get_admin_analytics(time_range)
    return jsonify(data)

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, port=5000)
