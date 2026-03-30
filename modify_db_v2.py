import re

with open('db.py', 'r') as f:
    code = f.read()

# Replace schema creation block entirely
tables_regex = r"tables = \[.*?\]\n    for stmt in tables:"
new_tables = """tables = [
        \"\"\"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' and xtype='U')
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
           )\"\"\",
        \"\"\"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='attendance' and xtype='U')
           CREATE TABLE attendance (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               date DATE NOT NULL,
               check_in DATETIME,
               check_out DATETIME,
               working_hours FLOAT DEFAULT 0,
               status VARCHAR(50) DEFAULT 'Present',
               late_reason NVARCHAR(255)
           )\"\"\",
        \"\"\"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='meetings' and xtype='U')
           CREATE TABLE meetings (
               id INT IDENTITY(1,1) PRIMARY KEY,
               title NVARCHAR(255) NOT NULL,
               description NVARCHAR(MAX),
               meeting_date DATE NOT NULL,
               meeting_time VARCHAR(10) NOT NULL,
               employee_id VARCHAR(50),
               created_by VARCHAR(50) DEFAULT 'admin',
               created_at DATETIME DEFAULT GETDATE()
           )\"\"\",
        \"\"\"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='leave_requests' and xtype='U')
           CREATE TABLE leave_requests (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               leave_type VARCHAR(100) NOT NULL,
               from_date DATE NOT NULL,
               to_date DATE NOT NULL,
               reason NVARCHAR(MAX),
               status VARCHAR(50) DEFAULT 'Pending',
               created_at DATETIME DEFAULT GETDATE()
           )\"\"\",
        \"\"\"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='login_logs' and xtype='U')
           CREATE TABLE login_logs (
               id INT IDENTITY(1,1) PRIMARY KEY,
               employee_id VARCHAR(50) NOT NULL,
               login_time DATETIME DEFAULT GETDATE(),
               date DATE DEFAULT CAST(GETDATE() AS DATE)
           )\"\"\"
    ]
    for stmt in tables:"""
code = re.sub(tables_regex, new_tables, code, flags=re.DOTALL)

# Modify default admin insert
old_admin = """c.execute("SELECT id FROM employees WHERE id='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO employees (id, name, role, password) VALUES ('admin', 'System Admin', 'admin', 'admin123')")"""
new_admin = """c.execute("SELECT id FROM users WHERE employee_id='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (employee_id, name, role, password) VALUES ('admin', 'System Admin', 'admin', 'admin123')")"""
code = code.replace(old_admin, new_admin)

# Table renaming
code = code.replace('FROM employees', 'FROM users')
code = code.replace('JOIN employees e', 'JOIN users u')
code = code.replace('JOIN employees', 'JOIN users')
code = code.replace('INTO employees', 'INTO users')
code = code.replace('UPDATE employees', 'UPDATE users')
code = code.replace('DELETE FROM employees', 'DELETE FROM users')

code = code.replace('e.id AS employee_id', 'u.employee_id')
code = code.replace('e.id', 'u.employee_id')
code = code.replace('e.name', 'u.name')
code = code.replace('e.department', 'u.department') # department is gone, but let's replace if exists

# Aliases Revert
code = code.replace("SELECT id AS employee_id, name, email, role, created_at FROM users", "SELECT employee_id, name, email, role, created_at FROM users")
code = code.replace("SELECT id AS employee_id, name, face_embedding FROM users", "SELECT employee_id, name, face_embedding FROM users")
code = code.replace("employee_id AS employee_id", "employee_id")

# WHERE parameters revert
code = code.replace("WHERE id=?", "WHERE employee_id=?")

# Insert fixes
code = code.replace("INSERT INTO login_logs (id)", "INSERT INTO login_logs (employee_id)")
code = code.replace("INSERT INTO users (id, name, email, role, password, face_embedding, face_image)", "INSERT INTO users (employee_id, name, email, role, password, face_embedding, face_image)")
code = code.replace("INSERT INTO attendance (id, date, check_in, status, late_reason)", "INSERT INTO attendance (employee_id, date, check_in, status, late_reason)")
code = code.replace("INSERT INTO meetings (title, description, meeting_date, meeting_time, id, created_by)", "INSERT INTO meetings (title, description, meeting_date, meeting_time, employee_id, created_by)")
code = code.replace("INSERT INTO leave_requests\\n                 (id, leave_type, from_date, to_date, reason, status)", "INSERT INTO leave_requests\\n                 (employee_id, leave_type, from_date, to_date, reason, status)")

# Revert specific ID columns
code = code.replace("SELECT attendance_id FROM attendance", "SELECT id FROM attendance")
code = code.replace("SELECT attendance_id, check_in FROM attendance", "SELECT id, check_in FROM attendance")
code = code.replace("WHERE attendance_id=?", "WHERE id=?")

# JOIN conditions fixes
code = code.replace("ON u.employee_id = a.id", "ON u.employee_id = a.employee_id")
code = code.replace("ON a.id = u.employee_id", "ON a.employee_id = u.employee_id")
code = code.replace("ON lr.id = u.employee_id", "ON lr.employee_id = u.employee_id")

# Drop the patch block
patch = '''# Patch get_employee to map 'id' -> 'employee_id' for output backward compatibility
_get_employee_orig = get_employee
def get_employee(emp_id):
    row = _get_employee_orig(emp_id)
    if row and 'id' in row:
        row['employee_id'] = row['id']
    return row'''
code = code.replace(patch, '')

with open('db.py', 'w') as f:
    f.write(code)
print('db.py updated successfully!')
