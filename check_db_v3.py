import pyodbc
import db

def check_columns():
    try:
        conn = db.get_conn()
        cursor = conn.cursor()
        
        tables = ['users', 'attendance', 'meetings', 'leave_requests']
        for table in tables:
            print(f"\nChecking table: {table}")
            try:
                cursor.execute(f"SELECT TOP 0 * FROM [{table}]")
                columns = [column[0] for column in cursor.description]
                print(f"Columns: {columns}")
            except Exception as e:
                print(f"Error checking {table}: {e}")
                
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_columns()
