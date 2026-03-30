import sqlite3
import os
from datetime import datetime, date

# --- Connection ---
USE_SQLITE = False
CONN_STR = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

try:
    import pyodbc
    # Test connection
    test = pyodbc.connect(CONN_STR, timeout=3)
    test.close()
except Exception:
    USE_SQLITE = True


def get_conn():
    if USE_SQLITE:
        conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), 'face_attendance.db'),
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        return conn
    return pyodbc.connect(CONN_STR)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    if USE_SQLITE:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                department TEXT,
                role TEXT DEFAULT 'employee',
                password TEXT,
                face_embedding TEXT,
                face_image BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                date DATE NOT NULL,
                check_in TIMESTAMP,
                check_out TIMESTAMP,
                working_hours REAL DEFAULT 0,
                status TEXT DEFAULT 'present',
                late_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                meeting_date DATE NOT NULL,
                meeting_time TEXT NOT NULL,
                employee_id TEXT,
                created_by TEXT DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                from_date DATE NOT NULL,
                to_date DATE NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Default admin
        c.execute("SELECT id FROM admin_users WHERE username='admin'")
        if not c.fetchone():
            c.execute("INSERT INTO admin_users (username, password) VALUES ('admin','admin123')")
    conn.commit()
    conn.close()


# --- Helpers ---
def row_to_dict(row):
    if row is None:
        return None
    if USE_SQLITE:
        return dict(row)
    cols = [col[0] for col in row.cursor_description] if hasattr(row, 'cursor_description') else []
    return dict(zip(cols, row))


def fmt_time(val):
    """Convert DB value to HH:MM:SS string safely."""
    if val is None:
        return '--:--:--'
    if isinstance(val, str):
        # e.g. "2026-03-28 09:15:00"
        try:
            return datetime.fromisoformat(val).strftime('%H:%M:%S')
        except Exception:
            return val
    if isinstance(val, datetime):
        return val.strftime('%H:%M:%S')
    return str(val)


def fmt_date(val):
    if val is None:
        return ''
    if isinstance(val, str):
        return val[:10]
    if isinstance(val, (datetime, date)):
        return val.strftime('%Y-%m-%d')
    return str(val)


# --- Employees ---
def get_all_employees():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT employee_id, name, email, department, role, created_at FROM employees ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def get_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE employee_id=?", (employee_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row and USE_SQLITE else row


def register_employee(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO employees (employee_id, name, email, department, role, password, face_embedding, face_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['employee_id'], data['name'], data['email'], data['department'],
          data.get('role', 'employee'), data['password'],
          data['face_embedding'], data['face_image']))
    conn.commit()
    conn.close()


def get_all_embeddings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT employee_id, name, face_embedding FROM employees WHERE face_embedding IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else [{'employee_id': r[0], 'name': r[1], 'face_embedding': r[2]} for r in rows]


def delete_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM employees WHERE employee_id=?", (employee_id,))
    c.execute("DELETE FROM attendance WHERE employee_id=?", (employee_id,))
    conn.commit()
    conn.close()


# --- Attendance ---
def get_today_record(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT * FROM attendance WHERE employee_id=? AND date=?", (employee_id, today))
    row = c.fetchone()
    conn.close()
    return dict(row) if row and USE_SQLITE else row


def log_checkin(employee_id, status='present', late_reason=None):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    now = datetime.now().isoformat()
    c.execute("SELECT id FROM attendance WHERE employee_id=? AND date=?", (employee_id, today))
    if not c.fetchone():
        c.execute("""INSERT INTO attendance (employee_id, date, check_in, status, late_reason)
                     VALUES (?, ?, ?, ?, ?)""", (employee_id, today, now, status, late_reason))
    conn.commit()
    conn.close()


def log_checkout(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    now_dt = datetime.now()
    c.execute("SELECT id, check_in FROM attendance WHERE employee_id=? AND date=? AND check_out IS NULL",
              (employee_id, today))
    row = c.fetchone()
    if row:
        row_id = row[0] if not USE_SQLITE else row['id']
        check_in_raw = row[1] if not USE_SQLITE else row['check_in']
        if isinstance(check_in_raw, str):
            check_in_dt = datetime.fromisoformat(check_in_raw)
        else:
            check_in_dt = check_in_raw
        hours = round((now_dt - check_in_dt).total_seconds() / 3600, 2)
        c.execute("UPDATE attendance SET check_out=?, working_hours=? WHERE id=?",
                  (now_dt.isoformat(), hours, row_id))
        conn.commit()
        conn.close()
        return hours
    conn.close()
    return 0


def update_late_reason(employee_id, reason):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("UPDATE attendance SET late_reason=? WHERE employee_id=? AND date=?",
              (reason, employee_id, today))
    conn.commit()
    conn.close()


def get_attendance_history(employee_id, limit=30):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE employee_id=? ORDER BY date DESC LIMIT ?",
              (employee_id, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def get_stats():
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT COUNT(*) FROM employees")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    present = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='late'", (today,))
    late = c.fetchone()[0]
    conn.close()
    return {'total': total, 'present': present, 'absent': total - present, 'late': late}


def get_today_attendance():
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT e.employee_id, e.name, e.department,
               a.check_in, a.check_out, a.status, a.working_hours
        FROM employees e
        LEFT JOIN attendance a ON e.employee_id = a.employee_id AND a.date=?
        ORDER BY e.name
    """, (today,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def get_recent_attendance(limit=10):
    conn = get_conn()
    c = conn.cursor()
    # Join with employees to get names for the admin history view
    if USE_SQLITE:
        c.execute("""
            SELECT e.name, a.employee_id, a.date, a.check_in, a.check_out, a.working_hours, a.status
            FROM attendance a
            JOIN employees e ON a.employee_id = e.employee_id
            ORDER BY a.date DESC, a.check_in DESC
            LIMIT ?
        """, (limit,))
    else:
        # SQL Server TOP syntax
        c.execute(f"""
            SELECT TOP {limit} e.name, a.employee_id, a.date, a.check_in, a.check_out, a.working_hours, a.status
            FROM attendance a
            JOIN employees e ON a.employee_id = e.employee_id
            ORDER BY a.date DESC, a.check_in DESC
        """)
    rows = c.fetchall()
    conn.close()
    if USE_SQLITE:
        return [dict(r) for r in rows]
    # For pyodbc, manually convert to list of dicts if needed for template consistency
    res = []
    for r in rows:
        res.append({
            'name': r[0], 'employee_id': r[1], 'date': r[2],
            'check_in': r[3], 'check_out': r[4], 'working_hours': r[5], 'status': r[6]
        })
    return res


# --- Meetings ---
def create_meeting(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO meetings (title, description, meeting_date, meeting_time, employee_id, created_by)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (data['title'], data['description'], data['date'],
               data['time'], data.get('employee_id') or None, data.get('created_by', 'admin')))
    conn.commit()
    conn.close()


def get_meetings_for_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""SELECT * FROM meetings
                 WHERE meeting_date >= ? AND (employee_id=? OR employee_id IS NULL)
                 ORDER BY meeting_date, meeting_time""",
              (today, employee_id))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def get_all_meetings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM meetings ORDER BY meeting_date DESC, meeting_time DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def delete_meeting(meeting_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM meetings WHERE id=?", (meeting_id,))
    conn.commit()
    conn.close()


# --- Leave Requests ---
def create_leave_request(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO leave_requests
                 (employee_id, leave_type, from_date, to_date, reason, status)
                 VALUES (?, ?, ?, ?, ?, 'Pending')""",
              (data['employee_id'], data['leave_type'],
               data['from_date'], data['to_date'], data.get('reason', '')))
    conn.commit()
    conn.close()


def get_leave_requests_by_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT * FROM leave_requests WHERE employee_id=?
                 ORDER BY created_at DESC""", (employee_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def get_all_leave_requests():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT lr.*, e.name as employee_name, e.department
                 FROM leave_requests lr
                 LEFT JOIN employees e ON lr.employee_id = e.employee_id
                 ORDER BY lr.created_at DESC""")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def update_leave_status(leave_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE leave_requests SET status=? WHERE id=?", (status, leave_id))
    conn.commit()
    conn.close()


# --- Dashboard Enhancement Helpers ---

def get_monthly_stats(employee_id):
    """Present/Late/Absent counts + attendance % for current month."""
    conn = get_conn()
    c = conn.cursor()
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    month_end   = today.isoformat()
    c.execute("""SELECT status, COUNT(*) as cnt FROM attendance
                 WHERE employee_id=? AND date>=? AND date<=?
                 GROUP BY status""", (employee_id, month_start, month_end))
    rows = c.fetchall()
    conn.close()
    stats = {'present': 0, 'late': 0, 'absent': 0}
    for r in rows:
        r = dict(r) if USE_SQLITE else {'status': r[0], 'cnt': r[1]}
        s = (r.get('status') or '').lower()
        if s in stats:
            stats[s] = r.get('cnt', 0)
    total_days = today.day  # working days approximation = days elapsed
    attended   = stats['present'] + stats['late']
    stats['pct'] = round(attended / total_days * 100) if total_days else 0
    stats['total_days'] = total_days
    return stats


def get_leave_balance(employee_id):
    """Calculate remaining leave days from leave_requests (approved only)."""
    LIMITS = {'Casual Leave': 12, 'Sick Leave': 10, 'Permission': 6, 'Half Day': 6, 'Work From Home': 20}
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT leave_type, COUNT(*) as cnt FROM leave_requests
                 WHERE employee_id=? AND status='Approved'
                 GROUP BY leave_type""", (employee_id,))
    rows = c.fetchall()
    conn.close()
    used = {}
    for r in rows:
        r = dict(r) if USE_SQLITE else {'leave_type': r[0], 'cnt': r[1]}
        used[r.get('leave_type', '')] = r.get('cnt', 0)
    balance = {}
    for lt, limit in LIMITS.items():
        balance[lt] = {'limit': limit, 'used': used.get(lt, 0), 'remaining': limit - used.get(lt, 0)}
    return balance


def get_upcoming_meetings(employee_id):
    """Today + future meetings for employee (or all-employee meetings)."""
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""SELECT * FROM meetings
                 WHERE (employee_id=? OR employee_id IS NULL OR employee_id='')
                   AND meeting_date >= ?
                 ORDER BY meeting_date ASC, meeting_time ASC
                 LIMIT 5""", (employee_id, today))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows] if USE_SQLITE else rows


def get_notifications(employee_id):
    """Build a list of contextual notifications for the employee."""
    notes = []
    # Late today?
    today_rec = get_today_record(employee_id)
    if today_rec:
        tr = dict(today_rec) if USE_SQLITE else today_rec
        if (tr.get('status') or '') == 'late':
            notes.append({'type': 'warn', 'icon': 'alert-triangle',
                          'text': f'You checked in late today — {fmt_time(tr.get("check_in"))}'})
    # Pending leave requests
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM leave_requests WHERE employee_id=? AND status='Approved'",
              (employee_id,))
    row = c.fetchone()
    approved = (dict(row) if USE_SQLITE else {'cnt': row[0]}).get('cnt', 0) if row else 0
    if approved:
        notes.append({'type': 'success', 'icon': 'check-circle',
                      'text': f'{approved} leave request(s) have been approved'})

    c.execute("SELECT COUNT(*) as cnt FROM leave_requests WHERE employee_id=? AND status='Rejected'",
              (employee_id,))
    row = c.fetchone()
    rejected = (dict(row) if USE_SQLITE else {'cnt': row[0]}).get('cnt', 0) if row else 0
    if rejected:
        notes.append({'type': 'danger', 'icon': 'x-circle',
                      'text': f'{rejected} leave request(s) have been rejected'})

    # Upcoming meetings today
    today = date.today().isoformat()
    c.execute("""SELECT COUNT(*) as cnt FROM meetings
                 WHERE (employee_id=? OR employee_id IS NULL OR employee_id='')
                   AND meeting_date=?""", (employee_id, today))
    row = c.fetchone()
    meet_today = (dict(row) if USE_SQLITE else {'cnt': row[0]}).get('cnt', 0) if row else 0
    conn.close()
    if meet_today:
        notes.append({'type': 'info', 'icon': 'calendar',
                      'text': f'You have {meet_today} meeting(s) scheduled today'})

    if not notes:
        notes.append({'type': 'muted', 'icon': 'bell', 'text': 'No new notifications'})
    return notes
