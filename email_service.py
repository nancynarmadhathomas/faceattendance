import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# --- Configuration (Gmail SMTP) ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASS = "app_password"
SENDER_EMAIL = SMTP_USER

def send_email(to_email, subject, body):
    """Generic helper to send email via SMTP."""
    if not to_email:
        print("DEBUG: No recipient email provided. Skipping email.")
        return False
        
    print("Sending email...")
    print("Recipient:", to_email)
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print(f"DEBUG: Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print("Email error:", str(e))
        return False

# --- Specific Notification Functions ---

def notify_attendance(user_name, user_email, time, status):
    """Subject: Attendance Recorded"""
    subject = "Attendance Recorded"
    body = f"Hello {user_name},\n\nYou clocked in at {time}.\nStatus: {status}\nWorking hours will be calculated after clock-out.\n\nBest regards,\nKolozen Face Attendance"
    send_email(user_email, subject, body)

def notify_checkout(user_name, user_email, hours):
    """Subject: Attendance Summary"""
    subject = "Attendance Summary"
    body = f"Hello {user_name},\n\nYou have clocked out.\nTotal hours worked today: {hours} hours.\n\nBest regards,\nKolozen Face Attendance"
    send_email(user_email, subject, body)

def send_clockin_email(email, name, user_id, time, status, reason=None):
    """Unified function for all clock-in notifications."""
    if status == "Late":
        subject = "Late Attendance Alert"
        body = f"Employee Name: {name}\nEmployee ID: {user_id}\nClock-in Time: {time}\nStatus: Late\nReason: {reason}"
    else:
        subject = "Attendance Recorded"
        body = f"Employee Name: {name}\nEmployee ID: {user_id}\nClock-in Time: {time}\nStatus: Present\n\nMessage:\nYou have successfully clocked in on time."
    
    return send_email(email, subject, body)

def send_checkout_email(email, name, user_id, clock_in, clock_out, hours, status):
    """Specific checkout email with work summary."""
    subject = "Work Summary"
    body = (
        f"Employee Name: {name}\n"
        f"Employee ID: {user_id}\n"
        f"Clock-in: {clock_in}\n"
        f"Clock out: {clock_out}\n"
        f"Total Hours: {hours}h\n"
        f"Status: {status}\n\n"
        f"Thank you for your work today!"
    )
    return send_email(email, subject, body)

def notify_late_arrival(user_name, user_email, time):
    """Subject: Late Attendance Alert"""
    subject = "Late Attendance Alert"
    body = f"Hello {user_name},\n\nYou clocked in late today at {time}.\nPlease ensure to follow shift timings.\n\nBest regards,\nHR Department"
    send_email(user_email, subject, body)

def send_late_email(email, name, user_id, time, reason):
    """Specific late email with reason as per requirements."""
    subject = "Late Attendance Alert"
    body = f"Employee Name: {name}\nEmployee ID: {user_id}\nClock-in Time: {time}\nStatus: Late\nReason: {reason}"
    
    print("Late detected")
    print("Sending late email to:", email)
    return send_email(email, subject, body)

def notify_leave_submitted(user_name, user_email, leave_type, from_date, to_date):
    """Subject: Leave Request Submitted"""
    subject = "Leave Request Submitted"
    body = f"Hello {user_name},\n\nYour {leave_type} request from {from_date} to {to_date} has been submitted and is pending approval.\n\nBest regards,\nHR Department"
    send_email(user_email, subject, body)

def notify_leave_status(user_name, user_email, status, from_date):
    """Subject: Leave Request Updated"""
    subject = f"Leave Request {status}"
    body = f"Hello {user_name},\n\nYour leave request starting {from_date} has been {status}.\n\nBest regards,\nHR Department"
    send_email(user_email, subject, body)

def notify_new_meeting(user_name, user_email, title, m_date, m_time):
    """Subject: New Meeting Scheduled"""
    subject = f"New Meeting: {title}"
    body = f"Hello {user_name},\n\nA new meeting '{title}' has been scheduled for {m_date} at {m_time}.\nPlease be on time.\n\nBest regards,\nKolozen Team"
    send_email(user_email, subject, body)

def notify_project_assigned(user_name, user_email, title, deadline):
    """Subject: New Project Assigned"""
    subject = f"New Project Assignment: {title}"
    body = f"Hello {user_name},\n\nYou have been assigned to a new project: {title}.\nDeadline: {deadline}\nPlease check your dashboard for details.\n\nBest regards,\nKolozen Projects"
    send_email(user_email, subject, body)
