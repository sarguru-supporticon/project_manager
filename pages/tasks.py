import streamlit as st
import os
from utils.database import (get_tasks, create_task, update_task, delete_task,
                             get_all_projects, get_all_users, get_milestones,
                             add_comment, get_comments, get_attachments, save_attachment,
                             add_notification, get_task)
from utils.email_utils import notify_task_assigned, notify_task_status_changed, notify_comment_added
from datetime import date

UPLOAD_DIR = "attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def show():
    user = st.session_state.user
    role = user['role']

    st.markdown("<h1 style='color:#1e1b4b;'>✅ Tasks</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Task List", "➕ Create Task", "🔍 Task Detail"])

    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            projects = get_all_projects(user['id'], role)
            proj_opts = {"All Projects": None} | {p['name']: p['id'] for p in projects}
            sel_proj = st.selectbox("Project", list(proj_opts.keys()))
            project_id = proj_opts[sel_proj]
        with col2:
            filter_status = st.selectbox("Status", ["All", "todo", "inprogress", "review", "done"])
        with col3:
            filter_priority = st.selectbox("Priority", ["All", "high", "medium", "low"])
        with col4:
            mine_only = st.checkbox("My Tasks Only", value=(role != 'admin'))

        tasks = get_tasks(
            project_id=project_id,
            assigned_to=user['id'] if mine_only else None,
            status=filter_status if filter_status != "All" else None
        )
        if filter_priority != "All":
            tasks = [t for t in tasks if t['priority'] == filter_priority]

        st.markdown(f"**{len(tasks)} tasks found**")

        if not tasks:
            st.info("No tasks match your filters.")
        else:
            priority_colors = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'}
            status_labels = {'todo': '📝 To Do', 'inprogress': '🔄 In Progress', 'review': '👀 Review', 'done': '✅ Done'}

            for t in tasks:
                pc = priority_colors.get(t['priority'], '#667eea')
                overdue = ''
                if t['due_date']:
                    try:
                        if date.fromisoformat(t['due_date']) < date.today() and t['status'] != 'done':
                            overdue = ' ⚠️'
                    except:
                        pass

                with st.expander(f"{status_labels.get(t['status'], t['status'])}  |  {t['title']}{overdue}  —  {t['project_name']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Description:** {t['description'] or 'N/A'}")
                        st.markdown(f"**Assigned to:** 👤 {t['assignee_name'] or 'Unassigned'}")
                        st.markdown(f"**Due Date:** 📅 {t['due_date'] or 'Not set'}")
                        st.markdown(f"**Milestone:** 🏁 {t['milestone_title'] or 'None'}")
                        hrs = f"{t['logged_hours'] or 0:.1f} / {t['estimated_hours'] or 0:.1f} hrs"
                        st.markdown(f"**Time:** ⏱️ {hrs}")
                        st.markdown(f"**Priority:** <span class='badge badge-{t['priority']}'>{t['priority'].upper()}</span>", unsafe_allow_html=True)

                    with c2:
                        st.markdown("**Update Status**")
                        statuses = ["todo", "inprogress", "review", "done"]
                        new_status = st.selectbox("", statuses,
                                                  index=statuses.index(t['status']),
                                                  key=f"ts_{t['id']}")
                        if st.button("Update", key=f"upd_{t['id']}", use_container_width=True):
                            old_status = t['status']
                            from utils.database import update_task_status
                            update_task_status(t['id'], new_status)
                            # Notify assignee
                            if t['assignee_email'] and new_status != old_status:
                                notify_task_status_changed(
                                    t['title'], t['project_name'],
                                    t['assignee_email'], t['assignee_name'],
                                    old_status, new_status
                                )
                            st.success("Updated!")
                            st.rerun()

                        if st.button("🔍 Open Detail", key=f"det_{t['id']}", use_container_width=True):
                            st.session_state.detail_task_id = t['id']
                            st.rerun()

                        if role == 'admin':
                            if st.button("🗑️ Delete", key=f"deltask_{t['id']}", use_container_width=True):
                                delete_task(t['id'])
                                st.success("Deleted!")
                                st.rerun()

    with tab2:
        if role not in ['admin']:
            st.info("Only admins can create tasks.")
            return

        with st.form("create_task_form"):
            st.markdown("### Create New Task")
            c1, c2 = st.columns(2)
            with c1:
                projects = get_all_projects(user['id'], role)
                proj_opts = {p['name']: p['id'] for p in projects}
                sel_proj_name = st.selectbox("Project *", list(proj_opts.keys()))
                proj_id = proj_opts.get(sel_proj_name)

                title = st.text_input("Task Title *")
                description = st.text_area("Description")
                priority = st.selectbox("Priority", ["medium", "high", "low"])

            with c2:
                users = get_all_users()
                user_opts = {u['name'] + f" ({u['email']})": u['id'] for u in users}
                sel_user = st.selectbox("Assign To *", list(user_opts.keys()))
                assigned_id = user_opts.get(sel_user)

                due_date = st.date_input("Due Date", value=date.today())
                estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=0.5)

                # Milestone
                if proj_id:
                    milestones = get_milestones(proj_id)
                    ms_opts = {"None": None} | {m['title']: m['id'] for m in milestones}
                    sel_ms = st.selectbox("Milestone", list(ms_opts.keys()))
                    ms_id = ms_opts.get(sel_ms)
                else:
                    ms_id = None

            submitted = st.form_submit_button("✅ Create Task", use_container_width=True, type="primary")
            if submitted:
                if title and proj_id and assigned_id:
                    tid = create_task(proj_id, title, description, assigned_id, user['id'],
                                      priority, str(due_date), estimated_hours, ms_id)
                    # Notify assignee
                    assignee = next((u for u in users if u['id'] == assigned_id), None)
                    proj = next((p for p in projects if p['id'] == proj_id), None)
                    if assignee:
                        notify_task_assigned(
                            title, proj['name'] if proj else '', assignee['name'],
                            assignee['email'], user['name'], str(due_date), priority
                        )
                        add_notification(assigned_id, "New Task Assigned",
                                         f"You've been assigned: {title}")
                    st.success(f"✅ Task '{title}' created and assignee notified!")
                    st.rerun()
                else:
                    st.error("Please fill required fields.")

    with tab3:
        task_id = st.session_state.get('detail_task_id')
        if not task_id:
            st.info("Select a task from the list to view details.")
            return

        task = get_task(task_id)
        if not task:
            st.warning("Task not found.")
            return

        st.markdown(f"## 🔍 {task['title']}")
        st.markdown(f"**Project:** {task['project_name']}  |  **Assignee:** {task['assignee_name'] or 'Unassigned'}")
        st.markdown(f"**Status:** <span class='badge badge-{task['status']}'>{task['status'].upper()}</span>  |  **Priority:** <span class='badge badge-{task['priority']}'>{task['priority'].upper()}</span>", unsafe_allow_html=True)

        detail_tabs = st.tabs(["💬 Comments", "📎 Attachments", "✏️ Edit Task"])

        with detail_tabs[0]:
            comments = get_comments(task_id)
            for c in comments:
                st.markdown(f"""
                <div style="background:#f8fafc;border-radius:8px;padding:12px;margin-bottom:8px;border-left:3px solid #667eea;">
                    <strong>{c['user_name']}</strong>
                    <span style="color:#94a3b8;font-size:12px;"> · {c['created_at'][:16]}</span>
                    <div style="margin-top:6px;">{c['comment']}</div>
                </div>
                """, unsafe_allow_html=True)

            with st.form(f"comment_form_{task_id}"):
                comment_text = st.text_area("Add a comment")
                if st.form_submit_button("💬 Post Comment"):
                    if comment_text:
                        add_comment(task_id, user['id'], comment_text)
                        # Notify assignee
                        if task['assigned_to'] and task['assigned_to'] != user['id']:
                            assignee_user = next((u for u in get_all_users() if u['id'] == task['assigned_to']), None)
                            if assignee_user:
                                notify_comment_added(task['title'], task['project_name'],
                                                     assignee_user['email'], assignee_user['name'],
                                                     user['name'], comment_text)
                                add_notification(task['assigned_to'], "New Comment",
                                                 f"{user['name']} commented on: {task['title']}")
                        st.success("Comment posted!")
                        st.rerun()

        with detail_tabs[1]:
            attachments = get_attachments(task_id)
            if attachments:
                for a in attachments:
                    size_kb = (a['filesize'] or 0) // 1024
                    st.markdown(f"📎 **{a['filename']}** ({size_kb} KB) — Uploaded by {a['user_name']} on {a['uploaded_at'][:10]}")
                    filepath = a['filepath']
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            st.download_button(f"⬇️ Download {a['filename']}", f.read(),
                                               file_name=a['filename'], key=f"dl_{a['id']}")
            else:
                st.info("No attachments yet.")

            uploaded = st.file_uploader("Upload File", key=f"upload_{task_id}")
            if uploaded:
                save_path = os.path.join(UPLOAD_DIR, f"{task_id}_{uploaded.name}")
                with open(save_path, 'wb') as f:
                    f.write(uploaded.getbuffer())
                save_attachment(task_id, user['id'], uploaded.name, save_path, uploaded.size)
                st.success(f"✅ '{uploaded.name}' uploaded!")
                st.rerun()

        with detail_tabs[2]:
            if role != 'admin':
                st.info("Only admins can edit tasks.")
                return
            users_list = get_all_users()
            user_opts = {u['name']: u['id'] for u in users_list}
            current_assignee = next((u['name'] for u in users_list if u['id'] == task['assigned_to']), list(user_opts.keys())[0])

            with st.form(f"edit_task_{task_id}"):
                new_title = st.text_input("Title", value=task['title'])
                new_desc = st.text_area("Description", value=task['description'] or '')
                new_assignee = st.selectbox("Assign To", list(user_opts.keys()),
                                            index=list(user_opts.keys()).index(current_assignee) if current_assignee in user_opts else 0)
                c1, c2 = st.columns(2)
                with c1:
                    new_priority = st.selectbox("Priority", ["medium", "high", "low"],
                                                index=["medium", "high", "low"].index(task['priority']))
                    new_status = st.selectbox("Status", ["todo", "inprogress", "review", "done"],
                                             index=["todo", "inprogress", "review", "done"].index(task['status']))
                with c2:
                    new_due = st.date_input("Due Date",
                                            value=date.fromisoformat(task['due_date']) if task['due_date'] else date.today())
                    new_hours = st.number_input("Estimated Hours", value=float(task['estimated_hours'] or 0), step=0.5)

                if st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary"):
                    update_task(task_id, new_title, new_desc, user_opts[new_assignee],
                                new_priority, str(new_due), new_hours, new_status)
                    st.success("Task updated!")
                    st.rerun()
