from pydantic import BaseModel, Field, validator
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str
    confirm_password: str

    @validator("password")
    def strong_password(cls, v):
        regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(regex, v):
            raise ValueError(
                "Password must be at least 8 characters, include uppercase, lowercase, number, and special character."
            )
        return v

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class MemberCreate(BaseModel):
    name: str
    email: str
