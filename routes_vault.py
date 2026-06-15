from flask import Blueprint, render_template, request, redirect, session, flash, url_for, send_file, current_app
import os
import uuid
import io
from werkzeug.utils import secure_filename
from models import db, User, StorageItem, SecureCredential, log_action
from extensions import cipher_suite
from decorators import login_required

vault_bp = Blueprint('vault', __name__)

@vault_bp.route('/vault')
@login_required
def vault_dashboard():
    user = User.query.get(session['user_id'])

    files = StorageItem.query.filter_by(user_id=user.id).order_by(StorageItem.uploaded_at.desc()).all()
    credentials = SecureCredential.query.filter_by(user_id=user.id).order_by(SecureCredential.created_at.desc()).all()
    
    # Decrypt passwords for display
    decrypted_creds = []
    for cred in credentials:
        try:
            dec_pw = cipher_suite.decrypt(cred.encrypted_password.encode()).decode()
        except Exception:
            dec_pw = "ERROR"
        decrypted_creds.append({
            'id': cred.id,
            'title': cred.title,
            'username': cred.username_field,
            'password': dec_pw,
            'url': cred.url,
            'notes': cred.notes
        })
        
    return render_template('vault_dashboard.html', user=user, files=files, credentials=decrypted_creds)

@vault_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    user = User.query.get(session['user_id'])
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('vault.vault_dashboard'))
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('vault.vault_dashboard'))
        
    file_data = file.read()
    file_size = len(file_data)
    
    if user.storage_used + file_size > user.storage_limit:
        flash("Storage limit exceeded. Please upgrade.", "danger")
        return redirect(url_for('vault.vault_dashboard'))
        
    encrypted_data = cipher_suite.encrypt(file_data)
    
    internal_filename = str(uuid.uuid4())
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], internal_filename)
    
    with open(save_path, 'wb') as f:
        f.write(encrypted_data)
        
    # Determine category
    category = 'files'
    if file.content_type.startswith('image/'): category = 'photos'
    elif file.content_type.startswith('video/'): category = 'videos'
        
    new_item = StorageItem(
        user_id=user.id,
        filename=internal_filename,
        original_filename=secure_filename(file.filename),
        file_type=file.content_type,
        category=category,
        file_size=file_size
    )
    
    user.storage_used += file_size
    db.session.add(new_item)
    db.session.commit()
    
    log_action("File Upload", f"Uploaded {file.filename}", user.email)
    flash("File encrypted and stored successfully.", "success")
    
    return redirect(url_for('vault.vault_dashboard'))

@vault_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    user = User.query.get(session['user_id'])
    item = StorageItem.query.filter_by(id=file_id, user_id=user.id).first()
    if not item:
        flash("File not found.", "danger")
        return redirect(url_for('vault.vault_dashboard'))
        
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.filename)
    if not os.path.exists(file_path):
        flash("File is missing from disk.", "danger")
        return redirect(url_for('vault.vault_dashboard'))
        
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()
        
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    
    log_action("File Download", f"Downloaded {item.original_filename}", user.email)
    return send_file(io.BytesIO(decrypted_data), download_name=item.original_filename, as_attachment=True)

@vault_bp.route('/delete_item/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    user = User.query.get(session['user_id'])
    item = StorageItem.query.filter_by(id=file_id, user_id=user.id).first()
    if item:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        user.storage_used = max(0, user.storage_used - item.file_size)
        db.session.delete(item)
        db.session.commit()
        log_action("File Delete", f"Deleted {item.original_filename}", user.email)
        flash("File deleted successfully.", "success")
        
    return redirect(url_for('vault.vault_dashboard'))

@vault_bp.route('/add_password', methods=['POST'])
@login_required
def add_password():
    user = User.query.get(session['user_id'])
    title = request.form.get('title')
    username = request.form.get('username')
    password = request.form.get('password')
    url = request.form.get('url')
    notes = request.form.get('notes')
    
    enc_password = cipher_suite.encrypt(password.encode()).decode()
    
    new_cred = SecureCredential(
        user_id=user.id,
        title=title,
        username_field=username,
        encrypted_password=enc_password,
        url=url,
        notes=notes
    )
    db.session.add(new_cred)
    db.session.commit()
    
    log_action("Password Added", f"Added credential for {title}", user.email)
    flash("Password securely stored.", "success")
    
    return redirect(url_for('vault.vault_dashboard'))

@vault_bp.route('/delete_password/<int:cred_id>', methods=['POST'])
@login_required
def delete_password(cred_id):
    user = User.query.get(session['user_id'])
    cred = SecureCredential.query.filter_by(id=cred_id, user_id=user.id).first()
    if cred:
        db.session.delete(cred)
        db.session.commit()
        log_action("Password Delete", f"Deleted credential for {cred.title}", user.email)
        flash("Password deleted.", "success")
        
    return redirect(url_for('vault.vault_dashboard'))

@vault_bp.route('/upgrade')
@login_required
def upgrade():
    user = User.query.get(session['user_id'])
    return render_template('upgrade.html', user=user)
