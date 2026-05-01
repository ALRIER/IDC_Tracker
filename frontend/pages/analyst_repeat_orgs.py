import streamlit as st
import requests
import pandas as pd
import plotly.express as px

def show(API_URL, headers):
    st.title("🔄 Repeat Organisations")
    st.caption("Companies appearing in more than one project")

    # Load data
    with st.spinner("Loading repeat organisations..."):
        try:
            r = requests.get(
                f"{API_URL}/dashboard/repeat-orgs", headers=headers)
            data = r.json()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if not data:
        st.info("No repeat organisations found yet.")
        return

    df = pd.DataFrame(data)

    # ── Summary metrics ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Repeat Organisations", len(df))
    col2.metric("Max Projects", int(df["project_count"].max()))
    col3.metric(
        "Avg Projects per Org",
        round(df["project_count"].mean(), 1)
    )

    st.divider()

    # ── Bar chart ────────────────────────────────────────────────
    st.write("### Organisations by Project Count")

    top_df = df.head(20)

    fig = px.bar(
        top_df.sort_values("project_count", ascending=True),
        x="project_count",
        y="org_name",
        orientation="h",
        color="project_count",
        color_continuous_scale=["#3498db", "#2ecc71"],
        labels={
            "project_count": "Number of Projects",
            "org_name": "Organisation"
        },
        text="project_count"
    )
    fig.update_traces(
        texttemplate="%{text}", textposition="outside"
    )
    fig.update_layout(
        height=max(300, len(top_df) * 35),
        coloraxis_showscale=False,
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Detailed list ────────────────────────────────────────────
    st.write("### Organisation Detail")

    # Search
    search = st.text_input(
        "🔍 Search organisation", placeholder="Type to filter..."
    )

    filtered_df = df
    if search:
        filtered_df = df[
            df["org_name"].str.contains(
                search, case=False, na=False
            )
        ]

    st.write(f"Showing **{len(filtered_df)}** organisations")

    for _, row in filtered_df.iterrows():
        projects_list = row.get("projects", [])
        if isinstance(projects_list, list):
            projects_str = " · ".join(projects_list)
        else:
            projects_str = str(projects_list)

        with st.expander(
            f"🏢 {row['org_name']} — "
            f"{row['project_count']} projects"
        ):
            st.write("**Appears in these projects:**")
            if isinstance(projects_list, list):
                for proj in projects_list:
                    st.write(f"  • {proj}")
            else:
                st.write(projects_str)

    st.divider()

    # ── Table view ───────────────────────────────────────────────
    st.write("### Full Table")

    display_df = filtered_df[["org_name", "project_count"]].copy()
    display_df.columns = ["Organisation", "Project Count"]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )