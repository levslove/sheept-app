"""
AI Consult Pro — A landing page for AI consulting
Built by Sheept 🐑💤 | Type: dashboard | Seed: 3f737e9222dd
"""
import json, sqlite3, uuid, hashlib
from datetime import datetime, timezone
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AI Consult Pro", description="A landing page for AI consulting")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
DB = "/tmp/ai_consult_pro_3f737e.db"

@contextmanager
def db():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    try: yield conn.cursor(); conn.commit()
    finally: conn.close()

def uid(): return uuid.uuid4().hex[:12]
def now(): return datetime.now(timezone.utc).isoformat()
def hash_pw(pw: str) -> str: return hashlib.sha256(pw.encode()).hexdigest()

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS auth_users (id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'user', created_at TEXT);
        CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, user_id TEXT, message TEXT, rating INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, data JSON, user_id TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS metrics (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, value REAL, unit TEXT, recorded_at TEXT);
        CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, user_id TEXT, title TEXT, data JSON, period TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS alerts (id TEXT PRIMARY KEY, user_id TEXT, metric_name TEXT, threshold REAL, direction TEXT DEFAULT 'above', active INTEGER DEFAULT 1, created_at TEXT);
        CREATE TABLE IF NOT EXISTS data_points (id TEXT PRIMARY KEY, metric_id TEXT, value REAL, timestamp TEXT);
        CREATE TABLE IF NOT EXISTS dashboards (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, layout JSON, created_at TEXT);
        """)
init()

def get_user(auth: Optional[str] = Header(None)):
    if not auth: raise HTTPException(401, "Missing Auth")
    with db() as c:
        c.execute("SELECT * FROM auth_users WHERE id=?", (auth.replace("Bearer ", ""),))
        u = c.fetchone()
        if not u: raise HTTPException(401, "Invalid token")
        return dict(u)

class RegisterReq(BaseModel): username: str; password: str
class LoginReq(BaseModel): username: str; password: str

@app.post("/register")
def register(r: RegisterReq):
    u = uid()
    with db() as c:
        try: c.execute("INSERT INTO auth_users VALUES (?,?,?,?,?)", (u, r.username, hash_pw(r.password), "user", now()))
        except sqlite3.IntegrityError: raise HTTPException(409, "Username taken")
    return {"user_id": u, "token": u}

@app.post("/login")
def login(r: LoginReq):
    with db() as c:
        c.execute("SELECT * FROM auth_users WHERE username=? AND password_hash=?", (r.username, hash_pw(r.password)))
        u = c.fetchone()
        if not u: raise HTTPException(401, "Invalid credentials")
    return {"user_id": u["id"], "token": u["id"], "username": u["username"]}

class MetricsReq(BaseModel):
    name: str
    value: float

class ReportsReq(BaseModel):
    title: str

class AlertsReq(BaseModel):
    metric_name: str
    threshold: float

@app.get("/metrics")
def list_metrics(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM metrics ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/metrics")
def create_metrics(r: MetricsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO metrics ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/metrics/{id}")
def get_metrics(id: str):
    with db() as c: c.execute("SELECT * FROM metrics WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/metrics/{id}")
def delete_metrics(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM metrics WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/reports")
def list_reports(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/reports")
def create_reports(r: ReportsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO reports ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/reports/{id}")
def get_reports(id: str):
    with db() as c: c.execute("SELECT * FROM reports WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/reports/{id}")
def delete_reports(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM reports WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/alerts")
def list_alerts(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/alerts")
def create_alerts(r: AlertsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO alerts ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/alerts/{id}")
def get_alerts(id: str):
    with db() as c: c.execute("SELECT * FROM alerts WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/alerts/{id}")
def delete_alerts(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM alerts WHERE id=?", (id,))
    return {"id": id, "deleted": True}

@app.get("/metrics/summary")
def metrics_summary(auth: Optional[str] = Header(None)):
    u = get_user(auth)
    with db() as c: c.execute("SELECT name, AVG(value) as avg_val FROM metrics WHERE user_id=? GROUP BY name", (u["id"],)); return [dict(r) for r in c.fetchall()]

class FeedbackReq(BaseModel): message: str; rating: Optional[int] = None

@app.post("/feedback")
def submit_feedback(r: FeedbackReq, auth: Optional[str] = Header(None)):
    user_id = None
    if auth:
        try: user_id = get_user(auth)["id"]
        except Exception: pass
    with db() as c: c.execute("INSERT INTO feedback VALUES (?,?,?,?,?)", (uid(), user_id, r.message, r.rating, now()))
    return {"message": "Thanks! 🐑"}

@app.get("/stats")
def stats():
    with db() as c:
        c.execute("SELECT COUNT(*) as cnt FROM auth_users"); users = c.fetchone()["cnt"]
    return {"total_users": users, "built_with": "Sheept 🐑"}

@app.get("/health")
def health(): return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
def home(): return FRONTEND_HTML


FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Consult Pro</title><script src="https://cdn.tailwindcss.com"></script>
<style>
:root { --pr:#1e293b; --sc:#10b981; --ac:#12aada; --bg:#0f172a; --tx:#e2e8f0; }
* { margin:0; padding:0; box-sizing:border-box; font-family:system-ui; }
body { background:var(--bg); color:var(--tx); }
.nav { display:flex; justify-content:space-between; padding:1rem 2rem; border-bottom:1px solid var(--pr); }
.hero { text-align:center; padding:4rem 2rem; } .hero h1 { color:var(--sc); font-size:3rem; }
.btn { padding:0.5rem 1rem; background:var(--ac); color:#fff; border:none; border-radius:8px; cursor:pointer; }
.section { padding:2rem; max-width:800px; margin:0 auto; } .card { border:1px solid var(--pr); padding:1rem; border-radius:8px; margin-bottom:1rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; }
input, textarea { width:100%; padding:0.5rem; margin-bottom:0.5rem; background:var(--bg); color:var(--tx); border:1px solid var(--pr); }
</style></head><body>
<nav class="nav"><div>🐑 AI Consult Pro</div><a href="#auth" style="color:var(--tx)">Sign In</a></nav>
<section class="hero"><h1>AI Consult Pro</h1><p>A landing page for AI consulting</p></section>
<section class="section" id="overview"><h2>📊 Dashboard</h2><div class="grid" id="stats-grid">Loading...</div><div class="card"><input id="metric-name"><input id="metric-value" type="number"><button class="btn" onclick="addMetric()">Track</button></div></section>
<section class="section" id="auth"><h2>Join</h2><div class="card"><input id="user" placeholder="Username"><input id="pass" type="password" placeholder="Password"><button class="btn" onclick="auth('/register')">Register</button><button class="btn" onclick="auth('/login')">Login</button></div></section>
<footer style="text-align:center;padding:2rem;">Built with 🐑 Sheept</footer>
<script>
const API = window.location.origin; let TOKEN = localStorage.getItem('token');
async function api(path, opts = {}) {
    if(TOKEN) opts.headers = {...opts.headers, 'Authorization': 'Bearer '+TOKEN};
    opts.headers = {...opts.headers, 'Content-Type': 'application/json'};
    const r = await fetch(API+path, opts); if(!r.ok) throw new Error('Error'); return r.json();
}
async function auth(path) {
    try { const d = await api(path, {method:'POST', body:JSON.stringify({username:document.getElementById('user').value, password:document.getElementById('pass').value})}); TOKEN=d.token; localStorage.setItem('token',TOKEN); loadData(); alert('Success!'); } catch(e) { alert('Failed'); }
}
async function loadData() {}async function addMetric() { await api('/metrics', {method:'POST', body: JSON.stringify({name: document.getElementById('metric-name').value, value: parseFloat(document.getElementById('metric-value').value)})}); loadData(); }
if(TOKEN) loadData();
</script></body></html>"""
