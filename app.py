import os, sqlite3, secrets
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

ROOT=os.path.dirname(os.path.abspath(__file__))
DB=os.environ.get("DATABASE_PATH", os.path.join(ROOT,"data","sar.db"))
os.makedirs(os.path.dirname(DB), exist_ok=True)
app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY") or secrets.token_hex(32)
STATUSES=["พร้อมปฏิบัติงาน","ปฏิบัติงานอยู่","ปฏิบัติภารกิจ","ติดราชการ/ประชุม","ฝึก/อบรม","ลา","ยังไม่ยืนยัน"]
HOURS=int(os.environ.get("STATUS_EXPIRY_HOURS","4"))

def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def ts(): return datetime.now(timezone.utc).isoformat()
def init():
    with connect() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password_hash TEXT,role TEXT DEFAULT 'admin');
        CREATE TABLE IF NOT EXISTS personnel(id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT,section TEXT,status TEXT,updated_at TEXT,updated_by TEXT,note TEXT DEFAULT '',active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY,personnel_id INTEGER REFERENCES personnel(id),old_status TEXT,new_status TEXT,changed_at TEXT,changed_by TEXT,note TEXT DEFAULT '');""")
        if not c.execute("SELECT 1 FROM users").fetchone():
            pw=os.environ.get("ADMIN_PASSWORD")
            if not pw:
                pw=secrets.token_urlsafe(18); print("\\n[ONE-TIME ADMIN PASSWORD]",pw,"\\nSet ADMIN_PASSWORD environment variable for stable credentials.\\n")
            c.execute("INSERT INTO users(username,password_hash) VALUES(?,?)",(os.environ.get("ADMIN_USERNAME","admin"),generate_password_hash(pw)))
        if not c.execute("SELECT 1 FROM personnel").fetchone():
            sample=[("DEMO-001","เจ้าหน้าที่ตัวอย่าง 01","สื่อสาร","พร้อมปฏิบัติงาน"),("DEMO-002","เจ้าหน้าที่ตัวอย่าง 02","สื่อสาร","ปฏิบัติภารกิจ"),("DEMO-003","เจ้าหน้าที่ตัวอย่าง 03","สนับสนุน","พร้อมปฏิบัติงาน"),("DEMO-004","เจ้าหน้าที่ตัวอย่าง 04","สื่อสาร","ฝึก/อบรม"),("DEMO-005","เจ้าหน้าที่ตัวอย่าง 05","สนับสนุน","ปฏิบัติงานอยู่"),("DEMO-006","เจ้าหน้าที่ตัวอย่าง 06","สื่อสาร","พร้อมปฏิบัติงาน"),("DEMO-007","เจ้าหน้าที่ตัวอย่าง 07","สนับสนุน","ติดราชการ/ประชุม"),("DEMO-008","เจ้าหน้าที่ตัวอย่าง 08","สื่อสาร","ลา"),("DEMO-009","เจ้าหน้าที่ตัวอย่าง 09","สนับสนุน","พร้อมปฏิบัติงาน"),("DEMO-010","เจ้าหน้าที่ตัวอย่าง 10","สื่อสาร","ยังไม่ยืนยัน"),("DEMO-011","เจ้าหน้าที่ตัวอย่าง 11","สนับสนุน","พร้อมปฏิบัติงาน"),("DEMO-012","เจ้าหน้าที่ตัวอย่าง 12","สนับสนุน","ปฏิบัติภารกิจ")]
            c.executemany("INSERT INTO personnel(code,name,section,status,updated_at,updated_by) VALUES(?,?,?,?,?,?)",[(a,b,d,e,None if e=="ยังไม่ยืนยัน" else ts(),"ข้อมูลจำลอง") for a,b,d,e in sample])
def require_login(fn):
    @wraps(fn)
    def inner(*a,**kw):
        if not session.get("uid"): return redirect(url_for("login",next=request.path))
        return fn(*a,**kw)
    return inner
def effective(p):
    if not p["updated_at"]: return "ยังไม่ยืนยัน"
    try:
        d=datetime.fromisoformat(p["updated_at"])
        if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc)-d.astimezone(timezone.utc)>timedelta(hours=HOURS): return "ยังไม่ยืนยัน"
    except Exception: return "ยังไม่ยืนยัน"
    return p["status"]
def people():
    with connect() as c: rows=c.execute("SELECT * FROM personnel WHERE active=1 ORDER BY code").fetchall()
    result=[]
    q=request.args.get("q","").casefold().strip(); filt=request.args.get("status","")
    for row in rows:
        p=dict(row); p["effective_status"]=effective(row)
        if q and q not in (p["name"]+" "+p["code"]+" "+p["section"]).casefold(): continue
        if filt and p["effective_status"]!=filt: continue
        result.append(p)
    return result
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        with connect() as c: u=c.execute("SELECT * FROM users WHERE username=?",(request.form.get("username","").strip(),)).fetchone()
        if u and check_password_hash(u["password_hash"],request.form.get("password","")):
            session.clear(); session["uid"]=u["id"]; session["username"]=u["username"]
            return redirect(url_for("home"))
        flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    return render_template("login.html")
@app.get("/logout")
def logout(): session.clear(); return redirect(url_for("login"))
@app.get("/")
@require_login
def home():
    allp=people(); counts={s:sum(p["effective_status"]==s for p in allp) for s in STATUSES}
    return render_template("index.html",people=allp,counts=counts,statuses=STATUSES,total=len(allp),hours=HOURS,username=session.get("username"),q=request.args.get("q",""),selected=request.args.get("status",""))
@app.post("/update")
@require_login
def update():
    pid=request.form.get("personnel_id",type=int); status=request.form.get("status",""); note=request.form.get("note","").strip()[:240]
    if status not in STATUSES or status=="ยังไม่ยืนยัน": flash("สถานะไม่ถูกต้อง"); return redirect(url_for("home"))
    with connect() as c:
        p=c.execute("SELECT * FROM personnel WHERE id=? AND active=1",(pid,)).fetchone()
        if not p: flash("ไม่พบรายชื่อ"); return redirect(url_for("home"))
        old=effective(p); t=ts(); user=session.get("username","")
        c.execute("UPDATE personnel SET status=?,updated_at=?,updated_by=?,note=? WHERE id=?",(status,t,user,note,pid))
        c.execute("INSERT INTO history(personnel_id,old_status,new_status,changed_at,changed_by,note) VALUES(?,?,?,?,?,?)",(pid,old,status,t,user,note))
    flash("บันทึกสถานะเรียบร้อย"); return redirect(url_for("home"))
@app.get("/history/<int:pid>")
@require_login
def history(pid):
    with connect() as c: rows=c.execute("SELECT * FROM history WHERE personnel_id=? ORDER BY id DESC LIMIT 100",(pid,)).fetchall()
    return render_template("history.html",rows=rows)
init()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT","5000")),debug=False)
