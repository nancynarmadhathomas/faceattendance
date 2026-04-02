import db
from datetime import date

def verify_project_capacity():
    user_id = "EMP222" # Assume this exists from early conversation summary
    user_id_2 = "EMP001"
    
    print("--- Starting verification for Project Capacity ---")
    
    # 1. Initialize DB and run migrations
    print("Initializing DB...")
    db.init_db()
    
    # 2. Create a test project with capacity 1
    print("Creating test project with capacity 1...")
    project_data = {
        'title': 'Capacity Test Project',
        'description': 'Testing the FULL status and capacity limits.',
        'members_wanted': 1,
        'deadline': date.today().isoformat(),
        'created_by': 'admin'
    }
    
    # We'll use a modified create_project_assignment or just manual SQL for testing
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO projects (title, description, members_wanted, deadline, created_by)
                 OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?)""",
              (project_data['title'], project_data['description'], project_data['members_wanted'], project_data['deadline'], project_data['created_by']))
    pid = c.fetchone()[0]
    conn.commit()
    print(f"Created project ID: {pid}")

    # 3. User 1 accepts the project
    print(f"User {user_id} accepting project...")
    db.update_project_interest_status(pid, user_id, 'accepted') or c.execute("INSERT INTO project_interest (project_id, user_id, status) VALUES (?, ?, 'accepted')", (pid, user_id))
    conn.commit()
    
    # 4. Check global status for User 2
    print(f"Checking project status for User {user_id_2}...")
    tasks = db.get_employee_project_tasks(user_id_2)
    test_task = next((t for t in tasks if t['project_id'] == pid), None)
    
    if test_task:
        print(f"Found project task: {test_task}")
        if test_task['accepted_count'] == 1 and test_task['project_status'] == 'FULL':
            print("SUCCESS: Project is correctly marked as FULL.")
        else:
            print(f"FAIL: Unexpected status. Count: {test_task['accepted_count']}, Status: {test_task['project_status']}")
    else:
        print("FAIL: Test project not found in employee tasks.")
        
    conn.close()
    print("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_project_capacity()
