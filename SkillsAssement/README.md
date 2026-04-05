# 🎯 Skill Assessment Module

An AI-powered **Soft Skills Assessment** microservice built on [O\*NET](https://www.onetonline.org/) standards. It matches users to occupations and generates scenario-based assessments for **14 workplace soft skills**.

This module is part of the **Jadeer** platform and runs as a microservice behind the API Gateway.

---

## 📁 Project Structure

| File | Description |
|------|-------------|
| `app.py` | **FastAPI REST API** — assessment backend with Supabase auth, O\*NET data, AI question generation, scoring, and result storage |
| `stremlitapp.py` | **Streamlit Web UI** — interactive frontend for taking assessments (runs standalone) |
| `main.py` | **CLI version** — lightweight command-line assessment tool |
| `Skills.xlsx` | **O\*NET Skills dataset** — official importance/level ratings for all occupations |
| `Dockerfile` | Docker container definition (port 5003) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## 🧠 Assessed Skills (14 O\*NET Soft Skills)

### Social Skills
Coordination · Instructing · Negotiation · Persuasion · Service Orientation · Social Perceptiveness

### Thinking Skills
Active Learning · Active Listening · Complex Problem Solving · Critical Thinking · Judgment and Decision Making · Learning Strategies · Monitoring · Time Management

---

## ⚙️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

```env
NEBIUS_API_KEY=your_nebius_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Run with Docker Compose (recommended)

From the **Jadeer root directory**:

```bash
docker compose up skills_assessment
```

Or start all services:

```bash
docker compose up
```

### 4. Run Standalone

```bash
uvicorn app:app --host 0.0.0.0 --port 5003
```

---

## 🏗 Architecture

```
Client → API Gateway (:8000) → /assessment/* → Skills Assessment Service (:5003)
```

The API Gateway handles JWT authentication and forwards requests to this service. All routes use the `/assessment/` prefix.

---

## 📡 API Endpoints

All endpoints are accessed through the **API Gateway** at port `8000` with prefix `/assessment/`.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/assessment/skills-list` | 🔒 | List all 14 soft skills |
| `GET` | `/assessment/occupations` | 🔒 | List all O\*NET occupations |
| `POST` | `/assessment/match-occupation` | 🔒 | Match user profile to closest O\*NET occupation |
| `POST` | `/assessment/generate-assessment` | 🔒 | Generate 5 MCQ questions for occupation + skill |
| `POST` | `/assessment/evaluate` | 🔒 | Evaluate answers, return score/pass-fail |
| `POST` | `/assessment/full-assessment` | 🔒 | All-in-one: generate → evaluate → save |
| `GET` | `/health` | — | Health check |

### Example: Generate Assessment (via API Gateway)

```bash
curl -X POST http://localhost:8000/assessment/generate-assessment \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"occupation_code": "15-1254.00", "skill_name": "Critical Thinking"}'
```

### Example: Full Assessment with Evaluation

```bash
curl -X POST http://localhost:8000/assessment/full-assessment \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "occupation_code": "15-1254.00",
    "skill_name": "Critical Thinking",
    "answers": {"0": "A", "1": "C", "2": "B", "3": "D", "4": "A"}
  }'
```

---

## 📊 How It Works

1. **Occupation Matching** — User's Supabase profile is matched to an O\*NET occupation via AI
2. **Skill Data Lookup** — O\*NET importance/level scores are loaded from `Skills.xlsx`
3. **Question Generation** — AI generates 5 scenario-based MCQs calibrated to skill difficulty
4. **Scoring** — Dynamic pass threshold based on skill importance (2/5, 3/5, or 4/5)
5. **Result Storage** — Results saved to Supabase `assessment_results` table

---

## 🛠 Tech Stack

- **Backend**: FastAPI + Uvicorn
- **AI Model**: Qwen 2.5 Coder 7B (via Nebius API)
- **Database**: Supabase (PostgreSQL + Auth + RLS)
- **Data Source**: O\*NET Skills database
- **Deployment**: Docker + Docker Compose
