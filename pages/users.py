import streamlit as st
from utils.database import get_all_users, create_user, update_user, delete_user
from utils.email_utils import notify_welcome
import random, string

def gen_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def show():
    user = st.session_state.user
    if user['role'] != 'admin':
        st.warning("Admin only.")
        return

    st.markdown("<h1 style='color:#1e1b4b;'>👤 User Management</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👤 All Users", "➕ Add User"])

    with tab1:
        users = get_all_users()
        st.markdown(f"**Total: {len(users)} users**")

        for u in users:
            icon = '👑' if u['role'] == 'admin' else '👤'
            with st.expander(f"{icon} {u['name']}  —  {u['email']}  [{u['role'].upper()}]"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    with st.form(f"edit_user_{u['id']}"):
                        new_name = st.text_input("Name", value=u['name'])
                        new_email = st.text_input("Email", value=u['email'])
                        new_role = st.selectbox("Role", ["member", "admin"],
                                               index=0 if u['role'] == 'member' else 1)
                        if st.form_submit_button("💾 Save"):
                            update_user(u['id'], new_name, new_email, new_role)
                            st.toast(f"✅ User '{new_name}' updated!", icon="💾")
                            st.rerun()
                with c2:
                    st.markdown(f"**Joined:** {u['created_at'][:10]}")
                    if u['id'] != user['id']:
                        if st.button(f"🗑️ Delete", key=f"delusr_{u['id']}"):
                            delete_user(u['id'])
                            st.success("User deleted!")
                            st.rerun()

    with tab2:
        with st.form("add_user_form"):
            st.markdown("### Add New User")
            name = st.text_input("Full Name *")
            email = st.text_input("Email Address *")
            role = st.selectbox("Role", ["member", "admin"])
            auto_pw = st.checkbox("Auto-generate password & send welcome email", value=True)
            manual_pw = ""
            if not auto_pw:
                manual_pw = st.text_input("Password *", type="password")

            if st.form_submit_button("➕ Create User", use_container_width=True, type="primary"):
                if not name or not email:
                    st.error("Name and email are required.")
                else:
                    password = gen_password() if auto_pw else manual_pw
                    if not password:
                        st.error("Password is required.")
                    else:
                        ok, msg = create_user(name, email.lower().strip(), password, role)
                        if ok:
                            if auto_pw:
                                sent_ok, sent_msg = notify_welcome(name, email, password)
                                if sent_ok:
                                    st.toast(f"✅ User created & welcome email sent to {email}!", icon="🎉")
                                else:
                                    st.toast(f"✅ User '{name}' created! (Email not sent)", icon="👤")
                                    st.info(f"Temporary password: **{password}**")
                            else:
                                st.toast(f"✅ User '{name}' created successfully!", icon="🎉")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg} — a user with this email already exists.")
