import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# === Function to create realistic synthetic dataset ===
def generate_realistic_typing_data(n_per_class=400, seed=42):
    np.random.seed(seed)
    data = []

    # Beginner
    for _ in range(n_per_class):
        wpm = np.random.normal(loc=30, scale=5)              # ~20–40
        acc = np.random.normal(loc=60, scale=10)             # ~50–70
        err = np.random.randint(10, 25)
        raw = err + np.random.randint(1, 6)
        backs = err + np.random.randint(5, 20)
        data.append([wpm, acc, err, raw, backs, "Beginner"])

    # Intermediate
    for _ in range(n_per_class):
        wpm = np.random.normal(loc=55, scale=10)             # ~40–70
        acc = np.random.normal(loc=80, scale=5)              # ~75–90
        err = np.random.randint(5, 10)
        raw = err + np.random.randint(1, 4)
        backs = err + np.random.randint(2, 8)
        data.append([wpm, acc, err, raw, backs, "Intermediate"])

    # Advanced
    for _ in range(n_per_class):
        wpm = np.random.normal(loc=90, scale=10)             # ~75–110
        acc = np.random.normal(loc=96, scale=3)              # ~90–100
        err = np.random.randint(0, 3)
        raw = err + np.random.randint(0, 2)
        backs = err + np.random.randint(0, 4)
        data.append([wpm, acc, err, raw, backs, "Advanced"])

    # Edge cases
    for _ in range(100):
        # High WPM, low accuracy (likely bad typing): classify as Beginner
        wpm = np.random.normal(loc=110, scale=10)
        acc = np.random.normal(loc=20, scale=10)
        err = np.random.randint(20, 40)
        raw = err + np.random.randint(2, 6)
        backs = err + np.random.randint(5, 15)
        data.append([wpm, acc, err, raw, backs, "Beginner"])

        # Low WPM, high accuracy (precise but slow): classify as Intermediate
        wpm = np.random.normal(loc=40, scale=3)
        acc = np.random.normal(loc=95, scale=2)
        err = np.random.randint(0, 2)
        raw = err + np.random.randint(0, 2)
        backs = err + np.random.randint(1, 3)
        data.append([wpm, acc, err, raw, backs, "Intermediate"])

    return pd.DataFrame(data, columns=["WPM", "Accuracy", "Errors", "RawMistakes", "Backspaces", "Level"])

# === Generate + encode dataset ===
df = generate_realistic_typing_data()
df["Level"] = df["Level"].map({"Beginner": 0, "Intermediate": 1, "Advanced": 2})

X = df[["WPM", "Accuracy", "Errors", "RawMistakes", "Backspaces"]]
y = df["Level"]

# === Train/test split ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Hyperparameter-tuned Random Forest ===
best_params = {
    "n_estimators": 200,
    "max_depth": 12,
    "min_samples_split": 4,
    "min_samples_leaf": 2,
    "max_features": "sqrt",
    "random_state": 42
}

model = RandomForestClassifier(**best_params)
model.fit(X_train, y_train)

# === Evaluation ===
y_pred = model.predict(X_test)
print("\n✅ Classification Report:")
print(classification_report(y_test, y_pred, target_names=["Beginner", "Intermediate", "Advanced"]))

# === Confusion matrix ===
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Beginner", "Intermediate", "Advanced"], yticklabels=["Beginner", "Intermediate", "Advanced"])
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Confusion Matrix")
plt.tight_layout()
plt.show()

# === Save model ===
joblib.dump(model, "typing_model.pkl")
print("🧠 Model saved → typing_model.pkl")