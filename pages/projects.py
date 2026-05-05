import streamlit as st
from utils.database import (get_all_projects, create_project, get_project,
                             update_project_status, delete_project,
                             get_all_teams, get_milestones, create_milestone,
                             update_milestone_status, get_tasks,
                             project_name_exists)
from utils.email_utils import send_project_update, get_smtp_config
from datetime import date

def show():
    user = st.session_state.user
    role = user['role']

    st.markdown("<h1 style='color:#1e1b4b;'>📁 Projects</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 All Projects", "➕ New Project" if role == 'admin' else "📋 My Projects"])

    with tab1:
        projects = get_all_projects(user['id'], role)

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.selectbox("Filter by Status", ["All", "active", "completed", "onhold"])
        with col2:
            filter_priority = st.selectbox("Filter by Priority", ["All", "high", "medium", "low"])
        with col3:
            search = st.text_input("🔍 Search", placeholder="Search project...")

        if filter_status != "All":
            projects = [p for p in projects if p['status'] == filter_status]
        if filter_priority != "All":
            projects = [p for p in projects if p['priority'] == filter_priority]
        if search:
            projects = [p for p in projects if search.lower() in p['name'].lower()]

        if not projects:
            st.info("No projects found.")
        else:
            for p in projects:
                total = p['task_count'] or 0
                done = p['done_count'] or 0
                pct = int((done / total * 100) if total > 0 else 0)
                priority_colors = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'}
                pc = priority_colors.get(p['priority'], '#667eea')

                with st.expander(f"📁 {p['name']}  —  {p['status'].upper()}  ({pct}% complete)", expanded=False):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Description:** {p['description'] or 'N/A'}")
                        st.markdown(f"**Team:** {p['team_name'] or 'None'}")
                        st.markdown(f"**Priority:** <span class='badge badge-{p['priority']}'>{p['priority'].upper()}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Timeline:** {p['start_date'] or '—'} → {p['end_date'] or '—'}")
                        st.markdown(f"**Progress:** {done}/{total} tasks done")
                        st.progress(pct / 100)

                    with c2:
                        st.markdown("**Quick Actions**")
                        new_status = st.selectbox("Change Status", ["active", "completed", "onhold"],
                                                  index=["active", "completed", "onhold"].index(p['status']),
                                                  key=f"status_{p['id']}")
                        if st.button("Update Status", key=f"upd_{p['id']}", use_container_width=True):
                            update_project_status(p['id'], new_status)
                            st.toast("✅ Status updated!", icon="📁")
                            st.rerun()

                        if st.button("📋 View Tasks", key=f"tasks_{p['id']}", use_container_width=True):
                            st.session_state.selected_project = p['id']
                            st.session_state.page = 'tasks'
                            st.rerun()

                        if st.button("📊 Kanban", key=f"kanban_{p['id']}", use_container_width=True):
                            st.session_state.selected_project = p['id']
                            st.session_state.page = 'kanban'
                            st.rerun()

                        if role == 'admin':
                            if st.button("🗑️ Delete", key=f"del_{p['id']}", use_container_width=True):
                                delete_project(p['id'])
                                st.success("Project deleted!")
                                st.rerun()

                    # Milestones
                    st.markdown("---")
                    st.markdown("**🏁 Milestones**")
                    milestones = get_milestones(p['id'])
                    mc1, mc2 = st.columns([2, 1])
                    with mc1:
                        if milestones:
                            for m in milestones:
                                status_icon = {'pending': '⏳', 'inprogress': '🔄', 'completed': '✅'}.get(m['status'], '⏳')
                                st.markdown(f"{status_icon} **{m['title']}** — Due: {m['due_date'] or 'N/A'} — {m['status']}")
                                ns = st.selectbox("", ["pending", "inprogress", "completed"],
                                                  index=["pending", "inprogress", "completed"].index(m['status']),
                                                  key=f"ms_{m['id']}")
                                if ns != m['status']:
                                    update_milestone_status(m['id'], ns)
                                    st.rerun()
                        else:
                            st.caption("No milestones yet.")

                    with mc2:
                        if role == 'admin':
                            with st.form(f"ms_form_{p['id']}"):
                                st.markdown("**Add Milestone**")
                                ms_title = st.text_input("Title", key=f"mst_{p['id']}")
                                ms_desc = st.text_input("Description", key=f"msd_{p['id']}")
                                ms_due = st.date_input("Due Date", key=f"msdate_{p['id']}")
                                if st.form_submit_button("Add"):
                                    if ms_title:
                                        create_milestone(p['id'], ms_title, ms_desc, str(ms_due))
                                        st.success("Milestone added!")
                                        st.rerun()

                    # Send project update email
                    if role == 'admin':
                        st.markdown("---")
                        st.markdown("**📧 Send Project Update Email**")
                        with st.form(f"update_form_{p['id']}"):
                            update_text = st.text_area("Update Message", placeholder="Enter project status update...", key=f"upd_text_{p['id']}")
                            if st.form_submit_button("📧 Send to Team"):
                                if update_text:
                                    from utils.database import get_team_members
                                    members = get_team_members(p['team_id']) if p['team_id'] else []
                                    emails = [m['email'] for m in members if m['email']]
                                    if emails:
                                        results = send_project_update(p['name'], update_text, emails, user['name'])
                                        ok_count = sum(1 for _, ok, _ in results if ok)
                                        st.success(f"Update sent to {ok_count}/{len(emails)} team members!")
                                    else:
                                        st.warning("No team members with email found.")

    if role == 'admin':
        with tab2:
            with st.form("new_project_form"):
                st.markdown("### Create New Project")
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Project Name *")
                    description = st.text_area("Description")
                    teams = get_all_teams()
                    team_options = {t['name']: t['id'] for t in teams}
                    team_name = st.selectbox("Team", ["-- No Team --"] + list(team_options.keys()))
                with col2:
                    priority = st.selectbox("Priority", ["medium", "high", "low"])
                    start_date = st.date_input("Start Date", value=date.today())
                    end_date = st.date_input("End Date")

                submitted = st.form_submit_button("🚀 Create Project", use_container_width=True, type="primary")
                if submitted:
                    if not name:
                        st.error("Project name is required.")
                    elif project_name_exists(name):
                        st.error(f"❌ A project named '{name}' already exists. Please use a different name.")
                    else:
                        team_id = team_options.get(team_name) if team_name != "-- No Team --" else None
                        create_project(name, description, team_id, priority,
                                       str(start_date), str(end_date), user['id'])
                        st.toast(f"✅ Project '{name}' created successfully!", icon="🎉")
                        st.rerun()
