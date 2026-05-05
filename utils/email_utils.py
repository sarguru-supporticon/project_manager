import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def get_smtp_config():
    """Get SMTP config from Streamlit secrets or session state."""
    try:
        return {
            'host': st.secrets.get("SMTP_HOST", "smtp.gmail.com"),
            'port': int(st.secrets.get("SMTP_PORT", 587)),
            'user': st.secrets.get("SMTP_USER", ""),
            'password': st.secrets.get("SMTP_PASSWORD", ""),
            'from_name': st.secrets.get("FROM_NAME", "Project Manager"),
        }
    except:
        return {
            'host': "smtp.gmail.com",
            'port': 587,
            'user': "",
            'password': "",
            'from_name': "Project Manager",
        }

def send_email(to_email, subject, body_html, body_text=None):
    """Send an email via Gmail SMTP."""
    config = get_smtp_config()
    if not config['user'] or not config['password']:
        return False, "SMTP not configured. Add credentials to .streamlit/secrets.toml"

    try:
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = f"{config['from_name']} <{config['user']}>"
        msg['To'] = to_email

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(config['host'], config['port']) as server:
            server.ehlo()
            server.starttls()
            server.login(config['user'], config['password'])
            server.sendmail(config['user'], to_email, msg.as_string())
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

def email_template(title, content, footer=""):
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f6f9;margin:0;padding:20px;">
    <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px 40px;">
            <h1 style="color:#fff;margin:0;font-size:24px;">📋 Project Manager</h1>
        </div>
        <div style="padding:30px 40px;">
            <h2 style="color:#333;margin-top:0;">{title}</h2>
            {content}
        </div>
        <div style="background:#f8f9fa;padding:20px 40px;text-align:center;color:#888;font-size:12px;">
            {footer if footer else 'This is an automated message from your Project Management System.'}
        </div>
    </div>
    </body></html>
    """

def notify_task_assigned(task_title, project_name, assignee_name, assignee_email,
                          assigner_name, due_date, priority):
    priority_colors = {'high': '#e74c3c', 'medium': '#f39c12', 'low': '#27ae60'}
    color = priority_colors.get(priority, '#667eea')
    content = f"""
    <p>Hi <strong>{assignee_name}</strong>,</p>
    <p>You have been assigned a new task:</p>
    <div style="background:#f8f9fa;padding:20px;border-radius:8px;border-left:4px solid {color};margin:15px 0;">
        <h3 style="margin:0 0 10px;color:#333;">{task_title}</h3>
        <p style="margin:5px 0;color:#666;"><strong>Project:</strong> {project_name}</p>
        <p style="margin:5px 0;color:#666;"><strong>Priority:</strong>
            <span style="background:{color};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;">{priority.upper()}</span>
        </p>
        <p style="margin:5px 0;color:#666;"><strong>Due Date:</strong> {due_date or 'Not set'}</p>
        <p style="margin:5px 0;color:#666;"><strong>Assigned by:</strong> {assigner_name}</p>
    </div>
    <p>Please log in to the Project Manager to view full details and get started.</p>
    """
    html = email_template(f"New Task Assigned: {task_title}", content)
    return send_email(assignee_email, f"[Task Assigned] {task_title} - {project_name}", html)

def notify_task_status_changed(task_title, project_name, user_email, user_name,
                                old_status, new_status):
    status_emoji = {'todo': '📝', 'inprogress': '🔄', 'review': '👀', 'done': '✅'}
    content = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>A task status has been updated:</p>
    <div style="background:#f8f9fa;padding:20px;border-radius:8px;margin:15px 0;">
        <h3 style="margin:0 0 10px;color:#333;">{task_title}</h3>
        <p style="color:#666;"><strong>Project:</strong> {project_name}</p>
        <p style="color:#666;">
            Status changed: <strong>{status_emoji.get(old_status,'')}{old_status}</strong>
            → <strong>{status_emoji.get(new_status,'')}{new_status}</strong>
        </p>
    </div>
    """
    html = email_template(f"Task Status Updated: {task_title}", content)
    return send_email(user_email, f"[Status Update] {task_title}", html)

def notify_comment_added(task_title, project_name, recipient_email, recipient_name,
                          commenter_name, comment_text):
    content = f"""
    <p>Hi <strong>{recipient_name}</strong>,</p>
    <p><strong>{commenter_name}</strong> commented on a task you're involved in:</p>
    <div style="background:#f8f9fa;padding:20px;border-radius:8px;border-left:4px solid #667eea;margin:15px 0;">
        <p style="color:#666;"><strong>Task:</strong> {task_title}</p>
        <p style="color:#666;"><strong>Project:</strong> {project_name}</p>
        <p style="color:#333;font-style:italic;">"{comment_text}"</p>
    </div>
    """
    html = email_template("New Comment on Your Task", content)
    return send_email(recipient_email, f"[New Comment] {task_title}", html)

def send_project_update(project_name, update_text, recipient_emails, sender_name):
    content = f"""
    <p>A project update has been shared by <strong>{sender_name}</strong>:</p>
    <div style="background:#f8f9fa;padding:20px;border-radius:8px;border-left:4px solid #667eea;margin:15px 0;">
        <h3 style="margin:0 0 10px;color:#333;">📢 {project_name}</h3>
        <p style="color:#333;white-space:pre-line;">{update_text}</p>
    </div>
    """
    html = email_template(f"Project Update: {project_name}", content)
    results = []
    for email in recipient_emails:
        ok, msg = send_email(email, f"[Project Update] {project_name}", html)
        results.append((email, ok, msg))
    return results

def notify_welcome(user_name, user_email, temp_password):
    content = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>Welcome to our Project Management System! Your account has been created.</p>
    <div style="background:#f8f9fa;padding:20px;border-radius:8px;margin:15px 0;">
        <p><strong>Email:</strong> {user_email}</p>
        <p><strong>Temporary Password:</strong> <code style="background:#eee;padding:3px 8px;border-radius:4px;">{temp_password}</code></p>
    </div>
    <p style="color:#e74c3c;"><strong>Please change your password after first login.</strong></p>
    """
    html = email_template("Welcome to Project Manager! 🎉", content)
    return send_email(user_email, "Welcome to Project Manager - Account Created", html)
