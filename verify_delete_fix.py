import db
from datetime import datetime, date

def verify_delete():
    user_id = "TEST_DEL_001"
    print(f"--- Starting verification for User: {user_id} ---")
    
    # 1. Setup Phase: Create user and dependent records
    try:
        # Create user if not exists
        if not db.get_employee(user_id):
            print("Creating test user...")
            db.register_employee({
                'user_id': user_id,
                'name': 'Test Delete User',
                'email': 'test@delete.com',
                'role': 'employee',
                'password': 'password123',
                'face_embedding': None,
                'face_image': None
            })
        
        # Add dependent records
        print("Adding dependent records...")
        conn = db.get_conn()
        c = conn.cursor()
        
        # Attendance
        c.execute("INSERT INTO attendance (user_id, date, status) VALUES (?, CAST(GETDATE() AS DATE), 'Present')", (user_id,))
        
        # Leave Record
        c.execute("INSERT INTO leave_requests (user_id, leave_type, from_date, to_date, status) VALUES (?, 'Sick Leave', CAST(GETDATE() AS DATE), CAST(GETDATE() AS DATE), 'Pending')", (user_id,))
        
        # Meeting
        c.execute("INSERT INTO meetings (title, meeting_date, meeting_time, user_id) VALUES ('Test Meeting', CAST(GETDATE() AS DATE), '10:00', ?)", (user_id,))
        
        # Notification
        c.execute("INSERT INTO notifications (user_id, message) VALUES (?, 'Test Notification')", (user_id,))
        
        # Login Log
        c.execute("INSERT INTO login_logs (user_id) VALUES (?)", (user_id,))
        
        conn.commit()
        conn.close()
        print("Setup complete.")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        return

    # 2. Execution Phase: Delete the employee
    try:
        print(f"Deleting user {user_id}...")
        db.delete_employee(user_id)
        print("Deletion call finished.")
    except Exception as e:
        print(f"Deletion failed with error: {e}")
        return

    # 3. Verification Phase: Check if records still exist
    print("Verifying cleanup...")
    conn = db.get_conn()
    c = conn.cursor()
    
    tables = ['users', 'attendance', 'leave_requests', 'meetings', 'notifications', 'login_logs', 'meeting_responses', 'project_interest']
    all_clean = True
    
    for table in tables:
        c.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id=?", (user_id,))
        count = c.fetchone()[0]
        if count > 0:
            print(f"FAIL: {count} records remain in {table}")
            all_clean = False
        else:
            print(f"SUCCESS: {table} is clean.")
            
    conn.close()
    
    if all_clean:
        print("--- VERIFICATION SUCCESSFUL: ALL RECORDS DELETED ---")
    else:
        print("--- VERIFICATION FAILED: LEFTOVER RECORDS FOUND ---")

if __name__ == "__main__":
    verify_delete()
