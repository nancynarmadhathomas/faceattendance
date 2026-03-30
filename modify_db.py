import re

with open('db.py', 'r') as f:
    code = f.read()

# Replace schema creation for employees
old_emp_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='employees' and xtype='U')
           CREATE TABLE employees (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) UNIQUE NOT NULL,
               name NVARCHAR(100) NOT NULL,
               email VARCHAR(100),
               department NVARCHAR(100),
               role VARCHAR(20) DEFAULT 'employee',
               password VARCHAR(255),
               face_embedding VARCHAR(MAX),
               face_image VARBINARY(MAX),
               created_at DATETIME DEFAULT GETDATE()
           )'''
new_emp_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='employees' and xtype='U')
           CREATE TABLE employees (
               id VARCHAR(50) PRIMARY KEY,
               name NVARCHAR(100) NOT NULL,
               email VARCHAR(100),
               role VARCHAR(20) DEFAULT 'employee',
               password VARCHAR(255),
               face_embedding VARCHAR(MAX),
               face_image VARBINARY(MAX),
               created_at DATETIME DEFAULT GETDATE()
           )'''
code = code.replace(old_emp_schema, new_emp_schema)

# Replace attendance schema
old_att_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='attendance' and xtype='U')
           CREATE TABLE attendance (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               date DATE NOT NULL,
               check_in DATETIME,
               check_out DATETIME,
               working_hours FLOAT DEFAULT 0,
               status VARCHAR(50) DEFAULT 'Present',
               late_reason NVARCHAR(255)
           )'''
new_att_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='attendance' and xtype='U')
           CREATE TABLE attendance (
               attendance_id INT IDENTITY(1,1) PRIMARY KEY,
               id VARCHAR(50) NOT NULL,
               date DATE NOT NULL,
               check_in DATETIME,
               check_out DATETIME,
               working_hours FLOAT DEFAULT 0,
               status VARCHAR(50) DEFAULT 'Present',
               late_reason NVARCHAR(255)
           )'''
code = code.replace(old_att_schema, new_att_schema)

# Replace meetings schema
old_meet_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='meetings' and xtype='U')
           CREATE TABLE meetings (
               id INT IDENTITY(1,1) PRIMARY KEY,
               title NVARCHAR(255) NOT NULL,
               description NVARCHAR(MAX),
               meeting_date DATE NOT NULL,
               meeting_time VARCHAR(10) NOT NULL,
               employee_id VARCHAR(50),
               created_by VARCHAR(50) DEFAULT 'admin',
               created_at DATETIME DEFAULT GETDATE()
           )'''
new_meet_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='meetings' and xtype='U')
           CREATE TABLE meetings (
               meeting_id INT IDENTITY(1,1) PRIMARY KEY,
               title NVARCHAR(255) NOT NULL,
               description NVARCHAR(MAX),
               meeting_date DATE NOT NULL,
               meeting_time VARCHAR(10) NOT NULL,
               id VARCHAR(50),
               created_by VARCHAR(50) DEFAULT 'admin',
               created_at DATETIME DEFAULT GETDATE()
           )'''
code = code.replace(old_meet_schema, new_meet_schema)

# Remove admin schema
admin_schema = '''        \"\"\"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='admin_users' and xtype='U')
           CREATE TABLE admin_users (
               id INT IDENTITY(1,1) PRIMARY KEY,
               username VARCHAR(50) UNIQUE NOT NULL,
               password VARCHAR(255) NOT NULL,
               created_at DATETIME DEFAULT GETDATE()
           )\"\"\",\n'''
code = code.replace(admin_schema, '')

# Replace log schema
old_log_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='login_logs' and xtype='U')
           CREATE TABLE login_logs (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               login_time DATETIME DEFAULT GETDATE(),
               date DATE DEFAULT CAST(GETDATE() AS DATE)
           )'''
new_log_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='login_logs' and xtype='U')
           CREATE TABLE login_logs (
               log_id INT IDENTITY(1,1) PRIMARY KEY,
               id VARCHAR(50) NOT NULL,
               login_time DATETIME DEFAULT GETDATE(),
               date DATE DEFAULT CAST(GETDATE() AS DATE)
           )'''
code = code.replace(old_log_schema, new_log_schema)

# Replace leave schema
old_leave_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='leave_requests' and xtype='U')
           CREATE TABLE leave_requests (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               leave_type VARCHAR(100) NOT NULL,
               from_date DATE NOT NULL,
               to_date DATE NOT NULL,
               reason NVARCHAR(MAX),
               status VARCHAR(50) DEFAULT 'Pending',
               created_at DATETIME DEFAULT GETDATE()
           )'''
new_leave_schema = '''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='leave_requests' and xtype='U')
           CREATE TABLE leave_requests (
               leave_id INT IDENTITY(1,1) PRIMARY KEY,
               id VARCHAR(50) NOT NULL,
               leave_type VARCHAR(100) NOT NULL,
               from_date DATE NOT NULL,
               to_date DATE NOT NULL,
               reason NVARCHAR(MAX),
               status VARCHAR(50) DEFAULT 'Pending',
               created_at DATETIME DEFAULT GETDATE()
           )'''
code = code.replace(old_leave_schema, new_leave_schema)

# Admin logic
old_admin_logic = '''c.execute("SELECT id FROM admin_users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO admin_users (username, password) VALUES ('admin','admin123')")'''
new_admin_logic = '''c.execute("SELECT id FROM employees WHERE id='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO employees (id, name, role, password) VALUES ('admin', 'System Admin', 'admin', 'admin123')")'''
code = code.replace(old_admin_logic, new_admin_logic)

# General employee_id -> id for table selects where we want internal query to use id
# We only want to alias to employee_id if returning it to frontend API.
# Let's actually rename employee_id to id in ALL queries.
code = re.sub(r'SELECT employee_id,\s+', 'SELECT id AS employee_id, ', code)
code = re.sub(r'SELECT employee_id\b', 'SELECT id AS employee_id', code)
code = re.sub(r'e\.employee_id\b', 'e.id AS employee_id', code)
code = re.sub(r'a\.employee_id\b', 'a.id', code)
code = re.sub(r'lr\.employee_id\b', 'lr.id', code)

# Fix remaining WHERE clauses
code = code.replace("WHERE employee_id=?", "WHERE id=?")

# Remove department logic from SELECTs
code = code.replace("email, department, role, created_at", "email, role, created_at")
code = code.replace("e.id AS employee_id, e.name, e.department,", "e.id AS employee_id, e.name,")
code = code.replace("e.name as employee_name, e.department", "e.name as employee_name")

# Fix insert and update parameter bindings
code = code.replace("INSERT INTO login_logs (employee_id)", "INSERT INTO login_logs (id)")

code = code.replace(
    "(employee_id, name, email, department, role, password, face_embedding, face_image)",
    "(id, name, email, role, password, face_embedding, face_image)"
)

code = code.replace(
    "(data['employee_id'], data['name'], data['email'], data['department'],\n          data.get('role', 'employee')",
    "(data['employee_id'], data['name'], data['email'],\n          data.get('role', 'employee')"
)

code = code.replace(
    "INSERT INTO attendance (employee_id, date, check_in, status, late_reason)",
    "INSERT INTO attendance (id, date, check_in, status, late_reason)"
)

code = code.replace(
    "INSERT INTO leave_requests\n                 (employee_id, leave_type, from_date, to_date, reason, status)",
    "INSERT INTO leave_requests\n                 (id, leave_type, from_date, to_date, reason, status)"
)

code = code.replace(
    "INSERT INTO meetings (title, description, meeting_date, meeting_time, employee_id, created_by)",
    "INSERT INTO meetings (title, description, meeting_date, meeting_time, id, created_by)"
)

# Update the Check Out logic which previously accessed attendance.id, we renamed to attendance_id
code = code.replace("SELECT id, check_in FROM attendance", "SELECT attendance_id, check_in FROM attendance")
code = code.replace("SET check_out=?, working_hours=? WHERE id=?", "SET check_out=?, working_hours=? WHERE attendance_id=?")
code = code.replace("SELECT id FROM attendance WHERE", "SELECT attendance_id FROM attendance WHERE")

# Rename other occurrences inside DB fetch queries where we need AS employee_id to keep the interface intact
# For get_all_embeddings
code = code.replace("SELECT id AS employee_id, name, face_embedding FROM employees", "SELECT id AS employee_id, name, face_embedding FROM employees")
# We already replaced `SELECT employee_id, ` with `SELECT id AS employee_id, ` 
# But let's check remaining
code = code.replace("employee_id AS employee_id", "id AS employee_id")
code = code.replace("e.id AS employee_id =", "e.id =")
code = code.replace("ON e.id AS employee_id = a.id", "ON e.id = a.id")
code = code.replace("ON lr.id = e.id AS employee_id", "ON lr.id = e.id")
code = code.replace("ON a.id = e.id AS employee_id", "ON a.id = e.id")
code = code.replace("= e.employee_id", "= e.id")
code = code.replace("a.employee_id", "a.id")

# Return dict keys for get_employee
# Since get_employee fetches * FROM employees WHERE id=?, it returns `id` inside row, not `employee_id`. 
# We should artificially inject it so `app.py` doesn't break if it expects row['employee_id']
# Actually app.py doesn't unpack it from get_employee very strictly. Wait, get_employee result is JSON'd!
code += """
# Patch get_employee to map 'id' -> 'employee_id' for output backward compatibility
_get_employee_orig = get_employee
def get_employee(emp_id):
    row = _get_employee_orig(emp_id)
    if row and 'id' in row:
        row['employee_id'] = row['id']
    return row
"""

with open('db.py', 'w') as f:
    f.write(code)
print('db.py updated successfully!')
