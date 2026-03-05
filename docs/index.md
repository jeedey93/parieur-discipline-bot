<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>Parieur Discipliné - AI Betting Predictions</title>
<meta name='description' content='AI-powered sports betting predictions for NHL and NBA. Daily picks with analysis and edge calculation.'>
<link rel='icon' type='image/png' href='parieur_discipline.png'>
</head>
<body>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1a1a1a; background: #f5f7fa; }
.main-content { max-width: 100% !important; padding: 0 !important; }
.blog-container { width: 100%; margin: 0; background: white; }
.hero-section { background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; padding: 50px 40px; text-align: center; position: relative; overflow: hidden; }
.hero-section::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('data:image/svg+xml,%3Csvg width="60" height="60" xmlns="http://www.w3.org/2000/svg"%3E%3Cpath d="M0 0h60v60H0z" fill="none"/%3E%3Cpath d="M30 0l30 30-30 30L0 30z" fill="%23ffffff" fill-opacity=".03"/%3E%3C/svg%3E'); opacity: 0.3; }
.hero-content { position: relative; z-index: 1; }
.hero-logo { width: 170px; height: 170px; border-radius: 50%; margin: 0 auto 20px auto; display: block; border: 4px solid rgba(255,255,255,0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
.blog-title { font-size: 3em; font-weight: 800; margin-bottom: 15px; letter-spacing: -1px; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.blog-subtitle { font-size: 1.3em; opacity: 0.95; margin-bottom: 10px; font-weight: 300; }
.blog-date { font-size: 1.1em; opacity: 0.85; font-weight: 500; }
.blog-update-time { font-size: 0.9em; opacity: 0.75; margin-top: 10px; }
.content-wrapper { padding: 0 60px 40px 60px; max-width: 1600px; margin: 0 auto; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin: -35px auto 35px auto; padding: 0 60px; max-width: 1600px; position: relative; z-index: 10; }
.stat-card { background: white; border-radius: 10px; padding: 18px 15px; text-align: center; box-shadow: 0 3px 12px rgba(0,0,0,0.08); transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #e8ecf1; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.12); }
.stat-label { font-size: 0.75em; color: #6b7280; text-transform: uppercase; font-weight: 700; letter-spacing: 0.8px; margin-bottom: 8px; }
.stat-value { font-size: 2.2em; font-weight: 800; margin-bottom: 6px; background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.stat-record { font-size: 0.9em; color: #4b5563; font-weight: 500; }
.nav-tabs { display: flex; gap: 10px; margin: 30px 0; padding: 10px; background: #f9fafb; border-radius: 12px; flex-wrap: wrap; }
.nav-tab { flex: 1; min-width: 120px; padding: 12px 20px; background: white; border: 2px solid #e5e7eb; border-radius: 8px; text-decoration: none; text-align: center; font-weight: 600; font-size: 0.95em; transition: all 0.2s; color: #374151; }
.nav-tab:hover { border-color: #4a90e2; color: #4a90e2; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(74,144,226,0.1); }
.section-header { margin: 50px 0 30px 0; padding-bottom: 15px; border-bottom: 3px solid #e5e7eb; }
.section-title { font-size: 2.2em; font-weight: 800; color: #111827; display: flex; align-items: center; gap: 12px; }
.section-subtitle { font-size: 0.95em; color: #6b7280; margin-top: 8px; font-weight: 400; }
.featured-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; margin: 25px 0; }
.pick-card { background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%); border-radius: 12px; padding: 25px; border: 2px solid #e5e7eb; transition: all 0.3s; }
.pick-card:hover { border-color: #4a90e2; box-shadow: 0 8px 25px rgba(74,144,226,0.15); transform: translateY(-3px); }
.pick-badge { display: inline-block; padding: 6px 12px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
.badge-nhl { background: #fee2e2; color: #dc2626; }
.badge-nba { background: #fed7aa; color: #ea580c; }
.badge-featured { background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; }
.pick-title { font-size: 1.25em; font-weight: 700; color: #111827; margin-bottom: 15px; line-height: 1.4; }
.pick-meta { display: block; padding: 8px 14px; background: #f3f4f6; border-radius: 8px; font-size: 0.85em; margin-bottom: 18px; }
.confidence-high { display: inline-block; background: #10b981; color: white; padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; margin-right: 8px; }
.confidence-medium { display: inline-block; background: #f59e0b; color: white; padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; margin-right: 8px; }
.pick-description { color: #4b5563; line-height: 1.7; font-size: 0.95em; }
.yesterday-section { background: #f9fafb; border-radius: 12px; padding: 30px; margin: 40px 0; border: 1px solid #e5e7eb; }
.result-card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #e5e7eb; transition: all 0.2s; }
.result-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.result-win { border-left-color: #10b981; background: linear-gradient(90deg, #ecfdf5 0%, #ffffff 100%); }
.result-loss { border-left-color: #ef4444; background: linear-gradient(90deg, #fef2f2 0%, #ffffff 100%); }
.result-push { border-left-color: #f59e0b; background: linear-gradient(90deg, #fffbeb 0%, #ffffff 100%); }
.results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }
.result-tile { background: white; border-radius: 8px; padding: 15px; text-align: center; border: 2px solid #e5e7eb; transition: all 0.2s; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.result-tile:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.result-tile-win { border-color: #10b981; background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%); }
.result-tile-loss { border-color: #ef4444; background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%); }
.result-tile-push { border-color: #f59e0b; background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%); }
.result-tile-emoji { font-size: 2em; margin-bottom: 8px; }
.result-tile-bet { font-size: 0.85em; color: #374151; font-weight: 500; line-height: 1.3; margin-bottom: 6px; }
.result-tile-units { font-size: 0.9em; font-weight: 700; margin-top: 6px; }
.result-tile-featured { border-width: 3px; box-shadow: 0 6px 20px rgba(234, 88, 12, 0.25); transform: scale(1.05); position: relative; }
.result-tile-featured:hover { transform: scale(1.08) translateY(-2px); box-shadow: 0 8px 30px rgba(234, 88, 12, 0.35); }
.botd-badge { position: absolute; top: -8px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.7em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; box-shadow: 0 2px 8px rgba(234, 88, 12, 0.4); }
.result-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.result-badge { padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; }
.badge-win { background: #10b981; color: white; }
.badge-loss { background: #ef4444; color: white; }
.badge-push { background: #f59e0b; color: white; }
.result-title { font-weight: 600; color: #111827; font-size: 1.05em; }
.result-score { color: #6b7280; font-size: 0.9em; padding-left: 50px; }
#back-to-top { position: fixed; bottom: 30px; right: 30px; background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; padding: 14px 18px; border-radius: 50%; box-shadow: 0 4px 20px rgba(74,144,226,0.4); cursor: pointer; font-size: 1.3em; display: none; z-index: 1000; border: none; transition: all 0.3s; }
#back-to-top:hover { transform: translateY(-5px); box-shadow: 0 6px 30px rgba(74,144,226,0.6); }
@media (max-width: 768px) { .content-wrapper { padding: 0 20px 30px 20px; } .stats-grid { margin: -25px 0px 25px 0px; grid-template-columns: repeat(5, 1fr); gap: 8px; max-width: 100%; padding: 0 15px; overflow-x: auto; -webkit-overflow-scrolling: touch; } .stat-card { padding: 12px 8px; min-width: 110px; } .stat-label { font-size: 0.65em; } .stat-value { font-size: 1.6em; } .stat-record { font-size: 0.75em; } .blog-title { font-size: 1.8em; } .blog-subtitle { font-size: 1em; } .blog-date { font-size: 0.95em; } .blog-update-time { font-size: 0.8em; } .hero-logo { width: 90px; height: 90px; margin-bottom: 15px; } .section-title { font-size: 1.5em; } .section-subtitle { font-size: 0.85em; } .featured-grid { grid-template-columns: 1fr; gap: 15px; } .pick-card { padding: 20px; } .pick-title { font-size: 1.1em; } .pick-badge { font-size: 0.7em; padding: 5px 10px; } .pick-meta { font-size: 0.8em; padding: 6px 12px; } .pick-description { font-size: 0.9em; } .hero-section { padding: 30px 20px; } .nav-tabs { gap: 8px; padding: 8px; } .nav-tab { padding: 10px 12px; font-size: 0.85em; min-width: 100px; } .result-card { padding: 15px; } .result-title { font-size: 0.95em; } .result-score { font-size: 0.85em; padding-left: 40px; } .results-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; } .result-tile { min-height: 90px; padding: 12px; } .result-tile-featured { min-height: 100px; } .result-tile-emoji { font-size: 1.8em; } .result-tile-bet { font-size: 0.8em; } .result-tile-units { font-size: 0.85em; } .botd-badge { font-size: 0.65em; padding: 3px 10px; top: -6px; } .yesterday-section { padding: 20px; } #back-to-top { bottom: 20px; right: 20px; padding: 12px 16px; font-size: 1.1em; } }
</style>

<div class='blog-container'>

<div class='hero-section'>
<div class='hero-content'>
<img src='parieur_discipline.png' alt='Parieur Discipliné' class='hero-logo'>
<div class='blog-title'>🎯 Parieur Discipliné</div>
<div class='blog-subtitle'>AI-Powered NHL & NBA Betting Predictions</div>
<div class='blog-date'>March 4, 2026</div>
<div class='blog-update-time'>⏱️ Updated at 01:16 PM ET</div>
</div>
</div>

<div class='stats-grid'>
<div class='stat-card'>
<div class='stat-label'>Yesterday</div>
<div class='stat-value'>50%</div>
<div class='stat-record'>3W - 3L</div>
<div class='stat-record' style='margin-top: 5px; color: #10b981; font-weight: 600;'>+0.05 units</div>
</div>
<div class='stat-card'>
<div class='stat-label'>This Week</div>
<div class='stat-value'>44%</div>
<div class='stat-record'>11W - 14L</div>
<div class='stat-record' style='margin-top: 5px; color: #ef4444; font-weight: 600;'>-2.50 units</div>
</div>
<div class='stat-card'>
<div class='stat-label'>Season</div>
<div class='stat-value'>49%</div>
<div class='stat-record'>33W - 34L</div>
<div class='stat-record' style='margin-top: 5px; color: #10b981; font-weight: 600;'>+3.87 units</div>
</div>
<div class='stat-card'>
<div class='stat-label'>🏒 NHL</div>
<div class='stat-value'>50%</div>
<div class='stat-record'>15W - 15L</div>
<div class='stat-record' style='margin-top: 5px; color: #10b981; font-weight: 600;'>+1.03 units</div>
</div>
<div class='stat-card'>
<div class='stat-label'>🏀 NBA</div>
<div class='stat-value'>49%</div>
<div class='stat-record'>18W - 19L</div>
<div class='stat-record' style='margin-top: 5px; color: #10b981; font-weight: 600;'>+2.84 units</div>
</div>
</div>

<div class='content-wrapper'>

<div class='nav-tabs'>
<a href='#featured-picks' class='nav-tab'>🔥 Featured Picks (Potential)</a>
<a href='#yesterday-results' class='nav-tab'>📋 Yesterday's Results</a>
</div>

<div style='background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; padding: 25px 40px; text-align: center; border-radius: 12px; margin: 30px 0; box-shadow: 0 4px 15px rgba(74,144,226,0.3);'>
<div style='font-size: 1.4em; font-weight: 700; margin-bottom: 8px;'>🕐 Preliminary Analysis Available</div>
<div style='font-size: 1em; opacity: 0.95;'>7am predictions shown below. Final picks with line movement analysis available at <strong>12:00 PM ET</strong></div>
</div>

<div id='featured-picks'>
<div class='section-header'>
<div class='section-title'>🔥 Featured Picks (Potential)</div>
<div class='section-subtitle'>7am predictions - subject to change at 12pm after line movement analysis</div>
</div>
<div class='featured-grid'>
<div class='pick-card' style='border: 2px solid #FFA500;'>
<div class='pick-badge badge-featured'>🏒 NHL</div>
<div class='pick-title'>Los Angeles Kings ML vs New York Islanders @ 1.74</div>
<div class='pick-meta'>Confidence Level: High, Units: 1.5u, Win Probability: 70.5%</div>
<div class='pick-description'>The Los Angeles Kings are significantly favored in this matchup due to the New York Islanders' extensive injury list, including starting goaltender Semyon Varlamov, key forward Kyle Palmieri, and top defensemen Alexander Romanov and Ryan Pulock. The Kings are well-rested, having last played on February 28, while the Islanders, though also rested, face a monumental challenge with so many core players out. This severe talent deficit for the Islanders, compounded by starting a backup goalie against a healthy Kings squad, creates a substantial mispricing by bookmakers, offering excellent value on the Kings' moneyline.</div>
<div style='margin-top: 15px; padding: 12px; background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 4px;'>
<div style='font-size: 0.85em; color: #92400e; font-weight: 600;'>⚠️ Preliminary Pick</div>
<div style='font-size: 0.8em; color: #78350f; margin-top: 4px;'>This pick may change after 12pm line movement analysis</div>
</div>
</div>
<div class='pick-card' style='border: 2px solid #FFA500;'>
<div class='pick-badge badge-featured'>🏀 NBA</div>
<div class='pick-title'>Sacramento Kings vs New Orleans Pelicans Under 234.5 @ 1.91</div>
<div class='pick-meta'>Confidence Level: High Units: 1.5u, Win Probability: 65%</div>
<div class='pick-description'>The Kings and Pelicans both come into this matchup relatively rested after playing on March 3rd. Recent trends show that both teams have been involved in lower-scoring games, with their last three combined totals for the Pelicans and the Kings' recent game all falling significantly below the current line of 234.5 points. Our model has historically performed well predicting Unders in Pelicans games, identifying a consistent market overestimation of totals for their matchups. This pattern, combined with the teams' recent scoring outputs, creates a strong edge against the implied probability.</div>
<div style='margin-top: 15px; padding: 12px; background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 4px;'>
<div style='font-size: 0.85em; color: #92400e; font-weight: 600;'>⚠️ Preliminary Pick</div>
<div style='font-size: 0.8em; color: #78350f; margin-top: 4px;'>This pick may change after 12pm line movement analysis</div>
</div>
</div>
</div>
</div>

<div id='yesterday-results'>
<div class='section-header'>
<div class='section-title'>📋 Yesterday's Results</div>
<div class='section-subtitle'>Performance breakdown for March 4, 2026</div>
</div>
<div class='yesterday-section'>
<h3 style='color: #dc2626; margin-top: 0; margin-bottom: 15px; font-size: 1.2em; font-weight: 700;'>🏒 NHL Results</h3>

<div class='results-grid'>
<div class='result-tile result-tile-loss result-tile-featured'>
<div class='botd-badge'>🔥 BET OF THE DAY</div>
<div class='result-tile-emoji'>❌</div>
<div class='result-tile-bet'>Toronto Maple Leafs ML vs New Jersey Devils</div>
<div class='result-tile-units' style='color: #ef4444;'>-1.50u</div>
</div>
</div>

<h3 style='color: #ea580c; margin-top: 25px; margin-bottom: 15px; font-size: 1.2em; font-weight: 700;'>🏀 NBA Results</h3>

<div class='results-grid'>
<div class='result-tile result-tile-loss result-tile-featured'>
<div class='botd-badge'>🔥 BET OF THE DAY</div>
<div class='result-tile-emoji'>❌</div>
<div class='result-tile-bet'>Boston Celtics -6.5 vs Charlotte Hornets</div>
<div class='result-tile-units' style='color: #ef4444;'>-1.50u</div>
</div>
<div class='result-tile result-tile-win'>
<div class='result-tile-emoji'>✅</div>
<div class='result-tile-bet'>Atlanta Hawks +1.5 vs Milwaukee Bucks</div>
<div class='result-tile-units' style='color: #10b981;'>+1.48u</div>
</div>
<div class='result-tile result-tile-win'>
<div class='result-tile-emoji'>✅</div>
<div class='result-tile-bet'>Atlanta Hawks ML vs Milwaukee Bucks</div>
<div class='result-tile-units' style='color: #10b981;'>+1.57u</div>
</div>
<div class='result-tile result-tile-win'>
<div class='result-tile-emoji'>✅</div>
<div class='result-tile-bet'>Los Angeles Clippers -12.5 vs Indiana Pacers</div>
<div class='result-tile-units' style='color: #10b981;'>+0.99u</div>
</div>
<div class='result-tile result-tile-loss'>
<div class='result-tile-emoji'>❌</div>
<div class='result-tile-bet'>Oklahoma City Thunder -4.0 vs New York Knicks</div>
<div class='result-tile-units' style='color: #ef4444;'>-1.00u</div>
</div>
</div>

</div>

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

<script defer src='/_vercel/insights/script.js'></script>
<script defer src='/_vercel/speed-insights/script.js'></script>

</body>
</html>

