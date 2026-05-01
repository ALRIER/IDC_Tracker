import streamlit as st
import requests
import pandas as pd

def show(API_URL, headers):
    st.title("📋 My Interviews")
    st.caption("You can only edit: Date, Status, Quality and Notes")

    # Load dropdowns
    def get_dropdown(category):
        try:
            r = requests.get(f"{API_URL}/admin/dropdowns", headers=headers)
            items = r.json()
            return [i["value"] for i in items if i["category"] == category and i["is_active"]]
        except:
            return []

    status_options = get_dropdown("interview_status")
    quality_options = get_dropdown("interview_quality")

    # Load interviews
    with st.spinner("Loading your interviews..."):
        try:
            r = requests.get(f"{API_URL}/interviews/", headers=headers)
            data = r.json()
        except Exception as e:
            st.error(f"Error loading interviews: {e}")
            return

    if not data:
        st.info("No interviews assigned to you yet.")
        return

    df = pd.DataFrame(data)

    # Show summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df))
    col2.metric("Completed", len(df[df["interview_status"] == "Completed"]))
    col3.metric("Scheduled", len(df[df["interview_status"] == "Scheduled"]))
    col4.metric("Not Contacted", len(df[df["interview_status"] == "Not Contacted"]))

    st.divider()

    # Filter by project
    projects = ["All"] + sorted(df["project_name"].dropna().unique().tolist())
    selected_project = st.selectbox("Filter by Project", projects)

    if selected_project != "All":
        df = df[df["project_name"] == selected_project]

    st.write(f"Showing **{len(df)}** interviews")

    # Display each interview as an editable card
    for _, row in df.iterrows():
        with st.expander(
            f"🏢 {row.get('interviewed_org_name', 'Unknown')} — "
            f"{row.get('interviewee_name', 'Unknown')} | "
            f"Status: {row.get('interview_status', 'Not Contacted')}"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Project:** {row.get('project_name', '')}")
                st.write(f"**Company:** {row.get('interviewed_org_name', '')}")
                st.write(f"**Interviewee:** {row.get('interviewee_name', '')}")
                st.write(f"**Title:** {row.get('interviewee_title', '')}")
                st.write(f"**Email:** {row.get('interviewee_email', '')}")
                st.write(f"**Industry:** {row.get('industry', '')}")
                st.write(f"**Country:** {row.get('country', '')}")

            with col2:
                st.write("### ✏️ Update Interview")

                new_status = st.selectbox(
                    "Status",
                    status_options,
                    index=status_options.index(row["interview_status"])
                    if row["interview_status"] in status_options else 0,
                    key=f"status_{row['id']}"
                )

                new_date = st.date_input(
                    "Date of Interview",
                    value=pd.to_datetime(row["date_of_interview"]).date()
                    if row.get("date_of_interview") else None,
                    key=f"date_{row['id']}"
                )

                new_quality = st.selectbox(
                    "Interview Quality",
                    [""] + quality_options,
                    index=([""] + quality_options).index(row["interview_quality"])
                    if row.get("interview_quality") in quality_options else 0,
                    key=f"quality_{row['id']}"
                )

                new_notes = st.text_area(
                    "Notes",
                    value=row.get("interviewer_notes") or "",
                    key=f"notes_{row['id']}"
                )

                if st.button("💾 Save", key=f"save_{row['id']}"):
                    payload = {
                        "interview_status": new_status,
                        "date_of_interview": str(new_date) if new_date else None,
                        "interview_quality": new_quality if new_quality else None,
                        "interviewer_notes": new_notes if new_notes else None
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