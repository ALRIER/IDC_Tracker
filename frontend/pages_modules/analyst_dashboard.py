import streamlit as st
import requests
import pandas as pd
import plotly.express as px


def get_json(url, headers):
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def first_year_from_row(row, cols):
    for col in cols:
        if col in row and pd.notna(row[col]):
            dt = pd.to_datetime(row[col], errors="coerce")
            if pd.notna(dt):
                return int(dt.year)
    return None


def show(API_URL, headers):
    st.title("📊 Program Dashboard")
    st.caption("Live overview of all interview activity")

    # Load raw data instead of pre-aggregated dashboard endpoints
    with st.spinner("Loading dashboard..."):
        try:
            projects = get_json(f"{API_URL}/projects/", headers)
            interviews = get_json(f"{API_URL}/interviews/", headers)
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")
            return

    if not interviews:
        st.info("No interview data yet.")
        return

    df = pd.DataFrame(interviews)
    projects_df = pd.DataFrame(projects)

    # ── Attach project status and project year ─────────────────
    if not projects_df.empty:
        project_date_cols = [
            "booking_date",
            "kickoff_date",
            "first_contact_date",
            "publication_date",
            "created_at",
            "updated_at",
        ]

        projects_df["project_year"] = projects_df.apply(
            lambda row: first_year_from_row(row, project_date_cols),
            axis=1
        )

        status_by_id = dict(zip(projects_df["id"].astype(str), projects_df["status"]))
        year_by_id = dict(zip(projects_df["id"].astype(str), projects_df["project_year"]))

        status_by_number = dict(zip(projects_df["project_number"], projects_df["status"]))
        year_by_number = dict(zip(projects_df["project_number"], projects_df["project_year"]))

        df["project_status_filter"] = df["project_id"].astype(str).map(status_by_id)

        if "project_number" in df.columns:
            df["project_status_filter"] = df["project_status_filter"].fillna(
                df["project_number"].map(status_by_number)
            )

        df["project_year"] = df["project_id"].astype(str).map(year_by_id)

        if "project_number" in df.columns:
            df["project_year"] = df["project_year"].fillna(
                df["project_number"].map(year_by_number)
            )
    else:
        df["project_status_filter"] = None
        df["project_year"] = None

    # Fallbacks from interviews table
    if "project_status" in df.columns:
        df["project_status_filter"] = df["project_status_filter"].fillna(
            df["project_status"]
        )

    interview_date_cols = [
        "date_provided",
        "date_of_interview",
        "created_at",
        "updated_at",
    ]

    df["project_year"] = df["project_year"].fillna(
        df.apply(lambda row: first_year_from_row(row, interview_date_cols), axis=1)
    )

    df["project_status_filter"] = df["project_status_filter"].fillna("Unknown")

    # ── Filters ───────────────────────────────────────────────
    st.write("### Filters")

    fcol1, fcol2 = st.columns(2)

    with fcol1:
        status_filter = st.selectbox(
            "Project status",
            ["All", "Active", "Inactive / Closed"]
        )

    available_years = sorted(
        [int(y) for y in df["project_year"].dropna().unique()],
        reverse=True
    )

    with fcol2:
        year_filter = st.selectbox(
            "Project year",
            ["All"] + available_years
        )

    filtered = df.copy()

    if status_filter == "Active":
        filtered = filtered[
            filtered["project_status_filter"].astype(str).str.lower() == "active"
        ]

    elif status_filter == "Inactive / Closed":
        filtered = filtered[
            filtered["project_status_filter"].astype(str).str.lower() != "active"
        ]

    if year_filter != "All":
        filtered = filtered[filtered["project_year"] == int(year_filter)]

    if filtered.empty:
        st.warning("No interview data found for the selected filters.")
        return

    # ── Calculate filtered summary ─────────────────────────────
    completed = filtered["interview_status"].isin(["Completed"]).sum()

    scheduled = filtered["interview_status"].isin([
        "Scheduled",
        "Being Rescheduled"
    ]).sum()

    no_low_response = filtered["interview_status"].isin([
        "No Show",
        "On Hold",
        "Contacted",
        "Not Contacted"
    ]).sum()

    cancelled = filtered["interview_status"].isin(["Cancelled"]).sum()

    total_interviewees = len(filtered)

    # ── KPI Cards ─────────────────────────────────────────────
    st.write("### Program Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Interviewees", total_interviewees)
    col2.metric("✅ Completed", completed)
    col3.metric("📅 Scheduled / In Progress", scheduled)
    col4.metric("📭 No / Low Response", no_low_response)
    col5.metric("❌ Cancelled", cancelled)

    st.divider()

    # ── Group by interviewer ──────────────────────────────────
    by_interviewer = (
        filtered.groupby("interviewer")
        .agg(
            total=("id", "count"),
            completed=("interview_status", lambda x: x.isin(["Completed"]).sum()),
            scheduled=("interview_status", lambda x: x.isin(["Scheduled"]).sum()),
            being_rescheduled=("interview_status", lambda x: x.isin(["Being Rescheduled"]).sum()),
            no_low_response=("interview_status", lambda x: x.isin([
                "No Show",
                "On Hold",
                "Contacted",
                "Not Contacted"
            ]).sum()),
            cancelled=("interview_status", lambda x: x.isin(["Cancelled"]).sum()),
        )
        .reset_index()
    )

    # ── Completion rate bar chart ─────────────────────────────
    st.write("### Completion by Interviewer")

    fig = px.bar(
        by_interviewer,
        x="interviewer",
        y=[
            "completed",
            "scheduled",
            "being_rescheduled",
            "no_low_response",
            "cancelled"
        ],
        title="Interview Status by Interviewer",
        labels={"value": "Count", "interviewer": "Interviewer"},
        color_discrete_map={
            "completed": "#2ecc71",
            "scheduled": "#3498db",
            "being_rescheduled": "#f39c12",
            "no_low_response": "#95a5a6",
            "cancelled": "#e74c3c"
        },
        barmode="stack"
    )

    fig.update_layout(
        legend_title="Status",
        xaxis_tickangle=-30,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Detailed table ────────────────────────────────────────
    st.write("### Breakdown by Interviewer")

    display_df = by_interviewer[[
        "interviewer",
        "total",
        "completed",
        "scheduled",
        "being_rescheduled",
        "no_low_response",
        "cancelled"
    ]].copy()

    display_df.columns = [
        "Interviewer",
        "Total",
        "Completed",
        "Scheduled",
        "Being Rescheduled",
        "No/Low Response",
        "Cancelled"
    ]

    display_df["Completion %"] = (
        display_df["Completed"] / display_df["Total"] * 100
    ).round(1).astype(str) + "%"

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ── Pie chart overall status ──────────────────────────────
    st.write("### Overall Status Distribution")

    pie_data = {
        "Completed": completed,
        "Scheduled/In Progress": scheduled,
        "No/Low Response": no_low_response,
        "Cancelled": cancelled
    }

    fig2 = px.pie(
        values=list(pie_data.values()),
        names=list(pie_data.keys()),
        color_discrete_sequence=[
            "#2ecc71",
            "#3498db",
            "#95a5a6",
            "#e74c3c"
        ]
    )

    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)