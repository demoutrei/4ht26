from .models import User
from typing import Any, Literal, Optional, Self, Union
import sqlite3


class Database:
  def __enter__(self: Self) -> sqlite3.Cursor:
    return self.connection.cursor()

  def __exit__(self: Self, exception_type, exception_value, exception_traceback) -> None:
    self.connection.commit()
  
  def __init__(self: Self) -> None:
    self.__file_path: str = 'database/main.db'
    self.__connection: sqlite3.Connection = sqlite3.connect(self.path, check_same_thread = False)
    self.connection.row_factory: sqlite3.Row = sqlite3.Row
    with self as cursor:
      cursor.execute(
        """
          CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            password TEXT NOT NULL,
            full_name TEXT,
            user_type TEXT CHECK (user_type IN ("student", "faculty"))
          )
        """
      )
      cursor.execute(
        """
          CREATE TABLE IF NOT EXISTS workflow_templates (
            workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            instruction TEXT,
            intent TEXT,
            status TEXT DEFAULT 'draft',
            pdf_path TEXT,
            signed_by TEXT,
            signature_hash TEXT,
            signed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
          )
        """
      )
      cursor.execute(
        """
          CREATE TABLE IF NOT EXISTS workflow_instances (
            instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            workflow_id INTEGER
          )
        """
      )
  
  @property
  def connection(self: Self) -> sqlite3.Connection:
    return self.__connection

  def clear_table(self: Self, name: str) -> None:
    with self as cursor:
      cursor.execute(f"""DELETE FROM {name}""")

  def create_user(self: Self, _id: int, *, full_name: str, password: str, user_type: Union[Literal["student"], Literal["faculty"]]) -> dict[str, Any]:
    with self as cursor:
      cursor.execute(
        """
          INSERT INTO users (user_id, password, full_name, user_type) values (?, ?, ?, ?)
        """,
        (_id, password, full_name, user_type)
      )
    return self.fetch_user(_id)

  def delete_table(self: Self, name: str) -> None:
    if not isinstance(name, str): raise TypeError(f"name: Must be an instance of {str.__name__}; not {name.__class__.__name__}")
    with self as cursor:
      cursor.execute(
        f"""
          DROP TABLE IF EXISTS {name}
        """
      )

  def delete_user(self: Self, user_id: int) -> None:
    with self as cursor:
      cursor.execute(
        """DELETE FROM users WHERE user_id = ?""",
        (user_id,)
      )

  def fetch_user(self: Self, user_id: int) -> Optional[dict[str, Any]]:
    data: Optional[dict[str, Any]] = None
    with self as cursor:
      cursor.execute(
        f"""
          SELECT * FROM users WHERE user_id = ?
        """,
        (int(user_id),)
      )
      data: Optional[dict[str, Any]] = cursor.fetchone()
    if not data: return None
    return dict(data)

  def get_workflow(self: Self, workflow_id: int) -> Optional[dict[str, Any]]:
    data: Optional[dict[str, Any]] = None
    with self as cursor:
      cursor.execute(
        f"""
          SELECT * FROM workflow_templates WHERE workflow_id = ?
        """,
        (int(workflow_id),)
      )
      data: Optional[dict[str, Any]] = cursor.fetchone()
    if not data: return None
    return dict(data)

  def get_workflow_instance(self: Self, user_id: int, instance_id: int) -> Optional[dict[str, Any]]:
    data: Optional[dict[str, Any]] = None
    with self as cursor:
      cursor.execute(
        f"""
          SELECT * FROM workflow_instances WHERE user_id = ? AND instance_id = ?
        """,
        (int(user_id), int(instance_id))
      )
      data: Optional[dict[str, Any]] = cursor.fetchone()
    if not data: return None
    return dict(data)

  def get_workflow_instances(self: Self, user_id: int) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = list()
    with self as cursor:
      cursor.execute(
        """
          SELECT * FROM workflow_instances WHERE user_id = ?
        """,
        (int(user_id),)
      )
      data: list[dict[str, Any]] = cursor.fetchall()
    return [dict(item) for item in data]

  @property
  def path(self: Self) -> str:
    return self.__file_path

  def trigger_workflow(self: Self, user_id: int, workflow_id: int) -> dict[str, Any]:
    instance_id: int = None
    with self as cursor:
      cursor.execute(
        """
          INSERT INTO workflow_instances (user_id, workflow_id) values (?, ?)
        """,
        (int(user_id), int(workflow_id))
      )
      instance_id = cursor.execute(
        """
          SELECT MAX(instance_id) FROM workflow_instances
        """
      )
      instance_id = list(cursor.fetchone())[0]
    return self.get_workflow_instance(user_id, instance_id)


# class FacultyDatabase(Database):
#   _instance: Optional[Self] = None


#   def __init__(self: Self) -> None:
#     super().__init__('database/faculty.db')
#     with self as cursor:
#       cursor.execute(
#         """
#           CREATE TABLE IF NOT EXISTS users (
#             user_id INTEGER PRIMARY KEY,
#             password TEXT NOT NULL,
#             full_name TEXT
#           )
#         """
#       )
#       cursor.execute(
#         """
#           CREATE TABLE IF NOT EXISTS workflow_templates (
#             workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER,
#             instruction TEXT,
#             intent TEXT,
#             status TEXT DEFAULT 'draft',
#             pdf_path TEXT,
#             signed_by TEXT,
#             signature_hash TEXT,
#             signed_at DATETIME,
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
#           )
#         """
#       )
#       cursor.execute(
#         """
#           CREATE TABLE IF NOT EXISTS workflow_instances (
#             instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER,
#             workflow_id INTEGER
#           )
#         """
#       )


#   def __new__(cls, *args, **kwargs) -> Self:
#     return cls._instance or super().__new__(cls)


# class StudentDatabase(Database):
#   _instance: Optional[Self] = None

  
#   def __init__(self: Self) -> None:
#     super().__init__('database/student.db')
#     with self as cursor:
#       cursor.execute(
#         """
#           CREATE TABLE IF NOT EXISTS users (
#             user_id INTEGER PRIMARY KEY,
#             password TEXT NOT NULL,
#             full_name TEXT
#           )
#         """
#       )
#       cursor.execute(
#         """
#           CREATE TABLE IF NOT EXISTS workflow_instances (
#             instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER,
#             workflow_id INTEGER
#           )
#         """
#       )
  
  
#   def __new__(cls, *args, **kwargs) -> Self:
#     return cls._instance or super().__new__(cls)