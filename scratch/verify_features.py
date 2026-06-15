import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, SmtpConfig
from utils import send_email_otp, send_security_alert_email, send_reactivation_email
from extensions import bcrypt

def verify_all():
    with app.app_context():
        print("=== Checking DB Records ===")
        admin = User.query.filter_by(is_admin=True).first()
        print("Admin found:", admin.email if admin else "None")
        smtp = SmtpConfig.query.first()
        print("SMTP Config found:", smtp.sender_email if smtp else "None")
        
        print("\n=== Testing Email Fallbacks ===")
        # Should print to console because default email is YOUR_EMAIL@gmail.com
        send_email_otp("test_user@example.com", "123456")
        send_security_alert_email("test_user@example.com")
        send_reactivation_email("test_user@example.com", "mock-token-uuid-12345")

        print("\n=== Creating Test User ===")
        test_user = User.query.filter_by(email="test_student@example.com").first()
        if not test_user:
            pw_hash = bcrypt.generate_password_hash("Student123!").decode('utf-8')
            test_user = User(
                name="Test Student",
                email="test_student@example.com",
                password_hash=pw_hash
            )
            db.session.add(test_user)
            db.session.commit()
            print("Created test user: test_student@example.com")
        else:
            print("Test user already exists.")

        print("\n=== Testing Failed Login Attempts Increment ===")
        test_user.failed_login_attempts += 1
        db.session.commit()
        print("Failed attempts incremented to:", test_user.failed_login_attempts)
        
        # Reset failed attempts
        test_user.failed_login_attempts = 0
        db.session.commit()
        print("Reset failed attempts to:", test_user.failed_login_attempts)

        print("\n=== Testing Suspension Toggle ===")
        print("Is suspended initially:", test_user.is_suspended)
        test_user.is_suspended = True
        test_user.reactivation_token = "test-reactivate-token"
        db.session.commit()
        print("Is suspended after suspend:", test_user.is_suspended)
        print("Reactivation token:", test_user.reactivation_token)

        # Query user back
        reactivating_user = User.query.filter_by(reactivation_token="test-reactivate-token").first()
        if reactivating_user:
            reactivating_user.is_suspended = False
            reactivating_user.reactivation_token = None
            db.session.commit()
            print("Successfully reactivated user using token. Is suspended:", reactivating_user.is_suspended)
        else:
            print("Error: Reactivating user not found by token.")

        print("\n=== Testing OTP Bypass Logic ===")
        from datetime import datetime, timedelta
        test_user.last_otp_verified = datetime.utcnow()
        db.session.commit()
        print("Set last_otp_verified to now:", test_user.last_otp_verified)
        is_bypass = test_user.last_otp_verified and datetime.utcnow() - test_user.last_otp_verified < timedelta(days=3)
        print("Is OTP bypassed (should be True):", is_bypass)

        test_user.last_otp_verified = datetime.utcnow() - timedelta(days=4)
        db.session.commit()
        print("Set last_otp_verified to 4 days ago:", test_user.last_otp_verified)
        is_bypass = test_user.last_otp_verified and datetime.utcnow() - test_user.last_otp_verified < timedelta(days=3)
        print("Is OTP bypassed (should be False):", is_bypass)

if __name__ == "__main__":
    verify_all()
