import streamlit as st
import requests
import pandas as pd

def show(API_URL, headers):
    st.title("📋 My Interviews")
    st.caption("Your assigned interviews — organised by project")

    # Load interviews
    with st.spinner("Loading your interviews..."):
        try:
            r = requests.get(
                f"{API_URL}/interviews/", headers=headers
            )
            data = r.json()
        except Exception as e:
            st.error(f"Error loading interviews: {e}")
            return

    if not data:
        st.info("No interviews assigned to you yet.")
        return

    # Load dropdowns directly
   try:
    	r = requests.get(
       	 f"{API_URL}/admin/dropdowns", headers=headers
    )
    raw = r.json()
    # Handle both list and dict responses
    if isinstance(raw, list):
        all_dropdowns = raw
    elif isinstance(raw, dict):
        all_dropdowns = list(raw.values()) \
            if raw else []
    else:
        all_dropdowns = []

    status_options = [
        d["value"] for d in all_dropdowns
        if isinstance(d, dict)
        and d.get("category") == "interview_status"
        and d.get("is_active")
    ]
    quality_options = [
        d["value"] for d in all_dropdowns
        if isinstance(d, dict)
        and d.get("category") == "interview_quality"
        and d.get("is_active")
    ]
except Exception as e:
    st.warning(f"Could not load dropdowns: {e}")
    status_options = [
        "Not Contacted", "Contacted", "Scheduled",
        "Being Rescheduled", "No Show", "On Hold",
        "Completed", "Cancelled", "Declined",
        "Disqualified"
    ]
    quality_options = ["Excellent", "Good", "Fair", "Poor"]
     
    df = pd.DataFrame(data)

    # Clean nan values
    df = df.fillna("")
    df = df.replace("nan", "")

    # ── Summary metrics ──────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", len(df))
    col2.metric("✅ Completed",
        len(df[df["interview_status"] == "Completed"]))
    col3.metric("📅 Scheduled",
        len(df[df["interview_status"] == "Scheduled"]))
    col4.metric("🔄 Rescheduling",
        len(df[df["interview_status"] == "Being Rescheduled"]))
    col5.metric("📭 Not Contacted",
        len(df[df["interview_status"] == "Not Contacted"]))

    st.divider()

    # ── Group by project ─────────────────────────────────────────
    projects = df["project_name"].unique().tolist()
    projects = [p for p in projects if p and p != ""]

    if not projects:
        st.info("No interviews found.")
        return

    st.write(f"### Your interviews across **{len(projects)}** projects")

    for project_name in sorted(projects):
        project_df = df[df["project_name"] == project_name]
        project_number = project_df.iloc[0].get(
            "project_number", ""
        )

        # Project completion stats
        total = len(project_df)
        completed = len(
            project_df[
                project_df["interview_status"] == "Completed"
            ]
        )
        scheduled = len(
            project_df[
                project_df["interview_status"] == "Scheduled"
            ]
        )

        with st.expander(
            f"📁 **{project_name}** ({project_number}) — "
            f"{total} contacts | "
            f"✅ {completed} completed | "
            f"📅 {scheduled} scheduled",
            expanded=False
        ):
            # Status filter within project
            status_filter = st.multiselect(
                "Filter by status",
                options=status_options,
                default=[],
                key=f"filter_{project_name}"
            )

            filtered_project = project_df
            if status_filter:
                filtered_project = project_df[
                    project_df["interview_status"].isin(
                        status_filter
                    )
                ]

            st.write(
                f"Showing **{len(filtered_project)}** contacts"
            )

            for _, row in filtered_project.iterrows():
                # Status color indicator
                status = row.get("interview_status", "")
                if status == "Completed":
                    icon = "✅"
                elif status == "Scheduled":
                    icon = "📅"
                elif status == "Being Rescheduled":
                    icon = "🔄"
                elif status in ("Declined", "Cancelled",
                                "Disqualified"):
                    icon = "❌"
                elif status == "No Show":
                    icon = "👻"
                else:
                    icon = "📭"

                org = row.get("interviewed_org_name") or "Unknown"
                name = row.get("interviewee_name") or "Unknown"
                title = row.get("interviewee_title") or ""

                with st.container():
                    st.markdown(
                        f"{icon} **{org}** — {name}"
                        + (f" | *{title}*" if title else "")
                    )

                    info_col, edit_col = st.columns([2, 2])

                    with info_col:
                        st.write("**Contact Details**")
                        if row.get("interviewee_email"):
                            st.write(
                                f"📧 {row['interviewee_email']}"
                            )
                        if row.get("interviewee_phone"):
                            st.write(
                                f"📞 {row['interviewee_phone']}"
                            )
                        if row.get("country"):
                            st.write(f"🌍 {row['country']}")
                        if row.get("industry"):
                            st.write(f"🏭 {row['industry']}")
                        if row.get("recruiting_partner"):
                            st.write(
                                f"🤝 **Source:** "
                                f"{row['recruiting_partner']}"
                            )
                        if row.get("date_provided"):
                            st.write(
                                f"📆 Provided: "
                                f"{row['date_provided']}"
                            )

                    with edit_col:
                        st.write("**Update Interview**")

                        # Status dropdown
                        current_status = row.get(
                            "interview_status", ""
                        )
                        status_idx = status_options.index(
                            current_status
                        ) if current_status in status_options \
                            else 0

                        new_status = st.selectbox(
                            "Status",
                            options=status_options,
                            index=status_idx,
                            key=f"status_{row['id']}"
                        )

                        # Date of interview
                        current_date = row.get(
                            "date_of_interview", ""
                        )
                        try:
                            date_val = pd.to_datetime(
                                current_date
                            ).date() if current_date else None
                        except:
                            date_val = None

                        new_date = st.date_input(
                            "Date of Interview",
                            value=date_val,
                            key=f"date_{row['id']}"
                        )

                        # Quality dropdown
                        current_quality = row.get(
                            "interview_quality", ""
                        )
                        quality_with_blank = [""] + quality_options
                        quality_idx = quality_with_blank.index(
                            current_quality
                        ) if current_quality in \
                            quality_with_blank else 0

                        new_quality = st.selectbox(
                            "Interview Quality",
                            options=quality_with_blank,
                            index=quality_idx,
                            key=f"quality_{row['id']}"
                        )

                        # Notes
                        current_notes = row.get(
                            "interviewer_notes", ""
                        )
                        if current_notes == "nan":
                            current_notes = ""

                        new_notes = st.text_area(
                            "Notes",
                            value=current_notes,
                            height=80,
                            key=f"notes_{row['id']}"
                        )

                        if st.button(
                            "💾 Save",
                            key=f"save_{row['id']}"
                        ):
                            payload = {
                                "interview_status": new_status,
                                "date_of_interview": str(new_date)
                                if new_date else None,
                                "interview_quality": new_quality
                                if new_quality else None,
                                "interviewer_notes": new_notes
                                if new_notes else None,
                            }
                            try:
                                r = requests.patch(
                                    f"{API_URL}/interviews/"
                                    f"{row['id']}",
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

                    st.markdown("---")