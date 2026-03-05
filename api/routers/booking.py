# routers/booking.py
# Room booking API endpoints
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from api.booking_scheduler import booking_scheduler
from api.auth import get_current_user

router = APIRouter(prefix="/bookings", tags=["Room Bookings"])

class RoomCreate(BaseModel):
    room_name: str
    room_type: str
    capacity: int
    location: str

class BookingCreate(BaseModel):
    room_id: int
    booking_title: str
    start_datetime: datetime
    end_datetime: datetime

class BookingAdjust(BaseModel):
    new_start_datetime: datetime
    new_end_datetime: datetime
    reason: Optional[str] = None

class BookingApproval(BaseModel):
    approved: bool
    reason: Optional[str] = None

@router.post("/rooms/")
def create_room(room: RoomCreate, current_user=Depends(get_current_user)):
    """Create a new room (admin only)."""
    if current_user.get("role") != "faculty":
        raise HTTPException(403, "Only faculty can create rooms")
    
    room_id = booking_scheduler.create_room(
        room.room_name,
        room.room_type,
        room.capacity,
        room.location
    )
    
    return {
        "status": "success",
        "message": "Room created",
        "room_id": room_id
    }

@router.get("/rooms/")
def get_rooms():
    """Get all available rooms."""
    rooms = booking_scheduler.get_all_rooms()
    return {"rooms": rooms}

@router.post("/")
def book_room(booking: BookingCreate, current_user=Depends(get_current_user)):
    """Create a new room booking (pending approval)."""
    result = booking_scheduler.book_room(
        booking.room_id,
        current_user["id_number"],
        booking.booking_title,
        booking.start_datetime,
        booking.end_datetime
    )
    
    if result["status"] == "conflict":
        raise HTTPException(
            409,
            f"Time slot conflict: {result['message']}"
        )
    
    return result

@router.get("/my-bookings/")
def get_my_bookings(current_user=Depends(get_current_user)):
    """Get all bookings for the current user."""
    bookings = booking_scheduler.get_user_bookings(current_user["id_number"])
    return {"bookings": bookings}

@router.get("/pending-approvals/")
def get_pending_approvals(current_user=Depends(get_current_user)):
    """Get all pending booking approvals (faculty only)."""
    if current_user.get("role") != "faculty":
        raise HTTPException(403, "Only faculty can approve bookings")
    
    bookings = booking_scheduler.get_pending_approvals()
    return {"pending_bookings": bookings}

@router.post("/{booking_id}/approve")
def approve_booking(booking_id: int, current_user=Depends(get_current_user)):
    """Approve a pending booking (faculty only)."""
    if current_user.get("role") != "faculty":
        raise HTTPException(403, "Only faculty can approve bookings")
    
    success = booking_scheduler.approve_booking(booking_id, current_user["id_number"])
    
    if not success:
        raise HTTPException(404, "Booking not found")
    
    return {
        "status": "success",
        "message": "Booking approved",
        "booking_id": booking_id
    }

@router.post("/{booking_id}/reject")
def reject_booking(booking_id: int, rejection: BookingApproval, current_user=Depends(get_current_user)):
    """Reject a pending booking (faculty only)."""
    if current_user.get("role") != "faculty":
        raise HTTPException(403, "Only faculty can reject bookings")
    
    success = booking_scheduler.reject_booking(booking_id, rejection.reason)
    
    if not success:
        raise HTTPException(404, "Booking not found")
    
    return {
        "status": "success",
        "message": "Booking rejected",
        "booking_id": booking_id
    }

@router.put("/{booking_id}/adjust")
def adjust_booking(booking_id: int, adjustment: BookingAdjust, current_user=Depends(get_current_user)):
    """Adjust booking time (for approved bookings)."""
    result = booking_scheduler.adjust_booking_time(
        booking_id,
        adjustment.new_start_datetime,
        adjustment.new_end_datetime,
        adjustment.reason
    )
    
    if result["status"] == "error":
        raise HTTPException(400, result["message"])
    
    if result["status"] == "conflict":
        raise HTTPException(409, result["message"])
    
    return result

@router.get("/room/{room_id}/schedule/")
def get_room_schedule(room_id: int, 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None):
    """Get the schedule for a specific room."""
    bookings = booking_scheduler.get_bookings_by_room(room_id, start_date, end_date)
    return {
        "room_id": room_id,
        "bookings": bookings
    }
