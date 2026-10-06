/**
 * NHL API proxy — forwards requests to api-web.nhle.com with a server-side
 * User-Agent, bypassing the CORS block the browser hits directly.
 *
 * Usage: GET /api/nhl-proxy?path=/v1/gamecenter/2026020001/boxscore
 *        GET /api/nhl-proxy?path=/v1/schedule/2026-10-06
 *
 * Only GET requests to api-web.nhle.com are allowed.
 */

const ALLOWED_HOST = 'api-web.nhle.com';

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const path = req.query?.path;
  if (!path || !path.startsWith('/v1/')) {
    return res.status(400).json({ error: 'Missing or invalid path parameter' });
  }

  const url = `https://${ALLOWED_HOST}${path}`;
  try {
    const upstream = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    const data = await upstream.json();
    // Cache for 30s so rapid polling doesn't hammer NHL
    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=10');
    return res.status(upstream.status).json(data);
  } catch (err) {
    return res.status(502).json({ error: 'Upstream fetch failed', detail: err.message });
  }
};
