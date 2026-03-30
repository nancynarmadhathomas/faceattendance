import pyodbc

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def fix_live():
    try:
        conn = pyodbc.connect(CONN_STR)
        c = conn.cursor()
        
        try:
            c.execute("EXEC sp_rename 'users.user_id', 'employee_id', 'COLUMN'")
            conn.commit()
            print("Renamed users.user_id to employee_id")
        except Exception as e:
            print(f"Rename failed (might already be fixed): {e}")

        try:
            c.execute("ALTER TABLE meetings DROP COLUMN employee_id")
            conn.commit()
            print("Dropped employee_id from meetings")
        except Exception as e:
            print(f"Drop failed (might already be removed): {e}")
            
        print("Live DB fix complete.")
    except Exception as e:
        print("Could not connect to db:", e)

if __name__ == '__main__':
    fix_live()
