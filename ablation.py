"""
Ablation study — progressive feature removal.
Standalone: does NOT read/write model.pkl, encoders.pkl, feature_columns.pkl,
or touch the Flask app. Trains + evaluates in memory only.
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)

df = pd.read_csv("dataset/balanced_bot_iot.csv")

# Always excluded: identifier + target-leakage columns already removed from the app model
GLOBAL_DROP = ["pkSeqID", "attack", "category", "subcategory", "seq"]

y = df["attack"]

# Model A: leak-free baseline (current app model's 14 features)
A = [c for c in df.columns if c not in GLOBAL_DROP]
# Model B: A minus source/destination address
B = [c for c in A if c not in ("saddr", "daddr")]
# Model C: B minus source/destination port
C = [c for c in B if c not in ("sport", "dport")]
# Model D: C minus connection-count features
D = [c for c in C if c not in ("N_IN_Conn_P_SrcIP", "N_IN_Conn_P_DstIP")]

MODELS = {"A": A, "B": B, "C": C, "D": D}
DESC = {
    "A": "leak-free baseline (14 feats)",
    "B": "A - saddr, daddr",
    "C": "B - sport, dport",
    "D": "C - conn-count feats",
}

def evaluate(features):
    X = df[features].copy()
    # LabelEncode any categorical columns present in this subset
    for col in X.select_dtypes(include=["object", "string"]).columns:
        X[col] = LabelEncoder().fit_transform(X[col].astype(str))
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_tr, y_tr)
    pred = clf.predict(X_te)
    proba = clf.predict_proba(X_te)[:, 1]
    return {
        "Accuracy":  accuracy_score(y_te, pred),
        "Precision": precision_score(y_te, pred),
        "Recall":    recall_score(y_te, pred),
        "F1":        f1_score(y_te, pred),
        "ROC-AUC":   roc_auc_score(y_te, proba),
        "n_feat":    len(features),
    }

rows = []
for name, feats in MODELS.items():
    m = evaluate(feats)
    rows.append((name, DESC[name], m))

# Print table
hdr = f"{'Model':<6}{'Description':<32}{'#Feat':<7}{'Accuracy':<10}{'Precision':<11}{'Recall':<9}{'F1':<9}{'ROC-AUC':<9}"
print(hdr)
print("-" * len(hdr))
for name, desc, m in rows:
    print(f"{name:<6}{desc:<32}{m['n_feat']:<7}"
          f"{m['Accuracy']:<10.4f}{m['Precision']:<11.4f}{m['Recall']:<9.4f}"
          f"{m['F1']:<9.4f}{m['ROC-AUC']:<9.4f}")

print("\nFeature sets:")
for name, feats in MODELS.items():
    print(f"  Model {name} ({len(feats)}): {feats}")
