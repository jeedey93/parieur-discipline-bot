/**
 * Pool 2027 feedback / bug report — Vercel Serverless Function
 * Receives a report from the draft or standings page and emails justin.do@hotmail.com.
 *
 * Required env var: RESEND_API_KEY
 *
 * POST /api/pool-feedback
 * Body: { type, player, message }
 */

const RESEND_API = 'https://api.resend.com/emails';
const FROM       = 'Pool 2027 <onboarding@resend.dev>';
const NOTIFY_TO  = 'justin.do@hotmail.com';

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'RESEND_API_KEY not configured' });

  const { type = 'Other', player = '', message = '' } = req.body || {};
  if (!message.trim()) return res.status(400).json({ error: 'Missing message' });

  const subject = `🚩 Pool 2027 Report: ${type}${player ? ` — ${player}` : ''}`;
  const html = `
    <h2 style="font-family:sans-serif;color:#1e3a8a;">🚩 Pool 2027 Issue Report</h2>
    <table style="font-family:sans-serif;font-size:15px;border-collapse:collapse;">
      <tr><td style="padding:4px 16px 4px 0;color:#6b7280;">Type</td><td style="font-weight:700;">${esc(type)}</td></tr>
      ${player ? `<tr><td style="padding:4px 16px 4px 0;color:#6b7280;">Player</td><td style="font-weight:600;">${esc(player)}</td></tr>` : ''}
      <tr><td style="padding:4px 16px 4px 0;color:#6b7280;vertical-align:top;">Details</td><td style="white-space:pre-wrap;">${esc(message)}</td></tr>
    </table>`;

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
};

function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
