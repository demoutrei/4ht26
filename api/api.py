import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import User
from api.db_copy_src import FacultyDatabase, StudentDatabase
from fastapi import FastAPI
import hashlib


app: FastAPI = FastAPI(
  root_path = "/api/v1"
)


faculty_db: FacultyDatabase = FacultyDatabase()
student_db: StudentDatabase = StudentDatabase()


@app.post('/users/')
def create_user_endpoint(user: User) -> dict:
    """Create a new user account."""
    try:
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        with faculty_db as cursor:
            cursor.execute(
                "INSERT INTO users (user_id, password, full_name) VALUES (?, ?, ?)",
                (user._id, hashed_password, user.full_name)
            )
        return {"message": "User created successfully", "user_id": user._id, "full_name": user.full_name}
    except Exception as e:
        return {"error": str(e)}


@app.get('/users/{user_id}')
def fetch_user(user_id: int) -> dict:
    """Retrieve user data from the database."""
    try:
        with faculty_db as cursor:
            cursor.execute("SELECT user_id, full_name FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id_number": row[0],
                    "full_name": row[1]
                }
            else:
                return {"error": "User not found"}
    except Exception as e:
        return {"error": str(e)}