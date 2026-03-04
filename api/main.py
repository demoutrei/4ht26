# from fastapi import FastAPI
# from typing import Any


# app: FastAPI = FastAPI()


# @app.get("/api/workflows/{workflow_id}")
# def workflow_display(workflow_id: int) -> dict[str, Any]:
#   return {
#     "text": "Hello, World!"
#   }


from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from datetime import timedelta
from dotenv import load_dotenv

from db import init_db, get_db, update_request_status, get_request_by_id, get_user_requests, approve_request_with_signature
from auth import create_access_token, get_current_user, hash_password, verify_password
from schemas import UserCreate, Token, Instruction, SignatureApprovalRequest
from routers.agent1 import router as agent_router

load_dotenv()
app = FastAPI(title="University Admin AI Agent")

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(agent_router, prefix="/api", tags=["Agent"])

@app.post("/signup")
def signup(user: UserCreate):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id_number FROM users WHERE id_number = ?", (user.id_number,))
        if c.fetchone():
            raise HTTPException(400, "ID number already taken")
        
        hashed = hash_password(user.password)
        c.execute("""
            INSERT INTO users (id_number, hashed_password, full_name, role)
            VALUES (?, ?, ?, ?)
        """, (user.id_number, hashed, user.full_name, user.role))
        conn.commit()
    
    return {"message": "Account created", "id_number": user.id_number, "role": user.role}

@app.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id_number = ?", (form_data.username,))
        user = c.fetchone()
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(401, "Incorrect ID number or password")
    
    token = create_access_token(
        data={"sub": user["id_number"], "role": user["role"]},
        expires_delta=timedelta(hours=24)
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "student":
        features = [
            "Letters: Academic Leave, Requests, Proposals",
            "Events: Bookings, Renting, Campus Activities, Field Trips"
        ]
    elif current_user["role"] == "faculty":
        features = [
            "Letters: Academic Leave, Requests, Proposals",
            "Events: Bookings, Renting, Campus Activities, Field Trips",
            "Memorandum / Notice Creation and Delivery"
        ]
    else:
        raise HTTPException(403, "Invalid role")

    return {
        "welcome": f"Hello {current_user['id_number']} ({current_user['role']})",
        "available_features": features
    }

@app.get("/api/requests/{request_id}")
def get_request(request_id: int, current_user: dict = Depends(get_current_user)):
    """Fetch a specific agent request."""
    request = get_request_by_id(request_id)
    if not request:
        raise HTTPException(404, "Request not found")
    
    # Users can only view their own requests (faculty can view all)
    if current_user["role"] != "faculty" and request["requester_id"] != current_user["id_number"]:
        raise HTTPException(403, "You don't have permission to view this request")
    
    return dict(request)

@app.get("/api/requests")
def list_user_requests(current_user: dict = Depends(get_current_user)):
    """List all requests for the current user."""
    requests = get_user_requests(current_user["id_number"])
    return {"requests": [dict(r) for r in requests]}

@app.post("/api/requests/{request_id}/approve")
def approve_request(request_id: int, approval: SignatureApprovalRequest, current_user: dict = Depends(get_current_user)):
    """Approve a draft request with e-signature (faculty only)."""
    if current_user["role"] != "faculty":
        raise HTTPException(403, "Only faculty can approve requests")
    
    request = get_request_by_id(request_id)
    if not request:
        raise HTTPException(404, "Request not found")
    
    if request["status"] != "draft":
        raise HTTPException(400, f"Cannot approve request with status '{request['status']}'")
    
    if not approval.signature or approval.signature.strip() == "":
        raise HTTPException(400, "E-signature is required for approval")
    
    success = approve_request_with_signature(request_id, current_user["id_number"], approval.signature)
    if not success:
        raise HTTPException(500, "Failed to approve request")
    
    return {
        "message": "Request approved with e-signature",
        "request_id": request_id,
        "new_status": "approved",
        "signed_by": current_user["id_number"]
    }

@app.post("/api/requests/{request_id}/reject")
def reject_request(request_id: int, current_user: dict = Depends(get_current_user)):
    """Reject a draft request (faculty only)."""
    if current_user["role"] != "faculty":
        raise HTTPException(403, "Only faculty can reject requests")
    
    request = get_request_by_id(request_id)
    if not request:
        raise HTTPException(404, "Request not found")
    
    if request["status"] != "draft":
        raise HTTPException(400, f"Cannot reject request with status '{request['status']}'")
    
    success = update_request_status(request_id, "rejected")
    if not success:
        raise HTTPException(500, "Failed to reject request")
    
    return {"message": "Request rejected", "request_id": request_id, "new_status": "rejected"}

@app.post("/api/requests/{request_id}/send")
def send_request(request_id: int, current_user: dict = Depends(get_current_user)):
    """Send an approved request (faculty only)."""
    if current_user["role"] != "faculty":
        raise HTTPException(403, "Only faculty can send requests")
    
    request = get_request_by_id(request_id)
    if not request:
        raise HTTPException(404, "Request not found")
    
    if request["status"] != "approved":
        raise HTTPException(400, f"Can only send approved requests. Current status: '{request['status']}'")
    
    success = update_request_status(request_id, "sent")
    if not success:
        raise HTTPException(500, "Failed to send request")
    
    return {"message": "Request sent successfully", "request_id": request_id, "new_status": "sent"}

@app.post("/api/requests/{request_id}/regenerate")
def regenerate_request(request_id: int, current_user: dict = Depends(get_current_user)):
    """Regenerate a rejected request back to draft status (requestor only)."""
    request = get_request_by_id(request_id)
    if not request:
        raise HTTPException(404, "Request not found")
    
    # Only the original requester can regenerate their request
    if request["requester_id"] != current_user["id_number"]:
        raise HTTPException(403, "You can only regenerate your own requests")
    
    if request["status"] != "rejected":
        raise HTTPException(400, f"Can only regenerate rejected requests. Current status: '{request['status']}'")
    
    success = update_request_status(request_id, "draft")
    if not success:
        raise HTTPException(500, "Failed to regenerate request")
    
    return {"message": "Request regenerated. Ready for resubmission.", "request_id": request_id, "new_status": "draft"}
