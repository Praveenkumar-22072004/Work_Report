import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Member
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from pydantic import EmailStr, ValidationError
from dotenv import load_dotenv

# ------------------- Load environment -------------------
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")  # safer
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google")

# ------------------- App setup -------------------
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# DB setup
Base.metadata.create_all(bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- Home -------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ------------------- Register -------------------
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    email = email.strip().lower()

    try:
        EmailStr.validate(email)
    except ValidationError:
        return templates.TemplateResponse("register.html", {"request": request, "error": "❌ Invalid email format."})

    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "❌ Username already exists."})

    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "❌ Email already registered."})

    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/login", status_code=303)

# ------------------- Login -------------------
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.password or not pwd_context.verify(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "❌ Invalid username or password."})

    request.session["user"] = user.username
    request.session["email"] = user.email
    request.session["picture"] = user.profile_pic
    return RedirectResponse(url="/welcome", status_code=303)

# ------------------- Google OAuth -------------------
@app.get("/login/google")
async def login_google(request: Request):
    # Use GOOGLE_REDIRECT_URI from .env to avoid mismatch
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@app.get("/auth/google")
async def auth_google(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        return RedirectResponse(url="/login")

    email = user_info["email"].lower()
    username = user_info.get("name", email.split("@")[0])
    picture = user_info.get("picture")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        new_user = User(username=username, email=email, password=None, profile_pic=picture)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    request.session["user"] = user.username
    request.session["email"] = user.email
    request.session["picture"] = user.profile_pic
    return RedirectResponse(url="/welcome")

# ------------------- Welcome -------------------
@app.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("welcome.html", {"request": request, "user": user})

# ------------------- Add Member -------------------
@app.get("/add-member", response_class=HTMLResponse)
async def add_member_form(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("add_member.html", {"request": request, "error": None})

@app.post("/add-member", response_class=HTMLResponse)
async def add_member(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")

    email = email.strip().lower()

    try:
        EmailStr.validate(email)
    except ValidationError:
        return templates.TemplateResponse("add_member.html", {"request": request, "error": "❌ Invalid email format."})

    if db.query(Member).filter(Member.email == email).first():
        return templates.TemplateResponse("add_member.html", {"request": request, "error": "❌ Member email already exists."})

    new_member = Member(name=name, email=email, role=role)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return RedirectResponse(url="/members", status_code=303)

# ------------------- Members -------------------
@app.get("/members", response_class=HTMLResponse)
async def members(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")

    members = db.query(Member).all()
    return templates.TemplateResponse("members.html", {"request": request, "members": members})

# ------------------- Logout -------------------
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")
