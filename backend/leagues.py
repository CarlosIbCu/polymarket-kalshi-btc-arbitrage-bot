"""
League configuration for soccer arbitrage bot.
Maps each league to its Polymarket and Kalshi identifiers.

Polymarket: uses tag_slug param on gamma API. EPL is uppercase "EPL".
Kalshi: match-level markets use series tickers with GAME suffix (e.g., KXEPLGAME).
"""

LEAGUES = {
    # Europe
    "epl": {
        "name": "English Premier League",
        "polymarket_tag_slug": "EPL",
        "kalshi_series": "KXEPLGAME",
    },
    "laliga": {
        "name": "La Liga",
        "polymarket_tag_slug": "la-liga",
        "kalshi_series": "KXLALIGAGAME",
    },
    "bundesliga": {
        "name": "Bundesliga",
        "polymarket_tag_slug": "bundesliga",
        "kalshi_series": "KXBUNDESLIGAGAME",
    },
    "serie_a": {
        "name": "Serie A",
        "polymarket_tag_slug": "serie-a",
        "kalshi_series": "KXSERIEAGAME",
    },
    "ligue1": {
        "name": "Ligue 1",
        "polymarket_tag_slug": "ligue-1",
        "kalshi_series": "KXLIGUE1GAME",
    },
    "ucl": {
        "name": "Champions League",
        "polymarket_tag_slug": "ucl",
        "kalshi_series": "KXUCLGAME",
    },
    "uel": {
        "name": "Europa League",
        "polymarket_tag_slug": "uel",
        "kalshi_series": "KXUELGAME",
    },
    "eredivisie": {
        "name": "Eredivisie",
        "polymarket_tag_slug": "eredivisie",
        "kalshi_series": "KXEREGAME",
    },
    "primeira_liga": {
        "name": "Primeira Liga",
        "polymarket_tag_slug": "primeira-liga",
        "kalshi_series": "KXPORGAME",
    },
    "efl_championship": {
        "name": "EFL Championship",
        "polymarket_tag_slug": "efl-championship",
        "kalshi_series": "KXELCGAME",
    },
    # Americas
    "mls": {
        "name": "Major League Soccer",
        "polymarket_tag_slug": "mls",
        "kalshi_series": "KXMLSGAME",
    },
    "liga_mx": {
        "name": "Liga MX",
        "polymarket_tag_slug": "liga-mx",
        "kalshi_series": "KXLIGAMXGAME",
    },
    "brasileirao": {
        "name": "Brasileirao",
        "polymarket_tag_slug": "brasileirao",
        "kalshi_series": "KXBRASILGAME",
    },
    "argentina_primera": {
        "name": "Argentine Primera Division",
        "polymarket_tag_slug": "argentina-primera",
        "kalshi_series": "KXARGGAME",
    },
    "copa_libertadores": {
        "name": "Copa Libertadores",
        "polymarket_tag_slug": "copa-libertadores",
        "kalshi_series": "KXLIBERTADORESGAME",
    },
    "copa_sudamericana": {
        "name": "Copa Sudamericana",
        "polymarket_tag_slug": "copa-sudamericana",
        "kalshi_series": "KXSUDAMERICANAGAME",
    },
    # International
    "world_cup": {
        "name": "FIFA World Cup",
        "polymarket_tag_slug": "fifa-world-cup",
        "kalshi_series": "KXWORLDCUPGAME",
    },
}
