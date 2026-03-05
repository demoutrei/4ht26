# BOOKING_SYSTEM_DOCUMENTATION.md

# Room Booking & Automated Scheduling System

## Overview
This system provides automated room booking, conflict detection, and schedule management for university spaces (Gymnasium, Open Court, Moot Court, AV Room, etc.). It includes a background scheduler that automatically manages booking approvals and cleanup.

## Features

### 1. **Room Management**
- Create and manage university rooms with details (capacity, location, type)
- Track room availability status
- View all available rooms

### 2. **Booking System**
- Students/Faculty can request room bookings with specific date/time slots
- Automatic conflict detection prevents double-bookings
- Pending approval workflow for faculty oversight
- Multi-status tracking: `pending` → `approved` → `confirmed` → `active` → `completed`

### 3. **Automated Scheduling**
- **Auto-Confirmation**: Bookings automatically transition from "confirmed" to "active" within 24 hours of event start time (runs hourly)
- **Auto-Cleanup**: Completed bookings are marked as such every 30 minutes
- **Conflict Management**: Time slot conflicts logged with resolution actions
- **Schedule Adjustments**: Approved bookings can be rescheduled with conflict checking

### 4. **Approval Workflow**
- Faculty-only approval rights
- Track who approved each booking and when
- Reject bookings with optional reason logging

## Database Schema

### `rooms`
```sql
room_id (PK)
room_name (UNIQUE)
room_type
capacity
location
is_available (default: 1)
created_at
```

### `bookings`
```sql
booking_id (PK)
room_id (FK)
user_id (FK)
booking_title
start_datetime
end_datetime
status (pending, confirmed, active, completed, cancelled)
approval_status (pending, approved, rejected)
approved_by (user_id of faculty approver)
approved_at
created_at
updated_at
```

### `booking_conflicts`
```sql
conflict_id (PK)
booking_id (FK)
conflicting_booking_id (FK)
conflict_type
resolution_action
resolved_at
created_at
```

### `schedule_adjustments`
```sql
adjustment_id (PK)
booking_id (FK)
original_start
original_end
new_start
new_end
reason
approved
created_at
```

## API Endpoints

### Room Management
- `POST /api/bookings/rooms/` - Create a new room (faculty only)
- `GET /api/bookings/rooms/` - List all available rooms

### Booking Operations
- `POST /api/bookings/` - Create a new booking request
  ```json
  {
    "room_id": 1,
    "booking_title": "Physics Lab Session",
    "start_datetime": "2026-03-10T10:00:00",
    "end_datetime": "2026-03-10T12:00:00"
  }
  ```

- `GET /api/bookings/my-bookings/` - View your bookings
- `GET /api/bookings/room/{room_id}/schedule/` - View schedule for specific room
- `GET /api/bookings/pending-approvals/` - View pending approvals (faculty only)

### Approval Workflow
- `POST /api/bookings/{booking_id}/approve` - Approve a booking (faculty only)
- `POST /api/bookings/{booking_id}/reject` - Reject a booking (faculty only)
  ```json
  {
    "approved": false,
    "reason": "Room already reserved for another event"
  }
  ```

### Schedule Adjustments
- `PUT /api/bookings/{booking_id}/adjust` - Adjust booking time
  ```json
  {
    "new_start_datetime": "2026-03-10T14:00:00",
    "new_end_datetime": "2026-03-10T16:00:00",
    "reason": "Rescheduled due to room maintenance"
  }
  ```

## Booking Status Workflow

```
┌─────────────────────────────────────────────────────────┐
│                    BOOKING LIFECYCLE                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. pending (waiting for approval)                      │
│     ↓                                                    │
│  2. approved (faculty approved) → confirmed              │
│     ↓                                                    │
│  3. active (within 24 hours of start - automated)       │
│     ↓                                                    │
│  4. completed (after end_datetime - automated)          │
│                                                          │
│  [At any time] → cancelled (rejected or cancelled)      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Automated Processes

### 1. Auto-Confirmation Job
- **Schedule**: Every hour (0 minutes of each hour)
- **Action**: Converts "confirmed" bookings to "active" if start time is within 24 hours
- **Purpose**: Activates bookings automatically when they're about to begin

### 2. Cleanup Job
- **Schedule**: Every 30 minutes (*/30)
- **Action**: Marks bookings as "completed" if end_datetime has passed
- **Purpose**: Maintains accurate booking status without manual intervention

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
# APScheduler should be included: APScheduler==3.10.1
```

### 2. Initialize Default Rooms
```bash
python setup_rooms.py
```

This creates default university rooms:
- Gymnasium (100 capacity)
- Open Court (200 capacity)
- Moot Court (50 capacity)
- AV Room (30 capacity)
- Auditorium (500 capacity)
- Seminar Room 1 (20 capacity)
- Conference Room A (25 capacity)

### 3. Start the API Server
```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

## Example Workflow

### Step 1: Student Books a Room
```bash
POST /api/bookings/
{
  "room_id": 1,
  "booking_title": "Physics Department Lab",
  "start_datetime": "2026-03-15T10:00:00",
  "end_datetime": "2026-03-15T12:00:00"
}
```
**Response**: `{status: "success", booking_id: 5}`

### Step 2: Faculty Approves Booking
```bash
POST /api/bookings/5/approve
```
**Status changes**: `pending` → `confirmed`

### Step 3: Automated Processes
- **24 hours before event**: Booking automatically transitions to "active"
- **After event ends**: Booking automatically marked as "completed"

### Step 4: View History
```bash
GET /api/bookings/my-bookings/
```

## Conflict Detection

When a user attempts to book a room:
1. System checks for overlapping confirmed bookings
2. If conflicts exist, returns HTTP 409 with conflict details:
```json
{
  "status": "conflict",
  "message": "Time slot conflicts with existing bookings",
  "conflicts": [
    {
      "booking_id": 3,
      "booking_title": "Board Meeting",
      "user_id": "prof123",
      "start_datetime": "2026-03-10T10:00:00",
      "end_datetime": "2026-03-10T11:30:00"
    }
  ]
}
```

## Administrative Features

### View All Pending Approvals
```bash
GET /api/bookings/pending-approvals/  (Faculty only)
```

### Check Room Schedule
```bash
GET /api/bookings/room/1/schedule/?start_date=2026-03-01&end_date=2026-03-31
```

### Adjust Approved Booking
```bash
PUT /api/bookings/5/adjust
{
  "new_start_datetime": "2026-03-15T14:00:00",
  "new_end_datetime": "2026-03-15T16:00:00",
  "reason": "Maintenance rescheduled"
}
```

## Security & Permissions

- **Students**: Can create bookings, view their own bookings
- **Faculty**: Can create bookings, approve/reject all bookings, view pending approvals, create rooms
- **Role Checks**: All approval endpoints verify user is faculty

## Troubleshooting

### Bookings Not Auto-Confirming?
- Check if APScheduler is installed: `pip install APScheduler==3.10.1`
- Verify server is running (scheduler runs in background)
- Check logs for scheduler errors

### Conflicts Not Detected?
- Ensure both bookings have `status='confirmed'`
- Check if time ranges actually overlap
- Review `booking_conflicts` table for logged conflicts

### Room Not Appearing?
- Verify `is_available=1` in rooms table
- Check room creation succeeded via setup script

## Future Enhancements

1. Email notifications on approval/rejection
2. Recurring bookings support
3. Room capacity-based auto-allocation
4. Building closures/blackout dates
5. User preference-based scheduling
6. Analytics dashboard for room utilization
