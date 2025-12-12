from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from decorators import log_function_call
import uuid
from app.db import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserUpdatePassword
from app.auth_utils import verify_token, encrypt_password, decrypt_password
from app.models.notifications import Notification
 
router = APIRouter(prefix="/users", tags=["users"])
 
@router.get("/", response_model=list[UserResponse])
@log_function_call
def get_users(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    if payload.get("role") != "Super Admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can view users")
 
    users = db.query(User).all()
    responses = []
    for u in users:
        resp = UserResponse.model_validate(u)
        resp.plain_password = decrypt_password(u.password)
        responses.append(resp)
    return responses
 
 
@router.post("/", response_model=UserResponse)
@log_function_call
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    if payload.get("role") != "Super Admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can create users")

    if db.query(User).filter(User.email_id == request.email_id).first():
        raise HTTPException(status_code=400, detail="Email already exists")
 
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
 
    # Default password
    default_password = "superadmin" if request.role == "Super Admin" else "admin"

    creator_user_id = payload.get("sub")
    creator_username = payload.get("username")
 
    new_user = User(
        user_id=uuid.uuid4(),
        username=request.username,
        email_id=request.email_id,
        role=request.role,
        password=encrypt_password(default_password),
        created_at=datetime.utcnow(),
        created_by=payload.get("username"),
    )

    #Adding user to DB
    db.add(new_user)

    notification_text = f"User {new_user.username} created by {creator_username}."

    creator_notification = Notification(
        user_id=creator_user_id,
        text=notification_text,
        timestamp=datetime.utcnow(),
        read=False
    )
    db.add(creator_notification)
    db.commit()
    db.refresh(new_user)
 
    resp = UserResponse.model_validate(new_user)
    resp.plain_password = default_password
    return resp
 
 
@router.put("/{user_id}", response_model=UserResponse)
@log_function_call
def update_user(
    user_id: str,
    request: UserUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    if payload.get("role") != "Super Admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can update users")
 
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    if payload.get("sub") == user_id:
        if request.email_id:
            user.email_id = request.email_id
        if request.role and request.role != user.role:
            raise HTTPException(status_code=400, detail="You cannot change your own role")
    else:
        if request.email_id:
            user.email_id = request.email_id
        if request.role:
            user.role = request.role
 
    db.commit()
    db.refresh(user)
 
    resp = UserResponse.model_validate(user)
    resp.plain_password = decrypt_password(user.password)
    return resp
 
@router.put("/{user_id}/password")
@log_function_call
def update_password(
    user_id: str,
    request: UserUpdatePassword,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token),
):
    if payload.get("sub") != user_id and payload.get("role") != "Super Admin":
        raise HTTPException(status_code=403, detail="Not allowed to change password for this user")
 
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    if payload.get("role") != "Super Admin":
        current_pw = decrypt_password(user.password)
        if current_pw != request.current_password:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
 
    user.password = encrypt_password(request.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
 
 
@router.delete("/{user_id}")
@log_function_call
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    if payload.get("role") != "Super Admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can delete users")
    
    creator_user_id = payload.get("sub")
    creator_username = payload.get("username")

    if creator_user_id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")

    user_to_delete = db.query(User).filter(User.user_id == user_id).first()
 
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
 
    deleted_username = user_to_delete.username

    db.delete(user_to_delete)

    notification_text = f"User {deleted_username} ({user_to_delete.role}) was deleted by {creator_username}."

    creator_notification = Notification(
        user_id=creator_user_id,
        text=notification_text,
        timestamp=datetime.utcnow(),
        read=False
    )
    db.add(creator_notification)
    db.commit()
    return {"message": "User deleted"}