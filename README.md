# 🔐 MFA Vault

### *Multi-Factor Authentication & Secure Data Vault System*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/MediaPipe-Biometrics-FF6F00?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Security-AES%20Encrypted-red?style=for-the-badge"/>
</p>

<p align="center">
  <i>🛡️ Three layers of authentication. One impenetrable vault. Secured by AI-powered biometrics and military-grade encryption.</i>
</p>

-----

## 📋 Project Overview & Abstract

**MFA Vault** is an advanced, graduation-level security system that redefines digital authentication by implementing a **three-tier Multi-Factor Authentication (MFA)** pipeline — combining traditional credential verification, time-based one-time passwords, and AI-powered biometric recognition — all guarding access to an **AES-encrypted personal data vault**.

Modern cybersecurity threats have rendered single-factor authentication obsolete. Password breaches, phishing, and credential stuffing attacks compromise millions of accounts daily. MFA Vault addresses this critical vulnerability by requiring users to pass **three independent authentication layers** before gaining access to their encrypted vault — ensuring that even if one factor is compromised, the system remains secure.

This project demonstrates a production-grade security architecture combining **classical cryptography**, **real-time computer vision**, and **modern web development** — representing a comprehensive implementation of Zero-Trust Authentication principles.

-----

## 🏗️ System Architecture & Authentication Flow

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│   HTML5 + CSS3 + Vanilla JS + Jinja2 Templates                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                    FLASK APPLICATION SERVER                      │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │   Auth      │  │   OTP        │  │   Biometric Engine     │  │
│  │   Module    │  │   Module     │  │   (CV + MediaPipe)     │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬─────────────┘  │
│         │                │                      │                │
│  ┌──────▼────────────────▼──────────────────────▼─────────────┐  │
│  │                  Security Middleware                        │  │
│  │          (Flask-Bcrypt + Cryptography Library)             │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼──────────────────────────────────┐  │
│  │              Secure Vault Engine (AES Encryption)           │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└───────────────────────────  │  ────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│               SQLite Database (Flask-SQLAlchemy ORM)            │
│         users | otp_tokens | vault_items | biometric_data       │
└─────────────────────────────────────────────────────────────────┘
```

-----

### 🔄 Three-Tier Authentication Flow

```
User Login Attempt
       │
       ▼
┌─────────────────────┐
│  TIER 1: Password   │  ──── Bcrypt Hash Verification
│  Authentication     │        against stored hash
└──────────┬──────────┘
           │ ✅ Pass
           ▼
┌─────────────────────┐
│  TIER 2: OTP        │  ──── Time-based One-Time Password
│  Verification       │        (6-digit, 30-second window)
└──────────┬──────────┘
           │ ✅ Pass
           ▼
┌─────────────────────┐
│  TIER 3: Biometric  │  ──── Face Recognition (MediaPipe)
│  Authentication     │        + Hand Gesture Confirmation
└──────────┬──────────┘
           │ ✅ Pass
           ▼
┌─────────────────────┐
│  🔓 VAULT ACCESS    │  ──── AES-Encrypted personal vault
│  GRANTED            │        decrypted and rendered
└─────────────────────┘
```

> ❌ **Failure at any tier** resets the entire authentication process and logs the attempt.

-----

## ✨ Key Features

### 🔑 Authentication Tiers

|Tier |Method    |Technology        |Description                                               |
|-----|----------|------------------|----------------------------------------------------------|
|**1**|Password  |Flask-Bcrypt      |Adaptive bcrypt hashing with configurable cost factor     |
|**2**|OTP       |TOTP Algorithm    |Time-based 6-digit one-time password with 30s expiry      |
|**3**|Biometrics|MediaPipe + OpenCV|Real-time face recognition and hand gesture liveness check|

-----

### 🧬 Biometric Integration

#### Face Recognition

- **MediaPipe Face Mesh** generates a **468-point 3D facial landmark map** from the webcam feed
- Landmark vectors are normalized and compared against the enrolled facial embedding stored during registration
- A **cosine similarity threshold** determines authentication success

```python
# Simplified face authentication logic
def authenticate_face(live_landmarks, stored_embedding, threshold=0.92):
    live_vector = normalize_landmarks(live_landmarks)
    similarity = cosine_similarity(live_vector, stored_embedding)
    return similarity >= threshold
```

#### Hand Gesture Liveness Check

- **MediaPipe Hands** tracks **21 hand landmarks** in real time
- User must perform a predefined gesture (e.g., open palm or specific finger configuration) to prove liveness and prevent spoofing via photos
- Gesture recognition uses landmark angle calculations across finger joints

-----

### 🏛️ Secure Data Vault

Once all three authentication tiers are cleared, the user gains access to their personal encrypted vault:

- 📄 **Encrypted Text Notes** — Sensitive notes stored with AES encryption
- 🔑 **Password Manager** — Credentials stored encrypted, revealed only inside the vault
- 📁 **Encrypted File Storage** — Upload and retrieve files with per-file encryption keys
- 🔒 **Vault Lock** — Vault auto-locks after configurable inactivity timeout

-----

## 🛠️ Technology Stack

|Technology            |Version |Role                                            |
|----------------------|--------|------------------------------------------------|
|**Python**            |3.9+    |Core application language                       |
|**Flask**             |3.0.0   |Web framework, routing, session management      |
|**Werkzeug**          |Latest  |WSGI utilities, request/response handling       |
|**Flask-SQLAlchemy**  |Latest  |ORM for database modeling and queries           |
|**SQLite**            |Built-in|Lightweight relational database                 |
|**Flask-Bcrypt**      |Latest  |Adaptive password hashing (bcrypt algorithm)    |
|**cryptography**      |Latest  |AES encryption for vault items and files        |
|**OpenCV**            |4.8+    |Webcam capture and image preprocessing          |
|**MediaPipe**         |Latest  |Face Mesh and Hand Landmark detection           |
|**NumPy**             |Latest  |Landmark vector math and similarity calculations|
|**HTML5 / CSS3**      |—       |Frontend structure and styling                  |
|**Vanilla JavaScript**|ES6+    |Webcam access, async API calls, UI interactions |
|**Jinja2**            |Built-in|Server-side HTML templating                     |

-----

## 🔒 Security Measures & Encryption Strategy

### Password Security

```
User Password
     │
     ▼
bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
     │
     ▼
Stored Hash (never the raw password)
```

- **bcrypt** with **12 cost rounds** — computationally expensive by design to resist brute-force attacks
- Raw passwords are **never stored or logged** at any point

-----

### OTP Security

- One-Time Passwords expire after **30 seconds**
- Each OTP is **single-use** — invalidated immediately after verification
- Tokens are stored as **hashed values** in the database

-----

### Biometric Security

- Facial embeddings are stored as **normalized mathematical vectors**, not raw images
- No biometric images are persisted — only the derived numerical representation
- Hand gesture liveness check prevents **photo spoofing attacks**

-----

### Vault Encryption Strategy

```python
from cryptography.fernet import Fernet

# Key generation (per-user, stored securely)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypting vault item
encrypted_data = cipher.encrypt(plaintext.encode())

# Decrypting vault item (only after full MFA)
decrypted_data = cipher.decrypt(encrypted_data).decode()
```

- Each user has a **unique encryption key** derived from their credentials
- Vault items are encrypted **at rest** — unreadable even if the database is compromised
- Keys are **never stored in plaintext** — derived and discarded per session

-----

### Defense-in-Depth Summary

|Threat         |Mitigation                         |
|---------------|-----------------------------------|
|Password breach|bcrypt hashing (12 rounds)         |
|Stolen session |OTP second factor + session timeout|
|Photo spoofing |Hand gesture liveness detection    |
|Database theft |AES-encrypted vault items          |
|Brute force    |Rate limiting + bcrypt cost factor |
|Replay attacks |Time-based OTP (30s window)        |

-----

## 📁 Project Structure

```
mfa-vault/
│
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # SQLAlchemy database models
│   ├── auth/
│   │   ├── routes.py            # Login, register, logout endpoints
│   │   ├── otp.py               # OTP generation and verification
│   │   └── biometric.py        # Face + hand gesture authentication
│   ├── vault/
│   │   ├── routes.py            # Vault CRUD endpoints
│   │   └── encryption.py       # AES encrypt/decrypt logic
│   └── static/
│       ├── css/styles.css       # Frontend styling
│       └── js/
│           ├── camera.js        # Webcam capture pipeline
│           └── gesture.js       # Hand gesture recognition
│
├── templates/
│   ├── auth/
│   │   ├── login.html           # Tier 1: Password form
│   │   ├── otp.html             # Tier 2: OTP input
│   │   └── biometric.html      # Tier 3: Camera authentication
│   └── vault/
│       └── dashboard.html      # Main vault interface
│
├── instance/
│   └── vault.db                 # SQLite database (auto-created)
│
├── config.py                    # App configuration and secrets
├── requirements.txt             # Python dependencies
└── run.py                       # Application entry point
```

-----

## ⚙️ Prerequisites & Installation

### Requirements

- Python **3.9+**
- Webcam (for biometric authentication)
- Modern browser with **camera permissions** enabled

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/mfa-vault.git
cd mfa-vault
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt`**

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Bcrypt==1.0.1
cryptography==41.0.5
opencv-python==4.8.1.78
mediapipe==0.10.7
numpy==1.24.4
Werkzeug==3.0.1
```

### 4. Initialize the Database

```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

### 5. Run the Application

```bash
python run.py
```

Open your browser at:

```
http://localhost:5000
```

-----

## 🗄️ Database Schema

```sql
-- User accounts
CREATE TABLE users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    face_embedding TEXT,          -- Stored as JSON vector
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OTP tokens
CREATE TABLE otp_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used       BOOLEAN DEFAULT FALSE
);

-- Encrypted vault items
CREATE TABLE vault_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(id),
    item_type      VARCHAR(20),   -- 'note', 'password', 'file'
    title          VARCHAR(255),
    encrypted_data TEXT NOT NULL, -- AES encrypted content
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

-----

## 🔮 Conclusion & Future Enhancements

### Conclusion

MFA Vault demonstrates that robust, multi-layered security is achievable within a lightweight Python web stack. By combining **three independent authentication factors** — knowledge (password), possession (OTP), and inherence (biometrics) — with **AES-encrypted vault storage**, the system provides a comprehensive Zero-Trust security model suitable for protecting sensitive personal and organizational data.

### Future Enhancements

- [ ] 🔑 **FIDO2 / WebAuthn Support** — Hardware security key integration
- [ ] 📱 **Mobile Authenticator App** — QR-code based TOTP enrollment
- [ ] 🌐 **OAuth2 / SSO Integration** — Enterprise identity provider support
- [ ] 🧠 **Behavioral Biometrics** — Typing pattern and mouse movement analysis
- [ ] ☁️ **Cloud Vault Sync** — End-to-end encrypted cross-device synchronization
- [ ] 📊 **Security Audit Logs** — Tamper-proof authentication event logging
- [ ] 🐳 **Docker Containerization** — One-command deployment pipeline
- [ ] 🔐 **Zero-Knowledge Architecture** — Server never sees decrypted vault contents

-----

## 👨‍💻 Author

**Majdi Awad**
*AI-Powered Web Developer | Computer Science Graduate — Al-Zaytoonah University of Jordan*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/majdi-awad)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/majdi-awad)

-----

## ⚠️ Security Disclaimer

> This project is developed for **educational and academic purposes** as a graduation project. For production deployment handling real sensitive data, a formal security audit, penetration testing, and compliance review (GDPR, HIPAA, etc.) are strongly recommended.

-----

<p align="center">
  <i>Built with 🔐 — because your data deserves more than a single password.</i>
</p>
