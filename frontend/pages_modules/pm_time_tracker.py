import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime


DATE_COLS = [
    "booking_date",
    "kickoff_date",
    "briefing_date",
    "ig_draft_from_bv",
    "ig_draft_to_client",
    "ig_approved",
    "first_contact_date",
    "interviews_complete_date",
    "results_presentation_date",
    "results_approval_date",
    "wp_draft_from_bv",
    "wp_draft_to_client",
    "wp_v1_feedback",
    "client_approval",
    "to_editing",
    "from_editing",
    "graphical_uplift",
    "to_client_final_approval",
    "publication_date",
]

EDITABLE_COLS = [
    "project_name",
    "project_type",
    "status",
    "bv_lead",
    "bvd",
    "interviews_target",
    "notes_status",
] + DATE_COLS


def get_json(url, headers):
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def build_unique_options(df, column_name, fallback_options=None):
    fallback_options = fallback_options or []

    values = []
    if not df.empty and column_name in df.columns:
        values = (
            df[column_name]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

    combined = values + fallback_options
    cleaned = sorted(
        list({
            x for x in combined
            if x and x.lower() not in ["nan", "none", "null"]
        })
    )

    return [""] + cleaned


def to_date_or_none(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    dt = pd.to_datetime(value, errors="coerce")

    if pd.isna(dt):
        return None

    return dt.date()


def clean_payload_value(value):
    """
    Converts Streamlit/Pandas values into JSON-safe values for FastAPI.
    Dates always become YYYY-MM-DD.
    Empty values become None.
    NumPy scalars become native Python scalars.
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, str):
        value = value.strip()
        return value if value else None

    return value


def values_are_equal(old_value, new_value):
    return clean_payload_value(old_value) == clean_payload_value(new_value)


def format_grid_df(df):
    grid_df = df.copy()

    text_cols = [
        "id",
        "project_name",
        "project_number",
        "project_type",
        "status",
        "bv_lead",
        "bvd",
        "notes_status",
    ]

    for col in text_cols:
        if col in grid_df.columns:
            grid_df[col] = grid_df[col].fillna("").astype(str)

    for col in ["interviews_target", "interviews_complete"]:
        if col in grid_df.columns:
            grid_df[col] = pd.to_numeric(
                grid_df[col],
                errors="coerce"
            ).fillna(0).astype(int)

    for col in DATE_COLS:
        if col in grid_df.columns:
            grid_df[col] = grid_df[col].apply(to_date_or_none)

    return grid_df


def patch_project(API_URL, headers, project_id, payload):
    r = requests.patch(
        f"{API_URL}/projects/{project_id}",
        json=payload,
        headers=headers,
    )
    return r


def show(API_URL, headers):
    st.title("⏱ Overall Project Tracker")

    # Load projects
    with st.spinner("Loading projects..."):
        try:
            projects = get_json(f"{API_URL}/projects/", headers)
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            return

    projects_df = pd.DataFrame(projects) if projects else pd.DataFrame()

    bv_lead_options = build_unique_options(
        projects_df,
        "bv_lead",
        fallback_options=[
            "Ladislav Kinda",
            "Matthew Marden",
            "Megan Szurley",
        ],
    )

    bvd_options = build_unique_options(
        projects_df,
        "bvd",
        fallback_options=[
            "Emily Taylor",
            "Julie Tiley",
            "Lynn",
            "Puneet Parasher",
        ],
    )

    tab1, tab2, tab3 = st.tabs([
        "📊 Team View (Excel-style)",
        "📋 Project Detail",
        "➕ Add New Project",
    ])

    # ── Tab 1: Excel-style editable grid ───────────────────────
    with tab1:
        if not projects:
            st.info("No projects yet. Add one in the tab above!")
        else:
            df = pd.DataFrame(projects)

            # Safety defaults for missing/null columns
            for col in ["status", "bv_lead", "bvd", "project_name", "project_number"]:
                if col not in df.columns:
                    df[col] = ""
                df[col] = df[col].fillna("").astype(str)

            # ── Filters ─────────────────────────────────────────
            st.write("### Filters")
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)

            with fcol1:
                status_values = sorted(
                    [x for x in df["status"].dropna().unique().tolist() if x]
                )
                default_status = ["Active"] if "Active" in status_values else status_values

                status_filter = st.multiselect(
                    "Status",
                    status_values,
                    default=default_status,
                )

            with fcol2:
                bv_leads = ["All"] + build_unique_options(df, "bv_lead")[1:]
                lead_filter = st.selectbox("BV Lead", bv_leads)

            with fcol3:
                bvds = ["All"] + build_unique_options(df, "bvd")[1:]
                bvd_filter = st.selectbox("IDC PM (BVD)", bvds)

            with fcol4:
                search = st.text_input("🔍 Search project name")

            # Apply filters
            filtered = df.copy()

            if status_filter:
                filtered = filtered[filtered["status"].isin(status_filter)]

            if lead_filter != "All":
                filtered = filtered[filtered["bv_lead"] == lead_filter]

            if bvd_filter != "All":
                filtered = filtered[filtered["bvd"] == bvd_filter]

            if search:
                filtered = filtered[
                    filtered["project_name"].str.contains(
                        search,
                        case=False,
                        na=False,
                    )
                    |
                    filtered["project_number"].str.contains(
                        search,
                        case=False,
                        na=False,
                    )
                ]

            st.write(f"**{len(filtered)} projects**")
            st.divider()

            # ── Editable grid ────────────────────────────────────
            grid_cols = [
                "id",
                "project_name",
                "project_number",
                "project_type",
                "status",
                "bv_lead",
                "bvd",
                "interviews_target",
                "interviews_complete",
                "notes_status",
            ] + DATE_COLS

            existing_cols = [c for c in grid_cols if c in filtered.columns]
            grid_df = format_grid_df(filtered[existing_cols])

            original_by_id = grid_df.set_index("id").to_dict("index")

            column_config = {
                "id": st.column_config.TextColumn(
                    "ID",
                    disabled=True,
                    width="small",
                ),
                "project_name": st.column_config.TextColumn(
                    "Project Name",
                    width="large",
                ),
                "project_number": st.column_config.TextColumn(
                    "Project #",
                    disabled=True,
                    width="medium",
                ),
                "project_type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["WP", "SB"],
                    width="small",
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Active", "Closed"],
                    width="small",
                ),
                "bv_lead": st.column_config.SelectboxColumn(
                    "BV Lead",
                    options=bv_lead_options,
                    width="medium",
                ),
                "bvd": st.column_config.SelectboxColumn(
                    "IDC PM",
                    options=bvd_options,
                    width="medium",
                ),
                "interviews_target": st.column_config.NumberColumn(
                    "Target",
                    width="small",
                    min_value=0,
                    step=1,
                ),
                "interviews_complete": st.column_config.NumberColumn(
                    "Complete",
                    width="small",
                    min_value=0,
                    disabled=True,
                ),
                "notes_status": st.column_config.TextColumn(
                    "Notes",
                    width="large",
                ),
            }

            date_column_labels = {
                "booking_date": "Booking",
                "kickoff_date": "Kickoff",
                "briefing_date": "Briefing",
                "ig_draft_from_bv": "IG Draft BV",
                "ig_draft_to_client": "IG To Client",
                "ig_approved": "IG Approved",
                "first_contact_date": "First Contact",
                "interviews_complete_date": "Interviews Done",
                "results_presentation_date": "Results Pres.",
                "results_approval_date": "Results Approval",
                "wp_draft_from_bv": "WP Draft BV",
                "wp_draft_to_client": "WP To Client",
                "wp_v1_feedback": "WP V1 Feedback",
                "client_approval": "Client Approval",
                "to_editing": "To Editing",
                "from_editing": "From Editing",
                "graphical_uplift": "Graphical Uplift",
                "to_client_final_approval": "Final Approval",
                "publication_date": "Publication",
            }

            for col, label in date_column_labels.items():
                column_config[col] = st.column_config.DateColumn(
                    label,
                    width="medium",
                    format="YYYY-MM-DD",
                )

            edited_df = st.data_editor(
                grid_df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key="overall_project_tracker_grid",
            )

            # ── Save changes button ──────────────────────────────
            col1, col2 = st.columns([1, 4])

            with col1:
                save = st.button(
                    "💾 Save Changes",
                    type="primary",
                    use_container_width=True,
                )

            if save:
                changed_rows = 0
                saved_rows = 0
                errors = 0
                error_details = []

                for _, row in edited_df.iterrows():
                    project_id = str(row["id"])
                    original = original_by_id.get(project_id, {})
                    payload = {}

                    for col in EDITABLE_COLS:
                        if col not in edited_df.columns:
                            continue

                        old_value = original.get(col)
                        new_value = row.get(col)

                        if not values_are_equal(old_value, new_value):
                            payload[col] = clean_payload_value(new_value)

                    # Do not PATCH rows that were not modified
                    if not payload:
                        continue

                    changed_rows += 1

                    try:
                        r = patch_project(
                            API_URL,
                            headers,
                            project_id,
                            payload,
                        )

                        if r.status_code == 200:
                            saved_rows += 1
                        else:
                            errors += 1
                            project_label = row.get("project_number") or project_id
                            error_details.append(
                                f"{project_label}: {r.status_code} - {r.text[:500]}"
                            )

                    except Exception as e:
                        errors += 1
                        project_label = row.get("project_number") or project_id
                        error_details.append(f"{project_label}: {str(e)}")

                if changed_rows == 0:
                    st.info("No changes detected.")
                elif errors == 0:
                    st.success(f"✅ {saved_rows} changed project(s) saved successfully.")
                    st.rerun()
                else:
                    st.warning(
                        f"⚠️ {saved_rows} saved, {errors} error(s). "
                        "Details below."
                    )

                    with st.expander("Show error details"):
                        for detail in error_details:
                            st.write(detail)

    # ── Tab 2: Project Detail (card view) ───────────────────────
    with tab2:
        if not projects:
            st.info("No projects yet.")
        else:
            project_options = {
                f"{p['project_name']} ({p['project_number']})": p
                for p in projects
            }

            selected_label = st.selectbox(
                "Select Project",
                list(project_options.keys()),
            )

            p = project_options[selected_label]

            completed = p.get("interviews_complete", 0) or 0
            target = p.get("interviews_target", 8) or 8
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
                st.progress(min(pct / 100, 1))
                st.caption(f"{pct}% complete")

            with col2:
                st.write("### Update")

                new_status = st.selectbox(
                    "Status",
                    ["Active", "Closed"],
                    index=0 if p.get("status") == "Active" else 1,
                    key="d_status",
                )

                current_bv_lead = p.get("bv_lead") or ""
                detail_bv_leads = bv_lead_options.copy()
                if current_bv_lead and current_bv_lead not in detail_bv_leads:
                    detail_bv_leads.append(current_bv_lead)

                new_bv_lead = st.selectbox(
                    "BV Lead",
                    detail_bv_leads,
                    index=detail_bv_leads.index(current_bv_lead)
                    if current_bv_lead in detail_bv_leads else 0,
                    key="d_bvlead",
                )

                current_bvd = p.get("bvd") or ""
                detail_bvds = bvd_options.copy()
                if current_bvd and current_bvd not in detail_bvds:
                    detail_bvds.append(current_bvd)

                new_bvd = st.selectbox(
                    "IDC PM (BVD)",
                    detail_bvds,
                    index=detail_bvds.index(current_bvd)
                    if current_bvd in detail_bvds else 0,
                    key="d_bvd",
                )

                new_target = st.number_input(
                    "Target Interviews",
                    value=int(target),
                    min_value=1,
                    step=1,
                    key="d_target",
                )

                new_notes = st.text_area(
                    "Notes",
                    value=p.get("notes_status") or "",
                    key="d_notes",
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
                        value=to_date_or_none(existing),
                        key=f"d_{field}",
                        format="YYYY-MM-DD",
                    )

            if st.button("💾 Save Project", type="primary"):
                payload = {
                    "status": clean_payload_value(new_status),
                    "bv_lead": clean_payload_value(new_bv_lead),
                    "bvd": clean_payload_value(new_bvd),
                    "interviews_target": clean_payload_value(new_target),
                    "notes_status": clean_payload_value(new_notes),
                }

                for field, _ in milestone_fields:
                    payload[field] = clean_payload_value(date_values[field])

                try:
                    r = patch_project(
                        API_URL,
                        headers,
                        p["id"],
                        payload,
                    )

                    if r.status_code == 200:
                        st.success("✅ Project saved!")
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")

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
                    "Project Type",
                    ["WP", "SB"],
                )

                bv_lead = st.selectbox(
                    "BV Lead",
                    bv_lead_options,
                )

            with col2:
                bvd = st.selectbox(
                    "IDC PM (BVD)",
                    bvd_options,
                )

                interviews_target = st.number_input(
                    "Target Interviews",
                    value=8,
                    min_value=1,
                    step=1,
                )

                notes = st.text_area("Notes")

            submit = st.form_submit_button(
                "➕ Create Project",
                use_container_width=True,
            )

            if submit:
                if not project_name or not project_number:
                    st.error("Project Name and Number are required!")
                else:
                    payload = {
                        "project_name": clean_payload_value(project_name),
                        "project_number": clean_payload_value(project_number),
                        "project_type": clean_payload_value(project_type),
                        "bv_lead": clean_payload_value(bv_lead),
                        "bvd": clean_payload_value(bvd),
                        "interviews_target": clean_payload_value(interviews_target),
                        "notes_status": clean_payload_value(notes),
                        "status": "Active",
                    }

                    try:
                        r = requests.post(
                            f"{API_URL}/projects/",
                            json=payload,
                            headers=headers,
                        )

                        if r.status_code == 200:
                            st.success("✅ Project created!")
                            st.rerun()
                        else:
                            st.error(f"Error {r.status_code}: {r.text}")

                    except Exception as e:
                        st.error(f"Error: {e}")