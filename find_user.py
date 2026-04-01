import pyodbc

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def find_user():
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT employee_id, name, email FROM users WHERE name LIKE 'zubairya%'")
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row.employee_id}, Name: {row.name}, Email: {row.email}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_user()
