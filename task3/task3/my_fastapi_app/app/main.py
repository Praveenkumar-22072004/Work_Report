import os
import re
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from authlib.integrations.starlette_client import OAuth
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv

from .database import SessionLocal, engine, Base
from .models import User, Member

# 🔹 Load environment variables
load_dotenv()

# ✅ Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ Middleware for session management
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# ✅ Templates & Static
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ Password hashing + regex
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{6,}$")

# ✅ Google OAuth Setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

# 🔹 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🔹 Helper
def get_current_user(request: Request, db: Session):
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.query(User).filter(User.id == uid).first()

# ===================== ROUTES =====================

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/login")

# ✅ Register
@app.get("/register")
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    username = username.strip()
    email = email.strip()

    if not username or not email or not password or not confirm_password:
        return templates.TemplateResponse("register.html", {"request": request, "error": "All fields are required."})

    try:
        v = validate_email(email)
        email = v.email.lower()
    except EmailNotValidError:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Invalid email address."})

    if password != confirm_password:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Passwords do not match."})

    if not PASSWORD_RE.match(password):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Password must be 6+ chars, include 1 uppercase and 1 symbol."
        })

    existing = db.query(User).filter(or_(User.username == username, User.email == email)).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username or email already exists."})

    try:
        user = User(username=username, email=email, hashed_password=pwd_context.hash(password))
        db.add(user)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return templates.TemplateResponse("register.html", {"request": request, "error": "Database error. Try again."})

    return RedirectResponse("/login?registered=1", status_code=302)

# ✅ Login
@app.get("/login")
def login_get(request: Request):
    msg = None
    if request.query_params.get("registered") == "1":
        msg = "Registration successful. Please log in."
    if request.query_params.get("error") == "google_failed":
        msg = "Google login failed. Please try again."
    return templates.TemplateResponse("login.html", {"request": request, "message": msg})

@app.post("/login")
def login_post(
    request: Request,
    identifier: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    identifier = identifier.strip()
    if "@" in identifier:
        user = db.query(User).filter(User.email == identifier.lower()).first()
    else:
        user = db.query(User).filter(User.username == identifier).first()

    if not user or not pwd_context.verify(password, user.hashed_password or ""):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return RedirectResponse("/welcome", status_code=302)

# ✅ Google OAuth
@app.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = str(request.url_for("auth_google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
    except Exception:
        return RedirectResponse("/login?error=google_failed")

    email = user_info.get("email")
    name = user_info.get("name") or email.split("@")[0]

    existing = db.query(User).filter(User.email == email).first()
    if not existing:
        user = User(username=name, email=email, hashed_password="")
        db.add(user)
        db.commit()
        existing = user

    request.session.clear()
    request.session["user_id"] = existing.id
    request.session["username"] = existing.username
    return RedirectResponse("/welcome", status_code=302)

# ✅ Logout
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

# ✅ Welcome page
@app.get("/welcome")
def welcome(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/login")
    members = db.query(Member).all()
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "username": request.session.get("username"),
        "members": members
    })

# ✅ Add Member
@app.post("/add-member")
def add_member_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    organization: str = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        return RedirectResponse("/login")

    try:
        member = Member(name=name, email=email, phone=phone, organization=organization)
        db.add(member)
        db.commit()
    except SQLAlchemyError:
        db.rollback()

    return RedirectResponse("/welcome", status_code=302)

# ✅ Edit Member
@app.post("/edit-member")
def edit_member_post(
    request: Request,
    member_id: int = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    organization: str = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        return RedirectResponse("/login")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return RedirectResponse("/welcome", status_code=302)

    member.name = name
    member.email = email
    member.phone = phone
    member.organization = organization
    db.commit()

    return RedirectResponse("/welcome", status_code=302)

# ✅ Delete Member
@app.post("/delete-member")
def delete_member_post(
    request: Request,
    member_id: int = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        return RedirectResponse("/login")

    member = db.query(Member).filter(Member.id == member_id).first()
    if member:
        db.delete(member)
        db.commit()

    return RedirectResponse("/welcome", status_code=302)
