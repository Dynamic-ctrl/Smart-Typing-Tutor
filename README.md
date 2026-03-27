# Quickeys: AI-Powered Typing Tutor

![Project Status](https://img.shields.io/badge/Status-Live-success) ![Tech Stack](https://img.shields.io/badge/Stack-FullStack-blue) ![AI Engine](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange)

**LIVE DEMO:** [https://quickeys-tutor-e7560b.netlify.app](https://quickeys-tutor-e7560b.netlify.app)

## About the Project
Quickeys is an intelligent typing assistant that uses a **Hybrid AI Architecture** to provide real-time coaching. Unlike standard typing tests, Quickeys analyzes *why* you made a mistake—whether it's speed, accuracy, or specific key patterns—and provides instant, personalized feedback using **Google's Gemini 1.5 Flash LLM**.

## Technical Architecture
This project uses a unique two-stage AI system:
1.  **Random Forest Classifier (Local ML):** Instantly classifies user skill level (Beginner/Int/Adv) based on keystroke dynamics (WPM, Error Rate, Backspace usage) using a pre-trained `scikit-learn` model.
2.  **Gemini 1.5 Flash (Cloud LLM):** A semantic analysis engine that reads the user's typed text to generate human-like, constructive feedback (e.g., *"You consistently miss capitalization on the left hand"*).

## Features
- **Real-time Analytics:** Tracks WPM, Accuracy, and Raw Mistakes instantly.
- **AI Feedback Engine:** Generates specific, actionable advice after every session.
- **Smart Progress Tracking:** Visualizes improvement over time with interactive charts.
- **Secure Authentication:** JWT-based login system with Bcrypt password hashing.
- **Persistent History:** SQLite database stores all past sessions.
- **Glassmorphism UI:** Modern, responsive interface built with vanilla CSS variables.

## Tech Stack
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js (Hosted on **Netlify**)(https://quickeys-tutor-e7560b.netlify.app)
- **Backend:** Python, Flask, Gunicorn (Hosted on **Render**) (https://smart-typing-tutor.onrender.com)
- **AI/ML:** Google Gemini API, Scikit-Learn, NumPy, Joblib
- **Database:** SQLite
- **Security:** JWT (JSON Web Tokens), Bcrypt, Dotenv

## Team Roles
- **Aditi Mehta** – Backend Development and AI/ML Implementation
- **Nandana v.** – UI/UX Design and Frontend Development  

## How to Run Locally

### 1. Clone the Repo
```bash
git clone [https://github.com/Dynamic-ctrl/Smart-Typing-Tutor.git](https://github.com/Dynamic-ctrl/Smart-Typing-Tutor.git)
cd Smart-Typing-Tutor


