from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import Interview, Project
from auth import get_current_user, require_role
from pydantic import BaseModel
from datetime import date

router = APIRouter()


class InterviewCreate(BaseModel):
    project_id: str
    project_number: str
    project_name: str
    project_status: Optional[str] = None
    idc_project_manager: Optional[str] = None
    bv_project_manager: Optional[str] = None
    scheduling_link: Optional[str] = None
    recruiting_partner: Optional[str] = None
    date_provided: Optional[date] = None
    interviewed_org_name: Optional[str] = None
    interviewee_name: Optional[str] = None
    interviewee_title: Optional[str] = None
    interviewee_email: Optional[str] = None
    interviewee_phone: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    interview_status: Optional[str] = "Not Contacted"
    date_of_interview: Optional[date] = None
    interview_quality: Optional[str] = None
    last_date_of_contact: Optional[date] = None
    number_of_attempts: Optional[int] = 0
    interviewer_notes: Optional[str] = None
    interviewer: str


class InterviewUpdateFull(BaseModel):
    project_status: Optional[str] = None
    idc_project_manager: Optional[str] = None
    bv_project_manager: Optional[str] = None
    scheduling_link: Optional[str] = None
    recruiting_partner: Optional[str] = None
    date_provided: Optional[date] = None
    interviewed_org_name: Optional[str] = None
    interviewee_name: Optional[str] = None
    interviewee_title: Optional[str] = None
    interviewee_email: Optional[str] = None
    interviewee_phone: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    interview_status: Optional[str] = None
    date_of_interview: Optional[date] = None
    interview_quality: Optional[str] = None
    last_date_of_contact: Optional[date] = None
    number_of_attempts: Optional[int] = None
    interviewer_notes: Optional[str] = None
    interviewer: Optional[str] = None


class InterviewUpdateRestricted(BaseModel):
    interview_status: Optional[str] = None
    date_of_interview: Optional[date] = None
    interview_quality: Optional[str] = None
    interviewer_notes: Optional[str] = None


@router.get("/")
def get_interviews(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Interview)

    # Interviewers only see their own assigned rows.
    # Analysts, PMs, and Admins see all rows for full audit visibility.
    if current_user.role == "interviewer":
        query = query.filter(
            Interview.interviewer == current_user.interviewer_name
        )

    if project_id:
        query = query.filter(Interview.project_id == project_id)

    return query.order_by(
        Interview.project_name,
        Interview.interviewee_name
    ).all()


@router.get("/{interview_id}")
def get_interview(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id)
        .first()
    )

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if current_user.role == "interviewer":
        if interview.interviewer != current_user.interviewer_name:
            raise HTTPException(status_code=403, detail="Access denied")

    return interview


@router.post("/", dependencies=[Depends(require_role("pm", "admin", "analyst"))])
def create_interview(
    data: InterviewCreate,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == data.project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    interview = Interview(**data.dict())
    db.add(interview)
    db.commit()
    db.refresh(interview)

    return interview


@router.patch("/{interview_id}")
def update_interview(
    interview_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id)
        .first()
    )

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if current_user.role == "interviewer":
        if interview.interviewer != current_user.interviewer_name:
            raise HTTPException(status_code=403, detail="Access denied")

        allowed_fields = {
            "interview_status",
            "date_of_interview",
            "interview_quality",
            "interviewer_notes",
        }

        data = {
            k: v for k, v in data.items()
            if k in allowed_fields
        }

    # PM, Admin, and Analyst can update all interview fields.
    for field, value in data.items():
        setattr(interview, field, value)

    db.commit()
    db.refresh(interview)

    return interview


@router.delete("/{interview_id}", dependencies=[Depends(require_role("pm", "admin", "analyst"))])
def delete_interview(
    interview_id: str,
    db: Session = Depends(get_db)
):
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id)
        .first()
    )

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    db.delete(interview)
    db.commit()

    return {"message": "Interview deleted"}