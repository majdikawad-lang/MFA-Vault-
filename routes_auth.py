from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from datetime import datetime
from models import db, User, log_action
from extensions import bcrypt
from utils import generate_otp, send_email_otp, send_security_alert_email, send_reactivation_email, validate_password
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            log_action("Registration Failed", "Email already exists", email, "WARNING")
            flash("Email already registered.", "danger")
            return redirect(url_for('auth.register'))

        if not validate_password(password):
            log_action("Registration Failed", "Weak password used", email, "WARNING")
            flash("Password must be at least 8 characters, include uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for('auth.register'))

        otp = generate_otp()
        session['reg_temp'] = {'name': name, 'email': email, 'pwd': bcrypt.generate_password_hash(password).decode('utf-8')}
        session['reg_otp'] = otp

        success = send_email_otp(email, otp)
        if success:
            log_action("OTP Sent", "Registration OTP sent", email)
            flash("An OTP has been sent to your email.", "info")
            return redirect(url_for('auth.otp_register'))
        else:
            log_action("OTP Failed", "Failed to send Registration OTP email", email, "ERROR")
            flash("Error sending email. Please check your SMTP configuration.", "danger")

    return render_template('register.html')

@auth_bp.route('/otp_register', methods=['GET', 'POST'])
def otp_register():
    if 'reg_temp' not in session:
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        temp = session.get('reg_temp')
        if request.form['otp'] == session.get('reg_otp'):
            temp = session.pop('reg_temp')
            session.pop('reg_otp', None)
            
            new_user = User(name=temp['name'], email=temp['email'], password_hash=temp['pwd'])
            db.session.add(new_user)
            db.session.commit()
            
            log_action("User Registered", "New user successfully created", temp['email'])
            flash("Registration successful! Please log in, and ensure you setup Hand/Face auth in your profile.", "success")
            return redirect(url_for('auth.login'))
        else:
            log_action("Invalid OTP", "Failed registration OTP", temp['email'], "WARNING")
            flash("Invalid OTP.", "danger")

    return render_template('otp.html', action_url=url_for('auth.otp_register'), title="Register Verification")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # 1. SQL Injection Detection
        sql_patterns = ["'", "\"", ";", "--", "OR 1=1", "DROP", "UNION", "/*", "*/"]
        if any(pattern.upper() in email.upper() or pattern in email for pattern in sql_patterns):
            log_action("SQL Injection Attempt", f"Malicious input detected in email field: {email}", email, "ERROR")
            flash("Security Alert: Malicious input detected. This action has been logged.", "danger")
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()

        if user:
            # Check if user is suspended
            if user.is_suspended:
                log_action("Login Prevented", "Suspended user tried to log in", email, "WARNING")
                flash("Your account is temporarily suspended for investigation. Please check your email to reactivate your account.", "danger")
                return redirect(url_for('auth.login'))

            if bcrypt.check_password_hash(user.password_hash, password):
                # Reset failed login attempts
                user.failed_login_attempts = 0
                db.session.commit()

                # Bypass MFA for Admin
                if getattr(user, 'is_admin', False):
                    session['user_id'] = user.id
                    session['last_active'] = datetime.utcnow().isoformat()
                    log_action("Admin Login", "Admin logged in bypassing MFA", email)
                    flash("Admin login successful.", "success")
                    return redirect(url_for('admin.admin_dashboard'))

                # Normal user: Check if OTP verified within last 3 days
                from datetime import timedelta
                if user.last_otp_verified and datetime.utcnow() - user.last_otp_verified < timedelta(days=3):
                    session['login_temp_user_id'] = user.id
                    log_action("Login OTP Bypassed", "OTP bypassed (verified within last 3 days)", email)
                    
                    if user.hand_data or user.face_data:
                        session['biometric_needed'] = True
                        flash("Welcome back! Please verify biometric to unlock.", "info")
                        return redirect(url_for('biometric.biometric_verify'))
                    else:
                        session['user_id'] = user.id
                        session['last_active'] = datetime.utcnow().isoformat()
                        session.pop('login_temp_user_id', None)
                        flash("Welcome back!", "success")
                        return redirect(url_for('main.dashboard'))

                # Normal user MFA OTP (Not verified in last 3 days)
                otp = generate_otp()
                session['login_temp_user_id'] = user.id
                session['login_otp'] = otp
                success = send_email_otp(email, otp)
                if success:
                    log_action("OTP Sent", "Login OTP sent", email)
                    flash("An OTP has been sent to your email.", "info")
                    return redirect(url_for('auth.otp_login'))
                else:
                    log_action("OTP Failed", "Failed to send Login OTP email", email, "ERROR")
                    flash("Error sending email OTP. Please check your SMTP configuration.", "danger")
            else:
                # Failed password
                user.failed_login_attempts += 1
                db.session.commit()
                log_action("Login Failed", f"Invalid credentials. Attempt {user.failed_login_attempts} of 5", email, "WARNING")

                if user.failed_login_attempts >= 5:
                    log_action("Brute Force Detected", "5 consecutive failed login attempts.", email, "CRITICAL")
                    send_security_alert_email(email)
                    flash("Access temporarily blocked due to multiple failed attempts. A security alert email has been sent to your inbox.", "danger")
                else:
                    flash(f"Invalid credentials. Attempt {user.failed_login_attempts} of 5.", "danger")
        else:
            # User not found (generic message for security)
            flash("Invalid credentials.", "danger")

    return render_template('login.html')

@auth_bp.route('/otp_login', methods=['GET', 'POST'])
def otp_login():
    if 'login_temp_user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session.get('login_temp_user_id')
    user = User.query.get(user_id)

    if request.method == 'POST':
        if request.form['otp'] == session.get('login_otp'):
            user.last_otp_verified = datetime.utcnow()
            db.session.commit()
            
            if user.hand_data or user.face_data:
                # Need biometric
                session['biometric_needed'] = True
                log_action("OTP Verified", "User passed OTP phase, proceeding to bio", user.email)
                flash("OTP Verified. Proceed to biometric verification.", "success")
                return redirect(url_for('biometric.biometric_verify'))
            else:
                # No biometric set up
                session['user_id'] = user.id
                session['last_active'] = datetime.utcnow().isoformat()
                session.pop('login_temp_user_id', None)
                session.pop('login_otp', None)
                log_action("Login Success", "User completed login (no bio set)", user.email)
                flash("Welcome! Please set up your Hand/Face verification in the Profile.", "warning")
                return redirect(url_for('main.dashboard'))
        else:
            log_action("Login Failed", "Invalid OTP entered during login", user.email, "WARNING")
            flash("Invalid OTP.", "danger")

    return render_template('otp.html', action_url=url_for('auth.otp_login'), title="Login Verification")

@auth_bp.route('/reactivate', methods=['GET'])
def reactivate():
    token = request.args.get('token')
    if not token:
        flash("Invalid activation link.", "danger")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(reactivation_token=token).first()
    if user:
        user.is_suspended = False
        user.reactivation_token = None
        user.failed_login_attempts = 0  # Also reset failed login attempts
        db.session.commit()
        log_action("Account Reactivated", "User reactivated account via email token link", user.email)
        flash("Your account has been reactivated successfully! You can now log in.", "success")
    else:
        flash("Invalid or expired reactivation token.", "danger")

    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            log_action("Logout", "User logged out", user.email)
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))
