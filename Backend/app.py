import os
import sqlite3
import datetime
import numpy as np
import joblib
import jwt
import bcrypt
import warnings
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv  # ✅ NEW: Imports the tool to read .env files

# ───────── CONFIGURATION ──────────
# ✅ Load environment variables from the .env file
load_dotenv()

# ✅ Now it reads the key from the hidden file, NOT this code
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")

# Keep DB local for deployment (Cloud servers usually want it in the app folder)
DB_FILE = "quickeys.db"
CLF_PATH = "typing_model.pkl"

warnings.filterwarnings("ignore")
app = Flask(__name__)
CORS(app)

# ───────── 1. AUTO-DISCOVER AI MODEL ──────────
active_model_name = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("🔍 Searching for available AI models...")
        # Automatically find a model that supports content generation
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                active_model_name = m.name
                print(f"✅ FOUND WORKING MODEL: {active_model_name}")
                break
        if not active_model_name:
            print("⚠️ No text-generation models found. Feedback will be generic.")
    except Exception as e:
        print(f"⚠️ API Connection Error: {e}")
else:
    print("⚠️ GEMINI_API_KEY not found in environment variables.")

# ───────── 2. LOAD ML MODEL (Random Forest) ──────────
classifier = None
if os.path.exists(CLF_PATH):
    try:
        classifier = joblib.load(CLF_PATH)
        print("✅ Random Forest Model loaded.")
    except:
        print("⚠️ Random Forest pkl file not found.")

LABEL_MAP = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}

# ───────── 3. DATABASE SETUP ──────────
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        # Create Users Table
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                       (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)''')
        # Create History Table
        conn.execute('''CREATE TABLE IF NOT EXISTS history 
                       (id INTEGER PRIMARY KEY, user_id INTEGER, wpm REAL, accuracy REAL, 
                        mistakes INTEGER, level TEXT, date TEXT)''')
init_db()

# ───────── AI FEEDBACK LOGIC ──────────
def generate_feedback(typed_text, target_text, wpm, accuracy):
    if not active_model_name:
        return "- ⚠️ AI unavailable.\n- 🎯 Focus on accuracy."

    try:
        model = genai.GenerativeModel(active_model_name)
        prompt = f"""
        Act as a strict typing coach. Analyze this session:
        - Target: "{target_text[:100]}..."
        - Typed: "{typed_text[:100]}..."
        - Stats: {wpm} WPM, {accuracy}% Acc.
        
        Provide exactly 3 short, constructive bullet points on what to improve.
        Start each point with a dash "-".
        """
        response = model.generate_content(prompt)
        return response.text
    except:
        return "- ⚠️ AI busy. Focus on accuracy!"

# ───────── ROUTES: AUTHENTICATION ──────────
@app.route("/auth/register", methods=["POST"])
def register():
    data = request.json
    u = data.get("username", "").strip()
    p = data.get("password", "")
    
    if not u or not p:
        return jsonify(error="Username and password required"), 400

    try:
        hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
        with get_db() as conn:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (u, hashed))
        return jsonify(msg="Registered successfully")
    except sqlite3.IntegrityError:
        return jsonify(error="Username taken"), 409

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    u = data.get("username", "").strip()
    p = data.get("password", "")

    with get_db() as conn:
        # Select explicit columns to prevent errors
        user = conn.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (u,)).fetchone()
    
    if user and bcrypt.checkpw(p.encode(), user['password_hash'].encode()):
        token = jwt.encode({"u": user['username'], "id": user['id']}, SECRET_KEY, algorithm="HS256")
        return jsonify(token=token, username=u)
    
    return jsonify(error="Invalid credentials"), 401

# ───────── ROUTE: ANALYZE (ML + AI) ──────────
@app.route("/analyze", methods=["POST"])
def analyze():
    d = request.get_json(force=True)
    wpm = float(d.get("wpm", 0))
    acc = float(d.get("accuracy", 100))
    
    # 1. Random Forest Classification
    level = "Intermediate"
    if classifier:
        try:
            vec = np.array([[
                wpm,
                acc,
                int(d.get("error_count", 0)),
                int(d.get("raw_mistakes", 0)),
                int(d.get("backspace_count", 0))
            ]])
            prediction = classifier.predict(vec)[0]
            level = LABEL_MAP.get(int(prediction), "Intermediate")
        except Exception as e:
            print(f"ML Predict Error: {e}")

    # 2. Gemini AI Feedback
    typed = d.get("typed_text", "")
    target = d.get("target_text", "")
    feedback = generate_feedback(typed, target, wpm, acc)

    return jsonify({
        "level": level, 
        "wpm": wpm, 
        "accuracy": acc, 
        "feedback": feedback
    })

# ───────── ROUTE: SAVE SESSION ──────────
@app.route("/session", methods=["POST"])
def save_session():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded.get("id")
        
        if not user_id:
             with get_db() as conn:
                 u_row = conn.execute("SELECT id FROM users WHERE username = ?", (decoded.get("u"),)).fetchone()
                 if u_row: user_id = u_row['id']
        
        if not user_id: return jsonify(error="Invalid User"), 401

        d = request.json
        with get_db() as conn:
            conn.execute("""
                INSERT INTO history (user_id, wpm, accuracy, mistakes, level, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, 
                d.get('wpm', 0), 
                d.get('accuracy', 0), 
                d.get('raw_mistakes', 0), 
                d.get('level', "Unknown"), 
                datetime.datetime.utcnow().strftime("%Y-%m-%d")
            ))
        return jsonify(msg="Saved")
    except Exception as e:
        print(f"Save Session Error: {e}")
        return jsonify(error="Failed to save"), 401

# ───────── ROUTE: HISTORY ──────────
@app.route("/history", methods=["GET"])
def get_history():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded.get("id")
        
        if not user_id:
             with get_db() as conn:
                 u_row = conn.execute("SELECT id FROM users WHERE username = ?", (decoded.get("u"),)).fetchone()
                 if u_row: user_id = u_row['id']

        with get_db() as conn:
            rows = conn.execute("SELECT * FROM history WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
            return jsonify([dict(row) for row in rows])
    except:
        return jsonify(error="Unauthorized"), 401

if __name__ == "__main__":
    app.run(debug=True, port=5000)