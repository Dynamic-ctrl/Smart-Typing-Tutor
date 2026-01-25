# ⚡ Quickeys: AI-Powered Typing Tutor

![Project Status](https://img.shields.io/badge/Status-Live-success) ![Tech Stack](https://img.shields.io/badge/Stack-FullStack-blue)

Quickeys is an intelligent typing assistant that uses a **Hybrid AI Architecture** to provide real-time coaching. Unlike standard typing tests, Quickeys analyzes *why* you made a mistake—whether it's speed, accuracy, or specific key patterns—and provides instant, personalized feedback using Google's Gemini LLM.

## 🚀 Live Demo
- **Frontend:** [Link to your Netlify/Vercel site here]
- **Backend:** [Link to your Render API here]

## 🧠 Technical Architecture
This project uses a unique two-stage AI system:
1.  **Random Forest Classifier (Local ML):** Instantly classifies user skill level (Beginner/Int/Adv) based on keystroke dynamics (WPM, Error Rate, Backspace usage) using a pre-trained `scikit-learn` model.
2.  **Gemini 1.5 Flash (Cloud LLM):** A semantic analysis engine that reads the user's typed text to generate human-like, constructive feedback (e.g., *"You consistently miss capitalization on the left hand"*).

## ✨ Features
- **Real-time Analytics:** Tracks WPM, Accuracy, and Raw Mistakes instantly.
- **AI Feedback Engine:** Generates specific, actionable advice after every session.
- **Smart Progress Tracking:** Visualizes improvement over time with Chart.js.
- **Secure Authentication:** JWT-based login system with Bcrypt password hashing.
- **Persistent History:** SQLite database stores all past sessions.
- **Glassmorphism UI:** Modern, responsive interface built with vanilla CSS variables.

## 🛠️ Tech Stack
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Chart.js
- **Backend:** Python, Flask, Gunicorn
- **AI/ML:** Google Gemini API, Scikit-Learn, NumPy, Joblib
- **Database:** SQLite
- **Deployment:** Render (Backend), Netlify (Frontend)

## ⚡ How to Run Locally

### 1. Clone the Repo
```bash
git clone [https://github.com/YOUR_USERNAME/quickeys.git](https://github.com/YOUR_USERNAME/quickeys.git)
cd quickeys
