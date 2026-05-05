import streamlit as st
from utils.database import (get_all_teams, create_team, get_team_members,
                             add_team_member, remove_team_member, get_all_users, delete_team,
                             team_name_exists)

def show():
    user = st.session_state.user
    role = user['role']

    if role != 'admin':
        st.warning("Access denied. Admin only.")
        return

    st.markdown("<h1 style='color:#1e1b4b;'>👥 Teams</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👥 All Teams", "➕ Create Team"])

    with tab1:
        teams = get_all_teams()
        if not teams:
            st.info("No teams yet. Create your first team!")
        else:
            for t in teams:
                with st.expander(f"👥 {t['name']}  —  {t['member_count']} members"):
                    st.markdown(f"**Description:** {t['description'] or 'N/A'}")
                    st.markdown(f"**Created by:** {t['creator_name']}")
                    st.markdown(f"**Created:** {t['created_at'][:10]}")

                    members = get_team_members(t['id'])
                    st.markdown("**Members:**")
                    for m in members:
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            icon = '👑' if m['role'] == 'admin' else '👤'
                            st.markdown(f"{icon} {m['name']} ({m['email']})")
                        with c2:
                            if m['id'] != user['id']:
                                if st.button("Remove", key=f"rem_{t['id']}_{m['id']}"):
                                    remove_team_member(t['id'], m['id'])
                                    st.toast(f"Removed {m['name']} from team.", icon="✂️")
                                    st.rerun()

                    st.markdown("**Add Member:**")
                    all_users = get_all_users()
                    member_ids = {m['id'] for m in members}
                    non_members = [u for u in all_users if u['id'] not in member_ids]
                    if non_members:
                        user_opts = {u['name'] + f" ({u['email']})": u['id'] for u in non_members}
                        sel = st.selectbox("Select User", list(user_opts.keys()), key=f"addmem_{t['id']}")
                        if st.button("➕ Add", key=f"add_{t['id']}"):
                            add_team_member(t['id'], user_opts[sel])
                            st.toast(f"✅ Member added to team!", icon="👥")
                            st.rerun()
                    else:
                        st.caption("All users are already in this team.")

                    st.markdown("---")
                    if st.button("🗑️ Delete Team", key=f"delteam_{t['id']}"):
                        delete_team(t['id'])
                        st.success("Team deleted!")
                        st.rerun()

    with tab2:
        with st.form("create_team_form"):
            st.markdown("### Create New Team")
            name = st.text_input("Team Name *")
            description = st.text_area("Description")

            all_users = get_all_users()
            user_opts = {u['name'] + f" ({u['email']})": u['id'] for u in all_users}
            initial_members = st.multiselect("Initial Members", list(user_opts.keys()))

            if st.form_submit_button("👥 Create Team", use_container_width=True, type="primary"):
                if not name:
                    st.error("Team name is required.")
                elif team_name_exists(name):
                    st.error(f"❌ A team named '{name}' already exists. Please use a different name.")
                else:
                    tid = create_team(name, description, user['id'])
                    for m_name in initial_members:
                        add_team_member(tid, user_opts[m_name])
                    st.toast(f"✅ Team '{name}' created successfully!", icon="🎉")
                    st.rerun()
