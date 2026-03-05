from .db import FacultyDatabase, StudentDatabase
from .models import User
from fastapi import FastAPI


app: FastAPI = FastAPI(
  root_path = "/api/v1"
)


faculty_db: FacultyDatabase = FacultyDatabase()
student_db: StudentDatabase = StudentDatabase()


@app.post('/users/')
def create_user(user: User) -> User:
  ...
  # Code to create User here


@app.get('/users/{user_id}')
def fetch_user(user_id: int) -> dict[str, Any]:
  return {
    "text": "Sample"
  }