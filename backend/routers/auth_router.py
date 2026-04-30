from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import verify_password, create_token

router = APIRouter()

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == form_data.username,
        User.is_active == True
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token({
        "sub": user.email,
        "name": user.name,
        "role": user.role,
        "interviewer_name": user.interviewer_name
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "interviewer_name": user.interviewer_name
        }
    }

@router.get("/me")
def get_me(db: Session = Depends(get_db)):
    return {"message": "Use Authorization header with Bearer token"}