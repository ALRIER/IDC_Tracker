import streamlit as st
import requests

API_URL = "https://idc-tracker-y0yo.onrender.com"

# ─────────────────────────────────────────────────────────────
# TEMPORARY DEMO PRIVACY MODE
# Frontend-only masking. Does NOT delete or modify database data.
# Turn off by changing True to False.
# ─────────────────────────────────────────────────────────────
DEMO_PRIVACY_MODE = True
MASK_INTERNAL_NAMES = False  # Set True to hide BV Lead / IDC PM / Interviewer names too


def redact_value(key, value, row=None):
    row = row or {}
    project_number = row.get("project_number") or row.get("Project #") or "XXXXX"

    if not DEMO_PRIVACY_MODE:
        return value

    sensitive_blank = {
        "interviewee_email",
        "interviewee_phone",
        "scheduling_link",
        "interviewer_notes",
        "notes_status",
        "notes",
    }

    sensitive_contact = {
        "interviewee_name",
        "name",
    }

    sensitive_title = {
        "interviewee_title",
        "title",
    }

    sensitive_company = {
        "interviewed_org_name",
        "org_name",
        "company",
        "company_name",
        "organisation",
        "organization",
    }

    project_name_fields = {
        "project_name",
    }

    internal_name_fields = {
        "bv_lead",
        "bvd",
        "idc_project_manager",
        "bv_project_manager",
        "interviewer",
    }

    if key in sensitive_blank:
        return ""

    if key in sensitive_contact:
        return "Redacted Contact"

    if key in sensitive_title:
        return "Redacted Title"

    if key in sensitive_company:
        return "Redacted Organisation"

    if key in project_name_fields:
        return f"Project {project_number}"

    if key == "projects":
        return ["Redacted Project List"]

    if MASK_INTERNAL_NAMES and key in internal_name_fields:
        return "Internal User"

    return value


def redact_obj(obj):
    if not DEMO_PRIVACY_MODE:
        return obj

    if isinstance(obj, list):
        return [redact_obj(item) for item in obj]

    if isinstance(obj, dict):
        redacted = {}

        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                redacted[key] = redact_obj(value)
            else:
                redacted[key] = redact_value(key, value, obj)

        return redacted

    return obj


_original_get = requests.get


def masked_get(*args, **kwargs):
    response = _original_get(*args, **kwargs)
    original_json = response.json

    def safe_json():
        data = original_json()
        return redact_obj(data)

    response.json = safe_json
    return response


if DEMO_PRIVACY_MODE:
    requests.get = masked_get


st.set_page_config(
    page_title="IDC BV Tracker",
    page_icon="",
    layout="wide"
)


def login(email, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": email, "password": password}
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("IDC BV Tracker")
        st.subheader("Sign in to your account")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button(
                "Sign In",
                use_container_width=True
            )

            if submit:
                if not email or not password:
                    st.error("Please enter email and password")
                else:
                    with st.spinner("Signing in..."):
                        result = login(email, password)

                        if result:
                            st.session_state.token = result["access_token"]
                            st.session_state.user = result["user"]
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error("Invalid email or password")


def show_sidebar():
    with st.sidebar:
        st.write(f"**{st.session_state.user['name']}**")
        st.write(f"Role: `{st.session_state.user['role']}`")
        st.divider()
        st.write("**Navigation**")

        role = st.session_state.user["role"]

        if role == "pm":
            page = st.radio(
                "",
                [
                    "⏱ Overall Project Tracker",
                    "Interview Sheet",
                    "Project Progress",
                ],
                label_visibility="collapsed"
            )

        elif role == "interviewer":
            page = st.radio(
                "",
                [
                    "My Interviews",
                ],
                label_visibility="collapsed"
            )

        elif role == "analyst":
            page = st.radio(
                "",
                [
                    "⏱ Overall Project Tracker",
                    "Interview Sheet",
                    "Project Progress",
                    "Dashboard",
                    "By Project",
                    "Projected Readout",
                    "Repeat Organisations",
                ],
                label_visibility="collapsed"
            )

        elif role == "admin":
            page = st.radio(
                "",
                [
                    "⏱ Overall Project Tracker",
                    "Interview Sheet",
                    "Project Progress",
                    "Dashboard",
                    "By Project",
                    "Projected Readout",
                    "Repeat Organisations",
                    "⚙️ Admin Panel",
                ],
                label_visibility="collapsed"
            )

        else:
            page = "⏱ Overall Project Tracker"

        st.divider()

        if DEMO_PRIVACY_MODE:
            st.warning("Demo mode")

        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        return page


def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if not st.session_state.logged_in:
    show_login()

else:
    page = show_sidebar()

    if page == "⏱ Overall Project Tracker":
        from pages_modules import pm_time_tracker
        pm_time_tracker.show(API_URL, get_headers())

    elif page == "Interview Sheet":
        from pages_modules import pm_interview_sheet
        pm_interview_sheet.show(API_URL, get_headers())

    elif page == "Project Progress":
        from pages_modules import project_progress
        project_progress.show(API_URL, get_headers())

    elif page == "My Interviews":
        from pages_modules import interviewer_view
        interviewer_view.show(API_URL, get_headers())

    elif page == "Dashboard":
        from pages_modules import analyst_dashboard
        analyst_dashboard.show(API_URL, get_headers())

    elif page == "By Project":
        from pages_modules import analyst_by_project
        analyst_by_project.show(API_URL, get_headers())

    elif page == "Projected Readout":
        from pages_modules import analyst_readout
        analyst_readout.show(API_URL, get_headers())

    elif page == "Repeat Organisations":
        from pages_modules import analyst_repeat_orgs
        analyst_repeat_orgs.show(API_URL, get_headers())

    elif page == "⚙️ Admin Panel":
        from pages_modules import admin_panel
        admin_panel.show(API_URL, get_headers())