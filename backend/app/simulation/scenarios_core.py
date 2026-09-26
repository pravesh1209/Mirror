"""12 hand-authored MIRROR calibration scenarios.

Coverage:
  4x everyday, 3x education (2 with reveal), 2x career (1 with reveal),
  2x finance, 1x productivity
  3 scenarios have has_reveal=True (to exercise adaptability)
  1 scenario has a time limit (to exercise time_pressure_response)

Attribute values are the design; changing them changes what MIRROR can
learn. Do not casually edit. If you edit, update _assert_count below.
"""
from __future__ import annotations

SCENARIOS: list[dict] = [
    # -------- EVERYDAY ------------------------------------------------
    {
        "domain": "everyday",
        "title": "Getting across town",
        "body": (
            "You need to get across town for a meeting that starts in 30 minutes. "
            "You have $40 with you. Traffic is unpredictable today."
        ),
        "difficulty": 0.35, "risk": 0.35, "uncertainty": 0.55,
        "time_pressure": 0.7, "novelty": 0.3, "reward": 0.5,
        "information_availability": 0.7,
        "time_limit_sec": 25, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "Bus", "description": "Cheap, but timing depends on traffic.",
             "risk": 0.3, "time_cost": 0.8, "money_cost": 0.1,
             "novelty": 0.2, "uncertainty": 0.6,
             "info_availability": 0.7, "reward": 0.4, "is_novel": False},
            {"label": "B", "title": "Rideshare", "description": "Fast and direct, but expensive today.",
             "risk": 0.4, "time_cost": 0.2, "money_cost": 0.8,
             "novelty": 0.3, "uncertainty": 0.3,
             "info_availability": 0.9, "reward": 0.7, "is_novel": False},
            {"label": "C", "title": "Bike share", "description": "Reliable if the weather holds.",
             "risk": 0.5, "time_cost": 0.5, "money_cost": 0.2,
             "novelty": 0.7, "uncertainty": 0.6,
             "info_availability": 0.6, "reward": 0.5, "is_novel": True},
        ],
    },
    {
        "domain": "everyday",
        "title": "Last-minute dinner",
        "body": (
            "It is 7 pm and you have not eaten. You have $25 and 45 minutes "
            "before a call. Three options are nearby."
        ),
        "difficulty": 0.25, "risk": 0.2, "uncertainty": 0.4,
        "time_pressure": 0.6, "novelty": 0.4, "reward": 0.6,
        "information_availability": 0.8,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "Familiar takeout", "description": "You know it works. Slightly boring.",
             "risk": 0.1, "time_cost": 0.3, "money_cost": 0.4,
             "novelty": 0.1, "uncertainty": 0.1,
             "info_availability": 1.0, "reward": 0.6, "is_novel": False},
            {"label": "B", "title": "New cafe", "description": "Looks good but you have not tried it.",
             "risk": 0.5, "time_cost": 0.5, "money_cost": 0.4,
             "novelty": 0.8, "uncertainty": 0.6,
             "info_availability": 0.4, "reward": 0.7, "is_novel": True},
            {"label": "C", "title": "Quick grocery run", "description": "Cheap and predictable, takes time.",
             "risk": 0.15, "time_cost": 0.7, "money_cost": 0.15,
             "novelty": 0.2, "uncertainty": 0.2,
             "info_availability": 0.9, "reward": 0.5, "is_novel": False},
        ],
    },
    {
        "domain": "everyday",
        "title": "A purchase you have been putting off",
        "body": (
            "You need to replace a device you use daily. Three models are "
            "available at similar price points. You will keep it for years."
        ),
        "difficulty": 0.5, "risk": 0.5, "uncertainty": 0.6,
        "time_pressure": 0.3, "novelty": 0.5, "reward": 0.7,
        "information_availability": 0.7,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "The safe brand", "description": "Boring but reliable. Everyone owns one.",
             "risk": 0.2, "time_cost": 0.3, "money_cost": 0.5,
             "novelty": 0.1, "uncertainty": 0.2,
             "info_availability": 0.9, "reward": 0.6, "is_novel": False},
            {"label": "B", "title": "The cheaper unknown", "description": "Half the reviews, much lower price.",
             "risk": 0.7, "time_cost": 0.4, "money_cost": 0.2,
             "novelty": 0.7, "uncertainty": 0.7,
             "info_availability": 0.4, "reward": 0.5, "is_novel": True},
            {"label": "C", "title": "The premium model", "description": "Best specs, highest cost, most unknowns.",
             "risk": 0.6, "time_cost": 0.5, "money_cost": 0.9,
             "novelty": 0.5, "uncertainty": 0.5,
             "info_availability": 0.8, "reward": 0.85, "is_novel": False},
        ],
    },
    {
        "domain": "everyday",
        "title": "How to spend a free Saturday",
        "body": (
            "You have a rare free Saturday. A local community group has asked "
            "for a few hours of help, an unfamiliar side project has been on "
            "your mind for weeks, and there is also the option of doing "
            "nothing and genuinely resting."
        ),
        "difficulty": 0.35, "risk": 0.3, "uncertainty": 0.5,
        "time_pressure": 0.25, "novelty": 0.6, "reward": 0.65,
        "information_availability": 0.5,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "Help the community group",
             "description": "Familiar cause, unclear how much it will matter.",
             "risk": 0.3, "time_cost": 0.6, "money_cost": 0.1,
             "novelty": 0.3, "uncertainty": 0.5,
             "info_availability": 0.6, "reward": 0.6, "is_novel": False},
            {"label": "B", "title": "Work on the unfamiliar side project",
             "description": "Real upside but you do not know where to start.",
             "risk": 0.6, "time_cost": 0.8, "money_cost": 0.1,
             "novelty": 0.85, "uncertainty": 0.75,
             "info_availability": 0.3, "reward": 0.85, "is_novel": True},
            {"label": "C", "title": "Do nothing and rest",
             "description": "Low risk of regret, low visible output.",
             "risk": 0.1, "time_cost": 0.1, "money_cost": 0.0,
             "novelty": 0.1, "uncertainty": 0.1,
             "info_availability": 1.0, "reward": 0.5, "is_novel": False},
        ],
    },

    # -------- EDUCATION -----------------------------------------------
    {
        "domain": "education",
        "title": "How to study for a hard exam",
        "body": (
            "You have 4 days before an exam that will heavily affect your "
            "grade. You can prepare in one of three ways. You cannot do all three."
        ),
        "difficulty": 0.6, "risk": 0.6, "uncertainty": 0.5,
        "time_pressure": 0.6, "novelty": 0.4, "reward": 0.8,
        "information_availability": 0.6,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "Cover everything lightly", "description": "Broad but shallow across the syllabus.",
             "risk": 0.4, "time_cost": 0.6, "money_cost": 0.0,
             "novelty": 0.3, "uncertainty": 0.5,
             "info_availability": 0.7, "reward": 0.6, "is_novel": False},
            {"label": "B", "title": "Go deep on the hardest topic", "description": "Ignores the rest of the syllabus.",
             "risk": 0.7, "time_cost": 0.5, "money_cost": 0.0,
             "novelty": 0.5, "uncertainty": 0.7,
             "info_availability": 0.4, "reward": 0.85, "is_novel": False},
            {"label": "C", "title": "Practice with past papers only", "description": "Ignores theory, focuses on recall.",
             "risk": 0.5, "time_cost": 0.4, "money_cost": 0.1,
             "novelty": 0.4, "uncertainty": 0.4,
             "info_availability": 0.8, "reward": 0.7, "is_novel": False},
        ],
    },
    {
        "domain": "education",
        "title": "An unplanned course opportunity",
        "body": (
            "A short course opens tomorrow. It is unusual, intensive, and "
            "would replace your usual study plan for the week."
        ),
        "difficulty": 0.5, "risk": 0.5, "uncertainty": 0.7,
        "time_pressure": 0.5, "novelty": 0.85, "reward": 0.7,
        "information_availability": 0.4,
        "time_limit_sec": None, "has_reveal": True,
        "reveal_payload": {"info": "The course has moved to a fully online format, which changes the time cost."},
        "options": [
            {"label": "A", "title": "Enrol", "description": "Commit now, deal with the schedule later.",
             "risk": 0.7, "time_cost": 0.6, "money_cost": 0.4,
             "novelty": 0.9, "uncertainty": 0.7,
             "info_availability": 0.3, "reward": 0.8, "is_novel": True},
            {"label": "B", "title": "Skip it", "description": "Stay with your existing plan.",
             "risk": 0.2, "time_cost": 0.2, "money_cost": 0.0,
             "novelty": 0.1, "uncertainty": 0.2,
             "info_availability": 0.9, "reward": 0.5, "is_novel": False},
            {"label": "C", "title": "Ask a mentor first", "description": "Delay the decision by one day.",
             "risk": 0.4, "time_cost": 0.4, "money_cost": 0.0,
             "novelty": 0.4, "uncertainty": 0.4,
             "info_availability": 0.6, "reward": 0.6, "is_novel": False},
        ],
    },
    {
        "domain": "education",
        "title": "Choosing a project partner",
        "body": (
            "You must choose a partner for a semester-long project. Three "
            "classmates have asked. You have worked with none of them before."
        ),
        "difficulty": 0.5, "risk": 0.6, "uncertainty": 0.7,
        "time_pressure": 0.4, "novelty": 0.55, "reward": 0.7,
        "information_availability": 0.4,
        "time_limit_sec": None, "has_reveal": True,
        "reveal_payload": {"info": "A mutual friend tells you one of the three has a history of dropping courses late in the semester."},
        "options": [
            {"label": "A", "title": "The high-performer you barely know", "description": "Strong reputation, no personal history.",
             "risk": 0.6, "time_cost": 0.3, "money_cost": 0.0,
             "novelty": 0.7, "uncertainty": 0.7,
             "info_availability": 0.4, "reward": 0.85, "is_novel": True},
            {"label": "B", "title": "The friend you already trust", "description": "Lower ceiling, much less risk.",
             "risk": 0.2, "time_cost": 0.3, "money_cost": 0.0,
             "novelty": 0.15, "uncertainty": 0.25,
             "info_availability": 0.9, "reward": 0.6, "is_novel": False},
            {"label": "C", "title": "The quiet one with a good portfolio", "description": "Evidence from their work, not from people.",
             "risk": 0.45, "time_cost": 0.4, "money_cost": 0.0,
             "novelty": 0.55, "uncertainty": 0.5,
             "info_availability": 0.6, "reward": 0.7, "is_novel": False},
        ],
    },

    # -------- CAREER --------------------------------------------------
    {
        "domain": "career",
        "title": "Two job offers, very different shapes",
        "body": (
            "You have two offers. One is stable with a familiar team. The "
            "other is a smaller, riskier company with a steeper learning curve."
        ),
        "difficulty": 0.7, "risk": 0.7, "uncertainty": 0.6,
        "time_pressure": 0.4, "novelty": 0.6, "reward": 0.8,
        "information_availability": 0.6,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "The stable offer", "description": "Known work, known people, predictable pay.",
             "risk": 0.25, "time_cost": 0.3, "money_cost": 0.1,
             "novelty": 0.2, "uncertainty": 0.25,
             "info_availability": 0.9, "reward": 0.65, "is_novel": False},
            {"label": "B", "title": "The risky offer", "description": "More upside, less certainty, steeper curve.",
             "risk": 0.8, "time_cost": 0.5, "money_cost": 0.3,
             "novelty": 0.85, "uncertainty": 0.75,
             "info_availability": 0.4, "reward": 0.9, "is_novel": True},
            {"label": "C", "title": "Negotiate for time", "description": "Ask both for a week to decide.",
             "risk": 0.5, "time_cost": 0.4, "money_cost": 0.1,
             "novelty": 0.4, "uncertainty": 0.4,
             "info_availability": 0.7, "reward": 0.6, "is_novel": False},
        ],
    },
    {
        "domain": "career",
        "title": "An unexpected internal move",
        "body": (
            "Your manager offers you a lateral move into a team you do not "
            "know. It is framed as an opportunity but not as a promotion. "
            "You must answer within the day."
        ),
        "difficulty": 0.6, "risk": 0.6, "uncertainty": 0.7,
        "time_pressure": 0.75, "novelty": 0.7, "reward": 0.7,
        "information_availability": 0.5,
        "time_limit_sec": None, "has_reveal": True,
        "reveal_payload": {"info": "A colleague privately tells you the new team has had two managers in six months."},
        "options": [
            {"label": "A", "title": "Accept immediately", "description": "Say yes today, learn on the way.",
             "risk": 0.7, "time_cost": 0.2, "money_cost": 0.1,
             "novelty": 0.8, "uncertainty": 0.7,
             "info_availability": 0.3, "reward": 0.75, "is_novel": True},
            {"label": "B", "title": "Decline politely", "description": "Stay in your current role.",
             "risk": 0.2, "time_cost": 0.2, "money_cost": 0.1,
             "novelty": 0.15, "uncertainty": 0.25,
             "info_availability": 0.9, "reward": 0.55, "is_novel": False},
            {"label": "C", "title": "Ask for a two-week trial", "description": "Try before committing.",
             "risk": 0.4, "time_cost": 0.5, "money_cost": 0.1,
             "novelty": 0.5, "uncertainty": 0.4,
             "info_availability": 0.6, "reward": 0.7, "is_novel": False},
        ],
    },

    # -------- FINANCE -------------------------------------------------
    {
        "domain": "finance",
        "title": "Where the extra $500 goes",
        "body": (
            "You have an unexpected $500. You can only put it in one place "
            "this month."
        ),
        "difficulty": 0.4, "risk": 0.5, "uncertainty": 0.4,
        "time_pressure": 0.2, "novelty": 0.35, "reward": 0.6,
        "information_availability": 0.8,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "Emergency fund", "description": "Safe, boring, slow.",
             "risk": 0.1, "time_cost": 0.2, "money_cost": 0.0,
             "novelty": 0.1, "uncertainty": 0.15,
             "info_availability": 1.0, "reward": 0.5, "is_novel": False},
            {"label": "B", "title": "A single stock", "description": "High upside, real chance of loss.",
             "risk": 0.9, "time_cost": 0.4, "money_cost": 0.0,
             "novelty": 0.6, "uncertainty": 0.8,
             "info_availability": 0.5, "reward": 0.9, "is_novel": False},
            {"label": "C", "title": "Pay down existing debt", "description": "Quietly reduces a monthly cost.",
             "risk": 0.15, "time_cost": 0.2, "money_cost": 0.0,
             "novelty": 0.15, "uncertainty": 0.2,
             "info_availability": 0.9, "reward": 0.65, "is_novel": False},
        ],
    },
    {
        "domain": "finance",
        "title": "An unfamiliar investment",
        "body": (
            "A friend mentions an unfamiliar investment they have done well "
            "with. You have a small amount you could put in this month."
        ),
        "difficulty": 0.6, "risk": 0.85, "uncertainty": 0.85,
        "time_pressure": 0.3, "novelty": 0.85, "reward": 0.85,
        "information_availability": 0.3,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "Put in a small amount", "description": "Treat it as a learning bet.",
             "risk": 0.7, "time_cost": 0.4, "money_cost": 0.4,
             "novelty": 0.9, "uncertainty": 0.85,
             "info_availability": 0.3, "reward": 0.8, "is_novel": True},
            {"label": "B", "title": "Read about it first", "description": "Research for a week before deciding.",
             "risk": 0.4, "time_cost": 0.7, "money_cost": 0.0,
             "novelty": 0.5, "uncertainty": 0.4,
             "info_availability": 0.7, "reward": 0.6, "is_novel": False},
            {"label": "C", "title": "Say no", "description": "Not interested in unfamiliar bets.",
             "risk": 0.1, "time_cost": 0.1, "money_cost": 0.0,
             "novelty": 0.1, "uncertainty": 0.1,
             "info_availability": 1.0, "reward": 0.4, "is_novel": False},
        ],
    },

    # -------- PRODUCTIVITY --------------------------------------------
    {
        "domain": "productivity",
        "title": "A day with too many open threads",
        "body": (
            "You have six things to do today and time for about three. "
            "Two of them are urgent but low-impact. One is high-impact but "
            "unbounded in time."
        ),
        "difficulty": 0.55, "risk": 0.5, "uncertainty": 0.5,
        "time_pressure": 0.7, "novelty": 0.4, "reward": 0.7,
        "information_availability": 0.6,
        "time_limit_sec": None, "has_reveal": False, "reveal_payload": None,
        "options": [
            {"label": "A", "title": "Clear the urgent items", "description": "Handle the loud things first.",
             "risk": 0.3, "time_cost": 0.4, "money_cost": 0.0,
             "novelty": 0.2, "uncertainty": 0.3,
             "info_availability": 0.9, "reward": 0.55, "is_novel": False},
            {"label": "B", "title": "Block the whole day for the high-impact one", "description": "Ignore everything else.",
             "risk": 0.6, "time_cost": 0.8, "money_cost": 0.0,
             "novelty": 0.5, "uncertainty": 0.6,
             "info_availability": 0.5, "reward": 0.85, "is_novel": False},
            {"label": "C", "title": "Try to touch everything briefly", "description": "Spread attention across all six.",
             "risk": 0.55, "time_cost": 0.6, "money_cost": 0.0,
             "novelty": 0.4, "uncertainty": 0.6,
             "info_availability": 0.7, "reward": 0.6, "is_novel": False},
        ],
    },
]


# Guard: keep the count in sync with the design doc.
# If this assertion fails, update _assert_count above AND the design doc.
_assert_count = 12
assert len(SCENARIOS) == _assert_count, (
    f"scenarios_core.py must contain exactly {_assert_count} scenarios, "
    f"found {len(SCENARIOS)}"
)


__all__ = ["SCENARIOS"]