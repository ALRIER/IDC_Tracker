import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import auth_router, projects_router, interviews_router, dashboard_router, admin_router

load_dotenv()

app = FastAPI(
    title="BV Tracker API",
    description="IDC Business Value Interview Tracking System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects_router.router, prefix="/projects", tags=["Projects"])
app.include_router(interviews_router.router, prefix="/interviews", tags=["Interviews"])
app.include_router(dashboard_router.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(admin_router.router, prefix="/admin", tags=["Admin"])

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "BV Tracker API is running"}

@app.get("/")
def root():
    return {"message": "Welcome to BV Tracker API"}