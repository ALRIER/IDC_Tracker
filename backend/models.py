from sqlalchemy import Column, String, Integer, Boolean, Date, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_number = Column(String, nullable=False, unique=True)
    project_name = Column(Text, nullable=False)
    project_type = Column(String)
    status = Column(String, default="Active")
    bv_lead = Column(Text)
    bvd = Column(Text)
    interviews_complete = Column(Integer, default=0)
    interviews_target = Column(Integer, default=8)
    notes_status = Column(Text)
    booking_date = Column(Date)
    kickoff_date = Column(Date)
    briefing_date = Column(Date)
    ig_draft_from_bv = Column(Date)
    ig_draft_to_client = Column(Date)
    ig_approved = Column(Date)
    first_contact_date = Column(Date)
    interviews_complete_date = Column(Date)
    results_presentation_date = Column(Date)
    results_approval_date = Column(Date)
    wp_draft_from_bv = Column(Date)
    wp_draft_to_client = Column(Date)
    wp_v1_feedback = Column(Date)
    client_approval = Column(Date)
    to_editing = Column(Date)
    from_editing = Column(Date)
    graphical_uplift = Column(Date)
    to_client_final_approval = Column(Date)
    publication_date = Column(Date)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    interviews = relationship("Interview", back_populates="project")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    project_number = Column(Text, nullable=False)
    project_name = Column(Text, nullable=False)
    project_status = Column(Text)
    idc_project_manager = Column(Text)
    bv_project_manager = Column(Text)
    scheduling_link = Column(Text)
    recruiting_partner = Column(Text)
    date_provided = Column(Date)
    interviewed_org_name = Column(Text)
    interviewee_name = Column(Text)
    interviewee_title = Column(Text)
    interviewee_email = Column(Text)
    interviewee_phone = Column(Text)
    country = Column(Text)
    industry = Column(Text)
    interview_status = Column(Text, default="Not Contacted")
    date_of_interview = Column(Date)
    interview_quality = Column(Text)
    last_date_of_contact = Column(Date)
    number_of_attempts = Column(Integer, default=0)
    interviewer_notes = Column(Text)
    interviewer = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="interviews")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    interviewer_name = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Dropdown(Base):
    __tablename__ = "dropdowns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)