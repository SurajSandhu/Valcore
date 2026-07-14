"""
Generate all publication-quality figures for the Valcore IEEE paper.

Figures:
  fig1_architecture.{pdf,png}      - System architecture (deployment view)
  fig2_ml_pipeline.{pdf,png}       - Machine-learning pipeline (model build)
  fig3_data_flow.{pdf,png}         - Data flow diagram (runtime inference, DFD)
  fig4_confusion_matrix.{pdf,png}  - Model C confusion matrix (host-grouped test)
  fig5_feature_importance.{pdf,png}- Model C Random Forest feature importances

Figures 4 and 5 are computed from the repository's actual artifacts / data,
so they faithfully reflect the deployed Model C.
"""
import os
import numpy as np
import pandas as pd
import joblib
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.colors import LinearSegmentedColormap
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- style
mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "savefig.dpi": 300,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.06,
    "pdf.fonttype": 42,   # embed TrueType (IEEE: no Type-3 fonts)
    "ps.fonttype": 42,
})

# Validated palette (dataviz skill reference instance)
INK      = "#0b0b0b"   # primary text
INK2     = "#52514e"   # secondary text
MUTED    = "#898781"   # axes / muted
GRID     = "#e1e0d9"   # hairline grid
BLUE     = "#2a78d6"
# Light tints (dark text -> high contrast, prints in grayscale)
T_PROC   = ("#eaf2fc", BLUE)        # processes / app blocks
T_DATA   = ("#fbf1d8", "#eda100")   # data files / stores
T_MODEL  = ("#ebe9f6", "#4a3aa7")   # ML / model core
T_OUT    = ("#e4f6ef", "#1baf7a")   # output / UI
T_ENT    = ("#f0efec", "#898781")   # external entity / user

BLUE_RAMP = LinearSegmentedColormap.from_list(
    "blueramp",
    ["#ffffff", "#cde2fb", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"],
)


def box(ax, x, y, w, h, text, tint, fs=8.5, bold=False, rounding=0.05, lw=1.3):
    fc, ec = tint
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.008,rounding_size={rounding}",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=3,
    )
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=INK, zorder=4,
            fontweight=("bold" if bold else "normal"))


def sq(ax, x, y, w, h, text, tint, fs=8.5, bold=False, lw=1.3):
    """Sharp-cornered rectangle (external entity / data store)."""
    fc, ec = tint
    ax.add_patch(Rectangle((x, y), w, h, linewidth=lw, edgecolor=ec,
                           facecolor=fc, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=INK, zorder=4,
            fontweight=("bold" if bold else "normal"))


def arrow(ax, p1, p2, color=INK2, lw=1.3, ls="-", rad=0.0):
    a = FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=11, color=color,
        lw=lw, linestyle=ls, shrinkA=3, shrinkB=3, zorder=2,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(a)


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"))
    plt.close(fig)
    print("wrote", name)


# ============================================================ Fig 1
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.1, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.2); ax.axis("off")

    def band(y, h, label):
        ax.add_patch(Rectangle((0.15, y), 9.7, h, facecolor="#f9f9f7",
                               edgecolor=GRID, lw=1.0, zorder=0))
        ax.text(0.32, y + h - 0.02, label, ha="left", va="top",
                fontsize=7.5, color=MUTED, style="italic", zorder=1)

    band(5.85, 1.25, "Client layer")
    band(3.30, 2.35, "Application layer  (Flask · app.py)")
    band(1.75, 1.35, "Model artifacts  (loaded at startup)")
    band(0.20, 1.35, "Presentation")

    # Client
    box(ax, 3.4, 6.15, 3.2, 0.75,
        "Web Browser\nupload CSV  ·  view dashboard", T_ENT, fs=8.5)

    # Application inner blocks
    blocks = ["Upload\nValidation", "Preprocess\n& Encode",
              "Random Forest\nInference", "Threat\nAssessment",
              "Template\nRendering"]
    bx, bw, gap = 0.55, 1.72, 0.13
    for i, b in enumerate(blocks):
        x = bx + i * (bw + gap)
        box(ax, x, 3.75, bw, 1.15, b, T_PROC, fs=8)
        if i < len(blocks) - 1:
            arrow(ax, (x + bw, 4.32), (x + bw + gap, 4.32), color=BLUE, lw=1.4)

    # Artifacts
    arts = ["model.pkl", "encoders.pkl", "feature_columns.pkl"]
    for i, a in enumerate(arts):
        x = 1.2 + i * 2.9
        sq(ax, x, 2.05, 2.35, 0.75, a, T_DATA, fs=8.5)

    # Presentation
    outs = ["templates/index.html", "static/script.js (Chart.js)", "static/style.css"]
    for i, o in enumerate(outs):
        x = 1.2 + i * 2.9
        box(ax, x, 0.50, 2.35, 0.75, o, T_OUT, fs=7.8)

    # Flows
    arrow(ax, (5.0, 6.15), (4.6, 4.90), color=INK2, lw=1.4)          # browser -> app
    ax.text(4.35, 5.55, "HTTP POST\n/predict", fontsize=7, color=INK2, ha="right")
    arrow(ax, (5.9, 4.90), (5.6, 6.15), color="#1baf7a", lw=1.4)     # app -> browser
    ax.text(6.05, 5.55, "rendered\nreport", fontsize=7, color="#158a63", ha="left")

    arrow(ax, (4.3, 2.80), (4.3, 3.75), color="#c98500", lw=1.3)     # artifacts -> app
    arrow(ax, (8.9, 3.75), (8.9, 1.25), color="#158a63", lw=1.3, ls=(0, (4, 3)))
    ax.text(9.0, 2.5, "renders", fontsize=6.8, color=MUTED, ha="left", rotation=90, va="center")

    # Offline training note
    ax.add_patch(FancyBboxPatch((0.55, 2.02), 3.6, 0.0, boxstyle="round,pad=0",
                                fc="none", ec="none"))
    ax.text(9.6, 2.15, "offline\ntraining\nproduces\nartifacts", fontsize=6.6,
            color=MUTED, ha="right", va="center", style="italic")

    ax.set_title("Valcore System Architecture", fontsize=11, color=INK,
                 fontweight="bold", pad=6)
    save(fig, "fig1_architecture")


# ============================================================ Fig 2
def fig_ml_pipeline():
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    ax.set_xlim(0, 12.4); ax.set_ylim(0, 3.2); ax.axis("off")

    stages = [
        ("1. Raw Data",       "UNSW Bot-IoT\n10-best CSV\n(semicolon)",        T_DATA),
        ("2. Preprocess",     "prepare_dataset.py\nchunked read\n1:1 balance · shuffle", T_PROC),
        ("3. Feature Select", "Model C: 10\nbehavioral feats\ndrop IDs + leakage", T_MODEL),
        ("4. Encode & Split", "label-encode proto\n80/20 split\nseed = 42",     T_PROC),
        ("5. Train",          "Random Forest\n100 trees\nseed = 42",           T_MODEL),
        ("6. Persist & Eval", "model/encoders/\nfeature_columns\nrandom + grouped", T_OUT),
    ]
    n = len(stages); bw, h = 1.72, 1.55; gap = (12.4 - 0.3 - n * bw) / (n - 1)
    y = 0.95
    for i, (title, detail, tint) in enumerate(stages):
        x = 0.15 + i * (bw + gap)
        box(ax, x, y, bw, h, "", tint, rounding=0.06)
        ax.text(x + bw / 2, y + h - 0.22, title, ha="center", va="center",
                fontsize=8.2, fontweight="bold", color=INK)
        ax.text(x + bw / 2, y + h / 2 - 0.28, detail, ha="center", va="center",
                fontsize=6.9, color=INK2)
        if i < n - 1:
            arrow(ax, (x + bw, y + h / 2), (x + bw + gap, y + h / 2),
                  color=BLUE, lw=1.5)

    ax.set_title("Machine-Learning Pipeline", fontsize=11, color=INK,
                 fontweight="bold", pad=4)
    save(fig, "fig2_ml_pipeline")


# ============================================================ Fig 3
def fig_data_flow():
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.4); ax.axis("off")

    # External entity
    sq(ax, 0.3, 2.7, 1.9, 1.0, "User", T_ENT, fs=9.5, bold=True)

    # Processes (rounded)
    procs = [
        (3.0,  4.4, "1\nValidate\nUpload"),
        (5.3,  4.4, "2\nPreprocess\n& Encode"),
        (7.6,  4.4, "3\nClassify\n(RF)"),
        (9.9,  4.4, "4\nAssess\nThreat"),
    ]
    pw, ph = 1.8, 1.5
    for x, y, t in procs:
        box(ax, x, y, pw, ph, t, T_PROC, fs=8, rounding=0.12)

    # Data store (open-ended: draw two horizontal lines + label)
    sq(ax, 5.3, 0.55, 4.6, 0.95, "D1   Model Artifacts   (model.pkl · encoders.pkl · feature_columns.pkl)",
       T_DATA, fs=7.6)

    # Flows entity <-> pipeline
    arrow(ax, (2.2, 3.3), (3.0, 4.7), color=INK2, lw=1.4)
    ax.text(2.35, 4.15, "CSV\nupload", fontsize=7, color=INK2, ha="left")

    chain_lbl = ["validated\nrows", "feature\nvectors", "predictions"]
    for i in range(3):
        x0 = procs[i][0] + pw
        x1 = procs[i + 1][0]
        arrow(ax, (x0, 5.15), (x1, 5.15), color=BLUE, lw=1.4)
        ax.text((x0 + x1) / 2, 5.55, chain_lbl[i], fontsize=6.8, color=INK2,
                ha="center", va="center")

    # process 4 -> user (threat report)
    arrow(ax, (9.9, 4.7), (2.2, 3.15), color="#158a63", lw=1.4, rad=0.28)
    ax.text(6.0, 3.05, "threat report  (counts · confidence · level · recommendation)",
            fontsize=7, color="#158a63", ha="center")

    # data store -> processes 2 and 3
    arrow(ax, (6.2, 1.5), (6.2, 4.4), color="#c98500", lw=1.2, ls=(0, (4, 3)))
    ax.text(6.32, 3.0, "encoders,\nfeature order", fontsize=6.6, color="#a06b00",
            ha="left", va="center")
    arrow(ax, (8.5, 1.5), (8.5, 4.4), color="#c98500", lw=1.2, ls=(0, (4, 3)))
    ax.text(8.62, 3.0, "trained\nmodel", fontsize=6.6, color="#a06b00",
            ha="left", va="center")

    # legend
    lx, ly = 0.3, 0.5
    sq(ax, lx, ly, 0.5, 0.35, "", T_ENT, lw=1.1)
    ax.text(lx + 0.62, ly + 0.17, "external entity", fontsize=6.8, color=INK2, va="center")
    box(ax, lx + 2.0, ly, 0.5, 0.35, "", T_PROC, lw=1.1, rounding=0.12)
    ax.text(lx + 2.62, ly + 0.17, "process", fontsize=6.8, color=INK2, va="center")
    sq(ax, lx + 3.5, ly, 0.5, 0.35, "", T_DATA, lw=1.1)
    ax.text(lx + 4.12, ly + 0.17, "data store", fontsize=6.8, color=INK2, va="center")

    ax.set_title("Data Flow Diagram — Inference Path", fontsize=11, color=INK,
                 fontweight="bold", pad=4)
    save(fig, "fig3_data_flow")


# ============================================================ real data
def compute_model_c():
    df = pd.read_csv(os.path.join(ROOT, "dataset", "balanced_bot_iot.csv"))
    C = ["proto", "stddev", "N_IN_Conn_P_SrcIP", "min", "state_number",
         "mean", "N_IN_Conn_P_DstIP", "drate", "srate", "max"]
    y = df["attack"]; groups = df["saddr"]
    X = df[C].copy()
    for col in X.select_dtypes(include=["object", "string"]).columns:
        X[col] = LabelEncoder().fit_transform(X[col].astype(str))
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr, te = next(gss.split(X, y, groups))
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X.iloc[tr], y.iloc[tr])
    cm = confusion_matrix(y.iloc[te], clf.predict(X.iloc[te]))
    # Feature importances from the DEPLOYED artifact
    model = joblib.load(os.path.join(ROOT, "model.pkl"))
    feats = joblib.load(os.path.join(ROOT, "feature_columns.pkl"))
    imp = sorted(zip(feats, model.feature_importances_), key=lambda t: t[1])
    return cm, imp


# ============================================================ Fig 4
def fig_confusion(cm):
    labels = ["Normal", "Attack"]
    fig, ax = plt.subplots(figsize=(3.5, 3.3))
    vmax = cm.max()
    im = ax.imshow(cm, cmap=BLUE_RAMP, vmin=0, vmax=vmax)
    ax.set_xticks([0, 1], labels=labels)
    ax.set_yticks([0, 1], labels=labels)
    ax.set_xlabel("Predicted label", color=INK, fontsize=9)
    ax.set_ylabel("True label", color=INK, fontsize=9)
    ax.tick_params(colors=INK2, length=0)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    for i in range(2):
        for j in range(2):
            v = cm[i, j]
            frac = v / vmax if vmax else 0
            ax.text(j, i, f"{v}", ha="center", va="center",
                    fontsize=15, fontweight="bold",
                    color=("#ffffff" if frac > 0.5 else INK))
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.outline.set_edgecolor(GRID)
    cbar.ax.tick_params(colors=MUTED, length=0, labelsize=7)
    ax.set_title("Model C — Confusion Matrix\n(host-grouped test set, n = 213)",
                 fontsize=9.5, color=INK, fontweight="bold", pad=6)
    save(fig, "fig4_confusion_matrix")


# ============================================================ Fig 5
def fig_importance(imp):
    names = [n for n, _ in imp]
    vals = np.array([v for _, v in imp])
    fig, ax = plt.subplots(figsize=(4.4, 3.5))
    colors = BLUE_RAMP(0.35 + 0.6 * (vals / vals.max()))
    ax.barh(names, vals, color=colors, edgecolor="#184f95", linewidth=0.5,
            height=0.68, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + 0.006, i, f"{v:.3f}", va="center", ha="left",
                fontsize=7.5, color=INK2)
    ax.set_xlim(0, vals.max() * 1.18)
    ax.set_xlabel("Gini importance", color=INK, fontsize=9)
    ax.tick_params(colors=INK, length=0, labelsize=8)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.set_title("Model C — Random Forest Feature Importance",
                 fontsize=9.5, color=INK, fontweight="bold", pad=6)
    save(fig, "fig5_feature_importance")


if __name__ == "__main__":
    fig_architecture()
    fig_ml_pipeline()
    fig_data_flow()
    cm, imp = compute_model_c()
    print("confusion matrix:", cm.tolist())
    fig_confusion(cm)
    fig_importance(imp)
    print("All figures written to", HERE)
