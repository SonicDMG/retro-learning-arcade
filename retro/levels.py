"""Turning a player's age into a difficulty tier.

One place decides how hard everything is, so a nine-year-old is not offered
counting ducks and a five-year-old is not shown long division. Games read the
tier rather than inventing their own idea of "hard".

Tiers, roughly:

    1  ages 5-6    counting, numbers to 10, first patterns
    2  ages 7-8    numbers to 20-100, times tables of 2, 5 and 10, word problems
    3  ages 9-10   multiplication and division facts, numbers to 1000
    4  ages 11-12  two-digit multiplication, two-step word problems

A child can still nudge the level up or down in the menus; the age only sets
the starting point.
"""

MIN_AGE = 5
MAX_AGE = 12
DEFAULT_TIER = 2
MIN_TIER = 1
MAX_TIER = 4

AGE_BANDS = (
    (6, 1),
    (8, 2),
    (10, 3),
)

TIER_NAMES = {
    1: "STARTER",
    2: "GROWING",
    3: "TRICKY",
    4: "EXPERT",
}

# How far a player may nudge the level away from their age's tier.
NUDGES = (-1, 0, 1)
NUDGE_NAMES = {-1: "EASIER", 0: "JUST RIGHT", 1: "HARDER"}


def tier_for_age(age):
    """Map an age to a tier. Unknown ages get the middle of the road."""
    if age is None:
        return DEFAULT_TIER
    try:
        age = int(age)
    except (TypeError, ValueError):
        return DEFAULT_TIER
    for limit, tier in AGE_BANDS:
        if age <= limit:
            return tier
    return MAX_TIER


def clamp_tier(tier):
    return max(MIN_TIER, min(MAX_TIER, int(tier)))


def tier_for(age, nudge=0):
    """The tier a player actually plays at, after any easier/harder nudge."""
    return clamp_tier(tier_for_age(age) + nudge)


def tier_name(tier):
    return TIER_NAMES.get(clamp_tier(tier), "")
