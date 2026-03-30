import pyodbc

def run_check():
    try:
        conn = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};'
            'Server=localhost\\SQLEXPRESS;'
            'Database=face_attendance;'
            'Trusted_Connection=yes;'
            'TrustServerCertificate=yes;'
        )
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"\n[{table}] - {count} rows")
            
            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}' ORDER BY ORDINAL_POSITION")
            cols = cursor.fetchall()
            for col in cols:
                print(f"  - {col[0]} ({col[1]}{'(' + str(col[2]) + ')' if col[2] else ''})")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    run_check()
