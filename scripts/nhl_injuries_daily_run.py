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
            # Search for the next "Injured:" tag after this header
            next_tag = header.find_next(['strong', 'b'])
            while next_tag and next_tag.get_text(strip=True).lower() != "injured:":
                next_tag = next_tag.find_next(['strong', 'b'])
            if next_tag and next_tag.get_text(strip=True).lower() == "injured:":
                # The player info is usually in the next sibling (NavigableString or tag)
                next_node = next_tag.next_sibling
                if next_node:
                    injured_list = str(next_node).strip()
                    injured_list = injured_list.lstrip(":").strip()
                    players = []
                    for player in injured_list.split(","):
                        player = player.strip()
                        player = player.replace('\xa0', '').replace('Â', '').strip()
                        if player and player.lower() != "none":
                            players.append(player)
                    if players:
                        injuries_by_team[team_name] = players

    return injuries_by_team

if __name__ == "__main__":
    injuries_by_team = scrape_nhl_injuries_by_team()
    print("NHL Injured Players by Team:")
    for team, players in injuries_by_team.items():
        print(f"{team}:")
        for player in players:
            print(f"  {player}")
