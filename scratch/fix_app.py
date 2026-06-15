import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace imports back to correct old
import_str_bad = """from hand_tracking import process_hand_image, verify_hand_single_image, capture_hand_data
from face_auth import process_face_image, verify_face_single_image, capture_face_data, verify_face_data as verify_face_data_live
from hand_compare import verify_hand_data"""
import_str_correct = """from hand_tracking import capture_hand_data
from face_auth import capture_face_data, verify_face_data as verify_face_data_live
from hand_compare import verify_hand_data"""
content = content.replace(import_str_bad, import_str_correct)

bad_verify = """@app.route('/biometric_verify', methods=['GET', 'POST'])
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

correct_verify = """@app.route('/biometric_verify', methods=['GET'])
def biometric_verify():
    if 'login_temp_user_id' not in session or not session.get('biometric_needed'):
        return redirect(url_for('login'))
        
    user_id = session.get('login_temp_user_id')
    user = User.query.get(user_id)

    return render_template('biometric_verify.html', user=user)

@app.route('/verify_hand_action', methods=['GET'])
def verify_hand_action():
    if 'login_temp_user_id' not in session or not session.get('biometric_needed'):
        return redirect(url_for('login'))
    user_id = session.get('login_temp_user_id')
    user = User.query.get(user_id)
    
    if user.hand_data:
        saved_features = json.loads(user.hand_data)
        if verify_hand_data(saved_features):
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
    return redirect(url_for('biometric_verify'))

@app.route('/verify_face_action', methods=['GET'])
def verify_face_action():
    if 'login_temp_user_id' not in session or not session.get('biometric_needed'):
        return redirect(url_for('login'))
    user_id = session.get('login_temp_user_id')
    user = User.query.get(user_id)
    
    if user.face_data:
        saved_features = json.loads(user.face_data)
        if verify_face_data_live(saved_features):
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
    return redirect(url_for('biometric_verify'))"""
content = content.replace(bad_verify, correct_verify)

bad_add_hand = """@app.route('/add_hand', methods=['GET', 'POST'])
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

correct_add_hand = """@app.route('/add_hand', methods=['GET'])
@login_required
def add_hand():
    user = User.query.get(session['user_id'])
    features = capture_hand_data()
    if features:
        user.hand_data = json.dumps(features)
        db.session.commit()
        log_action("Biometric Add", "Hand data added", user.email)
        flash("Hand data added successfully!", "success")
    else:
        flash("Failed to extract hand features. Please ensure your hand is visible and open.", "danger")
    return redirect(url_for('profile'))"""
content = content.replace(bad_add_hand, correct_add_hand)

bad_add_face = """@app.route('/add_face', methods=['GET', 'POST'])
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

correct_add_face = """@app.route('/add_face', methods=['GET'])
@login_required
def add_face():
    user = User.query.get(session['user_id'])
    features = capture_face_data()
    if features:
        user.face_data = json.dumps(features)
        db.session.commit()
        log_action("Biometric Add", "Face data added", user.email)
        flash("Face data added successfully!", "success")
    else:
        flash("Failed to capture face data. Please ensure your face is clearly visible.", "danger")
    return redirect(url_for('profile'))"""
content = content.replace(bad_add_face, correct_add_face)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Restored app.py successfully to previous exact state!")
