# 🎯 Skill Assessment Module

An AI-powered **Soft Skills Assessment** system built on [O\*NET](https://www.onetonline.org/) standards. It matches users to occupations and generates scenario-based assessments for **14 workplace soft skills**.

---

## 📁 Project Structure

| File | Description |
|------|-------------|
| `app.py` | **FastAPI REST API** — full assessment backend with Supabase auth, O\*NET data, AI question generation, scoring, and result storage |
| `stremlitapp.py` | **Streamlit Web UI** — interactive frontend for taking assessments with visual results and history |
| `main.py` | **CLI version** — lightweight command-line assessment tool |
| `Skills.xlsx` | **O\*NET Skills dataset** — official importance/level ratings for all occupations |
| `create_assessment_results_table.sql` | **Database schema** — SQL migration for the `assessment_results` table in Supabase |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## 🧠 Assessed Skills (14 O\*NET Soft Skills)

### Social Skills
- Coordination
- Instructing
- Negotiation
- Persuasion
- Service Orientation
- Social Perceptiveness

### Thinking Skills
- Active Learning
- Active Listening
- Complex Problem Solving
- Critical Thinking
- Judgment and Decision Making
- Learning Strategies
- Monitoring
- Time Management

---

## ⚙️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
NEBIUS_API_KEY=your_nebius_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

| Variable | Required By | Description |
|----------|------------|-------------|
| `NEBIUS_API_KEY` | All | API key for Nebius AI (powers question generation via Qwen model) |
| `SUPABASE_URL` | `app.py`, `stremlitapp.py` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | `app.py`, `stremlitapp.py` | Your Supabase anonymous/public key |

### 3. Set Up Database (for API / Streamlit)

Run the SQL in `create_assessment_results_table.sql` in your Supabase SQL Editor to create the `assessment_results` table with Row Level Security.

---

## 🚀 Running

### Option 1: FastAPI REST API (`app.py`)

```bash
uvicorn app:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. See [API Endpoints](#-api-endpoints) below.

### Option 2: Streamlit Web App (`stremlitapp.py`)

```bash
streamlit run stremlitapp.py
```

Opens an interactive web interface where users can:
- Log in with their Supabase account
- Get matched to an O\*NET occupation based on their profile
- Select a soft skill and take a 5-question scenario-based assessment
- View detailed results and assessment history

### Option 3: CLI Tool (`main.py`)

```bash
python main.py
```

A simple command-line interface — enter a job description, pick a skill, and answer 5 questions.

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | — | Service info and available endpoints |
| `GET` | `/health` | — | Health check (config status) |
| `GET` | `/api/skills-list` | — | List all 14 soft skills |
| `GET` | `/api/occupations` | — | List all O\*NET occupations |
| `POST` | `/api/match-occupation` | 🔒 Bearer | Match authenticated user's profile to closest O\*NET occupation |
| `POST` | `/api/generate-assessment` | — | Generate 5 MCQ questions for a given occupation + skill |
| `POST` | `/api/evaluate` | Optional | Evaluate answers and return score/pass-fail (saves to DB if authenticated) |
| `POST` | `/api/full-assessment` | Optional | All-in-one: generate questions → evaluate answers → save results |

### Example: Generate Assessment

```bash
curl -X POST http://localhost:8000/api/generate-assessment \
  -H "Content-Type: application/json" \
  -d '{"occupation_code": "15-1254.00", "skill_name": "Critical Thinking"}'
```

### Example: Full Assessment with Evaluation

```bash
curl -X POST http://localhost:8000/api/full-assessment \
  -H "Content-Type: application/json" \
  -d '{
    "occupation_code": "15-1254.00",
    "skill_name": "Critical Thinking",
    "answers": {"0": "A", "1": "C", "2": "B", "3": "D", "4": "A"}
  }'
```

---

## 🔒 Authentication

- The API uses **Supabase JWT tokens** for authentication
- Pass the token as: `Authorization: Bearer <supabase_access_token>`
- Authentication is **required** for `/api/match-occupation` (reads user profile)
- Authentication is **optional** for `/api/evaluate` and `/api/full-assessment` (saves results if authenticated)

---

## 📊 How It Works

1. **Occupation Matching** — The user's Supabase profile (skills, experience, CV) is sent to an LLM which matches them to the closest O\*NET occupation
2. **Skill Data Lookup** — O\*NET importance/level scores are retrieved from `Skills.xlsx` for the matched occupation
3. **Question Generation** — AI generates 5 scenario-based MCQs calibrated to the skill's importance and difficulty level
4. **Scoring** — Answers are scored with a dynamic pass threshold based on the skill's standardized importance
5. **Result Storage** — Results are saved to Supabase `assessment_results` table (if authenticated)

---

## 🛠 Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Frontend**: [Streamlit](https://streamlit.io/)
- **AI Model**: Qwen 2.5 Coder 7B (via [Nebius API](https://nebius.com/))
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL + Auth + RLS)
- **Data Source**: [O\*NET](https://www.onetonline.org/) Skills database
