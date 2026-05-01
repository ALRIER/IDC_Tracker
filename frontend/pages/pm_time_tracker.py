import streamlit as st
import requests
import pandas as pd
from datetime import date

def show(API_URL, headers):
    st.title("⏱ Time Tracker")
    st.caption("Project milestone tracking — PMs only")

    # Load projects
    with st.spinner("Loading projects..."):
        try:
            r = requests.get(f"{API_URL}/projects/", headers=headers)
            projects = r.json()
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            return

    # Tabs — View all vs Add new
    tab1, tab2 = st.tabs(["📋 All Projects", "➕ Add New Project"])

    # ── Tab 1: View and edit projects ──────────────────────────
    with tab1:
        if not projects:
            st.info("No projects yet. Add one in the tab above!")
        else:
            # Summary metrics
            active = [p for p in projects if p.get("status") == "Active"]
            closed = [p for p in projects if p.get("status") == "Closed"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Projects", len(projects))
            col2.metric("Active", len(active))
            col3.metric("Closed", len(closed))

            st.divider()

            # Filter
            status_filter = st.radio(
                "Show", ["Active", "Closed", "All"],
                horizontal=True
            )

            filtered = projects
            if status_filter != "All":
                filtered = [p for p in projects if p.get("status") == status_filter]

            st.write(f"Showing **{len(filtered)}** projects")

            # Display each project
            for p in filtered:
                completed = p.get("interviews_complete", 0)
                target = p.get("interviews_target", 8)
                pct = int((completed / target * 100)) if target else 0

                with st.expander(
                    f"📁 {p.get('project_name', '')} | "
                    f"{p.get('project_number', '')} | "
                    f"{p.get('status', '')} | "
                    f"Progress: {completed}/{target} ({pct}%)"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("### Project Info")
                        st.write(f"**Project Name:** {p.get('project_name', '')}")
                        st.write(f"**Project Number:** {p.get('project_number', '')}")
                        st.write(f"**Type:** {p.get('project_type', '')}")
                        st.write(f"**BV Lead:** {p.get('bv_lead', '')}")
                        st.write(f"**IDC PM (BVD):** {p.get('bvd', '')}")
                        st.write(f"**Target Interviews:** {target}")
                        st.write(f"**Completed:** {completed}")
                        st.progress(pct / 100)

                    with col2:
                        st.write("### Update Project")

                        new_status = st.selectbox(
                            "Status",
                            ["Active", "Closed"],
                            index=0 if p.get("status") == "Active" else 1,
                            key=f"pstatus_{p['id']}"
                        )

                        new_bv_lead = st.text_input(
                            "BV Lead",
                            value=p.get("bv_lead") or "",
                            key=f"bvlead_{p['id']}"
                        )

                        new_bvd = st.text_input(
                            "IDC PM (BVD)",
                            value=p.get("bvd") or "",
                            key=f"bvd_{p['id']}"
                        )

                        new_target = st.number_input(
                            "Target Interviews",
                            value=target,
                            min_value=1,
                            max_value=50,
                            key=f"target_{p['id']}"
                        )

                        new_notes = st.text_area(
                            "Notes / Status",
                            value=p.get("notes_status") or "",
                            key=f"pnotes_{p['id']}"
                        )

                    st.write("### 📅 Milestone Dates")
                    date_cols = st.columns(3)

                    milestone_fields = [
                        ("booking_date", "Booking Date"),
                        ("kickoff_date", "Kickoff Date"),
                        ("briefing_date", "Briefing Date"),
                        ("ig_draft_from_bv", "IG Draft from BV"),
                        ("ig_draft_to_client", "IG Draft to Client"),
                        ("ig_approved", "IG Approved"),
                        ("first_contact_date", "First Contact"),
                        ("interviews_complete_date", "Interviews Complete"),
                        ("results_presentation_date", "Results Presentation"),
                        ("results_approval_date", "Results Approval"),
                        ("wp_draft_from_bv", "WP Draft from BV"),
                        ("wp_draft_to_client", "WP Draft to Client"),
                        ("wp_v1_feedback", "WP V1 Feedback"),
                        ("client_approval", "Client Approval"),
                        ("to_editing", "To Editing"),
                        ("from_editing", "From Editing"),
                        ("graphical_uplift", "Graphical Uplift"),
                        ("to_client_final_approval", "To Client Final Approval"),
                        ("publication_date", "Publication Date"),
                    ]

                    date_values = {}
                    for i, (field, label) in enumerate(milestone_fields):
                        with date_cols[i % 3]:
                            existing = p.get(field)
                            date_values[field] = st.date_input(
                                label,
                                value=pd.to_datetime(existing).date()
                                if existing else None,
                                key=f"{field}_{p['id']}"
                            )

                    if st.button("💾 Save Project", key=f"psave_{p['id']}"):
                        payload = {
                            "status": new_status,
                            "bv_lead": new_bv_lead,
                            "bvd": new_bvd,
                            "interviews_target": new_target,
                            "notes_status": new_notes,
                        }
                        for field, _ in milestone_fields:
                            v = date_values[field]
                            payload[field] = str(v) if v else None

                        try:
                            r = requests.patch(
                                f"{API_URL}/projects/{p['id']}",
                                json=payload,
                                headers=headers
                            )
                            if r.status_code == 200:
                                st.success("✅ Project saved!")
                                st.rerun()
                            else:
                                st.error(f"Error: {r.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ── Tab 2: Add new project ──────────────────────────────────
    with tab2:
        st.write("### Add New Project")

        with st.form("new_project_form"):
            col1, col2 = st.columns(2)

            with col1:
                project_name = st.text_input("Project Name *")
                project_number = st.text_input("Project Number *")
                project_type = st.selectbox("Project Type", ["WP", "SB"])
                bv_lead = st.text_input("BV Lead")

            with col2:
                bvd = st.text_input("IDC PM (BVD)")
                interviews_target = st.number_input(
                    "Target Interviews", value=8, min_value=1
                )
                notes = st.text_area("Notes")

            submit = st.form_submit_button(
                "➕ Create Project", use_container_width=True
            )

            if submit:
                if not project_name or not project_number:
                    st.error("Project Name and Number are required!")
                else:
                    payload = {
                        "project_name": project_name,
                        "project_number": project_number,
                        "project_type": project_type,
                        "bv_lead": bv_lead,
                        "bvd": bvd,
                        "interviews_target": interviews_target,
                        "notes_status": notes,
                        "status": "Active"
                    }
                    try:
                        r = requests.post(
                            f"{API_URL}/projects/",
                            json=payload,
                            headers=headers
                        )
                        if r.status_code == 200:
                            st.success("✅ Project created!")
                            st.rerun()
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")