import streamlit as st
import requests
import pandas as pd
import plotly.express as px

def show(API_URL, headers):
    st.title("📁 By Project")
    st.caption("Completion status for all active projects")

    # Load data
    with st.spinner("Loading project data..."):
        try:
            r = requests.get(
                f"{API_URL}/dashboard/by-project", headers=headers)
            data = r.json()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if not data:
        st.info("No active projects yet.")
        return

    df = pd.DataFrame(data)

    # ── Summary metrics ──────────────────────────────────────────
    total_projects = len(df)
    total_interviews = df["total_interviews"].sum()
    total_completed = df["completed_interviews"].sum()
    total_target = df["interviews_target"].sum()
    overall_pct = round(
        total_completed / total_target * 100, 1
    ) if total_target else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Projects", total_projects)
    col2.metric("Total Interviews", int(total_interviews))
    col3.metric("Completed", int(total_completed))
    col4.metric("Overall Progress", f"{overall_pct}%")

    st.divider()

    # ── Progress bar chart ───────────────────────────────────────
    st.write("### Completion by Project")

    fig = px.bar(
        df.sort_values("pct_complete", ascending=True),
        x="pct_complete",
        y="project_name",
        orientation="h",
        color="pct_complete",
        color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
        range_color=[0, 100],
        labels={
            "pct_complete": "% Complete",
            "project_name": "Project"
        },
        text="pct_complete"
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(
        height=max(300, len(df) * 40),
        coloraxis_showscale=False,
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Detailed table ───────────────────────────────────────────
    st.write("### Project Detail Table")

    # Filter by BV Lead
    bv_leads = ["All"] + sorted(
        df["bv_lead"].dropna().unique().tolist()
    )
    selected_lead = st.selectbox("Filter by BV Lead", bv_leads)

    if selected_lead != "All":
        df = df[df["bv_lead"] == selected_lead]

    display_df = df[[
        "project_number",
        "project_name",
        "idc_pm",
        "bv_lead",
        "interviews_target",
        "total_interviews",
        "completed_interviews",
        "pct_complete"
    ]].copy()

    display_df.columns = [
        "Project #",
        "Project Name",
        "IDC PM",
        "BV Lead",
        "Target",
        "Total",
        "Completed",
        "% Complete"
    ]

    # Color code completion
    def color_pct(val):
        if val >= 80:
            return "background-color: #2ecc7133"
        elif val >= 50:
            return "background-color: #f39c1233"
        else:
            return "background-color: #e74c3c33"

    styled = display_df.style.applymap(
        color_pct, subset=["% Complete"]
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()

    # ── Projects needing attention ───────────────────────────────
    st.write("### ⚠️ Projects Needing Attention")
    st.caption("Less than 50% complete")

    attention = df[df["pct_complete"] < 50].sort_values("pct_complete")

    if attention.empty:
        st.success("All projects are on track! 🎉")
    else:
        for _, row in attention.iterrows():
            st.warning(
                f"**{row['project_name']}** ({row['project_number']}) — "
                f"{row['completed_interviews']}/{row['interviews_target']} "
                f"completed ({row['pct_complete']}%) — "
                f"BV Lead: {row.get('bv_lead', 'N/A')}"
            )