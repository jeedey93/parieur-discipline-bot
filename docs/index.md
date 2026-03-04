<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1a1a1a; background: #f5f7fa; }
.main-content { max-width: 100% !important; padding: 0 !important; }
.blog-container { width: 100%; margin: 0; background: white; }
.hero-section { background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; padding: 50px 40px; text-align: center; position: relative; overflow: hidden; }
.hero-section::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('data:image/svg+xml,%3Csvg width="60" height="60" xmlns="http://www.w3.org/2000/svg"%3E%3Cpath d="M0 0h60v60H0z" fill="none"/%3E%3Cpath d="M30 0l30 30-30 30L0 30z" fill="%23ffffff" fill-opacity=".03"/%3E%3C/svg%3E'); opacity: 0.3; }
.hero-content { position: relative; z-index: 1; }
.hero-logo { width: 120px; height: 120px; border-radius: 50%; margin: 0 auto 20px auto; display: block; border: 4px solid rgba(255,255,255,0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
.blog-title { font-size: 3em; font-weight: 800; margin-bottom: 15px; letter-spacing: -1px; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.blog-subtitle { font-size: 1.3em; opacity: 0.95; margin-bottom: 10px; font-weight: 300; }
.blog-date { font-size: 1.1em; opacity: 0.85; font-weight: 500; }
.blog-update-time { font-size: 0.9em; opacity: 0.75; margin-top: 10px; }
.content-wrapper { padding: 0 60px 40px 60px; max-width: 1600px; margin: 0 auto; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin: -40px auto 40px auto; padding: 0 60px; max-width: 1600px; position: relative; z-index: 10; }
.stat-card { background: white; border-radius: 12px; padding: 25px 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.08); transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #e8ecf1; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.12); }
.stat-label { font-size: 0.8em; color: #6b7280; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; margin-bottom: 10px; }
.stat-value { font-size: 2.5em; font-weight: 800; margin-bottom: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.stat-record { font-size: 0.95em; color: #4b5563; font-weight: 500; }
.nav-tabs { display: flex; gap: 10px; margin: 30px 0; padding: 10px; background: #f9fafb; border-radius: 12px; flex-wrap: wrap; }
.nav-tab { flex: 1; min-width: 120px; padding: 12px 20px; background: white; border: 2px solid #e5e7eb; border-radius: 8px; text-decoration: none; text-align: center; font-weight: 600; font-size: 0.95em; transition: all 0.2s; color: #374151; }
.nav-tab:hover { border-color: #667eea; color: #667eea; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(102,126,234,0.1); }
.section-header { margin: 50px 0 30px 0; padding-bottom: 15px; border-bottom: 3px solid #e5e7eb; }
.section-title { font-size: 2.2em; font-weight: 800; color: #111827; display: flex; align-items: center; gap: 12px; }
.section-subtitle { font-size: 0.95em; color: #6b7280; margin-top: 8px; font-weight: 400; }
.featured-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; margin: 25px 0; }
.pick-card { background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%); border-radius: 12px; padding: 25px; border: 2px solid #e5e7eb; transition: all 0.3s; }
.pick-card:hover { border-color: #667eea; box-shadow: 0 8px 25px rgba(102,126,234,0.15); transform: translateY(-3px); }
.pick-badge { display: inline-block; padding: 6px 12px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
.badge-nhl { background: #fee2e2; color: #dc2626; }
.badge-nba { background: #fed7aa; color: #ea580c; }
.badge-featured { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.pick-title { font-size: 1.25em; font-weight: 700; color: #111827; margin-bottom: 15px; line-height: 1.4; }
.pick-meta { display: inline-block; padding: 8px 14px; background: #f3f4f6; border-radius: 8px; font-size: 0.85em; margin-bottom: 12px; }
.confidence-high { display: inline-block; background: #10b981; color: white; padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; margin-right: 8px; }
.confidence-medium { display: inline-block; background: #f59e0b; color: white; padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; margin-right: 8px; }
.pick-description { color: #4b5563; line-height: 1.7; font-size: 0.95em; }
.yesterday-section { background: #f9fafb; border-radius: 12px; padding: 30px; margin: 40px 0; border: 1px solid #e5e7eb; }
.result-card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #e5e7eb; transition: all 0.2s; }
.result-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.result-win { border-left-color: #10b981; background: linear-gradient(90deg, #ecfdf5 0%, #ffffff 100%); }
.result-loss { border-left-color: #ef4444; background: linear-gradient(90deg, #fef2f2 0%, #ffffff 100%); }
.result-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.result-badge { padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; }
.badge-win { background: #10b981; color: white; }
.badge-loss { background: #ef4444; color: white; }
.result-title { font-weight: 600; color: #111827; font-size: 1.05em; }
.result-score { color: #6b7280; font-size: 0.9em; padding-left: 50px; }
#back-to-top { position: fixed; bottom: 30px; right: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 18px; border-radius: 50%; box-shadow: 0 4px 20px rgba(102,126,234,0.4); cursor: pointer; font-size: 1.3em; display: none; z-index: 1000; border: none; transition: all 0.3s; }
#back-to-top:hover { transform: translateY(-5px); box-shadow: 0 6px 30px rgba(102,126,234,0.6); }
@media (max-width: 768px) { .content-wrapper { padding: 0 20px 30px 20px; } .stats-grid { margin: -40px 20px 30px 20px; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; } .stat-card { padding: 18px 15px; } .blog-title { font-size: 2em; } .hero-logo { width: 90px; height: 90px; margin-bottom: 15px; } .section-title { font-size: 1.6em; } .featured-grid { grid-template-columns: 1fr; gap: 15px; } .hero-section { padding: 35px 20px; } .nav-tabs { gap: 8px; padding: 8px; } .nav-tab { padding: 10px 12px; font-size: 0.85em; min-width: 100px; } }
</style>

<div class='blog-container'>

<div class='hero-section'>
<div class='hero-content'>
<img src='parieur_discipline.png' alt='Parieur Discipliné' class='hero-logo'>
<div class='blog-title'>🎯 Parieur Discipliné</div>
<div class='blog-subtitle'>AI-Powered NHL & NBA Betting Predictions</div>
<div class='blog-date'>7am</div>
<div class='blog-update-time'>📡 Updated daily at 12:00 PM ET</div>
</div>
</div>

<div class='stats-grid'>
<div class='stat-card'>
<div class='stat-label'>Yesterday</div>
<div class='stat-value'>50%</div>
<div class='stat-record'>5W - 5L</div>
</div>
<div class='stat-card'>
<div class='stat-label'>Last 5 Days</div>
<div class='stat-value'>45%</div>
<div class='stat-record'>15W - 18L</div>
</div>
<div class='stat-card'>
<div class='stat-label'>Season</div>
<div class='stat-value'>48%</div>
<div class='stat-record'>30W - 32L</div>
</div>
<div class='stat-card'>
<div class='stat-label'>🏒 NHL</div>
<div class='stat-value'>50%</div>
<div class='stat-record'>15W - 15L</div>
</div>
<div class='stat-card'>
<div class='stat-label'>🏀 NBA</div>
<div class='stat-value'>47%</div>
<div class='stat-record'>15W - 17L</div>
</div>
</div>

<div class='content-wrapper'>

<div class='nav-tabs'>
<a href='#featured-picks' class='nav-tab'>🔥 Featured Picks</a>
<a href='#nhl-predictions' class='nav-tab'>🏒 NHL</a>
<a href='#nba-predictions' class='nav-tab'>🏀 NBA</a>
<a href='#yesterday-results' class='nav-tab'>📋 Yesterday</a>
</div>

<div id='featured-picks'>
<div class='section-header'>
<div class='section-title'>🔥 Featured Picks of the Day</div>
<div class='section-subtitle'>Our top AI-selected plays with the highest edge</div>
</div>
<div class='featured-grid'>

<div class='pick-card'>
<div class='pick-badge badge-nhl'>PICK #1 — NHL</div>
<div class='pick-title'>Washington Capitals ML vs Utah Mammoth @ 1.83</div>
<div class='pick-meta'><span class='confidence-medium'>MEDIUM</span> Confidence Level: Medium, Units: 1u, Win Probability: 60% The Capitals are well-rested and have shown strong form with recent wins, while Utah is a weaker opponent. Washington has consistently been a reliable pick for our model in similar matchups, demonstrating a strong historical edge.</div>
</div>

<div class='pick-card'>
<div class='pick-badge badge-nba'>PICK #2 — NBA</div>
<div class='pick-title'>Los Angeles Lakers vs New Orleans Pelicans Under 243.0 @ 1.99</div>
<div class='pick-meta'><span class='confidence-high'>HIGH</span> Confidence Level: High Units: 1.5u, Win Probability: 56% The Lakers and Pelicans are both well-rested and coming off wins, suggesting stable overall team performance for this matchup. Our model indicates that despite their strong offensive forms, the combined total is likely to stay under the generous line due to expected tighter defensive schemes in a competitive game.</div>
</div>

</div>

</div>

<div id='yesterday-results'>
<div class='section-header'>
<div class='section-title'>📋 Yesterday's Results</div>
<div class='section-subtitle'>Performance breakdown for 7am</div>
</div>
<div class='yesterday-section'>
<h3 style='color: #dc2626; margin-top: 0; margin-bottom: 20px; font-size: 1.4em; font-weight: 700;'>🏒 NHL Results</h3>

<div class='result-card result-loss'>
<div class='result-header'>
<span style='font-size: 1.5em;'>❌</span>
<span class='result-badge badge-loss'>LOSS</span>
<span class='result-title'>Washington Capitals ML vs Utah Mammoth @ 1.83</span>
</div>
<div class='result-score'>Utah 3 @ Washington 2 (Total goals: 5)</div>
</div>

<div class='result-card result-win'>
<div class='result-header'>
<span style='font-size: 1.5em;'>✅</span>
<span class='result-badge badge-win'>WIN</span>
<span class='result-title'>Ottawa Senators vs Edmonton Oilers Over 6.5 @ 1.95</span>
</div>
<div class='result-score'>Ottawa 4 @ Edmonton 5 (Total goals: 9)</div>
</div>

<div class='result-card result-loss'>
<div class='result-header'>
<span style='font-size: 1.5em;'>❌</span>
<span class='result-badge badge-loss'>LOSS</span>
<span class='result-title'>Tampa Bay Lightning vs Minnesota Wild Over 6.0 @ 2.18</span>
</div>
<div class='result-score'>Tampa Bay 1 @ Minnesota 5 (Total goals: 6)</div>
</div>

<div class='result-card result-win'>
<div class='result-header'>
<span style='font-size: 1.5em;'>✅</span>
<span class='result-badge badge-win'>WIN</span>
<span class='result-title'>Florida Panthers vs New Jersey Devils Over 5.5 @ 1.95</span>
</div>
<div class='result-score'>Florida 1 @ New Jersey 5 (Total goals: 6)</div>
</div>

<div class='result-card result-loss'>
<div class='result-header'>
<span style='font-size: 1.5em;'>❌</span>
<span class='result-badge badge-loss'>LOSS</span>
<span class='result-title'>Calgary Flames ML vs Dallas Stars @ 2.1</span>
</div>
<div class='result-score'>Dallas 6 @ Calgary 1 (Total goals: 7)</div>
</div>

<h3 style='color: #ea580c; margin-top: 30px; margin-bottom: 20px; font-size: 1.4em; font-weight: 700;'>🏀 NBA Results</h3>

<div class='result-card result-win'>
<div class='result-header'>
<span style='font-size: 1.5em;'>✅</span>
<span class='result-badge badge-win'>WIN</span>
<span class='result-title'>Los Angeles Lakers vs New Orleans Pelicans Under 243.0 @ 1.99</span>
</div>
<div class='result-score'>New Orleans Pelicans 101 @ Los Angeles Lakers 110</div>
</div>

<div class='result-card result-loss'>
<div class='result-header'>
<span style='font-size: 1.5em;'>❌</span>
<span class='result-badge badge-loss'>LOSS</span>
<span class='result-title'>Charlotte Hornets vs Dallas Mavericks Over 231.0 @ 1.98</span>
</div>
<div class='result-score'>Dallas Mavericks 90 @ Charlotte Hornets 117</div>
</div>

<div class='result-card result-loss'>
<div class='result-header'>
<span style='font-size: 1.5em;'>❌</span>
<span class='result-badge badge-loss'>LOSS</span>
<span class='result-title'>Detroit Pistons -2.5 vs Cleveland Cavaliers @ 1.99</span>
</div>
<div class='result-score'>Detroit Pistons 109 @ Cleveland Cavaliers 113</div>
</div>

<div class='result-card result-win'>
<div class='result-header'>
<span style='font-size: 1.5em;'>✅</span>
<span class='result-badge badge-win'>WIN</span>
<span class='result-title'>New York Knicks -2.5 vs Toronto Raptors @ 1.98</span>
</div>
<div class='result-score'>New York Knicks 111 @ Toronto Raptors 95</div>
</div>

<div class='result-card result-win'>
<div class='result-header'>
<span style='font-size: 1.5em;'>✅</span>
<span class='result-badge badge-win'>WIN</span>
<span class='result-title'>Phoenix Suns -10.0 vs Sacramento Kings @ 1.99</span>
</div>
<div class='result-score'>Phoenix Suns 114 @ Sacramento Kings 103</div>
</div>

</div>

</div>

<div id='nhl-predictions'>
<div class='section-header'>
<div class='section-title'>🏒 NHL Predictions</div>
<div class='section-subtitle'>Today's NHL picks with full analysis</div>
</div>

<details style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
<summary style='cursor:pointer;font-size:1.1em; font-weight: bold; color: #667eea;'><span style='font-size:1.2em;'>▶️</span> Morning vs Noon Analysis <span style='color:#999; font-weight: normal;'>(click to expand)</span></summary>

<div style='margin-top: 15px;'>
<p>Date: 2026-03-04</p>
<br>
<p>Vegas Golden Knights @ Detroit Red Wings</p>
<p>Home odds: 1.74, Away odds: 2.15, O/U: 6.0</p>
<p>------</p>
<p>Toronto Maple Leafs @ New Jersey Devils</p>
<p>Home odds: 1.83, Away odds: 2.0, O/U: 5.5</p>
<p>------</p>
<p>Carolina Hurricanes @ Vancouver Canucks</p>
<p>Home odds: 3.12, Away odds: 1.37, O/U: 6.0</p>
<p>------</p>
<p>New York Islanders @ Anaheim Ducks</p>
<p>Home odds: 1.91, Away odds: 1.91, O/U: 6.5</p>
<p>------</p>
<p>St Louis Blues @ Seattle Kraken</p>
<p>Home odds: 1.67, Away odds: 2.22, O/U: 5.5</p>
<p>------</p>
<br>
<p>AI Analysis Summary:</p>
<p>Current Roster Data Verified.</p>
</div>

</details>


<h3 style='margin: 30px 0 20px 0; color: #333; font-size: 1.5em;'>📋 Other Recommended Plays</h3>



</div>

<div id='nba-predictions'>
<div class='section-header'>
<div class='section-title'>🏀 NBA Predictions</div>
<div class='section-subtitle'>Today's NBA picks with full analysis</div>
</div>

<details style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
<summary style='cursor:pointer;font-size:1.1em; font-weight: bold; color: #667eea;'><span style='font-size:1.2em;'>▶️</span> Morning vs Noon Analysis <span style='color:#999; font-weight: normal;'>(click to expand)</span></summary>

<div style='margin-top: 15px;'>
<p>Date: 2026-03-04</p>
<br>
<p>New York Knicks vs Oklahoma City Thunder</p>
<p>Home odds: 2.54, Away odds: 1.54, O/U: 222.5</p>
<p>Spreads: Home 4.5 (1.91), Away -4.5 (1.99)</p>
<p>------</p>
<p>Boston Celtics vs Charlotte Hornets</p>
<p>Home odds: 1.41, Away odds: 3.0, O/U: 212.5</p>
<p>Spreads: Home -6.5 (1.92), Away 6.5 (1.98)</p>
<p>------</p>
<p>Philadelphia 76ers vs Utah Jazz</p>
<p>Home odds: 1.24, Away odds: 4.3, O/U: 239.5</p>
<p>Spreads: Home -9.5 (1.99), Away 9.5 (1.95)</p>
<p>------</p>
<p>Memphis Grizzlies vs Portland Trail Blazers</p>
<p>Home odds: 3.7, Away odds: 1.3, O/U: 237.5</p>
<p>Spreads: Home 8.5 (1.95), Away -8.5 (1.94)</p>
<p>------</p>
<p>Milwaukee Bucks vs Atlanta Hawks</p>
<p>Home odds: 1.86, Away odds: 1.98, O/U: 233.5</p>
<p>Spreads: Home -1.0 (1.91), Away 1.0 (1.91)</p>
<p>------</p>
<p>Los Angeles Clippers vs Indiana Pacers</p>
<p>Home odds: 1.15, Away odds: 5.9, O/U: 226.5</p>
<p>Spreads: Home -12.0 (1.94), Away 12.0 (1.95)</p>
<p>------</p>
<br>
<p>AI Analysis Summary:</p>
<p>Current Roster Data Verified.</p>
</div>

</details>


<h3 style='margin: 30px 0 20px 0; color: #333; font-size: 1.5em;'>📋 Other Recommended Plays</h3>



</div>

</div>

</div>

<button id='back-to-top' onclick='window.scrollTo({top: 0, behavior: "smooth"})'>↑</button>

<script>
window.addEventListener('scroll', function() {
  var btn = document.getElementById('back-to-top');
  if (window.pageYOffset > 300) { btn.style.display = 'block'; }
  else { btn.style.display = 'none'; }
});
</script>

