/**
 * NHL API proxy — two modes:
 *
 * 1. JSON proxy:  GET /api/nhl-schedule?path=/v1/...
 *    Forwards to api-web.nhle.com (which blocks browser CORS).
 *    Legacy:      GET /api/nhl-schedule?date=YYYY-MM-DD
 *
 * 2. Image proxy: GET /api/nhl-schedule?img=https://assets.nhle.com/...
 *    Fetches the image server-side and returns it with CORS headers so
 *    the browser can draw it to canvas (NHL CDN sends no CORS headers).
 */

const ALLOWED_API_HOST  = 'api-web.nhle.com';
const ALLOWED_IMG_HOSTS = ['assets.nhle.com'];

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  // --- Image proxy mode ---
  const imgUrl = req.query?.img;
  if (imgUrl) {
    let parsed;
    try { parsed = new URL(imgUrl); } catch { return res.status(400).json({ error: 'Invalid img url' }); }
    if (!ALLOWED_IMG_HOSTS.includes(parsed.hostname))
      return res.status(403).json({ error: 'Host not allowed' });
    try {
      const upstream = await fetch(imgUrl, {
        headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ParieurBot/1.0)' },
      });
      if (!upstream.ok) return res.status(upstream.status).end();
      const contentType = upstream.headers.get('content-type') || 'image/png';
      const buffer = Buffer.from(await upstream.arrayBuffer());
      res.setHeader('Content-Type', contentType);
      res.setHeader('Cache-Control', 'public, max-age=3600');
      return res.status(200).end(buffer);
    } catch (err) {
      return res.status(502).json({ error: 'Upstream fetch failed', detail: err.message });
    }
  }

  // --- JSON proxy mode ---
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
    const upstream = await fetch(`https://${ALLOWED_API_HOST}${path}`, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    const data = await upstream.json();
    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=10');
    return res.status(upstream.status).json(data);
  } catch (err) {
    return res.status(502).json({ error: 'Upstream fetch failed', detail: err.message });
  }
};
