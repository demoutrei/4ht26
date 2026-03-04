# db.py
import sqlite3
from contextlib import contextmanager

DB_FILE = "university_admin.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id_number TEXT PRIMARY KEY,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL CHECK(role IN ('student', 'faculty'))
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS agent_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id TEXT,
            instruction TEXT,
            intent TEXT,
            status TEXT DEFAULT 'draft',
            pdf_path TEXT,
            signed_by TEXT,
            signature_data TEXT,
            signed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()

def log_request(requester_id: str, instruction: str, intent: str, pdf_path: str, status: str = "draft") -> int:
    """Insert a new agent request into the database and return its ID."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO agent_requests (requester_id, instruction, intent, status, pdf_path)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (requester_id, instruction, intent, status, pdf_path),
        )
        conn.commit()
        return c.lastrowid

def update_request_status(request_id: int, status: str) -> bool:
    """Update the status of an agent request (e.g., approved, rejected, sent, draft)."""
    valid_statuses = ["draft", "approved", "rejected", "sent"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE agent_requests SET status = ? WHERE id = ?",
            (status, request_id)
        )
        conn.commit()
        return c.rowcount > 0

def approve_request_with_signature(request_id: int, faculty_id: str, signature_data: str) -> bool:
    """Approve a request with e-signature and save signature details."""
    from datetime import datetime
    
    with get_db() as conn:
        c = conn.cursor()
        signed_at = datetime.now().isoformat()
        c.execute(
            """UPDATE agent_requests 
               SET status = ?, signed_by = ?, signature_data = ?, signed_at = ? 
               WHERE id = ?""",
            ("approved", faculty_id, signature_data, signed_at, request_id)
        )
        conn.commit()
        return c.rowcount > 0

def get_request_by_id(request_id: int):
    """Fetch a single agent request by ID."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM agent_requests WHERE id = ?", (request_id,))
        return c.fetchone()

def get_user_requests(user_id: str):
    """Fetch all requests for a specific user."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM agent_requests WHERE requester_id = ? ORDER BY created_at DESC", (user_id,))
        return c.fetchall()

import sqlite3
from db import get_db # Importing your existing context manager

def seed_dummy_data():
    with get_db() as conn:
        c = conn.cursor()

        # 1. Dummy Data for the 'users' table 
        # Schema: id_number, hashed_password, full_name, role
        dummy_users = [
            ('2024-001', 'hash_abc_123', 'Alice Smith', 'student'),
            ('2024-002', 'hash_def_456', 'Dr. Bob Jones', 'faculty'),
            ('2024-003', 'hash_ghi_789', 'Charlie Brown', 'student')
        ]

        # 2. Dummy Data for the 'agent_requests' table 
        # Schema: requester_id, instruction, intent, status, pdf_path
        # Note: id and created_at are handled automatically 
        dummy_requests = [
            ('2024-001', 'Generate my transcript', 'transcript_request', 'completed', '/path/to/file1.pdf'),
            ('2024-003', 'Change my major to CS', 'major_change', 'pending', '/path/to/file2.pdf'),
            ('2024-002', 'Submit research grant', 'grant_submission', 'draft', None)
        ]

        # Execute inserts [cite: 34, 35, 36]
        c.executemany('''
            INSERT OR IGNORE INTO users (id_number, hashed_password, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', dummy_users)

        c.executemany('''
            INSERT INTO agent_requests (requester_id, instruction, intent, status, pdf_path)
            VALUES (?, ?, ?, ?, ?)
        ''', dummy_requests)

        conn.commit()
        print(f"Database seeded successfully!")

def clear_agent_requests():
    """Delete all records from the agent_requests table."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM agent_requests")
        conn.commit()
        print("All agent requests cleared from the database.")

def reset_agent_request_id():
    """Reset the AUTOINCREMENT ID sequence for agent_requests table."""
    with get_db() as conn:
        c = conn.cursor()
        # Reset the sequence counter in sqlite_sequence
        c.execute("DELETE FROM sqlite_sequence WHERE name='agent_requests'")
        conn.commit()
        print("Agent request ID counter reset to 0. Next insert will start at ID 1.")

def reset_agent_requests_full():
    """Clear all agent requests AND reset the ID sequence (nuclear option)."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM agent_requests")
        c.execute("DELETE FROM sqlite_sequence WHERE name='agent_requests'")
        conn.commit()
        print("Agent requests table cleared and ID counter reset.")

def clear_users():
    """Delete all records from the users table."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users")
        conn.commit()
        print("All users cleared from the database.")

def clear_all_data():
    """Clear both users and agent_requests tables, reset all sequences."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM agent_requests")
        c.execute("DELETE FROM users")
        c.execute("DELETE FROM sqlite_sequence WHERE name='agent_requests'")
        conn.commit()
        print("All data cleared and ID sequences reset.")

if __name__ == "__main__":
    seed_dummy_data()
    
    
    
    
    
    
    
    
    
    
    