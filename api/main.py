from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from datetime import timedelta
from dotenv import load_dotenv

from db import init_db, get_db, update_request_status, get_request_by_id, get_user_requests, approve_request_with_signature, create_workflow, get_workflow_by_id, get_user_workflows, trigger_workflow, get_triggered_workflow_by_id, get_user_triggered_workflows, update_triggered_workflow_status
from auth import create_access_token, get_current_user, hash_password, verify_password
from schemas import UserCreate, Token, Instruction, SignatureApprovalRequest, WorkflowCreate, WorkflowTrigger
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

# ============ WORKFLOW ENDPOINTS ============

@app.post("/api/workflows")
def create_new_workflow(workflow: WorkflowCreate, current_user: dict = Depends(get_current_user)):
    """Create a new workflow (users can create workflows)."""
    workflow_id = create_workflow(
        creator_id=current_user["id_number"],
        workflow_name=workflow.workflow_name,
        workflow_description=workflow.workflow_description or "",
        workflow_config=workflow.workflow_config
    )
    return {
        "message": "Workflow created successfully",
        "workflow_id": workflow_id,
        "creator_id": current_user["id_number"]
    }

@app.get("/api/workflows")
def list_workflows(current_user: dict = Depends(get_current_user)):
    """List all workflows created by the current user."""
    workflows = get_user_workflows(current_user["id_number"])
    return {"workflows": [dict(w) for w in workflows]}

@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: int, current_user: dict = Depends(get_current_user)):
    """Get details of a specific workflow."""
    workflow = get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")
    
    # Users can only view their own workflows
    if workflow["creator_id"] != current_user["id_number"]:
        raise HTTPException(403, "You can only view your own workflows")
    
    return dict(workflow)

@app.post("/api/workflows/{workflow_id}/trigger")
def trigger_new_workflow(workflow_id: int, current_user: dict = Depends(get_current_user)):
    """Trigger/execute a workflow."""
    workflow = get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")
    
    triggered_id = trigger_workflow(workflow_id, current_user["id_number"])
    return {
        "message": "Workflow triggered successfully",
        "triggered_id": triggered_id,
        "workflow_id": workflow_id,
        "status": "running"
    }

@app.get("/api/triggered-workflows")
def list_triggered_workflows(current_user: dict = Depends(get_current_user)):
    """List all workflow executions triggered by the current user."""
    triggered = get_user_triggered_workflows(current_user["id_number"])
    return {"triggered_workflows": [dict(t) for t in triggered]}

@app.get("/api/triggered-workflows/{triggered_id}")
def get_triggered_workflow(triggered_id: int, current_user: dict = Depends(get_current_user)):
    """Get details of a specific triggered workflow execution."""
    triggered = get_triggered_workflow_by_id(triggered_id)
    if not triggered:
        raise HTTPException(404, "Triggered workflow not found")
    
    # Users can only view their own triggered workflows
    if triggered["triggered_by"] != current_user["id_number"]:
        raise HTTPException(403, "You can only view your own triggered workflows")
    
    return dict(triggered)

@app.post("/api/triggered-workflows/{triggered_id}/complete")
def complete_triggered_workflow(triggered_id: int, current_user: dict = Depends(get_current_user)):
    """Mark a triggered workflow as completed with result."""
    triggered = get_triggered_workflow_by_id(triggered_id)
    if not triggered:
        raise HTTPException(404, "Triggered workflow not found")
    
    # Only the user who triggered it can update its status
    if triggered["triggered_by"] != current_user["id_number"]:
        raise HTTPException(403, "You can only update your own triggered workflows")
    
    success = update_triggered_workflow_status(triggered_id, "completed", "Workflow execution completed")
    if not success:
        raise HTTPException(500, "Failed to complete workflow")
    
    return {"message": "Workflow marked as completed", "triggered_id": triggered_id, "status": "completed"}

@app.post("/api/triggered-workflows/{triggered_id}/fail")
def fail_triggered_workflow(triggered_id: int, current_user: dict = Depends(get_current_user)):
    """Mark a triggered workflow as failed with error details."""
    triggered = get_triggered_workflow_by_id(triggered_id)
    if not triggered:
        raise HTTPException(404, "Triggered workflow not found")
    
    if triggered["triggered_by"] != current_user["id_number"]:
        raise HTTPException(403, "You can only update your own triggered workflows")
    
    success = update_triggered_workflow_status(triggered_id, "failed", "Workflow execution failed")
    if not success:
        raise HTTPException(500, "Failed to mark workflow as failed")
    
    return {"message": "Workflow marked as failed", "triggered_id": triggered_id, "status": "failed"}

