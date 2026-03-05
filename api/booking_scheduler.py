# booking_scheduler.py
# Automated room booking and scheduling system
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

DB_FILE = "university_admin.db"

class BookingScheduler:
    """Manages room bookings and automated schedule adjustments."""
    
    def __init__(self):
        self.scheduler = None
        self._init_scheduler()
        self._init_booking_tables()
    
    def _init_scheduler(self):
        """Initialize scheduler lazily to avoid pkg_resources import issues."""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            self._setup_scheduled_jobs()
        except Exception as e:
            print(f"Warning: APScheduler not available ({e}). Scheduler will not run automatically.")
            print("Bookings can still be created and approved manually.")
            self.scheduler = None
    
    def _setup_scheduled_jobs(self):
        """Setup background scheduled jobs."""
        def confirm_upcoming_bookings():
            conn = self._get_db()
            cursor = conn.cursor()
            cutoff_time = datetime.now() + timedelta(days=1)
            cursor.execute(
                '''UPDATE bookings 
                   SET status = 'active'
                   WHERE approval_status = 'approved' AND status = 'confirmed'
                   AND start_datetime <= ? AND end_datetime > ?''',
                (cutoff_time.isoformat(), datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        
        def mark_completed():
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE bookings 
                   SET status = 'completed'
                   WHERE status IN ('active', 'confirmed') 
                   AND end_datetime <= ?''',
                (datetime.now().isoformat(),)
            )
            conn.commit()
            conn.close()
        
        try:
            from apscheduler.triggers.cron import CronTrigger
            
            self.scheduler.add_job(
                confirm_upcoming_bookings,
                CronTrigger(minute=0),
                id='auto_confirm_bookings',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                mark_completed,
                CronTrigger(minute='*/30'),
                id='cleanup_expired_bookings',
                replace_existing=True
            )
        except Exception as e:
            print(f"Could not setup scheduled jobs: {e}")
    
    def _get_db(self):
        """Get database connection."""
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_booking_tables(self):
        """Initialize booking-related database tables."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Rooms table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            capacity INTEGER,
            location TEXT,
            is_available BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Bookings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            booking_title TEXT,
            start_datetime DATETIME NOT NULL,
            end_datetime DATETIME NOT NULL,
            status TEXT DEFAULT 'pending',
            approval_status TEXT DEFAULT 'pending',
            approved_by TEXT,
            approved_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(room_id) REFERENCES rooms(room_id),
            FOREIGN KEY(user_id) REFERENCES users(id_number)
        )
        ''')
        
        # Booking conflicts log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking_conflicts (
            conflict_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            conflicting_booking_id INTEGER NOT NULL,
            conflict_type TEXT,
            resolution_action TEXT,
            resolved_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(booking_id) REFERENCES bookings(booking_id),
            FOREIGN KEY(conflicting_booking_id) REFERENCES bookings(booking_id)
        )
        ''')
        
        # Schedule adjustments log (for auditing)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_adjustments (
            adjustment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            original_start DATETIME,
            original_end DATETIME,
            new_start DATETIME,
            new_end DATETIME,
            reason TEXT,
            approved BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(booking_id) REFERENCES bookings(booking_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_room(self, room_name: str, room_type: str, capacity: int, location: str) -> int:
        """Create a new room."""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO rooms (room_name, room_type, capacity, location)
               VALUES (?, ?, ?, ?)''',
            (room_name, room_type, capacity, location)
        )
        conn.commit()
        room_id = cursor.lastrowid
        conn.close()
        return room_id
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Fetch all available rooms."""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE is_available = 1 ORDER BY room_name")
        rooms = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rooms
    
    def book_room(self, room_id: int, user_id: str, booking_title: str, 
                  start_datetime: datetime, end_datetime: datetime) -> Dict[str, Any]:
        """Create a new booking (pending approval)."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Check for conflicts
        conflicts = self._check_conflicts(cursor, room_id, start_datetime, end_datetime)
        
        if conflicts:
            conn.close()
            return {
                "status": "conflict",
                "message": "Time slot conflicts with existing bookings",
                "conflicts": conflicts,
                "booking_id": None
            }
        
        # Create booking
        cursor.execute(
            '''INSERT INTO bookings 
               (room_id, user_id, booking_title, start_datetime, end_datetime, status)
               VALUES (?, ?, ?, ?, ?, 'pending')''',
            (room_id, user_id, booking_title, start_datetime, end_datetime)
        )
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()
        
        return {
            "status": "success",
            "message": "Booking created (pending approval)",
            "booking_id": booking_id
        }
    
    def approve_booking(self, booking_id: int, approved_by: str) -> bool:
        """Approve a pending booking."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            '''UPDATE bookings 
               SET approval_status = 'approved', approved_by = ?, 
                   approved_at = ?, status = 'confirmed', updated_at = ?
               WHERE booking_id = ?''',
            (approved_by, datetime.now().isoformat(), datetime.now().isoformat(), booking_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def reject_booking(self, booking_id: int, reason: str = None) -> bool:
        """Reject a pending booking."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            '''UPDATE bookings 
               SET approval_status = 'rejected', status = 'cancelled', updated_at = ?
               WHERE booking_id = ?''',
            (datetime.now().isoformat(), booking_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def adjust_booking_time(self, booking_id: int, new_start: datetime, 
                           new_end: datetime, reason: str = None) -> Dict[str, Any]:
        """Adjust booking time (for approved bookings only)."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Get current booking
        cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            conn.close()
            return {"status": "error", "message": "Booking not found"}
        
        if booking["status"] != "confirmed":
            conn.close()
            return {"status": "error", "message": "Only confirmed bookings can be adjusted"}
        
        # Check for conflicts with new time
        conflicts = self._check_conflicts(cursor, booking["room_id"], new_start, new_end, exclude_booking_id=booking_id)
        
        if conflicts:
            conn.close()
            return {
                "status": "conflict",
                "message": "New time slot conflicts with other bookings",
                "conflicts": conflicts
            }
        
        # Log the adjustment
        cursor.execute(
            '''INSERT INTO schedule_adjustments 
               (booking_id, original_start, original_end, new_start, new_end, reason)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (booking_id, booking["start_datetime"], booking["end_datetime"], 
             new_start.isoformat(), new_end.isoformat(), reason)
        )
        
        # Update booking
        cursor.execute(
            '''UPDATE bookings 
               SET start_datetime = ?, end_datetime = ?, updated_at = ?
               WHERE booking_id = ?''',
            (new_start.isoformat(), new_end.isoformat(), datetime.now().isoformat(), booking_id)
        )
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "Booking time adjusted",
            "booking_id": booking_id
        }
    
    def get_bookings_by_room(self, room_id: int, 
                            start_date: datetime = None, 
                            end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get all bookings for a specific room within a date range."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute(
                '''SELECT * FROM bookings 
                   WHERE room_id = ? AND status != 'cancelled'
                   AND start_datetime >= ? AND end_datetime <= ?
                   ORDER BY start_datetime''',
                (room_id, start_date.isoformat(), end_date.isoformat())
            )
        else:
            cursor.execute(
                '''SELECT * FROM bookings 
                   WHERE room_id = ? AND status != 'cancelled'
                   ORDER BY start_datetime''',
                (room_id,)
            )
        
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bookings
    
    def get_user_bookings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bookings for a specific user."""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT b.*, r.room_name, r.room_type 
               FROM bookings b
               JOIN rooms r ON b.room_id = r.room_id
               WHERE b.user_id = ? AND b.status != 'cancelled'
               ORDER BY b.start_datetime DESC''',
            (user_id,)
        )
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bookings
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending booking approvals."""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT b.*, r.room_name, r.room_type 
               FROM bookings b
               JOIN rooms r ON b.room_id = r.room_id
               WHERE b.approval_status = 'pending'
               ORDER BY b.created_at DESC'''
        )
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bookings
    
    def _check_conflicts(self, cursor: sqlite3.Cursor, room_id: int, 
                        start_datetime: datetime, end_datetime: datetime,
                        exclude_booking_id: int = None) -> List[Dict[str, Any]]:
        """Check for time slot conflicts."""
        query = '''
        SELECT booking_id, booking_title, user_id, start_datetime, end_datetime 
        FROM bookings 
        WHERE room_id = ? AND status = 'confirmed' 
        AND (
            (start_datetime < ? AND end_datetime > ?)
            OR (start_datetime >= ? AND start_datetime < ?)
        )
        '''
        params = [room_id, end_datetime.isoformat(), start_datetime.isoformat(),
                  start_datetime.isoformat(), end_datetime.isoformat()]
        
        if exclude_booking_id:
            query += " AND booking_id != ?"
            params.append(exclude_booking_id)
        
        cursor.execute(query, params)
        conflicts = [dict(row) for row in cursor.fetchall()]
        return conflicts
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()


# Initialize global scheduler instance
booking_scheduler = BookingScheduler()
