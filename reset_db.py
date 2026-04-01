import pyodbc
import db

def reset_database():
    try:
        print("--- DATABASE SCHEMA RESET ---")
        conn = db.get_conn()
        cursor = conn.cursor()
        
        # Drop existing tables to ensure a clean user_id schema
        tables_to_drop = [
            'meeting_responses', 'notifications', 'login_logs', 
            'leave_requests', 'meetings', 'attendance', 'users',
            'project_interest', 'projects'
        ]
        
        print("Dropping old tables...")
        for table in tables_to_drop:
            try:
                # Use cascade-like drop if needed, but simple drop usually works in SQLEXPRESS
                cursor.execute(f"DROP TABLE [{table}]")
                print(f"Dropped: {table}")
            except Exception as e:
                # Table might not exist or have FK constraints
                print(f"Skipping {table}: {e}")
        
        conn.commit()
        print("\nRecreating tables with standardized 'user_id' schema...")
        db.init_db()
        print("Database initialized successfully.")
        
        # Verify the change
        cursor.execute("SELECT TOP 0 * FROM users")
        columns = [column[0] for column in cursor.description]
        print(f"New Users table columns: {columns}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reset_database()
