import os
import re
from datetime import datetime

def parse_results_from_file(filepath):
    wins = 0
    losses = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        # Try to find summary lines first
        win_match = re.search(r"Total Wins:?[\s\*]*([0-9]+)", content, re.IGNORECASE)
        loss_match = re.search(r"Total Losses:?[\s\*]*([0-9]+)", content, re.IGNORECASE)
        if win_match and loss_match:
            wins = int(win_match.group(1))
            losses = int(loss_match.group(1))
        else:
            # Fallback: count occurrences in breakdown
            wins = len(re.findall(r"Outcome: ?\*?WIN\*?", content, re.IGNORECASE))
            losses = len(re.findall(r"Outcome: ?\*?LOSS\*?", content, re.IGNORECASE))
    return wins, losses

def get_date_from_filename(filename):
    # Try to extract date from filename (YYYY-MM-DD)
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return filename

def per_date_results(results_dir):
    date_results = []
    for fname in sorted(os.listdir(results_dir)):
        if fname.endswith('.txt'):
            wins, losses = parse_results_from_file(os.path.join(results_dir, fname))
            date = get_date_from_filename(fname)
            date_results.append((date, wins, losses))
    return date_results

def main():
    nba_dir = os.path.join('bot_results', 'nba')
    nhl_dir = os.path.join('bot_results', 'nhl')
    nba_results = per_date_results(nba_dir)
    nhl_results = per_date_results(nhl_dir)
    nba_wins = sum(x[1] for x in nba_results)
    nba_losses = sum(x[2] for x in nba_results)
    nhl_wins = sum(x[1] for x in nhl_results)
    nhl_losses = sum(x[2] for x in nhl_results)
    output = []
    output.append(f"Total Results Summary ({datetime.now().strftime('%Y-%m-%d')})\n")
    output.append('NBA:')
    output.append(f'TOTAL: {nba_wins} wins, {nba_losses} losses')
    for date, wins, losses in nba_results:
        output.append(f'{date}: {wins} win' + ('' if wins == 1 else 's') + f', {losses} loss' + ('' if losses == 1 else 'es'))
    output.append('')
    output.append('NHL:')
    output.append(f'TOTAL: {nhl_wins} wins, {nhl_losses} losses')
    for date, wins, losses in nhl_results:
        output.append(f'{date}: {wins} win' + ('' if wins == 1 else 's') + f', {losses} loss' + ('' if losses == 1 else 'es'))
    output.append('')
    summary_text = '\n'.join(output)
    print(summary_text)
    # Write to file
    summary_path = os.path.join('bot_results', 'total_results_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)

if __name__ == '__main__':
    main()
