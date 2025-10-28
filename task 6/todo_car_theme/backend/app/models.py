from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class GroupMemberLink(SQLModel, table=True):
    group_id: Optional[int] = Field(default=None, foreign_key="group.id", primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role: str = "member"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    groups: List["Group"] = Relationship(back_populates="members", link_model=GroupMemberLink)
    tasks: List["Task"] = Relationship(back_populates="assignee")


class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    members: List[User] = Relationship(back_populates="groups", link_model=GroupMemberLink)
    invitations: List["Invitation"] = Relationship(back_populates="group")
    tasks: List["Task"] = Relationship(back_populates="group")


class Invitation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id")
    email: str
    status: str = Field(default="pending")  # pending, accepted, rejected
    token: Optional[str] = None
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    group: Optional[Group] = Relationship(back_populates="invitations")


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    group_id: Optional[int] = Field(default=None, foreign_key="group.id")
    assignee_id: Optional[int] = Field(default=None, foreign_key="user.id")
    status: str = Field(default="todo")  # todo, in_progress, done
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    group: Optional[Group] = Relationship(back_populates="tasks")
    assignee: Optional[User] = Relationship(back_populates="tasks")
