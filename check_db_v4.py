import pyodbc
import db

def audit_schema():
    try:
        conn = db.get_conn()
        cursor = conn.cursor()
        
        tables = ['users', 'attendance', 'meetings', 'leave_requests', 'project_interest', 'projects']
        for table in tables:
            print(f"\nAudit for table: {table}")
            try:
                cursor.execute(f"SELECT TOP 0 * FROM [{table}]")
                columns = [column[0] for column in cursor.description]
                print(f"Columns found: {columns}")
                if 'employee_id' in columns:
                    print("⚠️ WARNING: This table still uses 'employee_id'!")
                if 'user_id' in columns:
                    print("✅ OK: This table uses 'user_id'.")
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    audit_schema()
