import pyodbc
import db

def test_db():
    try:
        print("Connecting to DB...")
        conn = db.get_conn()
        cursor = conn.cursor()
        print("Connected.")
        
        print("Running init_db()...")
        db.init_db()
        print("init_db() success.")
        
        cursor.execute("SELECT TOP 1 * FROM users")
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            print(f"Users table columns: {columns}")
        else:
            print("Users table is empty.")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_db()
