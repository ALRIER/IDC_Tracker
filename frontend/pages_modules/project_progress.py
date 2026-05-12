import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime


MILESTONE_DATE_COLS = [
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

STATUS_COMPLETED = ["Completed"]
STATUS_SCHEDULED = ["Scheduled", "Being Rescheduled"]
STATUS_NO_LOW = ["No Show", "On Hold", "Contacted", "Not Contacted"]
STATUS_CANCELLED = ["Cancelled"]


def get_json(url, headers):
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def clean_options(series):
    values = (
        series.dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    return sorted([x for x in values if x and x.lower() not in ["nan", "none"]])


def first_valid_year(row):
    for col in MILESTONE_DATE_COLS + ["created_at", "updated_at"]:
        if col in row and pd.notna(row[col]):
            dt = pd.to_datetime(row[col], errors="coerce")
            if pd.notna(dt):
                return int(dt.year)
    return None


def safe_date(value):
    dt = pd.to_datetime(value, errors="coerce")
    return dt if pd.notna(dt) else None


def build_project_label(project_name, project_number):
    name = str(project_name or "")
    number = str(project_number or "")
    if len(name) > 45:
        name = name[:45] + "..."
    return f"{name} ({number})"


def show(API_URL, headers):
    st.title("📈 Project Progress")
    st.caption("Gantt chart and progress overview by project milestones and interview completion")

    # ── Load data ──────────────────────────────────────────────
    with st.spinner("Loading project progress..."):
        try:
            projects = get_json(f"{API_URL}/projects/", headers)
            interviews = get_json(f"{API_URL}/interviews/", headers)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if not projects:
        st.info("No projects yet.")
        return

    projects_df = pd.DataFrame(projects)
    interviews_df = pd.DataFrame(interviews) if interviews else pd.DataFrame()

    required_project_cols = [
        "id",
        "project_number",
        "project_name",
        "status",
        "bv_lead",
        "bvd",
        "interviews_target",
        "interviews_complete",
    ] + MILESTONE_DATE_COLS

    for col in required_project_cols:
        if col not in projects_df.columns:
            projects_df[col] = None

    projects_df["status"] = projects_df["status"].fillna("Unknown")
    projects_df["bv_lead"] = projects_df["bv_lead"].fillna("")
    projects_df["bvd"] = projects_df["bvd"].fillna("")
    projects_df["project_year"] = projects_df.apply(first_valid_year, axis=1)

    projects_df["interviews_target"] = pd.to_numeric(
        projects_df["interviews_target"],
        errors="coerce"
    ).fillna(8)

    projects_df["interviews_complete"] = pd.to_numeric(
        projects_df["interviews_complete"],
        errors="coerce"
    ).fillna(0)

    # ── Interview counts from live interview table ─────────────
    projects_df["project_key"] = projects_df["id"].astype(str)

    if not interviews_df.empty:
        for col in ["project_id", "interview_status"]:
            if col not in interviews_df.columns:
                interviews_df[col] = None

        interviews_df["project_key"] = interviews_df["project_id"].astype(str)

        counts_df = (
            interviews_df.groupby("project_key")
            .agg(
                total_interviews=("project_key", "count"),
                completed_interviews=(
                    "interview_status",
                    lambda x: x.isin(STATUS_COMPLETED).sum()
                ),
                scheduled_interviews=(
                    "interview_status",
                    lambda x: x.isin(STATUS_SCHEDULED).sum()
                ),
                no_low_response=(
                    "interview_status",
                    lambda x: x.isin(STATUS_NO_LOW).sum()
                ),
                cancelled_interviews=(
                    "interview_status",
                    lambda x: x.isin(STATUS_CANCELLED).sum()
                ),
            )
            .reset_index()
        )

        df = projects_df.merge(counts_df, on="project_key", how="left")
    else:
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

    # Fallback: if there are no live interview counts, use project stored completed count
    df["completed_interviews"] = df.apply(
        lambda row: int(row["interviews_complete"])
        if row["completed_interviews"] == 0 and row["interviews_complete"] > 0
        else int(row["completed_interviews"]),
        axis=1
    )

    df["pct_complete"] = df.apply(
        lambda row: round(
            row["completed_interviews"] / row["interviews_target"] * 100,
            1
        ) if row["interviews_target"] else 0,
        axis=1
    )

    df["remaining_interviews"] = df.apply(
        lambda row: max(
            int(row["interviews_target"]) - int(row["total_interviews"]),
            0
        ),
        axis=1
    )

    # ── Filters ────────────────────────────────────────────────
    st.write("### Filters")

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)

    with fcol1:
        status_options = clean_options(df["status"])
        default_status = ["Active"] if "Active" in status_options else status_options
        selected_status = st.multiselect(
            "Project Status",
            status_options,
            default=default_status
        )

    with fcol2:
        years = sorted(
            [int(y) for y in df["project_year"].dropna().unique()],
            reverse=True
        )
        selected_year = st.selectbox("Project Year", ["All"] + years)

    with fcol3:
        bv_lead_options = ["All"] + clean_options(df["bv_lead"])
        selected_bv_lead = st.selectbox("BV Lead", bv_lead_options)

    with fcol4:
        bvd_options = ["All"] + clean_options(df["bvd"])
        selected_bvd = st.selectbox("IDC PM (BVD)", bvd_options)

    search = st.text_input("🔍 Search project name or project number")

    filtered = df.copy()

    if selected_status:
        filtered = filtered[filtered["status"].isin(selected_status)]

    if selected_year != "All":
        filtered = filtered[filtered["project_year"] == int(selected_year)]

    if selected_bv_lead != "All":
        filtered = filtered[filtered["bv_lead"] == selected_bv_lead]

    if selected_bvd != "All":
        filtered = filtered[filtered["bvd"] == selected_bvd]

    if search:
        filtered = filtered[
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
        ]

    if filtered.empty:
        st.info("No projects match your filters.")
        return

    st.write(f"**{len(filtered)} projects**")
    st.divider()

    # ── Summary KPIs ───────────────────────────────────────────
    total_target = filtered["interviews_target"].sum()
    total_completed = filtered["completed_interviews"].sum()

    overall_pct = round(
        total_completed / total_target * 100,
        1
    ) if total_target else 0

    projects_on_track = len(filtered[filtered["pct_complete"] >= 50])
    projects_at_risk = len(filtered[filtered["pct_complete"] < 50])

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric("Projects", len(filtered))
    kpi2.metric("Overall Progress", f"{overall_pct}%")
    kpi3.metric("✅ On Track (≥50%)", projects_on_track)
    kpi4.metric("⚠️ At Risk (<50%)", projects_at_risk)

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📊 Gantt Chart",
        "📈 Interview Progress",
        "📋 Milestone Table"
    ])

    # ── Tab 1: Gantt Chart ────────────────────────────────────
    with tab1:
        st.write("### Project Timeline — Gantt Chart")
        st.caption(
            "Shows project lifecycle from Booking to Publication. "
            "Bars are built from milestone dates; hover shows interview progress."
        )

        milestone_pairs = [
            ("booking_date", "kickoff_date", "Booking → Kickoff"),
            ("kickoff_date", "briefing_date", "Kickoff → Briefing"),
            ("briefing_date", "first_contact_date", "Briefing → First Contact"),
            ("first_contact_date", "interviews_complete_date", "Interviewing"),
            ("interviews_complete_date", "results_presentation_date", "Analysis → Readout"),
            ("results_presentation_date", "wp_draft_from_bv", "Readout → WP Draft"),
            ("wp_draft_from_bv", "wp_draft_to_client", "WP Draft → Client"),
            ("wp_draft_to_client", "client_approval", "Client Review"),
            ("client_approval", "publication_date", "Approval → Publication"),
        ]

        colors = {
            "Booking → Kickoff": "#3498db",
            "Kickoff → Briefing": "#2ecc71",
            "Briefing → First Contact": "#f39c12",
            "Interviewing": "#e74c3c",
            "Analysis → Readout": "#9b59b6",
            "Readout → WP Draft": "#1abc9c",
            "WP Draft → Client": "#e67e22",
            "Client Review": "#95a5a6",
            "Approval → Publication": "#27ae60",
        }

        gantt_rows = []

        for _, row in filtered.iterrows():
            project_label = build_project_label(
                row.get("project_name", ""),
                row.get("project_number", "")
            )

            for start_col, end_col, phase in milestone_pairs:
                start_date = safe_date(row.get(start_col))
                end_date = safe_date(row.get(end_col))

                if start_date is None or end_date is None:
                    continue

                if start_date >= end_date:
                    continue

                gantt_rows.append({
                    "Project": project_label,
                    "Project Number": row.get("project_number", ""),
                    "Phase": phase,
                    "Start": start_date,
                    "Finish": end_date,
                    "BV Lead": row.get("bv_lead", ""),
                    "IDC PM": row.get("bvd", ""),
                    "Completed Interviews": int(row.get("completed_interviews", 0)),
                    "Target Interviews": int(row.get("interviews_target", 0)),
                    "% Complete": row.get("pct_complete", 0),
                    "Status": row.get("status", ""),
                })

        if not gantt_rows:
            st.info(
                "No milestone date ranges available for the selected projects. "
                "PMs need to fill milestone dates in Overall Project Tracker."
            )
        else:
            gantt_df = pd.DataFrame(gantt_rows)

            fig = px.timeline(
                gantt_df,
                x_start="Start",
                x_end="Finish",
                y="Project",
                color="Phase",
                color_discrete_map=colors,
                hover_data={
                    "Project Number": True,
                    "BV Lead": True,
                    "IDC PM": True,
                    "Status": True,
                    "Completed Interviews": True,
                    "Target Interviews": True,
                    "% Complete": True,
                    "Start": "|%b %d, %Y",
                    "Finish": "|%b %d, %Y",
                },
                title="Project Milestones Timeline"
            )

            fig.update_yaxes(autorange="reversed")

            fig.update_layout(
                height=min(max(450, len(filtered) * 55), 1000),
                xaxis_title="Date",
                yaxis_title="",
                legend_title="Milestone Phase",
                showlegend=True,
                margin=dict(l=10, r=30, t=50, b=20)
            )

            fig.add_vline(
                x=datetime.now(),
                line_dash="dash",
                line_color="white",
                opacity=0.6,
                annotation_text="Today",
                annotation_position="top"
            )

            st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: Interview Progress ─────────────────────────────
    with tab2:
        st.write("### Interview Completion by Project")
        st.caption("Progress is calculated from completed interviews vs target interviews.")

        prog_df = filtered.copy()

        prog_df["project_label"] = prog_df.apply(
            lambda row: build_project_label(
                row.get("project_name", ""),
                row.get("project_number", "")
            ),
            axis=1
        )

        prog_df = prog_df.sort_values("pct_complete", ascending=True)

        fig2 = go.Figure()

        fig2.add_trace(go.Bar(
            name="Completed",
            x=prog_df["completed_interviews"],
            y=prog_df["project_label"],
            orientation="h",
            marker_color="#2ecc71",
            text=prog_df["completed_interviews"],
            textposition="inside",
        ))

        fig2.add_trace(go.Bar(
            name="Scheduled / In Progress",
            x=prog_df["scheduled_interviews"],
            y=prog_df["project_label"],
            orientation="h",
            marker_color="#3498db",
        ))

        fig2.add_trace(go.Bar(
            name="No / Low Response",
            x=prog_df["no_low_response"],
            y=prog_df["project_label"],
            orientation="h",
            marker_color="#95a5a6",
        ))

        fig2.add_trace(go.Bar(
            name="Cancelled",
            x=prog_df["cancelled_interviews"],
            y=prog_df["project_label"],
            orientation="h",
            marker_color="#e74c3c",
        ))

        fig2.add_trace(go.Bar(
            name="Remaining to Target",
            x=prog_df["remaining_interviews"],
            y=prog_df["project_label"],
            orientation="h",
            marker_color="#ecf0f1",
            opacity=0.5,
        ))

        fig2.update_layout(
            barmode="stack",
            height=min(max(450, len(prog_df) * 45), 1000),
            xaxis_title="Number of Interviews",
            yaxis_title="",
            legend_title="Interview Status",
            title="Interview Progress vs Target",
            margin=dict(l=10, r=30, t=50, b=20)
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.write("### Detail Table")

        display_df = prog_df[[
            "project_number",
            "project_name",
            "status",
            "project_year",
            "bv_lead",
            "bvd",
            "completed_interviews",
            "total_interviews",
            "interviews_target",
            "pct_complete"
        ]].copy()

        display_df.columns = [
            "Project #",
            "Project Name",
            "Status",
            "Year",
            "BV Lead",
            "IDC PM",
            "Completed",
            "Total",
            "Target",
            "% Complete"
        ]

        def color_row(row):
            pct = row["% Complete"]

            if pct >= 80:
                color = "background-color: #2ecc7133"
            elif pct >= 50:
                color = "background-color: #f39c1233"
            else:
                color = "background-color: #e74c3c33"

            return [color] * len(row)

        styled = display_df.style.apply(color_row, axis=1)

        st.dataframe(
            styled,
            use_container_width=True,
            hide_index=True
        )

    # ── Tab 3: Milestone Table ────────────────────────────────
    with tab3:
        st.write("### Milestone Dates Overview")

        milestone_cols = [
            "project_number",
            "project_name",
            "status",
            "project_year",
            "bv_lead",
            "bvd",
        ] + MILESTONE_DATE_COLS

        existing = [c for c in milestone_cols if c in filtered.columns]
        milestone_df = filtered[existing].copy()

        for col in MILESTONE_DATE_COLS:
            if col in milestone_df.columns:
                milestone_df[col] = pd.to_datetime(
                    milestone_df[col],
                    errors="coerce"
                ).dt.date

        milestone_df.columns = [
            c.replace("_", " ").title()
            for c in existing
        ]

        today = pd.Timestamp(date.today())

        def highlight_dates(val):
            if val == "" or val is None:
                return ""

            try:
                if pd.isna(val):
                    return ""
            except Exception:
                pass

            try:
                val_date = pd.to_datetime(val, errors="coerce")

                if pd.isna(val_date):
                    return ""

                if val_date < today:
                    return "color: #e74c3c"

                return "color: #2ecc71"

            except Exception:
                return ""

        date_columns = [
            c for c in milestone_df.columns
            if any(keyword in c for keyword in [
                "Date",
                "Booking",
                "Kickoff",
                "Briefing",
                "Draft",
                "Approved",
                "Approval",
                "Contact",
                "Interview",
                "Presentation",
                "Publication",
                "Editing",
                "Uplift",
                "Client"
            ])
        ]

        styled_m = milestone_df.style.map(
            highlight_dates,
            subset=date_columns
        )

        st.dataframe(
            styled_m,
            use_container_width=True,
            hide_index=True
        )

        st.caption("Red dates = past dates | Green dates = upcoming dates")