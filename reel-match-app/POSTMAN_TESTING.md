# API Testing — Postman

A ready-to-import collection is included at `postman_collection.json` (Postman → Import → File). It has all 9 requests below already set up, pointed at a `{{base_url}}` variable — just change that variable to your deployed URL and hit Send on each one to get your own screenshots.

Everything below was run locally against `http://127.0.0.1:5000` while the app was live, so the responses are real, not made up.

---

### 1. GET `/api/health`
Quick check that the server is up and the dataset loaded.

- **Method:** GET
- **Input:** none
- **Response (200):**
```json
{ "status": "ok", "movies_loaded": 174 }
```
- **Response time:** ~2ms locally (expect 1-3s on a cold free-tier instance, see README)

---

### 2. GET `/api/movies`
Returns every movie title, used by the frontend to power the autocomplete box.

- **Method:** GET
- **Input:** none
- **Response (200):** `{ "titles": ["10 Things I Hate About You", "12 Years a Slave", ...] }` (174 titles)
- **Response time:** ~3ms locally

---

### 3. POST `/api/recommend` — valid movie
- **Method:** POST
- **Input:** `{ "movie": "Inception" }`
- **Response (200):**
```json
{
  "matched_title": "Inception",
  "recommendations": [
    { "title": "The Prestige", "year": 2006, "genres": "Drama|Mystery|Sci-Fi", "director": "Christopher Nolan", "match_score": 17.6 },
    { "title": "Interstellar", "year": 2014, "genres": "Adventure|Drama|Sci-Fi", "director": "Christopher Nolan", "match_score": 16.2 },
    { "title": "Shutter Island", "year": 2010, "genres": "Mystery|Thriller", "director": "Martin Scorsese", "match_score": 15.9 },
    { "title": "The Departed", "year": 2006, "genres": "Crime|Drama|Thriller", "director": "Martin Scorsese", "match_score": 15.8 },
    { "title": "The Revenant", "year": 2015, "genres": "Action|Adventure|Drama", "director": "Alejandro G. Iñárritu", "match_score": 15.5 },
    { "title": "The Dark Knight", "year": 2008, "genres": "Action|Crime|Drama", "director": "Christopher Nolan", "match_score": 13.5 }
  ]
}
```
- **Response time:** ~2-3ms locally

---

### 4. POST `/api/recommend` — typo / fuzzy match
- **Input:** `{ "movie": "Incepton" }`
- **Response (200):** identical to test 3 — matched back to "Inception" via fuzzy string matching, so small spelling mistakes don't produce an error.

---

### 5. POST `/api/recommend` — ERROR: empty input
- **Input:** `{ "movie": "" }`
- **Response (400):**
```json
{ "error": "Please enter a movie title." }
```

### 6. POST `/api/recommend` — ERROR: missing field entirely
- **Input:** `{}`
- **Response (400):** same as above — `"Please enter a movie title."`

### 7. POST `/api/recommend` — ERROR: malformed JSON body
- **Input:** raw text `not valid json` (not parseable JSON)
- **Response (400):**
```json
{ "error": "Request body must be valid JSON." }
```

### 8. POST `/api/recommend` — ERROR: movie not in the dataset
- **Input:** `{ "movie": "zzqxnotamovie999" }`
- **Response (404):**
```json
{ "error": "Couldn't find a movie matching 'zzqxnotamovie999'. Try a different spelling or check /api/movies for the full list." }
```

### 9. GET `/api/recommend` — ERROR: wrong HTTP method
- **Response (405):**
```json
{ "error": "That HTTP method isn't allowed on this endpoint." }
```

---

None of the error cases above return a raw Flask/Werkzeug 500 traceback page — every failure path returns clean JSON with a 4xx status, which is what `app.errorhandler` in `app.py` guarantees even for unexpected exceptions (caught as a 500 with a generic message, not a stack trace).
