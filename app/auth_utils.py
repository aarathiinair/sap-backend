from datetime import datetime, timedelta
from jose import jwt, JWTError
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
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
 
 
def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Decodes the JWT and returns the payload.
    No database lookup is performed to avoid UUID conversion errors.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload # Returns the dict containing 'sub' and 'username'
    except JWTError:
        raise credentials_exception