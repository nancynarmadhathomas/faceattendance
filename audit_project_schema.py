import pyodbc
import db

def audit_pi():
    try:
        conn = db.get_conn()
        cursor = conn.cursor()
        
        for table in ['users', 'project_interest']:
            print(f"\nChecking table: {table}")
            try:
                cursor.execute(f"SELECT TOP 0 * FROM {table}")
                cols = [column[0] for column in cursor.description]
                print(f"Columns: {cols}")
            except Exception as e:
                print(f"Error checking {table}: {e}")
                
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    audit_pi()
