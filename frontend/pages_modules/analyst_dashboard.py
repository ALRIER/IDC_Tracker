import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show(API_URL, headers):
    st.title("📊 Program Dashboard")
    st.caption("Live overview of all interview activity")

    # Load data
    with st.spinner("Loading dashboard..."):
        try:
            summary_r = requests.get(
                f"{API_URL}/dashboard/summary", headers=headers)
            interviewer_r = requests.get(
                f"{API_URL}/dashboard/by-interviewer", headers=headers)
            summary = summary_r.json()
            by_interviewer = interviewer_r.json()
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")
            return

    # ── KPI Cards ───────────────────────────────────────────────
    st.write("### Program Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Interviewees",
                summary.get("total_interviewees", 0))
    col2.metric("✅ Completed",
                summary.get("completed", 0))
    col3.metric("📅 Scheduled / In Progress",
                summary.get("scheduled_in_progress", 0))
    col4.metric("📭 No / Low Response",
                summary.get("no_low_response", 0))
    col5.metric("❌ Cancelled",
                summary.get("cancelled", 0))

    st.divider()

    if not by_interviewer:
        st.info("No interview data yet.")
        return

    df = pd.DataFrame(by_interviewer)

    # ── Completion rate bar chart ────────────────────────────────
    st.write("### Completion by Interviewer")

    fig = px.bar(
        df,
        x="interviewer",
        y=["completed", "scheduled", "being_rescheduled",
           "no_low_response", "cancelled"],
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

    # ── Detailed table ───────────────────────────────────────────
    st.write("### Breakdown by Interviewer")

    display_df = df[[
        "interviewer", "total", "completed",
        "scheduled", "being_rescheduled",
        "no_low_response", "cancelled"
    ]].copy()

    display_df.columns = [
        "Interviewer", "Total", "Completed",
        "Scheduled", "Being Rescheduled",
        "No/Low Response", "Cancelled"
    ]

    # Add completion rate column
    display_df["Completion %"] = (
        display_df["Completed"] / display_df["Total"] * 100
    ).round(1).astype(str) + "%"

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ── Pie chart overall status ─────────────────────────────────
    st.write("### Overall Status Distribution")

    pie_data = {
        "Completed": summary.get("completed", 0),
        "Scheduled/In Progress": summary.get("scheduled_in_progress", 0),
        "No/Low Response": summary.get("no_low_response", 0),
        "Cancelled": summary.get("cancelled", 0)
    }

    fig2 = px.pie(
        values=list(pie_data.values()),
        names=list(pie_data.keys()),
        color_discrete_sequence=[
            "#2ecc71", "#3498db", "#95a5a6", "#e74c3c"
        ]
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)