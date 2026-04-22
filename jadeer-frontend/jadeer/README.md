# Jadeer — Frontend

Smart CV Authenticator & Advisor · KAU Senior Project (CPIS498)

## Run locally

```bash
cd jadeer
python -m http.server 8000
# open http://localhost:8000
```

No build step. Vanilla HTML/CSS/JS only.

## Project structure

```
jadeer/
├── index.html              Router shell + script loader
├── css/
│   ├── tokens.css          Design tokens (palette from current index.html — dark + purple)
│   ├── base.css            Reset, typography, signature purple-glow background
│   ├── components.css      Buttons, inputs, cards, badges, modals, proficiency bars, etc.
│   └── layout.css          App shell (sidebar + topbar) + auth shell
├── js/
│   ├── config.js           Supabase URL / anon key / API Gateway base URL
│   ├── api.js              fetch wrapper with JWT auth + Supabase direct calls
│   ├── auth.js             signUp / signIn / signOut / role detection
│   ├── i18n.js             EN/AR dictionary + RTL toggle (dir=rtl switch)
│   ├── router.js           Hash router with :param support and lang-change re-render
│   ├── ui.js               toast, modal, confirmDialog, el factory
│   └── pages/
│       ├── auth.js         Login + Sign Up (Figures 4.2 & 4.3) — DONE
│       └── stubs.js        Dashboard + placeholder routes — to be expanded in Phase 2
└── README.md
```

## What works right now (Phase 1 checkpoint)

- Full design system and app shell (RTL-aware using CSS logical properties)
- EN ⇄ عربي language toggle, persists across reloads
- **Login** (Figure 4.2) — hits Supabase `/auth/v1/token` directly
- **Sign Up** (Figure 4.3) — role picker + live password-rule checklist, hits Supabase `/auth/v1/signup`
- JWT stored in `localStorage`, auto-attached as `Bearer <token>` to all Gateway calls
- Role-aware redirects (candidate → `/dashboard`, employer → `/employer`)
- Minimal Candidate Dashboard skeleton (Figure 4.5) to confirm end-to-end flow

## Coming in Phase 2

Every remaining page from PDF Figures 4.4 through 4.21, matching the prototype exactly:

- Candidate onboarding, profile view/edit, skills + Add Skill modal + Assessment flow
  (10 questions delivered as 2× backend `generate-assessment` calls as agreed),
  Assessment Passed / Failed modals, Certificates tabs + Add Certificate, Recommendations
  input + results, CV Library, Edit CV modal, Chats (localStorage-backed stub)
- Employer onboarding, profile, candidate search with filters + ranked results, Chats

## Backend endpoint reference (already wired in `js/api.js`)

Base: `https://api-gateway-gati.onrender.com`

- Profile: `GET|PATCH /profile/me`, `*/experiences`, `*/education`, `*/certificates`, `*/skills` (full CRUD)
- Certificates: `POST /certificates`, `GET /certificates/issuers`, `GET /certificates/candidate/{id}`
- Assessment: `GET /assessment/skills-list`, `POST /assessment/full-assessment`, ...
- CV: `POST /cv/me.pdf` (returns PDF blob), `GET /cv/history`, `GET /cv/history/{id}`
- Recommendations: `POST /recommendation/analyze`, `POST /recommendation/generate-bio`
- Ranking: `POST /ranking/search`
