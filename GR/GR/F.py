import os
import cv2
import pickle
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from deepface import DeepFace
import absl.logging
import numpy as np

# 1. Silence the logs for a clean presentation
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
absl.logging.set_verbosity(absl.logging.ERROR)

# 2. Load the Multi-Biometric Database 
try:
    with open("face_db.pkl", "rb") as f:
        known_faces = pickle.load(f)
    print("Database loaded successfully!")
except FileNotFoundError:
    print("Error: face_db.pkl not found. Please run enroll.py first.")
    known_faces = {}

# 3. Setup Modern MediaPipe Tasks API
base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=False,
    running_mode=vision.RunningMode.VIDEO)
detector = vision.FaceLandmarker.create_from_options(options)

# 4. Start Webcam
cap = cv2.VideoCapture(0)
current_name = "Unknown"
counter = 0 # Run recognition every 20 frames

recognition_history = []

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    
    # --- IMPLEMENT FACE RECOGNITION (DIAGNOSTIC MODE) ---
    if counter % 20 == 0 and len(known_faces) > 0:
        try:
            # Get live embedding using Facenet
        
            results = DeepFace.represent(
            img_path=frame, 
            model_name="Facenet", 
            enforce_detection=False, 
            detector_backend='opencv'
                                        )
            if results:
                live_embedding = results[0]["embedding"]
                
                best_match = "Unknown"
                min_dist = 1.0 
                
                print(f"\n--- Frame {counter} ---") # Space out the logs
                
                for name, embedding_list in known_faces.items():
                    for stored_embedding in embedding_list:
                        # Standard Cosine Similarity math: 1 - (dot_product / (norm_a * norm_b))
                        a = np.array(live_embedding)
                        b = np.array(stored_embedding)
                        dist = 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                        
                        # Diagnostic: Print the distance
                        print(f"Distance to {name}: {dist:.3f}")
                        
                        if dist < 0.38 and dist < min_dist:
                            min_dist = dist
                            best_match = name
                            recognition_history.append(best_match)
                            if len(recognition_history) > 5:
                                recognition_history.pop(0)
                                if len(recognition_history) == 5 and len(set(recognition_history)) == 1:
                                    current_name = recognition_history[0]
                
                
        except Exception as e:
            # Print the exact error instead of silently passing
            print(f"DeepFace failed on this frame: {e}")

        except Exception:
            pass # Skip if face isn't clear enough for DeepFace

    # --- FACE LANDMARKS (Modern API) ---
    rgb_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    timestamp = int(cap.get(cv2.CAP_PROP_POS_MSEC))
    
    # Ensure timestamp is strictly increasing
    if timestamp <= 0: timestamp = counter + 1 
    
    result = detector.detect_for_video(rgb_frame, timestamp)

    # Draw the green landmark dots
    if result.face_landmarks:
        for landmarks in result.face_landmarks:
            for landmark in landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

    # Display results
    color = (0, 255, 0) if current_name != "Unknown" else (0, 0, 255)
    cv2.putText(frame, f"Identity: {current_name}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    
    cv2.imshow('Graduation Project: Face OTP Biometrics', frame)
    counter += 1
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()