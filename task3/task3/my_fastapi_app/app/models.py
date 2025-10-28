from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.database import Base

class User(Base):
    __tablename__ = "users"   # ✅ use plural table name
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # password hash
    profile_picture = Column(String(255), nullable=True)   # Google OAuth profile picture

    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

class Member(Base):
    __tablename__ = "members"   # ✅ use plural table name
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(40), nullable=True)
    organization = Column(String(120), nullable=True)

    __table_args__ = (
        UniqueConstraint("email", name="uq_members_email"),
    )
