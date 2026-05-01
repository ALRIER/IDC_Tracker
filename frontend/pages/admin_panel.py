import streamlit as st
import requests
import pandas as pd

def show(API_URL, headers):
    st.title("⚙️ Admin Panel")
    st.caption("User management, dropdown configuration and system settings")

    tab1, tab2, tab3 = st.tabs([
        "👥 User Management",
        "🔧 Dropdown Config",
        "📤 Data Export"
    ])

    # ── Tab 1: User Management ───────────────────────────────────
    with tab1:
        st.write("### Current Users")

        try:
            r = requests.get(f"{API_URL}/admin/users", headers=headers)
            users = r.json()
        except Exception as e:
            st.error(f"Error loading users: {e}")
            users = []

        if users:
            df = pd.DataFrame(users)
            display_df = df[[
                "name", "email", "role",
                "interviewer_name", "is_active"
            ]].copy()
            display_df.columns = [
                "Name", "Email", "Role",
                "Interviewer Name", "Active"
            ]
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

        st.divider()
        st.write("### Add New User")

        with st.form("new_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Full Name *")
                email = st.text_input("Email *")
                password = st.text_input(
                    "Password *", type="password"
                )

            with col2:
                role = st.selectbox(
                    "Role *",
                    ["pm", "interviewer", "analyst", "admin"]
                )
                interviewer_name = st.text_input(
                    "Interviewer Name",
                    help="Required for interviewer role — "
                         "must match exactly the name used "
                         "in interview assignments"
                )
                is_active = st.checkbox("Active", value=True)

            submit = st.form_submit_button(
                "➕ Create User", use_container_width=True
            )

            if submit:
                if not name or not email or not password:
                    st.error("Name, email and password are required!")
                elif role == "interviewer" and not interviewer_name:
                    st.error(
                        "Interviewer name is required "
                        "for interviewer role!"
                    )
                else:
                    payload = {
                        "name": name,
                        "email": email,
                        "password": password,
                        "role": role,
                        "interviewer_name": interviewer_name
                        if interviewer_name else None
                    }
                    try:
                        r = requests.post(
                            f"{API_URL}/admin/users",
                            json=payload,
                            headers=headers
                        )
                        if r.status_code == 200:
                            st.success(f"✅ User {name} created!")
                            st.rerun()
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()
        st.write("### Deactivate User")

        if users:
            active_users = [
                u for u in users if u.get("is_active")
            ]
            user_options = {
                f"{u['name']} ({u['email']})": u["id"]
                for u in active_users
            }

            if user_options:
                selected_user = st.selectbox(
                    "Select user to deactivate",
                    list(user_options.keys())
                )
                if st.button(
                    "🚫 Deactivate User",
                    type="secondary"
                ):
                    user_id = user_options[selected_user]
                    try:
                        r = requests.delete(
                            f"{API_URL}/admin/users/{user_id}",
                            headers=headers
                        )
                        if r.status_code == 200:
                            st.success(
                                f"✅ {selected_user} deactivated"
                            )
                            st.rerun()
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── Tab 2: Dropdown Config ───────────────────────────────────
    with tab2:
        st.write("### Manage Dropdown Options")

        try:
            r = requests.get(
                f"{API_URL}/admin/dropdowns", headers=headers
            )
            dropdowns = r.json()
        except Exception as e:
            st.error(f"Error loading dropdowns: {e}")
            dropdowns = []

        categories = [
            "interview_status",
            "interview_quality",
            "industry",
            "country",
            "recruiting_partner",
            "project_type",
            "project_status"
        ]

        selected_cat = st.selectbox(
            "Select Category", categories
        )

        cat_items = [
            d for d in dropdowns
            if d["category"] == selected_cat
        ]

        if cat_items:
            st.write(
                f"**{len(cat_items)} options "
                f"in {selected_cat}:**"
            )
            for item in sorted(
                cat_items, key=lambda x: x["sort_order"]
            ):
                col1, col2 = st.columns([4, 1])
                with col1:
                    status = "✅" if item["is_active"] else "❌"
                    st.write(
                        f"{status} {item['value']} "
                        f"(order: {item['sort_order']})"
                    )
                with col2:
                    if item["is_active"]:
                        if st.button(
                            "Disable",
                            key=f"dis_{item['id']}"
                        ):
                            try:
                                requests.patch(
                                    f"{API_URL}/admin/dropdowns"
                                    f"/{item['id']}",
                                    json={"is_active": False},
                                    headers=headers
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        if st.button(
                            "Enable",
                            key=f"en_{item['id']}"
                        ):
                            try:
                                requests.patch(
                                    f"{API_URL}/admin/dropdowns"
                                    f"/{item['id']}",
                                    json={"is_active": True},
                                    headers=headers
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

        st.divider()
        st.write(f"### Add Option to {selected_cat}")

        with st.form("new_dropdown_form"):
            new_value = st.text_input("New value")
            new_order = st.number_input(
                "Sort order",
                value=len(cat_items) + 1,
                min_value=1
            )
            submit_dd = st.form_submit_button(
                "➕ Add Option", use_container_width=True
            )

            if submit_dd:
                if not new_value:
                    st.error("Please enter a value!")
                else:
                    try:
                        r = requests.post(
                            f"{API_URL}/admin/dropdowns",
                            json={
                                "category": selected_cat,
                                "value": new_value,
                                "sort_order": new_order
                            },
                            headers=headers
                        )
                        if r.status_code == 200:
                            st.success(
                                f"✅ '{new_value}' added!"
                            )
                            st.rerun()
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── Tab 3: Data Export ───────────────────────────────────────
    with tab3:
        st.write("### Export Data")
        st.caption(
            "Download current database as CSV files"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Export Projects**")
            if st.button(
                "📥 Download Projects CSV",
                use_container_width=True
            ):
                try:
                    r = requests.get(
                        f"{API_URL}/projects/",
                        headers=headers
                    )
                    df = pd.DataFrame(r.json())
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "💾 Save Projects.csv",
                        csv,
                        "projects.csv",
                        "text/csv",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

        with col2:
            st.write("**Export Interviews**")
            if st.button(
                "📥 Download Interviews CSV",
                use_container_width=True
            ):
                try:
                    r = requests.get(
                        f"{API_URL}/interviews/",
                        headers=headers
                    )
                    df = pd.DataFrame(r.json())
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "💾 Save Interviews.csv",
                        csv,
                        "interviews.csv",
                        "text/csv",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()
        st.write("### System Info")
        st.write(f"**API URL:** `{API_URL}`")
        st.write("**Database:** Supabase PostgreSQL")
        st.write("**Backend:** FastAPI on Render.com")
        st.write("**Frontend:** Streamlit Cloud")