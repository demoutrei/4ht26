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
        c.execute('''
        CREATE TABLE IF NOT EXISTS created_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id TEXT NOT NULL,
            workflow_name TEXT NOT NULL,
            workflow_description TEXT,
            workflow_config TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(creator_id) REFERENCES users(id_number)
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS triggered_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            triggered_by TEXT NOT NULL,
            status TEXT DEFAULT 'running',
            execution_result TEXT,
            triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            FOREIGN KEY(workflow_id) REFERENCES created_workflows(id),
            FOREIGN KEY(triggered_by) REFERENCES users(id_number)
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

def create_workflow(creator_id: str, workflow_name: str, workflow_description: str, workflow_config: str) -> int:
    """Create a new workflow and return its ID."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            '''INSERT INTO created_workflows (creator_id, workflow_name, workflow_description, workflow_config)
               VALUES (?, ?, ?, ?)''',
            (creator_id, workflow_name, workflow_description, workflow_config)
        )
        conn.commit()
        return c.lastrowid

def get_workflow_by_id(workflow_id: int):
    """Fetch a workflow by ID."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM created_workflows WHERE id = ?", (workflow_id,))
        return c.fetchone()

def get_user_workflows(user_id: str):
    """Fetch all workflows created by a user."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM created_workflows WHERE creator_id = ? ORDER BY created_at DESC", (user_id,))
        return c.fetchall()

def trigger_workflow(workflow_id: int, triggered_by: str) -> int:
    """Trigger/execute a workflow and return the execution ID."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            '''INSERT INTO triggered_workflows (workflow_id, triggered_by, status)
               VALUES (?, ?, 'running')''',
            (workflow_id, triggered_by)
        )
        conn.commit()
        return c.lastrowid

def get_triggered_workflow_by_id(triggered_id: int):
    """Fetch a triggered workflow execution by ID."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM triggered_workflows WHERE id = ?", (triggered_id,))
        return c.fetchone()

def get_user_triggered_workflows(user_id: str):
    """Fetch all workflow executions triggered by a user."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM triggered_workflows WHERE triggered_by = ? ORDER BY triggered_at DESC", (user_id,))
        return c.fetchall()

def update_triggered_workflow_status(triggered_id: int, status: str, execution_result: str = None) -> bool:
    """Update the status and result of a triggered workflow."""
    from datetime import datetime
    valid_statuses = ["running", "completed", "failed", "cancelled"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
    
    with get_db() as conn:
        c = conn.cursor()
        completed_at = datetime.now().isoformat() if status in ["completed", "failed", "cancelled"] else None
        c.execute(
            '''UPDATE triggered_workflows 
               SET status = ?, execution_result = ?, completed_at = ?
               WHERE id = ?''',
            (status, execution_result, completed_at, triggered_id)
        )
        conn.commit()
        return c.rowcount > 0


    
    
    
    
    
    
    
    
    
    
    