from enum import Enum

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Role(str, Enum):
    EMPLOYEE = "employee"
    CLIENT = "client"
    MODERATOR = "moderator"


class UserOut(BaseModel):
    id: Optional[str] = None
    email: str
    password: str
    role: Role


