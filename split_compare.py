"""
Split comparison — random split vs group-aware split (grouped by source host `saddr`).
Standalone: does NOT touch the Flask app or its served artifacts.
Everything except the split is identical to ablation.py.
"""
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)
warnings.filterwarnings("ignore")

df = pd.read_csv("dataset/balanced_bot_iot.csv")
GLOBAL_DROP = ["pkSeqID", "attack", "category", "subcategory", "seq"]
y = df["attack"]
groups = df["saddr"]            # grouping key (host); used even when saddr is not a feature

A = [c for c in df.columns if c not in GLOBAL_DROP]
B = [c for c in A if c not in ("saddr", "daddr")]
C = [c for c in B if c not in ("sport", "dport")]
D = [c for c in C if c not in ("N_IN_Conn_P_SrcIP", "N_IN_Conn_P_DstIP")]
MODELS = {"A": A, "B": B, "C": C, "D": D}


def encode(features):
    X = df[features].copy()
    for col in X.select_dtypes(include=["object", "string"]).columns:
        X[col] = LabelEncoder().fit_transform(X[col].astype(str))
    return X


def metrics(y_te, pred, proba):
    single_class = len(np.unique(y_te)) < 2
    return {
        "Accuracy":  accuracy_score(y_te, pred),
        "Precision": precision_score(y_te, pred, zero_division=0),
        "Recall":    recall_score(y_te, pred, zero_division=0),
        "F1":        f1_score(y_te, pred, zero_division=0),
        "ROC-AUC":   (float("nan") if single_class else roc_auc_score(y_te, proba)),
    }


def run(features, split):
    X = encode(features)
    if split == "random":
        idx = np.arange(len(X))
        tr, te = train_test_split(idx, test_size=0.2, random_state=42)
    else:  # group-aware by saddr
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        tr, te = next(gss.split(X, y, groups))
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X.iloc[tr], y.iloc[tr])
    pred = clf.predict(X.iloc[te])
    proba = clf.predict_proba(X.iloc[te])[:, 1]
    m = metrics(y.iloc[te], pred, proba)
    m["_test_pos"] = int(y.iloc[te].sum())
    m["_test_n"] = len(te)
    return m


for split in ["random", "group"]:
    print(f"\n=== {split.upper()} SPLIT ===")
    hdr = f"{'Model':<6}{'Acc':<9}{'Prec':<9}{'Rec':<9}{'F1':<9}{'ROC-AUC':<10}{'test(pos/n)':<12}"
    print(hdr); print("-" * len(hdr))
    for name, feats in MODELS.items():
        m = run(feats, split)
        auc = "nan" if m["ROC-AUC"] != m["ROC-AUC"] else f"{m['ROC-AUC']:.4f}"
        print(f"{name:<6}{m['Accuracy']:<9.4f}{m['Precision']:<9.4f}{m['Recall']:<9.4f}"
              f"{m['F1']:<9.4f}{auc:<10}{str(m['_test_pos'])+'/'+str(m['_test_n']):<12}")

# Report the group split composition once
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
tr, te = next(gss.split(df, y, groups))
print("\nGroup split composition:")
print("  train hosts:", sorted(df.iloc[tr]['saddr'].unique()))
print("  test  hosts:", sorted(df.iloc[te]['saddr'].unique()))
print(f"  train size={len(tr)} (attack rate {y.iloc[tr].mean():.2f}), "
      f"test size={len(te)} (attack rate {y.iloc[te].mean():.2f})")
