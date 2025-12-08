import os
from flask import Flask, jsonify
import mysql.connector
from threading import Lock

app = Flask(__name__)

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_HOST = os.getenv("MYSQL_HOST", "db")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_NAME = os.getenv("MYSQL_DATABASE", "appdb")
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASS = os.getenv("MYSQL_PASSWORD", "apppass")

STUDENT_ID = os.getenv("STUDENT_ID", "4012262209")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                path VARCHAR(255) NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        app.logger.error(f"DB init failed: {e}")

_init_done = False
_init_lock = Lock()
def ensure_init():
    global _init_done
    if _init_done:
        return
    with _init_lock:
        if _init_done:
            return
        init_db()
        _init_done = True

@app.before_request
def _ensure_init_once():
    ensure_init()

def record_visit(path):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO visits (path) VALUES (%s);", (path,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        app.logger.error(f"record_visit failed: {e}")

@app.get("/")
def index():
    record_visit("/")
    return "<h1>Welcome</h1><p>This is the index page.</p>"

@app.get("/home")
def home():
    record_visit("/home")
    return "<h1>Home</h1><p>Hello from /home.</p>"  

@app.get("/about")
def about():
    record_visit("/about")
    return "<h1>About</h1><p>About this demo app.</p>"

@app.get(f"/{STUDENT_ID}")
def me():
    record_visit(f"/{STUDENT_ID}")
    return f"<h1>Student Route</h1><p>This is /{STUDENT_ID}</p>"

@app.get("/health")
def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchall()
        conn.close()
        return jsonify(status="ok"), 200
    except Exception as e:
        return jsonify(status="error", error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
