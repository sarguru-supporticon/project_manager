import streamlit as st
from utils.database import get_dashboard_stats, get_tasks, get_all_projects
from datetime import datetime, date

def show():
    user = st.session_state.user
    role = user['role']
    stats = get_dashboard_stats(user['id'], role)

    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <h1 style="margin:0;color:#1e1b4b;">{'🏠' if role!='admin' else '👑'} Dashboard</h1>
        <p style="color:#64748b;margin:4px 0 0;">Welcome back, <strong>{user['name']}</strong>!
        &nbsp;·&nbsp; {datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ──────────────────────────────────────────
    if role == 'admin':
        cols = st.columns(4)
        stat_data = [
            ("Total Projects", stats['total_projects'], "#667eea", "📁"),
            ("Active Projects", stats['active_projects'], "#10b981", "🟢"),
            ("Total Tasks", stats['total_tasks'], "#f59e0b", "✅"),
            ("Team Members", stats['total_users'], "#8b5cf6", "👥"),
        ]
        for col, (label, value, color, icon) in zip(cols, stat_data):
            with col:
                st.markdown(f"""
                <div class="pm-stat-card" style="border-top-color:{color};">
                    <div style="font-size:2rem;">{icon}</div>
                    <div class="pm-stat-number" style="color:{color};">{value}</div>
                    <div class="pm-stat-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cols2 = st.columns(4)
        stat_data2 = [
            ("Completed Tasks", stats['completed_tasks'], "#10b981", "✅"),
            ("Overdue Tasks", stats['overdue_tasks'], "#ef4444", "⚠️"),
            ("Total Teams", stats['total_teams'], "#667eea", "👥"),
            ("Hours Logged", f"{stats['total_hours']:.1f}h", "#f59e0b", "⏱️"),
        ]
        for col, (label, value, color, icon) in zip(cols2, stat_data2):
            with col:
                st.markdown(f"""
                <div class="pm-stat-card" style="border-top-color:{color};">
                    <div style="font-size:2rem;">{icon}</div>
                    <div class="pm-stat-number" style="color:{color};">{value}</div>
                    <div class="pm-stat-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        cols = st.columns(5)
        stat_data = [
            ("My Tasks", stats['my_tasks'], "#667eea", "📝"),
            ("In Progress", stats['in_progress'], "#f59e0b", "🔄"),
            ("Completed", stats['completed_tasks'], "#10b981", "✅"),
            ("Overdue", stats['overdue_tasks'], "#ef4444", "⚠️"),
            ("Hours Logged", f"{stats['total_hours']:.1f}h", "#8b5cf6", "⏱️"),
        ]
        for col, (label, value, color, icon) in zip(cols, stat_data):
            with col:
                st.markdown(f"""
                <div class="pm-stat-card" style="border-top-color:{color};">
                    <div style="font-size:1.8rem;">{icon}</div>
                    <div class="pm-stat-number" style="color:{color};">{value}</div>
                    <div class="pm-stat-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two columns: tasks + projects ──────────────────
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### 🔥 My Active Tasks")
        if role == 'admin':
            tasks = get_tasks(status='inprogress')[:8]
        else:
            tasks = get_tasks(assigned_to=user['id'])
            tasks = [t for t in tasks if t['status'] != 'done'][:8]

        if not tasks:
            st.info("No active tasks right now. 🎉")
        else:
            priority_colors = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'}
            for t in tasks:
                pc = priority_colors.get(t['priority'], '#667eea')
                due = t['due_date'] or 'No due date'
                overdue = ''
                if t['due_date']:
                    try:
                        if date.fromisoformat(t['due_date']) < date.today() and t['status'] != 'done':
                            overdue = '⚠️ OVERDUE'
                    except:
                        pass
                overdue_html = (
                    f'&nbsp;·&nbsp;<span style="color:#ef4444;font-weight:700;">{overdue}</span>'
                    if overdue else ''
                )
                card_html = (
                    f'<div class="pm-card" style="border-left:4px solid {pc};padding:14px 16px;margin-bottom:10px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:start;">'
                    f'<div style="flex:1;">'
                    f'<div style="font-weight:600;color:#1e293b;">{t["title"]}</div>'
                    f'<div style="font-size:12px;color:#64748b;margin-top:4px;">'
                    f'📁 {t["project_name"]} &nbsp;·&nbsp; 📅 {due}{overdue_html}'
                    f'</div>'
                    f'</div>'
                    f'<div><span class="badge badge-{t["status"]}">{t["status"].upper()}</span></div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

    with right:
        st.markdown("### 📁 Recent Projects")
        projects = get_all_projects(user['id'], role)[:6]
        if not projects:
            st.info("No projects yet.")
        else:
            for p in projects:
                total = p['task_count'] or 0
                done = p['done_count'] or 0
                pct = int((done / total * 100) if total > 0 else 0)
                status_color = {'active': '#10b981', 'completed': '#6366f1', 'onhold': '#f59e0b'}.get(p['status'], '#667eea')
                proj_html = (
                    f'<div class="pm-card" style="padding:14px 16px;margin-bottom:10px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                    f'<div style="font-weight:600;color:#1e293b;">{p["name"]}</div>'
                    f'<span class="badge badge-{p["status"]}">{p["status"].upper()}</span>'
                    f'</div>'
                    f'<div style="font-size:12px;color:#64748b;margin-bottom:8px;">'
                    f'👥 {p["team_name"] or "No Team"} &nbsp;·&nbsp; {total} tasks'
                    f'</div>'
                    f'<div style="display:flex;align-items:center;gap:8px;">'
                    f'<div class="progress-wrap" style="flex:1;">'
                    f'<div class="progress-fill" style="width:{pct}%;background:{status_color};"></div>'
                    f'</div>'
                    f'<span style="font-size:12px;font-weight:600;color:{status_color};">{pct}%</span>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(proj_html, unsafe_allow_html=True)

        if st.button("➕ New Project", use_container_width=True, type="primary"):
            st.session_state.page = 'projects'
            st.rerun()
