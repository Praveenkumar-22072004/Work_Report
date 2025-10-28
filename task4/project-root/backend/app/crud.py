from sqlalchemy.orm import Session
from . import models, auth
from typing import Optional

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, username: str, email: str, password: str):
    hashed = auth.hash_password(password)
    user = models.User(username=username, email=email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, identifier: str, password: str):
    user = get_user_by_email(db, identifier) if "@" in identifier else get_user_by_username(db, identifier)
    if not user:
        return None
    if not auth.verify_password(password, user.hashed_password):
        return None
    return user

# Members CRUD
def list_members(db: Session):
    return db.query(models.Member).order_by(models.Member.id.desc()).all()

def create_member(db: Session, name:str, email:str, phone:Optional[str]=None, organization:Optional[str]=None):
    m = models.Member(name=name, email=email, phone=phone, organization=organization)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

def update_member(db: Session, member_id:int, **data):
    m = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not m:
        return None
    for k,v in data.items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m

def delete_member(db: Session, member_id:int):
    m = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not m:
        return False
    db.delete(m)
    db.commit()
    return True
