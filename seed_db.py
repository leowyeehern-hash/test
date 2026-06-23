"""
seed_db.py — Seed StudyConnect database with Malaysian school subject users
Run:  python seed_db.py
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sqlite3
import os

DB_NAME = "students.db"

# ── Malaysian school subjects ──────────────────────────────────
SUBJECTS = [
    "Mathematics",
    "Additional Mathematics",
    "Bahasa Melayu",
    "English Language",
    "Physics",
    "Chemistry",
    "Biology",
    "Sejarah (History)",
    "Geografi (Geography)",
    "Pendidikan Islam",
    "Moral Education",
    "Accounting",
    "Economics",
    "Computer Science",
    "Science",
    "Business Studies",
    "Art (Seni Visual)",
]

# ── Seed users ─────────────────────────────────────────────────
# Each entry: (name, subject, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating, bio, contact_info)

SEED_USERS = [
    # ── Tutors (Providers) ──────────────────────────────────────
    (
        "Cikgu Azmi", "Mathematics", "MON_8AM,WED_8AM,FRI_8AM",
        "Algebra, Calculus, Trigonometry", "Statistics",
        "Provider", "Free Only", "Alumni (Mentor)", False, 4.8,
        "Retired mathematics teacher with 20 years of experience. Happy to help SPM students for free!",
        "azmi@studyconnect.my"
    ),
    (
        "Dr. Priya Nair", "Chemistry", "TUE_3PM,THU_3PM,SAT_10AM",
        "Organic Chemistry, Titration, Electrolysis", "Thermodynamics",
        "Provider", "Free Only", "Alumni (Mentor)", False, 4.9,
        "Chemistry PhD graduate. Specialises in SPM & STPM Chemistry. Volunteering to help SPM students for free.",
        "priya@chemtutor.my"
    ),
    (
        "Ahmad Fauzi", "Physics", "MON_6PM,WED_6PM,FRI_6PM",
        "Mechanics, Electromagnetism, Waves", "Nuclear Physics",
        "Provider", "Free Only", "Student (Peer)", False, 4.5,
        "Final-year Physics student at UM. Volunteer tutoring for SPM students.",
        "fauzi@um.edu.my"
    ),
    (
        "Tan Shu Qi", "Additional Mathematics", "SAT_9AM,SUN_9AM",
        "Differentiation, Integration, Vectors", "Statistics",
        "Provider", "Free Only", "Alumni (Mentor)", False, 4.7,
        "A+ in SPM Add Maths. Volunteer tutor offering proven exam strategies for free.",
        "shuqi.tutor@gmail.com"
    ),
    (
        "Nabilah Husna", "Bahasa Melayu", "MON_4PM,TUE_4PM,WED_4PM",
        "Karangan, Tatabahasa, Komsas", "Pemahaman",
        "Provider", "Free Only", "Student (Peer)", False, 4.3,
        "SPM BM scorer (A+). Offering free BM essay coaching for struggling students.",
        "nabilah@studyconnect.my"
    ),
    (
        "Marcus Lee", "English Language", "TUE_7PM,THU_7PM,SAT_2PM",
        "Essay Writing, Grammar, Comprehension", "Speaking",
        "Provider", "Free Only", "Alumni (Mentor)", False, 4.6,
        "MUET Band 6. English tutor specialising in SPM, MUET and IELTS preparation. Volunteer tutor.",
        "marcus@englishpro.my"
    ),
    (
        "Kavitha Devi", "Biology", "WED_2PM,FRI_2PM,SUN_10AM",
        "Cell Biology, Genetics, Ecology", "Physiology",
        "Provider", "Free Only", "Student (Peer)", False, 4.4,
        "Biology degree student at UPM. Free tutoring for SPM Bio, focus on memorisation techniques.",
        "kavitha@upm.edu.my"
    ),
    (
        "Wong Kai Ming", "Accounting", "MON_7PM,WED_7PM,SAT_9AM",
        "Double Entry, Financial Statements, Costing", "Budgeting",
        "Provider", "Free Only", "Alumni (Mentor)", False, 4.8,
        "ACCA qualified. Volunteering to tutor SPM Perakaunan and A-Level Accounting for free.",
        "kaiming@accatutor.my"
    ),
    (
        "Syafiq Hazwan", "Computer Science", "TUE_8PM,THU_8PM,SAT_3PM",
        "Programming, Algorithms, Database", "Networking",
        "Provider", "Free Only", "Student (Peer)", False, 4.2,
        "CS student at UTM. Tutoring SPM Sains Komputer — Python, pseudocode, databases.",
        "syafiq@utm.edu.my"
    ),
    (
        "Lim Jia Hao", "Economics", "MON_5PM,FRI_5PM,SUN_2PM",
        "Macroeconomics, Microeconomics, Demand & Supply", "International Trade",
        "Provider", "Free Only", "Alumni (Mentor)", False, 4.5,
        "Economics graduate. SPM & STPM Economics specialist. Volunteer tutoring.",
        "jiahao@ecotutor.my"
    ),
    (
        "Farah Nadia", "Sejarah (History)", "TUE_4PM,THU_4PM",
        "SPM History facts, Essay technique, Timeline", "World History",
        "Provider", "Free Only", "Student (Peer)", False, 4.1,
        "Scored A+ in SPM Sejarah. Sharing my memorisation framework for free.",
        "farah@studyconnect.my"
    ),
    (
        "Rajesh Kumar", "Science", "MON_4PM,WED_4PM,FRI_4PM",
        "Physics concepts, Chemistry basics, Biology", "Advanced topics",
        "Provider", "Free Only", "Student (Peer)", False, 4.0,
        "Form 5 student. Can help Form 3 students with PT3 Science preparation.",
        "rajesh@studyconnect.my"
    ),


    # ── Study Partners / Peers (Receivers, Free Only) ───────────
    (
        "Amirah Zainal", "Mathematics", "MON_3PM,WED_3PM",
        "Geometry, Number Patterns", "Calculus, Integration",
        "Receiver", "Free Only", "Student (Peer)", False, 3.5,
        "Form 5 student aiming for A in SPM Maths. Looking for a study buddy!",
        "amirah@student.my"
    ),
    (
        "Li Wei", "Physics", "TUE_4PM,SAT_10AM",
        "Waves, Optics", "Electricity, Mechanics",
        "Receiver", "Free Only", "Student (Peer)", False, 3.2,
        "Struggling with electricity chapter. Want to study together with someone at similar level.",
        "liwei@student.my"
    ),
    (
        "Nurul Ain", "Chemistry", "WED_5PM,SUN_3PM",
        "Acids & Bases", "Organic Chemistry, Electrolysis",
        "Receiver", "Free Only", "Student (Peer)", False, 3.8,
        "Love discussion-based study sessions! Looking for a Chemistry study partner.",
        "nurulain@student.my"
    ),
    (
        "Muhammad Hafiz", "Biology", "MON_7PM,THU_7PM",
        "Cell Biology", "Genetics, Ecology",
        "Receiver", "Free Only", "Student (Peer)", False, 3.4,
        "Prefer online group study. Looking for Bio friends for SPM 2025.",
        "hafiz@student.my"
    ),
    (
        "Chen Jie", "Additional Mathematics", "SAT_2PM,SUN_4PM",
        "Geometry, Trigonometry", "Integration, Differentiation",
        "Receiver", "Free Only", "Student (Peer)", False, 3.6,
        "Weekend study group for Add Maths? Count me in! Weak in calculus.",
        "chenjie@student.my"
    ),
    (
        "Siti Rahayu", "Bahasa Melayu", "TUE_5PM,FRI_5PM",
        "Komsas, Literature", "Karangan Formal",
        "Receiver", "Free Only", "Student (Peer)", False, 3.9,
        "Looking for a BM study partner especially for formal essay practice.",
        "siti@student.my"
    ),
    (
        "Vikram Singh", "English Language", "MON_8PM,WED_8PM",
        "Comprehension, Literature", "Essay Writing, Grammar",
        "Receiver", "Free Only", "Student (Peer)", False, 3.3,
        "Weak in English essay writing. Looking for a peer to practice with.",
        "vikram@student.my"
    ),
    (
        "Ng Wei Ting", "Accounting", "THU_6PM,SAT_11AM",
        "Ledger Entries", "Final Accounts, Costing",
        "Receiver", "Free Only", "Student (Peer)", False, 3.7,
        "SPM Perakaunan is hard! Looking for someone to do past-year papers together.",
        "weiting@student.my"
    ),
    (
        "Azlan Shah", "Economics", "TUE_6PM,SUN_5PM",
        "Demand & Supply, Market Structures", "Macroeconomics",
        "Receiver", "Free Only", "Student (Peer)", False, 3.5,
        "Prefer discussion-style study. Looking for Econ study buddy for STPM.",
        "azlan@student.my"
    ),
    (
        "Ong Kai Xin", "Computer Science", "FRI_7PM,SAT_4PM",
        "Programming logic, Boolean algebra", "Database, Networking",
        "Receiver", "Free Only", "Student (Peer)", False, 3.2,
        "SPM CS student. Looking for someone to practice coding with.",
        "kaixin@student.my"
    ),
    (
        "Priya Devi", "Moral Education", "WED_6PM,SAT_2PM",
        "Nilai Murni concepts", "Essay technique",
        "Receiver", "Free Only", "Student (Peer)", False, 3.8,
        "SPM Pendidikan Moral — need help with memorising nilai and essay structure.",
        "priya@student.my"
    ),
    (
        "Hakim Roslan", "Sejarah (History)", "MON_5PM,THU_5PM",
        "Perang Dunia, Tokoh", "Kronologi, Peta Minda",
        "Receiver", "Free Only", "Student (Peer)", False, 3.0,
        "Sejarah is so much to memorise! Need a study partner with good memory tricks.",
        "hakim@student.my"
    ),
    (
        "Grace Tan", "Science", "TUE_3PM,FRI_3PM",
        "Biology basics, Chemistry concepts", "Physics",
        "Receiver", "Free Only", "Student (Peer)", False, 3.6,
        "PT3 Science student. Looking for online study buddy — prefer Zoom sessions.",
        "grace@student.my"
    ),
]


def seed():
    print("=" * 55)
    print("  StudyConnect Database Seeder")
    print("  Malaysian School Subjects Edition")
    print("=" * 55)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Ensure table exists with all needed columns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        subject_id TEXT, time_slots TEXT,
        advantage TEXT, weakness TEXT,
        intent TEXT, fee_pref TEXT, role TEXT, privacy_mode BOOLEAN, rating REAL,
        email TEXT, email_verified INTEGER DEFAULT 0, google_id TEXT,
        contact_info TEXT, bio TEXT, profile_pic TEXT
    )
    """)

    # Safe migration: add columns if they don't exist
    new_cols = [
        ("email",          "TEXT"),
        ("email_verified", "INTEGER DEFAULT 0"),
        ("google_id",      "TEXT"),
        ("contact_info",   "TEXT"),
        ("bio",            "TEXT"),
        ("profile_pic",    "TEXT"),
    ]
    for col_name, col_type in new_cols:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass

    # Seed matches and messages tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_a TEXT, user_b TEXT, status TEXT DEFAULT 'pending'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT, receiver TEXT, content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE, token TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    print(f"\nSeeding {len(SEED_USERS)} users...\n")
    inserted = 0
    skipped  = 0

    for user in SEED_USERS:
        name, subject, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating, bio, contact_info = user
        try:
            cursor.execute("""
            INSERT INTO users (name, subject_id, time_slots, advantage, weakness, intent, fee_pref,
                               role, privacy_mode, rating, bio, contact_info, email_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (name, subject, time_slots, advantage, weakness, intent, fee_pref,
                  role, int(privacy_mode), rating, bio, contact_info))
            conn.commit()
            tag = "[TUTOR]" if intent == "Provider" else "[PEER] "
            print(f"  OK  {tag}  {name:<25} -- {subject}")
            inserted += 1
        except sqlite3.IntegrityError:
            print(f"  ⏭  Skipped (already exists): {name}")
            skipped += 1

    conn.close()
    print(f"\n{'─'*55}")
    print(f"  Done! {inserted} added, {skipped} skipped.")
    print(f"  Subjects covered: {len(SUBJECTS)}")
    print(f"  Tutors: {sum(1 for u in SEED_USERS if u[5] == 'Provider')}")
    print(f"  Study Partners: {sum(1 for u in SEED_USERS if u[5] == 'Receiver')}")
    print(f"{'─'*55}\n")


if __name__ == "__main__":
    seed()
