/**
 * Serverless voting + page-view API for GitHub Pages
 * Uses GitHub Issues API to store votes and page view counts
 * GET  /api/vote?page=standings              — page view (increment)
 * GET  /api/vote?page=standings&count_only=1 — page view (read only)
 * GET  /api/vote?date=YYYY-MM-DD             — fetch vote counts
 * POST /api/vote                             — cast vote / record share
 * DELETE /api/vote                           — remove vote
 *
 * Deployment: Vercel Serverless Function (merged vote + page-views)
 */

const PAGE_VIEWS_ISSUE_TITLE = 'Page Views Counter';

const GITHUB_OWNER = 'jeedey93';
const GITHUB_REPO = 'parieur-discipline-bot';

/**
 * Get GitHub token (with trimming)
 */
function getGitHubToken() {
  const token = process.env.GH_API_TOKEN || process.env.GITHUB_TOKEN || process.env.GITHUB_PAT;
  if (!token) {
    throw new Error('GitHub token environment variable is not set');
  }
  return token.trim();
}

/**
 * Hash IP address for privacy
 */
function hashIP(ip) {
  let hash = 0;
  for (let i = 0; i < ip.length; i++) {
    const char = ip.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}

/**
 * Get or create voting issue for today
 */
async function getOrCreateVotingIssue(date) {
  const GITHUB_TOKEN = getGitHubToken();
  const issueTitle = `Votes: ${date}`;

  // Search for existing issue
  const searchUrl = `https://api.github.com/search/issues?q=repo:${GITHUB_OWNER}/${GITHUB_REPO}+is:issue+in:title+"${issueTitle}"`;
  const searchResponse = await fetch(searchUrl, {
    headers: {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'Parieur-Discipline-Bot',
    },
  });

  if (!searchResponse.ok) {
    const errorText = await searchResponse.text();
    throw new Error(`Failed to search issues: ${searchResponse.statusText} - ${errorText}`);
  }

  const searchData = await searchResponse.json();

  if (searchData.total_count > 0) {
    return searchData.items[0].number;
  }

  // Create new issue
  const createUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues`;
  const createResponse = await fetch(createUrl, {
    method: 'POST',
    headers: {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent': 'Parieur-Discipline-Bot',
    },
    body: JSON.stringify({
      title: issueTitle,
      body: `## Voting data for ${date}\n\nThis issue stores votes for daily picks. Each comment represents one vote.\n\n**Format:**\n\`\`\`json\n{\n  "pickId": "nhl-game1-over",\n  "ipHash": "abc123",\n  "timestamp": "2026-03-15T10:30:00Z"\n}\n\`\`\``,
      labels: ['votes', 'automated'],
    }),
  });

  if (!createResponse.ok) {
    throw new Error(`Failed to create issue: ${createResponse.statusText}`);
  }

  const createData = await createResponse.json();
  return createData.number;
}

/**
 * Get all votes for a date
 */
async function getVotes(date) {
  try {
    const GITHUB_TOKEN = getGitHubToken();
    const issueNumber = await getOrCreateVotingIssue(date);

    // Fetch all comments on the issue
    const commentsUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/${issueNumber}/comments`;
    const response = await fetch(commentsUrl, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Parieur-Discipline-Bot',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch comments: ${response.statusText}`);
    }

    const comments = await response.json();

    // Parse votes and shares from comments
    const votes = {};
    const shares = {};
    const userVotes = {}; // Track what each IP voted for

    comments.forEach(comment => {
      try {
        const data = JSON.parse(comment.body);
        const { pickId, ipHash, type = 'vote' } = data;

        if (type === 'share') {
          // Shares are unlimited per person — just count them
          if (!shares[pickId]) shares[pickId] = 0;
          shares[pickId]++;
        } else {
          // Votes: one per IP per pick
          if (!votes[pickId]) votes[pickId] = 0;
          const voteKey = `${ipHash}-${pickId}`;
          if (!userVotes[voteKey]) {
            votes[pickId]++;
            userVotes[voteKey] = true;
          }
        }
      } catch (e) {
        // Ignore malformed comments
      }
    });

    return { votes, shares, userVotes };
  } catch (error) {
    console.error('Error getting votes:', error);
    return { votes: {}, shares: {}, userVotes: {} };
  }
}

/**
 * Cast a vote
 */
async function castVote(date, pickId, ipHash) {
  try {
    const GITHUB_TOKEN = getGitHubToken();
    const issueNumber = await getOrCreateVotingIssue(date);

    // Check if user already voted for this pick
    const { userVotes } = await getVotes(date);
    const voteKey = `${ipHash}-${pickId}`;

    if (userVotes[voteKey]) {
      return { success: false, error: 'You have already voted for this pick' };
    }

    // Add comment with vote
    const commentsUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/${issueNumber}/comments`;
    const response = await fetch(commentsUrl, {
      method: 'POST',
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'Parieur-Discipline-Bot',
      },
      body: JSON.stringify({
        body: JSON.stringify({
          pickId,
          ipHash,
          timestamp: new Date().toISOString(),
        }),
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to post comment: ${response.statusText}`);
    }

    return { success: true };
  } catch (error) {
    console.error('Error casting vote:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Remove a vote
 */
async function removeVote(date, pickId, ipHash) {
  try {
    const GITHUB_TOKEN = getGitHubToken();
    const issueNumber = await getOrCreateVotingIssue(date);

    // Fetch all comments
    const commentsUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/${issueNumber}/comments`;
    const response = await fetch(commentsUrl, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Parieur-Discipline-Bot',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch comments: ${response.statusText}`);
    }

    const comments = await response.json();

    // Find and delete the user's vote comment
    for (const comment of comments) {
      try {
        const voteData = JSON.parse(comment.body);
        if (voteData.pickId === pickId && voteData.ipHash === ipHash) {
          // Delete this comment
          const deleteUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/comments/${comment.id}`;
          const deleteResponse = await fetch(deleteUrl, {
            method: 'DELETE',
            headers: {
              'Authorization': `token ${GITHUB_TOKEN}`,
              'Accept': 'application/vnd.github.v3+json',
              'User-Agent': 'Parieur-Discipline-Bot',
            },
          });

          if (!deleteResponse.ok) {
            throw new Error(`Failed to delete comment: ${deleteResponse.statusText}`);
          }

          return { success: true };
        }
      } catch (e) {
        // Ignore malformed comments
        continue;
      }
    }

    return { success: false, error: 'Vote not found' };
  } catch (error) {
    console.error('Error removing vote:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Vercel Serverless Function handler
 */
// ── Page-views helpers (merged from page-views.js) ────────────────────────────

async function getPVIssue() {
  const token = getGitHubToken();
  const headers = {
    'Authorization': `token ${token}`,
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json',
    'User-Agent': 'Parieur-Discipline-Bot',
  };
  const list = await fetch(
    `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues?labels=analytics&state=open&per_page=50`,
    { headers }
  );
  const issues = await list.json();
  const existing = Array.isArray(issues) && issues.find(i => i.title === PAGE_VIEWS_ISSUE_TITLE);
  if (existing) return existing;
  const create = await fetch(
    `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues`,
    { method: 'POST', headers, body: JSON.stringify({ title: PAGE_VIEWS_ISSUE_TITLE, body: '{}', labels: ['analytics', 'automated'] }) }
  );
  return await create.json();
}

async function handlePageViews(req, res) {
  const page = ((req.query && req.query.page) || 'standings').toLowerCase();
  const countOnly = req.query && req.query.count_only === 'true';
  const token = getGitHubToken();
  const issue = await getPVIssue();
  let views = {};
  try { views = JSON.parse(issue.body) || {}; } catch { views = {}; }

  if (countOnly) {
    return res.status(200).json({ success: true, page, count: views[page] || 0 });
  }

  views[page] = (views[page] || 0) + 1;
  await fetch(
    `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/${issue.number}`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `token ${token}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'Parieur-Discipline-Bot',
      },
      body: JSON.stringify({ body: JSON.stringify(views) }),
    }
  );
  return res.status(200).json({ success: true, page, count: views[page] });
}

// ─────────────────────────────────────────────────────────────────────────────

module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Route page-view requests (legacy /api/page-views URL or ?page= param without date)
  const url = req.url || '';
  if (url.includes('/page-views') || (req.query && req.query.page && !req.query.date && req.method === 'GET')) {
    try { return await handlePageViews(req, res); }
    catch (err) { return res.status(500).json({ success: false, error: err.message }); }
  }

  try {
    // Get GitHub token
    const token = process.env.GH_API_TOKEN || process.env.GITHUB_TOKEN || process.env.GITHUB_PAT;

    if (!token) {
      return res.status(500).json({
        success: false,
        error: 'GitHub token environment variable is not set'
      });
    }

    const { date = new Date().toISOString().split('T')[0] } = req.query;

    // Get IP address from request
    const ip = req.headers['x-forwarded-for']?.split(',')[0] ||
               req.headers['x-real-ip'] ||
               req.connection.remoteAddress ||
               'unknown';
    const ipHash = hashIP(ip);

    // GET: Fetch vote and share counts
    if (req.method === 'GET') {
      const { votes, shares } = await getVotes(date);
      return res.status(200).json({ success: true, votes, shares });
    }

    // POST: Cast a vote or record a share
    if (req.method === 'POST') {
      const { pickId, type = 'vote' } = req.body;

      if (!pickId) {
        return res.status(400).json({ success: false, error: 'Missing pickId' });
      }

      if (type === 'share') {
        // Record share — no duplicate check, just append
        const issueNumber = await getOrCreateVotingIssue(date);
        const commentsUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/${issueNumber}/comments`;
        const GITHUB_TOKEN = getGitHubToken();
        await fetch(commentsUrl, {
          method: 'POST',
          headers: {
            'Authorization': `token ${GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'Parieur-Discipline-Bot',
          },
          body: JSON.stringify({
            body: JSON.stringify({ pickId, type: 'share', timestamp: new Date().toISOString() }),
          }),
        });
        const { votes, shares } = await getVotes(date);
        return res.status(200).json({ success: true, votes, shares });
      }

      const result = await castVote(date, pickId, ipHash);

      if (result.success) {
        const { votes, shares } = await getVotes(date);
        return res.status(200).json({ success: true, votes, shares });
      } else {
        return res.status(400).json(result);
      }
    }

    // DELETE: Remove a vote
    if (req.method === 'DELETE') {
      const { pickId } = req.body;

      if (!pickId) {
        return res.status(400).json({ success: false, error: 'Missing pickId' });
      }

      const result = await removeVote(date, pickId, ipHash);

      if (result.success) {
        const { votes, shares } = await getVotes(date);
        return res.status(200).json({ success: true, votes, shares });
      } else {
        return res.status(400).json(result);
      }
    }

    return res.status(405).json({ error: 'Method not allowed' });

  } catch (error) {
    console.error('Error in vote handler:', error);
    return res.status(500).json({ success: false, error: error.message });
  }
};
