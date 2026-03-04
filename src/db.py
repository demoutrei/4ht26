from typing import Optional, Self
import sqlite3


class Database:
  def __enter__(self: Self) -> sqlite3.Cursor:
    return self.connection.cursor()


  def __exit__(self: Self, exception_type, exception_value, exception_traceback) -> None:
    self.connection.commit()
  
  
  def __init__(self: Self, file_path: str) -> None:
    self.__file_path: str = file_path
    self.__connection: sqlite3.Connection = sqlite3.connect(self.path, check_same_thread = False)
  
  
  @property
  def connection(self: Self) -> sqlite3.Connection:
    return self.__connection


  @property
  def path(self: Self) -> str:
    return self.__file_path


class FacultyDatabase(Database):
  _instance: Optional[Self] = None


  def __init__(self: Self) -> None:
    super().__init__('database/faculty.db')
    with self as cursor:
      cursor.execute(
        """
          CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            password TEXT NOT NULL,
            full_name TEXT
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


  def __new__(cls, *args, **kwargs) -> Self:
    return cls._instance or super().__new__(cls)


class StudentDatabase(Database):
  _instance: Optional[Self] = None

  
  def __init__(self: Self) -> None:
    super().__init__('database/student.db')
    with self as cursor:
      cursor.execute(
        """
          CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            password TEXT NOT NULL,
            full_name TEXT
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
  
  
  def __new__(cls, *args, **kwargs) -> Self:
    return cls._instance or super().__new__(cls)