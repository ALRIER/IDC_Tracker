import streamlit as st
import requests
import pandas as pd

def show(API_URL, headers):
    st.title("👥 Interview Sheet")
    st.caption("Add and manage interviewees for your projects")

    # Load projects for dropdown
    with st.spinner("Loading projects..."):
        try:
            r = requests.get(f"{API_URL}/projects/", headers=headers)
            projects = r.json()
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            return

    if not projects:
        st.info("No projects yet. Create one in the Time Tracker first!")
        return

    # Load dropdowns
    def get_dropdown(category):
        try:
            r = requests.get(f"{API_URL}/admin/dropdowns", headers=headers)
            items = r.json()
            return [i["value"] for i in items
                    if i["category"] == category and i["is_active"]]
        except:
            return []

    status_options = get_dropdown("interview_status")
    quality_options = get_dropdown("interview_quality")
    industry_options = get_dropdown("industry")
    country_options = get_dropdown("country")
    recruiting_options = get_dropdown("recruiting_partner")

    # Project selector
    project_map = {
        f"{p['project_name']} ({p['project_number']})": p
        for p in projects
    }
    selected_label = st.selectbox(
        "Select Project", list(project_map.keys())
    )
    selected_project = project_map[selected_label]

    # Load interviews for selected project
    with st.spinner("Loading interviews..."):
        try:
            r = requests.get(
                f"{API_URL}/interviews/",
                headers=headers,
                params={"project_id": selected_project["id"]}
            )
            interviews = r.json()
        except Exception as e:
            st.error(f"Error: {e}")
            return

    # Tabs
    tab1, tab2 = st.tabs([
        f"📋 Interviews ({len(interviews)})",
        "➕ Add Interviewee"
    ])

    # ── Tab 1: View all interviews ──────────────────────────────
    with tab1:
        if not interviews:
            st.info("No interviewees added yet for this project.")
        else:
            # Summary
            df = pd.DataFrame(interviews)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", len(df))
            col2.metric("Completed",
                len(df[df["interview_status"] == "Completed"]))
            col3.metric("Scheduled",
                len(df[df["interview_status"] == "Scheduled"]))
            col4.metric("Not Contacted",
                len(df[df["interview_status"] == "Not Contacted"]))

            st.divider()

            # Filter by interviewer
            interviewers = ["All"] + sorted(
                df["interviewer"].dropna().unique().tolist()
            )
            selected_interviewer = st.selectbox(
                "Filter by Interviewer", interviewers
            )
            if selected_interviewer != "All":
                df = df[df["interviewer"] == selected_interviewer]

            st.write(f"Showing **{len(df)}** interviewees")

            # Display each interview
            for _, row in df.iterrows():
                with st.expander(
                    f"🏢 {row.get('interviewed_org_name', 'Unknown')} — "
                    f"{row.get('interviewee_name', 'Unknown')} | "
                    f"👤 {row.get('interviewer', '')} | "
                    f"Status: {row.get('interview_status', '')}"
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("**Contact Info**")
                        st.write(f"Name: {row.get('interviewee_name', '')}")
                        st.write(f"Title: {row.get('interviewee_title', '')}")
                        st.write(f"Email: {row.get('interviewee_email', '')}")
                        st.write(f"Phone: {row.get('interviewee_phone', '')}")
                        st.write(f"Company: {row.get('interviewed_org_name', '')}")
                        st.write(f"Country: {row.get('country', '')}")
                        st.write(f"Industry: {row.get('industry', '')}")

                    with col2:
                        st.write("**Interview Info**")
                        st.write(f"Interviewer: {row.get('interviewer', '')}")
                        st.write(f"Status: {row.get('interview_status', '')}")
                        st.write(f"Date: {row.get('date_of_interview', '')}")
                        st.write(f"Quality: {row.get('interview_quality', '')}")
                        st.write(f"Partner: {row.get('recruiting_partner', '')}")
                        st.write(f"Date Provided: {row.get('date_provided', '')}")

                    with col3:
                        st.write("**Notes**")
                        st.write(row.get("interviewer_notes", ""))

                    # PM can edit all fields
                    st.write("### ✏️ Edit")
                    ecol1, ecol2, ecol3 = st.columns(3)

                    with ecol1:
                        e_name = st.text_input(
                            "Interviewee Name",
                            value=row.get("interviewee_name") or "",
                            key=f"ename_{row['id']}"
                        )
                        e_title = st.text_input(
                            "Title",
                            value=row.get("interviewee_title") or "",
                            key=f"etitle_{row['id']}"
                        )
                        e_email = st.text_input(
                            "Email",
                            value=row.get("interviewee_email") or "",
                            key=f"eemail_{row['id']}"
                        )
                        e_phone = st.text_input(
                            "Phone",
                            value=row.get("interviewee_phone") or "",
                            key=f"ephone_{row['id']}"
                        )
                        e_org = st.text_input(
                            "Company",
                            value=row.get("interviewed_org_name") or "",
                            key=f"eorg_{row['id']}"
                        )

                    with ecol2:
                        e_country = st.selectbox(
                            "Country",
                            [""] + country_options,
                            index=([""] + country_options).index(
                                row.get("country", ""))
                            if row.get("country") in country_options else 0,
                            key=f"ecountry_{row['id']}"
                        )
                        e_industry = st.selectbox(
                            "Industry",
                            [""] + industry_options,
                            index=([""] + industry_options).index(
                                row.get("industry", ""))
                            if row.get("industry") in industry_options else 0,
                            key=f"eindustry_{row['id']}"
                        )
                        e_partner = st.selectbox(
                            "Recruiting Partner",
                            [""] + recruiting_options,
                            index=([""] + recruiting_options).index(
                                row.get("recruiting_partner", ""))
                            if row.get("recruiting_partner")
                            in recruiting_options else 0,
                            key=f"epartner_{row['id']}"
                        )
                        e_interviewer = st.text_input(
                            "Assigned Interviewer",
                            value=row.get("interviewer") or "",
                            key=f"einterviewer_{row['id']}"
                        )

                    with ecol3:
                        e_status = st.selectbox(
                            "Status",
                            status_options,
                            index=status_options.index(
                                row["interview_status"])
                            if row.get("interview_status")
                            in status_options else 0,
                            key=f"estatus_{row['id']}"
                        )
                        e_date = st.date_input(
                            "Date of Interview",
                            value=pd.to_datetime(
                                row["date_of_interview"]).date()
                            if row.get("date_of_interview") else None,
                            key=f"edate_{row['id']}"
                        )
                        e_quality = st.selectbox(
                            "Quality",
                            [""] + quality_options,
                            index=([""] + quality_options).index(
                                row.get("interview_quality", ""))
                            if row.get("interview_quality")
                            in quality_options else 0,
                            key=f"equality_{row['id']}"
                        )
                        e_notes = st.text_area(
                            "Notes",
                            value=row.get("interviewer_notes") or "",
                            key=f"enotes_{row['id']}"
                        )

                    if st.button("💾 Save Changes",
                                 key=f"esave_{row['id']}"):
                        payload = {
                            "interviewee_name": e_name,
                            "interviewee_title": e_title,
                            "interviewee_email": e_email,
                            "interviewee_phone": e_phone,
                            "interviewed_org_name": e_org,
                            "country": e_country or None,
                            "industry": e_industry or None,
                            "recruiting_partner": e_partner or None,
                            "interviewer": e_interviewer,
                            "interview_status": e_status,
                            "date_of_interview": str(e_date)
                            if e_date else None,
                            "interview_quality": e_quality or None,
                            "interviewer_notes": e_notes or None,
                        }
                        try:
                            r = requests.patch(
                                f"{API_URL}/interviews/{row['id']}",
                                json=payload,
                                headers=headers
                            )
                            if r.status_code == 200:
                                st.success("✅ Saved!")
                                st.rerun()
                            else:
                                st.error(f"Error: {r.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ── Tab 2: Add new interviewee ──────────────────────────────
    with tab2:
        st.write(f"### Add Interviewee to {selected_project['project_name']}")

        with st.form("new_interview_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Contact Info**")
                interviewee_name = st.text_input("Interviewee Name")
                interviewee_title = st.text_input("Title")
                interviewee_email = st.text_input("Email")
                interviewee_phone = st.text_input("Phone")
                org_name = st.text_input("Company Name")

            with col2:
                st.write("**Classification**")
                country = st.selectbox(
                    "Country", [""] + country_options
                )
                industry = st.selectbox(
                    "Industry", [""] + industry_options
                )
                recruiting_partner = st.selectbox(
                    "Recruiting Partner", [""] + recruiting_options
                )
                date_provided = st.date_input(
                    "Date Provided", value=None
                )

            with col3:
                st.write("**Assignment**")
                interviewer = st.text_input("Assigned Interviewer")
                scheduling_link = st.text_input("Scheduling Link")
                initial_status = st.selectbox(
                    "Initial Status", status_options
                )
                notes = st.text_area("Initial Notes")

            submit = st.form_submit_button(
                "➕ Add Interviewee", use_container_width=True
            )

            if submit:
                if not interviewee_name and not org_name:
                    st.error(
                        "Please enter at least a name or company!"
                    )
                elif not interviewer:
                    st.error("Please assign an interviewer!")
                else:
                    payload = {
                        "project_id": selected_project["id"],
                        "project_number": selected_project[
                            "project_number"],
                        "project_name": selected_project["project_name"],
                        "idc_project_manager": select