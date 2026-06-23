/**
 * cloudflare-worker.js — StudyConnect Email Worker
 * ─────────────────────────────────────────────────
 * Deploy this as a Cloudflare Worker to send emails
 * via MailChannels with DKIM signing support.
 *
 * DEPLOY STEPS:
 *  1. Go to dash.cloudflare.com → Workers & Pages → Create Worker
 *  2. Paste this file content into the editor
 *  3. Set Worker name: "studyconnect-mailer"
 *  4. Add Secret: WORKER_SECRET = (any random string you choose)
 *  5. Set APP_BASE_URL = https://yourdomain.com
 *  6. Add your domain's DNS TXT record:
 *       Name:  _mailchannels
 *       Value: v=mc1 cfid=studyconnect-mailer.<your-cf-subdomain>.workers.dev
 *  7. Update APP_BASE_URL in cloudflare_email.py to point to your Flask app
 *
 * Flask app calls this Worker at:  POST https://studyconnect-mailer.<subdomain>.workers.dev/send
 * with Authorization: Bearer <WORKER_SECRET>
 */

const ALLOWED_ORIGIN = "*"; // Restrict to your domain in production

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // Auth check
    const authHeader = request.headers.get("Authorization") || "";
    const token = authHeader.replace("Bearer ", "").trim();
    if (env.WORKER_SECRET && token !== env.WORKER_SECRET) {
      return new Response("Unauthorized", { status: 401 });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response("Invalid JSON", { status: 400 });
    }

    const { to_email, to_name, subject, html, text } = body;
    if (!to_email || !subject) {
      return new Response("Missing required fields: to_email, subject", { status: 422 });
    }

    const fromEmail = env.FROM_EMAIL || "noreply@studyconnect.example.com";
    const fromName  = "StudyConnect";

    const mailPayload = {
      personalizations: [
        {
          to: [{ email: to_email, name: to_name || to_email }],
          // Optional DKIM — add your key as a Worker Secret named DKIM_PRIVATE_KEY
          ...(env.DKIM_PRIVATE_KEY && env.DKIM_SELECTOR && {
            dkim_domain: new URL(`https://${fromEmail.split("@")[1]}`).hostname,
            dkim_selector: env.DKIM_SELECTOR,
            dkim_private_key: env.DKIM_PRIVATE_KEY,
          }),
        },
      ],
      from:    { email: fromEmail, name: fromName },
      subject: subject,
      content: [
        { type: "text/plain", value: text  || subject },
        { type: "text/html",  value: html  || `<p>${text || subject}</p>` },
      ],
    };

    const mcResponse = await fetch("https://api.mailchannels.net/tx/v1/send", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(mailPayload),
    });

    if (mcResponse.status === 202) {
      return new Response(JSON.stringify({ ok: true, message: "Email sent" }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        },
      });
    }

    const errText = await mcResponse.text();
    return new Response(
      JSON.stringify({ ok: false, status: mcResponse.status, error: errText }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        },
      }
    );
  },
};
