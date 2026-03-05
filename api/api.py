from .db import FacultyDatabase, StudentDatabase
from .models import User
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Any


app: FastAPI = FastAPI(
  root_path = "/api/v1"
)


app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


faculty_db: FacultyDatabase = FacultyDatabase()
student_db: StudentDatabase = StudentDatabase()


@app.post('/users/')
def create_user(payload: dict[str, Any]) -> dict[str, Any]:
  return faculty_db.create_user(payload["_id"], full_name = payload["full_name"], password = payload["password"])


@app.get('/users/{user_id}')
def fetch_user(user_id: int) -> dict[str, Any]:
  return {
    "text": "Sample"
  }