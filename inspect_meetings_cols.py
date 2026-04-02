import pyodbc
CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
try:
    conn = pyodbc.connect(CONN_STR)
    c = conn.cursor()
    print("Columns in 'meetings' table:")
    for row in c.columns(table='meetings'):
        print(row.column_name)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
