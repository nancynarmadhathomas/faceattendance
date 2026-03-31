import pyodbc

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def check_columns():
    conn = pyodbc.connect(CONN_STR)
    c = conn.cursor()
    print("Columns in 'notifications':")
    c.execute("SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('notifications')")
    for row in c.fetchall():
        print(f"- {row[0]}")
    conn.close()

if __name__ == "__main__":
    try:
        check_columns()
    except Exception as e:
        print(f"Error: {e}")
