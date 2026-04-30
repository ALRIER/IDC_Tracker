from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from database import get_db
from models import Interview, Project
from auth import get_current_user, require_role

router = APIRouter()

@router.get("/summary")
def get_program_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    total = db.query(func.count(Interview.id)).scalar()
    completed = db.query(func.count(Interview.id)).filter(
        Interview.interview_status == "Completed").scalar()
    scheduled = db.query(func.count(Interview.id)).filter(
        Interview.interview_status.in_(["Scheduled", "Being Rescheduled"])).scalar()
    no_low_response = db.query(func.count(Interview.id)).filter(
        Interview.interview_status.in_(["No Show", "On Hold", "Contacted", "Not Contacted"])).scalar()
    cancelled = db.query(func.count(Interview.id)).filter(
        Interview.interview_status == "Cancelled").scalar()

    return {
        "total_interviewees": total,
        "completed": completed,
        "scheduled_in_progress": scheduled,
        "no_low_response": no_low_response,
        "cancelled": cancelled
    }

@router.get("/by-interviewer")
def get_by_interviewer(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    results = db.query(
        Interview.interviewer,
        func.count(Interview.id).label("total"),
        func.count(case((Interview.interview_status == "Completed", 1))).label("completed"),
        func.count(case((Interview.interview_status == "Scheduled", 1))).label("scheduled"),
        func.count(case((Interview.interview_status == "Being Rescheduled", 1))).label("being_rescheduled"),
        func.count(case((Interview.interview_status.in_(
            ["No Show", "On Hold", "Contacted", "Not Contacted"]), 1))).label("no_low_response"),
        func.count(case((Interview.interview_status == "Cancelled", 1))).label("cancelled"),
    ).group_by(Interview.interviewer).order_by(Interview.interviewer).all()

    return [
        {
            "interviewer": r.interviewer,
            "total": r.total,
            "completed": r.completed,
            "scheduled": r.scheduled,
            "being_rescheduled": r.being_rescheduled,
            "no_low_response": r.no_low_response,
            "cancelled": r.cancelled
        }
        for r in results
    ]

@router.get("/by-project")
def get_by_project(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    results = db.query(
        Project.project_number,
        Project.project_name,
        Project.bvd.label("idc_pm"),
        Project.bv_lead,
        Project.interviews_target,
        func.count(Interview.id).label("total_interviews"),
        func.count(case((Interview.interview_status == "Completed", 1))).label("completed_interviews"),
    ).outerjoin(Interview, Interview.project_id == Project.id)\
     .filter(Project.status == "Active")\
     .group_by(
        Project.id,
        Project.project_number,
        Project.project_name,
        Project.bvd,
        Project.bv_lead,
        Project.interviews_target
     ).order_by(Project.project_name).all()

    return [
        {
            "project_number": r.project_number,
            "project_name": r.project_name,
            "idc_pm": r.idc_pm,
            "bv_lead": r.bv_lead,
            "interviews_target": r.interviews_target,
            "total_interviews": r.total_interviews,
            "completed_interviews": r.completed_interviews,
            "pct_complete": round(
                (r.completed_interviews / r.interviews_target * 100)
                if r.interviews_target else 0, 1
            )
        }
        for r in results
    ]

@router.get("/repeat-orgs")
def get_repeat_orgs(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    results = db.query(
        Interview.interviewed_org_name,
        func.count(func.distinct(Interview.project_number)).label("project_count"),
        func.array_agg(func.distinct(Interview.project_name)).label("projects")
    ).filter(Interview.interviewed_org_name != None)\
     .group_by(Interview.interviewed_org_name)\
     .having(func.count(func.distinct(Interview.project_number)) > 1)\
     .order_by(func.count(func.distinct(Interview.project_number)).desc())\
     .all()

    return [
        {
            "org_name": r.interviewed_org_name,
            "project_count": r.project_count,
            "projects": r.projects
        }
        for r in results
    ]

@router.get("/timeline-summary")
def get_timeline_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    projects = db.query(Project).filter(Project.status == "Active").all()

    summary = []
    for p in projects:
        if p.booking_date and p.kickoff_date:
            bkg_to_ko = (p.kickoff_date - p.booking_date).days / 7
            summary.append({
                "project_number": p.project_number,
                "project_name": p.project_name,
                "booking_to_kickoff_weeks": round(bkg_to_ko, 1)
            })

    return summary