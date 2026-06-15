import logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    hand_data = db.Column(db.Text, nullable=True) # Will store JSON string of features
    face_data = db.Column(db.Text, nullable=True) # For colleague to implement later
    is_admin = db.Column(db.Boolean, default=False)
    is_suspended = db.Column(db.Boolean, default=False)
    reactivation_token = db.Column(db.String(100), nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_otp_verified = db.Column(db.DateTime, nullable=True)
    storage_used = db.Column(db.BigInteger, default=0) # Track in bytes
    storage_limit = db.Column(db.BigInteger, default=3 * 1024 * 1024 * 1024) # 3GB default
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

class StorageItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False) # UUID based filename on disk
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='files') # files, photos, videos
    file_size = db.Column(db.BigInteger, nullable=False) # Size in bytes
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('files', lazy=True))

class SecureCredential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    username_field = db.Column(db.String(120), nullable=True)
    encrypted_password = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('credentials', lazy=True))

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20), nullable=False) # e.g. INFO, WARNING, ERROR
    target_email = db.Column(db.String(120), nullable=True) # Email of user involved
    event_type = db.Column(db.String(100), nullable=False) # e.g. Login, Failed Login, OTP
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<SystemLog {self.event_type} - {self.timestamp}>'

class SmtpConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(120), nullable=False, default="smtp.gmail.com")
    smtp_port = db.Column(db.Integer, nullable=False, default=465)
    sender_email = db.Column(db.String(120), nullable=False, default="YOUR_EMAIL@gmail.com")
    app_password = db.Column(db.String(120), nullable=False, default="YOUR_APP_PASSWORD")
    use_ssl = db.Column(db.Boolean, default=True)

def log_action(event_type, message, target_email=None, level='INFO'):
    # Log to file
    if level == 'INFO':
        logging.info(f"{event_type} | {target_email} | {message}")
    elif level == 'WARNING':
        logging.warning(f"{event_type} | {target_email} | {message}")
    elif level == 'ERROR':
        logging.error(f"{event_type} | {target_email} | {message}")
    elif level == 'CRITICAL':
        logging.critical(f"{event_type} | {target_email} | {message}")
        
    # Log to DB
    new_log = SystemLog(level=level, event_type=event_type, message=message, target_email=target_email)
    db.session.add(new_log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Logging failed:", e)
