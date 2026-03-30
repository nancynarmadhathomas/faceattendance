import db

def fix_meetings_table():
    print("Attempting to add 'employee_id' column to 'meetings' table...")
    conn = db.get_conn()
    c = conn.cursor()
    try:
        # Check if column exists (for SQL Server)
        c.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('meetings') AND name = 'employee_id'
            )
            BEGIN
                ALTER TABLE meetings ADD employee_id VARCHAR(50);
                PRINT 'Column added successfully.';
            END
            ELSE
            BEGIN
                PRINT 'Column already exists.';
            END
        """)
        conn.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_meetings_table()
