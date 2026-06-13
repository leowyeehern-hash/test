# StudyConnect – MVP Platform

StudyConnect is a web platform that connects students seeking academic support with peers willing to tutor them, either voluntarily or for a fee. The platform features an intelligent, weighted compatibility matching algorithm, real-time message threads, session request management, and a comprehensive admin reporting dashboard.

---

## Tech Stack & Architecture

- **Backend**: Python 3 + Flask (REST API) + SQLite (Database) + Pandas (Analytics)
- **Frontend**: React 18 + Vite (Dev Server) + Framer Motion (Animations) + Lucide Icons + CSS Variables (Modern Theme)

```
Project Mini IT/
├── backend/                  ← Flask Python REST API
│   ├── app.py                ← Main application server
│   ├── database.py           ← SQLite database helper functions
│   ├── matching.py           ← Weighted matching algorithm
│   ├── analytics.py          ← Pandas dashboard analytical queries
│   └── requirements.txt      ← Python package dependencies
│
├── frontend/                 ← React JS SPA
│   ├── src/                  ← Components & pages code
│   ├── package.json          ← Frontend npm packages
│   └── vite.config.js        ← Vite configurations & backend proxy
│
├── seed_db.py                ← Local SQLite database seeder
└── README.md                 ← Document guide (this file)
```

---

## Getting Started

### 1. Set Up and Run Backend

First, navigate to the `backend/` directory or remain in the root directory to install Python dependencies:

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start Flask Server (starts on http://127.0.0.1:5000)
python backend/app.py
```

### 2. Seed Demo Database Records

Run the database seeder from the root workspace folder to populate user accounts, availability grids, messages, reviews, and pending requests:

```bash
python seed_db.py
```

### 3. Set Up and Run Frontend

Navigate to the `frontend/` directory, install packages, and spin up the Vite development server:

```bash
cd frontend

# Install Node modules
npm install

# Run Vite dev server (starts on http://localhost:5173)
npm run dev
```

*Note: Vite configuration includes a proxy mapping `/api/*` requests directly to Flask (`http://127.0.0.1:5000/api/*`).*

---

## Seeded Demo Accounts

You can log in to any of these accounts using the password **`password123`**:

| Name | Email | Role | Subjects / Info |
|---|---|---|---|
| **Admin** | `admin@studyconnect.com` | `admin` | Access to Admin dashboard, user accounts tables, platform charts |
| **Alice Tan** | `alice@monash.edu` | `student` | Needs help with Mathematics & Physics |
| **Bob Lim** | `bob@monash.edu` | `student` | Needs help with Accounting & Economics |
| **Charlie Song** | `charlie@monash.edu` | `volunteer` | Volunteer tutor for Mathematics & Physics (Free help) |
| **Dana Vance** | `dana@monash.edu` | `volunteer` | Volunteer tutor for Programming & Data Science (Free help) |
| **Elena Gilbert** | `elena@monash.edu` | `paid` | Paid tutor for Chemistry & Biology (RM 45/hr) |
| **Frank Castle** | `frank@monash.edu` | `paid` | Paid tutor for Economics, Accounting & Statistics (RM 60/hr) |
