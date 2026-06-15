from flask import Blueprint, render_template, request, jsonify, session, flash, url_for, redirect
from datetime import datetime
import json
import numpy as np
from models import db, User, log_action
from utils import base64_to_image
from hand_tracking import process_hand_frame_for_state, verify_hand_single_image
from face_auth import process_face_image, verify_face_single_image
from decorators import login_required

biometric_bp = Blueprint('biometric', __name__)

@biometric_bp.route('/biometric_verify', methods=['GET'])
def biometric_verify():
    if 'login_temp_user_id' not in session or not session.get('biometric_needed'):
        return redirect(url_for('auth.login'))
        
    user_id = session.get('login_temp_user_id')
    user = User.query.get(user_id)

    return render_template('biometric_verify.html', user=user)

@biometric_bp.route('/camera_capture/<action>/<bio_type>')
def camera_capture(action, bio_type):
    if action == 'enroll':
        if 'user_id' not in session: return redirect(url_for('auth.login'))
        session['hand_state'] = 'waiting_for_open'
        session['hand_data_list'] = []
    elif action == 'verify':
        if 'login_temp_user_id' not in session or not session.get('biometric_needed'):
            return redirect(url_for('auth.login'))
        session['verify_history'] = []
        session['bio_attempts'] = 0  # Initialize biometric mismatch attempts count
        session['hand_state'] = 'waiting_for_open'
    else:
        return redirect(url_for('auth.login'))
        
    return render_template('camera_capture.html', action=action, bio_type=bio_type)

@biometric_bp.route('/api/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    action = data.get('action')
    bio_type = data.get('bio_type')
    img_b64 = data.get('image')
    save_triggered = data.get('save_triggered', False)
    
    img = base64_to_image(img_b64)
    if img is None:
        return jsonify({"status": "processing", "message": "Invalid image format"})
        
    if action == 'enroll':
        if 'user_id' not in session: return jsonify({"status": "failed", "redirect": url_for('auth.login')})
        user = User.query.get(session['user_id'])
        
        if bio_type == 'hand':
            state = session.get('hand_state', 'waiting_for_open')
            data_list = session.get('hand_data_list', [])
            
            new_state, features, msg = process_hand_frame_for_state(img, state)
            
            if new_state == "done":
                data_list.append(features)
                if len(data_list) >= 10:
                    avg_features = np.mean(data_list, axis=0).tolist()
                    user.hand_data = json.dumps(avg_features)
                    db.session.commit()
                    log_action("Biometric Add", "Hand data added via Web", user.email)
                    flash("Hand data added successfully!", "success")
                    return jsonify({"status": "success", "message": "Capture Complete!", "redirect": url_for('main.profile')})
                else:
                    session['hand_data_list'] = data_list
                    return jsonify({"status": "processing", "message": "Hold still... Capturing"})
            else:
                session['hand_state'] = new_state
                return jsonify({"status": "processing", "message": msg})
                
        elif bio_type == 'face':
            if save_triggered:
                embedding = process_face_image(img)
                if embedding:
                    user.face_data = json.dumps(embedding)
                    db.session.commit()
                    log_action("Biometric Add", "Face data added via Web", user.email)
                    flash("Face data added successfully!", "success")
                    return jsonify({"status": "success", "message": "Capture Complete!", "redirect": url_for('main.profile')})
                else:
                    return jsonify({"status": "processing", "message": "No face detected. Try again."})
            else:
                return jsonify({"status": "processing", "message": "Click 'Save Face' when ready"})
                
    elif action == 'verify':
        if 'login_temp_user_id' not in session: return jsonify({"status": "failed", "redirect": url_for('auth.login')})
        user = User.query.get(session['login_temp_user_id'])
        
        if bio_type == 'hand':
            saved_features = json.loads(user.hand_data) if user.hand_data else None
            if not saved_features: return jsonify({"status": "failed", "message": "No hand data saved", "redirect": url_for('auth.login')})
            
            state = session.get('hand_state', 'waiting_for_open')
            new_state, features, msg = process_hand_frame_for_state(img, state)
            
            if new_state != 'done':
                session['hand_state'] = new_state
                return jsonify({"status": "processing", "message": msg})
            else:
                # Sequence completed. Check features.
                if features:
                    a = np.array(features)
                    b = np.array(saved_features)
                    min_len = min(len(a), len(b))
                    if min_len > 0:
                        dist = np.linalg.norm(a[:min_len] - b[:min_len])
                        rms_dist = dist / np.sqrt(min_len)
                        is_match = rms_dist < 0.038
                    else:
                        is_match = False
                    
                    if is_match:
                        session['user_id'] = user.id
                        session['last_active'] = datetime.utcnow().isoformat()
                        session.pop('login_temp_user_id', None)
                        session.pop('login_otp', None)
                        session.pop('biometric_needed', None)
                        session.pop('bio_attempts', None)
                        session.pop('hand_state', None)
                        log_action("Login Success", "Hand verification passed (Web)", user.email)
                        flash("Welcome back!", "success")
                        return jsonify({"status": "success", "message": "Match Found!", "redirect": url_for('vault.vault_dashboard')})
                
                attempts = session.get('bio_attempts', 0) + 1
                session['bio_attempts'] = attempts
                
                if attempts >= 3:
                    session.pop('hand_state', None)
                    session.pop('bio_attempts', None)
                    log_action("Login Failed", "Failed hand biometric verification (attempts limit reached)", user.email, "WARNING")
                    flash("Login failed: Biometric is incorrect.", "danger")
                    return jsonify({"status": "failed", "message": "Login failed: Biometric is incorrect.", "redirect": url_for('auth.login')})
                
                # Reset gesture to retry
                session['hand_state'] = 'waiting_for_open'
                return jsonify({"status": "processing", "message": "Biometric incorrect. Show open hand to retry."})
                
        elif bio_type == 'face':
            saved_features = json.loads(user.face_data) if user.face_data else None
            if not saved_features: return jsonify({"status": "failed", "message": "No face data saved", "redirect": url_for('auth.login')})
            
            is_match = verify_face_single_image(img, saved_features)
            if is_match:
                history = session.get('verify_history', [])
                history.append(True)
                session['verify_history'] = history
                if len(history) >= 2:
                    session['user_id'] = user.id
                    session['last_active'] = datetime.utcnow().isoformat()
                    session.pop('login_temp_user_id', None)
                    session.pop('login_otp', None)
                    session.pop('biometric_needed', None)
                    session.pop('bio_attempts', None)
                    log_action("Login Success", "Face verification passed (Web)", user.email)
                    flash("Welcome back!", "success")
                    return jsonify({"status": "success", "message": "Match Found!", "redirect": url_for('vault.vault_dashboard')})
                else:
                    return jsonify({"status": "processing", "message": "Verifying..."})
            else:
                session['verify_history'] = []
                attempts = session.get('bio_attempts', 0) + 1
                session['bio_attempts'] = attempts
                
                # After 10 mismatching frames (approx. 4 seconds), fail with incorrect biometric error
                if attempts >= 10:
                    log_action("Login Failed", "Failed face biometric verification (mismatch limit reached)", user.email, "WARNING")
                    flash("Login failed: Biometric is incorrect.", "danger")
                    return jsonify({"status": "failed", "message": "Login failed: Biometric is incorrect.", "redirect": url_for('auth.login')})
                
                return jsonify({"status": "processing", "message": "Biometric is incorrect. Please retry..."})
                
    return jsonify({"status": "processing", "message": "Waiting..."})

@biometric_bp.route('/verify_hand_action', methods=['GET'])
def verify_hand_action():
    return redirect(url_for('biometric.camera_capture', action='verify', bio_type='hand'))

@biometric_bp.route('/verify_face_action', methods=['GET'])
def verify_face_action():
    return redirect(url_for('biometric.camera_capture', action='verify', bio_type='face'))

@biometric_bp.route('/add_hand', methods=['GET'])
@login_required
def add_hand():
    return redirect(url_for('biometric.camera_capture', action='enroll', bio_type='hand'))

@biometric_bp.route('/delete_hand', methods=['POST'])
@login_required
def delete_hand():
    user = User.query.get(session['user_id'])
    if not user.face_data:
        flash("Action denied: You must have at least one biometric (Face) set up before deleting Hand data.", "danger")
    else:
        user.hand_data = None
        db.session.commit()
        log_action("Biometric Delete", "Hand data deleted", user.email)
        flash("Hand data deleted.", "success")
    return redirect(url_for('main.profile'))

@biometric_bp.route('/add_face', methods=['GET'])
@login_required
def add_face():
    return redirect(url_for('biometric.camera_capture', action='enroll', bio_type='face'))

@biometric_bp.route('/delete_face', methods=['POST'])
@login_required
def delete_face():
    user = User.query.get(session['user_id'])
    if not user.hand_data:
        flash("Action denied: You must have at least one biometric (Hand) set up before deleting Face data.", "danger")
    else:
        user.face_data = None
        db.session.commit()
        log_action("Biometric Delete", "Face data deleted", user.email)
        flash("Face data deleted.", "success")
    return redirect(url_for('main.profile'))
