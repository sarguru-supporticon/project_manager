import streamlit as st
import pandas as pd
from utils.database import get_all_projects, get_tasks, get_time_logs, get_all_users

def show():
    user = st.session_state.user
    role = user['role']

    st.markdown("<h1 style='color:#1e1b4b;'>📈 Reports</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Project Overview", "👤 Team Performance", "⏱️ Time Analysis"])

    with tab1:
        st.markdown("### Project Status Overview")
        projects = get_all_projects(user['id'], role)

        if not projects:
            st.info("No projects to report on.")
            return

        rows = []
        for p in projects:
            tasks = get_tasks(project_id=p['id'])
            total = len(tasks)
            done = len([t for t in tasks if t['status'] == 'done'])
            inprog = len([t for t in tasks if t['status'] == 'inprogress'])
            todo = len([t for t in tasks if t['status'] == 'todo'])
            review = len([t for t in tasks if t['status'] == 'review'])
            pct = round((done / total * 100) if total > 0 else 0, 1)
            total_hours = sum(t['logged_hours'] or 0 for t in tasks)
            rows.append({
                'Project': p['name'],
                'Team': p['team_name'] or 'N/A',
                'Status': p['status'],
                'Priority': p['priority'],
                'Total Tasks': total,
                'To Do': todo,
                'In Progress': inprog,
                'Review': review,
                'Done': done,
                'Progress (%)': pct,
                'Hours Logged': round(total_hours, 2),
                'Start': p['start_date'] or '—',
                'End': p['end_date'] or '—',
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Charts
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Task Distribution by Status**")
            status_counts = {
                'To Do': sum(r['To Do'] for r in rows),
                'In Progress': sum(r['In Progress'] for r in rows),
                'Review': sum(r['Review'] for r in rows),
                'Done': sum(r['Done'] for r in rows),
            }
            st.bar_chart(pd.DataFrame.from_dict(status_counts, orient='index', columns=['Tasks']))

        with c2:
            st.markdown("**Progress by Project**")
            progress_df = pd.DataFrame({'Progress (%)': df.set_index('Project')['Progress (%)']})
            st.bar_chart(progress_df)

        # Download
        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv, "project_report.csv", "text/csv")

    with tab2:
        st.markdown("### Team Performance")
        users = get_all_users()
        rows = []
        for u in users:
            tasks = get_tasks(assigned_to=u['id'])
            total = len(tasks)
            done = len([t for t in tasks if t['status'] == 'done'])
            inprog = len([t for t in tasks if t['status'] == 'inprogress'])
            logs = get_time_logs(user_id=u['id'])
            hours = sum(l['hours'] for l in logs)
            rows.append({
                'Name': u['name'],
                'Email': u['email'],
                'Role': u['role'],
                'Total Tasks': total,
                'In Progress': inprog,
                'Completed': done,
                'Completion Rate (%)': round((done / total * 100) if total > 0 else 0, 1),
                'Hours Logged': round(hours, 2),
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Tasks Completed by Member**")
            st.bar_chart(df.set_index('Name')['Completed'])
        with c2:
            st.markdown("**Hours Logged by Member**")
            st.bar_chart(df.set_index('Name')['Hours Logged'])

        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv, "team_report.csv", "text/csv")

    with tab3:
        st.markdown("### ⏱️ Time Analysis")
        logs = get_time_logs(user_id=None if role == 'admin' else user['id'])

        if not logs:
            st.info("No time logs yet.")
            return

        df = pd.DataFrame(logs)
        total = df['hours'].sum()
        st.metric("Total Hours Logged", f"{total:.2f} hrs")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Hours by Project**")
            proj_hours = df.groupby('project_name')['hours'].sum().sort_values(ascending=False)
            st.bar_chart(proj_hours)

        with c2:
            st.markdown("**Hours by User**")
            user_hours = df.groupby('user_name')['hours'].sum().sort_values(ascending=False)
            st.bar_chart(user_hours)

        st.markdown("**Daily Hours Trend**")
        daily = df.groupby('logged_date')['hours'].sum()
        st.line_chart(daily)

        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv, "time_report.csv", "text/csv")
