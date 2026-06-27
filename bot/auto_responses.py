from rapidfuzz import fuzz

from ids import botguidemention, ticketchannelmention


# Each entry is matched by checking every keyword against the user's message using
# fuzz.partial_ratio — which scores how well the keyword fits as a substring of the
# message (handles typos and paraphrasing). The entry with the highest score above
# its match_threshold wins.
AUTO_RESPONSES: list[dict] = [
    {
        "id": "bot_command_in_server",
        "keywords": ["!buy", "!buytf", "!buyhydra", "!add", "!info", "!check", "!level"],
        "match_threshold": 92,
        "response": "PLACEHOLDER",
    },
    {
        "id": "add_bot_friend_request",
        "keywords": [
            "add me on bot",
            "add me on the bot",
            "friend request",
            "bot add me",
            "send me a friend request",
            "can the bot add me",
        ],
        "match_threshold": 75,
        "response": f"PLACEHOLDER — open a {ticketchannelmention}",
    },
    {
        "id": "specific_sets",
        "keywords": ["specific set", "specific sets", "sell specific", "choose my sets"],
        "match_threshold": 80,
        "response": "PLACEHOLDER",
    },
    {
        "id": "tradable_keys",
        "keywords": ["tradable", "tradeable", "not tradable", "keys not tradable", "untradable"],
        "match_threshold": 82,
        "response": "PLACEHOLDER",
    },
    {
        "id": "steam_error_occurred",
        "keywords": ["an error occurred", "error occurred while"],
        "match_threshold": 82,
        "response": "PLACEHOLDER",
    },
    {
        "id": "profile_private",
        "keywords": [
            "error loading your profile",
            "profile is private",
            "profile as it is private",
            "loading your profile",
        ],
        "match_threshold": 80,
        "response": "PLACEHOLDER",
    },
    {
        "id": "processing_hold",
        "keywords": [
            "processing your request, please hold",
            "stuck on processing",
            "please hold",
            "stuck on please hold",
        ],
        "match_threshold": 78,
        "response": "PLACEHOLDER",
    },
    {
        "id": "no_tradable_tf2_keys",
        "keywords": [
            "don't find any tradable tf2",
            "i don't find any tradable tf2",
            "no tradable tf2 key",
        ],
        "match_threshold": 78,
        "response": "PLACEHOLDER",
    },
    {
        "id": "no_tradable_csgo_keys",
        "keywords": [
            "don't find any tradable csgo",
            "i don't find any tradable csgo",
            "no tradable csgo key",
        ],
        "match_threshold": 78,
        "response": "PLACEHOLDER",
    },
    {
        "id": "no_tradable_hydra_keys",
        "keywords": [
            "don't find any tradable hydra",
            "i don't find any tradable hydra",
            "no tradable hydra key",
        ],
        "match_threshold": 78,
        "response": "PLACEHOLDER",
    },
    {
        "id": "crypto_payment",
        "keywords": ["crypto", "paypal", "bitcoin", "ethereum", "pay with cash", "cash payment"],
        "match_threshold": 90,
        "response": "PLACEHOLDER",
    },
    {
        "id": "refund",
        "keywords": ["refund", "money back", "get my money back", "want a refund"],
        "match_threshold": 85,
        "response": "PLACEHOLDER",
    },
    {
        "id": "less_sets_lower_level",
        "keywords": [
            "less sets than expected",
            "lower level than expected",
            "fewer sets",
            "got less sets",
            "wrong level",
            "less levels than",
        ],
        "match_threshold": 78,
        "response": f"PLACEHOLDER — open a {ticketchannelmention} if needed",
    },
    {
        "id": "which_bot_to_use",
        "keywords": [
            "which bot",
            "what bot",
            "what does high mean",
            "what does low mean",
            "high bot",
            "low bot",
            "which bot do i use",
        ],
        "match_threshold": 80,
        "response": f"PLACEHOLDER — see {botguidemention}",
    },
    {
        "id": "accepted_keys",
        "keywords": [
            "what keys",
            "which keys",
            "accepted keys",
            "what keys does the bot accept",
            "does the bot accept",
        ],
        "match_threshold": 80,
        "response": "PLACEHOLDER — key list: https://pastebin.com/5cxyRMTb",
    },
    {
        "id": "where_to_buy_keys",
        "keywords": [
            "where to buy keys",
            "where can i buy keys",
            "best place to buy keys",
            "cheapest keys",
            "buy tf2 keys",
            "buy csgo keys",
        ],
        "match_threshold": 78,
        "response": "PLACEHOLDER",
    },
]


def find_auto_response(content: str) -> dict | None:
    """Return the highest-scoring AUTO_RESPONSES entry whose best keyword clears
    its match_threshold, or None if nothing matches."""
    best_entry = None
    best_score = 0

    for entry in AUTO_RESPONSES:
        threshold = entry["match_threshold"]
        for keyword in entry["keywords"]:
            score = fuzz.partial_ratio(keyword.lower(), content)
            if score >= threshold and score > best_score:
                best_score = score
                best_entry = entry
                break  # one keyword hit is enough; move to next entry

    return best_entry
