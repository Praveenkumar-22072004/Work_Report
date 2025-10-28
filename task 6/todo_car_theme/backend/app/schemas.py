from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ---------- USER ----------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- GROUP ----------
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- INVITE ----------
class InviteCreate(BaseModel):
    email: EmailStr


class InviteRead(BaseModel):
    id: int
    email: EmailStr
    group_id: int
    status: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- TASK ----------
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_email: Optional[EmailStr] = None
    due_date: Optional[datetime] = None


class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    group_id: int
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True
