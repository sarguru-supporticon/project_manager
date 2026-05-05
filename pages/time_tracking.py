import streamlit as st
from utils.database import get_tasks, log_time, get_time_logs, get_all_projects
from datetime import date

def show():
    user = st.session_state.user
    role = user['role']

    st.markdown("<h1 style='color:#1e1b4b;'>⏱️ Time Tracking</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["⏱️ Log Time", "📊 Time Report"])

    with tab1:
        projects = get_all_projects(user['id'], role)
        if not projects:
            st.info("No projects available.")
            return

        proj_opts = {p['name']: p['id'] for p in projects}
        selected_proj = st.selectbox("Select Project", list(proj_opts.keys()))
        proj_id = proj_opts[selected_proj]

        tasks = get_tasks(project_id=proj_id, assigned_to=None if role == 'admin' else user['id'])
        if not tasks:
            st.info("No tasks found for this project.")
        else:
            task_opts = {f"{t['title']} [{t['status']}]": t['id'] for t in tasks}
            sel_task = st.selectbox("Select Task", list(task_opts.keys()))
            task_id = task_opts[sel_task]

            # Show current logged hours
            task = next((t for t in tasks if t['id'] == task_id), None)
            if task:
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Estimated Hours", f"{task['estimated_hours'] or 0:.1f} hrs")
                with c2:
                    st.metric("Total Logged", f"{task['logged_hours'] or 0:.1f} hrs")

            with st.form("log_time_form"):
                st.markdown("### Log Time")
                c1, c2 = st.columns(2)
                with c1:
                    hours = st.number_input("Hours *", min_value=0.25, max_value=24.0, step=0.25, value=1.0)
                    log_date = st.date_input("Date", value=date.today())
                with c2:
                    description = st.text_area("What did you work on?", placeholder="Describe your work...")

                if st.form_submit_button("⏱️ Log Time", use_container_width=True, type="primary"):
                    log_time(task_id, user['id'], hours, description, str(log_date))
                    st.success(f"✅ Logged {hours:.2f} hours successfully!")
                    st.rerun()

    with tab2:
        st.markdown("### 📊 Time Logs")

        c1, c2, c3 = st.columns(3)
        with c1:
            view_mine = st.checkbox("My Logs Only", value=(role != 'admin'))
        with c2:
            projects = get_all_projects(user['id'], role)
            proj_filter_opts = {"All Projects": None} | {p['name']: p['id'] for p in projects}
            sel_proj_filter = st.selectbox("Project Filter", list(proj_filter_opts.keys()))
            filter_proj_id = proj_filter_opts[sel_proj_filter]

        logs = get_time_logs(user_id=user['id'] if view_mine else None)

        # Filter by project
        if filter_proj_id:
            task_ids_in_proj = {t['id'] for t in get_tasks(project_id=filter_proj_id)}
            logs = [l for l in logs if l['task_id'] in task_ids_in_proj]

        if not logs:
            st.info("No time logs found.")
        else:
            total_hours = sum(l['hours'] for l in logs)
            st.metric("Total Hours", f"{total_hours:.2f} hrs")

            # Group by project
            from collections import defaultdict
            by_project = defaultdict(list)
            for l in logs:
                by_project[l['project_name']].append(l)

            for proj_name, proj_logs in by_project.items():
                proj_total = sum(l['hours'] for l in proj_logs)
                with st.expander(f"📁 {proj_name}  —  {proj_total:.2f} hrs total"):
                    for l in proj_logs:
                        st.markdown(f"""
                        <div style="background:#f8fafc;border-radius:8px;padding:10px 14px;
                                    margin-bottom:6px;border-left:3px solid #667eea;">
                            <div style="display:flex;justify-content:space-between;">
                                <strong>{l['task_title']}</strong>
                                <span style="color:#667eea;font-weight:700;">⏱️ {l['hours']:.2f} hrs</span>
                            </div>
                            <div style="font-size:12px;color:#64748b;margin-top:4px;">
                                👤 {l['user_name']}  ·  📅 {l['logged_date']}
                                {'  ·  ' + l['description'] if l['description'] else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            # Chart
            import pandas as pd
            df = pd.DataFrame(logs)
            if not df.empty:
                st.markdown("### 📈 Hours by User")
                user_hours = df.groupby('user_name')['hours'].sum().reset_index()
                st.bar_chart(user_hours.set_index('user_name'))

                st.markdown("### 📅 Hours by Date")
                date_hours = df.groupby('logged_date')['hours'].sum().reset_index()
                st.line_chart(date_hours.set_index('logged_date'))
