import streamlit as st
import requests
import os

API_URL = "https://idc-tracker-y0yo.onrender.com"

st.set_page_config(
    page_title="IDC BV Tracker",
    page_icon="📊",
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
        st.image("https://www.idc.com/img/idc-logo.svg", width=150)
        st.title("BV Tracker")
        st.subheader("Sign in to your account")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
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
        st.write(f"👤 **{st.session_state.user['name']}**")
        st.write(f"Role: `{st.session_state.user['role']}`")
        st.divider()
        
        role = st.session_state.user["role"]
        
        if role == "pm":
            page = st.radio("Navigation", [
                "⏱ Time Tracker",
                "👥 Interview Sheet"
            ])
        elif role == "interviewer":
            page = st.radio("Navigation", [
                "📋 My Interviews"
            ])
        elif role == "analyst":
            page = st.radio("Navigation", [
                "📊 Dashboard",
                "📁 By Project",
                "📅 Projected Readout",
                "🔄 Repeat Organisations"
            ])
        elif role == "admin":
            page = st.radio("Navigation", [
                "⏱ Time Tracker",
                "👥 Interview Sheet",
                "📊 Dashboard",
                "📁 By Project",
                "📅 Projected Readout",
                "🔄 Repeat Organisations",
                "⚙️ Admin Panel"
            ])
        
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        return page

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

# ── Main app logic ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_login()
else:
    page = show_sidebar()
    
    if page == "⏱ Time Tracker":
        from pages import pm_time_tracker
        pm_time_tracker.show(API_URL, get_headers())
    
    elif page == "👥 Interview Sheet":
        from pages import pm_interview_sheet
        pm_interview_sheet.show(API_URL, get_headers())
    
    elif page == "📋 My Interviews":
        from pages import interviewer_view
        interviewer_view.show(API_URL, get_headers())
    
    elif page == "📊 Dashboard":
        from pages import analyst_dashboard
        analyst_dashboard.show(API_URL, get_headers())
    
    elif page == "📁 By Project":
        from pages import analyst_by_project
        analyst_by_project.show(API_URL, get_headers())
    
    elif page == "📅 Projected Readout":
        from pages import analyst_readout
        analyst_readout.show(API_URL, get_headers())
    
    elif page == "🔄 Repeat Organisations":
        from pages import analyst_repeat_orgs
        analyst_repeat_orgs.show(API_URL, get_headers())
    
    elif page == "⚙️ Admin Panel":
        from pages import admin_panel
        admin_panel.show(API_URL, get_headers())