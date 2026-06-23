"""
cloudflare_email.py
─────────────────────────────────────────────────────────────────
Sends transactional emails via Cloudflare MailChannels API.

Setup (one-time):
  1. Add your domain to Cloudflare.
  2. Add this DNS TXT record to your domain:
       Name:  _mailchannels
       Value: v=mc1 cfid=<your-cf-worker-subdomain>.workers.dev
  3. Set environment variables:
       CF_FROM_EMAIL   = noreply@yourdomain.com
       APP_BASE_URL    = https://yourdomain.com   (or http://localhost:5000 for dev)
  4. Optionally deploy cloudflare-worker.js as a Worker that acts as a
     proxy so you can add DKIM signing (see cloudflare-worker.js).

For local development: emails are printed to the console and the
MailChannels call is attempted (it will fail gracefully on localhost).
─────────────────────────────────────────────────────────────────
"""

import os
import requests

# ── Configuration ─────────────────────────────────────────────
CF_FROM_EMAIL = os.environ.get("CF_FROM_EMAIL", "noreply@studyconnect.example.com")
CF_FROM_NAME  = "StudyConnect"
APP_BASE_URL  = os.environ.get("APP_BASE_URL", "http://localhost:5000")

MAILCHANNELS_URL = "https://api.mailchannels.net/tx/v1/send"

# ── HTML Email Templates ───────────────────────────────────────

def _base_template(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ margin:0; padding:0; background:#0a0a14; font-family:'Segoe UI',Arial,sans-serif; color:#e2e8f0; }}
  .wrap {{ max-width:560px; margin:40px auto; background:linear-gradient(145deg,#13131f,#1e1b4b22);
           border:1px solid rgba(139,92,246,0.3); border-radius:20px; overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,#7c3aed,#2563eb); padding:32px 40px; text-align:center; }}
  .header h1 {{ margin:0; font-size:28px; color:#fff; letter-spacing:-0.5px; }}
  .header p  {{ margin:6px 0 0; color:rgba(255,255,255,0.8); font-size:14px; }}
  .body {{ padding:36px 40px; }}
  .body h2 {{ color:#a78bfa; font-size:22px; margin:0 0 12px; }}
  .body p  {{ color:#94a3b8; line-height:1.7; margin:0 0 16px; }}
  .btn {{ display:inline-block; background:linear-gradient(135deg,#7c3aed,#2563eb);
          color:#fff; padding:14px 32px; border-radius:10px; text-decoration:none;
          font-weight:700; font-size:15px; margin:8px 0 20px; }}
  .footer {{ background:rgba(255,255,255,0.03); padding:20px 40px; border-top:1px solid rgba(255,255,255,0.06); }}
  .footer p {{ color:#475569; font-size:12px; margin:0; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>📚 StudyConnect</h1>
    <p>Connect · Learn · Grow</p>
  </div>
  <div class="body">{body_html}</div>
  <div class="footer">
    <p>© 2025 StudyConnect. You received this email because you signed up at StudyConnect.</p>
    <p>If you didn't request this, please ignore this email.</p>
  </div>
</div>
</body>
</html>"""


def _confirmation_body(name: str, confirm_url: str) -> str:
    return f"""
    <h2>Confirm Your Email ✉️</h2>
    <p>Hi <strong style="color:#e2e8f0">{name}</strong>! Welcome to StudyConnect — Malaysia's smartest study matching platform.</p>
    <p>Please confirm your email address to unlock access to tutors, study partners, and more.</p>
    <a href="{confirm_url}" class="btn">✅ Confirm My Email</a>
    <p style="font-size:13px;color:#64748b;">This link expires in <strong>24 hours</strong>. If you didn't create an account, you can safely ignore this email.</p>
    <p style="font-size:13px;color:#64748b;">Or copy this link: <br><code style="color:#a78bfa;word-break:break-all;">{confirm_url}</code></p>
    """


def _welcome_body(name: str) -> str:
    return f"""
    <h2>Welcome to StudyConnect! 🎉</h2>
    <p>Hi <strong style="color:#e2e8f0">{name}</strong>! Your email is verified. You're all set.</p>
    <p>Here's what you can do next:</p>
    <ul style="color:#94a3b8;line-height:2;">
      <li>🔍 <strong style="color:#e2e8f0">Find a Tutor</strong> — Browse expert tutors by subject</li>
      <li>🤝 <strong style="color:#e2e8f0">Find a Study Partner</strong> — Match with peers for free collaborative study</li>
      <li>💬 <strong style="color:#e2e8f0">Chat</strong> — Message your matches directly in-app</li>
    </ul>
    <a href="{APP_BASE_URL}" class="btn">🚀 Start Exploring</a>
    """


# ── Sender ─────────────────────────────────────────────────────

def _send(to_email: str, to_name: str, subject: str, html: str, text: str) -> bool:
    """Send email via Cloudflare MailChannels. Falls back to console log."""
    payload = {
        "personalizations": [{"to": [{"email": to_email, "name": to_name}]}],
        "from": {"email": CF_FROM_EMAIL, "name": CF_FROM_NAME},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html",  "value": html},
        ],
    }

    # Always log to console (useful for development)
    print(f"\n{'━'*60}")
    print(f"[EMAIL] To:      {to_email}")
    print(f"[EMAIL] Subject: {subject}")
    print(f"[EMAIL] From:    {CF_FROM_EMAIL}")
    print(f"{'━'*60}\n")

    try:
        resp = requests.post(MAILCHANNELS_URL, json=payload, timeout=10)
        if resp.status_code in (200, 202):
            print(f"[EMAIL] ✅ Delivered via MailChannels ({resp.status_code})")
            return True
        else:
            print(f"[EMAIL] ⚠️  MailChannels returned {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.exceptions.RequestException as exc:
        print(f"[EMAIL] ℹ️  MailChannels unreachable (expected in dev): {exc}")
        return False  # Graceful fail — don't crash the app


# ── Public API ─────────────────────────────────────────────────

def send_confirmation_email(to_email: str, name: str, token: str) -> bool:
    confirm_url = f"{APP_BASE_URL}/api/auth/confirm-email?token={token}"
    html = _base_template(_confirmation_body(name, confirm_url))
    text = (
        f"Hi {name}! Confirm your StudyConnect account:\n{confirm_url}\n"
        "(Link expires in 24 hours)"
    )
    return _send(to_email, name, "Confirm your StudyConnect account 📚", html, text)


def send_welcome_email(to_email: str, name: str) -> bool:
    html = _base_template(_welcome_body(name))
    text = f"Hi {name}! Your StudyConnect account is confirmed. Visit: {APP_BASE_URL}"
    return _send(to_email, name, "Welcome to StudyConnect! 🎉", html, text)
