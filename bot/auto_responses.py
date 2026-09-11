import logging
import re

from rapidfuzz import fuzz

from ids import botguidemention, ticketchannelmention

log = logging.getLogger("duobot.auto_responses")

SITE_LINK = "[Our Website](https://duobot.com/p/deepforce)"
WHICH_BOT_CHANNEL_LINK = "<#1165717673322221649>"

# Each entry is matched by sliding a window of words across the user's message and
# scoring each window against the keyword with fuzz.ratio (handles typos and small
# paraphrasing). The whole keyword has to be present in the message — a message that
# only contains a fragment of it does not match. The entry with the highest score
# above its match_threshold wins.
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
            "transfer balance",
            "balance transfer",
            "send balance to",
            "for other account",
            "to other account",
            "for another account",
            "to another account",
            "buy for someone else",
            "buy for my friend",
        ],
        "match_threshold": 75,
        "response": f"On {SITE_LINK} the level up page has an option in the top right to buy on behalf of someone else. You can also use a support ticket on the site to request a balance transfer.",
    },
    {
        "id": "specific_sets",
        "keywords": ["specific set", "specific sets", "specific card sets", "choose my sets"],
        "match_threshold": 80,
        "response": f"You can buy specific sets of cards on {SITE_LINK}",
    },
    {
        "id": "tradable_keys",
        "keywords": ["which keys", "what keys", "keys not tradable", "key list"],
        "match_threshold": 82,
        "response": "The keys the bot accepts can be found here: https://duobot.com/faq/what-are-the-accepted-keys and https://steamcommunity.com/market/listings/440/Mann%20Co.%20Supply%20Crate%20Key",
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
        "keywords": ["crypto", "paypal", "bitcoin", "ethereum", "pay with cash", "cash payment", "pixpay"],
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


_TOKEN_RE = re.compile(r"[!\w']+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _score_keyword(keyword: str, words: list[str]) -> float:
    """Score how well `keyword` appears in the already-tokenized message.

    The keyword is compared against every window of message words that is roughly
    the same length as the keyword itself, using fuzz.ratio on the whole window.
    Unlike fuzz.partial_ratio this cannot report a perfect match when the message
    only holds a fragment of the keyword (e.g. "account" vs "for other account"),
    and it will not match a keyword hidden inside a longer word.
    """
    keyword_words = keyword.split()
    n = len(keyword_words)
    if not words or n == 0:
        return 0.0

    best = 0.0
    # Allow the window to be one word shorter/longer than the keyword so filler
    # words ("to my other account") and dropped words still match.
    for size in sorted({max(1, n - 1), n, n + 1}):
        if size > len(words):
            continue
        for i in range(len(words) - size + 1):
            window = " ".join(words[i:i + size])
            score = fuzz.ratio(keyword, window)
            if score > best:
                best = score
    return best


def find_auto_response(content: str) -> dict | None:
    """Return the highest-scoring AUTO_RESPONSES entry whose best keyword clears
    its match_threshold, or None if nothing matches."""
    best_entry = None
    best_score = 0.0

    words = _tokenize(content)
    log.debug("Scoring message: %r -> %r", content, words)

    for entry in AUTO_RESPONSES:
        threshold = entry["match_threshold"]
        for keyword in entry["keywords"]:
            score = _score_keyword(keyword.lower(), words)
            log.debug("  [%s] keyword=%r score=%d threshold=%d", entry["id"], keyword, score, threshold)
            if score >= threshold and score > best_score:
                best_score = score
                best_entry = entry

    if best_entry:
        log.debug("Best match: %s (score=%d)", best_entry["id"], best_score)
    else:
        log.debug("No match found")

    return best_entry


AUTO_RESPONSES_BY_ID: dict[str, dict] = {entry["id"]: entry for entry in AUTO_RESPONSES}


def auto_response_label(response_id: str) -> str:
    """Human readable name for an entry id, e.g. 'fund_transfer' -> 'Fund Transfer'."""
    return response_id.replace("_", " ").title()


def list_auto_responses() -> list[tuple[str, str]]:
    """Every entry as (id, label), in the order they are defined."""
    return [(entry["id"], auto_response_label(entry["id"])) for entry in AUTO_RESPONSES]


def get_auto_response(response_id: str) -> dict | None:
    """Look up a single entry by its id, or None if there is no such entry."""
    return AUTO_RESPONSES_BY_ID.get(response_id)
