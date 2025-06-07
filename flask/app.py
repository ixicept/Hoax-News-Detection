import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import nltk

import sys
print(sys.version)

nltk.download("stopwords")
from nltk.corpus import stopwords

# Load pipeline
with open("./rf_w2v_hoax.pkl", "rb") as f:
    bundle = pickle.load(f)
rf = bundle["rf_model"]
w2v = bundle["w2v_model"]
stops = bundle["stops"]

def clean_tokenize(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in stops and len(t) > 1]

def doc_embedding(tokens):
    vecs = [w2v.wv[w] for w in tokens if w in w2v.wv]
    return np.mean(vecs, axis=0) if vecs else np.zeros(w2v.vector_size)

app = Flask(__name__)
CORS(app, origins=["*"])

@app.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(force=True)
    title = payload.get("title", "")
    body  = payload.get("body", "")
    title_emb = doc_embedding(clean_tokenize(title))
    body_emb  = doc_embedding(clean_tokenize(body))
    feat = np.hstack([title_emb, body_emb])  # shape (600,)
    probas = rf.predict_proba([feat])[0]
    pred_idx = np.argmax(probas)
    label = rf.classes_[pred_idx]
    confidence = float(probas[pred_idx])
    return jsonify({
        "prediction": label,
        "confidence": confidence
    })

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=4998, debug=True)