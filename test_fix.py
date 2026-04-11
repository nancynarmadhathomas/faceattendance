import db
try:
    # Use a likely existing user_id or 'admin'
    res = db.get_today_record('admin')
    print("Success! Result:", res)
except Exception as e:
    print("Failed with error:", e)
