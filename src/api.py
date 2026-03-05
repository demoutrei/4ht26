from .db import FacultyDatabase, StudentDatabase
from .models import User
from fastapi import FastAPI


app: FastAPI = FastAPI(
  root_path = "/api/v1"
)


faculty_db: FacultyDatabase = FacultyDatabase()
student_db: StudentDatabase = StudentDatabase()


@app.post('/users/')
def create_user(_id: int, full_name: str, password: str) -> User:
  user: User = faculty_db.create_user(_id, full_name = full_name, password = password)
  return user


@app.get('/users/{user_id}')
def fetch_user(user_id: int) -> dict[str, Any]:
  return {
    "text": "Sample"
  }