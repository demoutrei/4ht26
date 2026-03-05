# setup_rooms.py
# Script to initialize default university rooms
import sys
sys.path.insert(0, '.')

from api.booking_scheduler import booking_scheduler

def setup_default_rooms():
    """Create default university rooms."""
    rooms = [
        {
            "room_name": "Gymnasium",
            "room_type": "Sports",
            "capacity": 100,
            "location": "Building A, Ground Floor"
        },
        {
            "room_name": "Open Court",
            "room_type": "Outdoor",
            "capacity": 200,
            "location": "Campus Grounds"
        },
        {
            "room_name": "Moot Court",
            "room_type": "Classroom",
            "capacity": 50,
            "location": "Law Building, 3rd Floor"
        },
        {
            "room_name": "AV Room",
            "room_type": "Meeting",
            "capacity": 30,
            "location": "Admin Building, 2nd Floor"
        },
        {
            "room_name": "Auditorium",
            "room_type": "Event",
            "capacity": 500,
            "location": "Main Building"
        },
        {
            "room_name": "Seminar Room 1",
            "room_type": "Classroom",
            "capacity": 20,
            "location": "Academic Block, 1st Floor"
        },
        {
            "room_name": "Conference Room A",
            "room_type": "Meeting",
            "capacity": 25,
            "location": "Admin Building, 3rd Floor"
        }
    ]
    
    created_count = 0
    for room in rooms:
        try:
            room_id = booking_scheduler.create_room(
                room["room_name"],
                room["room_type"],
                room["capacity"],
                room["location"]
            )
            print(f"✓ Created: {room['room_name']} (ID: {room_id})")
            created_count += 1
        except Exception as e:
            print(f"✗ Failed to create {room['room_name']}: {str(e)}")
    
    print(f"\n✓ Successfully initialized {created_count} rooms!")
    print("Run the following command to start the API server:")
    print("python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload")

if __name__ == "__main__":
    setup_default_rooms()
