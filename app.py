"""
app.py — StudyConnect API
─────────────────────────────────────────────────────────────────
Endpoints:
  GET  /                          Health check
  POST /api/auth/google           Google Sign-In (verifies ID token)
  GET  /api/auth/confirm-email    Email confirmation (token link)
  POST /api/add_user              Register / update a user profile
  POST /api/match                 Run matching algorithm
  GET  /api/find-tutor            Browse tutors (optional ?subject=)
  GET  /api/find-peer             Browse study partners (optional ?subject=)
  GET  /api/subjects              List all available subjects
  POST /api/send_message          Send chat message (matched only)
  GET  /api/get_messages          Retrieve chat history
  GET  /api/stats                 Platform stats
  POST /api/confirm_match         Confirm / accept a match request
─────────────────────────────────────────────────────────────────
"""

import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from database import (
    create_table, get_users, save_or_update_user, connect,
    get_user_by_email, get_user_by_google_id,
    create_google_user, verify_user_email,
    save_email_token, get_email_by_token,
    get_tutors, get_peers,
)
from cloudflare_email import send_confirmation_email, send_welcome_email

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the frontend

# ── Secret key for token signing ──────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "studyconnect-dev-secret-change-in-prod")
serializer = URLSafeTimedSerializer(SECRET_KEY)

# ── Google OAuth Client ID ────────────────────────────────────
# Set via environment variable OR replace the placeholder below.
GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID",
    "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"  # ← Replace this
)

# ── Malaysian school subjects ─────────────────────────────────
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
    "Pendidikan Jasmani",
    "Music",
]

# Initialise DB tables (safe: uses CREATE IF NOT EXISTS)
create_table()


# ═══════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.route('/')
@app.route('/index.html')
def home():
    from flask import send_file
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_file(os.path.join(root_dir, 'index.html'))



# ═══════════════════════════════════════════════════════════════
#  AUTH — GOOGLE SIGN-IN
# ═══════════════════════════════════════════════════════════════

@app.route('/api/auth/google', methods=['POST'])
def google_signin():
    """
    Accepts a Google ID token from the frontend (via Google Identity Services).
    Verifies it, creates/fetches the user, and sends a confirmation email
    if the email has not yet been verified.

    Body: { "id_token": "<google_id_token>" }
    """
    data = request.json or {}
    id_token_str = data.get("id_token")

    if not id_token_str:
        return jsonify({"error": "Missing id_token"}), 400

    # ── Verify the token with Google ──────────────────────────
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        id_info = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except Exception as exc:
        # In dev/testing without a real client ID, allow a mock payload
        if os.environ.get("FLASK_ENV") == "development" or GOOGLE_CLIENT_ID.startswith("YOUR_"):
            # Accept a manually constructed payload for local dev
            id_info = data.get("dev_payload", {})
            if not id_info.get("sub"):
                return jsonify({
                    "error": "Google token verification failed",
                    "detail": str(exc),
                    "hint": "Set GOOGLE_CLIENT_ID env var or pass dev_payload for local testing",
                }), 401
        else:
            return jsonify({"error": "Invalid Google token", "detail": str(exc)}), 401

    google_id  = id_info.get("sub")
    email      = id_info.get("email", "")
    name       = id_info.get("name", email.split("@")[0])
    picture    = id_info.get("picture", "")

    if not google_id:
        return jsonify({"error": "Could not extract user info from Google token"}), 400

    # ── Create or fetch user ──────────────────────────────────
    user = create_google_user(name, email, google_id, profile_pic=picture)

    # ── Send confirmation email if not yet verified ───────────
    if not user.get("email_verified"):
        token = serializer.dumps(email, salt="email-confirm")
        save_email_token(email, token)
        send_confirmation_email(email, name, token)
        email_status = "confirmation_sent"
    else:
        email_status = "already_verified"

    return jsonify({
        "message"      : "Sign-in successful",
        "user"         : {
            "name"           : user.get("name"),
            "email"          : user.get("email"),
            "email_verified" : bool(user.get("email_verified")),
            "profile_pic"    : user.get("profile_pic", picture),
            "intent"         : user.get("intent", "Receiver"),
        },
        "email_status" : email_status,
    })


# ═══════════════════════════════════════════════════════════════
#  AUTH — EMAIL CONFIRMATION
# ═══════════════════════════════════════════════════════════════

@app.route('/api/auth/confirm-email', methods=['GET'])
def confirm_email():
    """
    Validates the emailed token and marks the user's email as verified.
    Called when user clicks the link in their confirmation email.
    """
    token = request.args.get("token", "")
    if not token:
        return _redirect_to_frontend("error", "Missing confirmation token.")

    try:
        email = serializer.loads(token, salt="email-confirm", max_age=86400)  # 24 h
    except SignatureExpired:
        return _redirect_to_frontend("error", "This link has expired. Please request a new one.")
    except BadSignature:
        return _redirect_to_frontend("error", "Invalid confirmation link.")

    # Confirm in DB
    db_email = get_email_by_token(token)
    if not db_email:
        return _redirect_to_frontend("error", "Token not found or already used.")

    verify_user_email(email)

    # Send welcome email
    user = get_user_by_email(email)
    if user:
        send_welcome_email(email, user.get("name", email))

    return _redirect_to_frontend("success", "Email confirmed! Welcome to StudyConnect.")


def _redirect_to_frontend(status, message):
    """Redirects user back to the index.html with a status message."""
    from flask import redirect
    frontend_url = os.environ.get("FRONTEND_URL", "/")
    return redirect(f"{frontend_url}?email_confirm={status}&msg={message}", code=302)


# ═══════════════════════════════════════════════════════════════
#  SUBJECTS LIST
# ═══════════════════════════════════════════════════════════════

@app.route('/api/subjects', methods=['GET'])
def list_subjects():
    return jsonify({"subjects": SUBJECTS})


# ═══════════════════════════════════════════════════════════════
#  FIND A TUTOR
# ═══════════════════════════════════════════════════════════════

@app.route('/api/find-tutor', methods=['GET'])
def find_tutor():
    """
    Returns a list of tutors (intent=Provider).
    Query params:
      ?subject=Mathematics    (optional filter)
      ?limit=20               (optional, default 50)
    """
    subject = request.args.get("subject", "").strip()
    limit   = int(request.args.get("limit", 50))

    tutors = get_tutors(subject=subject or None, limit=limit)

    # Privacy: hide contact unless matched (simplified — show contact if privacy_mode=False)
    for t in tutors:
        if t.get("privacy_mode"):
            t["contact_info"] = "HIDDEN — send a connect request to reveal"
        t.pop("google_id", None)  # Never expose internal IDs

    return jsonify({
        "count"  : len(tutors),
        "subject": subject or "All",
        "tutors" : tutors,
    })


# ═══════════════════════════════════════════════════════════════
#  FIND A STUDY PARTNER / PEER
# ═══════════════════════════════════════════════════════════════

@app.route('/api/find-peer', methods=['GET'])
def find_peer():
    """
    Returns study-buddy candidates (intent=Receiver, fee_pref=Free Only).
    Query params:
      ?subject=Physics    (optional)
      ?limit=20           (optional)
    """
    subject = request.args.get("subject", "").strip()
    limit   = int(request.args.get("limit", 50))

    peers = get_peers(subject=subject or None, limit=limit)

    for p in peers:
        if p.get("privacy_mode"):
            p["contact_info"] = "HIDDEN — send a connect request to reveal"
        p.pop("google_id", None)

    return jsonify({
        "count"  : len(peers),
        "subject": subject or "All",
        "peers"  : peers,
    })


# ═══════════════════════════════════════════════════════════════
#  MATCHING ALGORITHM (unchanged from v1)
# ═══════════════════════════════════════════════════════════════

def calculate_match(s1, s2):
    sub1 = str(s1.get('subject_id', '')).strip().upper()
    sub2 = str(s2.get('subject_id', '')).strip().upper()
    if sub1 != sub2:
        return 0, []

    score = 0
    reasons = []

    i1 = s1.get('intent', 'Unknown')
    i2 = s2.get('intent', 'Unknown')
    f1 = s1.get('fee_pref', 'Unknown')
    f2 = s2.get('fee_pref', 'Unknown')

    is_study_buddy_pair = False

    if i1 == 'Provider' and i2 == 'Provider':
        return 0, []
    elif i1 == 'Receiver' and i2 == 'Receiver':
        if f1 == 'Free Only' and f2 == 'Free Only':
            is_study_buddy_pair = True
            score += 35
            reasons.append("📚 Study Buddy Match: Both seeking peers! (+35)")
        else:
            return 0, []
    else:
        receiver_fee = f1 if i1 == 'Receiver' else f2
        provider_fee = f1 if i1 == 'Provider' else f2
        if receiver_fee == 'Free Only' and provider_fee == 'Paid Only':
            return 0, []
        elif receiver_fee == 'Free Only' and provider_fee == 'Free Only':
            score += 20
            reasons.append("🌱 Voluntarism Match: Free connection! (+20)")
        elif receiver_fee == 'Paid Only':
            score += 15
            reasons.append("💰 Premium Match: Paid Receiver (+15)")
            if provider_fee == 'Paid Only':
                score += 10
                reasons.append("🤝 Premium Deal: Paid Tutor (+10)")

    s1_adv  = [x.strip().lower() for x in str(s1.get('advantage', '')).split(",") if x.strip()]
    s1_weak = [x.strip().lower() for x in str(s1.get('weakness',  '')).split(",") if x.strip()]
    s2_adv  = [x.strip().lower() for x in str(s2.get('advantage', '')).split(",") if x.strip()]
    s2_weak = [x.strip().lower() for x in str(s2.get('weakness',  '')).split(",") if x.strip()]

    def check_complementary(adv_list, weak_list):
        for adv in adv_list:
            for weak in weak_list:
                if adv in weak or weak in adv:
                    return True
        return False

    is_complementary = (
        (i1 == 'Provider' and check_complementary(s1_adv, s2_weak)) or
        (i2 == 'Provider' and check_complementary(s2_adv, s1_weak))
    )

    has_shared_strength = any(
        a1 in a2 or a2 in a1 for a1 in s1_adv for a2 in s2_adv
    )

    if is_study_buddy_pair:
        if has_shared_strength:
            score += 20
            reasons.append("🤝 Buddy Synergy (+20)")
    else:
        if is_complementary and has_shared_strength:
            score += 55
            reasons.append("⚡ Ultimate Match (+55)")
        elif is_complementary:
            score += 45
            reasons.append("✓ Complementary Match (+45)")
        elif has_shared_strength:
            score += 25
            reasons.append("🤝 Shared Stack (+25)")
        else:
            score -= 10
            reasons.append("⚠ Skill Gap (-10)")

    fields = ['frequency', 'study_mode', 'group_size', 'grade_goal', 'study_style', 'resource_pref', 'language']
    matched_fields = []
    for field in fields:
        val1 = str(s1.get(field, 'Unknown')).strip().lower()
        val2 = str(s2.get(field, 'Unknown')).strip().lower()
        if val1 != 'unknown' and val1 == val2:
            score += 2
            matched_fields.append(field.replace("_", " ").title())
    if matched_fields:
        reasons.append(f"✓ Shared Habits ({', '.join(matched_fields)}) (+{len(matched_fields)*2})")

    r1 = s1.get('role', 'Unknown')
    r2 = s2.get('role', 'Unknown')
    if r1 == 'Student (Peer)' and r2 == 'Student (Peer)':
        score += 5
    elif r1 == 'Alumni (Mentor)' and r2 == 'Alumni (Mentor)':
        score += 5

    user_rating = float(s2.get('rating', 3.0))
    if user_rating >= 4.5:
        score += 10
        reasons.append("★ Top-Rated Peer (+10)")
    elif user_rating < 3.0:
        score -= 15
        reasons.append("⚠ Low Peer Rating (-15)")

    return max(0, min(score, 100)), reasons


# ═══════════════════════════════════════════════════════════════
#  MATCH API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/match', methods=['POST'])
def match_api():
    if 'user_info' not in request.json:
        return jsonify({"error": "Missing user_info"}), 400
    if 'name' not in request.json['user_info']:
        return jsonify({"error": "Missing name"}), 400

    user_data = request.json['user_info']
    required_fields = ['intent', 'fee_pref', 'role', 'rating', 'advantage', 'weakness', 'time_slots']
    for field in required_fields:
        if field not in user_data:
            user_data[field] = "Unknown" if field != 'rating' else 3.0

    all_students = get_users()
    all_fields   = ['frequency', 'study_mode', 'group_size', 'grade_goal', 'study_style', 'resource_pref', 'language']
    match_results = []

    for target in all_students:
        for field in all_fields:
            if field not in target or target[field] is None:
                target[field] = "Unknown"
        if target.get('name') == user_data.get('name'):
            continue
        score, reasons = calculate_match(user_data, target)
        if score > 0:
            match_results.append({'target': target, 'score': score, 'reasons': reasons})

    match_results.sort(key=lambda x: x['score'], reverse=True)

    for res in match_results:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)",
            (user_data['name'], res['target']['name'], res['target']['name'], user_data['name'])
        )
        status_row = cursor.fetchone()
        conn.close()
        is_matched = status_row and status_row[0] == 'matched'
        if res['target'].get('privacy_mode') and not is_matched:
            res['target']['contact_info'] = "HIDDEN"
        res['target'].pop('google_id', None)

    return jsonify(match_results)


# ═══════════════════════════════════════════════════════════════
#  ADD / UPDATE USER
# ═══════════════════════════════════════════════════════════════

@app.route('/api/add_user', methods=['POST'])
def add_user():
    data = request.json or {}
    if 'user_info' in data:
        data = data['user_info']
    try:
        save_or_update_user(
            data['name'],
            data['subject_id'],
            data['time_slots'],
            data['advantage'],
            data['weakness'],
            data['intent'],
            data['fee_pref'],
            data['role'],
            data['privacy_mode'],
            data.get('rating', 3.0),
            email=data.get('email'),
            contact_info=data.get('contact_info'),
            bio=data.get('bio'),
        )
        return jsonify({"message": "User saved successfully"})
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400


# ═══════════════════════════════════════════════════════════════
#  MESSAGING
# ═══════════════════════════════════════════════════════════════

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json or {}
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)",
        (data['sender'], data['receiver'], data['receiver'], data['sender'])
    )
    res = cursor.fetchone()
    if not res or res[0] != 'matched':
        conn.close()
        return jsonify({"error": "Chat unavailable: You are not yet matched."}), 403
    cursor.execute(
        "INSERT INTO messages (sender, receiver, content) VALUES (?, ?, ?)",
        (data['sender'], data['receiver'], data['content'])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Message sent successfully."})


@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    u1 = request.args.get('user1')
    u2 = request.args.get('user2')
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sender, content, timestamp FROM messages "
        "WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp ASC",
        (u1, u2, u2, u1)
    )
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"sender": r[0], "content": r[1], "time": r[2]} for r in rows])


# ═══════════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════════

@app.route('/api/stats', methods=['GET'])
def get_stats():
    users_list = get_users()
    if not users_list:
        return jsonify({"message": "No users in database yet"})
    df = pd.DataFrame(users_list)
    subject_counts = df['subject_id'].value_counts().to_dict() if 'subject_id' in df.columns else {}
    avg_rating = float(df['rating'].mean()) if 'rating' in df.columns else 0.0
    tutors_count = int(df[df['intent'] == 'Provider'].shape[0]) if 'intent' in df.columns else 0
    peers_count  = int(df[(df['intent'] == 'Receiver') & (df['fee_pref'] == 'Free Only')].shape[0]) if 'intent' in df.columns else 0
    return jsonify({
        "total_users"          : len(df),
        "tutors"               : tutors_count,
        "study_partners"       : peers_count,
        "subject_distribution" : subject_counts,
        "average_rating"       : round(avg_rating, 2),
        "available_subjects"   : SUBJECTS,
    })


# ═══════════════════════════════════════════════════════════════
#  CONFIRM MATCH
# ═══════════════════════════════════════════════════════════════

@app.route('/api/confirm_match', methods=['POST'])
def confirm_match():
    data   = request.json or {}
    me     = data.get('my_name')
    target = data.get('target_name')
    if not me or not target:
        return jsonify({"error": "my_name and target_name are required"}), 400

    conn   = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)",
        (target, me, me, target)
    )
    res = cursor.fetchone()

    if res and res[0] == 'pending':
        cursor.execute(
            "UPDATE matches SET status='matched' WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)",
            (target, me, me, target)
        )
        msg = "Match successful!"
    else:
        cursor.execute(
            "SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)",
            (me, target, target, me)
        )
        existing = cursor.fetchone()
        if not existing:
            cursor.execute(
                "INSERT INTO matches (user_a, user_b, status) VALUES (?, ?, 'pending')",
                (me, target)
            )
            msg = "Request sent."
        elif existing[0] == 'matched':
            msg = "You are already matched."
        else:
            msg = "Request already sent; please wait for confirmation."

    conn.commit()
    conn.close()
    return jsonify({"message": msg})


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True)