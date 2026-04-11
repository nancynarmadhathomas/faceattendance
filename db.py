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
    
    # Core Schema Definitions
    tables = [
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' and xtype='U')
           CREATE TABLE users (
               user_id VARCHAR(50) PRIMARY KEY,
               name NVARCHAR(100) NOT NULL,
               email VARCHAR(100),
               department NVARCHAR(100),
               role VARCHAR(20) DEFAULT 'employee',
               password VARCHAR(255),
               face_embedding VARCHAR(MAX),
               face_image VARBINARY(MAX),
               title NVARCHAR(20) DEFAULT '',
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='attendance' and xtype='U')
           CREATE TABLE attendance (
               user_id VARCHAR(50) NOT NULL,
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
               meeting_type VARCHAR(20) DEFAULT 'Physical',
               meeting_link VARCHAR(MAX),
               location NVARCHAR(255),
               user_id VARCHAR(50),
               created_by VARCHAR(50) DEFAULT 'admin',
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='meeting_attendance' and xtype='U')
           CREATE TABLE meeting_attendance (
               id INT IDENTITY(1,1) PRIMARY KEY,
               meeting_id INT NOT NULL,
               user_id VARCHAR(50) NOT NULL,
               status VARCHAR(20) DEFAULT 'Absent',
               joined_at DATETIME DEFAULT GETDATE(),
               UNIQUE(meeting_id, user_id)
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='leave_requests' and xtype='U')
           CREATE TABLE leave_requests (
               user_id VARCHAR(50) NOT NULL,
               leave_type VARCHAR(100) NOT NULL,
               from_date DATE NOT NULL,
               to_date DATE NOT NULL,
               reason NVARCHAR(MAX),
               status VARCHAR(50) DEFAULT 'Pending',
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='login_logs' and xtype='U')
           CREATE TABLE login_logs (
               user_id VARCHAR(50) NOT NULL,
               login_time DATETIME DEFAULT GETDATE(),
               date DATE DEFAULT CAST(GETDATE() AS DATE)
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='notifications' and xtype='U')
           CREATE TABLE notifications (
               recipient_id VARCHAR(50) NOT NULL,
               message NVARCHAR(MAX) NOT NULL,
               type VARCHAR(20) DEFAULT 'info',
               project_id INT,
               is_read BIT DEFAULT 0,
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='meeting_responses' and xtype='U')
           CREATE TABLE meeting_responses (
               meeting_id INT NOT NULL,
               user_id VARCHAR(50) NOT NULL,
               status VARCHAR(20) NOT NULL,
               reason NVARCHAR(MAX),
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='projects' and xtype='U')
           CREATE TABLE projects (
               id INT IDENTITY(1,1) PRIMARY KEY,
               title NVARCHAR(255) NOT NULL,
               description NVARCHAR(MAX),
               members_wanted INT DEFAULT 1,
               deadline DATE,
               created_by VARCHAR(50),
               created_at DATETIME DEFAULT GETDATE()
           )""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='project_interest' and xtype='U')
           CREATE TABLE project_interest (
               project_id INT NOT NULL,
               user_id VARCHAR(50) NOT NULL,
               status VARCHAR(20) DEFAULT 'pending', 
               created_at DATETIME DEFAULT GETDATE()
           )"""
    ]
    # --- Migration: Add 'status' to 'projects' ---
    try:
        c.execute("SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'status'")
        if not c.fetchone():
            print("Migrating 'projects' table: Adding 'status' column...")
            c.execute("ALTER TABLE projects ADD status VARCHAR(50) DEFAULT 'Pending'")
            conn.commit()
    except Exception as e:
        print(f"Migration error adding 'status' to projects: {e}")

    for stmt in tables:
        c.execute(stmt)

    # --- AUTOMATIC MIGRATION: Rename employee_id to user_id if present ---
    # This block ensures that old tables are automatically updated.
    target_tables = ['users', 'attendance', 'meetings', 'leave_requests', 'login_logs', 
                     'notifications', 'meeting_responses', 'project_interest']
    for table in target_tables:
        try:
            # Check if employee_id column exists
            c.execute(f"SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('{table}') AND name = 'employee_id'")
            if c.fetchone():
                print(f"Migrating table {table}: Renaming employee_id to user_id...")
                c.execute(f"EXEC sp_rename '{table}.employee_id', 'user_id', 'COLUMN'")
                conn.commit()
        except Exception as e:
            print(f"Migration error on {table}: {e}")

    # --- Migration: Add 'id' to 'meetings' if missing ---
    try:
        c.execute("SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('meetings') AND name = 'id'")
        if not c.fetchone():
            print("Migrating 'meetings' table: Adding 'id' primary key column...")
            c.execute("ALTER TABLE meetings ADD id INT IDENTITY(1,1) PRIMARY KEY")
            conn.commit()
    except Exception as e:
        print(f"Migration error adding 'id' to meetings: {e}")

    # --- Migration: Remove 'employee_name' from 'attendance' if exists ---
    try:
        c.execute("SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('attendance') AND name = 'employee_name'")
        if c.fetchone():
            print("Migrating 'attendance' table: Removing 'employee_name' column...")
            c.execute("ALTER TABLE attendance DROP COLUMN employee_name")
            conn.commit()
    except Exception as e:
        print(f"Migration error removing 'employee_name' from attendance: {e}")

    # --- Migration: Add 'description' to 'projects' ---
    try:
        c.execute("SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'description'")
        if not c.fetchone():
            print("Migrating 'projects' table: Adding 'description' column...")
            c.execute("ALTER TABLE projects ADD description NVARCHAR(MAX)")
            conn.commit()
    except Exception as e:
        print(f"Migration error adding 'description' to projects: {e}")

    # --- Migration: Rename user_id to recipient_id in notifications ---
    try:
        c.execute("SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('notifications') AND name = 'user_id'")
        if c.fetchone():
            print("Migrating table notifications: Renaming user_id to recipient_id...")
            c.execute("EXEC sp_rename 'notifications.user_id', 'recipient_id', 'COLUMN'")
            conn.commit()
    except Exception as e:
        print(f"Migration error on notifications: {e}")

    # --- Migration: Hybrid Meetings (type, link, location) ---
    meeting_cols = [
        ('meeting_type', "VARCHAR(20) DEFAULT 'Physical'"),
        ('meeting_link', "VARCHAR(MAX)"),
        ('location', "NVARCHAR(255)")
    ]
    for col_name, col_def in meeting_cols:
        try:
            c.execute(f"SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('meetings') AND name = '{col_name}'")
            if not c.fetchone():
                # Specialized Migration: Check if legacy 'meeting_location' exists to rename it instead of adding new
                if col_name == 'location':
                    c.execute("SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('meetings') AND name = 'meeting_location'")
                    if c.fetchone():
                        print("Migrating 'meetings' table: Renaming 'meeting_location' to 'location'...")
                        c.execute("EXEC sp_rename 'meetings.meeting_location', 'location', 'COLUMN'")
                        conn.commit()
                        continue

                print(f"Migrating 'meetings' table: Adding '{col_name}' column...")
                c.execute(f"ALTER TABLE meetings ADD {col_name} {col_def}")
                conn.commit()
        except Exception as e:
            print(f"Migration error adding '{col_name}' to meetings: {e}")

    # Check admin existence
    c.execute("SELECT user_id FROM users WHERE user_id='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, name, role, password) VALUES ('admin', 'System Admin', 'admin', 'admin123')")
    
    conn.commit()
    conn.close()

# --- Helpers ---
def _row_to_dict(cursor, row):
    if not row:
        return None
    cols = [col[0] for col in cursor.description]
    d = dict(zip(cols, row))
    # Standardize: Convert all date/datetime/time to ISO strings for template/JSON safety
    for k, v in d.items():
        if isinstance(v, (date, datetime)):
            d[k] = v.isoformat()
        elif hasattr(v, 'isoformat') and not isinstance(v, str):
            d[k] = v.isoformat()
    return d

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
    c.execute("SELECT user_id, name, email, role, title, created_at FROM users ORDER BY name")
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_employee(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = _row_to_dict(c, c.fetchone())
    conn.close()
    return row

def register_employee(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (user_id, name, email, role, title, password, face_embedding, face_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['user_id'], data['name'], data['email'],
          data.get('role', 'employee'), data.get('title', ''), data['password'],
          data['face_embedding'], data['face_image']))
    conn.commit()
    conn.close()

def get_all_embeddings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, name, face_embedding FROM users WHERE face_embedding IS NOT NULL")
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def delete_employee(user_id):
    conn = get_conn()
    c = conn.cursor()
    # 2. Delete dependent records first (attendance, leave_requests, meetings if exists)
    # Order: attendance → leave_requests → meetings → users
    # Plus other dependencies discovered in schema
    c.execute("DELETE FROM attendance WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM leave_requests WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM meeting_responses WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM meetings WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM notifications WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM project_interest WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM login_logs WHERE user_id=?", (user_id,))
    
    # 3. Then delete from users table
    c.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    
    conn.commit()
    conn.close()

# --- Login Logs ---
def log_login_event(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO login_logs (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

# --- Attendance ---
def get_today_record(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT TOP 1 * FROM attendance 
                 WHERE user_id=? AND date = CAST(GETDATE() AS DATE)
                 ORDER BY check_in DESC""", (user_id,))
    row = _row_to_dict(c, c.fetchone())
    conn.close()
    return row

def log_checkin(user_id, status='Present', late_reason=None):
    """
    STRICT CHECKIN with FK Validation:
    1. Check if user exists in 'users' table (satisfy FK constraint).
    2. If not exists -> Insert 'Temp User'.
    3. If attendance exists -> UPDATE.
    4. Else -> INSERT attendance.
    """
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now()
    
    # 1. Check if user exists (FK constraint validation)
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        # 3. If not exists: insert user first
        print(f"DEBUG: User {user_id} not found in users table. Creating 'Temp User' placeholder.")
        c.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, 'Temp User'))
        conn.commit()

    # 5. If record already exists, update instead of insert
    c.execute("SELECT * FROM attendance WHERE user_id=? AND date = CAST(GETDATE() AS DATE)", (user_id,))
    if c.fetchone():
        c.execute("""UPDATE attendance SET check_in=?, status=?, late_reason=? 
                     WHERE user_id=? AND date = CAST(GETDATE() AS DATE)""", 
                  (now, status, late_reason, user_id))
    else:
        c.execute("""INSERT INTO attendance (user_id, date, check_in, status, late_reason)
                     VALUES (?, CAST(GETDATE() AS DATE), ?, ?, ?)""", 
                  (user_id, now, status, late_reason))
    conn.commit()
    conn.close()

def log_checkout(user_id):
    conn = get_conn()
    c = conn.cursor()
    now_dt = datetime.now()
    c.execute("SELECT check_in FROM attendance WHERE user_id=? AND date = CAST(GETDATE() AS DATE) AND check_out IS NULL",
              (user_id,))
    row = c.fetchone()
    if row:
        check_in_raw = row[0]
        
        if isinstance(check_in_raw, str):
            try:
                check_in_dt = datetime.fromisoformat(check_in_raw.split('.')[0])
            except:
                check_in_dt = datetime.strptime(check_in_raw.split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            check_in_dt = check_in_raw
            
        hours = round((now_dt - check_in_dt).total_seconds() / 3600, 2)
        
        # New: Half Day logic (threshold: 4.5 hours)
        status_update = "Present"
        # Determine if it should be Half Day based on hours
        if hours < 4.5:
            status_update = "Half Day"
        else:
            # Keep existing 'Late' / 'Present' status if already set, but upgrade to Present if it was Half Day?
            # Actually, the requirement says "If working hours completed → mark Present"
            # It implies status can change based on hours.
            pass

        # We should fetch existing status to see if it was 'Late'
        c.execute("SELECT status FROM attendance WHERE user_id=? AND date=CAST(GETDATE() AS DATE)", (user_id,))
        existing_status = c.fetchone()
        if existing_status and existing_status[0] == 'Late' and hours >= 4.5:
            # If they were late but worked full day, we can keep 'Late' but they are still 'Present' in terms of full day?
            # Usually 'Late' is a sub-status of 'Present'. 
            # Requirement says: mark Present if hours completed.
            status_update = "Late" # Keep Late if they were late
        elif hours >= 4.5:
            status_update = "Present"

        c.execute("""UPDATE attendance SET check_out=?, working_hours=?, status=?
                     WHERE user_id=? AND date=CAST(GETDATE() AS DATE) AND check_out IS NULL""",
                  (now_dt, hours, status_update, user_id))
        conn.commit()
        
        # Return summary for email
        res = {
            'check_in':      check_in_dt.strftime('%I:%M %p'),
            'check_out':     now_dt.strftime('%I:%M %p'),
            'working_hours': hours,
            'status':        status_update
        }
        conn.close()
        return res
    conn.close()
    return None

def update_late_reason(user_id, reason):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE attendance SET late_reason=? WHERE user_id=? AND date = CAST(GETDATE() AS DATE)",
              (reason, user_id))
    conn.commit()
    conn.close()

def get_attendance_history(user_id, limit=30):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT TOP {limit} * FROM attendance WHERE user_id=? ORDER BY date DESC", (user_id,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_today_attendance():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT u.user_id, u.name,
               a.check_in, a.check_out, a.status, a.working_hours
        FROM users u
        LEFT JOIN attendance a ON u.user_id = a.user_id AND a.date = CAST(GETDATE() AS DATE)
        ORDER BY u.name
    """)
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_recent_attendance(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        SELECT TOP {limit} u.name, a.date, a.check_in, a.check_out, a.working_hours, a.status
        FROM attendance a
        JOIN users u ON a.user_id = u.user_id
        ORDER BY a.date DESC, a.check_in DESC
    """)
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

# --- Dashboard Details ---
def get_stats():
    conn = get_conn()
    c = conn.cursor()
    
    # 1. Counts
    c.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
    total = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM attendance WHERE date = CAST(GETDATE() AS DATE)")
    present = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM attendance WHERE date = CAST(GETDATE() AS DATE) AND status='Late'")
    late = c.fetchone()[0] or 0
    
    # 2. On Leave Today
    c.execute("""SELECT COUNT(*) FROM leave_requests 
                 WHERE status='Approved' AND CAST(GETDATE() AS DATE) BETWEEN from_date AND to_date""")
    on_leave = c.fetchone()[0] or 0
    
    # 3. Avg Working Hours Today
    c.execute("SELECT AVG(working_hours) FROM attendance WHERE date = CAST(GETDATE() AS DATE)")
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
    c.execute("""INSERT INTO meetings (title, description, meeting_date, meeting_time, user_id, created_by)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (data['title'], data['description'], data['date'],
               data['time'], data.get('user_id'), data.get('created_by', 'admin')))
    conn.commit()
    conn.close()

def get_meetings_for_employee(user_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    # Fetch meetings with attendance status
    c.execute("""SELECT m.*, ma.status as attendance_status 
                 FROM meetings m
                 LEFT JOIN meeting_attendance ma ON m.id = ma.meeting_id AND ma.user_id = ?
                 WHERE m.meeting_date >= ?
                 AND (m.user_id IS NULL OR LOWER(m.user_id) = LOWER(?))
                 ORDER BY m.meeting_date, m.meeting_time""", (user_id, today, user_id))
    rows = _rows_to_dicts(c, c.fetchall())
    
    # Also fetch the response status for each meeting (Accepted/Declined)
    for r in rows:
        c.execute("SELECT status, reason FROM meeting_responses WHERE meeting_id=? AND user_id=?", (r['id'], user_id))
        res = c.fetchone()
        if res:
            r['response_status'] = res[0]
            r['response_reason'] = res[1]
        else:
            r['response_status'] = None

    conn.close()
    return rows

def save_meeting_response(meeting_id, user_id, status, reason=None):
    conn = get_conn()
    c = conn.cursor()
    # Remove existing response if any
    c.execute("DELETE FROM meeting_responses WHERE meeting_id=? AND user_id=?", (meeting_id, user_id))
    c.execute("""INSERT INTO meeting_responses (meeting_id, user_id, status, reason)
                 VALUES (?, ?, ?, ?)""", (meeting_id, user_id, status, reason))
    conn.commit()
    conn.close()

def get_all_meetings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM meetings ORDER BY meeting_date DESC, meeting_time DESC")
    rows = _rows_to_dicts(c, c.fetchall())
    
    # Enrich with stats
    for r in rows:
        stats = get_meeting_analytics(r['id'])
        r['stats'] = stats
        
    conn.close()
    return rows

def delete_meeting_by_id(meeting_id):
    conn = get_conn()
    c = conn.cursor()
    # First delete responses to avoid foreign key issues (if any) or just clean up
    c.execute("DELETE FROM meeting_responses WHERE meeting_id=?", (meeting_id,))
    # Then delete meeting
    c.execute("DELETE FROM meetings WHERE id=?", (meeting_id,))
    conn.commit()
    conn.close()
    return True

def delete_meeting(title, meeting_date, user_id):
    """Old deletion method using composite keys (fallback)."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM meetings WHERE title=? AND meeting_date=? AND user_id=?", (title, meeting_date, user_id))
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
    c.execute("""INSERT INTO leave_requests (user_id, leave_type, from_date, to_date, reason)
                 VALUES (?, ?, ?, ?, ?)""",
              (data['user_id'], data['leave_type'], from_str, to_str, data.get('reason', '')))
    conn.commit()
    conn.close()

def get_leave_requests_by_employee(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM leave_requests WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def get_all_leave_requests():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT lr.*, u.name as employee_name
                 FROM leave_requests lr
                 LEFT JOIN users u ON lr.user_id = u.user_id
                 ORDER BY lr.created_at DESC""")
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def update_leave_status(user_id, from_date, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE leave_requests SET status=? WHERE user_id=? AND from_date=?", (status, user_id, from_date))
    conn.commit()
    conn.close()

# --- Aggregates ---
def get_monthly_stats(user_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    month_end   = today.isoformat()
    c.execute("""SELECT status, COUNT(*) as cnt FROM attendance
                 WHERE user_id=? AND date>=? AND date<=?
                 GROUP BY status""", (user_id, month_start, month_end))
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

def get_leave_balance(user_id):
    LIMITS = {'Casual Leave': 12, 'Sick Leave': 10, 'Permission': 6, 'Half Day': 6, 'Work From Home': 20}
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT leave_type, COUNT(*) as cnt FROM leave_requests WHERE user_id=? AND status='Approved' GROUP BY leave_type", (user_id,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    used = {r.get('leave_type', ''): r.get('cnt', 0) for r in rows}
    balance = {lt: {'limit': limit, 'used': used.get(lt, 0), 'remaining': limit - used.get(lt, 0)} for lt, limit in LIMITS.items()}
    return balance

def get_upcoming_meetings(user_id):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    # Fetch meetings where user is assigned or it's for everyone (user_id IS NULL)
    c.execute("""SELECT m.*, ma.status as attendance_status 
                 FROM meetings m
                 LEFT JOIN meeting_attendance ma ON m.id = ma.meeting_id AND ma.user_id = ?
                 WHERE (m.user_id = ? OR m.user_id IS NULL) 
                 AND m.meeting_date >= ?
                 ORDER BY m.meeting_date ASC, m.meeting_time ASC""", (user_id, user_id, today))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def add_admin_meeting(title, m_date, m_time, assigned_to=None, description=None, m_type='Physical', link=None, location=None, created_by='admin'):
    # Clean up parameters based on meeting type for data integrity
    if m_type.lower() == 'physical':
        link = None
    elif m_type.lower() == 'virtual':
        location = None

    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO meetings 
                 (title, description, meeting_date, meeting_time, user_id, created_by, meeting_type, meeting_link, location) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
              (title, description, m_date, m_time, assigned_to, created_by, m_type, link, location))
    conn.commit()
    conn.close()
    return True

def mark_meeting_attendance(meeting_id, user_id, status='Present'):
    conn = get_conn()
    c = conn.cursor()
    # Check if entry exists
    c.execute("SELECT id FROM meeting_attendance WHERE meeting_id=? AND user_id=?", (meeting_id, user_id))
    row = c.fetchone()
    if row:
        c.execute("UPDATE meeting_attendance SET status=?, joined_at=GETDATE() WHERE meeting_id=? AND user_id=?", (status, meeting_id, user_id))
    else:
        c.execute("INSERT INTO meeting_attendance (meeting_id, user_id, status) VALUES (?, ?, ?)", (meeting_id, user_id, status))
    conn.commit()
    conn.close()
    return True

def get_meeting_analytics(meeting_id):
    conn = get_conn()
    c = conn.cursor()
    # Total Invited
    c.execute("SELECT user_id FROM meetings WHERE id=?", (meeting_id,))
    row = c.fetchone()
    assigned = row[0] if row else None
    
    total_invited = 1 if assigned else 0
    if not assigned:
        c.execute("SELECT COUNT(*) FROM users WHERE role='employee'")
        total_invited = c.fetchone()[0] or 0
        
    # Attended
    c.execute("SELECT COUNT(*) FROM meeting_attendance WHERE meeting_id=? AND status='Present'", (meeting_id,))
    attended = c.fetchone()[0] or 0
    
    conn.close()
    return {
        'total_invited': total_invited,
        'attended': attended,
        'absent': max(0, total_invited - attended)
    }

def get_notifications(user_id):
    conn = get_conn()
    c = conn.cursor()
    # Fetch Notifications from the new table
    c.execute("SELECT TOP 10 * FROM notifications WHERE recipient_id=? ORDER BY created_at DESC", (user_id,))
    notes = _rows_to_dicts(c, c.fetchall())
    
    # Optional: include Pending Leave requests for Admin as notifications
    if user_id == 'admin':
        c.execute("""SELECT lr.user_id, u.name, lr.leave_type, lr.created_at
                     FROM leave_requests lr
                     JOIN users u ON lr.user_id = u.user_id
                     WHERE lr.status='Pending'
                     ORDER BY lr.created_at DESC""")
        pending = c.fetchall()
        for p in pending:
            notes.append({
                'type': 'leave_request',
                'user_id': p[0],
                'name': p[1],
                'message': f"{p[1]} requested leave ({p[2]})",
                'created_at': p[3].isoformat() if hasattr(p[3], 'isoformat') else str(p[3])
            })
    conn.close()
    return notes

def add_notification(recipient_id, message, type='info', project_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO notifications (recipient_id, message, type, project_id) VALUES (?, ?, ?, ?)", 
               (recipient_id, message, type, project_id))
    conn.commit()
    conn.close()

def get_project_details(project_id, user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT p.*, pi.status as user_status
        FROM projects p
        LEFT JOIN project_interest pi ON p.id = pi.project_id AND pi.user_id = ?
        WHERE p.id = ?
    """, (user_id, project_id))
    row = c.fetchone()
    if row:
        columns = [column[0] for column in c.description]
        res = dict(zip(columns, row))
        conn.close()
        return res
    conn.close()
    return None

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
        present.append(day_att['present'] + day_att['late'])
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
        SELECT u.user_id, u.name, 
               COUNT(*) as days_present,
               SUM(CASE WHEN a.status='Late' THEN 1 ELSE 0 END) as late_count
        FROM users u
        LEFT JOIN attendance a ON u.user_id = a.user_id AND a.date >= ? AND a.status IN ('Present', 'Late')
        WHERE u.role != 'admin'
        GROUP BY u.user_id, u.name
        ORDER BY days_present DESC, late_count ASC
    """, (month_start,))
    
    rows = c.fetchall()
    performers = []
    total_working_days = today.day
    
    for r in rows[:limit]:
        uid, name, pres_count, late_count = r
        # Get leave count for this month
        c.execute("SELECT COUNT(*) FROM leave_requests WHERE user_id=? AND status='Approved' AND from_date>=?", (uid, month_start))
        leave_count = c.fetchone()[0] or 0
        
        pct = round((pres_count / total_working_days * 100)) if total_working_days > 0 else 0
        performers.append({
            'name': name,
            'id': uid,
            'pct': pct,
            'late': late_count,
            'leaves': leave_count
        })
        
    conn.close()
    return performers

def get_employee_analytics(user_id):
    import datetime as dt
    conn = get_conn()
    c = conn.cursor()
    today = dt.date.today()
    month_start = today.replace(day=1).isoformat()
    # Find start of current week (Monday)
    week_start = (today - dt.timedelta(days=today.weekday())).isoformat()

    # 1. Monthly Summary Stats
    c.execute("""SELECT status, COUNT(*) as cnt FROM attendance
                 WHERE user_id=? AND date>=? GROUP BY status""", (user_id, month_start))
    att_rows = {r[0].lower(): r[1] for r in c.fetchall()}
    present_m = att_rows.get('present', 0)
    late_m = att_rows.get('late', 0)
    
    total_month_days = today.day
    pct = round((present_m + late_m) / total_month_days * 100) if total_month_days > 0 else 0
    
    c.execute("SELECT COUNT(*) FROM leave_requests WHERE user_id=? AND status='Approved' AND from_date>=?", (user_id, month_start))
    leaves_m = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(working_hours) FROM attendance WHERE user_id=? AND date>=?", (user_id, month_start))
    hours_m = round(c.fetchone()[0] or 0, 1)

    # 2. Weekly Summary Stats
    c.execute("""SELECT status, COUNT(*), SUM(working_hours) FROM attendance
                 WHERE user_id=? AND date>=? GROUP BY status""", (user_id, week_start))
    w_rows = c.fetchall()
    present_w = sum(r[1] for r in w_rows if r[0].lower() == 'present')
    late_w = sum(r[1] for r in w_rows if r[0].lower() == 'late')
    hours_w = round(sum(r[2] or 0 for r in w_rows), 1)
    
    c.execute("SELECT COUNT(*) FROM leave_requests WHERE user_id=? AND status='Approved' AND from_date>=?", (user_id, week_start))
    leaves_w = c.fetchone()[0] or 0

    # 3. Monthly Attendance Distribution (Donut)
    # Absent = Total Month Days - (Present + Late + Leaves)
    absent_m = max(0, total_month_days - (present_m + late_m + leaves_m))
    attendance_dist = {
        'labels': ['Present', 'Late', 'Absent', 'Leave'],
        'data': [present_m, late_m, absent_m, leaves_m]
    }

    # 4. Monthly Working Hours Trend (Daily)
    labels_bar, data_bar = [], []
    c.execute("SELECT date, working_hours FROM attendance WHERE user_id=? AND date>=? ORDER BY date ASC", (user_id, month_start))
    trend_map = {str(r[0]): r[1] for r in c.fetchall()}
    for i in range(1, today.day + 1):
        d_str = today.replace(day=i).isoformat()
        labels_bar.append(d_str[-5:]) # MM-DD
        data_bar.append(trend_map.get(d_str, 0))

    # 5. Leave Summary (Casual, Sick, Permission)
    LIMITS = {'Casual Leave': 12, 'Sick Leave': 10, 'Permission': 6}
    c.execute("SELECT leave_type, COUNT(*) FROM leave_requests WHERE user_id=? AND status='Approved' GROUP BY leave_type", (user_id,))
    l_rows = {r[0]: r[1] for r in c.fetchall()}
    leave_summary = []
    total_remaining = 0
    for lt, lim in LIMITS.items():
        used = l_rows.get(lt, 0)
        rem = max(0, lim - used)
        total_remaining += rem
        leave_summary.append({'type': lt, 'used': used, 'limit': lim, 'remaining': rem})

    # 6. Recent Attendance (Analytics Table)
    c.execute("SELECT TOP 10 date, check_in, check_out, working_hours, status FROM attendance WHERE user_id=? ORDER BY date DESC", (user_id,))
    recent = _rows_to_dicts(c, c.fetchall())

    conn.close()
    return {
        'attendance_pct': pct,
        'present_days_month': present_m + late_m,
        'late_count_month': late_m,
        'working_hours_month': hours_m,
        'weekly': {
            'present': present_w,
            'late': late_w,
            'hours': hours_w,
            'leaves': leaves_w
        },
        'attendance_dist': attendance_dist,
        'chart_monthly_bar': {'labels': labels_bar, 'data': data_bar},
        'leave_summary': leave_summary,
        'remaining_leaves_total': total_remaining,
        'recent_attendance': recent
    }

# --- Projects (Strict Mode) ---
def create_project_assignment(data):
    conn = get_conn()
    c = conn.cursor()
    # Insert Project
    c.execute("""INSERT INTO projects (title, description, members_wanted, deadline, created_by)
                 OUTPUT INSERTED.id
                 VALUES (?, ?, ?, ?, ?)""",
              (data['title'], data.get('description', ''), data['members_wanted'], data['deadline'], data['created_by']))
    project_id = c.fetchone()[0]
    
    # Get All Employees
    c.execute("SELECT user_id FROM users WHERE role = 'employee'")
    employees = [row[0] for row in c.fetchall()]
    
    # Create Interest & Notification for ALL
    for eid in employees:
        c.execute("INSERT INTO project_interest (project_id, user_id, status) VALUES (?, ?, 'pending')",
                  (project_id, eid))
        # Logic to add a notification in DB (using the add_notification helper)
        # We'll just call it manually or reuse it
    
    conn.commit()
    conn.close()
    
    # For notifications, let's call the global helper for each one to be safe
    for eid in employees:
        add_notification(eid, f"Project Assigned\n{data['title']}\nDeadline: {data['deadline']}", type='project', project_id=project_id)

def get_admin_project_list():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT p.*,
               (SELECT COUNT(*) FROM project_interest WHERE project_id = p.id AND status = 'accepted') as accepted_count,
               (SELECT COUNT(*) FROM project_interest WHERE project_id = p.id AND status = 'declined') as declined_count,
               (SELECT COUNT(*) FROM project_interest WHERE project_id = p.id AND status = 'pending') as pending_count
        FROM projects p
        ORDER BY p.created_at DESC
    """)
    rows = _rows_to_dicts(c, c.fetchall())
    
    # Enrich with accepted/declined employee names
    for row in rows:
        # Get Accepted
        c.execute("""
            SELECT u.name FROM project_interest pi
            JOIN users u ON pi.user_id = u.user_id
            WHERE pi.project_id = ? AND pi.status = 'accepted'
        """, (row['id'],))
        row['accepted_names'] = [r[0] for r in c.fetchall()]
        
        # Get Declined
        c.execute("""
            SELECT u.name FROM project_interest pi
            JOIN users u ON pi.user_id = u.user_id
            WHERE pi.project_id = ? AND pi.status = 'declined'
        """, (row['id'],))
        row['declined_names'] = [r[0] for r in c.fetchall()]
        
    conn.close()
    return rows

def get_projects_for_employee(user_id):
    """Alias for get_employee_project_tasks to maintain compatibility with app.py calls."""
    return get_employee_project_tasks(user_id)

def get_employee_project_tasks(user_id):
    conn = get_conn()
    c = conn.cursor()
    # Fetch ALL projects with capacity tracking and user status
    c.execute("""
        SELECT 
            p.id as project_id,
            p.title,
            p.description,
            p.deadline,
            p.members_wanted as members_wanted,
            p.status as project_completion_status,
            (SELECT COUNT(*) FROM project_interest WHERE project_id = p.id AND status = 'accepted') as accepted_count,
            CASE 
                WHEN (SELECT COUNT(*) FROM project_interest WHERE project_id = p.id AND status = 'accepted') >= p.members_wanted 
                THEN 'FULL' 
                ELSE 'OPEN' 
            END as project_status,
            COALESCE(pi.status, 'pending') as status
        FROM projects p
        LEFT JOIN project_interest pi ON p.id = pi.project_id AND pi.user_id = ?
        ORDER BY p.created_at DESC
    """, (user_id,))
    rows = _rows_to_dicts(c, c.fetchall())
    conn.close()
    return rows

def update_project_interest_status(project_id, user_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE project_interest SET status = ? WHERE project_id = ? AND user_id = ?",
              (status, project_id, user_id))
    conn.commit()
    conn.close()

def update_project_completion_status(project_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
    conn.commit()
    conn.close()

# --- Specialized Analytics Helpers ---
def get_live_status_analytics():
    conn = get_conn()
    c = conn.cursor()
    
    # 1. Working Now (Checked in today, no checkout)
    c.execute("SELECT COUNT(*) FROM attendance WHERE date = CAST(GETDATE() AS DATE) AND check_in IS NOT NULL AND check_out IS NULL")
    working = c.fetchone()[0] or 0
    
    # 2. Clocked In (Total check-ins today)
    c.execute("SELECT COUNT(*) FROM attendance WHERE date = CAST(GETDATE() AS DATE) AND check_in IS NOT NULL")
    clocked_in = c.fetchone()[0] or 0
    
    # 3. Clocked Out (Checked out today)
    c.execute("SELECT COUNT(*) FROM attendance WHERE date = CAST(GETDATE() AS DATE) AND check_out IS NOT NULL")
    clocked_out = c.fetchone()[0] or 0
    
    conn.close()
    return {
        'working_now': working,
        'clocked_in': clocked_in,
        'clocked_out': clocked_out
    }

def get_avg_working_hours_analytics():
    import datetime as dt
    conn = get_conn()
    c = conn.cursor()
    # Monthly total per employee
    today = dt.date.today()
    month_start = today.replace(day=1).isoformat()
    
    # Use LEFT JOIN to include ALL employees, even those with 0 hours
    c.execute("""
        SELECT u.name, COALESCE(SUM(a.working_hours), 0) as total_hrs
        FROM users u
        LEFT JOIN attendance a ON u.user_id = a.user_id AND a.date >= ?
        WHERE u.user_id != 'admin'
        GROUP BY u.user_id, u.name
        ORDER BY total_hrs DESC
    """, (month_start,))
    rows = c.fetchall()
    conn.close()
    return {
        'labels': [r[0] for r in rows],
        'data': [round(float(r[1]), 1) for r in rows]
    }

def get_frequent_late_analytics():
    conn = get_conn()
    c = conn.cursor()
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    
    c.execute("""
        SELECT TOP 5 u.name, COUNT(*) as late_count
        FROM users u
        JOIN attendance a ON u.user_id = a.user_id
        WHERE a.date >= ? AND a.status = 'Late' AND u.role != 'admin'
        GROUP BY u.name
        ORDER BY late_count DESC
    """, (month_start,))
    rows = c.fetchall()
    conn.close()
    return {
        'labels': [r[0] for r in rows],
        'data': [r[1] for r in rows]
    }

def get_leave_type_analytics():
    conn = get_conn()
    c = conn.cursor()
    # Grouped by type for the bar chart
    c.execute("""
        SELECT leave_type, COUNT(*) as cnt 
        FROM leave_requests 
        WHERE status='Approved' 
        GROUP BY leave_type
    """)
    rows = c.fetchall()
    conn.close()
    types = ['Casual Leave', 'Sick Leave', 'Permission', 'Half Day', 'Work From Home']
    data_map = {r[0]: r[1] for r in rows}
    return {
        'labels': types,
        'data': [data_map.get(t, 0) for t in types]
    }

def get_table_data(table_name):
    allowed = ['users', 'attendance', 'leave_requests', 'meetings', 'projects', 'notifications']
    if table_name not in allowed:
        return [], []
    
    conn = get_conn()
    c = conn.cursor()
    # Using brackets for table names to handle spaces or reserved keywords safely in SQL Server
    c.execute(f"SELECT * FROM [{table_name}]")
    columns = [col[0] for col in c.description]
    rows = c.fetchall()
    
    data = []
    for row in rows:
        d = {}
        for i, val in enumerate(row):
            col_name = columns[i]
            # Mask sensitive data
            if col_name in ['password', 'face_embedding']:
                val = "********"
            elif col_name == 'face_image' and val:
                val = "<Binary Data>"
            # Date/Time formatting
            if isinstance(val, (date, datetime)):
                val = val.isoformat()
            d[col_name] = val
        data.append(d)
        
    conn.close()
    return columns, data

