import requests
from bs4 import BeautifulSoup

def scrape_nhl_injuries_by_team():
    url = "https://www.nhl.com/news/nhl-lineup-projections-2025-26-season"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    injuries_by_team = {}

    # Find all elements that could be a team section header
    for header in soup.find_all(['strong', 'b']):
        header_text = header.get_text(strip=True)
        # Look for team section headers
        if "projected lineup" in header_text.lower():
            team_name = header_text.replace("projected lineup", "").strip(" :")
            team_players = []

            # Search for both "Scratched:" and "Injured:" tags after this header
            next_tag = header.find_next(['strong', 'b'])

            # Look for scratched players
            while next_tag:
                next_text = next_tag.get_text(strip=True).lower()

                if next_text == "scratched:":
                    # The player info is usually in the next sibling
                    next_node = next_tag.next_sibling
                    if next_node:
                        scratched_list = str(next_node).strip()
                        scratched_list = scratched_list.lstrip(":").strip()
                        for player in scratched_list.split(","):
                            player = player.strip()
                            player = player.replace('\xa0', '').replace('Â', '').strip()
                            if player and player.lower() != "none":
                                team_players.append(f"{player} (scratched)")

                elif next_text == "injured:":
                    # The player info is usually in the next sibling
                    next_node = next_tag.next_sibling
                    if next_node:
                        injured_list = str(next_node).strip()
                        injured_list = injured_list.lstrip(":").strip()
                        for player in injured_list.split(","):
                            player = player.strip()
                            player = player.replace('\xa0', '').replace('Â', '').strip()
                            if player and player.lower() != "none":
                                team_players.append(player)

                # Stop when we hit the next team's lineup
                elif "projected lineup" in next_text:
                    break

                next_tag = next_tag.find_next(['strong', 'b'])

            if team_players:
                injuries_by_team[team_name] = team_players

    return injuries_by_team

if __name__ == "__main__":
    injuries_by_team = scrape_nhl_injuries_by_team()
    print("NHL Injured/Scratched Players by Team:")
    for team, players in injuries_by_team.items():
        print(f"{team}:")
        for player in players:
            print(f"  {player}")
