import db

def verify_notifications():
    user_id = "admin"
    print(f"--- Starting verification for Notifications ---")
    
    # 1. Initialize DB to trigger migrations
    print("Initializing DB and running migrations...")
    db.init_db()
    
    # 2. Add a test notification
    print(f"Adding test notification for {user_id}...")
    try:
        db.add_notification(user_id, "Test Notification for recipient_id fix")
        print("Notification added successfully.")
    except Exception as e:
        print(f"Failed to add notification: {e}")
        return

    # 3. Retrieve notifications
    print(f"Retrieving notifications for {user_id}...")
    try:
        notes = db.get_notifications(user_id)
        found = False
        for n in notes:
            if n.get('message') == "Test Notification for recipient_id fix":
                print(f"SUCCESS: Found the test notification: {n}")
                found = True
                break
        if not found:
            print("FAIL: Test notification not found in retrieved list.")
    except Exception as e:
        print(f"Failed to retrieve notifications: {e}")

    print("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_notifications()
