import sqlite3
import os
import secrets
import time
from datetime import datetime

DB_PATH = "project_manager.db"

AUTH_SESSION_DAYS = 30

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            user_id INTEGER,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(team_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            team_id INTEGER,
            status TEXT DEFAULT 'active',
            priority TEXT DEFAULT 'medium',
            start_date TEXT,
            end_date TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            milestone_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            assigned_to INTEGER,
            created_by INTEGER,
            status TEXT DEFAULT 'todo',
            priority TEXT DEFAULT 'medium',
            due_date TEXT,
            estimated_hours REAL DEFAULT 0,
            logged_hours REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (milestone_id) REFERENCES milestones(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            comment TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS time_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            hours REAL NOT NULL,
            description TEXT,
            logged_date TEXT DEFAULT CURRENT_DATE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions(token);
    """)

    # Create default admin if not exists
    import hashlib
    admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""
        INSERT OR IGNORE INTO users (name, email, password, role)
        VALUES ('Admin', 'admin@office.com', ?, 'admin')
    """, (admin_pw,))

    conn.commit()
    conn.close()

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

# ── Persistent login (browser localStorage holds token only) ──
def create_auth_session(user_id):
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + AUTH_SESSION_DAYS * 86400
    conn = get_connection()
    conn.execute(
        "INSERT INTO auth_sessions (user_id, token, expires_at) VALUES (?,?,?)",
        (user_id, token, expires_at),
    )
    conn.commit()
    conn.close()
    return token

def get_user_by_auth_token(token):
    if not token:
        return None
    now = int(time.time())
    conn = get_connection()
    row = conn.execute(
        """
        SELECT u.* FROM users u
        JOIN auth_sessions s ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > ?
        """,
        (token, now),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_auth_session(token):
    if not token:
        return
    conn = get_connection()
    conn.execute("DELETE FROM auth_sessions WHERE token=?", (token,))
    conn.commit()
    conn.close()

# ── Users ──────────────────────────────────────────────
def get_user_by_email(email):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_user(name, email, password, role="member"):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
                     (name, email, hash_password(password), role))
        conn.commit()
        return True, "User created"
    except sqlite3.IntegrityError:
        return False, "Email already exists"
    finally:
        conn.close()

def update_user(user_id, name, email, role):
    conn = get_connection()
    conn.execute("UPDATE users SET name=?,email=?,role=? WHERE id=?", (name, email, role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

# ── Teams ──────────────────────────────────────────────
def team_name_exists(name):
    conn = get_connection()
    row = conn.execute("SELECT id FROM teams WHERE LOWER(name)=LOWER(?)", (name.strip(),)).fetchone()
    conn.close()
    return row is not None

def create_team(name, description, created_by):
    conn = get_connection()
    cur = conn.execute("INSERT INTO teams (name,description,created_by) VALUES (?,?,?)",
                       (name, description, created_by))
    team_id = cur.lastrowid
    conn.execute("INSERT OR IGNORE INTO team_members (team_id,user_id) VALUES (?,?)", (team_id, created_by))
    conn.commit()
    conn.close()
    return team_id

def get_all_teams():
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.*, u.name as creator_name,
               COUNT(DISTINCT tm.user_id) as member_count
        FROM teams t
        LEFT JOIN users u ON t.created_by=u.id
        LEFT JOIN team_members tm ON t.id=tm.team_id
        GROUP BY t.id
        ORDER BY t.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_team(team_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def add_team_member(team_id, user_id):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO team_members (team_id,user_id) VALUES (?,?)", (team_id, user_id))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def remove_team_member(team_id, user_id):
    conn = get_connection()
    conn.execute("DELETE FROM team_members WHERE team_id=? AND user_id=?", (team_id, user_id))
    conn.commit()
    conn.close()

def get_team_members(team_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.* FROM users u
        JOIN team_members tm ON u.id=tm.user_id
        WHERE tm.team_id=?
    """, (team_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_team(team_id):
    conn = get_connection()
    conn.execute("DELETE FROM team_members WHERE team_id=?", (team_id,))
    conn.execute("DELETE FROM teams WHERE id=?", (team_id,))
    conn.commit()
    conn.close()

# ── Projects ───────────────────────────────────────────
def project_name_exists(name):
    conn = get_connection()
    row = conn.execute("SELECT id FROM projects WHERE LOWER(name)=LOWER(?)", (name.strip(),)).fetchone()
    conn.close()
    return row is not None

def create_project(name, description, team_id, priority, start_date, end_date, created_by):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO projects (name,description,team_id,priority,start_date,end_date,created_by)
        VALUES (?,?,?,?,?,?,?)
    """, (name, description, team_id, priority, start_date, end_date, created_by))
    project_id = cur.lastrowid
    conn.commit()
    conn.close()
    return project_id

def get_all_projects(user_id=None, role=None):
    conn = get_connection()
    if role == 'admin':
        rows = conn.execute("""
            SELECT p.*, t.name as team_name, u.name as creator_name,
                   COUNT(DISTINCT tk.id) as task_count,
                   SUM(CASE WHEN tk.status='done' THEN 1 ELSE 0 END) as done_count
            FROM projects p
            LEFT JOIN teams t ON p.team_id=t.id
            LEFT JOIN users u ON p.created_by=u.id
            LEFT JOIN tasks tk ON p.id=tk.project_id
            GROUP BY p.id ORDER BY p.created_at DESC
        """).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.*, t.name as team_name, u.name as creator_name,
                   COUNT(DISTINCT tk.id) as task_count,
                   SUM(CASE WHEN tk.status='done' THEN 1 ELSE 0 END) as done_count
            FROM projects p
            LEFT JOIN teams t ON p.team_id=t.id
            LEFT JOIN users u ON p.created_by=u.id
            LEFT JOIN tasks tk ON p.id=tk.project_id
            JOIN team_members tm ON p.team_id=tm.team_id
            WHERE tm.user_id=?
            GROUP BY p.id ORDER BY p.created_at DESC
        """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_project(project_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT p.*, t.name as team_name FROM projects p
        LEFT JOIN teams t ON p.team_id=t.id
        WHERE p.id=?
    """, (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_project_status(project_id, status):
    conn = get_connection()
    conn.execute("UPDATE projects SET status=? WHERE id=?", (status, project_id))
    conn.commit()
    conn.close()

def delete_project(project_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE project_id=?", (project_id,))
    conn.execute("DELETE FROM milestones WHERE project_id=?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()

# ── Milestones ─────────────────────────────────────────
def create_milestone(project_id, title, description, due_date):
    conn = get_connection()
    cur = conn.execute("INSERT INTO milestones (project_id,title,description,due_date) VALUES (?,?,?,?)",
                       (project_id, title, description, due_date))
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return mid

def get_milestones(project_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM milestones WHERE project_id=? ORDER BY due_date", (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_milestone_status(milestone_id, status):
    conn = get_connection()
    conn.execute("UPDATE milestones SET status=? WHERE id=?", (status, milestone_id))
    conn.commit()
    conn.close()

# ── Tasks ──────────────────────────────────────────────
def create_task(project_id, title, description, assigned_to, created_by,
                priority, due_date, estimated_hours, milestone_id=None):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO tasks (project_id,milestone_id,title,description,assigned_to,
                           created_by,priority,due_date,estimated_hours)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (project_id, milestone_id, title, description, assigned_to,
          created_by, priority, due_date, estimated_hours))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(project_id=None, assigned_to=None, status=None):
    conn = get_connection()
    query = """
        SELECT tk.*, u.name as assignee_name, u.email as assignee_email,
               p.name as project_name, m.title as milestone_title
        FROM tasks tk
        LEFT JOIN users u ON tk.assigned_to=u.id
        LEFT JOIN projects p ON tk.project_id=p.id
        LEFT JOIN milestones m ON tk.milestone_id=m.id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND tk.project_id=?"
        params.append(project_id)
    if assigned_to:
        query += " AND tk.assigned_to=?"
        params.append(assigned_to)
    if status:
        query += " AND tk.status=?"
        params.append(status)
    query += " ORDER BY tk.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_task(task_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT tk.*, u.name as assignee_name, p.name as project_name
        FROM tasks tk
        LEFT JOIN users u ON tk.assigned_to=u.id
        LEFT JOIN projects p ON tk.project_id=p.id
        WHERE tk.id=?
    """, (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_task_status(task_id, status):
    conn = get_connection()
    conn.execute("UPDATE tasks SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, task_id))
    conn.commit()
    conn.close()

def update_task(task_id, title, description, assigned_to, priority, due_date, estimated_hours, status):
    conn = get_connection()
    conn.execute("""
        UPDATE tasks SET title=?,description=?,assigned_to=?,priority=?,
        due_date=?,estimated_hours=?,status=?,updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (title, description, assigned_to, priority, due_date, estimated_hours, status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM comments WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM time_logs WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM attachments WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# ── Comments ───────────────────────────────────────────
def add_comment(task_id, user_id, comment):
    conn = get_connection()
    conn.execute("INSERT INTO comments (task_id,user_id,comment) VALUES (?,?,?)", (task_id, user_id, comment))
    conn.commit()
    conn.close()

def get_comments(task_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.*, u.name as user_name FROM comments c
        JOIN users u ON c.user_id=u.id
        WHERE c.task_id=? ORDER BY c.created_at ASC
    """, (task_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Time Logs ──────────────────────────────────────────
def log_time(task_id, user_id, hours, description, logged_date):
    conn = get_connection()
    conn.execute("INSERT INTO time_logs (task_id,user_id,hours,description,logged_date) VALUES (?,?,?,?,?)",
                 (task_id, user_id, hours, description, logged_date))
    conn.execute("UPDATE tasks SET logged_hours=logged_hours+? WHERE id=?", (hours, task_id))
    conn.commit()
    conn.close()

def get_time_logs(task_id=None, user_id=None):
    conn = get_connection()
    query = """
        SELECT tl.*, u.name as user_name, tk.title as task_title, p.name as project_name
        FROM time_logs tl
        JOIN users u ON tl.user_id=u.id
        JOIN tasks tk ON tl.task_id=tk.id
        JOIN projects p ON tk.project_id=p.id
        WHERE 1=1
    """
    params = []
    if task_id:
        query += " AND tl.task_id=?"
        params.append(task_id)
    if user_id:
        query += " AND tl.user_id=?"
        params.append(user_id)
    query += " ORDER BY tl.logged_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Attachments ────────────────────────────────────────
def save_attachment(task_id, user_id, filename, filepath, filesize):
    conn = get_connection()
    conn.execute("INSERT INTO attachments (task_id,user_id,filename,filepath,filesize) VALUES (?,?,?,?,?)",
                 (task_id, user_id, filename, filepath, filesize))
    conn.commit()
    conn.close()

def get_attachments(task_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.*, u.name as user_name FROM attachments a
        JOIN users u ON a.user_id=u.id
        WHERE a.task_id=? ORDER BY a.uploaded_at DESC
    """, (task_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Notifications ──────────────────────────────────────
def add_notification(user_id, title, message):
    conn = get_connection()
    conn.execute("INSERT INTO notifications (user_id,title,message) VALUES (?,?,?)", (user_id, title, message))
    conn.commit()
    conn.close()

def get_notifications(user_id, unread_only=False):
    conn = get_connection()
    query = "SELECT * FROM notifications WHERE user_id=?"
    if unread_only:
        query += " AND is_read=0"
    query += " ORDER BY created_at DESC LIMIT 50"
    rows = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_notifications_read(user_id):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ── Dashboard Stats ────────────────────────────────────
def get_dashboard_stats(user_id=None, role=None):
    conn = get_connection()
    if role == 'admin':
        stats = {
            'total_projects': conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
            'active_projects': conn.execute("SELECT COUNT(*) FROM projects WHERE status='active'").fetchone()[0],
            'total_tasks': conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
            'completed_tasks': conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0],
            'total_users': conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            'total_teams': conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0],
            'overdue_tasks': conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE due_date < date('now') AND status != 'done'"
            ).fetchone()[0],
            'total_hours': conn.execute("SELECT COALESCE(SUM(hours),0) FROM time_logs").fetchone()[0],
        }
    else:
        stats = {
            'my_tasks': conn.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to=?", (user_id,)).fetchone()[0],
            'completed_tasks': conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND status='done'", (user_id,)
            ).fetchone()[0],
            'in_progress': conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND status='inprogress'", (user_id,)
            ).fetchone()[0],
            'overdue_tasks': conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND due_date < date('now') AND status!='done'",
                (user_id,)
            ).fetchone()[0],
            'total_hours': conn.execute(
                "SELECT COALESCE(SUM(hours),0) FROM time_logs WHERE user_id=?", (user_id,)
            ).fetchone()[0],
        }
    conn.close()
    return stats
