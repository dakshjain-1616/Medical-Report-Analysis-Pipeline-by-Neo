import os
from typing import Optional
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging
import json

# Monkeypatch passlib for bcrypt 4.0+ compatibility in Python 3.12
import bcrypt
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type('about', (object,), {'__version__': bcrypt.__version__})

# HIPAA Compliance Constants
SECRET_KEY = os.environ.get("HIPAA_SECRET_KEY", "7b6f634f6d3957545366436e59325453")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
FERNET_KEY = os.environ.get("FERNET_KEY", Fernet.generate_key().decode())

# Security Contexts
# Use pbkdf2_sha256 as a more stable alternative on this environment if bcrypt fails
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
cipher_suite = Fernet(FERNET_KEY.encode())

# Structured Audit Logging (PHI Masking)
logger = logging.getLogger("hipaa_audit")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("/root/MedicalReportAnalysis/logs/audit.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def mask_phi(data: str) -> str:
    """Mask potential PHI in strings for audit logs."""
    # Basic masking for sensitive fields if they appear in logs
    phi_keywords = ['name', 'dob', 'ssn', 'phone', 'address', 'email']
    if any(key in data.lower() for key in phi_keywords):
        return "***REDACTED_PHI***"
    return data

def log_audit_event(user_id: str, action: str, resource_id: str, status: str):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": action,
        "resource_id": resource_id,
        "status": status
    }
    logger.info(json.dumps(log_entry))

class EncryptionHandler:
    @staticmethod
    def encrypt_data(data: bytes) -> bytes:
        return cipher_suite.encrypt(data)

    @staticmethod
    def decrypt_data(token: bytes) -> bytes:
        return cipher_suite.decrypt(token)

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt