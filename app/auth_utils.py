from datetime import datetime, timedelta
from jose import jwt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
 
from app.db import get_db
from app.models.user import User
 

load_dotenv()

# JWT Config
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
 
# Encryption Config (symmetric, Fernet)
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    FERNET_KEY = Fernet.generate_key().decode()
    print(f"[auth_utils] Generated new FERNET_KEY: {FERNET_KEY}")

# FERNET_KEY = "MzY4uPL6WUvOk1n3XgFP0xVq9WZ39S1zIEnK2nbEWCQ="
fernet = Fernet(FERNET_KEY.encode())
 
def encrypt_password(password: str) -> str:
    """Encrypt plain password for storage"""
    return fernet.encrypt(password.encode()).decode()
 
 
def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password from DB back to plain text"""
    return fernet.decrypt(encrypted_password.encode()).decode()

# JWT Token Management
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
 
 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
 
 
def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decode JWT and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
 
    # Ensure user still exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
 
    return payload