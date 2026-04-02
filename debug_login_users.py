import db
import json

def check_users():
    db.init_db()
    users = db.get_all_employees()
    print(f"Total users: {len(users)}")
    for u in users:
        emp = db.get_employee(u['user_id'])
        has_face = emp.get('face_embedding') is not None
        print(f"ID: {u['user_id']}, Name: {u['name']}, Role: {u['role']}, Has Face: {has_face}")

if __name__ == "__main__":
    check_users()
