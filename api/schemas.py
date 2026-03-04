# schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal

class UserCreate(BaseModel):
    id_number: str
    password: str
    full_name: str
    role: Literal["student", "faculty"]

class Token(BaseModel):
    access_token: str
    token_type: str

class Instruction(BaseModel):
    text: str

# Future endpoints (not active yet)
class LeaveRequestCreate(BaseModel):
    leave_type: Literal["sick", "vacation", "study", "maternity", "others"]
    start_date: datetime
    end_date: datetime
    reason: str = Field(..., min_length=10)

class MemoCreate(BaseModel):
    title: str = Field(..., min_length=5)
    body: str = Field(..., min_length=20)
    recipients: List[str]

class BookingCreate(BaseModel):
    facility_type: Literal["room", "equipment", "vehicle", "venue"]
    facility_name: str
    start_datetime: datetime
    end_datetime: datetime
    purpose: str = Field(..., min_length=10)

class RequestOut(BaseModel):
    id: int
    request_type: Literal["leave", "memo", "booking"]
    requester_id: str
    title_or_subject: str
    status: str
    created_at: datetime
    pdf_path: Optional[str] = None

class ApprovalRequest(BaseModel):
    decision: Literal["approve", "reject"]
    comment: Optional[str] = None

class SignatureApprovalRequest(BaseModel):
    signature: str = Field(..., min_length=1, description="E-signature data (base64, text, or signature code)")
