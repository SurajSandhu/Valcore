import joblib
import pickle

model = joblib.load("model.pkl")

with open("encoders.pkl","rb") as f:
    encoders = pickle.load(f)

feature_columns = joblib.load("feature_columns.pkl")