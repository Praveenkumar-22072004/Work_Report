import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import SQLModel, create_engine, Session, select
from dotenv import load_dotenv
from . import models, crud, schemas
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

if not DATABASE_URL:
    raise RuntimeError("Please set DATABASE_URL in .env (see .env.example)")

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI(title="ToDo Car Theme Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# ===============================
# USERS
# ===============================
@app.post("/users/", response_model=schemas.UserCreate)
def create_user(user: schemas.UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(models.User).where(models.User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    u = models.User(email=user.email, full_name=user.full_name)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


# ===============================
# GROUPS
# ===============================
@app.post("/groups/")
def create_group(data: schemas.GroupCreate, session: Session = Depends(get_session)):
    group = crud.create_group(session, data.name, data.description, creator_email=data.name + "@local")
    return {"group": group}


@app.get("/groups")
def list_groups(session: Session = Depends(get_session)):
    groups = session.exec(select(models.Group)).all()
    return {"groups": [{"id": g.id, "name": g.name, "description": g.description} for g in groups]}


# ===============================
# INVITES
# ===============================
@app.post("/groups/{group_id}/invite")
def invite(group_id: int, invite: schemas.InviteCreate, request: Request, session: Session = Depends(get_session)):
    group = session.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    backend_url = str(request.base_url).rstrip("/")
    inv = crud.invite_member(session, group, invite.email, backend_url)
    return {"invitation": inv}


# ---------- Invitation Landing Page ----------
@app.get("/backend/invites/accept/{token}", response_class=HTMLResponse)
def show_accept_page(token: str, session: Session = Depends(get_session)):
    inv = session.exec(select(models.Invitation).where(models.Invitation.token == token)).first()
    if not inv:
        return HTMLResponse("<h1>❌ Invalid or expired invitation</h1>", status_code=404)

    group = session.get(models.Group, inv.group_id)

    html = f"""
    <html>
    <head>
        <title>Invitation to {group.name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                background: #f9fafb;
                padding: 40px;
            }}
            h1 {{
                color: #333;
            }}
            .btn {{
                display: inline-block;
                margin: 15px;
                padding: 14px 28px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                text-decoration: none;
                transition: 0.3s ease;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .accept {{
                background: linear-gradient(45deg, #4caf50, #66bb6a);
                color: white;
            }}
            .accept:hover {{
                background: linear-gradient(45deg, #43a047, #388e3c);
                transform: scale(1.08);
            }}
            .time {{
                background: linear-gradient(45deg, #ff9800, #ffa726);
                color: white;
            }}
            .time:hover {{
                background: linear-gradient(45deg, #fb8c00, #ef6c00);
                transform: scale(1.08);
            }}
        </style>
    </head>
    <body>
        <h1>📩 Invitation to join <b>{group.name}</b></h1>
        <p>{group.description or ''}</p>
        <a class="btn accept" href="/backend/invites/accept/{token}/confirm">✅ Accept</a>
        <a class="btn time" href="/backend/invites/accept/{token}/time">⏳ Need More Time</a>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ---------- Accept Invite ----------
@app.get("/backend/invites/accept/{token}/confirm", response_class=HTMLResponse)
def confirm_accept(token: str, session: Session = Depends(get_session)):
    result = crud.accept_invitation(session, token, user_email=None)
    if not result:
        return HTMLResponse("<h1>❌ Invalid or expired invitation</h1>", status_code=404)

    group, user_email = result
    user = session.exec(select(models.User).where(models.User.email == user_email)).first()

    tasks = session.exec(
        select(models.Task).where(
            models.Task.group_id == group.id,
            models.Task.assignee_email == user.email
        )
    ).all()

    members = [m.email for m in group.members]

    tasks_html = "".join(
        f"<tr><td>{t.title}</td><td>{t.description or ''}</td><td>{t.due_date or 'N/A'}</td></tr>"
        for t in tasks
    ) or "<tr><td colspan='3'>No tasks assigned yet</td></tr>"

    members_html = "".join(f"<li>{m}</li>" for m in members)

    html = f"""
    <html>
    <head>
        <title>Tasks for {user_email}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6f8;
                padding: 30px;
            }}
            h1, h2, h3 {{
                color: #333;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background: #eaeaea;
            }}
            ul {{
                margin-top: 15px;
                padding-left: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>✅ You have joined <b>{group.name}</b></h1>
        <h2>Welcome, {user_email}</h2>

        <h3>Your Assigned Tasks:</h3>
        <table>
            <tr><th>Title</th><th>Description</th><th>Due Date</th></tr>
            {tasks_html}
        </table>

        <h3>Group Members:</h3>
        <ul>{members_html}</ul>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ---------- Need More Time ----------
@app.get("/backend/invites/accept/{token}/time", response_class=HTMLResponse)
def need_more_time(token: str, session: Session = Depends(get_session)):
    inv = session.exec(select(models.Invitation).where(models.Invitation.token == token)).first()
    if not inv:
        return HTMLResponse("<h1>❌ Invalid or expired invitation</h1>", status_code=404)

    return HTMLResponse("<h1>⏳ You requested more time. The inviter has been notified.</h1>")


# ===============================
# TASKS
# ===============================
@app.post("/groups/{group_id}/tasks")
def create_task(group_id: int, task: schemas.TaskCreate, session: Session = Depends(get_session)):
    group = session.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    t = crud.create_task(session, group, task.title, task.description, assignee_email=task.assignee_email)
    return {"task": t}
