
# Valcore — IoT Botnet Detection System

## Table of Contents

- Features
- Dataset Used
- Model C Feature Set
- Installation
- Running the Project
- Training
- Evaluation
- Limitations
- Future Work

---


<p align="center">
  <img src="static/banner2.png" alt="Valcore Logo" width="180">
</p>

<h1 align="center">Valcore</h1>

<p align="center">
Leakage-aware IoT Botnet Detection using Random Forest
</p>

Valcore is a machine-learning system that classifies IoT network traffic as **botnet attack** or **normal**. It pairs a trained Random Forest classifier with a Flask web dashboard: you upload a CSV of network-flow records and receive a per-file threat assessment (attack vs. normal packet counts, model confidence, threat level, and a security recommendation).

The deployed model is **Model C**, the winner of an ablation study that removed host- and port-identifier features so the classifier generalizes to hosts it has never seen, rather than memorizing IP addresses.

---

## Features

- **Binary threat detection** — Random Forest classifier labels each flow record as attack (`1`) or normal (`0`).
- **Web dashboard** — upload a CSV and get a rendered report: packets scanned, attack/normal counts, model confidence, threat level (LOW / MEDIUM / HIGH), and a recommendation.
- **Traffic distribution chart** — doughnut chart (Chart.js) of attack vs. normal packets.
- **Robust inference contract** — uploads are reindexed to exactly the Model C feature set, so extra columns (e.g. `saddr`, `daddr`, `sport`, `dport`) present in a raw capture are ignored automatically.
- **Leakage-aware design** — identifier and target-leakage columns are excluded from the model by construction (see below).
- **Reproducible pipeline** — standalone scripts for dataset preparation, training, ablation, and split comparison.

---

## Dataset used

- **Source:** UNSW **Bot-IoT** dataset — `UNSW_2018_IoT_Botnet_Final_10_Best.csv` (the "10-best-features" release), a semicolon-delimited CSV of labeled IoT network flows.
- **Balancing:** `prepare_dataset.py` streams the raw file in chunks, separates normal from attack traffic, downsamples the majority class to a **1:1 balance**, shuffles (`random_state=42`), and writes `dataset/balanced_bot_iot.csv` (~954 rows).

The balanced CSV (`dataset/balanced_bot_iot.csv`) is what all downstream scripts read. The raw 517 MB source file is **not** shipped with the repository — see [Limitations](#limitations) for reproducibility implications.

### Columns excluded from every model

| Column(s) | Reason for exclusion |
|-----------|----------------------|
| `pkSeqID` | Row / capture identifier |
| `category`, `subcategory` | **Target leakage** — they encode the label directly |
| `seq` | Capture-order / temporal proxy that leaks the label |
| `saddr`, `daddr` | **Host-identity leakage** — IP addresses; memorizing them does not generalize |
| `sport`, `dport` | Environment-specific port identifiers |

---

## Model C feature set

Model C uses **10 behavioral / statistical flow features only** — no host or port identifiers. Removing the identifiers is what lets the model generalize to unseen hosts.

| # | Feature | Description |
|---|---------|-------------|
| 1 | `proto` | Transport/application protocol (categorical, label-encoded) |
| 2 | `stddev` | Std. deviation of aggregated record duration |
| 3 | `N_IN_Conn_P_SrcIP` | Inbound connections per source IP |
| 4 | `min` | Minimum duration of aggregated records |
| 5 | `state_number` | Numerical encoding of connection state |
| 6 | `mean` | Mean duration of aggregated records |
| 7 | `N_IN_Conn_P_DstIP` | Inbound connections per destination IP |
| 8 | `drate` | Destination-to-source packets-per-second rate |
| 9 | `srate` | Source-to-destination packets-per-second rate |
| 10 | `max` | Maximum duration of aggregated records |

`proto` is the only categorical feature and is encoded with a `LabelEncoder`; the fitted encoder is persisted in `encoders.pkl`.

### Why Model C

An ablation study (`ablation.py`) progressively removed feature groups (A → B → C → D), and `split_compare.py` evaluated each under both a random split and a **host-grouped split** (train/test split by source host, so the test hosts are unseen during training). Model C matches the best leak-free model on the honest grouped split while relying solely on behavioral features:

| Model | Features | Grouped-split Acc | Grouped-split F1 |
|-------|:--------:|:-----------------:|:----------------:|
| A (baseline, incl. IPs) | 14 | 0.9953 | 0.9962 |
| B (− saddr, daddr) | 12 | 0.9906 | 0.9923 |
| **C (− sport, dport)** | **10** | **0.9906** | **0.9923** |
| D (− conn-count feats) | 8 | 0.9671 | 0.9725 |

Model C keeps B's generalization with fewer, purely behavioral features, and avoids A's reliance on IP identifiers; D over-prunes and loses recall.

---

## Installation

Requires **Python 3.11+**.

```bash
# 1. Clone the repository, then create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

Pinned dependencies (`requirements.txt`):

```
flask==3.1.3
pandas==3.0.3
scikit-learn==1.9.0
joblib==1.5.3
numpy==2.4.6
```

> **Note:** `model.pkl` and `encoders.pkl` were pickled with **scikit-learn 1.9.0** and **joblib 1.5.3**. Loading them under a different scikit-learn version may warn or fail — install the pinned versions.

---

## Running the project

The repository ships with pre-trained artifacts (`model.pkl`, `encoders.pkl`, `feature_columns.pkl`), so you can run the app directly:

```bash
python app.py
```

Then open <http://127.0.0.1:5000> and upload a CSV of flow records.

**Input format:** the app reads uploads as **comma-delimited** CSVs. A file must contain the 10 Model C columns (extra columns are ignored). Note that the raw Bot-IoT export is *semicolon*-delimited and must be converted before upload.

Artifacts consumed by `app.py`:

| File | Purpose |
|------|---------|
| `model.pkl` | Trained Random Forest (Model C, 10 features) |
| `encoders.pkl` | Fitted `LabelEncoder`s (only `proto`) |
| `feature_columns.pkl` | Exact feature order the model expects |

---

## Training

To regenerate the model from the balanced dataset:

```bash
python train_model.py
```

This script:

1. Loads `dataset/balanced_bot_iot.csv`.
2. Selects the **Model C** feature set (`MODEL_C_FEATURES`).
3. Label-encodes `proto`.
4. Trains a `RandomForestClassifier(n_estimators=100, random_state=42)` on an 80/20 split.
5. Prints accuracy and a classification report.
6. Saves `model.pkl`, `encoders.pkl`, and `feature_columns.pkl`.

To rebuild the balanced dataset from the raw source (requires the 517 MB raw CSV in `dataset/`):

```bash
python prepare_dataset.py
```

---

## Evaluation

Two standalone scripts reproduce the study. Neither touches the served artifacts — they train and evaluate in memory only.

**Ablation study** (progressive feature removal, random split):

```bash
python ablation.py
```

**Split comparison** (random split vs. host-grouped split — the honest generalization test):

```bash
python split_compare.py
```

### Deployed Model C metrics

| Evaluation | Accuracy | Precision | Recall | F1 | ROC-AUC |
|------------|:--------:|:---------:|:------:|:----:|:-------:|
| Random 80/20 split | 0.9948 | 1.0000 | 0.9880 | 0.9939 | 1.0000 |
| **Host-grouped split (unseen hosts)** | **0.9906** | **0.9923** | **0.9923** | **0.9923** | **0.9996** |

The **host-grouped split is the meaningful number**: it evaluates on 5 hosts never seen in training. The random-split figure is inflated by flow-level near-duplicates shared across train and test (see below).

---

## Limitations

- **Random-split metrics are optimistic.** Bot-IoT flow records from the same host/attack burst are near-duplicates, so a random train/test split leaks near-identical rows across both sides. Treat the **host-grouped** results as the honest estimate; the random-split numbers overstate generalization.
- **Small, artificially balanced evaluation set.** The balanced dataset is ~954 rows, and the grouped test set contains only **5 hosts / 213 rows**. Results come from a single `random_state=42` split with no cross-validation or confidence intervals, so point estimates are fragile.
- **Balanced test set ≠ real-world prevalence.** Bot-IoT is heavily attack-dominated. Because the model is evaluated on a 1:1-balanced holdout, the reported accuracy and especially **precision will not transfer directly** to a deployment with realistic (skewed) traffic prevalence.
- **Raw dataset not reproducible from this repo alone.** The 517 MB raw source CSV is not distributed here, and its provenance is not scripted end-to-end. Downstream training/evaluation are reproducible from the committed `balanced_bot_iot.csv`, but the balancing step itself cannot be re-derived without the raw file.
- **Input handling is strict and quiet.** Uploads must be comma-delimited and contain the 10 Model C columns. A wrong delimiter, a missing required column, or an empty file yields a generic error page rather than a specific validation message.
- **Not a production IDS.** This is a research/demo artifact — no streaming/live-capture ingestion, authentication, rate limiting, or model-monitoring. Do not deploy as a security control without further hardening.
