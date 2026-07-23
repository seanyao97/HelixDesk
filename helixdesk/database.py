import sqlite3, os, json, uuid
from datetime import datetime

CFG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'HelixDesk')
os.makedirs(CFG_DIR, exist_ok=True)
CFG_PATH = os.path.join(CFG_DIR, 'config.json')

def _cfg():
    try:
        with open(CFG_PATH, encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def _save_cfg(u):
    c = _cfg()
    c.update(u)
    with open(CFG_PATH, 'w', encoding='utf-8') as f:
        json.dump(c, f, indent=2, ensure_ascii=False)

def get_db_path():
    c = _cfg()
    p = c.get('dbPath', '')
    if p and os.path.exists(os.path.dirname(p)):
        return p
    return os.path.join(CFG_DIR, 'helixdesk.db')

def migrate_db(np):
    op = get_db_path()
    if op == np:
        return False
    try:
        os.makedirs(os.path.dirname(np), exist_ok=True)
        if os.path.exists(op):
            import shutil
            shutil.copy2(op, np)
        _save_cfg({'dbPath': np})
        return True
    except:
        return False

def conn():
    db = sqlite3.connect(get_db_path())
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db

def init():
    c = conn()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id),
            title TEXT NOT NULL, purpose TEXT DEFAULT '',
            date TEXT DEFAULT (date('now','localtime')),
            location TEXT DEFAULT '', status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS steps (
            id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            title TEXT NOT NULL, content TEXT DEFAULT '', order_num INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            step_id TEXT, type TEXT DEFAULT 'text', content TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY, date TEXT NOT NULL, experiment_id TEXT,
            title TEXT NOT NULL, done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS materials (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT DEFAULT '',
            vendor TEXT DEFAULT '', catalog TEXT DEFAULT '', notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS experiment_materials (
            experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            material_id TEXT REFERENCES materials(id), usage_text TEXT DEFAULT '',
            PRIMARY KEY (experiment_id, material_id));
        CREATE TABLE IF NOT EXISTS run_logs (
            id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            version INTEGER DEFAULT 1, run_date TEXT, observations TEXT DEFAULT '',
            deviations TEXT DEFAULT '', conclusion TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS parameters (
            id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id) ON DELETE CASCADE,
            step_id TEXT, name TEXT NOT NULL, value TEXT DEFAULT '', unit TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')));
    ''')
    c.commit()
    c.close()

def uid():
    return str(uuid.uuid4())
def list_projects():
    c = conn()
    r = [dict(x) for x in c.execute("SELECT * FROM projects ORDER BY updated_at DESC")]
    c.close()
    return r

def create_project(name, desc=""):
    p = uid()
    c = conn()
    c.execute("INSERT INTO projects (id, name, description) VALUES (?, ?, ?)", (p, name, desc))
    c.commit()
    row = c.execute("SELECT * FROM projects WHERE id = ?", (p,)).fetchone()
    c.close()
    return dict(row) if row else None

def delete_project(pid):
    c = conn()
    results = c.execute("SELECT id FROM experiments WHERE project_id = ?", (pid,)).fetchall()
    for r in results:
        eid = r["id"]
        c.execute("DELETE FROM results WHERE experiment_id = ?", (eid,))
        c.execute("DELETE FROM steps WHERE experiment_id = ?", (eid,))
        c.execute("DELETE FROM experiment_materials WHERE experiment_id = ?", (eid,))
        c.execute("DELETE FROM run_logs WHERE experiment_id = ?", (eid,))
        c.execute("DELETE FROM parameters WHERE experiment_id = ?", (eid,))
    c.execute("DELETE FROM experiments WHERE project_id = ?", (pid,))
    c.execute("DELETE FROM plans WHERE experiment_id IN (SELECT id FROM experiments WHERE project_id = ?)", (pid,))
    c.execute("DELETE FROM projects WHERE id = ?", (pid,))
    c.commit()
    c.close()

def list_experiments(pid=None):
    c = conn()
    sql = "SELECT e.*, p.name as project_name FROM experiments e LEFT JOIN projects p ON e.project_id = p.id"
    params = []
    if pid:
        sql += " WHERE e.project_id = ?"
        params.append(pid)
    sql += " ORDER BY e.date DESC, e.created_at DESC"
    r = [dict(x) for x in c.execute(sql, params)]
    c.close()
    return r

def create_experiment(pid, title, purpose="", date=None, location=""):
    e = uid()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    c = conn()
    c.execute("INSERT INTO experiments (id, project_id, title, purpose, date, location) VALUES (?, ?, ?, ?, ?, ?)",
              (e, pid, title, purpose, date, location))
    c.commit()
    c.close()
    return get_experiment(e)

def get_experiment(eid):
    c = conn()
    row = c.execute("""SELECT e.*, p.name as project_name FROM experiments e
        LEFT JOIN projects p ON e.project_id = p.id WHERE e.id = ?""", (eid,)).fetchone()
    if not row:
        c.close()
        return None
    exp = dict(row)
    exp["steps"] = [dict(x) for x in c.execute("SELECT * FROM steps WHERE experiment_id = ? ORDER BY order_num ASC", (eid,))]
    exp["results"] = [dict(x) for x in c.execute("SELECT * FROM results WHERE experiment_id = ? ORDER BY created_at ASC", (eid,))]
    exp["materials"] = [dict(x) for x in c.execute("""SELECT m.*, em.usage_text FROM materials m
        JOIN experiment_materials em ON m.id = em.material_id WHERE em.experiment_id = ?""", (eid,))]
    exp["run_logs"] = [dict(x) for x in c.execute("SELECT * FROM run_logs WHERE experiment_id = ? ORDER BY version DESC", (eid,))]
    exp["parameters"] = [dict(x) for x in c.execute("SELECT * FROM parameters WHERE experiment_id = ? ORDER BY name ASC", (eid,))]
    c.close()
    return exp

def update_experiment(eid, fields):
    sets = []
    vals = []
    for k in ["title", "purpose", "date", "location", "status", "project_id"]:
        if k in fields:
            sets.append(f"{k} = ?")
            vals.append(fields[k])
    if not sets:
        return get_experiment(eid)
    sets.append("updated_at = datetime('now','localtime')")
    vals.append(eid)
    c = conn()
    c.execute(f"UPDATE experiments SET {', '.join(sets)} WHERE id = ?", vals)
    c.commit()
    c.close()
    return get_experiment(eid)

def delete_experiment(eid):
    c = conn()
    for t in ["results", "steps", "experiment_materials", "run_logs", "parameters", "experiments"]:
        c.execute(f"DELETE FROM {t} WHERE experiment_id = ?", (eid,))
    c.commit()
    c.close()

def add_step(eid, title, content=""):
    s = uid()
    c = conn()
    n = c.execute("SELECT COALESCE(MAX(order_num), -1) + 1 as n FROM steps WHERE experiment_id = ?", (eid,)).fetchone()["n"]
    c.execute("INSERT INTO steps (id, experiment_id, title, content, order_num) VALUES (?, ?, ?, ?, ?)", (s, eid, title, content, n))
    c.commit()
    c.close()
    return {"id": s, "title": title}

def delete_step(sid):
    c = conn()
    c.execute("DELETE FROM steps WHERE id = ?", (sid,))
    c.commit()
    c.close()

def add_result(eid, content, typ="text", step_id=None):
    r = uid()
    c = conn()
    c.execute("INSERT INTO results (id, experiment_id, step_id, type, content) VALUES (?, ?, ?, ?, ?)", (r, eid, step_id, typ, content))
    c.commit()
    c.close()
    return {"id": r}

def delete_result(rid):
    c = conn()
    c.execute("DELETE FROM results WHERE id = ?", (rid,))
    c.commit()
    c.close()

def list_plans(date=None):
    c = conn()
    sql = "SELECT p.*, e.title as experiment_title FROM plans p LEFT JOIN experiments e ON p.experiment_id = e.id"
    params = []
    if date:
        sql += " WHERE p.date = ?"
        params.append(date)
    sql += " ORDER BY p.date ASC, p.created_at ASC"
    r = [dict(x) for x in c.execute(sql, params)]
    c.close()
    return r

def add_plan(date, title, experiment_id=None):
    p = uid()
    c = conn()
    c.execute("INSERT INTO plans (id, date, experiment_id, title) VALUES (?, ?, ?, ?)", (p, date, experiment_id, title))
    c.commit()
    c.close()
    return {"id": p, "title": title, "done": 0}

def toggle_plan(pid):
    c = conn()
    c.execute("UPDATE plans SET done = CASE WHEN done THEN 0 ELSE 1 END WHERE id = ?", (pid,))
    c.commit()
    row = c.execute("SELECT * FROM plans WHERE id = ?", (pid,)).fetchone()
    c.close()
    return dict(row)

def delete_plan(pid):
    c = conn()
    c.execute("DELETE FROM plans WHERE id = ?", (pid,))
    c.commit()
    c.close()

def list_materials():
    c = conn()
    r = [dict(x) for x in c.execute("SELECT * FROM materials ORDER BY name ASC")]
    c.close()
    return r

def create_material(name, typ="", vendor="", catalog="", notes=""):
    m = uid()
    c = conn()
    c.execute("INSERT INTO materials (id, name, type, vendor, catalog, notes) VALUES (?, ?, ?, ?, ?, ?)", (m, name, typ, vendor, catalog, notes))
    c.commit()
    c.close()
    return {"id": m, "name": name}

def link_material(eid, mid, usage=""):
    c = conn()
    c.execute("INSERT OR REPLACE INTO experiment_materials VALUES (?, ?, ?)", (eid, mid, usage))
    c.commit()
    c.close()

def add_run_log(eid, obs="", dev="", con="", ver=1, rd=None):
    r = uid()
    if not rd:
        rd = datetime.now().strftime("%Y-%m-%d")
    c = conn()
    c.execute("INSERT INTO run_logs (id, experiment_id, version, run_date, observations, deviations, conclusion) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (r, eid, ver, rd, obs, dev, con))
    c.commit()
    c.close()
    return {"id": r}

def list_run_logs(eid):
    c = conn()
    r = [dict(x) for x in c.execute("SELECT * FROM run_logs WHERE experiment_id = ? ORDER BY version DESC", (eid,))]
    c.close()
    return r

def delete_run_log(rid):
    c = conn()
    c.execute("DELETE FROM run_logs WHERE id = ?", (rid,))
    c.commit()
    c.close()

def add_param(eid, name, value="", unit=""):
    p = uid()
    c = conn()
    c.execute("INSERT INTO parameters (id, experiment_id, name, value, unit) VALUES (?, ?, ?, ?, ?)", (p, eid, name, value, unit))
    c.commit()
    c.close()
    return {"id": p}

def list_params(eid):
    c = conn()
    r = [dict(x) for x in c.execute("SELECT * FROM parameters WHERE experiment_id = ? ORDER BY name ASC", (eid,))]
    c.close()
    return r

def delete_param(pid):
    c = conn()
    c.execute("DELETE FROM parameters WHERE id = ?", (pid,))
    c.commit()
    c.close()

def search(q):
    q = f"%{q}%"
    c = conn()
    exps = [dict(x) for x in c.execute("""SELECT e.*, p.name as project_name FROM experiments e
        LEFT JOIN projects p ON e.project_id = p.id WHERE e.title LIKE ? OR e.purpose LIKE ?""", (q, q))]
    steps = [dict(x) for x in c.execute("""SELECT s.*, e.title as experiment_title FROM steps s
        JOIN experiments e ON s.experiment_id = e.id WHERE s.title LIKE ? OR s.content LIKE ?""", (q, q))]
    mats = [dict(x) for x in c.execute("SELECT * FROM materials WHERE name LIKE ? OR type LIKE ?", (q, q))]
    c.close()
    return {"experiments": exps, "steps": steps, "materials": mats}

def export_markdown(eid):
    exp = get_experiment(eid)
    if not exp:
        return ""
    lines = [f"# {exp['title']}", ""]
    if exp.get("purpose"):
        lines.append(f"**目的：** {exp['purpose']}")
        lines.append("")
    lines.append(f"- **日期：** {exp.get('date', '')}")
    lines.append(f"- **地点：** {exp.get('location', '')}")
    smap = {"draft": "草稿", "submitted": "已提交", "archived": "已归档"}
    lines.append(f"- **状态：** {smap.get(exp.get(chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115), chr(33)), chr(33))}")
    if exp.get("steps"):
        lines.append("## 步骤")
        lines.append("")
        for i, s in enumerate(exp["steps"]):
            lines.append(f"### {i+1}. {s['title']}")
            if s.get("content"):
                lines.append("")
                lines.append(s["content"])
            lines.append("")
    if exp.get("parameters"):
        lines.append("## 参数")
        lines.append("")
        lines.append("| 名称 | 值 | 单位 |")
        lines.append("|------|-----|------|")
        for p in exp["parameters"]:
            lines.append(f"| {p['name']} | {p['value']} | {p['unit']} |")
        lines.append("")
    if exp.get("run_logs"):
        lines.append("## 运行日志")
        lines.append("")
        for log in exp["run_logs"]:
            lines.append(f"### v{log['version']} ({log.get('run_date', '')})")
            if log.get("observations"):
                lines.append(f"- 观察：{log['observations']}")
            if log.get("deviations"):
                lines.append(f"- 偏差：{log['deviations']}")
            if log.get("conclusion"):
                lines.append(f"- 结论：{log['conclusion']}")
            lines.append("")
    if exp.get("results"):
        lines.append("## 结果")
        lines.append("")
        for r in exp["results"]:
            lines.append(f"- {r['content']}")
        lines.append("")
    return "\n".join(lines)