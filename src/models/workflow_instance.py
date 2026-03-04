from pydantic import BaseModel


class WorkflowInstance(BaseModel):
  _id: int
  user_id: int
  workflow_id: int