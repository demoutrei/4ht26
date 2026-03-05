from .db import Database
from .models import User
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Any


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


database: Database = Database()


@app.post('/users/')
def create_user(payload: dict[str, Any]) -> dict[str, Any]:
  return database.create_user(
    payload["_id"],
    full_name = payload["full_name"],
    password = payload["password"],
    user_type = payload["user_type"]
  )


@app.get('/users/{user_id}')
def fetch_user(user_id: int) -> Optional[dict[str, Any]]:
  return database.fetch_user(user_id)


@app.get('/users/{user_id}/workflows/instances')
def workflow_instances(user_id: int) -> list[dict[str, Any]]:
  return database.get_workflow_instances(user_id)


@app.post('/users/{user_id}/workflows/{workflow_id}/trigger')
def workflow_trigger(user_id: int, workflow_id: int) -> dict[str, Any]:
  return database.trigger_workflow(user_id, workflow_id)