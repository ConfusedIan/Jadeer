# Jadeer Survey (Streamlit + Supabase)

Arabic survey page that stores responses in a Supabase Postgres database.

## Setup

1. Copy `.env.example` → `.env` and fill in `SUPABASE_DB_PASSWORD`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create the table (one-time). Either:
   - Paste `schema.sql` into the Supabase SQL Editor and run it, **or**
   - Let the app run `ensure_schema()` on first submit (it runs `CREATE TABLE IF NOT EXISTS`).

## Run

```bash
streamlit run survey_app.py
```

## Schema

One row per submission in `survey_responses`:

- `q1_skills_proof`, `q2_cert_verification`, `q3_cv_tailoring`, `q4_cv_biggest_problem` — stored as the full Arabic option text (A/B/C/D).
- `q5_rank_skills_assessment`, `q5_rank_cert_verification`, `q5_rank_cv_tailoring`, `q5_rank_smart_matching` — rank 1–4 (1 = most important). App enforces unique ranks client-side.
