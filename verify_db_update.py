import db

def verify():
    print("Initializing DB...")
    db.init_db()
    
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'attendance'")
    columns = [row[0] for row in c.fetchall()]
    conn.close()
    
    print(f"Columns in attendance table: {columns}")
    if 'employee_name' in columns:
        print("SUCCESS: employee_name column exists.")
    else:
        print("FAILURE: employee_name column NOT found.")

if __name__ == "__main__":
    verify()
