# Reel Match — Content-Based Movie Recommender

![Image](https://raw.githubusercontent.com/khelendrameena/neubytes_internship_task/main/reel-match-app/home.png)

A small full-stack app: you type a movie you like, it returns 6 similar movies based on genre, director, cast and theme overlap. Built with Flask + scikit-learn on the backend and a plain HTML/CSS/JS frontend — no framework build step, no external ML API, no paid services.

**Live app:** _add your deployed URL here after deploying_
**Repo:** _add your GitHub repo URL here_

---

## How it works (plain-English version)

Every movie in the dataset gets turned into one "content string" — its genres, director, lead cast and a few theme words all mashed together (e.g. `"crime drama christopher nolan christian bale heath ledger batman joker gotham"`). TF-IDF (a standard scikit-learn technique) converts every movie's content string into a vector of numbers, weighting words by how distinctive they are — "drama" barely counts since half the dataset has it, but "gotham" or a specific director's name counts a lot. Cosine similarity then measures the angle between every pair of movie vectors: a small angle means two movies share a lot of the same distinctive words, which usually means they're actually similar in tone and subject.

There's no training loop, no neural network, and no model file to bundle — the whole "model" is built from `data/movies.csv` in under a second whenever the server starts, which is why it's light enough for a free hosting tier.

---

## Project structure

```
movie_reco/
├── app.py                   # Flask backend — routes, error handling, recommendation logic
├── build_dataset.py         # One-time script that generated data/movies.csv
├── data/
│   └── movies.csv           # 174 movies: title, year, genres, director, cast, tags
├── templates/
│   └── index.html           # Frontend — single page, no build step
├── requirements.txt
├── render.yaml               # Render deployment config
├── Procfile                  # Railway / other Procfile-based platforms
├── .env.example               # Pattern for environment variables (see Security below)
├── postman_collection.json    # Import into Postman to re-run all API tests
├── POSTMAN_TESTING.md          # Documented request/response/timing for every endpoint
└── README.md
```

---

## Dataset

`data/movies.csv` — 174 well-known movies spanning most major genres and five decades, hand-curated rather than pulled from a large external dataset. Each row has: `movie_id, title, year, genres, director, cast, tags`. `genres` is pipe-separated (e.g. `Action|Crime|Drama`) so a movie can belong to more than one genre.

Kept intentionally small and self-contained (24KB) instead of using a public 5,000+ row dataset (some of which run 20MB+) for two reasons: it means the app has zero external dependency at runtime — no file to download, nothing that can fail on a cold start — and it stays well inside the "avoid bundling very large files" guidance for free hosting tiers. `build_dataset.py` documents exactly how it was built, and is easy to extend — add rows to the `MOVIES` list and rerun it to grow the catalog.

---

## Running it locally

```bash
git clone <your-repo-url>
cd movie_reco
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

Open `http://127.0.0.1:5000` in a browser. That's the whole setup — no database, no build step, no API key required.

---

## Using the app (non-technical walkthrough)

1. Open the link.
2. Type the name of a movie you like into the box (autocomplete suggests titles as you type).
3. Click **Find Similar**.
4. Six similar movies appear, each with a match percentage, genre, director and year.

Small typos are handled — typing "Incepton" still matches "Inception". If a movie isn't in the catalog, the app says so clearly instead of failing silently.

---

## API reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the frontend |
| `/api/health` | GET | Returns `{"status": "ok", "movies_loaded": N}` |
| `/api/movies` | GET | Returns all movie titles (powers the autocomplete) |
| `/api/recommend` | POST | Body: `{"movie": "<title>"}` → returns matched title + 6 recommendations |

Full documented request/response pairs (including every error case) are in **[POSTMAN_TESTING.md](POSTMAN_TESTING.md)**, and importable into Postman directly from **`postman_collection.json`**.

---

## Error handling

The backend never returns a raw 500 error page to the user. Specifically handled:

- Empty or missing `movie` field → `400` with a clear message
- Malformed JSON body → `400`
- A movie title not in the dataset → `404`, with a suggestion to check `/api/movies`
- Wrong HTTP method on an endpoint → `405`
- Any unexpected server exception → caught by a generic `500` handler that returns JSON, not a traceback

---

## Security

No API keys, database credentials, or secrets are used by this app — the whole recommender is self-contained. Even so, the project follows the environment-variable pattern (`.env.example` shows it) rather than hardcoding anything, so it's ready to extend without a rewrite if you plug in a real API later. `.env` itself is git-ignored and was never committed.

---

## Testing

**Automated:** `python3 -m pytest tests/` runs a small pytest suite covering a valid request, all four error cases, and the health check (see `tests/test_app.py`).

**Manual / API:** see `POSTMAN_TESTING.md` — every endpoint tested with real captured request/response/timing data, plus the importable `postman_collection.json`.

---

## Deployment (Render — recommended free option)

1. Push this repo to GitHub (make sure `.env` is **not** included — check `.gitignore`).
2. Go to [render.com](https://render.com) → New → Web Service → connect your GitHub repo.
3. Render will read `render.yaml` automatically. If asked manually:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Deploy. Render gives you a public `https://<your-app>.onrender.com` URL.

**Railway** and **PythonAnywhere** work too — Railway reads the included `Procfile` the same way; PythonAnywhere needs the WSGI file pointed at `app.app` per their Flask setup guide.

### Cold starts
Free tiers on Render/Railway spin the app down after a period of inactivity. **Expect the first request after idle time to take 20-50 seconds** while the instance wakes up — every request after that is fast (single-digit milliseconds for this app, since there's no heavy model to reload). If you're demoing this live, open the link a minute before you need it.

---

## Model explanation (short version, for the submission writeup)

**Type:** Content-based recommender using TF-IDF vectorization + cosine similarity (scikit-learn's `TfidfVectorizer` and `cosine_similarity`) — not a neural network, not a collaborative-filtering model that needs user rating history.

**Why this approach:** it needs no training data beyond the movie metadata itself, no GPU, produces results instantly on server start, and stays interpretable — you can point at exactly why two movies matched (shared director, shared genres, shared theme words), which matters for a project meant to show you can build, connect, test, and deploy a complete pipeline rather than just call a black-box API.

**Limitations, stated honestly:** with 174 movies the catalog is a demo-scale dataset, not a production one — recommendations are only as good as the tag words assigned to each movie, and it has no notion of user taste over time (every request is independent, there's no login or history). Scaling this up would mean swapping `data/movies.csv` for a larger dataset and nothing else in `app.py` needs to change.
