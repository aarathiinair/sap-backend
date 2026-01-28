from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import Base, engine, SessionLocal
from app.routers import all_routers
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth_utils import encrypt_password
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
 
load_dotenv()

from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
 
load_dotenv()

# Create DB tables if they don’t exist
Base.metadata.create_all(bind=engine)
 
app = FastAPI(
    title="Admin Console API",
    version="1.0.0",
    description="Backend APIs for Admin Console"
)

app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET_KEY", "najkwe&7qyw7iqhi&W^Yiu2hb13jk213uy"),
    session_cookie="msal_session",
    same_site="lax",
    domain="bitzer.biz",
)


app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET_KEY", "najkwe&7qyw7iqhi&W^Yiu2hb13jk213uy"),
    session_cookie="msal_session",
    same_site="lax",
    domain="bitzer.biz",
)

# CORS config for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200",
                   "https://127.0.0.1:4200",
                   "http://localhost:443",
                   "https://127.0.0.1:443",
                   "http://localhost",
                   "http://localhost:80",
                   "https://127.0.0.1:80",
                   "https://monitoring-dev.bitzer.biz",
                   "https://monitoring-uat.bitzer.biz"],
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