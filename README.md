# Rocks Leader Ability

How many tech cards can a Rocks deck run before the leader ability starts whiffing too often?

This is a small Monte Carlo simulator that answers that. It plays the draw pattern of a game a few hundred thousand times and counts what happened.

## The ability

- 50 card deck. Some cards are "Rocks Pirates" type, the rest are tech cards.
- Before turn 1, 5 cards go to your hand and 5 become life cards, so the deck starts at 40. Tech cards that land there can never be revealed.
- Every turn you draw one card.
- Every turn after the first, you can use the leader ability: trash a card from hand, then reveal the top card of your deck.
  - **Hit** (it's a Rocks card): add it to hand and draw one more. Net +1 card after the trash.
  - **Miss** (it's a tech card): it stays on top of the deck. Net -1 card, you trashed for nothing.

## Run it

Needs Python 3 and nothing else.

```bash
python3 card_reveal_sim.py
```

## Results

50 card deck, 5 card starting hand, 5 life cards, game ends when the deck hits 15 cards left, 200,000 games per row.

| tech cards | miss per use | miss at least once per game | NET per use | NET per game |
|---|---|---|---|---|
| 0 | 0.0% | 0.0% | +1.00 | +8.00 |
| 1 | 2.0% | 16.0% | +0.96 | +7.84 |
| 2 | 3.9% | 29.7% | +0.92 | +7.67 |
| 3 | 5.9% | 41.3% | +0.88 | +7.50 |
| 4 | 7.8% | 51.3% | +0.84 | +7.30 |
| 5 | 9.8% | 59.8% | +0.80 | +7.09 |
| 10 | 19.7% | 85.7% | +0.61 | +5.79 |
| 20 | 39.6% | 98.9% | +0.21 | +2.33 |
| 25 | 49.5% | 99.8% | +0.01 | +0.11 |
| 30 | 59.5% | 100.0% | -0.19 | -2.59 |

NET is cards gained from the leader ability on top of your normal draw, after paying the trash.

## Takeaways

- **Each use misses with probability (tech cards / deck size).** One tech card is a 2% miss per use, two is 4%, and so on.
- **Over a whole game it adds up fast.** One tech card means you whiff at least once in 16% of games. Four tech cards is a coin flip.
- **Each tech card costs about 0.04 cards per use**, or roughly a fifth of a card over a game.
- **The opening 10 cards don't change the per-use odds.** A tech card is as likely to be in your opening hand or life as anywhere else, so each reveal still misses at (tech cards / deck size). What changes is the deck starts at 40, so you get about 8 uses before it hits 15.
- **The ability only becomes a net loss past 25 tech cards.** A hit is +1 and a miss is -1, so break-even is missing half the time. At realistic tech counts it's always worth using.
- **This counts cards, not card quality.** You pick what to trash, so in practice you're trading your worst card for two random ones.

## Settings

Everything adjustable is at the top of `card_reveal_sim.py`.

| setting | what it does |
|---|---|
| `DECK_SIZE` | Cards in the deck before anything is dealt. |
| `STARTING_HAND` | Cards dealt to hand before turn 1. |
| `LIFE_CARDS` | Cards set aside as life before turn 1. |
| `END_AT_CARDS_LEFT` | The game ends once the deck is at or below this. Set to 0 to play the deck out. |
| `MAX_TURNS` | The game also ends after this many turns. `None` for no limit. |
| `TECH_CARD_COUNTS` | Which tech card counts to test. One output row each. |
| `GAMES_PER_ROW` | Games simulated per row. More is more accurate and slower. |
| `RANDOM_SEED` | Fixed seed so results repeat between runs. |
| `TRASH_COST` | Cards trashed per use of the ability. |
| `CARDS_ON_HIT` | Cards gained on a hit (the revealed card plus the bonus draw). |

The two end conditions give different pictures. With `END_AT_CARDS_LEFT`, a miss mostly costs you a turn. With `MAX_TURNS`, every miss is a bonus draw you never get back.

## What it doesn't model

- Hand size, or running out of cards to trash.
- Choosing not to use the ability. It's used every turn it can be, since it's net positive at any realistic tech count.
- Searchers, shuffles, or anything else that changes the top of the deck.
- The opponent.
