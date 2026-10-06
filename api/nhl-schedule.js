/**
 * NHL API proxy — forwards requests to api-web.nhle.com with a server-side
 * User-Agent, bypassing the CORS block the browser hits directly.
 *
 * Usage (generic):  GET /api/nhl-schedule?path=/v1/gamecenter/2026020001/boxscore
 * Usage (schedule): GET /api/nhl-schedule?date=YYYY-MM-DD  (legacy, kept for compat)
 */

const ALLOWED_HOST = 'api-web.nhle.com';

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  // Resolve path: explicit ?path= takes priority, else build from ?date=
  let path = req.query?.path;
  if (!path && req.query?.date) {
    const date = req.query.date;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date))
      return res.status(400).json({ error: 'Invalid date format. Use YYYY-MM-DD' });
    path = `/v1/schedule/${date}`;
  }
  if (!path || !path.startsWith('/v1/'))
    return res.status(400).json({ error: 'Missing or invalid path parameter' });

  try {
    const upstream = await fetch(`https://${ALLOWED_HOST}${path}`, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    const data = await upstream.json();
    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=10');
    return res.status(upstream.status).json(data);
  } catch (err) {
    return res.status(502).json({ error: 'Upstream fetch failed', detail: err.message });
  }
};
