import pandas as pd
import joblib
import pickle

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load balanced dataset
df = pd.read_csv("dataset/balanced_bot_iot.csv")

print("Dataset Loaded!")
print(df.shape)

# Deployed production model = Model C (ablation-study winner).
# Model C uses ONLY behavioral / statistical flow features. It deliberately
# excludes:
#   pkSeqID                 -> row / capture identifier
#   category, subcategory   -> TARGET LEAKAGE (they encode the label directly)
#   seq                     -> capture-order / temporal proxy that leaks the label
#   saddr, daddr            -> host-identity leakage (IP addresses)
#   sport, dport            -> environment-specific port identifiers
# Removing the identifiers is what lets the model generalize to unseen hosts.
MODEL_C_FEATURES = [
    "proto",
    "stddev",
    "N_IN_Conn_P_SrcIP",
    "min",
    "state_number",
    "mean",
    "N_IN_Conn_P_DstIP",
    "drate",
    "srate",
    "max",
]

# Features / Target
X = df[MODEL_C_FEATURES].copy()
y = df["attack"]

# Encode categorical columns with LabelEncoder.
# NOTE: this matches the inference contract in app.py
# (model.pkl + encoders.pkl + feature_columns.pkl), so the retrained
# model can be served without any change to app.py's behaviour.
categorical_cols = X.select_dtypes(include=["object", "string"]).columns

encoders = {}

for col in categorical_cols:
    encoder = LabelEncoder()
    X[col] = encoder.fit_transform(X[col].astype(str))
    encoders[col] = encoder

# Column order the model is trained on (consumed by app.py)
feature_columns = list(X.columns)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Train
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# Predict
pred = model.predict(X_test)

print("\nAccuracy")

print(accuracy_score(y_test, pred))

print("\n")

print(classification_report(y_test, pred))

# Save the artifacts consumed by app.py
joblib.dump(model, "model.pkl")

joblib.dump(feature_columns, "feature_columns.pkl")

with open("encoders.pkl", "wb") as f:
    pickle.dump(encoders, f)

print("\nModel, encoders, and feature_columns saved successfully!")
print("Features used:", feature_columns)
