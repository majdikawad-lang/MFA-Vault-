from deepface import DeepFace
import os
import pickle
import re

DB_PATH = "members"
ENCODINGS_FILE = "face_db.pkl"

def extract_and_store_features():
    known_embeddings = {} # Dictionary: { "Name": [list_of_vectors] }

    for file in os.listdir(DB_PATH):
        if file.endswith((".jpg", ".png", ".jpeg")):
            # Clean name: "amman_student1.jpg" -> "amman_student"
            user_name = re.sub(r'\d+', '', os.path.splitext(file)[0]).strip('_')
            img_path = os.path.join(DB_PATH, file)
            
            try:
                
                # force 'opencv' to avoid the MediaPipe .solutions error
                results = DeepFace.represent(
                img_path=img_path, 
                model_name="Facenet", 
                detector_backend='opencv', 
                enforce_detection=True
                )
                embedding = results[0]["embedding"]
                
                if user_name not in known_embeddings:
                    known_embeddings[user_name] = []
                
                known_embeddings[user_name].append(embedding)
                print(f"Added feature {len(known_embeddings[user_name])} for: {user_name}")
            except Exception as e:
                print(f"Skipping {file}: {e}")

    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(known_embeddings, f)
    print("\nMulti-biometric database created!")

if __name__ == "__main__":
    extract_and_store_features()