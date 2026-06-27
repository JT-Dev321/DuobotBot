import logging

from rapidfuzz import fuzz

from ids import botguidemention, ticketchannelmention

log = logging.getLogger("duobot.auto_responses")

SITE_LINK = "[Our Website](https://duobot.com/p/deepforce)"
WHICH_BOT_CHANNEL_LINK = "<#1165717673322221649>"

# Each entry is matched by checking every keyword against the user's message using
# fuzz.partial_ratio — which scores how well the keyword fits as a substring of the
# message (handles typos and paraphrasing). The entry with the highest score above
# its match_threshold wins.
AUTO_RESPONSES: list[dict] = [
    {
        "id": "bot_command_in_server",
        "keywords": ["!buy", "!buytf", "!buyhydra", "!add", "!info", "!check", "!level"],
        "match_threshold": 92,
        "response": "Please send our bots these commands on steam, not in the discord. ",
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
        "response": f"You can bypass the need to be added by using {SITE_LINK}",
    },
    {
        "id": "friend_list_fill",
        "keywords": [
            "friends list full",
            "friend list full",
            "friends list is full",
            "friend list is full",
            "clear friends",
            "clear friends list",
        ],
        "match_threshold": 75,
        "response": f"You can bypass the need to be added by using {SITE_LINK}",
    },
    {
        "id": "fund_transfer",
        "keywords": [
            "transfer funds",
            "for other account",
            "to other account",
        ],
        "match_threshold": 75,
        "response": f"On {SITE_LINK} the level up page has an option in the top right to buy on behalf of someone else. You can also use a support ticket on the site to request a balance transfer.",
    },
    {
        "id": "specific_sets",
        "keywords": ["specific set", "specific sets", "sell specific", "choose my sets"],
        "match_threshold": 80,
        "response": f"You can buy specific sets of cards on {SITE_LINK}",
    },
    {
        "id": "tradable_keys",
        "keywords": ["which keys", "what keys", "keys not tradable", "key list"],
        "match_threshold": 82,
        "response": "https://pastebin.com/5cxyRMTb",
    },
    {
        "id": "steam_error_occurred",
        "keywords": ["an error occurred", "error occurred while"],
        "match_threshold": 82,
        "response": "This is likely a case of the steam servers being slow to communicate with the bot, meaning it cannot operate. Please try again in around 10 minutes. - We cannot fix this.",
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
        "response": "If you are certain your entire profile is not private, this is a case of the steam servers being slow to communicate with the bot, meaning it cannot operate. Please try again in around 10 minutes. - We cannot fix this.",
    },
    {
        "id": "crypto_payment",
        "keywords": ["crypto", "paypal", "bitcoin", "ethereum", "pay with cash", "cash payment"],
        "match_threshold": 90,
        "response": f"Our {SITE_LINK} has several deposit options available.",
    },
    {
        "id": "refund",
        "keywords": ["refund", "money back", "get my money back", "want a refund"],
        "match_threshold": 85,
        "response": f"We do not formally offer refunds, if you would like to make a request you can open a {ticketchannelmention}",
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
        "response": "If you are using the site there can sometimes be rounding errors where you may get slightly the incorrect amount of XP.",
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
        "response": f"See {botguidemention}",
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
        "response": "Key list: https://pastebin.com/5cxyRMTb",
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
        "response": 
            f"""
            There are many ways of purchasing keys across a range of payment methods/gateways. The two sites we personally recommend are:
            https://marketplace.tf/items/tf2/5021;6
            https://cs.deals/new/market?game=tf2&sort=price&sort_desc=1&name=key&exact_match=0
            
            You can also use the site {SITE_LINK} to deposit balance directly.
            """,
    },
]


def find_auto_response(content: str) -> dict | None:
    """Return the highest-scoring AUTO_RESPONSES entry whose best keyword clears
    its match_threshold, or None if nothing matches."""
    best_entry = None
    best_score = 0

    log.debug("Scoring message: %r", content)

    for entry in AUTO_RESPONSES:
        threshold = entry["match_threshold"]
        for keyword in entry["keywords"]:
            score = fuzz.partial_ratio(keyword.lower(), content)
            log.debug("  [%s] keyword=%r score=%d threshold=%d", entry["id"], keyword, score, threshold)
            if score >= threshold and score > best_score:
                best_score = score
                best_entry = entry
                break

    if best_entry:
        log.debug("Best match: %s (score=%d)", best_entry["id"], best_score)
    else:
        log.debug("No match found")

    return best_entry
