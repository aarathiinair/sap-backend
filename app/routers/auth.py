from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from decorators import log_function_call
 
from app.db import get_db
from app.models.user import User
from app.auth_utils import create_access_token, decrypt_password
from app.schemas.auth import LoginResponse
from app.schemas.user import UserResponse
 
router = APIRouter(prefix="/auth", tags=["auth"])
 
ACCESS_TOKEN_EXPIRE_MINUTES = 60

@router.post("/login", response_model=LoginResponse)
@log_function_call
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    try:
        stored_password = decrypt_password(user.password)
    except Exception:
        raise HTTPException(status_code=500, detail="Password decryption failed")
    
    if form_data.password != stored_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
 
    # generate JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
 
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }