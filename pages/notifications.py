import streamlit as st
from utils.database import get_notifications, mark_notifications_read

def show():
    user = st.session_state.user
    st.markdown("<h1 style='color:#1e1b4b;'>🔔 Notifications</h1>", unsafe_allow_html=True)

    notifs = get_notifications(user['id'])

    if not notifs:
        st.info("No notifications yet.")
        return

    unread = [n for n in notifs if not n['is_read']]
    if unread:
        if st.button(f"✅ Mark All Read ({len(unread)} unread)", type="primary"):
            mark_notifications_read(user['id'])
            st.rerun()

    for n in notifs:
        bg = "#eff6ff" if not n['is_read'] else "#f8fafc"
        border = "#3b82f6" if not n['is_read'] else "#e2e8f0"
        dot = "🔵 " if not n['is_read'] else "⚪ "
        st.markdown(f"""
        <div style="background:{bg};border-radius:10px;padding:14px 18px;margin-bottom:8px;
                    border-left:4px solid {border};">
            <div style="font-weight:600;color:#1e293b;">{dot}{n['title']}</div>
            <div style="color:#475569;margin-top:4px;">{n['message']}</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:6px;">📅 {n['created_at'][:16]}</div>
        </div>
        """, unsafe_allow_html=True)
