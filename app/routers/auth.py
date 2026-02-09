import os
import msal
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.auth_utils import create_access_token 
from dotenv import load_dotenv
from pathlib import Path
from decorators import log_function_call

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

router = APIRouter(prefix="/auth", tags=["auth"])

# MSAL Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["User.Read"]
# REDIRECT_URI must match exactly what is registered in Azure Portal
REDIRECT_URI = f"{os.getenv('FRONTEND_URL', 'http://localhost:443')}/"

msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
)

@router.get("/login")
@log_function_call
async def login():
    """
    Step 1: Initiate Auth Flow. 
    We return the flow object to the frontend to store in sessionStorage.
    """
    flow = msal_app.initiate_auth_code_flow(SCOPE, redirect_uri=REDIRECT_URI)
    return {
        "auth_url": flow["auth_uri"],
        "flow": flow 
    }

@router.post("/exchange")
@log_function_call
async def exchange_code(payload: dict):
    flow = payload.get("flow")
    code = payload.get("code")
    state = payload.get("state") # <--- Get state from payload
    
    if not flow or not code or not state:
        raise HTTPException(status_code=400, detail="Missing auth data.")

    # Prepare the auth_response dictionary that MSAL expects
    auth_response = {
        "code": code,
        "state": state
    }
        
    # MSAL compares auth_response["state"] with flow["state"]
    result = msal_app.acquire_token_by_auth_code_flow(flow, auth_response)
    
    if "error" in result:
        print("--- MSAL EXCHANGE ERROR ---")
        print(f"Error: {result.get('error')}")
        print(f"Description: {result.get('error_description')}")
        print(f"Correlation ID: {result.get('correlation_id')}")
        print("---------------------------")
        return JSONResponse(status_code=400, content=result)

    # Extract user info
    claims = result.get("id_token_claims", {})
    username = claims.get("preferred_username") or claims.get("name")
    
    if not username:
        raise HTTPException(status_code=400, detail="Could not retrieve username from Microsoft.")

    # Create your internal JWT
    token = create_access_token(data={"sub": username, "username": username})
    
    return {"token": token, "username": username}