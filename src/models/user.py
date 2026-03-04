from pydantic import BaseModel


class User(BaseModel):
  _id: int
  full_name: str
  password: str