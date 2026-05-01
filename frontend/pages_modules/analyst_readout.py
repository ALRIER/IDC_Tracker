import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

def show(API_URL, headers):
    st.title("📅 Projected Readout")
    st.caption("Projected and scheduled readout dates by BV Lead")

    # Load data
    with st.spinner("Loading readout data..."):
        try:
            projects_r = requests.get(
                f"{API_URL}/projects/", headers=headers)
            byproject_r = requests.get(
                f"{API_URL}/dashboard/by-project", headers=headers)
            projects = projects_r.json()
            by_project = byproject_r.json()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if not projects:
        st.info("No active projects yet.")
        return

    # Merge project details with completion data
    completion_map = {
        p["project_number"]: p for p in by_project
    }

    rows = []
    for p in projects:
        if p.get("status") != "Active":
            continue

        comp = completion_map.get(p.get("project_number"), {})
        pct = comp.get("pct_complete", 0)
        completed = comp.get("completed_interviews", 0)
        target = comp.get("interviews_target",
                          p.get("interviews_target", 8))

        # Calculate projected readout date
        # Based on interviews_complete_date or estimated from progress
        projected_date = None
        if p.get("results_presentation_date"):
            projected_date = p["results_presentation_date"]
        elif p.get("interviews_complete_date") and pct >= 100:
            # Add 2 weeks after interviews complete
            base = pd.to_datetime(
                p["interviews_complete_date"]
            ).date()
            projected_date = base + timedelta(weeks=2)
        elif p.get("first_contact_date") and pct > 0:
            # Estimate based on current progress rate
            base = pd.to_datetime(
                p["first_contact_date"]
            ).date()
            days_elapsed = (date.today() - base).days
            if pct > 0:
                estimated_total_days = int(
                    days_elapsed / (pct / 100)
                )
                estimated_complete = base + timedelta(
                    days=estimated_total_days
                )
                projected_date = estimated_complete + timedelta(
                    weeks=2
                )

        rows.append({
            "project_number": p.get("project_number", ""),
            "project_name": p.get("project_name", ""),
            "bv_lead": p.get("bv_lead", ""),
            "idc_pm": p.get("bvd", ""),
            "target": target,
            "completed": completed,
            "pct_complete": pct,
            "interviews_complete_date": p.get(
                "interviews_complete_date", ""
            ),
            "results_presentation_date": p.get(
                "results_presentation_date", ""
            ),
            "projected_readout": str(projected_date)
            if projected_date else "TBD",
            "publication_date": p.get("publication_date", "")
        })

    df = pd.DataFrame(rows)

    # ── Summary by BV Lead ───────────────────────────────────────
    st.write("### Readout Schedule by BV Lead")

    bv_leads = sorted(df["bv_lead"].dropna().unique().tolist())

    if not bv_leads:
        st.info("No BV Leads assigned yet.")
    else:
        for lead in bv_leads:
            lead_df = df[df["bv_lead"] == lead]
            scheduled = lead_df[
                lead_df["results_presentation_date"] != ""
            ]

            with st.expander(
                f"👤 {lead} — "
                f"{len(lead_df)} projects | "
                f"{len(scheduled)} scheduled"
            ):
                for _, row in lead_df.iterrows():
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        st.write(
                            f"**{row['project_name']}**"
                        )
                        st.write(
                            f"#{row['project_number']} | "
                            f"IDC PM: {row['idc_pm']}"
                        )
                        st.progress(
                            min(row["pct_complete"] / 100, 1.0)
                        )
                        st.caption(
                            f"{row['completed']}/{row['target']} "
                            f"({row['pct_complete']}%)"
                        )

                    with col2:
                        st.write("**Key Dates**")
                        st.write(
                            f"Interviews done: "
                            f"{row.get('interviews_complete_date') or 'TBD'}"
                        )
                        st.write(
                            f"Projected readout: "
                            f"{row.get('projected_readout') or 'TBD'}"
                        )

                    with col3:
                        st.write("**Scheduled**")
                        if row.get("results_presentation_date"):
                            st.success(
                                f"📅 {row['results_presentation_date']}"
                            )
                        else:
                            st.warning("Not scheduled yet")

                        if row.get("publication_date"):
                            st.write(
                                f"Publication: "
                                f"{row['publication_date']}"
                            )

    st.divider()

    # ── Full table view ──────────────────────────────────────────
    st.write("### Full Readout Table")

    display_df = df[[
        "project_number",
        "project_name",
        "bv_lead",
        "idc_pm",
        "pct_complete",
        "interviews_complete_date",
        "projected_readout",
        "results_presentation_date",
        "publication_date"
    ]].copy()

    display_df.columns = [
        "Project #",
        "Project Name",
        "BV Lead",
        "IDC PM",
        "% Complete",
        "Interviews Done",
        "Projected Readout",
        "Scheduled Readout",
        "Publication"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )