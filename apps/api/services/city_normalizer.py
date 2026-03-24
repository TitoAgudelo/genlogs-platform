"""Normalize city names from user input to canonical database values.

Handles common abbreviations (NYC, DC, SF, LA) and variations
(e.g., "Washington" → "Washington DC", "Los Angeles" → "Los Angeles").
"""

# Maps lowercase aliases to canonical city names as stored in the database.
CITY_ALIASES: dict[str, str] = {
    # New York (+ Spanish/localized variants from Google Places)
    "nyc": "New York",
    "new york city": "New York",
    "new york": "New York",
    "manhattan": "New York",
    "nueva york": "New York",
    # Washington DC (+ localized variants with periods/spaces)
    "dc": "Washington DC",
    "washington": "Washington DC",
    "washington dc": "Washington DC",
    "washington d.c.": "Washington DC",
    "washington d.c": "Washington DC",
    "washington d. c.": "Washington DC",
    "washington, d.c.": "Washington DC",
    # San Francisco
    "sf": "San Francisco",
    "san francisco": "San Francisco",
    "san fran": "San Francisco",
    # Los Angeles (+ Spanish variant)
    "la": "Los Angeles",
    "los angeles": "Los Angeles",
    "los ángeles": "Los Angeles",
    # Chicago
    "chicago": "Chicago",
    "chi": "Chicago",
    # Detroit
    "detroit": "Detroit",
    # Dallas
    "dallas": "Dallas",
    # Houston
    "houston": "Houston",
    # Miami
    "miami": "Miami",
    # Atlanta
    "atlanta": "Atlanta",
    # Seattle
    "seattle": "Seattle",
    # Portland
    "portland": "Portland",
    # Boston
    "boston": "Boston",
    # Philadelphia (+ Spanish variant)
    "philadelphia": "Philadelphia",
    "philly": "Philadelphia",
    "filadelfia": "Philadelphia",
    # Denver
    "denver": "Denver",
    # Salt Lake City
    "salt lake city": "Salt Lake City",
    "slc": "Salt Lake City",
}

# Sorted by length descending so longer matches take priority
# (e.g., "new york city" matches before "new york")
_SORTED_ALIASES = sorted(CITY_ALIASES.keys(), key=len, reverse=True)


def normalize_city(city: str) -> str:
    """Normalize a city name to its canonical form.

    Returns the canonical name if found in aliases, otherwise returns the
    original input stripped and title-cased.
    """
    cleaned = city.strip().lower()
    if cleaned in CITY_ALIASES:
        return CITY_ALIASES[cleaned]
    return city.strip()


def extract_cities_from_text(text: str) -> tuple[str | None, str | None]:
    """Extract origin and destination cities from natural language text.

    Scans for known city aliases (longest first), returns them
    in order of appearance (first = origin, second = destination).
    """
    text_lower = text.strip().lower()

    found: list[tuple[int, str]] = []
    working_text = text_lower

    for alias in _SORTED_ALIASES:
        pos = working_text.find(alias)
        if pos != -1:
            canonical = CITY_ALIASES[alias]
            # Avoid duplicate cities (e.g., "washington" and "dc" both → "Washington DC")
            if not any(c == canonical for _, c in found):
                found.append((pos, canonical))
            # Mask matched text to prevent re-matching
            working_text = working_text[:pos] + ("_" * len(alias)) + working_text[pos + len(alias):]

    found.sort(key=lambda x: x[0])

    if len(found) >= 2:
        return found[0][1], found[1][1]
    if len(found) == 1:
        return found[0][1], None
    return None, None
