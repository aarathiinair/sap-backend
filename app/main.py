from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import Base, engine, SessionLocal
from app.routers import all_routers
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth_utils import encrypt_password
 
# Create DB tables if they don’t exist
Base.metadata.create_all(bind=engine)
 
app = FastAPI(
    title="Admin Console API",
    version="1.0.0",
    description="Backend APIs for Admin Console"
)
 
# CORS config for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200",
                   "https://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Register all routers
for router in all_routers:
    app.include_router(router)

# Seed users at startup
@app.on_event("startup")
def seed_users():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                user_id=uuid.uuid4(),
                username="admin",
                email_id="admin@example.com",
                password=encrypt_password("admin"),
                role="Admin",
                created_at=datetime.utcnow(),
                created_by="system"
            )
            db.add(admin)
 
        if not db.query(User).filter(User.username == "superadmin").first():
            super_admin = User(
                user_id=uuid.uuid4(),
                username="superadmin",
                email_id="superadmin@example.com",
                password=encrypt_password("superadmin"),
                role="Super Admin",
                created_at=datetime.utcnow(),
                created_by="system"
            )
            db.add(super_admin)
 
        db.commit()
    finally:
        db.close()