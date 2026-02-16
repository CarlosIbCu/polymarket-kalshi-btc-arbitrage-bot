"""
Match the same soccer game across Polymarket and Kalshi.
Uses team name normalization and date matching.
"""
import re
from difflib import SequenceMatcher

# Common team name aliases for normalization
TEAM_ALIASES = {
    # EPL
    "man united": "manchester united",
    "man utd": "manchester united",
    "manchester utd": "manchester united",
    "mun": "manchester united",
    "man city": "manchester city",
    "man. city": "manchester city",
    "mci": "manchester city",
    "spurs": "tottenham",
    "tottenham hotspur": "tottenham",
    "tot": "tottenham",
    "liverpool fc": "liverpool",
    "lfc": "liverpool",
    "liv": "liverpool",
    "arsenal fc": "arsenal",
    "ars": "arsenal",
    "chelsea fc": "chelsea",
    "che": "chelsea",
    "newcastle united": "newcastle",
    "newcastle utd": "newcastle",
    "new": "newcastle",
    "west ham united": "west ham",
    "west ham utd": "west ham",
    "whu": "west ham",
    "aston villa fc": "aston villa",
    "avl": "aston villa",
    "brighton & hove albion": "brighton",
    "brighton and hove albion": "brighton",
    "bha": "brighton",
    "wolverhampton wanderers": "wolves",
    "wolverhampton": "wolves",
    "wol": "wolves",
    "nottingham forest": "nott forest",
    "nfo": "nott forest",
    "crystal palace fc": "crystal palace",
    "cry": "crystal palace",
    "bournemouth fc": "bournemouth",
    "afc bournemouth": "bournemouth",
    "bou": "bournemouth",
    "fulham fc": "fulham",
    "ful": "fulham",
    "brentford fc": "brentford",
    "bre": "brentford",
    "everton fc": "everton",
    "eve": "everton",
    "ipswich town": "ipswich",
    "ips": "ipswich",
    "leicester city": "leicester",
    "lei": "leicester",
    "southampton fc": "southampton",
    "sou": "southampton",
    # La Liga
    "real madrid cf": "real madrid",
    "fc barcelona": "barcelona",
    "barca": "barcelona",
    "atletico madrid": "atletico",
    "atletico de madrid": "atletico",
    "atl madrid": "atletico",
    "real sociedad": "sociedad",
    "athletic bilbao": "athletic",
    "athletic club": "athletic",
    "real betis": "betis",
    "villarreal cf": "villarreal",
    "celta vigo": "celta",
    "rcd mallorca": "mallorca",
    "girona fc": "girona",
    "getafe cf": "getafe",
    "rayo vallecano": "rayo",
    # Bundesliga
    "bayern munich": "bayern",
    "fc bayern munich": "bayern",
    "bayern munchen": "bayern",
    "fc bayern": "bayern",
    "borussia dortmund": "dortmund",
    "bvb": "dortmund",
    "rb leipzig": "leipzig",
    "rasenballsport leipzig": "leipzig",
    "bayer leverkusen": "leverkusen",
    "bayer 04 leverkusen": "leverkusen",
    "eintracht frankfurt": "frankfurt",
    "vfb stuttgart": "stuttgart",
    "borussia monchengladbach": "gladbach",
    "borussia m'gladbach": "gladbach",
    "sc freiburg": "freiburg",
    "vfl wolfsburg": "wolfsburg",
    "1. fc union berlin": "union berlin",
    "tsg hoffenheim": "hoffenheim",
    "fc augsburg": "augsburg",
    "1. fsv mainz 05": "mainz",
    "sv werder bremen": "bremen",
    # Serie A
    "ac milan": "milan",
    "inter milan": "inter",
    "fc internazionale": "inter",
    "inter milano": "inter",
    "juventus fc": "juventus",
    "juve": "juventus",
    "as roma": "roma",
    "ssc napoli": "napoli",
    "ss lazio": "lazio",
    "atalanta bc": "atalanta",
    "acf fiorentina": "fiorentina",
    "torino fc": "torino",
    "us sassuolo": "sassuolo",
    "bologna fc": "bologna",
    "uc sampdoria": "sampdoria",
    "hellas verona": "verona",
    # Ligue 1
    "paris saint-germain": "psg",
    "paris saint germain": "psg",
    "paris sg": "psg",
    "olympique marseille": "marseille",
    "olympique de marseille": "marseille",
    "om": "marseille",
    "olympique lyonnais": "lyon",
    "olympique lyon": "lyon",
    "ol": "lyon",
    "as monaco": "monaco",
    "losc lille": "lille",
    "ogc nice": "nice",
    "rc lens": "lens",
    "stade rennais": "rennes",
    "rc strasbourg": "strasbourg",
    "fc nantes": "nantes",
    "toulouse fc": "toulouse",
    "montpellier hsc": "montpellier",
    "stade brestois": "brest",
    "le havre ac": "le havre",
    "hac": "le havre",
    # MLS
    "la galaxy": "galaxy",
    "los angeles galaxy": "galaxy",
    "inter miami cf": "inter miami",
    "inter miami": "inter miami",
    "new york red bulls": "ny red bulls",
    "new york city fc": "nycfc",
    "atlanta united fc": "atlanta united",
    "seattle sounders fc": "seattle sounders",
    "portland timbers": "portland",
    "lafc": "lafc",
    "los angeles fc": "lafc",
    # Americas
    "boca juniors": "boca",
    "river plate": "river",
    "club america": "america",
    "cf monterrey": "monterrey",
    "cd guadalajara": "chivas",
    "chivas": "chivas",
    "santos fc": "santos",
    "palmeiras": "palmeiras",
    "se palmeiras": "palmeiras",
    "flamengo": "flamengo",
    "cr flamengo": "flamengo",
    "corinthians": "corinthians",
    "sc corinthians": "corinthians",
    "sao paulo fc": "sao paulo",
}


def normalize_team_name(name):
    """Normalize a team name for comparison."""
    name = name.lower().strip()
    # Remove common suffixes
    name = re.sub(r'\s*(fc|cf|sc|ac|bc|ssc|afc)\s*$', '', name)
    name = re.sub(r'^\s*(fc|cf|sc|ac|bc|ssc|afc)\s+', '', name)
    name = name.strip()

    # Check aliases
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]

    return name


def extract_teams_from_title(title):
    """
    Extract team names from a match title.
    Common formats:
    - "Team A vs Team B"
    - "Team A v Team B"
    - "Team A - Team B"
    - "Team A vs. Team B"
    """
    title = title.strip()

    # Try various separators
    for separator in [" vs ", " vs. ", " v ", " - ", " @ "]:
        if separator in title.lower():
            idx = title.lower().index(separator)
            home = title[:idx].strip()
            away = title[idx + len(separator):].strip()
            return normalize_team_name(home), normalize_team_name(away)

    return None, None


def similarity(a, b):
    """String similarity ratio between 0 and 1."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def teams_match(team_a, team_b, threshold=0.75):
    """Check if two team names refer to the same team."""
    if not team_a or not team_b:
        return False

    norm_a = normalize_team_name(team_a)
    norm_b = normalize_team_name(team_b)

    if norm_a == norm_b:
        return True

    # Check if one contains the other
    if norm_a in norm_b or norm_b in norm_a:
        return True

    # Fuzzy match
    return similarity(norm_a, norm_b) >= threshold


def match_markets(poly_matches, kalshi_matches):
    """
    Match Polymarket events with Kalshi events for the same game.
    Returns list of paired matches.
    """
    paired = []
    used_kalshi = set()

    for poly in poly_matches:
        poly_home, poly_away = extract_teams_from_title(poly.get("title", ""))
        if not poly_home or not poly_away:
            # Try slug-based extraction (e.g., "epl-liv-ars-2026-02-15")
            slug = poly.get("slug", "")
            poly_home, poly_away = _extract_teams_from_slug(slug)

        if not poly_home:
            continue

        best_match = None
        best_score = 0

        for i, kalshi in enumerate(kalshi_matches):
            if i in used_kalshi:
                continue

            # Skip if different league
            if poly.get("league") and kalshi.get("league"):
                if poly["league"] != kalshi["league"]:
                    continue

            kalshi_home, kalshi_away = _extract_teams_from_kalshi(kalshi)
            if not kalshi_home:
                continue

            # Check if teams match (in either order)
            home_match = teams_match(poly_home, kalshi_home) and teams_match(poly_away, kalshi_away)
            swap_match = teams_match(poly_home, kalshi_away) and teams_match(poly_away, kalshi_home)

            if home_match or swap_match:
                score = 1.0 if home_match else 0.9
                if score > best_score:
                    best_score = score
                    best_match = (i, kalshi, home_match)

        if best_match:
            idx, kalshi, is_home_match = best_match
            used_kalshi.add(idx)
            paired.append({
                "home_team": poly_home,
                "away_team": poly_away,
                "league": poly.get("league", ""),
                "league_name": poly.get("league_name", ""),
                "polymarket": poly,
                "kalshi": kalshi,
                "teams_swapped": not is_home_match,
            })

    return paired


def _extract_teams_from_slug(slug):
    """Try to extract team identifiers from a Polymarket slug."""
    # Slugs like: "epl-liv-ars-2026-02-15"
    parts = slug.split("-")
    if len(parts) >= 3:
        # First part is league, next parts might be team abbreviations
        # This is approximate — will be refined with actual data
        return parts[1], parts[2]
    return None, None


def _extract_teams_from_kalshi(kalshi_event):
    """Extract team names from Kalshi event data."""
    # Try the title first
    title = kalshi_event.get("title", "")
    home, away = extract_teams_from_title(title)
    if home:
        return home, away

    # Try parsing from outcome market titles
    outcomes = kalshi_event.get("outcomes", {})
    teams = []
    for outcome_name, data in outcomes.items():
        market_title = data.get("title", outcome_name) if isinstance(data, dict) else outcome_name
        # "Will Liverpool beat Arsenal?" -> extract Liverpool, Arsenal
        match = re.search(r'[Ww]ill (.+?) beat (.+?)\??$', market_title)
        if match:
            teams.append((match.group(1).strip(), match.group(2).strip()))

    if teams:
        # Use the first win market to determine home/away
        return normalize_team_name(teams[0][0]), normalize_team_name(teams[0][1])

    return None, None
