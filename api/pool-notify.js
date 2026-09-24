/**
 * Pool 2027 notifications — Vercel Serverless Function
 * Handles two cases:
 *
 *   action = "overwrite"  — frontend PATCH proxy using service role key
 *   (default)             — feedback / bug report
 *
 * Required env vars: RESEND_API_KEY, SUPABASE_SERVICE_KEY
 *
 * POST /api/pool-notify
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

  const body = req.body || {};

  // ── Overwrite proxy (frontend can't PATCH with service key) ─────────────────
  if (body.action === 'overwrite') {
    const sbUrl = process.env.SUPABASE_URL || 'https://fifurqlitkywtmhgtzeu.supabase.co';
    const sbKey = process.env.SUPABASE_SERVICE_KEY;
    if (!sbKey) return res.status(500).json({ error: 'Supabase service key not configured' });
    const { email, payload } = body;
    if (!email || !payload) return res.status(400).json({ error: 'Missing email or payload' });
    try {
      const patchRes = await fetch(
        `${sbUrl}/rest/v1/pool_2027_submissions?email=eq.${encodeURIComponent(email)}`,
        {
          method: 'PATCH',
          headers: {
            'apikey': sbKey,
            'Authorization': `Bearer ${sbKey}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation',
          },
          body: JSON.stringify(payload),
        }
      );
      const text = await patchRes.text();
      let data;
      try { data = JSON.parse(text); } catch { data = text; }
      if (!patchRes.ok) return res.status(patchRes.status).json({ error: 'Supabase PATCH failed', detail: data });
      const rows = Array.isArray(data) ? data : [];
      if (rows.length === 0) return res.status(404).json({ error: 'No row matched that email' });
      return res.status(200).json({ ok: true, record: rows[0] });
    } catch (err) {
      console.error('overwrite error:', err);
      return res.status(500).json({ error: err.message });
    }
  }

  // ── Feedback / bug report ─────────────────────────────────────────────────
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'RESEND_API_KEY not configured' });

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
