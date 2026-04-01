import pyodbc
import db

def check_project_interest():
    try:
        conn = db.get_conn()
        cursor = conn.cursor()
        print("\nChecking table: project_interest")
        try:
            cursor.execute("SELECT TOP 0 * FROM project_interest")
            columns = [column[0] for column in cursor.description]
            print(f"Columns: {columns}")
        except Exception as e:
            print(f"Error: {e}")
            
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_project_interest()
