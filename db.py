import os
from datetime import datetime, date
import pyodbc

# --- Connection ---
CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def get_conn():
    return pyodbc.connect(CONN_STR)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    tables = [
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' and xtype='U')
           CREATE TABLE users (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) UNIQUE NOT NULL,
               name NVARCHAR(100) NOT NULL,
               email VARCHAR(100),
               role VARCHAR(20) DEFAULT 'employee',
               password VARCHAR(255),
               face_embedding VARCHAR(MAX),
               face_image VARBINARY(MAX),
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='attendance' and xtype='U')
           CREATE TABLE attendance (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               date DATE NOT NULL,
               check_in DATETIME,
               check_out DATETIME,
               working_hours FLOAT DEFAULT 0,
               status VARCHAR(50) DEFAULT 'Present',
               late_reason NVARCHAR(255)
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='meetings' and xtype='U')
           CREATE TABLE meetings (
               id INT IDENTITY(1,1) PRIMARY KEY,
               title NVARCHAR(255) NOT NULL,
               description NVARCHAR(MAX),
               meeting_date DATE NOT NULL,
               meeting_time VARCHAR(10) NOT NULL,
               created_by VARCHAR(50) DEFAULT 'admin',
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='leave_requests' and xtype='U')
           CREATE TABLE leave_requests (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               leave_type VARCHAR(100) NOT NULL,
               from_date DATE NOT NULL,
               to_date DATE NOT NULL,
               reason NVARCHAR(MAX),
               status VARCHAR(50) DEFAULT 'Pending',
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='login_logs' and xtype='U')
           CREATE TABLE login_logs (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               login_time DATETIME DEFAULT GETDATE(),
               date DATE DEFAULT CAST(GETDATE() AS DATE)
           )"""
    ]
    for stmt in tables:
        c.execute(stmt)
        
    # Ensure late_reason column exists in attendance table
    try:
        c.execute("IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('attendance') AND name = 'late_reason') ALTER TABLE attendance ADD late_reason NVARCHAR(255)")
    except Exception:
        pass

    c.execute("SELECT id FROM users WHERE employee_id='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (employee_id, name, role, password) VALUES ('admin', 'System Admin', 'admin', 'admin123')")
    conn.commit()
    conn.close()


# --- Helpers ---
def _row_to_dict(cursor, row):
    if not row:
        return None
    cols = [col[0] for col in cursor.description]
    return dict(zip(cols, row))

def _rows_to_dicts(cursor, rows):
    if not rows:
        return []
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in rows]

def fmt_time(val):
    if val is None:
        return '--:--:--'
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val).strftime('%H:%M:%S')
        except Exception:
            try:
                # pyodbc might return raw time strings
                return datetime.strptime(val.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
            except:
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
    c.execute("SELECT employee_id, name, email, role, created_at FROM users ORDER BY name")
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE employee_id=?", (employee_id,))
    row = _row_to_dict(c, c.fetchone())
    conn.close()
    return row

def register_employee(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (employee_id, name, email, role, password, face_embedding, face_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['employee_id'], data['name'], data['email'],
          data.get('role', 'employee'), data['password'],
          data['face_embedding'], data['face_image']))
    conn.commit()
    conn.close()

def get_all_embeddings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT employee_id, name, face_embedding FROM users WHERE face_embedding IS NOT NULL")
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def delete_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE employee_id=?", (employee_id,))
    c.execute("DELETE FROM attendance WHERE employee_id=?", (employee_id,))
    conn.commit()
    conn.close()


# --- Login Logs ---
def log_login_event(employee_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO login_logs (employee_id) VALUES (?)", (employee_id,))
    conn.commit()
    conn.close()


# --- Attendance ---
def get_today_record(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT * FROM attendance WHERE employee_id=? AND date=?", (employee_id, today))
    row = _row_to_dict(c, c.fetchone())
    conn.close()
    return row

def log_checkin(employee_id, status='Present', late_reason=None):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    now = datetime.now()
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
        row_id = row[0]
        check_in_raw = row[1]
        
        if isinstance(check_in_raw, str):
            try:
                check_in_dt = datetime.fromisoformat(check_in_raw.split('.')[0])
            except:
                check_in_dt = datetime.strptime(check_in_raw.split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            check_in_dt = check_in_raw
            
        hours = round((now_dt - check_in_dt).total_seconds() / 3600, 2)
        c.execute("UPDATE attendance SET check_out=?, working_hours=? WHERE id=?",
                  (now_dt, hours, row_id))
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
    c.execute(f"SELECT TOP {limit} * FROM attendance WHERE employee_id=? ORDER BY date DESC", (employee_id,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_today_attendance():
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT u.employee_id, u.name,
               a.check_in, a.check_out, a.status, a.working_hours
        FROM users e
        LEFT JOIN attendance a ON u.employee_id = a.employee_id AND a.date=?
        ORDER BY u.name
    """, (today,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_recent_attendance(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        SELECT TOP {limit} u.name, a.id, a.date, a.check_in, a.check_out, a.working_hours, a.status
        FROM attendance a
        JOIN users u ON a.employee_id = u.employee_id
        ORDER BY a.date DESC, a.check_in DESC
    """)
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows


# --- Dashboard Details ---
def get_stats():
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    present = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Late'", (today,))
    late = c.fetchone()[0]
    conn.close()
    return {'total': total, 'present': present, 'absent': total - present, 'late': late}


# --- Meetings ---
def create_meeting(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO meetings (title, description, meeting_date, meeting_time, created_by)
                 VALUES (?, ?, ?, ?, ?)""",
              (data['title'], data['description'], data['date'],
               data['time'], data.get('created_by', 'admin')))
    conn.commit()
    conn.close()

def get_meetings_for_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    # Meetings are global now, no employee_id filter except meeting_date
    c.execute("""SELECT * FROM meetings
                 WHERE meeting_date >= ?
                 ORDER BY meeting_date, meeting_time""", (today,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_all_meetings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM meetings ORDER BY meeting_date DESC, meeting_time DESC")
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

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
                 (id, leave_type, from_date, to_date, reason, status)
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
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_all_leave_requests():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT lr.*, u.name as employee_name
                 FROM leave_requests lr
                 LEFT JOIN users u ON lr.employee_id = u.employee_id
                 ORDER BY lr.created_at DESC""")
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def update_leave_status(leave_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE leave_requests SET status=? WHERE employee_id=?", (status, leave_id))
    conn.commit()
    conn.close()


# --- Aggregates ---
def get_monthly_stats(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    month_end   = today.isoformat()
    
    c.execute("""SELECT status, COUNT(*) as cnt FROM attendance
                 WHERE employee_id=? AND date>=? AND date<=?
                 GROUP BY status""", (employee_id, month_start, month_end))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    
    stats = {'present': 0, 'late': 0, 'absent': 0}
    for r in rows:
        s = (r.get('status') or '').lower()
        if s in stats:
            stats[s] = r.get('cnt', 0)
            
    total_days = today.day
    attended   = stats['present'] + stats['late']
    stats['pct'] = round(attended / total_days * 100) if total_days else 0
    stats['total_days'] = total_days
    return stats

def get_leave_balance(employee_id):
    LIMITS = {'Casual Leave': 12, 'Sick Leave': 10, 'Permission': 6, 'Half Day': 6, 'Work From Home': 20}
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT leave_type, COUNT(*) as cnt FROM leave_requests
                 WHERE employee_id=? AND status='Approved'
                 GROUP BY leave_type""", (employee_id,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    
    used = {}
    for r in rows:
        used[r.get('leave_type', '')] = r.get('cnt', 0)
        
    balance = {}
    for lt, limit in LIMITS.items():
        balance[lt] = {'limit': limit, 'used': used.get(lt, 0), 'remaining': limit - used.get(lt, 0)}
    return balance

def get_upcoming_meetings(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""SELECT TOP 5 * FROM meetings
                 WHERE meeting_date >= ?
                 ORDER BY meeting_date ASC, meeting_time ASC""", (today,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_notifications(employee_id):
    notes = []
    today_rec = get_today_record(employee_id)
    if today_rec:
        s = today_rec.get('status') or ''
        if s.lower() == 'late':
            notes.append({'type': 'warn', 'icon': 'alert-triangle',
                          'text': f'You checked in late today — {fmt_time(today_rec.get("check_in"))}'})
            
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as cnt FROM leave_requests WHERE employee_id=? AND status='Approved'", (employee_id,))
    row = c.fetchone()
    approved = row[0] if row else 0
    if approved:
        notes.append({'type': 'success', 'icon': 'check-circle',
                      'text': f'{approved} leave request(s) have been approved'})

    c.execute("SELECT COUNT(*) as cnt FROM leave_requests WHERE employee_id=? AND status='Rejected'", (employee_id,))
    row = c.fetchone()
    rejected = row[0] if row else 0
    if rejected:
        notes.append({'type': 'danger', 'icon': 'x-circle',
                      'text': f'{rejected} leave request(s) have been rejected'})

    today = date.today().isoformat()
    c.execute("""SELECT COUNT(*) as cnt FROM meetings
                 WHERE meeting_date=?""", (today,))
    row = c.fetchone()
    meet_today = row[0] if row else 0
    if meet_today:
        notes.append({'type': 'info', 'icon': 'calendar',
                      'text': f'You have {meet_today} meeting(s) scheduled today'})

    conn.close()
    if not notes:
        notes.append({'type': 'muted', 'icon': 'bell', 'text': 'No new notifications'})
    return notes


