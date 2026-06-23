import requests
import random

# Malaysian school subjects
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
    "Art (Seni Visual)",
    "Business Studies",
    "Science",
]

INTENTS   = ["Provider", "Receiver"]
SKILLS    = [
    "Algebra", "Calculus", "Essay Writing", "Organic Chemistry",
    "Mechanics", "Data Analysis", "Grammar", "Trigonometry",
    "Electromagnetism", "Cell Biology", "Accounting Principles",
    "Macroeconomics", "Coding", "Statistics", "Titration",
]
TIME_SLOTS = [
    "MON_9AM,WED_2PM",
    "TUE_10AM,THU_3PM",
    "MON_6PM,FRI_4PM",
    "SAT_10AM,SUN_2PM",
    "WED_8AM,FRI_12PM",
]
FEE_PREFS  = ["Free Only", "Free Only", "Free Only", "Paid Only"]  # bias toward free
ROLES      = ["Student (Peer)", "Student (Peer)", "Alumni (Mentor)"]
LANGUAGES  = ["English", "Bahasa Melayu", "Both"]
STUDY_MODES = ["Online", "In-Person", "Both"]
GRADE_GOALS = ["A+", "A", "B+", "Pass"]

# Realistic Malaysian student names
NAMES = [
    "Amirah Binti Zainal", "Rajesh Kumar", "Li Wei", "Nurul Ain",
    "Muhammad Hafiz", "Priya Devi", "Chen Jie", "Siti Rahayu",
    "Ahmad Fauzi", "Kavitha Nair", "Wong Mei Ling", "Syafiq Hazwan",
    "Tan Shu Qi", "Nabilah Husna", "Vikram Singh", "Ong Kai Xin",
    "Farah Nadia", "Lim Jia Hao", "Azlan Shah", "Ng Wei Ting",
]

def generate_and_add(api_url="http://127.0.0.1:5000", count=20):
    print(f"Generating {count} virtual students with Malaysian school subjects...")
    added = 0
    for i in range(count):
        subject   = random.choice(SUBJECTS)
        intent    = random.choice(INTENTS)
        fee_pref  = random.choice(FEE_PREFS) if intent == "Provider" else "Free Only"
        adv_skills = random.sample(SKILLS, k=random.randint(1, 3))
        weak_skills = random.sample(SKILLS, k=random.randint(1, 2))
        name = random.choice(NAMES) + f" {i+1}"

        user = {
            "name"        : name,
            "subject_id"  : subject,
            "time_slots"  : random.choice(TIME_SLOTS),
            "advantage"   : ", ".join(adv_skills),
            "weakness"    : ", ".join(weak_skills),
            "intent"      : intent,
            "fee_pref"    : fee_pref,
            "role"        : random.choice(ROLES),
            "privacy_mode": random.choice([True, False, False]),  # bias public
            "rating"      : round(random.uniform(3.0, 5.0), 1),
            "language"    : random.choice(LANGUAGES),
            "study_mode"  : random.choice(STUDY_MODES),
            "grade_goal"  : random.choice(GRADE_GOALS),
            "bio"         : f"Studying {subject}. Looking to {'teach' if intent == 'Provider' else 'learn'}.",
        }

        try:
            resp = requests.post(f"{api_url}/api/add_user", json=user, timeout=5)
            print(f"  [{resp.status_code}] Added {user['name']} — {subject} ({intent})")
            added += 1
        except Exception as e:
            print(f"  [ERR] Could not add {user['name']}: {e}")

    print(f"\nDone! {added}/{count} students added.")

if __name__ == "__main__":
    generate_and_add()