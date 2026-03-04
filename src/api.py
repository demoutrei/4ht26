from .db import FacultyDatabase, StudentDatabase
from fastapi import FastAPI


app: FastAPI = FastAPI(
  root_path = "/api/v1"
)


faculty_db: FacultyDatabase = FacultyDatabase()
student_db: StudentDatabase = StudentDatabase()


@app.get('/users/{user_id}')
def fetch_user(user_id: int) -> dict[str, Any]:
  return {
    "text": "Sample"
  }