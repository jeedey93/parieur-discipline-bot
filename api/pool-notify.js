/**
 * Pool 2027 notifications — Vercel Serverless Function
 * Handles two cases based on `type` in the request body or header:
 *
 *   type = "submission"  — called by Supabase webhook on INSERT/UPDATE
 *   type = "feedback"    — called by the Report an Issue modal
 *
 * Required env vars: RESEND_API_KEY, POOL_WEBHOOK_SECRET
 *
 * POST /api/pool-notify
 */

const RESEND_API = 'https://api.resend.com/emails';
const FROM       = 'Pool 2027 <onboarding@resend.dev>';
const NOTIFY_TO  = 'justin.do@hotmail.com';

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-webhook-secret');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'RESEND_API_KEY not configured' });

  const body = req.body || {};

  // ── Submission notification (from Supabase webhook) ──────────────────────
  // Supabase webhooks send { type: 'INSERT'|'UPDATE', record: {...} }
  // We also detect it by presence of x-webhook-secret header
  const isWebhook = !!req.headers['x-webhook-secret'];
  if (isWebhook) {
    const secret = process.env.POOL_WEBHOOK_SECRET;
    if (secret && req.headers['x-webhook-secret'] !== secret) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    const record   = body.record || body;
    const name     = record.name      || '(unknown)';
    const teamName = record.team_name || '—';
    const email    = record.email     || '—';
    const paid     = record.paid ? '💰 Paid' : '🎮 Free';
    const capUsed  = record.cap_used ? `$${(record.cap_used / 1_000_000).toFixed(2)}M` : '—';
    const roster   = record.roster || {};
    const fSlugs   = (roster.F || []).join(', ') || '—';
    const dSlugs   = (roster.D || []).join(', ') || '—';
    const gSlugs   = (roster.G || []).join(', ') || '—';
    const verb     = body.type === 'UPDATE' ? 'Updated' : 'New';

    const html = `
      <h2 style="font-family:sans-serif;color:#1e3a8a;">🏒 ${verb} Pool 2027 Submission</h2>
      <table style="font-family:sans-serif;font-size:15px;border-collapse:collapse;">
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Name</td><td style="font-weight:600;">${esc(name)}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Team name</td><td style="font-weight:600;">${esc(teamName)}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Email</td><td>${esc(email)}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Entry</td><td>${paid}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;">Cap used</td><td>${capUsed}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;vertical-align:top;">Forwards</td><td style="font-size:13px;color:#374151;">${esc(fSlugs)}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;vertical-align:top;">Defence</td><td style="font-size:13px;color:#374151;">${esc(dSlugs)}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7280;vertical-align:top;">Goalies</td><td style="font-size:13px;color:#374151;">${esc(gSlugs)}</td></tr>
      </table>
      <p style="font-family:sans-serif;font-size:13px;color:#9ca3af;margin-top:16px;">
        <a href="https://parieurdiscipline.com/pool-2027/standings/" style="color:#2563eb;">View standings</a>
      </p>`;

    return sendEmail(apiKey, `🏒 ${verb} entry: ${teamName} (${name})`, html, res);
  }

  // ── Feedback / bug report ─────────────────────────────────────────────────
  const { type = 'Other', player = '', message = '' } = body;
  if (!message.trim()) return res.status(400).json({ error: 'Missing message' });

  const subject = `🚩 Pool 2027 Report: ${type}${player ? ` — ${player}` : ''}`;
  const html = `
    <h2 style="font-family:sans-serif;color:#1e3a8a;">🚩 Pool 2027 Issue Report</h2>
    <table style="font-family:sans-serif;font-size:15px;border-collapse:collapse;">
      <tr><td style="padding:4px 16px 4px 0;color:#6b7280;">Type</td><td style="font-weight:700;">${esc(type)}</td></tr>
      ${player ? `<tr><td style="padding:4px 16px 4px 0;color:#6b7280;">Player</td><td style="font-weight:600;">${esc(player)}</td></tr>` : ''}
      <tr><td style="padding:4px 16px 4px 0;color:#6b7280;vertical-align:top;">Details</td><td style="white-space:pre-wrap;">${esc(message)}</td></tr>
    </table>`;

  return sendEmail(apiKey, subject, html, res);
};

async function sendEmail(apiKey, subject, html, res) {
  const emailRes = await fetch(RESEND_API, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: FROM, to: [NOTIFY_TO], subject, html }),
  });
  if (!emailRes.ok) {
    const err = await emailRes.text();
    console.error('Resend error:', err);
    return res.status(500).json({ error: 'Email send failed' });
  }
  return res.status(200).json({ ok: true });
}

function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
