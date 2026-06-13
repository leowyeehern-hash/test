import sys
import os
import json
import random
from werkzeug.security import generate_password_hash

# Add backend directory to sys.path at index 0 to override root files
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from database import (
    init_db,
    create_user,
    save_or_update_profile,
    create_review,
    send_message,
    create_help_request
)

def seed():
    print("Initializing Database...")
    init_db()

    password_hash = generate_password_hash("password123")

    # 1. Create Users
    users_data = [
        {"username": "admin", "email": "admin@studyconnect.com", "role": "admin"},
        {"username": "Alice Tan", "email": "alice@monash.edu", "role": "student"},
        {"username": "Bob Lim", "email": "bob@monash.edu", "role": "student"},
        {"username": "Charlie Song", "email": "charlie@monash.edu", "role": "volunteer"},
        {"username": "Dana Vance", "email": "dana@monash.edu", "role": "volunteer"},
        {"username": "Elena Gilbert", "email": "elena@monash.edu", "role": "paid"},
        {"username": "Frank Castle", "email": "frank@monash.edu", "role": "paid"},
    ]

    uids = {}
    print("Seeding Users...")
    for u in users_data:
        uid = create_user(u["username"], u["email"], password_hash, u["role"])
        uids[u["username"]] = uid
        print(f"  Created user: {u['username']} (ID: {uid}, Role: {u['role']})")

    # 2. Seed Profiles
    profiles_data = {
        "admin": {
            "university": "Monash University",
            "course": "Administration",
            "year": "Postgraduate",
            "bio": "System administrator for StudyConnect.",
            "subjects": [],
            "schedule": {},
        },
        "Alice Tan": {
            "university": "Monash University",
            "course": "Computer Science",
            "year": "1st Year",
            "bio": "Freshman CS student struggling with algebra and physics. Love hiking and coffee.",
            "subjects": ["Mathematics", "Physics"],
            "schedule": {
                "Monday": ["9am", "10am", "2pm", "3pm"],
                "Wednesday": ["10am", "11am", "4pm", "5pm"],
                "Friday": ["9am", "10am", "12pm", "1pm"],
            },
            "learning_style": "Visual",
            "strengths": "Python coding, report formatting",
        },
        "Bob Lim": {
            "university": "Monash University",
            "course": "Business Administration",
            "year": "2nd Year",
            "bio": "Looking for help with Accounting and Economics before the midterms.",
            "subjects": ["Accounting", "Economics"],
            "schedule": {
                "Tuesday": ["10am", "11am", "2pm", "3pm"],
                "Thursday": ["10am", "11am", "4pm", "5pm"],
            },
            "learning_style": "Reading/Writing",
            "strengths": "Presentation skills",
        },
        "Charlie Song": {
            "university": "Monash University",
            "course": "Mechanical Engineering",
            "year": "3rd Year",
            "bio": "Enthusiastic about math and physics. Happy to help peers review calculus sheets for free!",
            "subjects": ["Mathematics", "Physics"],
            "schedule": {
                "Monday": ["9am", "10am", "2pm", "3pm", "6pm", "7pm"],
                "Wednesday": ["10am", "11am", "4pm", "5pm", "6pm", "7pm"],
                "Friday": ["9am", "10am", "3pm", "4pm"],
            },
            "learning_style": "Kinesthetic",
            "strengths": "Calculus, Solid Mechanics, CAD drawing",
            "rate": 0,
            "experience": "Tutored peers during college. Led calculus review workshops.",
            "max_students": 4,
        },
        "Dana Vance": {
            "university": "Monash University",
            "course": "Software Engineering",
            "year": "4th Year",
            "bio": "Software engineer intern. Ready to tutor programming (Python, JS, Java) and statistics.",
            "subjects": ["Programming", "Data Science", "Statistics"],
            "schedule": {
                "Monday": ["6pm", "7pm", "8pm"],
                "Tuesday": ["6pm", "7pm", "8pm"],
                "Thursday": ["6pm", "7pm", "8pm"],
                "Saturday": ["10am", "11am", "12pm", "2pm", "3pm"],
            },
            "learning_style": "Kinesthetic",
            "strengths": "Web development, database architecture",
            "rate": 0,
            "experience": "Voted best helper in CodeClub Monash. 2 years web dev experience.",
            "max_students": 5,
        },
        "Elena Gilbert": {
            "university": "Monash University",
            "course": "Medicinal Chemistry",
            "year": "3rd Year",
            "bio": "Tutoring organic chemistry and cell biology. Providing custom summary notes.",
            "subjects": ["Chemistry", "Biology"],
            "schedule": {
                "Wednesday": ["2pm", "3pm", "4pm"],
                "Friday": ["10am", "11am", "2pm", "3pm"],
                "Sunday": ["10am", "11am", "2pm", "3pm"],
            },
            "learning_style": "Visual",
            "strengths": "Laboratory reporting, chemical reactions diagramming",
            "rate": 45.0,
            "experience": "Private home tuition tutor for 2 years. Got A+ in all chem units.",
            "max_students": 3,
        },
        "Frank Castle": {
            "university": "University of Malaya",
            "course": "Applied Economics",
            "year": "Postgraduate",
            "bio": "Teaching macro/micro economics, accounting, and financial management.",
            "subjects": ["Economics", "Accounting", "Statistics"],
            "schedule": {
                "Tuesday": ["2pm", "3pm", "4pm", "5pm"],
                "Thursday": ["2pm", "3pm", "4pm", "5pm"],
                "Saturday": ["9am", "10am", "11am", "2pm", "3pm"],
            },
            "learning_style": "Auditory",
            "strengths": "Financial modeling, econometrics",
            "rate": 60.0,
            "experience": "Teaching Assistant for college level economics. Professional tutor.",
            "max_students": 6,
        },
    }

    print("Seeding Profiles...")
    for username, p_data in profiles_data.items():
        uid = uids[username]
        save_or_update_profile(uid, p_data)
        print(f"  Profile set for: {username}")

    # 3. Seed Reviews
    print("Seeding Reviews...")
    reviews_data = [
        {"reviewer": "Alice Tan", "reviewee": "Charlie Song", "rating": 5.0, "comment": "Charlie explains derivatives really well! Highly recommend."},
        {"reviewer": "Bob Lim", "reviewee": "Frank Castle", "rating": 4.5, "comment": "Helped me pass my accounting mock test. Worth the hourly rate."},
        {"reviewer": "Alice Tan", "reviewee": "Elena Gilbert", "rating": 4.0, "comment": "Elena has great chemistry notes. Very structured session."},
    ]

    for rev in reviews_data:
        create_review(
            reviewer_id=uids[rev["reviewer"]],
            reviewee_id=uids[rev["reviewee"]],
            rating=rev["rating"],
            comment=rev["comment"]
        )
        print(f"  Review added: {rev['reviewer']} -> {rev['reviewee']}")

    # 4. Seed Messages
    print("Seeding Messages...")
    msgs = [
        {"sender": "Alice Tan", "receiver": "Charlie Song", "content": "Hi Charlie! I saw you tutor Mathematics. Are you free this Monday morning?"},
        {"sender": "Charlie Song", "receiver": "Alice Tan", "content": "Hi Alice! Yes, I am free between 9am and 11am on Monday. What topics are you looking to review?"},
        {"sender": "Alice Tan", "receiver": "Charlie Song", "content": "I need some help reviewing calculus limits and linear functions."},
        {"sender": "Bob Lim", "receiver": "Frank Castle", "content": "Hello Frank, I would like to schedule an accounting lesson. Is RM 60 your fixed rate?"},
    ]

    for msg in msgs:
        send_message(
            sender_id=uids[msg["sender"]],
            receiver_id=uids[msg["receiver"]],
            content=msg["content"]
        )
        print(f"  Message: {msg['sender']} -> {msg['receiver']}")

    # 5. Seed Help Requests
    print("Seeding Help Requests...")
    reqs = [
        {
            "student": "Alice Tan",
            "tutor": "Charlie Song",
            "subject": "Mathematics",
            "topic": "Calculus Limits",
            "description": "Struggling with delta-epsilon limit definitions and solving exam questions.",
            "type": "Exam Prep",
            "urgency": "High"
        },
        {
            "student": "Bob Lim",
            "tutor": "Frank Castle",
            "subject": "Accounting",
            "topic": "Ledger Bookkeeping",
            "description": "Struggling to balance trial balance sheet assets and liabilities columns.",
            "type": "General Learning",
            "urgency": "Medium"
        }
    ]

    for req in reqs:
        create_help_request(
            student_id=uids[req["student"]],
            tutor_id=uids[req["tutor"]],
            subject=req["subject"],
            topic=req["topic"],
            description=req["description"],
            req_type=req["type"],
            urgency=req["urgency"]
        )
        print(f"  Help Request created: {req['student']} -> {req['tutor']}")

    print("\nDatabase Seeding Completed Successfully!")

if __name__ == "__main__":
    seed()
