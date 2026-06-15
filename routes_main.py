from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from models import db, User, log_action
from extensions import bcrypt
from utils import validate_password
from decorators import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            if user.is_admin:
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('vault.vault_dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('vault.vault_dashboard'))

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        if name: user.name = name
        if email: user.email = email
        db.session.commit()
        log_action("Profile Updated", "User updated info", user.email)
        flash("Profile updated successfully.", "success")
        return redirect(url_for('main.profile'))
        
    return render_template('profile.html', user=user)

@main_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        
        if not bcrypt.check_password_hash(user.password_hash, old_password):
            log_action("Password Change Failed", "Incorrect old password", user.email, "WARNING")
            flash("Incorrect old password.", "danger")
            return redirect(url_for('main.change_password'))
            
        if not validate_password(new_password):
            flash("New password must be at least 8 characters, include uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for('main.change_password'))
            
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        log_action("Password Changed", "User successfully changed password", user.email)
        flash("Password successfully updated.", "success")
        return redirect(url_for('main.profile'))
        
    return render_template('change_password.html', user=user)
