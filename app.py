import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from streamlit_js_eval import streamlit_js_eval, set_local_storage, remove_local_storage

from utils.database import (
    init_db,
    get_user_by_email,
    hash_password,
    get_notifications,
    mark_notifications_read,
    create_auth_session,
    get_user_by_auth_token,
    delete_auth_session,
)

LOCAL_STORAGE_AUTH_KEY = "office_pm_auth_token"
_LS_EMPTY = "__none__"

st.set_page_config(
    page_title="Office Project Manager",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme CSS ──────────────────────────────────────────
def apply_theme(dark=False):
    if dark:
        app_bg       = "#0f172a"
        card_bg      = "#1e293b"
        card_shadow  = "0 2px 8px rgba(0,0,0,0.4)"
        text_primary = "#e2e8f0"
        text_muted   = "#94a3b8"
        input_bg     = "#1e293b"
        input_border = "#334155"
        kanban_col   = "#1e293b"
        kanban_card  = "#0f172a"
        metric_bg    = "#1e293b"
        header_bg    = "#1e293b"
        progress_bg  = "#334155"
    else:
        app_bg       = "#f0f2f6"
        card_bg      = "#ffffff"
        card_shadow  = "0 2px 8px rgba(0,0,0,0.08)"
        text_primary = "#1e1b4b"
        text_muted   = "#64748b"
        input_bg     = "#ffffff"
        input_border = "#e2e8f0"
        kanban_col   = "#f8fafc"
        kanban_card  = "#ffffff"
        metric_bg    = "#ffffff"
        header_bg    = "#ffffff"
        progress_bg  = "#e2e8f0"

    st.markdown(f"""
<style>
    /* Hide Streamlit auto-generated page navigation */
    [data-testid="stSidebarNav"] {{ display: none !important; }}
    [data-testid="stSidebarNavItems"] {{ display: none !important; }}

    .stApp {{ background: {app_bg} !important; }}
    .stApp > div, .block-container {{ color: {text_primary}; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%) !important;
    }}
    section[data-testid="stSidebar"] * {{ color: #e0e7ff !important; }}
    section[data-testid="stSidebar"] .stButton button {{
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: #fff !important;
        border-radius: 8px !important;
        width: 100%;
        text-align: left;
        padding: 8px 12px;
        margin: 2px 0;
        transition: all 0.2s;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        background: rgba(255,255,255,0.25) !important;
    }}

    /* Cards */
    .pm-card {{
        background: {card_bg};
        border-radius: 12px;
        padding: 20px;
        box-shadow: {card_shadow};
        margin-bottom: 16px;
    }}
    .pm-stat-card {{
        background: {card_bg};
        border-radius: 12px;
        padding: 20px;
        box-shadow: {card_shadow};
        text-align: center;
        border-top: 4px solid;
    }}
    .pm-stat-number {{ font-size: 2.2rem; font-weight: 700; color: {text_primary}; }}
    .pm-stat-label {{ color: {text_muted}; font-size: 0.9rem; margin-top: 4px; }}

    /* Badges */
    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }}
    .badge-high {{ background: #fee2e2; color: #dc2626; }}
    .badge-medium {{ background: #fef3c7; color: #d97706; }}
    .badge-low {{ background: #d1fae5; color: #059669; }}
    .badge-todo {{ background: #e0e7ff; color: #4338ca; }}
    .badge-inprogress {{ background: #fef3c7; color: #d97706; }}
    .badge-review {{ background: #ede9fe; color: #7c3aed; }}
    .badge-done {{ background: #d1fae5; color: #059669; }}
    .badge-active {{ background: #d1fae5; color: #059669; }}
    .badge-completed {{ background: #e0e7ff; color: #4338ca; }}
    .badge-onhold {{ background: #fee2e2; color: #dc2626; }}

    /* Kanban */
    .kanban-col {{
        background: {kanban_col};
        border-radius: 10px;
        padding: 12px;
        min-height: 200px;
    }}
    .kanban-header {{
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 12px;
        padding: 6px 10px;
        border-radius: 6px;
    }}
    .kanban-card {{
        background: {kanban_card};
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        border-left: 3px solid;
        cursor: pointer;
    }}

    /* Page header */
    .page-header {{
        background: {header_bg};
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: {card_shadow};
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    /* Notification dot */
    .notif-dot {{
        background: #ef4444;
        color: #fff;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
    }}

    /* Progress bar */
    .progress-wrap {{ background: {progress_bg}; border-radius: 10px; height: 8px; overflow: hidden; }}
    .progress-fill {{ height: 100%; border-radius: 10px; transition: width 0.3s; }}

    /* Inputs */
    .stTextInput input, .stTextArea textarea {{
        border-radius: 8px !important;
        background: {input_bg} !important;
        color: {text_primary} !important;
        border-color: {input_border} !important;
    }}
    .stButton > button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}
    div[data-testid="metric-container"] {{
        background: {metric_bg} !important;
        border-radius: 12px !important;
        padding: 16px !important;
        box-shadow: {card_shadow} !important;
    }}
    div[data-testid="metric-container"] label,
    div[data-testid="metric-container"] div {{
        color: {text_primary} !important;
    }}
    /* Expanders */
    .streamlit-expanderHeader {{
        background: {card_bg} !important;
        color: {text_primary} !important;
        border-radius: 8px !important;
    }}
    .streamlit-expanderContent {{
        background: {card_bg} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ── Init DB ────────────────────────────────────────────
init_db()

# ── Session State ──────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

apply_theme(st.session_state.dark_mode)


def try_restore_session_from_browser():
    """Read session token from browser localStorage and log in if still valid.

    Returns:
        None  – component hasn't run yet (show a loading screen)
        False – no saved session found (show login form)
        True  – session restored (rerun triggered)
    """
    if st.session_state.logged_in:
        return True

    # Using a sentinel so we can tell "not yet read" (Python None) apart from
    # "key doesn't exist in localStorage" (our sentinel string).
    result = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{LOCAL_STORAGE_AUTH_KEY}') ?? '{_LS_EMPTY}'",
        key="pm_auth_check",
    )

    if result is None:
        # The JS component hasn't fired yet — still on the first render cycle.
        return None

    if result == _LS_EMPTY:
        # localStorage has no saved token.
        return False

    # We have a token — validate it against the DB.
    user = get_user_by_auth_token(result)
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user
        st.session_state.auth_token = result
        if not st.session_state.get("page"):
            st.session_state.page = "dashboard"
        st.rerun()
        return True
    else:
        # Stale / expired token — clear it from localStorage.
        streamlit_js_eval(
            js_expressions=f"localStorage.removeItem('{LOCAL_STORAGE_AUTH_KEY}')",
            key="pm_clear_stale",
        )
        return False


def login_page():
    # Hide sidebar completely on the login screen
    st.markdown("""
<style>
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"]  { display: none !important; }
    .stApp { background: #f0f2f6 !important; }
</style>
""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px;">
        <div style="font-size:64px;">📋</div>
        <h1 style="color:#1e1b4b;font-size:2rem;margin:10px 0 4px;">Office Project Manager</h1>
        <p style="color:#64748b;">Sign in to manage your projects & teams</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container():
            st.markdown("### 🔐 Sign In")
            email = st.text_input("Email Address", placeholder="you@office.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            remember_me = st.checkbox(
                "Stay signed in (saved in this browser local storage)",
                value=True,
                help="Uses a secure random token; your password is never stored in the browser.",
            )

            if st.button("Sign In →", use_container_width=True, type="primary"):
                if email and password:
                    user = get_user_by_email(email.strip().lower())
                    if user and user['password'] == hash_password(password):
                        if remember_me:
                            tok = create_auth_session(user["id"])
                            set_local_storage(
                                LOCAL_STORAGE_AUTH_KEY,
                                tok,
                                component_key="pm_login_write",
                            )
                            st.session_state.auth_token = tok
                        else:
                            streamlit_js_eval(
                                js_expressions=f"localStorage.removeItem('{LOCAL_STORAGE_AUTH_KEY}')",
                                key="pm_login_clear",
                            )
                            st.session_state.auth_token = None
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password")
                else:
                    st.warning("Please enter email and password")

            st.markdown("---")
            st.markdown("""
            <div style="text-align:center;color:#94a3b8;font-size:13px;">
                Default Admin: admin@office.com / admin123
            </div>
            """, unsafe_allow_html=True)

def sidebar():
    user = st.session_state.user
    role = user['role']

    with st.sidebar:
        # User info
        st.markdown(f"""
        <div style="padding:16px;background:rgba(255,255,255,0.1);border-radius:10px;margin-bottom:16px;">
            <div style="font-size:32px;text-align:center;">{'👑' if role=='admin' else '👤'}</div>
            <div style="text-align:center;font-weight:700;font-size:1rem;margin-top:8px;">{user['name']}</div>
            <div style="text-align:center;font-size:12px;opacity:0.7;">{user['email']}</div>
            <div style="text-align:center;margin-top:8px;">
                <span style="background:rgba(255,255,255,0.2);padding:2px 10px;border-radius:12px;font-size:11px;">
                    {role.upper()}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Notifications
        notifs = get_notifications(user['id'], unread_only=True)
        notif_count = len(notifs)

        st.markdown("### Navigation")

        pages = [
            ("🏠", "Dashboard", "dashboard"),
            ("📁", "Projects", "projects"),
            ("✅", "My Tasks", "tasks"),
            ("📊", "Kanban Board", "kanban"),
            ("⏱️", "Time Tracking", "time"),
            (f"🔔{'  🔴' if notif_count else ''}", f"Notifications {f'({notif_count})' if notif_count else ''}", "notifications"),
            ("📈", "Reports", "reports"),
        ]
        if role == 'admin':
            pages += [
                ("👥", "Teams", "teams"),
                ("👤", "Users", "users"),
                ("⚙️", "Settings", "settings"),
            ]

        for icon, label, page_key in pages:
            if st.button(f"{icon}  {label}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()

        st.markdown("---")
        if st.button("🚪  Sign Out", use_container_width=True):
            tok = st.session_state.get("auth_token")
            if tok:
                delete_auth_session(tok)
            streamlit_js_eval(
                js_expressions=f"localStorage.removeItem('{LOCAL_STORAGE_AUTH_KEY}')",
                key="pm_logout_clear",
            )
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.auth_token = None
            st.session_state.page = "dashboard"
            st.rerun()

# ── Page Router ────────────────────────────────────────
def route():
    page = st.session_state.page
    if page == 'dashboard':
        from pages.dashboard import show; show()
    elif page == 'projects':
        from pages.projects import show; show()
    elif page == 'tasks':
        from pages.tasks import show; show()
    elif page == 'kanban':
        from pages.kanban import show; show()
    elif page == 'time':
        from pages.time_tracking import show; show()
    elif page == 'notifications':
        from pages.notifications import show; show()
    elif page == 'reports':
        from pages.reports import show; show()
    elif page == 'teams':
        from pages.teams import show; show()
    elif page == 'users':
        from pages.users import show; show()
    elif page == 'settings':
        from pages.settings import show; show()
    else:
        from pages.dashboard import show; show()

# ── Main ───────────────────────────────────────────────
auth_status = try_restore_session_from_browser()

if st.session_state.logged_in:
    sidebar()
    route()
elif auth_status is None:
    # Still waiting for the localStorage component to fire — show a brief loader.
    st.markdown("""
<style>
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"]  { display: none !important; }
</style>
<div style="text-align:center;padding:120px 0;">
    <div style="font-size:64px;">📋</div>
    <p style="color:#64748b;margin-top:16px;font-size:1rem;">Loading session…</p>
</div>
""", unsafe_allow_html=True)
else:
    login_page()
