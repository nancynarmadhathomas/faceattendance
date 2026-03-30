import db
import json
from datetime import date

def test_integration():
    print("--- STARTING INTEGRATION TEST ---")
    db.init_db()
    
    # 1. Create a test employee if not exists
    emp_id = "TEST001"
    emp_name = "Test User"
    if not db.get_employee(emp_id):
        print(f"Creating test employee {emp_id}...")
        db.register_employee({
            'employee_id': emp_id,
            'name': emp_name,
            'email': 'test@example.com',
            'role': 'employee',
            'password': 'password123',
            'face_embedding': json.dumps([0.1]*128),
            'face_image': b''
        })

    # 2. Test Leave Request
    print("Testing Leave Flow...")
    db.create_leave_request({
        'employee_id': emp_id,
        'leave_type': 'Casual Leave',
        'from_date': '01-04-2026',
        'to_date': '02-04-2026',
        'reason': 'Integration Test'
    })
    
    leaves = db.get_leave_requests_by_employee(emp_id)
    latest_leave = leaves[0]
    print(f"  Leave Status (Initial): {latest_leave['status']}")
    
    db.update_leave_status(latest_leave['id'], 'Approved')
    updated_leave = db.get_leave_requests_by_employee(emp_id)[0]
    print(f"  Leave Status (After Approval): {updated_leave['status']}")
    
    if updated_leave['status'] == 'Approved':
        print("  ✅ Leave Approval Success")
    else:
        print("  ❌ Leave Approval Failed")

    # 3. Test Targeted Meetings
    print("\nTesting Meeting Assignments...")
    today = date.today().isoformat()
    
    # Global meeting
    db.create_meeting({
        'title': 'Global Meeting',
        'description': 'For everyone',
        'date': today,
        'time': '10:00',
        'employee_id': None
    })
    
    # Targeted meeting for our test user
    db.create_meeting({
        'title': 'Private Sync',
        'description': 'Just for you',
        'date': today,
        'time': '11:00',
        'employee_id': emp_id
    })
    
    # Targeted meeting for someone else
    db.create_meeting({
        'title': 'Other Sync',
        'description': 'Not for you',
        'date': today,
        'time': '12:00',
        'employee_id': 'EMP999'
    })
    
    my_meetings = db.get_meetings_for_employee(emp_id)
    titles = [m['title'] for m in my_meetings]
    print(f"  Meetings for {emp_id}: {titles}")
    
    success = 'Global Meeting' in titles and 'Private Sync' in titles and 'Other Sync' not in titles
    if success:
        print("  ✅ Meeting Assignment Success")
    else:
        print("  ❌ Meeting Assignment Failed")

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    test_integration()
