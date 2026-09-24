/**
 * Pool 2027 submission notification — Vercel Serverless Function
 * Called by a Supabase Database Webhook on INSERT to pool_2027_submissions.
 *
 * Required env vars (set in Vercel dashboard):
 *   RESEND_API_KEY         — Resend API key (re_xxxxxxxx)
 *   POOL_WEBHOOK_SECRET    — shared secret set in the Supabase webhook header
 *
 * The Supabase webhook should send:
 *   POST /api/pool-submission-notify
 *   Header: x-webhook-secret: <POOL_WEBHOOK_SECRET>
 *   Body: Supabase webhook payload (type, table, record, ...)
 */

const RESEND_API  = 'https://api.resend.com/emails';
const FROM        = 'Pool 2027 <onboarding@resend.dev>';
const NOTIFY_TO   = 'justin.do@hotmail.com';

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  // Verify shared secret
  const secret = process.env.POOL_WEBHOOK_SECRET;
  if (secret && req.headers['x-webhook-secret'] !== secret) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'RESEND_API_KEY not configured' });

  const payload = req.body || {};
  // Supabase sends { type: 'INSERT', table: '...', record: {...}, ... }
  const record = payload.record || payload;

  const name     = record.name     || '(unknown)';
  const teamName = record.team_name || '—';
  const email    = record.email    || '—';
  const paid     = record.paid ? '💰 Paid' : '🎮 Free';
  const capUsed  = record.cap_used ? `$${(record.cap_used / 1_000_000).toFixed(2)}M` : '—';
  const roster   = record.roster   || {};
  const fSlugs   = (roster.F || []).join(', ') || '—';
  const dSlugs   = (roster.D || []).join(', ') || '—';
  const gSlugs   = (roster.G || []).join(', ') || '—';

  const html = `
    <h2 style="font-family:sans-serif;color:#1e3a8a;">🏒 New Pool 2027 Submission</h2>
    <table style="font-family:sans-serif;font-size:15px;border-collapse:collapse;">
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Name</td><td style="padding:4px 0;font-weight:600;">${esc(name)}</td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Team name</td><td style="padding:4px 0;font-weight:600;">${esc(teamName)}</td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Email</td><td style="padding:4px 0;">${esc(email)}</td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Entry</td><td style="padding:4px 0;">${paid}</td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Cap used</td><td style="padding:4px 0;">${capUsed}</td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;vertical-align:top;">Forwards</td><td style="padding:4px 0;font-size:13px;color:#374151;">${esc(fSlugs)}</td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;vertical-align:top;">Defence</td><td style="padding:4px 0;font-size:13px;color:#374151;">${esc(dSlugs)}</td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#6b7280;vertical-align:top;">Goalies</td><td style="padding:4px 0;font-size:13px;color:#374151;">${esc(gSlugs)}</td></tr>
    </table>
    <p style="font-family:sans-serif;font-size:13px;color:#9ca3af;margin-top:16px;">
      <a href="https://parieurdiscipline.com/pool-2027/standings/" style="color:#2563eb;">View standings</a>
    </p>`;

  const emailRes = await fetch(RESEND_API, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from: FROM,
      to: [NOTIFY_TO],
      subject: `🏒 New entry: ${teamName} (${name})`,
      html,
    }),
  });

  if (!emailRes.ok) {
    const err = await emailRes.text();
    console.error('Resend error:', err);
    return res.status(500).json({ error: 'Email send failed', details: err });
  }

  return res.status(200).json({ ok: true });
};

function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
