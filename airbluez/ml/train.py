import os

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier


def train_gesture_model(hand: str):
    csv_path = f"data/gestures/{hand}.csv"
    model_dir = "airbluez/ml/models"
    os.makedirs(model_dir, exist_ok=True)

    if not os.path.exists(csv_path):
        print(f"Error: Data file {csv_path} not found. Capture data first!")
        return

    df = pd.read_csv(csv_path)
    X = df.drop("label", axis=1)  # Features
    y = df["label"]  # Target labels

    # split data (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\n---------Training {hand.capitalize()} Hand Model -----------")

    # define and train mlp
    # (64, 32) hidden layers as per IMPLEMENTATION_PLAN.md
    clf = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        max_iter=1000,
        activation="relu",
        solver="adam",
        random_state=42,
    )

    clf.fit(X_train.values, y_train)

    # Evaluation
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Validation Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 5. Save Model
    model_path = f"{model_dir}/{hand}_gesture.joblib"
    joblib.dump(clf, model_path)
    print(f"Model saved to {model_path}")


if __name__ == "__main__":
    train_gesture_model("left")
    train_gesture_model("right")
