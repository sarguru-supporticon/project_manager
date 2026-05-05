import streamlit as st
from utils.database import hash_password, get_connection

def show():
    user = st.session_state.user
    role = user['role']

    st.markdown("<h1 style='color:#1e1b4b;'>⚙️ Settings</h1>", unsafe_allow_html=True)

    tab0, tab1, tab2 = st.tabs(["🎨 Appearance", "🔑 Change Password", "📧 Email / SMTP Config"])

    with tab0:
        st.markdown("### Display Theme")
        dark = st.session_state.get('dark_mode', False)
        col_l, col_r = st.columns(2)
        with col_l:
            if st.button(
                "☀️  Light Mode",
                use_container_width=True,
                type="primary" if not dark else "secondary"
            ):
                st.session_state.dark_mode = False
                st.rerun()
        with col_r:
            if st.button(
                "🌙  Dark Mode",
                use_container_width=True,
                type="primary" if dark else "secondary"
            ):
                st.session_state.dark_mode = True
                st.rerun()

        current = "🌙 Dark Mode" if dark else "☀️ Light Mode"
        st.info(f"Current theme: **{current}**")

    with tab1:
        st.markdown("### Change Your Password")
        with st.form("change_pw"):
            old_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("🔑 Change Password", use_container_width=True, type="primary"):
                if not old_pw or not new_pw or not confirm_pw:
                    st.error("All fields required.")
                elif new_pw != confirm_pw:
                    st.error("Passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif hash_password(old_pw) != user['password']:
                    st.error("Current password is incorrect.")
                else:
                    conn = get_connection()
                    conn.execute("UPDATE users SET password=? WHERE id=?",
                                 (hash_password(new_pw), user['id']))
                    conn.commit()
                    conn.close()
                    st.session_state.user['password'] = hash_password(new_pw)
                    st.success("✅ Password changed successfully!")

    with tab2:
        if role != 'admin':
            st.info("Only admins can configure SMTP settings.")
            return

        st.markdown("### Gmail SMTP Configuration")
        st.info("""
        ℹ️ **How to configure Gmail SMTP:**
        1. Create a file `.streamlit/secrets.toml` in your project folder
        2. Add the following settings:
        ```toml
        SMTP_HOST = "smtp.gmail.com"
        SMTP_PORT = 587
        SMTP_USER = "your.email@gmail.com"
        SMTP_PASSWORD = "your_app_password"
        FROM_NAME = "Office Project Manager"
        ```
        3. For Gmail, use an **App Password** (not your regular password).
           Go to: Google Account → Security → 2-Step Verification → App passwords
        """)

        st.markdown("### Test Email")
        with st.form("test_email_form"):
            test_to = st.text_input("Send Test Email To", placeholder="test@example.com")
            if st.form_submit_button("📧 Send Test Email"):
                if test_to:
                    from utils.email_utils import send_email, email_template
                    html = email_template(
                        "Email Configuration Test ✅",
                        "<p>If you received this email, your SMTP configuration is working correctly!</p>",
                        "Sent from Office Project Manager"
                    )
                    ok, msg = send_email(test_to, "Test Email - Project Manager", html)
                    if ok:
                        st.success(f"✅ Test email sent to {test_to}")
                    else:
                        st.error(f"❌ Failed: {msg}")
                        st.info("Make sure to configure .streamlit/secrets.toml with your Gmail credentials.")

        st.markdown("### About")
        st.markdown("""
        <div style="background:#f8fafc;border-radius:10px;padding:20px;">
            <h4>📋 Office Project Manager</h4>
            <p>Version 1.0.0</p>
            <ul>
                <li>Built with Streamlit</li>
                <li>SQLite database (file-based, no setup required)</li>
                <li>Gmail SMTP for email notifications</li>
                <li>File attachments stored locally</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
