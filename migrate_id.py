import pyodbc

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def migrate():
    conn = pyodbc.connect(CONN_STR)
    c = conn.cursor()
    
    tables = [
        'users', 'attendance', 'meetings', 'leave_requests', 
        'login_logs', 'notifications', 'meeting_responses', 'project_interest'
    ]
    
    for table in tables:
        print(f"Renaming column in {table}...")
        try:
            # Check if column exists before renaming
            c.execute(f"SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('{table}') AND name = 'employee_id'")
            if c.fetchone():
                c.execute(f"EXEC sp_rename '{table}.employee_id', 'user_id', 'COLUMN'")
                print(f"  - Successfully renamed {table}.employee_id to {table}.user_id")
            else:
                print(f"  - Column 'employee_id' not found in {table} (already renamed?)")
        except Exception as e:
            print(f"  - Error renaming {table}.employee_id: {e}")
            
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
