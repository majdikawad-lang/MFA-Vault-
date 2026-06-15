import re
import random
import smtplib
from email.mime.text import MIMEText

def validate_password(password):
    """
    Validates that a password is:
    - At least 8 characters long
    - Contains at least 1 uppercase letter
    - Contains at least 1 lowercase letter
    - Contains at least 1 number
    - Contains at least 1 special character
    """
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    if re.match(pattern, password):
        return True
    return False

def generate_otp():
    return str(random.randint(100000, 999999))

def get_smtp_config():
    from models import SmtpConfig
    # Query database for SMTP settings
    try:
        config = SmtpConfig.query.first()
        return config
    except Exception:
        return None

def send_email_otp(email, otp):
    """
    Sends an OTP to the given email address.
    For this to work, you MUST provide a valid SMTP configuration.
    """
    config = get_smtp_config()

    # Development fallback: If credentials are not set up, print the OTP to the terminal
    if not config or config.sender_email == "YOUR_EMAIL@gmail.com":
        print(f"\n==========================================")
        print(f"DEVELOPMENT OTP FOR {email}: {otp}")
        print(f"==========================================\n")
        return True

    try:
        msg = MIMEText(f"Your OTP code is: {otp}")
        msg['Subject'] = "MFA System - OTP Verification"
        msg['From'] = config.sender_email
        msg['To'] = email

        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port)
            server.login(config.sender_email, config.app_password)
            server.send_message(msg)
            server.quit()
        else:
            server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            server.starttls()
            server.login(config.sender_email, config.app_password)
            server.send_message(msg)
            server.quit()
        return True
    except Exception as e:
        print(f"CRITICAL ERROR sending email to {email}: {e}")
        return False

def send_security_alert_email(email):
    """
    Sends a security alert email warning of failed login attempts.
    """
    config = get_smtp_config()
    
    subject = "Security Alert: Multiple Failed Login Attempts"
    body = (
        "Dear User,\n\n"
        "We have detected multiple failed login attempts on your account.\n"
        "If you did not perform these attempts, someone else might be trying to access your account.\n"
        "We highly recommend that you log in and change your password immediately to secure your account.\n\n"
        "Best regards,\n"
        "MFA Vault Security Team"
    )

    if not config or config.sender_email == "YOUR_EMAIL@gmail.com":
        print(f"\n==========================================")
        print(f"DEVELOPMENT SECURITY ALERT FOR {email}")
        print(body)
        print(f"==========================================\n")
        return True

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = config.sender_email
        msg['To'] = email

        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port)
            server.login(config.sender_email, config.app_password)
            server.send_message(msg)
            server.quit()
        else:
            server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            server.starttls()
            server.login(config.sender_email, config.app_password)
            server.send_message(msg)
            server.quit()
        return True
    except Exception as e:
        print(f"CRITICAL ERROR sending security alert email to {email}: {e}")
        return False

def send_reactivation_email(email, token):
    """
    Sends an account reactivation email containing the link.
    """
    config = get_smtp_config()
    
    reactivation_link = f"http://127.0.0.1:5000/reactivate?token={token}"
    subject = "Account Suspension Notice - Reactivation Required"
    body = (
        "Dear User,\n\n"
        "Your account has been temporarily suspended for investigation by the system administrator.\n"
        "To verify your identity and reactivate your account, please click the link below:\n\n"
        f"{reactivation_link}\n\n"
        "If you did not request this or have questions, please contact the administrator.\n\n"
        "Best regards,\n"
        "MFA Vault Administration Team"
    )

    if not config or config.sender_email == "YOUR_EMAIL@gmail.com":
        print(f"\n==========================================")
        print(f"DEVELOPMENT REACTIVATION EMAIL FOR {email}")
        print(body)
        print(f"==========================================\n")
        return True

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = config.sender_email
        msg['To'] = email

        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port)
            server.login(config.sender_email, config.app_password)
            server.send_message(msg)
            server.quit()
        else:
            server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            server.starttls()
            server.login(config.sender_email, config.app_password)
            server.send_message(msg)
            server.quit()
        return True
    except Exception as e:
        print(f"CRITICAL ERROR sending reactivation email to {email}: {e}")
        return False

import base64
import cv2
import numpy as np

def base64_to_image(b64_string):
    """Converts a base64 encoded data URI to an OpenCV image."""
    try:
        if ',' in b64_string:
            encoded_data = b64_string.split(',')[1]
        else:
            encoded_data = b64_string
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None
