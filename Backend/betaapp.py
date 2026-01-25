# app.py  – minimal backend that matches the JS
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt, jwt, re, numpy as np, joblib, torch

from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline

# ───────────────────────── CONFIG ────────────────────────────
SECRET_KEY  = "super-secret"                 # change for prod
CLF_PATH    = Path("typing_model.pkl")
GPT2_DIR    = Path("typing_feedback_final_model")
MAX_TOKENS  = 120

# ───────────────────────── APP / CORS ────────────────────────
app = Flask(__name__)
CORS(
    app,
    origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
)

# ───────────────────────── MODELS ────────────────────────────
if not CLF_PATH.exists():
    raise FileNotFoundError(f"Classifier not found → {CLF_PATH.resolve()}")
classifier = joblib.load(CLF_PATH)
label_map: Dict[int, str] = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}

if not GPT2_DIR.exists():
    raise FileNotFoundError(f"GPT-2 directory missing → {GPT2_DIR.resolve()}")
tok  = GPT2Tokenizer.from_pretrained(GPT2_DIR)
gpt2 = GPT2LMHeadModel.from_pretrained(GPT2_DIR)
device_idx = 0 if torch.cuda.is_available() else -1
gen = pipeline(
    "text-generation",
    model=gpt2,
    tokenizer=tok,
    device=device_idx,
    max_new_tokens=MAX_TOKENS,
    do_sample=False,
    pad_token_id=tok.eos_token_id,
)

# ──────────────────────── IN-MEM “DB” ────────────────────────
users:   Dict[str, str]        = {}           # username → hashed pw
history: Dict[str, List[dict]] = {}           # username → [sessions]

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_pw(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def make_token(user: str) -> str:
    return jwt.encode({"u": user}, SECRET_KEY, algorithm="HS256")

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])["u"]
    except Exception:
        return None

# ──────────────────── FEEDBACK GENERATION ────────────────────
def build_feedback(level: str, original: str, typed: str) -> str:
    prompt = (
        f"Skill Level: {level}\n"
        f"Original Text: {original}\n"
        f"Typed Text: {typed}\n"
        "Give concise, actionable feedback in bullet points.\n"
        "Feedback:"
    )
    body = gen(prompt)[0]["generated_text"].split("Feedback:", 1)[-1]

    bullets, seen = [], set()
    for raw in body.splitlines():
        line = re.sub(r"^[\s💡\-•>]*", "", raw).strip()
        if not line or line.lower() in seen:
            continue
        seen.add(line.lower())

        icon = "🧠"
        l = line.lower()
        if "capital" in l: icon = "🔤"
        elif "space" in l or "spacing" in l: icon = "📏"
        elif any(k in l for k in ("comma", "period", "apostrophe", "punctuation", "hyphen")):
            icon = "❌"

        bullets.append(f"{icon} {line}")
        if len(bullets) == 6:
            break

    return "\n".join(bullets) or "🧠 Great job! Keep practising."

# ────────────────────────── AUTH ROUTES ───────────────────────
@app.post("/auth/register")
def register():
    data = request.get_json()
    u, p = data.get("username", "").strip(), data.get("password", "")
    if not u or not p:
        return jsonify(error="username & password required"), 400
    if u in users:
        return jsonify(error="username taken"), 409

    users[u] = hash_pw(p)
    history[u] = []
    return jsonify(msg="registered")

@app.post("/auth/login")
def login():
    data = request.get_json()
    u, p = data.get("username", "").strip(), data.get("password", "")
    if u not in users or not check_pw(p, users[u]):
        return jsonify(error="bad credentials"), 401

    # ensure history list exists
    history.setdefault(u, [])
    return jsonify(token=make_token(u), username=u)

# ───────────────────────── ANALYZE ───────────────────────────
@app.post("/analyze")
def analyze():
    d = request.get_json(force=True)
    vec = np.array([[
        float(d.get("wpm", 0)),
        float(d.get("accuracy", 100)),
        int  (d.get("error_count", 0)),
        int  (d.get("raw_mistakes", 0)),
        int  (d.get("backspace_count", 0)),
    ]])

    typed  = d.get("typed_text", "")
    target = d.get("target_text", "")
    idx    = int(classifier.predict(vec)[0])
    level  = label_map[idx]
    conf   = round(classifier.predict_proba(vec)[0][idx] * 100, 2)

    return jsonify(
        level      = level,
        confidence = f"{conf}%",
        feedback   = build_feedback(level, target, typed)
    )

# ─────────────────────── SAVE SESSION ───────────────────────
@app.post("/session")
def save_session():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user  = decode_token(token)
    if not user:
        return jsonify(error="bad token"), 401

    d = request.get_json()
    history.setdefault(user, []).append({
        "date":     datetime.utcnow().strftime("%Y-%m-%d"),
        "wpm":      float(d.get("wpm", 0)),
        "accuracy": float(d.get("accuracy", 0)),
        "level":    d.get("level", "Unknown"),
        "errors":   int(d.get("raw_mistakes", 0)),
    })
    return jsonify(msg="saved")

# ─────────────────────── HISTORY ROUTE ──────────────────────
@app.get("/history")
def get_history():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user  = decode_token(token)
    if not user:
        return jsonify(error="bad token"), 401
    return jsonify(history.get(user, []))

# ─────────────────────────── RUN ─────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)