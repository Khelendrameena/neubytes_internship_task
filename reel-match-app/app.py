"""
Movie Recommender - Flask backend.

How it works (kept simple on purpose):
- Each movie gets a "content string" made of its genres, director, cast and a few tag words.
- TF-IDF turns those content strings into vectors, and cosine similarity finds movies whose
  vectors point in a similar direction - that's the whole recommendation engine.
- There's no training step and no external model file, so there's nothing large to bundle
  and nothing that can run out of memory on a free hosting tier.
"""
import os
import difflib

import pandas as pd
from flask import Flask, jsonify, render_template, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "movies.csv")


def load_model():
    df = pd.read_csv(DATA_PATH)
    df["genres_clean"] = df["genres"].fillna("").str.replace("|", " ", regex=False)
    df["content"] = (
        df["genres_clean"] + " " +
        df["director"].fillna("") + " " +
        df["cast"].fillna("").str.replace(",", " ", regex=False) + " " +
        df["tags"].fillna("")
    ).str.lower()

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(df["content"])
    similarity = cosine_similarity(matrix)

    title_lookup = {t.lower(): i for i, t in enumerate(df["title"])}
    return df, similarity, title_lookup


# Loaded once at startup, not per-request - keeps response times well under the 3-5s target.
MOVIES_DF, SIMILARITY_MATRIX, TITLE_LOOKUP = load_model()


def find_closest_title(user_input):
    """Exact match first, then fuzzy match, so small typos still work."""
    key = user_input.strip().lower()
    if key in TITLE_LOOKUP:
        return MOVIES_DF.loc[TITLE_LOOKUP[key], "title"]

    matches = difflib.get_close_matches(key, TITLE_LOOKUP.keys(), n=1, cutoff=0.6)
    if matches:
        return MOVIES_DF.loc[TITLE_LOOKUP[matches[0]], "title"]
    return None


def get_recommendations(title, top_n=6):
    idx = TITLE_LOOKUP[title.lower()]
    scores = list(enumerate(SIMILARITY_MATRIX[idx]))
    scores.sort(key=lambda x: x[1], reverse=True)
    scores = [s for s in scores if s[0] != idx][:top_n]

    results = []
    for i, score in scores:
        row = MOVIES_DF.loc[i]
        results.append({
            "title": row["title"],
            "year": int(row["year"]),
            "genres": row["genres"],
            "director": row["director"],
            "match_score": round(float(score) * 100, 1),
        })
    return results


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "movies_loaded": int(len(MOVIES_DF))})


@app.route("/api/movies")
def list_movies():
    """Lets the frontend build an autocomplete list instead of the user guessing exact titles."""
    return jsonify({"titles": sorted(MOVIES_DF["title"].tolist())})


@app.route("/api/recommend", methods=["POST"])
def recommend():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    movie_name = payload.get("movie", "")
    if not isinstance(movie_name, str) or not movie_name.strip():
        return jsonify({"error": "Please enter a movie title."}), 400

    matched_title = find_closest_title(movie_name)
    if matched_title is None:
        return jsonify({
            "error": f"Couldn't find a movie matching '{movie_name.strip()}'. "
                     f"Try a different spelling or check /api/movies for the full list."
        }), 404

    recommendations = get_recommendations(matched_title)
    return jsonify({
        "matched_title": matched_title,
        "recommendations": recommendations,
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "That endpoint doesn't exist."}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "That HTTP method isn't allowed on this endpoint."}), 405


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Something went wrong on our end. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
