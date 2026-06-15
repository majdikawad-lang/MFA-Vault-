from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from models import db, User, SystemLog, StorageItem, SecureCredential, SmtpConfig, log_action
from extensions import cipher_suite
from decorators import admin_required
from utils import send_reactivation_email
import os
import uuid

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    user = User.query.get(session['user_id'])
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).all()
    all_users = User.query.all()
    
    # Collect some stats
    total_users = User.query.count()
    failed_logins = SystemLog.query.filter(SystemLog.event_type.like('%Failed%')).count()
    
    # Calculate total storage used across system
    total_storage = db.session.query(db.func.sum(User.storage_used)).scalar() or 0
    total_storage_mb = round(total_storage / (1024 * 1024), 2)
    
    # Fetch SMTP settings for admin panel
    smtp_config = SmtpConfig.query.first()
    
    return render_template(
        'admin_dashboard.html', 
        user=user, 
        logs=logs, 
        all_users=all_users, 
        total_users=total_users, 
        failed_logins=failed_logins, 
        total_storage_mb=total_storage_mb, 
        smtp_config=smtp_config
    )

@admin_bp.route('/admin/delete_user/<int:del_user_id>', methods=['POST'])
@admin_required
def delete_user(del_user_id):
    admin_user = User.query.get(session['user_id'])
    if admin_user.id == del_user_id:
        flash("Cannot delete your own admin account.", "danger")
        return redirect(url_for('admin.admin_dashboard'))
        
    user_to_del = User.query.get(del_user_id)
    if user_to_del:
        # Delete associated items from disk
        items = StorageItem.query.filter_by(user_id=del_user_id).all()
        for item in items:
            from flask import current_app
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(item)
            
        SecureCredential.query.filter_by(user_id=del_user_id).delete()
        
        email_deleted = user_to_del.email
        db.session.delete(user_to_del)
        db.session.commit()
        log_action("User Deleted", f"Admin deleted user {email_deleted}", admin_user.email)
        flash(f"User {email_deleted} deleted successfully.", "success")
    else:
        flash("User not found.", "danger")
        
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/suspend_user/<int:user_id>', methods=['POST'])
@admin_required
def suspend_user(user_id):
    admin_user = User.query.get(session['user_id'])
    if admin_user.id == user_id:
        flash("You cannot suspend your own admin account.", "danger")
        return redirect(url_for('admin.admin_dashboard'))
        
    user = User.query.get(user_id)
    if user:
        user.is_suspended = True
        user.reactivation_token = str(uuid.uuid4())
        db.session.commit()
        
        # Send reactivation email (will fallback to printing if not configured)
        send_reactivation_email(user.email, user.reactivation_token)
        
        log_action("User Suspended", f"Admin suspended user account. Reactivation email sent.", user.email, "WARNING")
        flash(f"Account {user.email} has been suspended. Reactivation email has been sent.", "success")
    else:
        flash("User not found.", "danger")
        
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/unsuspend_user/<int:user_id>', methods=['POST'])
@admin_required
def unsuspend_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_suspended = False
        user.reactivation_token = None
        user.failed_login_attempts = 0  # reset block attempts
        db.session.commit()
        
        log_action("User Un-suspended", "Admin manually unsuspended user account.", user.email, "INFO")
        flash(f"Account {user.email} has been reactivated successfully.", "success")
    else:
        flash("User not found.", "danger")
        
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/smtp_settings', methods=['POST'])
@admin_required
def smtp_settings():
    smtp_server = request.form.get('smtp_server')
    smtp_port = int(request.form.get('smtp_port', 465))
    sender_email = request.form.get('sender_email')
    app_password = request.form.get('app_password')
    use_ssl = 'use_ssl' in request.form
    
    config = SmtpConfig.query.first()
    if not config:
        config = SmtpConfig()
        db.session.add(config)
        
    config.smtp_server = smtp_server
    config.smtp_port = smtp_port
    config.sender_email = sender_email
    config.app_password = app_password
    config.use_ssl = use_ssl
    
    db.session.commit()
    
    admin_user = User.query.get(session['user_id'])
    log_action("SMTP Settings Updated", "Admin updated SMTP settings config.", admin_user.email, "INFO")
    flash("SMTP Server configurations saved successfully.", "success")
    return redirect(url_for('admin.admin_dashboard'))
