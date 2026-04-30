from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Project
from auth import get_current_user, require_role
from pydantic import BaseModel
from datetime import date

router = APIRouter()

class ProjectCreate(BaseModel):
    project_number: str
    project_name: str
    project_type: Optional[str] = None
    status: Optional[str] = "Active"
    bv_lead: Optional[str] = None
    bvd: Optional[str] = None
    interviews_target: Optional[int] = 8
    notes_status: Optional[str] = None
    booking_date: Optional[date] = None
    kickoff_date: Optional[date] = None
    briefing_date: Optional[date] = None
    ig_draft_from_bv: Optional[date] = None
    ig_draft_to_client: Optional[date] = None
    ig_approved: Optional[date] = None
    first_contact_date: Optional[date] = None
    interviews_complete_date: Optional[date] = None
    results_presentation_date: Optional[date] = None
    results_approval_date: Optional[date] = None
    wp_draft_from_bv: Optional[date] = None
    wp_draft_to_client: Optional[date] = None
    wp_v1_feedback: Optional[date] = None
    client_approval: Optional[date] = None
    to_editing: Optional[date] = None
    from_editing: Optional[date] = None
    graphical_uplift: Optional[date] = None
    to_client_final_approval: Optional[date] = None
    publication_date: Optional[date] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    bv_lead: Optional[str] = None
    bvd: Optional[str] = None
    interviews_target: Optional[int] = None
    notes_status: Optional[str] = None
    booking_date: Optional[date] = None
    kickoff_date: Optional[date] = None
    briefing_date: Optional[date] = None
    ig_draft_from_bv: Optional[date] = None
    ig_draft_to_client: Optional[date] = None
    ig_approved: Optional[date] = None
    first_contact_date: Optional[date] = None
    interviews_complete_date: Optional[date] = None
    results_presentation_date: Optional[date] = None
    results_approval_date: Optional[date] = None
    wp_draft_from_bv: Optional[date] = None
    wp_draft_to_client: Optional[date] = None
    wp_v1_feedback: Optional[date] = None
    client_approval: Optional[date] = None
    to_editing: Optional[date] = None
    from_editing: Optional[date] = None
    graphical_uplift: Optional[date] = None
    to_client_final_approval: Optional[date] = None
    publication_date: Optional[date] = None

@router.get("/")
def get_projects(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role == "admin":
        return db.query(Project).all()
    elif current_user.role in ("pm", "analyst"):
        return db.query(Project).filter(Project.status == "Active").all()
    else:
        return db.query(Project).filter(Project.status == "Active").all()

@router.get("/{project_id}")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", dependencies=[Depends(require_role("pm", "admin"))])
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    existing = db.query(Project).filter(Project.project_number == data.project_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project number already exists")

    project = Project(**data.dict())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.patch("/{project_id}", dependencies=[Depends(require_role("pm", "admin"))])
def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", dependencies=[Depends(require_role("admin"))])
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}