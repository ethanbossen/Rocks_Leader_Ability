"""
How many tech cards should I put in my Rocks Deck?
==================================================

The rules this sim follows:

  * You have a 50 card deck. Some cards are "Rocks Pirates" type and the rest
    are tech cards.
  * Before turn 1, you deal 5 cards to your hand and 5 life cards off the top.
    So the deck really starts at 40.
  * Every turn you draw one card. That's the normal draw and it always happens.
  * On every turn AFTER the first, you use the leader ability: trash a card
    from hand, then reveal the top card of the deck.
      - Hit (it's a Rocks card): add it to hand, then draw one more.
        That's 2 cards for the price of 1 trash, so you come out +1.
      - Miss (it's a tech card): it stays on top of the deck and you get nothing.
        You paid 1 trash for 0 cards, so you come out -1.

The +1 and -1 are what this file calls NET. It only counts what the leader
ability did for you. The normal draw isn't included, because you get that
whether you use the ability or not.

The question: how often does the ability miss, and how much does that cost
you as you add more tech cards?

How it gets answered: instead of doing the math by hand, we shuffle a deck,
play the turns, and write down what happened. Then we do that a couple hundred
thousand more times and average it. That trick is called "Monte Carlo", and
with that many games the averages land very close to the true odds.

How to read this file: start at the bottom. main() prints the table,
simulate() plays lots of games, play_one_game() plays one, and the small
functions above it each answer one simple question.

Run it with:  python3 card_reveal_sim.py
"""

import random # <- for shuffle


# ---------------------------------------------------------------------------
# Globals :)
# These are the knobs. Change a number, run it again, see what moves.
# ---------------------------------------------------------------------------

# How many cards are in the deck before anything gets dealt.
DECK_SIZE = 50

# Cards that come off the top of the deck before turn 1.
# If a tech card ends up here, the leader ability can never reveal it.
STARTING_HAND = 5
LIFE_CARDS = 5

# The game "ends" once the deck is down to this many cards (or fewer).
# Set it to 0 to keep going until the deck is empty.
END_AT_CARDS_LEFT = 15

# The game also ends after this many of your turns (counting the first).
# Whichever limit gets hit first wins. Set it to None for no turn limit.
MAX_TURNS = None

# Which tech card counts to try. Each one becomes a row in the table.
# The big numbers at the end are only there to show where the leader ability stops being worth it.
TECH_CARD_COUNTS = [0, 1, 2, 3, 4, 5, 10, 20, 25, 30]

# How many games to play for each row. More games = more accurate, but slower.
GAMES_PER_ROW = 200000

# The random seed. Same seed = same shuffles = same results every time you run it.
# That way, if a number changes, you know it's because of something you changed.
RANDOM_SEED = 1

# --- What the leader ability costs and what it pays ---
TRASH_COST = 1      # cards you trash from hand every time you use it, hit or miss
CARDS_ON_HIT = 2    # the Rocks card you revealed (+1) and the bonus draw (+1)

# NET = how many cards the ability gained you, after paying the trash.
NET_ON_HIT = CARDS_ON_HIT - TRASH_COST      # +2 -1 = +1
NET_ON_MISS = -TRASH_COST                   #    -1 = -1


# ---------------------------------------------------------------------------
# ONE GAME
# ---------------------------------------------------------------------------

def build_shuffled_deck(tech_cards, rng):
    """
    Build a deck and shuffle it.

    We don't care what the cards actually are, only whether each one is a
    Rocks card or not. So the deck is just a list of True/False values:
        True  = a Rocks card, yippee!! draw!!
        False = a tech card     D:
    """
    rocks_cards = DECK_SIZE - tech_cards

    # [True] * 3 makes [True, True, True], and + sticks two lists together.
    # So this is all the Rocks cards followed by all the tech cards...
    deck = [True] * rocks_cards + [False] * tech_cards

    # ...which is why we shuffle it.
    rng.shuffle(deck)
    return deck


def game_is_over(turn, top):
    """Are we done? Yes if the deck is low enough, or if we're out of turns."""
    cards_left = DECK_SIZE - top
    deck_is_low = cards_left <= END_AT_CARDS_LEFT
    out_of_turns = MAX_TURNS is not None and turn >= MAX_TURNS
    return deck_is_low or out_of_turns


def can_use_leader_ability(turn, top):
    """Can we use it? Yes on any turn after the first, as long as there's a card to reveal."""
    after_first_turn = turn > 1
    deck_has_cards = top < DECK_SIZE
    return after_first_turn and deck_has_cards


def top_card_is_rocks(deck, top):
    """Flip the top card. True = Rocks card (hit), False = tech card (miss)."""
    return deck[top]


def play_one_game(tech_cards, rng):
    """
    Play one game and report what happened.

    We never actually remove cards from the deck list. Instead, `top` keeps
    track of which position is the top card right now. Drawing a card just
    means moving `top` forward by one.

        deck:  [ T  T  F  T  T  T  F  T ... ]
                          ^
                         top   (everything to the left is already drawn)
    """
    deck = build_shuffled_deck(tech_cards, rng)

    # Deal the starting hand and life cards by skipping past them.
    top = STARTING_HAND + LIFE_CARDS

    turn = 0    # how many turns we've played
    uses = 0    # how many times we used the leader ability
    hits = 0    # how many of those uses flipped a Rocks card

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
            # On a miss nothing moves. The tech card stays on top and you trashed for nothing, rip

    # Every use is either a hit or a miss, so whatever wasn't a hit was a miss.
    misses = uses - hits
    net = hits * NET_ON_HIT + misses * NET_ON_MISS

    return {
        "uses": uses,
        "hits": hits,
        "misses": misses,
        "net": net,     # cards the leader ability gained us this game, after paying the trashes
    }


# ---------------------------------------------------------------------------
# MANY GAMES
# ---------------------------------------------------------------------------

def average(total, count):
    """Plain old average. Gives 0 instead of crashing if there was nothing to count."""
    if count == 0:
        return 0
    return total / count


def simulate(tech_cards):
    """
    Play GAMES_PER_ROW games with this many tech cards and return the averages.
    """
    # A fresh random generator for every row, so one row can't affect another.
    rng = random.Random(RANDOM_SEED)

    # Running totals across all the games.
    total_uses = 0
    total_hits = 0
    total_misses = 0
    total_net = 0
    games_with_a_miss = 0   # games where the ability missed at least once

    for _ in range(GAMES_PER_ROW):
        game = play_one_game(tech_cards, rng)

        total_uses += game["uses"]
        total_hits += game["hits"]
        total_misses += game["misses"]
        total_net += game["net"]

        if game["misses"] > 0:
            games_with_a_miss += 1

    return {
        # Out of every time we used the ability, how often did it miss?
        # This should come out very close to tech_cards / DECK_SIZE.
        "miss_chance_per_use": average(total_misses, total_uses),

        # Out of every game, how often did we miss at least once?
        "chance_of_any_miss": average(games_with_a_miss, GAMES_PER_ROW),

        # Cards gained each time we use the ability, on average.
        # Positive = worth using. Negative = using it loses you cards.
        "net_per_use": average(total_net, total_uses),

        # What a typical game looks like.
        "avg_uses": average(total_uses, GAMES_PER_ROW),
        "avg_hits": average(total_hits, GAMES_PER_ROW),
        "avg_misses": average(total_misses, GAMES_PER_ROW),
        "avg_net": average(total_net, GAMES_PER_ROW),
    }


# ---------------------------------------------------------------------------
# PRINT THE RESULTS
# ---------------------------------------------------------------------------

def main():
    # First, print the settings so you know what you're looking at.
    turn_limit = "none" if MAX_TURNS is None else MAX_TURNS
    print(f"Deck size: {DECK_SIZE}   "
          f"Starting hand: {STARTING_HAND}   "
          f"Life cards: {LIFE_CARDS}   "
          f"End at cards left: {END_AT_CARDS_LEFT}   "
          f"Max turns: {turn_limit}   "
          f"Games per row: {GAMES_PER_ROW:,}")
    print()
    print("  tech   miss      miss at least   avg     avg     avg      NET per   NET per")
    print("  cards  per use   once per game   uses    hits    misses   use       game")
    print("  -----  -------   -------------   -----   -----   ------   -------   -------")

    # Then one row per tech card count.
    # The bits after each colon are just formatting so the columns line up:
    #   5d    = a whole number, 5 characters wide
    #   7.1%  = a percent with 1 decimal, 7 wide
    #   5.2f  = a decimal number with 2 decimals, 5 wide
    #   +7.2f = same, but always show the + or - sign
    for tech_cards in TECH_CARD_COUNTS:
        r = simulate(tech_cards)
        print(f"  {tech_cards:5d}"
              f"  {r['miss_chance_per_use']:7.1%}"
              f"   {r['chance_of_any_miss']:13.1%}"
              f"   {r['avg_uses']:5.2f}"
              f"   {r['avg_hits']:5.2f}"
              f"   {r['avg_misses']:6.2f}"
              f"   {r['net_per_use']:+7.2f}"
              f"   {r['avg_net']:+7.2f}")

if __name__ == "__main__":
    main()
