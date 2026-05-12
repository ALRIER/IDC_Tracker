import streamlit as st
import requests
import pandas as pd
from datetime import date

def show(API_URL, headers):
    st.title("⏱ Overall Project Tracker")

    # Load projects
    with st.spinner("Loading projects..."):
        try:
            r = requests.get(f"{API_URL}/projects/", headers=headers)
            projects = r.json()
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            return

    tab1, tab2, tab3 = st.tabs([
        "📊 Team View (Excel-style)",
        "📋 Project Detail",
        "➕ Add New Project"
    ])

    # ── Tab 1: Excel-style editable grid ───────────────────────
    with tab1:
        if not projects:
            st.info("No projects yet. Add one in the tab above!")
        else:
            df = pd.DataFrame(projects)

            # ── Filters ─────────────────────────────────────────
            st.write("### Filters")
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)

            with fcol1:
                status_filter = st.multiselect(
                    "Status",
                    ["Active", "Closed"],
                    default=["Active"]
                )
            with fcol2:
                bv_leads = ["All"] + sorted(
                    df["bv_lead"].dropna().unique().tolist()
                )
                lead_filter = st.selectbox("BV Lead", bv_leads)

            with fcol3:
                bvds = ["All"] + sorted(
                    df["bvd"].dropna().unique().tolist()
                )
                bvd_filter = st.selectbox("IDC PM (BVD)", bvds)

            with fcol4:
                search = st.text_input(
                    "🔍 Search project name"
                )

            # Apply filters
            filtered = df.copy()
            if status_filter:
                filtered = filtered[
                    filtered["status"].isin(status_filter)
                ]
            if lead_filter != "All":
                filtered = filtered[
                    filtered["bv_lead"] == lead_filter
                ]
            if bvd_filter != "All":
                filtered = filtered[filtered["bvd"] == bvd_filter]
            if search:
                filtered = filtered[
                    filtered["project_name"].str.contains(
                        search, case=False, na=False
                    )
                ]

            st.write(f"**{len(filtered)} projects**")
            st.divider()

            # ── Editable grid ────────────────────────────────────
            # Select columns to show in the grid
            date_cols = [
                "booking_date", "kickoff_date", "briefing_date",
                "ig_draft_from_bv", "ig_draft_to_client",
                "ig_approved", "first_contact_date",
                "interviews_complete_date",
                "results_presentation_date",
                "results_approval_date",
                "wp_draft_from_bv", "wp_draft_to_client",
                "wp_v1_feedback", "client_approval",
                "to_editing", "from_editing",
                "graphical_uplift",
                "to_client_final_approval",
                "publication_date"
            ]

            grid_cols = [
                "id", "project_name", "project_number",
                "project_type", "status", "bv_lead", "bvd",
                "interviews_target", "interviews_complete",
                "notes_status"
            ] + date_cols

            # Keep only existing columns
            existing_cols = [
                c for c in grid_cols if c in filtered.columns
            ]
            grid_df = filtered[existing_cols].copy()

            # Convert date columns to proper date type
            for col in date_cols:
                if col in grid_df.columns:
                    grid_df[col] = pd.to_datetime(
                        grid_df[col], errors="coerce"
                    ).dt.date

            # Configure columns
            column_config = {
                "id": st.column_config.TextColumn(
                    "ID", disabled=True, width="small"
                ),
                "project_name": st.column_config.TextColumn(
                    "Project Name", width="large"
                ),
                "project_number": st.column_config.TextColumn(
                    "Project #", width="medium"
                ),
                "project_type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["WP", "SB"],
                    width="small"
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Active", "Closed"],
                    width="small"
                ),
                "bv_lead": st.column_config.TextColumn(
                    "BV Lead", width="medium"
                ),
                "bvd": st.column_config.TextColumn(
                    "IDC PM", width="medium"
                ),
                "interviews_target": st.column_config.NumberColumn(
                    "Target", width="small", min_value=0
                ),
                "interviews_complete": st.column_config.NumberColumn(
                    "Complete", width="small", min_value=0,
                    disabled=True
                ),
                "notes_status": st.column_config.TextColumn(
                    "Notes", width="large"
                ),
                "booking_date": st.column_config.DateColumn(
                    "Booking", width="medium"
                ),
                "kickoff_date": st.column_config.DateColumn(
                    "Kickoff", width="medium"
                ),
                "briefing_date": st.column_config.DateColumn(
                    "Briefing", width="medium"
                ),
                "ig_draft_from_bv": st.column_config.DateColumn(
                    "IG Draft BV", width="medium"
                ),
                "ig_draft_to_client": st.column_config.DateColumn(
                    "IG To Client", width="medium"
                ),
                "ig_approved": st.column_config.DateColumn(
                    "IG Approved", width="medium"
                ),
                "first_contact_date": st.column_config.DateColumn(
                    "First Contact", width="medium"
                ),
                "interviews_complete_date": st.column_config.DateColumn(
                    "Interviews Done", width="medium"
                ),
                "results_presentation_date": st.column_config.DateColumn(
                    "Results Pres.", width="medium"
                ),
                "results_approval_date": st.column_config.DateColumn(
                    "Results Approval", width="medium"
                ),
                "wp_draft_from_bv": st.column_config.DateColumn(
                    "WP Draft BV", width="medium"
                ),
                "wp_draft_to_client": st.column_config.DateColumn(
                    "WP To Client", width="medium"
                ),
                "wp_v1_feedback": st.column_config.DateColumn(
                    "WP V1 Feedback", width="medium"
                ),
                "client_approval": st.column_config.DateColumn(
                    "Client Approval", width="medium"
                ),
                "to_editing": st.column_config.DateColumn(
                    "To Editing", width="medium"
                ),
                "from_editing": st.column_config.DateColumn(
                    "From Editing", width="medium"
                ),
                "graphical_uplift": st.column_config.DateColumn(
                    "Graphical Uplift", width="medium"
                ),
                "to_client_final_approval": st.column_config.DateColumn(
                    "Final Approval", width="medium"
                ),
                "publication_date": st.column_config.DateColumn(
                    "Publication", width="medium"
                ),
            }

            edited_df = st.data_editor(
                grid_df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key="time_tracker_grid"
            )

            # ── Save changes button ──────────────────────────────
            col1, col2 = st.columns([1, 4])
            with col1:
                save = st.button(
                    "💾 Save All Changes",
                    type="primary",
                    use_container_width=True
                )

            if save:
                changes = 0
                errors = 0

                for _, row in edited_df.iterrows():
                    project_id = row["id"]
                    payload = {}

                    for col in [
                        "project_name", "project_type", "status",
                        "bv_lead", "bvd", "interviews_target",
                        "notes_status"
                    ] + date_cols:
                        if col in row and col != "id":
                            val = row[col]
                            if pd.isna(val) if not isinstance(
                                val, (str, date)
                            ) else False:
                                payload[col] = None
                            elif isinstance(val, date):
                                payload[col] = str(val)
                            else:
                                payload[col] = val if val != "" \
                                    else None

                    try:
                        r = requests.patch(
                            f"{API_URL}/projects/{project_id}",
                            json=payload,
                            headers=headers
                        )
                        if r.status_code == 200:
                            changes += 1
                        else:
                            errors += 1
                    except Exception as e:
                        errors += 1

                if errors == 0:
                    st.success(
                        f"✅ {changes} projects saved successfully!"
                    )
                    st.rerun()
                else:
                    st.warning(
                        f"⚠️ {changes} saved, {errors} errors"
                    )

    # ── Tab 2: Project Detail (card view) ───────────────────────
    with tab2:
        if not projects:
            st.info("No projects yet.")
        else:
            # Filter selector
            project_options = {
                f"{p['project_name']} ({p['project_number']})": p
                for p in projects
            }
            selected_label = st.selectbox(
                "Select Project", list(project_options.keys())
            )
            p = project_options[selected_label]

            completed = p.get("interviews_complete", 0)
            target = p.get("interviews_target", 8)
            pct = int(completed / target * 100) if target else 0

            col1, col2 = st.columns(2)

            with col1:
                st.write("### Project Info")
                st.write(f"**Name:** {p.get('project_name')}")
                st.write(f"**Number:** {p.get('project_number')}")
                st.write(f"**Type:** {p.get('project_type')}")
                st.write(f"**BV Lead:** {p.get('bv_lead')}")
                st.write(f"**IDC PM:** {p.get('bvd')}")
                st.write(f"**Target:** {target}")
                st.write(f"**Completed:** {completed}")
                st.progress(pct / 100)
                st.caption(f"{pct}% complete")

            with col2:
                st.write("### Update")
                new_status = st.selectbox(
                    "Status",
                    ["Active", "Closed"],
                    index=0 if p.get("status") == "Active" else 1,
                    key="d_status"
                )
                new_bv_lead = st.text_input(
                    "BV Lead",
                    value=p.get("bv_lead") or "",
                    key="d_bvlead"
                )
                new_bvd = st.text_input(
                    "IDC PM (BVD)",
                    value=p.get("bvd") or "",
                    key="d_bvd"
                )
                new_target = st.number_input(
                    "Target Interviews",
                    value=target,
                    min_value=1,
                    key="d_target"
                )
                new_notes = st.text_area(
                    "Notes",
                    value=p.get("notes_status") or "",
                    key="d_notes"
                )

            st.write("### 📅 Milestone Dates")
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
                ("to_client_final_approval", "Final Approval"),
                ("publication_date", "Publication Date"),
            ]

            date_values = {}
            date_cols_ui = st.columns(3)
            for i, (field, label) in enumerate(milestone_fields):
                with date_cols_ui[i % 3]:
                    existing = p.get(field)
                    date_values[field] = st.date_input(
                        label,
                        value=pd.to_datetime(existing).date()
                        if existing else None,
                        key=f"d_{field}"
                    )

            if st.button("💾 Save Project", type="primary"):
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

    # ── Tab 3: Add New Project ───────────────────────────────────
    with tab3:
        st.write("### Add New Project")

        with st.form("new_project_form"):
            col1, col2 = st.columns(2)

            with col1:
                project_name = st.text_input("Project Name *")
                project_number = st.text_input("Project Number *")
                project_type = st.selectbox(
                    "Project Type", ["WP", "SB"]
                )
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
                    st.error(
                        "Project Name and Number are required!"
                    )
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