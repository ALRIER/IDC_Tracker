import streamlit as st
import requests
import pandas as pd


def show(API_URL, headers):
    st.title("👥 Interview Sheet")
    st.caption("Add and manage interviewees for your projects")

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

    def get_dropdown(category):
        try:
            r = requests.get(f"{API_URL}/admin/dropdowns", headers=headers)
            items = r.json()
            return [i["value"] for i in items
                    if i["category"] == category and i["is_active"]]
        except:
            return []

    def safe_date(val):
        """Safely convert any value to a date or None"""
        if val is None or val == "" or val == "nan":
            return None
        try:
            result = pd.to_datetime(val)
            if pd.isna(result):
                return None
            return result.date()
        except Exception:
            return None

    status_options = get_dropdown("interview_status")
    quality_options = get_dropdown("interview_quality")
    industry_options = get_dropdown("industry")
    country_options = get_dropdown("country")
    recruiting_options = get_dropdown("recruiting_partner")

    # Get list of interviewers for dropdown
    try:
        r = requests.get(f"{API_URL}/admin/users", headers=headers)
        all_users = r.json()
        interviewer_names = sorted([
            u["interviewer_name"] for u in all_users
            if u.get("role") == "interviewer"
            and u.get("interviewer_name")
            and u.get("is_active")
        ])
    except Exception:
        interviewer_names = []

    project_map = {
        f"{p['project_name']} ({p['project_number']})": p
        for p in projects
    }
    selected_label = st.selectbox(
        "Select Project", list(project_map.keys())
    )
    selected_project = project_map[selected_label]

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

    tab1, tab2 = st.tabs([
        f"📋 Interviews ({len(interviews)})",
        "➕ Add Interviewee"
    ])

    # ── Tab 1: View interviews ───────────────────────────────────
    with tab1:
        if not interviews:
            st.info("No interviewees added yet for this project.")
        else:
            df = pd.DataFrame(interviews)
            df = df.fillna("").replace("nan", "")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", len(df))
            col2.metric("Completed",
                len(df[df["interview_status"] == "Completed"]))
            col3.metric("Scheduled",
                len(df[df["interview_status"] == "Scheduled"]))
            col4.metric("Not Contacted",
                len(df[df["interview_status"] == "Not Contacted"]))

            st.divider()

            interviewers = ["All"] + sorted(
                df["interviewer"].dropna().unique().tolist()
            )
            selected_interviewer = st.selectbox(
                "Filter by Interviewer", interviewers
            )
            if selected_interviewer != "All":
                df = df[df["interviewer"] == selected_interviewer]

            st.write(f"Showing **{len(df)}** interviewees")

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
                        st.write(f"Date of Interview: {row.get('date_of_interview', '')}")
                        st.write(f"Quality: {row.get('interview_quality', '')}")
                        st.write(f"Source: {row.get('recruiting_partner', '')}")
                        st.write(f"Date Provided: {row.get('date_provided', '')}")
                        st.write(f"Last Contacted: {row.get('last_date_of_contact', '')}")

                    with col3:
                        st.write("**Notes**")
                        notes_val = row.get("interviewer_notes", "")
                        if notes_val == "nan":
                            notes_val = ""
                        st.write(notes_val)

                    # PM can edit contact/assignment fields only
                    # Interviewers handle status/date/quality/notes
                    st.write("### ✏️ Edit Contact Info")
                    ecol1, ecol2 = st.columns(2)

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
                            "Source / Recruiting Partner",
                            [""] + recruiting_options,
                            index=([""] + recruiting_options).index(
                                row.get("recruiting_partner", ""))
                            if row.get("recruiting_partner")
                            in recruiting_options else 0,
                            key=f"epartner_{row['id']}"
                        )
                        # Interviewer as dropdown
                        interviewer_opts = [""] + interviewer_names
                        current_int = row.get("interviewer") or ""
                        int_idx = interviewer_opts.index(current_int) \
                            if current_int in interviewer_opts else 0
                        e_interviewer = st.selectbox(
                            "Assigned Interviewer",
                            interviewer_opts,
                            index=int_idx,
                            key=f"einterviewer_{row['id']}"
                        )

                        e_date_provided = st.date_input(
                            "Date Provided",
                            value=safe_date(row.get("date_provided")),
                            key=f"edateprov_{row['id']}"
                        )

                    if st.button(
                        "💾 Save Contact Info",
                        key=f"esave_{row['id']}"
                    ):
                        payload = {
                            "interviewee_name": e_name,
                            "interviewee_title": e_title,
                            "interviewee_email": e_email,
                            "interviewee_phone": e_phone,
                            "interviewed_org_name": e_org,
                            "country": e_country or None,
                            "industry": e_industry or None,
                            "recruiting_partner": e_partner or None,
                            "interviewer": e_interviewer or None,
                            "date_provided": str(e_date_provided)
                            if e_date_provided else None,
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

    # ── Tab 2: Add new interviewee ───────────────────────────────
    with tab2:
        st.write(
            f"### Add Interviewee to "
            f"{selected_project['project_name']}"
        )
        st.caption("Fields marked with * are required")

        with st.form("new_interview_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Contact Info**")
                interviewee_name = st.text_input("Interviewee Name *")
                interviewee_title = st.text_input("Title *")
                interviewee_email = st.text_input("Email")
                interviewee_phone = st.text_input("Phone")
                org_name = st.text_input("Company Name *")

            with col2:
                st.write("**Classification**")
                country = st.selectbox(
                    "Country *", [""] + country_options
                )
                industry = st.selectbox(
                    "Industry *", [""] + industry_options
                )
                recruiting_partner = st.selectbox(
                    "Source / Recruiting Partner *",
                    [""] + recruiting_options
                )
                date_provided = st.date_input(
                    "Date Provided *", value=None
                )

            with col3:
                st.write("**Assignment & Status**")
                # Interviewer dropdown
                interviewer = st.selectbox(
                    "Assigned Interviewer *",
                    [""] + interviewer_names
                )
                scheduling_link = st.text_input("Scheduling Link")
                initial_status = st.selectbox(
                    "Initial Status *",
                    [""] + status_options
                )
                # Show last contacted date if status is Contacted
                last_contacted = st.date_input(
                    "Last Date of Contact",
                    value=None,
                    help="Fill this if status is Contacted or beyond"
                )
                notes = st.text_area("Initial Notes")

            submit = st.form_submit_button(
                "➕ Add Interviewee", use_container_width=True
            )

            if submit:
                # Validate required fields
                errors = []
                if not interviewee_name:
                    errors.append("Interviewee Name")
                if not interviewee_title:
                    errors.append("Title")
                if not org_name:
                    errors.append("Company Name")
                if not country:
                    errors.append("Country")
                if not industry:
                    errors.append("Industry")
                if not recruiting_partner:
                    errors.append("Source / Recruiting Partner")
                if not date_provided:
                    errors.append("Date Provided")
                if not interviewer:
                    errors.append("Assigned Interviewer")
                if not initial_status:
                    errors.append("Initial Status")

                if errors:
                    st.error(
                        f"Please fill in required fields: "
                        f"{', '.join(errors)}"
                    )
                else:
                    payload = {
                        "project_id": selected_project["id"],
                        "project_number": selected_project[
                            "project_number"
                        ],
                        "project_name": selected_project["project_name"],
                        "idc_project_manager": selected_project.get(
                            "bvd", ""
                        ),
                        "bv_project_manager": selected_project.get(
                            "bv_lead", ""
                        ),
                        "interviewee_name": interviewee_name,
                        "interviewee_title": interviewee_title,
                        "interviewee_email": interviewee_email or None,
                        "interviewee_phone": interviewee_phone or None,
                        "interviewed_org_name": org_name,
                        "country": country,
                        "industry": industry,
                        "recruiting_partner": recruiting_partner,
                        "date_provided": str(date_provided),
                        "interviewer": interviewer,
                        "scheduling_link": scheduling_link or None,
                        "interview_status": initial_status,
                        "last_date_of_contact": str(last_contacted)
                        if last_contacted else None,
                        "interviewer_notes": notes or None,
                    }
                    try:
                        r = requests.post(
                            f"{API_URL}/interviews/",
                            json=payload,
                            headers=headers
                        )
                        if r.status_code == 200:
                            st.success(
                                f"✅ {interviewee_name} from "
                                f"{org_name} added successfully!"
                            )
                            st.rerun()
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")