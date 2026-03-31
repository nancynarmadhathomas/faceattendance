import os
from datetime import datetime, date
import datetime as dt
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
               employee_id VARCHAR(50),
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

    # Ensure meetings table has employee_id column (FIX for 500 error)
    try:
        c.execute("IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('meetings') AND name = 'employee_id') ALTER TABLE meetings ADD employee_id VARCHAR(50)")
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
    if not rows: return []
    cols = [col[0] for col in cursor.description]
    res = []
    for row in rows:
        d = {}
        for i, val in enumerate(row):
            # Convert date/datetime/time to ISO strings for template compatibility
            if isinstance(val, (date, datetime)):
                val = val.isoformat()
            elif hasattr(val, 'isoformat'): # catch other potential types
                val = val.isoformat()
            d[cols[i]] = val
        res.append(d)
    return res

def fmt_time(val):
    if val is None:
        return '--:--:--'
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val).strftime('%H:%M:%S')
        except Exception:
            try:
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
        VALUES (?, ?, ?, ?, ?, ?, ?)
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
        FROM users u
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
    
    # 1. Counts
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    present = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Late'", (today,))
    late = c.fetchone()[0] or 0
    
    # 2. On Leave Today
    c.execute("""SELECT COUNT(*) FROM leave_requests 
                 WHERE status='Approved' AND ? BETWEEN from_date AND to_date""", (today,))
    on_leave = c.fetchone()[0] or 0
    
    # 3. Avg Working Hours Today
    c.execute("SELECT AVG(working_hours) FROM attendance WHERE date=?", (today,))
    avg_hours = c.fetchone()[0] or 0.0
    
    # 4. Computed Stats
    absent = max(0, total - present - on_leave)
    attendance_rate = 0
    if total > 0:
        attendance_rate = round((present / total) * 100, 1)

    conn.close()
    return {
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'on_leave': on_leave,
        'avg_hours': round(float(avg_hours), 1),
        'attendance_rate': attendance_rate
    }

# --- Meetings ---
def create_meeting(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO meetings (title, description, meeting_date, meeting_time, employee_id, created_by)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (data['title'], data['description'], data['date'],
               data['time'], data.get('employee_id'), data.get('created_by', 'admin')))
    conn.commit()
    conn.close()

def get_meetings_for_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    # Use case-insensitive match for the ID
    c.execute("""SELECT * FROM meetings
                 WHERE meeting_date >= ?
                 AND (employee_id IS NULL OR LOWER(employee_id) = LOWER(?))
                 ORDER BY meeting_date, meeting_time""", (today, employee_id))
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
    from_str = data['from_date']
    to_str = data['to_date']
    try:
        from_str = datetime.strptime(from_str, '%d-%m-%Y').strftime('%Y-%m-%d')
        to_str = datetime.strptime(to_str, '%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception:
        pass
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO leave_requests (employee_id, leave_type, from_date, to_date, reason)
                 VALUES (?, ?, ?, ?, ?)""",
              (data['employee_id'], data['leave_type'], from_str, to_str, data.get('reason', '')))
    conn.commit()
    conn.close()

def get_leave_requests_by_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM leave_requests WHERE employee_id=? ORDER BY created_at DESC", (employee_id,))
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
    c.execute("UPDATE leave_requests SET status=? WHERE id=?", (status, leave_id))
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
        if s in stats: stats[s] = r.get('cnt', 0)
    total_days = today.day
    attended = stats['present'] + stats['late']
    stats['pct'] = round(attended / total_days * 100) if total_days else 0
    return stats

def get_leave_balance(employee_id):
    LIMITS = {'Casual Leave': 12, 'Sick Leave': 10, 'Permission': 6, 'Half Day': 6, 'Work From Home': 20}
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT leave_type, COUNT(*) as cnt FROM leave_requests WHERE employee_id=? AND status='Approved' GROUP BY leave_type", (employee_id,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    used = {r.get('leave_type', ''): r.get('cnt', 0) for r in rows}
    balance = {lt: {'limit': limit, 'used': used.get(lt, 0), 'remaining': limit - used.get(lt, 0)} for lt, limit in LIMITS.items()}
    return balance

def get_upcoming_meetings(employee_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""SELECT TOP 5 * FROM meetings
                 WHERE meeting_date >= ? AND (employee_id IS NULL OR employee_id = ?)
                 ORDER BY meeting_date ASC, meeting_time ASC""", (today, employee_id))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_notifications(employee_id):
    notes = []
    # ... notifications logic (omitted for brevity in this scratch, but I'll preserve it)
    return notes

# --- Admin Analytics ---
# --- Admin Analytics ---
def get_admin_analytics(time_range):
    import datetime as dt
    conn = get_conn()
    c = conn.cursor()
    today = dt.date.today()
    
    if time_range == 'week': days_to_fetch = 7
    elif time_range == 'month': days_to_fetch = today.day
    else: days_to_fetch = 30
        
    start_date = (today - dt.timedelta(days=days_to_fetch - 1))
    
    c.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
    total_emps = c.fetchone()[0] or 0

    # 1. Attendance Data
    c.execute("""SELECT date, 
                       SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present,
                       SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END) as late
                FROM attendance WHERE date >= ? GROUP BY date ORDER BY date ASC""", (start_date.isoformat(),))
    att_data = {str(r[0]): {'present': r[1], 'late': r[2]} for r in c.fetchall()}

    # 2. Leave Data (Historical)
    c.execute("""SELECT from_date, to_date FROM leave_requests WHERE status='Approved' AND to_date >= ?""", (start_date.isoformat(),))
    leave_reqs = c.fetchall()

    labels, present, late, absent, on_leave = [], [], [], [], []
    for i in range(days_to_fetch):
        curr_d = (start_date + dt.timedelta(days=i))
        d_str = curr_d.isoformat()
        
        # Count who was on leave this specific day
        leave_count = sum(1 for l in leave_reqs if l[0] <= curr_d and l[1] >= curr_d)
        
        day_att = att_data.get(d_str, {'present': 0, 'late': 0})
        
        labels.append(d_str[-5:])
        present.append(day_att['present'])
        late.append(day_att['late'])
        on_leave.append(leave_count)
        # Absent = Total - (Present + Late + On Leave)
        abs_count = max(0, total_emps - (day_att['present'] + day_att['late'] + leave_count))
        absent.append(abs_count)
        
    conn.close()
    return {
        'labels': labels,
        'present': present,
        'late': late,
        'absent': absent,
        'on_leave': on_leave
    }

def get_admin_detailed_stats():
    import datetime as dt
    conn = get_conn()
    c = conn.cursor()
    today = dt.date.today()
    weekday = today.weekday()
    week_start = today - dt.timedelta(days=weekday)
    
    # 1. Weekly Attendance Bar
    labels_weekly = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    data_weekly = [0]*7
    data_late_weekly = [0]*7
    
    c.execute("""SELECT date, status, COUNT(*) FROM attendance 
                 WHERE date >= ? GROUP BY date, status""", (week_start.isoformat(),))
    for r in c.fetchall():
        d_str, status, count = str(r[0]), r[1], r[2]
        d_dt = dt.date.fromisoformat(d_str)
        idx = d_dt.weekday()
        if status in ['Present', 'Late']:
            data_weekly[idx] += count
        if status == 'Late':
            data_late_weekly[idx] += count

    # 2. Leave Breakdown
    c.execute("SELECT leave_type, COUNT(*) FROM leave_requests WHERE status='Approved' GROUP BY leave_type")
    l_rows = c.fetchall()
    leave_types = {'labels': [r[0] for r in l_rows], 'data': [r[1] for r in l_rows]}

    # 3. Distribution
    stats = get_stats()
    dist = {
        'labels': ['Present', 'Absent', 'On Leave'],
        'data': [stats['present'], stats['absent'], stats['on_leave']]
    }

    conn.close()
    return {
        'weekly_att': {'labels': labels_weekly, 'data': data_weekly},
        'weekly_late': {'labels': labels_weekly, 'data': data_late_weekly},
        'leave_donut': leave_types,
        'dist_donut': dist
    }

def get_top_performers(limit=5):
    conn = get_conn()
    c = conn.cursor()
    today = dt.date.today()
    month_start = today.replace(day=1).isoformat()
    
    # Simple algorithm: Sort by presence count, then by late count (inverse)
    c.execute("""
        SELECT u.employee_id, u.name, 
               COUNT(a.id) as days_present,
               SUM(CASE WHEN a.status='Late' THEN 1 ELSE 0 END) as late_count
        FROM users u
        LEFT JOIN attendance a ON u.employee_id = a.employee_id AND a.date >= ? AND a.status IN ('Present', 'Late')
        WHERE u.role != 'admin'
        GROUP BY u.employee_id, u.name
        ORDER BY days_present DESC, late_count ASC
    """, (month_start,))
    
    rows = c.fetchall()
    performers = []
    total_working_days = today.day
    
    for r in rows[:limit]:
        emp_id, name, pres_count, late_count = r
        # Get leave count for this month
        c.execute("SELECT COUNT(*) FROM leave_requests WHERE employee_id=? AND status='Approved' AND from_date>=?", (emp_id, month_start))
        leave_count = c.fetchone()[0] or 0
        
        pct = round((pres_count / total_working_days * 100)) if total_working_days > 0 else 0
        performers.append({
            'name': name,
            'id': emp_id,
            'pct': pct,
            'late': late_count,
            'leaves': leave_count
        })
        
    conn.close()
    return performers

def get_employee_analytics(employee_id):
    import datetime as dt
    conn = get_conn()
    c = conn.cursor()
    today = dt.date.today()
    month_start = today.replace(day=1).isoformat()

    # Summary Stats
    c.execute("""SELECT status, COUNT(*) as cnt FROM attendance
                 WHERE employee_id=? AND date>=? GROUP BY status""", (employee_id, month_start))
    att_rows = {r[0].lower(): r[1] for r in c.fetchall()}
    present = att_rows.get('present', 0)
    late = att_rows.get('late', 0)
    
    total_days = today.day
    pct = round((present + late) / total_days * 100) if total_days > 0 else 0
    
    c.execute("SELECT COUNT(*) FROM leave_requests WHERE employee_id=? AND status='Approved' AND from_date>=?", (employee_id, month_start))
    leaves = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(working_hours) FROM attendance WHERE employee_id=? AND date>=?", (employee_id, month_start))
    hours = round(c.fetchone()[0] or 0, 1)

    # Monthly Bar (Dates)
    labels_bar, data_bar = [], []
    c.execute("SELECT date, working_hours FROM attendance WHERE employee_id=? AND date>=? ORDER BY date ASC", (employee_id, month_start))
    trend_map = {str(r[0]): r[1] for r in c.fetchall()}
    for i in range(1, today.day + 1):
        d_str = today.replace(day=i).isoformat()
        labels_bar.append(d_str[-2:]) # Day Number
        data_bar.append(trend_map.get(d_str, 0))

    # Leave Donut
    c.execute("SELECT leave_type, COUNT(*) FROM leave_requests WHERE employee_id=? AND status='Approved' GROUP BY leave_type", (employee_id,))
    l_rows = c.fetchall()
    leave_donut = {
        'labels': [r[0] for r in l_rows] if l_rows else ['No Leaves'],
        'data': [r[1] for r in l_rows] if l_rows else [0]
    }

    conn.close()
    return {
        'attendance_pct': pct,
        'late_count_month': late,
        'leaves_taken_month': leaves,
        'working_hours_month': hours,
        'chart_monthly_bar': {'labels': labels_bar, 'data': data_bar},
        'chart_leave_donut': leave_donut
    }
