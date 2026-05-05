# 📋 Office Project Manager

A full-featured project management tool built with Streamlit for small office teams (up to 10 people).

## Features
- 🔐 Role-based login (Admin / Member)
- 📁 Project management with priorities & milestones
- ✅ Task assignment & tracking
- 📊 Kanban board (To Do → In Progress → Review → Done)
- 💬 Task comments / team chat
- 📎 File attachments
- ⏱️ Time tracking & logging
- 📈 Reports & dashboards
- 🔔 In-app notifications
- 📧 Gmail email notifications (task assigned, status changes, comments, project updates)

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Gmail SMTP (for email notifications)
```bash
mkdir .streamlit
cp secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your Gmail credentials
```

> **Gmail App Password:** Google Account → Security → 2-Step Verification → App Passwords

### 3. Run locally
```bash
streamlit run app.py
```

### 4. Deploy to Streamlit Community Cloud (Free)
1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the entry point
4. In **Settings → Secrets**, paste your `secrets.toml` contents
5. Click **Deploy**!

## Default Login
- **Email:** admin@office.com
- **Password:** admin123
- ⚠️ Change this password after first login!

## File Structure
```
project_manager/
├── app.py              # Main entry point
├── requirements.txt
├── secrets.toml.example
├── pages/
│   ├── dashboard.py
│   ├── projects.py
│   ├── tasks.py
│   ├── kanban.py
│   ├── time_tracking.py
│   ├── teams.py
│   ├── users.py
│   ├── reports.py
│   ├── notifications.py
│   └── settings.py
└── utils/
    ├── database.py     # SQLite ORM
    └── email_utils.py  # Gmail SMTP
```

## Data Storage
- All data is stored in `project_manager.db` (SQLite)
- File attachments are stored in `attachments/` folder
- Both are auto-created on first run

## Notes for Streamlit Cloud
- The SQLite database resets on each deployment (use for internal/non-critical data)
- For persistent data, consider upgrading to PostgreSQL via `st.connection`
- File uploads won't persist across restarts on free tier
