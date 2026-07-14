from datetime import datetime
from flask import Flask, render_template, request
import pandas as pd
import joblib
import pickle


app = Flask(__name__)

# Load trained model
model = joblib.load("model.pkl")

# Load encoders
with open("encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

# Column subset/order the deployed model (Model C) was trained on
feature_columns = joblib.load("feature_columns.pkl")

# The columns an upload MUST contain for the model to run (Model C features)
REQUIRED_COLUMNS = feature_columns


def validate_upload(df):
    """Return a user-friendly error string if the uploaded DataFrame is not
    usable, or None if it passes all checks. Does not modify df."""

    # 1. Wrong delimiter: a non-comma separator makes pandas read the entire
    #    row as ONE column whose name still contains that separator.
    if df.shape[1] == 1:
        only_col = str(df.columns[0])
        for delim, name in ((";", "semicolon (;)"), ("\t", "tab"), ("|", "pipe (|)")):
            if delim in only_col:
                return (
                    f"The file does not look comma-delimited — it appears to use a "
                    f"{name} separator, so every field was read as a single column. "
                    f"Valcore expects a comma-separated CSV. Please convert the file "
                    f"to use commas as the delimiter and upload it again."
                )

    # 2. Empty CSV: a header with no data rows (or a blank file).
    if df.shape[0] == 0:
        return (
            "The uploaded CSV has no data rows — it contains only a header (or is "
            "blank). Please upload a file with at least one row of network-flow data."
        )

    # 3. A single unusable column with no recognizable delimiter.
    if df.shape[1] == 1:
        return (
            "The uploaded file has only one column, so it cannot be read as a "
            "network-flow CSV. Please check that it is a valid, comma-delimited file."
        )

    # 4. Missing required feature columns.
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return (
            "The CSV is missing required column(s): "
            + ", ".join(missing)
            + ". Valcore's model needs all of these features: "
            + ", ".join(REQUIRED_COLUMNS)
            + "."
        )

    return None


@app.route("/")
def home():
    return render_template("index.html")
# NOTE:
# If you want the dashboard to clear previous scan results on every refresh,
# replace this home() function with the commented version below.
# @app.route("/")
# def home():
#     return render_template(
#         "index.html",
#         packets=None,
#         attack=None,
#         normal=None,
#         confidence=None,
#         threat=None,
#         recommendation=None,
#         timestamp=None
#     )

@app.route("/predict", methods=["POST"])
def predict():

    if "file" not in request.files:
        return render_template(
            "index.html",
            error="No file was uploaded. Please choose a CSV file and try again."
        )

    file = request.files["file"]

    if file.filename == "":
        return render_template(
            "index.html",
            error="No file selected. Please choose a CSV file to analyze."
        )

    # --- Read the file, catching an empty or unparseable upload ---
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        return render_template(
            "index.html",
            error="The uploaded file is empty. Please upload a CSV that has a header "
                  "row and at least one row of network-flow data."
        )
    except pd.errors.ParserError as e:
        return render_template(
            "index.html",
            error=f"The file could not be read as CSV: {e}. Please make sure it is a "
                  "valid, comma-delimited CSV file."
        )

    # --- Validate the structure before running the model ---
    validation_error = validate_upload(df)
    if validation_error:
        return render_template("index.html", error=validation_error)

    try:

        for col in ["Unnamed: 0", "pkSeqID", "category", "subcategory", "seq"]:
            if col in df.columns:
                df.drop(columns=col, inplace=True)

        if "attack" in df.columns:
            df_features = df.drop(columns=["attack"])
        else:
            df_features = df.copy()

        for col, encoder in encoders.items():

            if col in df_features.columns:

                df_features[col] = df_features[col].astype(str)

                known = set(encoder.classes_)

                df_features[col] = df_features[col].apply(
                    lambda x: x if x in known else encoder.classes_[0]
                )

                df_features[col] = encoder.transform(df_features[col])

        # Keep only the Model C features, in the exact training order.
        # Any extra columns in the upload (e.g. saddr, daddr, sport, dport)
        # are ignored so the input matches what the model expects.
        df_features = df_features[feature_columns]

        predictions = model.predict(df_features)

        attack_packets = int(predictions.sum())

        normal_packets = len(predictions) - attack_packets

        probabilities = model.predict_proba(df_features)

        confidence = round(
    probabilities.max(axis=1).mean() * 100,
    2
)

        attack_percent = attack_packets / len(predictions)

        if attack_percent < 0.30:
            threat = "LOW"
            recommendation = "Continue Monitoring"

        elif attack_percent < 0.70:
            threat = "MEDIUM"
            recommendation = "Investigate Suspicious Activity"

        else:
            threat = "HIGH"
            attack_percent = attack_packets / len(predictions)

        if attack_percent < 0.30:
            threat = "LOW"
            recommendation = "Continue monitoring network traffic."

        elif attack_percent < 0.70:
            threat = "MEDIUM"
            recommendation = "Investigate suspicious devices and traffic."

        else:
            threat = "HIGH"
            recommendation = "Isolate affected devices and begin incident response."

        return render_template(

            "index.html",

    packets=len(predictions),

    attack=attack_packets,

    normal=normal_packets,

    confidence=confidence,

    threat=threat,

    recommendation=recommendation,

    timestamp=datetime.now().strftime("%d %b %Y %H:%M")

)

    except Exception as e:

        return render_template(

            "index.html",

            error=str(e)

        )

if __name__ == "__main__":
    app.run(debug=True)