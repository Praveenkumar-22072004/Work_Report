from sqlmodel import Session, select
from .models import User, Group, Invitation, Task
from .email_utils import send_email
import secrets


def get_or_create_user(session: Session, email: str, full_name: str = None):
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        return user
    user = User(email=email, full_name=full_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_group(session: Session, name: str, description: str, creator_email: str):
    group = Group(name=name, description=description)
    session.add(group)
    session.commit()
    session.refresh(group)

    # add creator as member
    user = get_or_create_user(session, creator_email)
    group.members.append(user)
    session.add(group)
    session.commit()
    return group


def invite_member(session: Session, group: Group, email: str, backend_url: str):
    """Create an invitation and email a unique accept link"""
    token = secrets.token_urlsafe(16)
    inv = Invitation(group_id=group.id, email=email, token=token, status="pending")
    session.add(inv)
    session.commit()
    session.refresh(inv)

    # ✅ Build invite link safely
    link = f"{backend_url.rstrip('/')}/backend/invites/accept/{inv.token}"

    subject = f"You're invited to join group '{group.name}'"
    html = (
        f"<p>Hello,</p>"
        f"<p>You were invited to join the group <b>{group.name}</b>.</p>"
        f"<p>Description: {group.description or ''}</p>"
        f"<p>To accept, click here: <a href='{link}'>{link}</a></p>"
    )
    send_email(email, subject, html)
    return inv


def accept_invitation(session: Session, token: str, user_email: str = None):
    inv = session.exec(select(Invitation).where(Invitation.token == token)).first()
    if not inv:
        return None

    # fallback: use email from invitation
    if not user_email:
        user_email = inv.email

    inv.status = "accepted"
    user = get_or_create_user(session, user_email)
    group = session.get(Group, inv.group_id)

    if user not in group.members:
        group.members.append(user)

    session.add(inv)
    session.add(group)
    session.commit()
    session.refresh(group)

    # ✅ Notify group creator (first member assumed to be creator)
    if group.members:
        creator = group.members[0]
        subject = f"{user.email} accepted your invitation to '{group.name}'"
        html = (
            f"<p>Hello {creator.full_name or creator.email},</p>"
            f"<p><b>{user.email}</b> has accepted your invitation to join "
            f"<b>{group.name}</b>.</p>"
        )
        send_email(creator.email, subject, html)

    return group, user_email


def create_task(session: Session, group: Group, title: str, description: str, assignee_email: str = None):
    assignee = None
    if assignee_email:
        assignee = get_or_create_user(session, assignee_email)

    task = Task(
        title=title,
        description=description,
        group_id=group.id,
        assignee_email=assignee.email if assignee else None,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # send email if assigned
    if assignee:
        subject = f"New task in group '{group.name}': {title}"
        html = (
            f"<p>You were assigned a task in group <b>{group.name}</b>.</p>"
            f"<p>Group description: {group.description or ''}</p>"
            f"<p>Task: <b>{title}</b></p>"
            f"<p>Description: {description or ''}</p>"
        )
        send_email(assignee.email, subject, html)

    return task
