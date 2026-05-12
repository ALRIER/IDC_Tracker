import streamlit as st
import requests
import pandas as pd
import plotly.express as px


PROJECT_DATE_COLUMNS = [
    "booking_date",
    "kickoff_date",
    "briefing_date",
    "first_contact_date",
    "interviews_complete_date",
    "results_presentation_date",
    "publication_date",
    "created_at",
    "updated_at",
]


def get_json(url, headers):
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def clean_options(series):
    if series is None:
        return []

    values = (
        series.dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    return sorted([x for x in values if x and x.lower() not in ["nan", "none"]])


def first_valid_year(row):
    for col in PROJECT_DATE_COLUMNS:
        if col in row and pd.notna(row[col]):
            dt = pd.to_datetime(row[col], errors="coerce")
            if pd.notna(dt):
                return int(dt.year)

    return None


def show(API_URL, headers):
    st.title("📁 By Project")
    st.caption("Completion status by project")

    # ── Load raw data ──────────────────────────────────────────
    with st.spinner("Loading project data..."):
        try:
            projects = get_json(f"{API_URL}/projects/", headers)
            interviews = get_json(f"{API_URL}/interviews/", headers)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if not projects:
        st.info("No projects available.")
        return

    projects_df = pd.DataFrame(projects)
    interviews_df = pd.DataFrame(interviews) if interviews else pd.DataFrame()

    # ── Ensure required project columns exist ──────────────────
    required_project_cols = [
        "id",
        "project_number",
        "project_name",
        "status",
        "bv_lead",
        "bvd",
        "interviews_target",
    ]

    for col in required_project_cols:
        if col not in projects_df.columns:
            projects_df[col] = None

    projects_df["interviews_target"] = pd.to_numeric(
        projects_df["interviews_target"],
        errors="coerce"
    ).fillna(0)

    projects_df["project_year"] = projects_df.apply(
        first_valid_year,
        axis=1
    )

    projects_df["status"] = projects_df["status"].fillna("Unknown")
    projects_df["bv_lead"] = projects_df["bv_lead"].fillna("")
    projects_df["bvd"] = projects_df["bvd"].fillna("")

    # ── Build interview counts ─────────────────────────────────
    if not interviews_df.empty:
        for col in ["project_id", "project_number", "interview_status"]:
            if col not in interviews_df.columns:
                interviews_df[col] = None

        interviews_df["project_key"] = interviews_df["project_id"].astype(str)
        projects_df["project_key"] = projects_df["id"].astype(str)

        interview_counts = (
            interviews_df.groupby("project_key")
            .agg(
                total_interviews=("project_key", "count"),
                completed_interviews=(
                    "interview_status",
                    lambda x: x.isin(["Completed"]).sum()
                ),
                scheduled_interviews=(
                    "interview_status",
                    lambda x: x.isin(["Scheduled", "Being Rescheduled"]).sum()
                ),
                no_low_response=(
                    "interview_status",
                    lambda x: x.isin([
                        "No Show",
                        "On Hold",
                        "Contacted",
                        "Not Contacted"
                    ]).sum()
                ),
                cancelled_interviews=(
                    "interview_status",
                    lambda x: x.isin(["Cancelled"]).sum()
                ),
            )
            .reset_index()
        )

        df = projects_df.merge(
            interview_counts,
            on="project_key",
            how="left"
        )
    else:
        projects_df["project_key"] = projects_df["id"].astype(str)
        df = projects_df.copy()

    count_cols = [
        "total_interviews",
        "completed_interviews",
        "scheduled_interviews",
        "no_low_response",
        "cancelled_interviews",
    ]

    for col in count_cols:
        if col not in df.columns:
            df[col] = 0

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["pct_complete"] = df.apply(
        lambda row: round(
            row["completed_interviews"] / row["interviews_target"] * 100,
            1
        ) if row["interviews_target"] else 0,
        axis=1
    )

    # ── Filters ────────────────────────────────────────────────
    st.write("### Filters")

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)

    with fcol1:
        status_options = ["All"] + clean_options(df["status"])
        selected_status = st.selectbox("Project Status", status_options)

    with fcol2:
        available_years = sorted(
            [int(y) for y in df["project_year"].dropna().unique()],
            reverse=True
        )
        selected_year = st.selectbox("Project Year", ["All"] + available_years)

    with fcol3:
        bv_lead_options = ["All"] + clean_options(df["bv_lead"])
        selected_bv_lead = st.selectbox("BV Lead", bv_lead_options)

    with fcol4:
        bvd_options = ["All"] + clean_options(df["bvd"])
        selected_bvd = st.selectbox("IDC PM (BVD)", bvd_options)

    search = st.text_input("🔍 Search project name or project number")

    filtered = df.copy()

    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]

    if selected_year != "All":
        filtered = filtered[filtered["project_year"] == int(selected_year)]

    if selected_bv_lead != "All":
        filtered = filtered[filtered["bv_lead"] == selected_bv_lead]

    if selected_bvd != "All":
        filtered = filtered[filtered["bvd"] == selected_bvd]

    if search:
        search_mask = (
            filtered["project_name"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["project_number"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
        )
        filtered = filtered[search_mask]

    if filtered.empty:
        st.warning("No projects found for the selected filters.")
        return

    # ── Summary metrics ────────────────────────────────────────
    total_projects = len(filtered)
    total_interviews = filtered["total_interviews"].sum()
    total_completed = filtered["completed_interviews"].sum()
    total_target = filtered["interviews_target"].sum()

    overall_pct = round(
        total_completed / total_target * 100,
        1
    ) if total_target else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Projects", total_projects)
    col2.metric("Total Interviewees", int(total_interviews))
    col3.metric("Completed", int(total_completed))
    col4.metric("Overall Progress", f"{overall_pct}%")

    st.divider()

    # ── Progress bar chart ─────────────────────────────────────
    st.write("### Completion by Project")

    chart_df = filtered.copy()
    chart_df["project_label"] = (
        chart_df["project_name"].astype(str)
        + " ("
        + chart_df["project_number"].astype(str)
        + ")"
    )

    chart_df = chart_df.sort_values("pct_complete", ascending=True)

    fig = px.bar(
        chart_df,
        x="pct_complete",
        y="project_label",
        orientation="h",
        color="pct_complete",
        color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
        range_color=[0, 100],
        labels={
            "pct_complete": "% Complete",
            "project_label": "Project"
        },
        text="pct_complete"
    )

    fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside"
    )

    fig.update_layout(
        height=min(max(350, len(chart_df) * 38), 900),
        coloraxis_showscale=False,
        yaxis_title="",
        xaxis_range=[0, 110],
        margin=dict(l=10, r=30, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Detailed table ─────────────────────────────────────────
    st.write("### Project Detail Table")

    display_df = filtered[[
        "project_number",
        "project_name",
        "status",
        "project_year",
        "bvd",
        "bv_lead",
        "interviews_target",
        "total_interviews",
        "completed_interviews",
        "scheduled_interviews",
        "no_low_response",
        "cancelled_interviews",
        "pct_complete",
    ]].copy()

    display_df = display_df.sort_values(
        ["status", "pct_complete", "project_name"],
        ascending=[True, True, True]
    )

    display_df.columns = [
        "Project #",
        "Project Name",
        "Status",
        "Year",
        "IDC PM",
        "BV Lead",
        "Target",
        "Total",
        "Completed",
        "Scheduled/In Progress",
        "No/Low Response",
        "Cancelled",
        "% Complete",
    ]

    def color_pct(val):
        if val >= 80:
            return "background-color: #2ecc7133"
        elif val >= 50:
            return "background-color: #f39c1233"
        else:
            return "background-color: #e74c3c33"

    styled = display_df.style.map(
        color_pct,
        subset=["% Complete"]
    )

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ── Projects needing attention ─────────────────────────────
    st.write("### ⚠️ Projects Needing Attention")
    st.caption("Projects below 50% completion")

    attention = filtered[
        (filtered["pct_complete"] < 50)
        & (filtered["interviews_target"] > 0)
    ].sort_values("pct_complete")

    if attention.empty:
        st.success("All filtered projects are on track!")
    else:
        for _, row in attention.iterrows():
            st.warning(
                f"**{row['project_name']}** "
                f"({row['project_number']}) — "
                f"{row['completed_interviews']}/"
                f"{int(row['interviews_target'])} completed "
                f"({row['pct_complete']}%) — "
                f"BV Lead: {row.get('bv_lead') or 'N/A'}"
            )