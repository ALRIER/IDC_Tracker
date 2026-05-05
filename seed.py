import requests
import pandas as pd
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Config ─────────────────────────────────────────────────────
API_URL = "https://idc-tracker-y0yo.onrender.com"
ADMIN_EMAIL = "alvaro.rivera-eraso@idc.com"
ADMIN_PASSWORD = "Admin2026"
FILES_DIR = r"C:\Users\AlvaroRivera-Eraso\bv-tracker\excelTrackers"

INTERVIEWER_FILES = {
    "Terra":    "BV_Tracker_Terra.xlsx",
    "Alvaro":   "BV_Tracker_Alvaro.xlsx",
    "Ramona":   "BV_Tracker_Ramona.xlsx",
    "Tom":      "BV_Tracker_Tom.xlsx",
    "Patricia": "BV_Tracker_Patricia.xlsx",
    "Sherri":   "BV_Tracker_Sherri.xlsx",
}

MASTER_FILE = "BV_Master_Tracker_Final.xlsx"

# Use a session with SSL verification disabled (corporate VPN fix)
session = requests.Session()
session.verify = False

# ── Step 1: Login ───────────────────────────────────────────────
print("🔐 Logging in...")
r = session.post(
    f"{API_URL}/auth/login",
    data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
)
if r.status_code != 200:
    print(f"❌ Login failed: {r.text}")
    exit()

token = r.json()["access_token"]
session.headers.update({"Authorization": f"Bearer {token}"})
print("✅ Logged in successfully!")

# ── Helpers ─────────────────────────────────────────────────────
def clean_date(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except:
        pass
    try:
        return pd.to_datetime(val).strftime("%Y-%m-%d")
    except:
        return None

def clean_str(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except:
        pass
    s = str(val).strip()
    return s if s and s.lower() not in ("nan", "none", "") else None

# ── Step 2: Load Projects from Master Tracker ───────────────────
print("\n📁 Loading projects from Master Tracker...")

master_path = os.path.join(FILES_DIR, MASTER_FILE)
try:
    df_projects = pd.read_excel(
        master_path,
        sheet_name="Project Tracker",
        header=3
    )
    print(f"   Found {len(df_projects)} rows in Project Tracker")
    print(f"   Columns: {list(df_projects.columns[:10])}")
except Exception as e:
    print(f"❌ Error reading master file: {e}")
    exit()

projects_created = 0
projects_skipped = 0
project_map = {}

for _, row in df_projects.iterrows():
    project_number = clean_str(
        row.get("Project Number") or
        row.get("Project No") or
        row.get("Project #") or
        row.get("Proj #")
    )
    project_name = clean_str(
        row.get("Project Name") or
        row.get("Project")
    )

    if not project_number or not project_name:
        continue

    payload = {
        "project_number": project_number,
        "project_name": project_name,
        "project_type": clean_str(row.get("Type")),
        "status": "Active",
        "bv_lead": clean_str(
            row.get("BV Lead") or row.get("BV Project Manager")
        ),
        "bvd": clean_str(
            row.get("BVD") or
            row.get("IDC PM") or
            row.get("Project Manager")
        ),
        "interviews_target": int(row.get("Target", 8))
	if str(row.get("Target", 8)).strip() not in ("", "-", "nan", "None")
	else 8,
        "notes_status": clean_str(
            row.get("Notes") or row.get("Status")
        ),
        "booking_date": clean_date(
            row.get("Booking Date") or row.get("Booking")
        ),
        "kickoff_date": clean_date(
            row.get("Kickoff Date") or row.get("Kickoff")
        ),
        "briefing_date": clean_date(
            row.get("Briefing Date") or row.get("Briefing")
        ),
        "publication_date": clean_date(
            row.get("Publication Date") or row.get("Publication")
        ),
    }

    r = session.post(f"{API_URL}/projects/", json=payload)

    if r.status_code == 200:
        project_id = r.json()["id"]
        project_map[project_number] = project_id
        projects_created += 1
        print(f"   ✅ Created: {project_name} ({project_number})")
    elif "already exists" in r.text:
        existing = session.get(f"{API_URL}/projects/").json()
        for p in existing:
            if p["project_number"] == project_number:
                project_map[project_number] = p["id"]
                break
        projects_skipped += 1
        print(f"   ⏭ Skipped (exists): {project_number}")
    else:
        print(f"   ⚠️ Error for {project_number}: {r.text[:100]}")

print(f"\n   Projects created: {projects_created}")
print(f"   Projects skipped: {projects_skipped}")

# ── Step 3: Load Interviews ──────────────────────────────────────
print("\n👥 Loading interviews from individual trackers...")

interviews_created = 0
interviews_skipped = 0

# Cache all projects once
all_projects = session.get(f"{API_URL}/projects/").json()

for interviewer_name, filename in INTERVIEWER_FILES.items():
    filepath = os.path.join(FILES_DIR, filename)

    if not os.path.exists(filepath):
        print(f"   ⚠️ File not found: {filename} — skipping")
        continue

    print(f"\n   📄 Processing {filename}...")

    try:
        df = pd.read_excel(filepath, sheet_name="Contacts", header=0)
        print(f"      Columns: {list(df.columns[:10])}")
        print(f"      Found {len(df)} rows")
    except Exception as e:
        print(f"      ❌ Error reading {filename}: {e}")
        continue

    for _, row in df.iterrows():
        project_number = clean_str(
            row.get("Project Number") or
            row.get("Project No") or
            row.get("Project #") or
            row.get("Proj #")
        )
        project_name = clean_str(
            row.get("Project Name") or
            row.get("Project")
        )

        if not project_number and not project_name:
            continue

        # Find project_id from cache
        project_id = project_map.get(project_number)
        project_details = {}

        if not project_id:
            for p in all_projects:
                if project_number and p["project_number"] == project_number:
                    project_id = p["id"]
                    project_map[project_number] = project_id
                    project_details = p
                    break
                elif project_name and p["project_name"] == project_name:
                    project_id = p["id"]
                    project_details = p
                    break
        else:
            project_details = next(
                (p for p in all_projects if p["id"] == project_id), {}
            )

        if not project_id:
            print(f"      ⚠️ Project not found: "
                  f"{project_number} / {project_name} — skipping")
            continue

        payload = {
            "project_id": project_id,
            "project_number": project_number or
                              project_details.get("project_number", ""),
            "project_name": project_name or
                           project_details.get("project_name", ""),
            "project_status": clean_str(row.get("Project Status")),
            "idc_project_manager": clean_str(
                row.get("IDC Project Manager") or
                row.get("IDC PM") or
                project_details.get("bvd")
            ),
            "bv_project_manager": clean_str(
                row.get("BV Project Manager") or
                row.get("BV PM") or
                project_details.get("bv_lead")
            ),
            "scheduling_link": clean_str(row.get("Scheduling Link")),
            "recruiting_partner": clean_str(
                row.get("Recruiting Partner") or row.get("Partner")
            ),
            "date_provided": clean_date(
                row.get("Date Provided") or row.get("Date Added")
            ),
            "interviewed_org_name": clean_str(
                row.get("Interviewed Org Name") or
                row.get("Company") or
                row.get("Organisation") or
                row.get("Org Name")
            ),
            "interviewee_name": clean_str(
                row.get("Interviewee Name") or
                row.get("Name") or
                row.get("Contact Name")
            ),
            "interviewee_title": clean_str(
                row.get("Interviewee Title") or
                row.get("Title") or
                row.get("Job Title")
            ),
            "interviewee_email": clean_str(
                row.get("Interviewee Email") or
                row.get("Email")
            ),
            "interviewee_phone": clean_str(
                row.get("Interviewee Phone") or
                row.get("Phone")
            ),
            "country": clean_str(row.get("Country")),
            "industry": clean_str(row.get("Industry")),
            "interview_status": clean_str(
                row.get("Interview Status") or
                row.get("Status")
            ) or "Not Contacted",
            "date_of_interview": clean_date(
                row.get("Date of Interview") or
                row.get("Interview Date")
            ),
            "interview_quality": clean_str(
                row.get("Interview Quality") or
                row.get("Quality")
            ),
            "last_date_of_contact": clean_date(
                row.get("Last Date of Contact")
            ),
            "number_of_attempts": int(row.get("Number of Attempts", 0))
            if not pd.isna(row.get("Number of Attempts", 0)) else 0,
            "interviewer_notes": clean_str(
                row.get("Interviewer Notes") or
                row.get("Notes")
            ),
            "interviewer": clean_str(
                row.get("Interviewer")
            ) or interviewer_name,
        }

        r = session.post(f"{API_URL}/interviews/", json=payload)

        if r.status_code == 200:
            interviews_created += 1
        else:
            interviews_skipped += 1
            if interviews_skipped <= 3:
                print(f"      ⚠️ Skipped: {r.text[:80]}")

    print(f"      Done — interviews created so far: {interviews_created}")

# ── Summary ─────────────────────────────────────────────────────
print("\n" + "="*50)
print("✅ SEED COMPLETE!")
print(f"   Projects created:    {projects_created}")
print(f"   Projects skipped:    {projects_skipped}")
print(f"   Interviews created:  {interviews_created}")
print(f"   Interviews skipped:  {interviews_skipped}")
print("="*50)