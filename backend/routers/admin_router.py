from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, Dropdown
from auth import get_current_user, require_role, hash_password
from pydantic import BaseModel

router = APIRouter()

# ── User Management ──────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    interviewer_name: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    interviewer_name: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/dropdowns")
def get_dropdowns(db: Session = Depends(get_db), current_user = Depends(get_current_user)):

@router.post("/users", dependencies=[Depends(require_role("admin"))])
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    if data.role not in ("pm", "interviewer", "analyst", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        interviewer_name=data.interviewer_name,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": f"User {user.name} created successfully", "id": str(user.id)}

@router.patch("/users/{user_id}", dependencies=[Depends(require_role("admin"))])
def update_user(user_id: str, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return {"message": f"User {user.name} updated successfully"}

@router.delete("/users/{user_id}", dependencies=[Depends(require_role("admin"))])
def deactivate_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Never hard delete — just deactivate
    user.is_active = False
    db.commit()
    return {"message": f"User {user.name} deactivated"}


# ── Dropdown Management ───────────────────────────────────────

class DropdownCreate(BaseModel):
    category: str
    value: str
    sort_order: Optional[int] = 0

class DropdownUpdate(BaseModel):
    value: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

@router.get("/dropdowns", dependencies=[Depends(require_role("admin"))])
def get_dropdowns(db: Session = Depends(get_db)):
    return db.query(Dropdown).order_by(
        Dropdown.category, Dropdown.sort_order
    ).all()

@router.post("/dropdowns", dependencies=[Depends(require_role("admin"))])
def create_dropdown(data: DropdownCreate, db: Session = Depends(get_db)):
    existing = db.query(Dropdown).filter(
        Dropdown.category == data.category,
        Dropdown.value == data.value
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Value already exists in this category")

    dropdown = Dropdown(**data.dict())
    db.add(dropdown)
    db.commit()
    db.refresh(dropdown)
    return {"message": f"'{data.value}' added to {data.category}"}

@router.patch("/dropdowns/{dropdown_id}", dependencies=[Depends(require_role("admin"))])
def update_dropdown(
    dropdown_id: str,
    data: DropdownUpdate,
    db: Session = Depends(get_db)
):
    dropdown = db.query(Dropdown).filter(Dropdown.id == dropdown_id).first()
    if not dropdown:
        raise HTTPException(status_code=404, detail="Dropdown not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(dropdown, field, value)

    db.commit()
    return {"message": "Dropdown updated"}

@router.delete("/dropdowns/{dropdown_id}", dependencies=[Depends(require_role("admin"))])
def delete_dropdown(dropdown_id: str, db: Session = Depends(get_db)):
    dropdown = db.query(Dropdown).filter(Dropdown.id == dropdown_id).first()
    if not dropdown:
        raise HTTPException(status_code=404, detail="Dropdown not found")
    db.delete(dropdown)
    db.commit()
    return {"message": "Dropdown deleted"}