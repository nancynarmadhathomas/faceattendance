import pyodbc
import json

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=face_attendance;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def export_users():
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT employee_id, name, role FROM users")
        rows = cursor.fetchall()
        users = []
        for row in rows:
            users.append({"id": row.employee_id, "name": row.name, "role": row.role})
        
        with open("users_debug.json", "w") as f:
            json.dump(users, f)
        
        print("Exported users to users_debug.json")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    export_users()
