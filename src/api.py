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
  allow_origins=["*", 'https://127.0.0.1:5500'],
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
  payload: dict[str, Any] = dict()
  with faculty_db as cursor:
    cursor.execute(
      f"""
        SELECT * FROM users WHERE user_id = ?
      """,
      (int(user_id),)
    )
    data = cursor.fetchone()
    print(f"{data = }")
    payload["_id"]: int = int(user_id)
    payload["full_name"]: str = data[1]
    payload["password"]: str = data[2]
  return payload