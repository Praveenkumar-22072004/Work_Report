import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import SessionLocal, engine, Base
from . import models, schemas, crud, auth

load_dotenv()

# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="React-Vite + FastAPI Starter")

# allow frontend origin
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth endpoints
class LoginPayload(BaseModel):
    identifier: str
    password: str

@app.post("/api/auth/register", response_model=dict)
def api_register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, payload.username) or crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = crud.create_user(db, payload.username, payload.email, payload.password)
    return {"msg": "ok", "user_id": user.id}

@app.post("/api/auth/login", response_model=schemas.Token)
def api_login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, payload.identifier, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

# Simple utility to get current user
from jose import jwt, JWTError
JWT_SECRET = os.environ.get("JWT_SECRET") or "dev-secret-please-change"

def get_current_user(token: str = Depends(lambda authorization: None), db: Session = Depends(get_db)):
    # This function will be replaced by a proper dependency below.
    raise HTTPException(status_code=500, detail="Use get_current_user_from_header")

from fastapi import Header, Request

def get_current_user_from_header(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    scheme, _, param = authorization.partition(" ")
    if scheme.lower() != "bearer" or not param:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    try:
        payload = jwt.decode(param, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Members CRUD endpoints (protected)
@app.get("/api/members", response_model=list[schemas.MemberOut])
def api_list_members(current_user: models.User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    return crud.list_members(db)

@app.post("/api/members", response_model=schemas.MemberOut)
def api_create_member(member: schemas.MemberCreate, current_user: models.User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    return crud.create_member(db, member.name, member.email, member.phone, member.organization)

@app.put("/api/members/{member_id}", response_model=schemas.MemberOut)
def api_update_member(member_id: int, payload: schemas.MemberCreate, current_user: models.User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    m = crud.update_member(db, member_id, name=payload.name, email=payload.email, phone=payload.phone, organization=payload.organization)
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")
    return m

@app.delete("/api/members/{member_id}", response_model=dict)
def api_delete_member(member_id: int, current_user: models.User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    ok = crud.delete_member(db, member_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"ok": True}
