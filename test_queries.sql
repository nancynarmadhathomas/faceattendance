-- ==========================================
-- TEST QUERIES FOR FACE ATTENDANCE SYSTEM 
-- Database: face_attendance.db (SQLite)
-- ==========================================

-- 1. INSPECT CURRENT DATA
SELECT * FROM employees;
SELECT * FROM admin_users;
SELECT * FROM attendance;
SELECT * FROM meetings;
SELECT * FROM leave_requests;

-- 2. ADD MOCK EMPLOYEES (Note: face_image and face_embedding will be null here so 'login by face' won't work for these, but dashboard login via session will)
INSERT INTO employees (employee_id, name, email, department, role) 
VALUES 
    ('EMP001', 'Alice Smith', 'alice@kolozen.com', 'Engineering', 'employee'),
    ('EMP002', 'Bob Johnson', 'bob@kolozen.com', 'HR', 'employee'),
    ('EMP003', 'Charlie Brown', 'charlie@kolozen.com', 'Marketing', 'manager');

-- 3. MOCK ATTENDANCE RECORDS (Simulating past few days)
-- Present day (full 9 hours)
INSERT INTO attendance (employee_id, date, check_in, check_out, working_hours, status)
VALUES ('EMP001', date('now', '-1 day'), datetime('now', '-1 day', '09:00:00'), datetime('now', '-1 day', '18:00:00'), 9.0, 'present');

-- Late day
INSERT INTO attendance (employee_id, date, check_in, working_hours, status, late_reason)
VALUES ('EMP002', date('now'), datetime('now', '10:15:00'), 0, 'late', 'Heavy Traffic');

-- Checked-in currently
INSERT INTO attendance (employee_id, date, check_in, working_hours, status)
VALUES ('EMP001', date('now'), datetime('now', '08:50:00'), 0, 'present');

-- 4. CREATE MOCK MEETINGS
-- Meeting for everyone
INSERT INTO meetings (title, description, meeting_date, meeting_time, created_by)
VALUES ('All Hands Sync', 'Weekly company update', date('now', '+1 day'), '10:00', 'admin');

-- Meeting specifically for Alice
INSERT INTO meetings (title, description, meeting_date, meeting_time, employee_id, created_by)
VALUES ('1-on-1 Review', 'Quarterly performance review', date('now', '+2 days'), '14:30', 'EMP001', 'admin');

-- 5. CREATE LEAVE REQUESTS
-- Pending leave request
INSERT INTO leave_requests (employee_id, leave_type, from_date, to_date, reason, status)
VALUES ('EMP002', 'Sick Leave', date('now', '+3 days'), date('now', '+4 days'), 'Severe cold', 'Pending');

-- Approved leave request
INSERT INTO leave_requests (employee_id, leave_type, from_date, to_date, reason, status)
VALUES ('EMP001', 'Casual Leave', date('now', '-5 days'), date('now', '-5 days'), 'Family function', 'Approved');

-- 6. RESET/CLEANUP (DANGER ZONE)
-- DELETE FROM attendance;
-- DELETE FROM employees WHERE employee_id IN ('EMP001', 'EMP002', 'EMP003');
-- UPDATE sqlite_sequence SET seq = 0 WHERE name IN ('attendance', 'employees');
