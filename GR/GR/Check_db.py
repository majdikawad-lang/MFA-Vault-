import pickle

with open("face_db.pkl", "rb") as f:
    db = pickle.load(f)

print(f"Total Users Enrolled: {len(db)}")
for name in db.keys():
    print(f"Found User in DB: '{name}'")