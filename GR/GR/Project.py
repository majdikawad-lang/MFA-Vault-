import os
import logging
import absl.logging

logging.getLogger('mediapipe').setLevel(logging.ERROR)
absl.logging.set_verbosity(absl.logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Setup the Landmarker settings
base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    running_mode=vision.RunningMode.VIDEO)

# 2. Initialize the Landmarker
detector = vision.FaceLandmarker.create_from_options(options)

# 3. Open Webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    # Convert BGR to RGB
    rgb_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Get the timestamp for the current frame
    timestamp = int(cap.get(cv2.CAP_PROP_POS_MSEC))
    
    # Detect landmarks
    result = detector.detect_for_video(rgb_frame, timestamp)

    # Draw the results (Simple dots for now)
    if result.face_landmarks:
        for landmarks in result.face_landmarks:
            for landmark in landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

    cv2.imshow('Face Landmarks - Modern API', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()