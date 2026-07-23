import sqlite3
import os
import json
import uuid
from datetime import datetime


def get_config_path():
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    config_dir = os.path.join(app_data, 'HelixDesk')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.json')


def get_default_db_path():
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    data_dir = os.path.join(app_data, 'HelixDesk')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'helixdesk.db')


def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(updates):
    config_path = get_config_path()
    config = load_config()
    config.update(updates)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return config


def get_db_path():
    config = load_config()
    db_path = config.get('dbPath', '')
    if db_path and os.path.exists(os.path.dirname(db_path)):
        return db_path
    return get_default_db_path()


def migrate_db(new_path):
    old_path = get_db_path()
    if old_path == new_path:
        return False
    try:
        new_dir = os.path.dirname(new_path)
        os.makedirs(new_dir, exist_ok=True)
        if os.path.exists(old_path):
            import shutil
            shutil.copy2(old_path, new_path)
        save_config({'dbPath': new_path})
        return True
    except Exception as e:
        print(f'Migration failed: {e}')
        return False


def get_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(id),
            title TEXT NOT NULL,
            purpose TEXT DEFAULT '',
            date TEXT DEFAULT (date('now','localtime')),
            location TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS steps (
            id TEXT PRIMARY KEY,
            experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            order_num INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY,
            experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            step_id TEXT,
            type TEXT DEFAULT 'text',
            content TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            experiment_id TEXT,
            title TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS materials (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT DEFAULT '',
            vendor TEXT DEFAULT '',
            catalog TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS experiment_materials (
            experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            material_id TEXT REFERENCES materials(id),
            usage_text TEXT DEFAULT '',
            PRIMARY KEY (experiment_id, material_id)
        );
    ''')
    conn.commit()
    conn.close()


def new_id():
    return str(uuid.uuid4())


# ====== 项目 ======

def list_projects():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM projects ORDER BY updated_at DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_project(name, description=''):
    pid = new_id()
    conn = get_connection()
    conn.execute('INSERT INTO projects (id, name, description) VALUES (?, ?, ?)',
                 (pid, name, description))
    conn.commit()
    row = conn.execute('SELECT * FROM projects WHERE id = ?', (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_project(pid):
    conn = get_connection()
    conn.execute('DELETE FROM results WHERE experiment_id IN (SELECT id FROM experiments WHERE project_id = ?)', (pid,))
    conn.execute('DELETE FROM steps WHERE experiment_id IN (SELECT id FROM experiments WHERE project_id = ?)', (pid,))
    conn.execute('DELETE FROM experiment_materials WHERE experiment_id IN (SELECT id FROM experiments WHERE project_id = ?)', (pid,))
    conn.execute('DELETE FROM experiments WHERE project_id = ?', (pid,))
    conn.execute('DELETE FROM projects WHERE id = ?', (pid,))
    conn.commit()
    conn.close()


# ====== 实验 ======

def list_experiments(project_id=None):
    conn = get_connection()
    if project_id:
        rows = conn.execute('''
            SELECT e.*, p.name as project_name FROM experiments e
            LEFT JOIN projects p ON e.project_id = p.id
            WHERE e.project_id = ? ORDER BY e.date DESC, e.created_at DESC
        ''', (project_id,)).fetchall()
    else:
        rows = conn.execute('''
            SELECT e.*, p.name as project_name FROM experiments e
            LEFT JOIN projects p ON e.project_id = p.id
            ORDER BY e.date DESC, e.created_at DESC
        ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_experiment(project_id, title, purpose='', date=None, location=''):
    eid = new_id()
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    conn = get_connection()
    conn.execute('INSERT INTO experiments (id, project_id, title, purpose, date, location) VALUES (?, ?, ?, ?, ?, ?)',
                 (eid, project_id, title, purpose, date, location))
    conn.commit()
    conn.close()
    return get_experiment(eid)


def get_experiment(eid):
    conn = get_connection()
    row = conn.execute('''
        SELECT e.*, p.name as project_name FROM experiments e
        LEFT JOIN projects p ON e.project_id = p.id WHERE e.id = ?
    ''', (eid,)).fetchone()
    if not row:
        conn.close()
        return None
    exp = dict(row)
    exp['steps'] = [dict(s) for s in conn.execute('SELECT * FROM steps WHERE experiment_id = ? ORDER BY order_num ASC', (eid,)).fetchall()]
    exp['results'] = [dict(r) for r in conn.execute('SELECT * FROM results WHERE experiment_id = ? ORDER BY created_at ASC', (eid,)).fetchall()]
    exp['materials'] = [dict(m) for m in conn.execute('''
        SELECT m.*, em.usage_text FROM materials m
        JOIN experiment_materials em ON m.id = em.material_id
        WHERE em.experiment_id = ?
    ''', (eid,)).fetchall()]
    conn.close()
    return exp


def update_experiment(eid, fields):
    sets = []
    vals = []
    for key in ['title', 'purpose', 'date', 'location', 'status', 'project_id']:
        if key in fields:
            sets.append(f'{key} = ?')
            vals.append(fields[key])
    if not sets:
        return get_experiment(eid)
    sets.append("updated_at = datetime('now','localtime')")
    vals.append(eid)
    conn = get_connection()
    conn.execute(f'UPDATE experiments SET {", ".join(sets)} WHERE id = ?', vals)
    conn.commit()
    conn.close()
    return get_experiment(eid)


def delete_experiment(eid):
    conn = get_connection()
    conn.execute('DELETE FROM results WHERE experiment_id = ?', (eid,))
    conn.execute('DELETE FROM steps WHERE experiment_id = ?', (eid,))
    conn.execute('DELETE FROM experiment_materials WHERE experiment_id = ?', (eid,))
    conn.execute('DELETE FROM experiments WHERE id = ?', (eid,))
    conn.commit()
    conn.close()


# ====== 步骤 ======

def add_step(experiment_id, title, content=''):
    sid = new_id()
    conn = get_connection()
    max_order = conn.execute('SELECT COALESCE(MAX(order_num), -1) + 1 as next FROM steps WHERE experiment_id = ?',
                             (experiment_id,)).fetchone()['next']
    conn.execute('INSERT INTO steps (id, experiment_id, title, content, order_num) VALUES (?, ?, ?, ?, ?)',
                 (sid, experiment_id, title, content, max_order))
    conn.commit()
    conn.close()
    return {'id': sid, 'experiment_id': experiment_id, 'title': title, 'content': content, 'order_num': max_order}


def delete_step(sid):
    conn = get_connection()
    conn.execute('DELETE FROM steps WHERE id = ?', (sid,))
    conn.commit()
    conn.close()


# ====== 结果 ======

def add_result(experiment_id, content, type='text', step_id=None):
    rid = new_id()
    conn = get_connection()
    conn.execute('INSERT INTO results (id, experiment_id, step_id, type, content) VALUES (?, ?, ?, ?, ?)',
                 (rid, experiment_id, step_id, type, content))
    conn.commit()
    conn.close()
    return {'id': rid, 'experiment_id': experiment_id, 'content': content, 'type': type}


def delete_result(rid):
    conn = get_connection()
    conn.execute('DELETE FROM results WHERE id = ?', (rid,))
    conn.commit()
    conn.close()


# ====== 计划 ======

def list_plans(date=None):
    conn = get_connection()
    if date:
        rows = conn.execute('''
            SELECT p.*, e.title as experiment_title FROM plans p
            LEFT JOIN experiments e ON p.experiment_id = e.id
            WHERE p.date = ? ORDER BY p.created_at ASC
        ''', (date,)).fetchall()
    else:
        rows = conn.execute('''
            SELECT p.*, e.title as experiment_title FROM plans p
            LEFT JOIN experiments e ON p.experiment_id = e.id
            ORDER BY p.date ASC, p.created_at ASC
        ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_plan(date, title, experiment_id=None):
    pid = new_id()
    conn = get_connection()
    conn.execute('INSERT INTO plans (id, date, experiment_id, title) VALUES (?, ?, ?, ?)',
                 (pid, date, experiment_id, title))
    conn.commit()
    conn.close()
    return {'id': pid, 'date': date, 'title': title, 'done': 0}


def toggle_plan(pid):
    conn = get_connection()
    conn.execute('UPDATE plans SET done = CASE WHEN done THEN 0 ELSE 1 END WHERE id = ?', (pid,))
    conn.commit()
    row = conn.execute('SELECT * FROM plans WHERE id = ?', (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_plan(pid):
    conn = get_connection()
    conn.execute('DELETE FROM plans WHERE id = ?', (pid,))
    conn.commit()
    conn.close()


# ====== 材料 ======

def list_materials():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM materials ORDER BY name ASC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_material(name, type='', vendor='', catalog='', notes=''):
    mid = new_id()
    conn = get_connection()
    conn.execute('INSERT INTO materials (id, name, type, vendor, catalog, notes) VALUES (?, ?, ?, ?, ?, ?)',
                 (mid, name, type, vendor, catalog, notes))
    conn.commit()
    conn.close()
    return {'id': mid, 'name': name, 'type': type}


def link_material_to_experiment(experiment_id, material_id, usage=''):
    conn = get_connection()
    conn.execute('INSERT OR REPLACE INTO experiment_materials (experiment_id, material_id, usage_text) VALUES (?, ?, ?)',
                 (experiment_id, material_id, usage))
    conn.commit()
    conn.close()


# ====== 搜索 ======

def search(query):
    q = f'%{query}%'
    conn = get_connection()
    exps = [dict(r) for r in conn.execute('''
        SELECT e.*, p.name as project_name FROM experiments e
        LEFT JOIN projects p ON e.project_id = p.id
        WHERE e.title LIKE ? OR e.purpose LIKE ? ORDER BY e.updated_at DESC
    ''', (q, q)).fetchall()]

    steps = [dict(r) for r in conn.execute('''
        SELECT s.*, e.title as experiment_title FROM steps s
        JOIN experiments e ON s.experiment_id = e.id
        WHERE s.title LIKE ? OR s.content LIKE ? ORDER BY s.order_num ASC
    ''', (q, q)).fetchall()]

    mats = [dict(r) for r in conn.execute('''
        SELECT * FROM materials WHERE name LIKE ? OR type LIKE ? ORDER BY name ASC
    ''', (q, q)).fetchall()]

    conn.close()
    return {'experiments': exps, 'steps': steps, 'materials': mats}