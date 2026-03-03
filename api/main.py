from fastapi import FastAPI
from typing import Any


app: FastAPI = FastAPI()


@app.get("/api/workflows/{workflow_id}")
def workflow_display(workflow_id: int) -> dict[str, Any]:
  return {
    "text": "Hello, World!"
  }