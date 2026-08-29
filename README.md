# Sprint Retro

A self-hosted, multi-tenant sprint retrospective SaaS. Anyone can sign up and
create their own organization; create a retro, invite the team, collect the
five-question retrospective from each member, and give PMO/Team Leads a
consolidated view and report — all stored on your own infrastructure.

This is intentionally **not** a project management tool. It does not track
action items, tasks, or use AI. See the product spec for the full list of
what's in and out of scope for V1.

## Accounts, organizations, and sign-up

Sprint Retro is multi-tenant: signing up (`/signup`) always creates a **new
organization**, with the signing-up person as that org's Admin. Email
ownership is verified with a 6-digit OTP sent via SMTP before the account can
log in.

A single email/login can belong to **more than one organization** — e.g. an
Admin adds someone who already has a Sprint Retro account (from `/users`,
leaving the password field blank) and that person is simply attached to the
new org with whatever role they're given there, independent of their role
elsewhere. If a login belongs to 2+ active orgs, the login screen asks which
one to enter; an org switcher in the nav bar lets them move between orgs
afterward without re-entering their password.

Every team, project, and retrospective is scoped to one organization — no
data is ever visible across orgs.

## Architecture

```
                              Docker Compose

               ┌────────────────────┐   ┌────────────────────┐
               │      Landing       │   │      Frontend      │
               │   Next.js (3001)   │   │   Next.js (3000)   │
               │  (marketing site,  │   │  (the application)  │
               │  independent       │   └─────────┬──────────┘
               │  container)        │             │ REST API
               │  Login → :3000     │             ↓
               └────────────────────┘   ┌────────────────────┐
                                         │      Backend       │
                                         │  FastAPI (8000)    │
                                         └─────────┬──────────┘
                                                   ↓
                                         ┌────────────────────┐
                                         │       SQLite       │
                                         │   ./data (volume)  │
                                         └────────────────────┘
```

- **Backend**: Python + FastAPI + SQLAlchemy + SQLite, JWT auth, role-based access
  (Admin / PMO / Team Member).
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS — the actual
  application (login, dashboards, retros, admin pages).
- **Landing**: Next.js (App Router) + TypeScript + Tailwind CSS — a separate,
  independent marketing/landing container (Material You design system: purple
  seed color, pill buttons, tonal surfaces). It only links out to the frontend's
  `/login`; it has no dependency on the backend or frontend containers and can
  be built, deployed, or taken down on its own.
- **Email**: SMTP invitation emails (optional — the app works without SMTP
  configured; it just logs that email was skipped).

## Requirements

- Docker and Docker Compose
- No local Python or Node.js installation needed to run the app

## Setup

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

- `SECRET_KEY` — a strong random value, e.g. `openssl rand -hex 32`
- `SMTP_*` — if you want retro invitation emails to actually send. Leave blank
  to run without email (invitations are simply not delivered, and this is
  logged).
- `APP_NAME` — shown in the UI and browser tab.

## Start

```bash
docker compose up -d
```

- Frontend (the app): http://localhost:3000
- Landing page (marketing site): http://localhost:3001
- Backend API: http://localhost:8000 (docs at `/docs`)
- Health check: http://localhost:8000/health

The backend creates its SQLite schema automatically on startup. To load
development sample data (an admin, a PMO/team lead, two team members, a team,
a project, and an open retro), run once:

```bash
docker compose exec backend python seed.py
```

This prints development-only login credentials to the console. **Never use
seed credentials in production.**

## Stop

```bash
docker compose down
```

## Logs

```bash
docker compose logs -f
```

## Database

The SQLite database lives at `./data/sprint_retro.db` on the host, mounted
into the backend container so it survives restarts and rebuilds.

## Backup

Because SQLite is a single file, a backup is just a copy of that file made
while the application is idle (or at least not mid-write):

```bash
docker compose stop backend
cp data/sprint_retro.db backups/sprint_retro-$(date +%Y%m%d-%H%M%S).db
docker compose start backend
```

No backup-management system is built into V1 — this manual copy is enough for
an internal tool.

## Roles

Roles are **per-organization** — the same person can be Admin in one org and
a Team Member in another.

- **Admin** — manages users, teams, and projects; the only role that can see
  Sprint Hero vote results.
- **PMO / Team Lead** — creates retros, invites team members, reviews
  responses, generates reports, closes retros.
- **Team Member** — fills out and submits their own retro response.

## Sprint Hero voting

Alongside the five-question form, any invited participant can cast one
**Sprint Hero** vote per retro — for anyone active in the organization, not
just their own team (you can't vote for yourself). Votes are anonymous by
default; the voter can opt in to reveal their name. An optional comment (up
to 500 characters) can be added explaining the vote. Votes can be changed at
any time until the retro is marked Completed.

Only **Admin** can see the results (vote counts per person, plus any comments
and the names of anyone who chose to reveal themselves) — not PMO, not other
team members, and never who voted for whom unless that voter opted in.

## Local development (without Docker)

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py        # optional sample data
uvicorn app.main:app --reload --port 8000
```

Run backend tests:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Landing page (runs on port 3001, independent of the app):

```bash
cd landing
npm install
cp .env.example .env.local
npm run dev
```

## Project structure

```
sprint-retro/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, database.py
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── api/          # FastAPI routers
│   │   ├── services/     # business logic
│   │   └── auth/         # password hashing, JWT
│   ├── tests/
│   ├── seed.py
│   └── Dockerfile
├── frontend/
│   ├── app/               # Next.js App Router pages
│   ├── components/
│   ├── lib/               # API client, auth context, types
│   └── Dockerfile
└── landing/                # separate marketing site container (Material You)
    ├── app/                # page.tsx, layout.tsx, globals.css
    ├── components/         # Header, Hero, Features, HowItWorks, Faq, ...
    ├── lib/config.ts       # NEXT_PUBLIC_APP_URL (where Login/CTAs point)
    └── Dockerfile
```
