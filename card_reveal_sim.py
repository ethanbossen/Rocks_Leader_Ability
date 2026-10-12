"""
How many tech cards should I put in my Rocks Deck?
=====================

Premise:

  * You have a 50 card deck. Some cards are the type "Rocks Pirates" (they meet your
    condition) and some are not (they don't).
  * Every turn you draw one card. That's the normal draw.
  * On every turn AFTER the first, you may use leader ability to first trash a card from hand then reveal the top card of the deck:
      - If it's a "Rocks Pirates" type card (a "hit"): you add it to hand, then draw one
        more card as a bonus. Thus, giving you one card draw for the turn, and two more cards with a sucuessful reveal.
        Although still down 1 card from the initial discard.
        So like a +3 -1 situation.
      - If it's not a "Rocks Pirates" type card (a "miss"): it stays on top of the deck and you are penalized by trashing a card with no reward.
        So like a +1/-1 deal.

The question: how often does a reveal miss, and how much does that cost you
as you add more tech cards to the deck?

The approach is "Monte Carlo": We simulate the pattern of game (kinda?) a few hundred thousand times with random shuffles and count
what happened. With that many games the averages land very close to the true probabilities.

Run it with:  python3 card_reveal_sim.py
"""

import random # <- for shuffle


# ---------------------------------------------------------------------------
# Globals :)
# ---------------------------------------------------------------------------

# Total number of cards in the deck at the start of the game.
DECK_SIZE = 50

# The game "ends" once the deck has this many cards left (or fewer).
# Set to 0 to sim until the deck is completely empty.
END_AT_CARDS_LEFT = 20

# The game also ends after this many turns (counting the first), whichever limit is hit first.
# Set to None for no turn limit.
# Note: This would be max turns on one side. Or max turns the Rocks player takes each sim run.
MAX_TURNS = None

# Which tech-card counts to test. Each one becomes a row in the output table.
# The big numbers at the end are only there to show where the leader ability stops being worth it.
TECH_CARD_COUNTS = [0, 1, 2, 3, 4, 5, 10, 20, 25, 30]

# How many games to simulate per row. More games = more accurate, but slower.
GAMES_PER_ROW = 200000

# The random seed.
RANDOM_SEED = 1

# --- What the leader ability costs and pays ---
TRASH_COST = 1      # cards you trash from hand every time you use it, hit or miss
CARDS_ON_HIT = 2    # the revealed Rocks card (+1) and the bonus draw (+1)

# NET = what the ability did to your card count, on top of your normal draw.
NET_ON_HIT = CARDS_ON_HIT - TRASH_COST      # +2 -1 = +1
NET_ON_MISS = -TRASH_COST                   #    -1 = -1


# ---------------------------------------------------------------------------
# ONE GAME
# ---------------------------------------------------------------------------

def build_shuffled_deck(tech_cards, rng):
    """
    Build a deck and shuffle it.

    The deck is just a list of True/False values:
        True  = a Rocks card, yippee!! draw!!
        False = a tech card     D:
    """
    rocks_cards = DECK_SIZE - tech_cards
    deck = [True] * rocks_cards + [False] * tech_cards
    rng.shuffle(deck)
    return deck


def game_is_over(turn, top):
    """The sim stops when the deck gets low enough, or when we run out of turns."""
    cards_left = DECK_SIZE - top
    deck_is_low = cards_left <= END_AT_CARDS_LEFT
    out_of_turns = MAX_TURNS is not None and turn >= MAX_TURNS
    return deck_is_low or out_of_turns


def can_use_leader_ability(turn, top):
    """You can use it any turn after the first, as long as the deck has a card to reveal."""
    after_first_turn = turn > 1
    deck_has_cards = top < DECK_SIZE
    return after_first_turn and deck_has_cards


def top_card_is_rocks(deck, top):
    """Reveal the top card. True = Rocks card (hit), False = tech card (miss)."""
    return deck[top]


def play_one_game(tech_cards, rng):
    """
    Play a single game and return a small summary of what happened.
    """
    deck = build_shuffled_deck(tech_cards, rng)

    top = 0     # index of the current top card of the deck
    turn = 0    # how many turns have been played so far
    uses = 0    # how many times we used the leader ability
    hits = 0    # how many of those uses revealed a Rocks card

    while not game_is_over(turn, top):

        # --- Step 1: start your turn & do your normal one card draw ---
        turn += 1
        top += 1

        # --- Step 2: leader ability ---
        if can_use_leader_ability(turn, top):
            uses += 1
            if top_card_is_rocks(deck, top):
                # W, take the revealed card (+1) and draw a bonus card (+1).
                hits += 1
                top += CARDS_ON_HIT
            # On a miss nothing moves: the tech card stays on top and you trashed for nothing dumbass

    misses = uses - hits
    net = hits * NET_ON_HIT + misses * NET_ON_MISS

    return {
        "turns": turn,
        "uses": uses,
        "hits": hits,
        "misses": misses,
        "net": net,     # cards gained from the leader ability this game, after paying the trashes
    }


# ---------------------------------------------------------------------------
# MANY GAMES
# ---------------------------------------------------------------------------

def simulate(tech_cards, rng):
    """
    Play GAMES_PER_ROW games with the given number of tech cards and return
    the averages.
    """
    # Running totals across every game. Same keys that play_one_game hands back.
    totals = {"turns": 0, "uses": 0, "hits": 0, "misses": 0, "net": 0}
    games_with_a_miss = 0   # games where at least one reveal missed

    for _ in range(GAMES_PER_ROW):
        game = play_one_game(tech_cards, rng)

        for stat in totals:
            totals[stat] += game[stat]

        if game["misses"] > 0:
            games_with_a_miss += 1

    return {
        # Chance that any single use is a miss. Should come out very
        # close to tech_cards / DECK_SIZE.
        "miss_chance_per_use": totals["misses"] / totals["uses"],

        # Chance that you miss at least once somewhere in the game.
        "chance_of_any_miss": games_with_a_miss / GAMES_PER_ROW,

        # Average cards gained each time you use the ability.
        # Positive = worth using. Negative = you lose cards on average by using it.
        "net_per_use": totals["net"] / totals["uses"],

        # Per-game averages.
        "avg_turns": totals["turns"] / GAMES_PER_ROW,
        "avg_uses": totals["uses"] / GAMES_PER_ROW,
        "avg_hits": totals["hits"] / GAMES_PER_ROW,
        "avg_misses": totals["misses"] / GAMES_PER_ROW,
        "avg_net": totals["net"] / GAMES_PER_ROW,
    }


# ---------------------------------------------------------------------------
# PRINT THE RESULTS
# ---------------------------------------------------------------------------

def main():
    rng = random.Random(RANDOM_SEED)

    turn_limit = "none" if MAX_TURNS is None else MAX_TURNS
    print(f"Deck size: {DECK_SIZE}   "
          f"End at cards left: {END_AT_CARDS_LEFT}   "
          f"Max turns: {turn_limit}   "
          f"Games per row: {GAMES_PER_ROW:,}")
    print()
    print("  tech   miss      miss at least   avg     avg     avg     avg      NET per   NET per")
    print("  cards  per use   once per game   turns   uses    hits    misses   use       game")
    print("  -----  -------   -------------   -----   -----   -----   ------   -------   -------")

    for tech_cards in TECH_CARD_COUNTS:
        r = simulate(tech_cards, rng)
        print(f"  {tech_cards:5d}"
              f"  {r['miss_chance_per_use']:7.1%}"
              f"   {r['chance_of_any_miss']:13.1%}"
              f"   {r['avg_turns']:5.2f}"
              f"   {r['avg_uses']:5.2f}"
              f"   {r['avg_hits']:5.2f}"
              f"   {r['avg_misses']:6.2f}"
              f"   {r['net_per_use']:+7.2f}"
              f"   {r['avg_net']:+7.2f}")

if __name__ == "__main__":
    main()
