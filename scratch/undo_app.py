import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace imports
import_str_old = """from hand_tracking import process_hand_image, verify_hand_single_image, capture_hand_data
from face_auth import process_face_image, verify_face_single_image, capture_face_data, verify_face_data as verify_face_data_live
from hand_compare import verify_hand_data"""
import_str_new = """from flask import Response, jsonify
from hand_tracking import gen_hand_capture_frames, gen_hand_verify_frames, hand_stream_state, hand_verify_state
from face_auth import gen_face_capture_frames, gen_face_verify_frames, face_stream_state, face_verify_state"""
content = content.replace(import_str_new, import_str_old)

# Replace verify_hand_action and verify_face_action and add streaming logic
verify_old = """@app.route('/biometric_verify', methods=['GET', 'POST'])
def biometric_verify():
    if 'login_temp_user_id' not in session or not session.get('biometric_needed'):
        return redirect(url_for('login'))
        
    user_id = session.get('login_temp_user_id')
    user = User.query.get(user_id)

    if request.method == 'POST':
        method = request.form.get('method')
        image_data = request.form.get('image_data')
        
        if not image_data:
            flash("No image data received.", "danger")
            return redirect(url_for('biometric_verify'))
            
        img = base64_to_image(image_data)
        if img is None:
            flash("Invalid image data.", "danger")
            return redirect(url_for('biometric_verify'))
        
        if method == 'hand' and user.hand_data:
            saved_features = json.loads(user.hand_data)
            if verify_hand_single_image(img, saved_features):
                session['user_id'] = user.id
                session['last_active'] = datetime.utcnow().isoformat()
                session.pop('login_temp_user_id', None)
                session.pop('login_otp', None)
                session.pop('biometric_needed', None)
                log_action("Login Success", "Hand verification passed", user.email)
                flash("Welcome back!", "success")
                return redirect(url_for('vault_dashboard'))
            else:
                log_action("Biometric Failed", "Hand verification failed", user.email, "WARNING")
                flash("Hand verification failed. Try again.", "danger")
        
        elif method == 'face' and user.face_data:
            saved_features = json.loads(user.face_data)
            if verify_face_single_image(img, saved_features):
                session['user_id'] = user.id
                session['last_active'] = datetime.utcnow().isoformat()
                session.pop('login_temp_user_id', None)
                session.pop('login_otp', None)
                session.pop('biometric_needed', None)
                log_action("Login Success", "Face verification passed", user.email)
                flash("Welcome back!", "success")
                return redirect(url_for('vault_dashboard'))
            else:
                log_action("Biometric Failed", "Face verification failed", user.email, "WARNING")
                flash("Face verification failed. Try again.", "danger")

    return render_template('biometric_verify.html', user=user)"""

verify_new_part = """@app.route('/biometric_verify', methods=['GET'])
def biometric_verify():
    if 'login_temp_user_id' not in session or not session.get('biometric_needed'):
        return redirect(url_for('login'))
        
    user_id = session.get('login_temp_user_id')
    user = User.query.get(user_id)

    return render_template('biometric_verify.html', user=user)

@app.route('/verify_hand_action', methods=['GET'])
def verify_hand_action():
    if 'login_temp_user_id' not in session: return redirect(url_for('login'))
    return render_template('stream_verify.html', method_type='hand', title='Verify Hand Signature', feed_url=url_for('video_feed_hand_verify'), status_url=url_for('status_hand_verify'), commit_url=url_for('commit_hand_verify'))

@app.route('/verify_face_action', methods=['GET'])
def verify_face_action():
    if 'login_temp_user_id' not in session: return redirect(url_for('login'))
    return render_template('stream_verify.html', method_type='face', title='Verify Face ID', feed_url=url_for('video_feed_face_verify'), status_url=url_for('status_face_verify'), commit_url=url_for('commit_face_verify'))

@app.route('/video_feed_hand_verify')
def video_feed_hand_verify():
    if 'login_temp_user_id' not in session: return Response("Unauthorized", 401)
    user = User.query.get(session['login_temp_user_id'])
    saved_features = json.loads(user.hand_data)
    return Response(gen_hand_verify_frames(saved_features), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status_hand_verify')
def status_hand_verify():
    return jsonify({'status': hand_verify_state['status'], 'result': hand_verify_state['result']})

@app.route('/commit_hand_verify')
def commit_hand_verify():
    if 'login_temp_user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['login_temp_user_id'])
    if hand_verify_state['status'] == 'done' and hand_verify_state['result']:
        session['user_id'] = user.id
        session['last_active'] = datetime.utcnow().isoformat()
        session.pop('login_temp_user_id', None)
        session.pop('login_otp', None)
        session.pop('biometric_needed', None)
        log_action("Login Success", "Hand verification passed via stream", user.email)
        flash("Welcome back!", "success")
        return redirect(url_for('vault_dashboard'))
    else:
        log_action("Biometric Failed", "Hand verification failed via stream", user.email, "WARNING")
        flash("Hand verification failed. Try again.", "danger")
        return redirect(url_for('biometric_verify'))

@app.route('/video_feed_face_verify')
def video_feed_face_verify():
    if 'login_temp_user_id' not in session: return Response("Unauthorized", 401)
    user = User.query.get(session['login_temp_user_id'])
    saved_features = json.loads(user.face_data)
    return Response(gen_face_verify_frames(saved_features), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status_face_verify')
def status_face_verify():
    return jsonify({'status': face_verify_state['status'], 'result': face_verify_state['result']})

@app.route('/commit_face_verify')
def commit_face_verify():
    if 'login_temp_user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['login_temp_user_id'])
    if face_verify_state['status'] == 'done' and face_verify_state['result']:
        session['user_id'] = user.id
        session['last_active'] = datetime.utcnow().isoformat()
        session.pop('login_temp_user_id', None)
        session.pop('login_otp', None)
        session.pop('biometric_needed', None)
        log_action("Login Success", "Face verification passed via stream", user.email)
        flash("Welcome back!", "success")
        return redirect(url_for('vault_dashboard'))
    else:
        log_action("Biometric Failed", "Face verification failed via stream", user.email, "WARNING")
        flash("Face verification failed. Try again.", "danger")
        return redirect(url_for('biometric_verify'))"""

content = content.replace(verify_new_part, verify_old)

add_old = """@app.route('/add_hand', methods=['GET', 'POST'])
@login_required
def add_hand():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        image_data = request.form.get('image_data')
        if not image_data:
            flash("No image data received.", "danger")
            return redirect(url_for('add_hand'))
            
        img = base64_to_image(image_data)
        if img is None:
            flash("Invalid image data.", "danger")
            return redirect(url_for('add_hand'))
            
        features = process_hand_image(img)
        if features:
            user.hand_data = json.dumps(features)
            db.session.commit()
            log_action("Biometric Add", "Hand data added", user.email)
            flash("Hand data added successfully!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Failed to extract hand features. Please ensure your hand is visible and open.", "danger")
            return redirect(url_for('add_hand'))
            
    return render_template('biometric_capture.html', title="Register Hand Print", action_url=url_for('add_hand'), method_type="hand")"""

add_new = """@app.route('/add_hand', methods=['GET'])
@login_required
def add_hand():
    return render_template('stream_capture.html', method_type='hand', title='Register Hand Print', feed_url=url_for('video_feed_hand_enroll'), status_url=url_for('status_hand_enroll'), commit_url=url_for('commit_hand_enroll'))

@app.route('/video_feed_hand_enroll')
@login_required
def video_feed_hand_enroll():
    return Response(gen_hand_capture_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status_hand_enroll')
@login_required
def status_hand_enroll():
    return jsonify({'status': hand_stream_state['status']})

@app.route('/commit_hand_enroll')
@login_required
def commit_hand_enroll():
    user = User.query.get(session['user_id'])
    if hand_stream_state['status'] == 'done' and hand_stream_state['data']:
        user.hand_data = json.dumps(hand_stream_state['data'])
        db.session.commit()
        log_action("Biometric Add", "Hand data added via stream", user.email)
        flash("Hand data added successfully!", "success")
    else:
        flash("Hand capture failed or was cancelled.", "danger")
    return redirect(url_for('profile'))"""

content = content.replace(add_new, add_old)

face_old = """@app.route('/add_face', methods=['GET', 'POST'])
@login_required
def add_face():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        image_data = request.form.get('image_data')
        if not image_data:
            flash("No image data received.", "danger")
            return redirect(url_for('add_face'))
            
        img = base64_to_image(image_data)
        if img is None:
            flash("Invalid image data.", "danger")
            return redirect(url_for('add_face'))
            
        features = process_face_image(img)
        if features:
            user.face_data = json.dumps(features)
            db.session.commit()
            log_action("Biometric Add", "Face data added", user.email)
            flash("Face data added successfully!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Failed to capture face data. Please ensure your face is clearly visible.", "danger")
            return redirect(url_for('add_face'))
            
    return render_template('biometric_capture.html', title="Register Face Print", action_url=url_for('add_face'), method_type="face")"""

face_new = """@app.route('/add_face', methods=['GET'])
@login_required
def add_face():
    return render_template('stream_capture.html', method_type='face', title='Register Face Print', feed_url=url_for('video_feed_face_enroll'), status_url=url_for('status_face_enroll'), commit_url=url_for('commit_face_enroll'))

@app.route('/video_feed_face_enroll')
@login_required
def video_feed_face_enroll():
    return Response(gen_face_capture_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status_face_enroll')
@login_required
def status_face_enroll():
    return jsonify({'status': face_stream_state['status']})

@app.route('/commit_face_enroll')
@login_required
def commit_face_enroll():
    user = User.query.get(session['user_id'])
    if face_stream_state['status'] == 'done' and face_stream_state['data']:
        user.face_data = json.dumps(face_stream_state['data'])
        db.session.commit()
        log_action("Biometric Add", "Face data added via stream", user.email)
        flash("Face data added successfully!", "success")
    else:
        flash("Face capture failed or was cancelled.", "danger")
    return redirect(url_for('profile'))"""

content = content.replace(face_new, face_old)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Undid app.py changes successfully!")
