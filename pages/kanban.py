import streamlit as st
from utils.database import get_tasks, get_all_projects, update_task_status

COLUMNS = [
    ("todo", "📝 To Do", "#6366f1"),
    ("inprogress", "🔄 In Progress", "#f59e0b"),
    ("review", "👀 Review", "#8b5cf6"),
    ("done", "✅ Done", "#10b981"),
]

def show():
    user = st.session_state.user
    role = user['role']

    st.markdown("<h1 style='color:#1e1b4b;'>📊 Kanban Board</h1>", unsafe_allow_html=True)

    projects = get_all_projects(user['id'], role)
    if not projects:
        st.info("No projects available.")
        return

    proj_opts = {p['name']: p['id'] for p in projects}

    # If coming from projects page
    default_proj = None
    if 'selected_project' in st.session_state:
        for p in projects:
            if p['id'] == st.session_state.selected_project:
                default_proj = p['name']
                break

    selected_name = st.selectbox(
        "Select Project",
        list(proj_opts.keys()),
        index=list(proj_opts.keys()).index(default_proj) if default_proj else 0
    )
    project_id = proj_opts[selected_name]

    mine_only = st.checkbox("My Tasks Only", value=(role != 'admin'))

    tasks = get_tasks(project_id=project_id,
                      assigned_to=user['id'] if mine_only else None)

    priority_colors = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'}
    priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}

    cols = st.columns(4)
    for col_idx, (status_key, label, header_color) in enumerate(COLUMNS):
        col_tasks = [t for t in tasks if t['status'] == status_key]
        with cols[col_idx]:
            st.markdown(f"""
            <div style="background:{header_color}20;border-radius:10px;padding:10px 14px;margin-bottom:12px;
                        border-top:3px solid {header_color};">
                <span style="font-weight:700;color:{header_color};font-size:0.95rem;">{label}</span>
                <span style="float:right;background:{header_color};color:#fff;border-radius:12px;
                             padding:1px 8px;font-size:12px;font-weight:700;">{len(col_tasks)}</span>
            </div>
            """, unsafe_allow_html=True)

            if not col_tasks:
                st.markdown(f"""
                <div style="background:#f8fafc;border-radius:8px;padding:20px;text-align:center;
                            color:#94a3b8;font-size:13px;border:2px dashed #e2e8f0;">
                    No tasks here
                </div>
                """, unsafe_allow_html=True)

            for t in col_tasks:
                pc = priority_colors.get(t['priority'], '#667eea')
                pi = priority_icons.get(t['priority'], '⚪')
                due_str = f"📅 {t['due_date']}" if t['due_date'] else ""

                st.markdown(f"""
                <div style="background:#fff;border-radius:8px;padding:12px;margin-bottom:8px;
                            box-shadow:0 2px 6px rgba(0,0,0,0.08);border-left:3px solid {pc};">
                    <div style="font-weight:600;color:#1e293b;font-size:0.9rem;margin-bottom:6px;">
                        {t['title']}
                    </div>
                    <div style="font-size:11px;color:#64748b;margin-bottom:6px;">
                        {pi} {t['priority'].upper()} &nbsp;
                        {'·&nbsp; 👤 ' + t['assignee_name'] if t['assignee_name'] else ''}
                    </div>
                    {f'<div style="font-size:11px;color:#94a3b8;">{due_str}</div>' if due_str else ''}
                </div>
                """, unsafe_allow_html=True)

                # Move task
                other_statuses = [s for s, _, _ in COLUMNS if s != status_key]
                status_labels_map = {s: l for s, l, _ in COLUMNS}

                move_options = ["Move to..."] + [status_labels_map[s] for s in other_statuses]
                move_rev = {status_labels_map[s]: s for s in other_statuses}

                selected_move = st.selectbox("", move_options, key=f"move_{t['id']}")
                if selected_move != "Move to...":
                    new_status = move_rev[selected_move]
                    update_task_status(t['id'], new_status)
                    st.rerun()

    # Summary at bottom
    st.markdown("---")
    st.markdown("### 📊 Summary")
    sum_cols = st.columns(4)
    for i, (status_key, label, color) in enumerate(COLUMNS):
        count = len([t for t in tasks if t['status'] == status_key])
        with sum_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;background:#fff;border-radius:10px;padding:16px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);border-top:3px solid {color};">
                <div style="font-size:1.8rem;font-weight:700;color:{color};">{count}</div>
                <div style="color:#64748b;font-size:13px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
