import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime


def show(API_URL, headers):
    st.title("📈 Project Progress")
    st.caption("Gantt chart and progress overview for all active projects")

    # Load projects
    with st.spinner("Loading projects..."):
        try:
            r = requests.get(f"{API_URL}/projects/", headers=headers)
            projects = r.json()
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            return

    # Load completion data
    try:
        r = requests.get(
            f"{API_URL}/dashboard/by-project", headers=headers
        )
        by_project = r.json()
    except Exception:
        by_project = []

    if not projects:
        st.info("No projects yet.")
        return

    df = pd.DataFrame(projects)
    completion_map = {
        p["project_number"]: p for p in by_project
    }

    # ── Filters ──────────────────────────────────────────────────
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
        search = st.text_input("🔍 Search project")

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
                search, case=False, na=False
            )
        ]

    st.write(f"**{len(filtered)} projects**")
    st.divider()

    if filtered.empty:
        st.info("No projects match your filters.")
        return

    # ── Summary KPIs ─────────────────────────────────────────────
    st.write("### Summary")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    total_target = 0
    total_completed = 0
    projects_on_track = 0
    projects_at_risk = 0

    for _, row in filtered.iterrows():
        comp = completion_map.get(row.get("project_number", ""), {})
        pct = comp.get("pct_complete", 0)
        target = row.get("interviews_target", 8) or 8
        completed = comp.get("completed_interviews", 0)
        total_target += target
        total_completed += completed
        if pct >= 50:
            projects_on_track += 1
        else:
            projects_at_risk += 1

    overall_pct = round(
        total_completed / total_target * 100, 1
    ) if total_target else 0

    kpi1.metric("Projects", len(filtered))
    kpi2.metric("Overall Progress", f"{overall_pct}%")
    kpi3.metric("✅ On Track (≥50%)", projects_on_track)
    kpi4.metric("⚠️ At Risk (<50%)", projects_at_risk)

    st.divider()

    # ── Tabs ─────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📊 Gantt Chart",
        "📈 Interview Progress",
        "📋 Milestone Table"
    ])

    # ── Tab 1: Gantt Chart ───────────────────────────────────────
    with tab1:
        st.write("### Project Timeline — Gantt Chart")
        st.caption(
            "Shows project lifecycle from Booking to Publication. "
            "Hover over bars for details."
        )

        milestone_pairs = [
            ("booking_date", "kickoff_date", "Booking → Kickoff"),
            ("kickoff_date", "briefing_date", "Kickoff → Briefing"),
            ("briefing_date", "first_contact_date",
             "Briefing → First Contact"),
            ("first_contact_date", "interviews_complete_date",
             "Interviewing"),
            ("interviews_complete_date", "results_presentation_date",
             "Analysis → Readout"),
            ("results_presentation_date", "wp_draft_from_bv",
             "Readout → WP Draft"),
            ("wp_draft_from_bv", "publication_date",
             "WP Draft → Publication"),
        ]

        colors = {
            "Booking → Kickoff": "#3498db",
            "Kickoff → Briefing": "#2ecc71",
            "Briefing → First Contact": "#f39c12",
            "Interviewing": "#e74c3c",
            "Analysis → Readout": "#9b59b6",
            "Readout → WP Draft": "#1abc9c",
            "WP Draft → Publication": "#e67e22",
        }

        gantt_rows = []

        for _, row in filtered.iterrows():
            project_name = row.get("project_name", "")
            project_number = row.get("project_number", "")
            label = f"{project_name[:40]}..." \
                if len(project_name) > 40 else project_name

            for start_col, end_col, phase in milestone_pairs:
                start_val = row.get(start_col)
                end_val = row.get(end_col)

                try:
                    start_date = pd.to_datetime(start_val)
                    end_date = pd.to_datetime(end_val)
                    if pd.isna(start_date) or pd.isna(end_date):
                        continue
                    if start_date >= end_date:
                        continue
                except Exception:
                    continue

                gantt_rows.append({
                    "Project": label,
                    "Project Number": project_number,
                    "Phase": phase,
                    "Start": start_date,
                    "Finish": end_date,
                    "BV Lead": row.get("bv_lead", ""),
                    "IDC PM": row.get("bvd", ""),
                })

        if not gantt_rows:
            st.info(
                "No milestone dates entered yet for these projects. "
                "PMs need to fill in dates in the Time Tracker."
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
                    "Phase": True,
                    "Start": "|%b %d, %Y",
                    "Finish": "|%b %d, %Y",
                },
                title="Project Milestones Timeline"
            )

            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                height=max(400, len(filtered) * 45),
                xaxis_title="Date",
                yaxis_title="",
                legend_title="Phase",
                showlegend=True,
            )

            # Add today line
            fig.add_vline(
                x=datetime.now(),
                line_dash="dash",
                line_color="white",
                opacity=0.5,
                annotation_text="Today",
                annotation_position="top"
            )

            st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: Interview Progress ────────────────────────────────
    with tab2:
        st.write("### Interview Completion by Project")

        progress_rows = []
        for _, row in filtered.iterrows():
            comp = completion_map.get(
                row.get("project_number", ""), {}
            )
            pct = comp.get("pct_complete", 0)
            target = row.get("interviews_target", 8) or 8
            completed = comp.get("completed_interviews", 0)
            total = comp.get("total_interviews", 0)

            progress_rows.append({
                "project_name": row.get("project_name", ""),
                "project_number": row.get("project_number", ""),
                "bv_lead": row.get("bv_lead", ""),
                "bvd": row.get("bvd", ""),
                "target": target,
                "total": total,
                "completed": completed,
                "pct_complete": pct,
            })

        prog_df = pd.DataFrame(progress_rows)
        prog_df = prog_df.sort_values(
            "pct_complete", ascending=True
        )

        # Horizontal bar chart
        fig2 = go.Figure()

        fig2.add_trace(go.Bar(
            name="Completed",
            x=prog_df["completed"],
            y=prog_df["project_name"],
            orientation="h",
            marker_color="#2ecc71",
            text=prog_df["completed"],
            textposition="inside",
        ))

        fig2.add_trace(go.Bar(
            name="In Progress",
            x=prog_df["total"] - prog_df["completed"],
            y=prog_df["project_name"],
            orientation="h",
            marker_color="#3498db",
        ))

        fig2.add_trace(go.Bar(
            name="Remaining",
            x=prog_df["target"] - prog_df["total"],
            y=prog_df["project_name"],
            orientation="h",
            marker_color="#ecf0f1",
            opacity=0.5,
        ))

        fig2.update_layout(
            barmode="stack",
            height=max(400, len(prog_df) * 40),
            xaxis_title="Number of Interviews",
            yaxis_title="",
            legend_title="Status",
            title="Interview Progress vs Target"
        )

        st.plotly_chart(fig2, use_container_width=True)

        # Progress table with color coding
        st.write("### Detail Table")

        display_df = prog_df[[
            "project_number", "project_name",
            "bv_lead", "bvd",
            "completed", "total", "target", "pct_complete"
        ]].copy()

        display_df.columns = [
            "Project #", "Project Name",
            "BV Lead", "IDC PM",
            "Completed", "Total", "Target", "% Complete"
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
        st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Tab 3: Milestone Table ───────────────────────────────────
    with tab3:
        st.write("### Milestone Dates Overview")

        milestone_cols = [
            "project_number", "project_name", "bv_lead", "bvd",
            "booking_date", "kickoff_date", "briefing_date",
            "first_contact_date", "interviews_complete_date",
            "results_presentation_date", "wp_draft_from_bv",
            "wp_draft_to_client", "publication_date"
        ]

        existing = [c for c in milestone_cols if c in filtered.columns]
        milestone_df = filtered[existing].copy()

        milestone_df.columns = [
            c.replace("_", " ").title()
            for c in existing
        ]

        # Highlight past-due dates in red
        today = pd.Timestamp(date.today())

        def highlight_dates(val):
            if val == "" or val is None or pd.isna(val) \
                    if not isinstance(val, str) else val == "":
                return ""
            try:
                if pd.to_datetime(val) < today:
                    return "color: #e74c3c"
                return "color: #2ecc71"
            except Exception:
                return ""

        date_columns = [
            c for c in milestone_df.columns
            if "Date" in c or "From" in c or "To" in c
        ]

        styled_m = milestone_df.style.applymap(
            highlight_dates, subset=date_columns
        )

        st.dataframe(
            styled_m,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "🔴 Red dates = past due | "
            "🟢 Green dates = upcoming"
        )