# Retro Learning Arcade

![Number Blaster, Word Rocket and Pattern Power](docs/screenshots/banner.png)

Five little learning games for kids, in Python, with chunky 8-bit graphics and
chiptune bleeps. They stretch from five-year-olds counting ducks to
twelve-year-olds doing two-digit multiplication and matrix reasoning: big
buttons, nothing to lose, and a star for every question answered right on the
first go.

**Each player is asked their age once**, and that sets how hard everything is
— which maths modes even appear, how big the numbers get, and how tricky the
puzzles are. A child can still nudge the level easier or harder in any menu.

Everything is drawn onto a 320x180 pixel screen and then blown up to fill the
window, which is what gives it the retro look. The game itself loads no image
or sound files at all: the pictures are hand-drawn pixel grids in
`retro/sprites.py` and every sound is a square wave generated at startup.
(The PNGs above live in `docs/` for this README, and the game never touches
them.)

## What it looks like

<p align="center">
  <img src="docs/screenshots/arcade.png" width="420" alt="The game shelf, showing three games and a star total">
  <img src="docs/screenshots/counting.png" width="420" alt="Counting mode, with six ducks to count">
</p>
<p align="center">
  <img src="docs/screenshots/word-rocket.png" width="420" alt="Word Rocket, with a cat picture and the word C_T">
  <img src="docs/screenshots/pattern-power.png" width="420" alt="Pattern Power, with a star-apple-star-apple pattern">
</p>
<p align="center">
  <img src="docs/screenshots/crystal-keys.png" width="420" alt="Crystal Keys, typing the word PHOENIX with the next key lit on an on-screen keyboard">
  <img src="docs/screenshots/logic-lab.png" width="420" alt="Logic Lab, a matrix puzzle with one cell missing">
</p>
<p align="center">
  <img src="docs/screenshots/story-problem.png" width="420" alt="A story problem naming the player: Juni has 18 marbles and gives away 7">
  <img src="docs/screenshots/scoreboard.png" width="420" alt="The scoreboard: stars, crystals, rounds played and best score per game">
</p>

Every screenshot is a real frame from the game, scanlines and all, produced by
`tools/screenshots.py`. Re-run it after a UI change to refresh them.

## Running it

### With uv (recommended)

[uv](https://docs.astral.sh/uv/) handles Python and pygame for you, so there
is no virtual environment to think about. Play without cloning anything:

```sh
uvx --from git+https://github.com/SonicDMG/retro-learning-arcade retro-arcade
```

From a clone, it's one command — uv reads `pyproject.toml`, installs what's
missing and starts the game:

```sh
git clone https://github.com/SonicDMG/retro-learning-arcade.git
cd retro-learning-arcade
uv run retro-arcade
```

To keep it on the machine as a normal command:

```sh
uv tool install git+https://github.com/SonicDMG/retro-learning-arcade
retro-arcade
```

`uv.lock` pins the exact pygame build, so every machine gets the same one.

#### Installing uv

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or, if you use Homebrew, `brew install uv`. It installs to `~/.local/bin`,
which may not be on your `PATH` until you open a new terminal window — so if
`uv` is "not found" straight after installing, that is why. `run.command`
knows about this and looks there directly.

You don't have to install it by hand: double-clicking `run.command` on a Mac
without uv offers to fetch it for you, and falls back to a plain virtual
environment if you say no.

### On the Mac, without touching a terminal

1. Copy this folder anywhere you like (Documents is fine).
2. Double-click **`run.command`**.

It uses uv if it finds it, and otherwise falls back to building a plain
virtual environment with the system Python — so it works either way. The
first run takes a minute; after that it starts straight away.

If macOS refuses to open it ("unidentified developer"), right-click
`run.command` → **Open** → **Open**. That only has to be done once.

### Without uv

```sh
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python launcher.py
```

macOS ships with a usable `python3`; if it's missing, the launcher will say so
and point at python.org.

### Where progress is saved

Run from a clone, the save file sits in `saves/progress.json` next to the
code. Installed as a tool, it goes to the platform's user data directory
(`~/Library/Application Support/RetroLearningArcade` on macOS) — writing
inside the installed package would mean a reinstall quietly wiped the kids'
stars. Set `RETRO_ARCADE_SAVE_DIR` to put it anywhere else.

## The games

### How age sets the level

One table decides difficulty everywhere, in `retro/levels.py`:

| Tier | Ages | Maths | Reasoning |
| --- | --- | --- | --- |
| Starter | 5–6 | Counting, numbers to 10 | Repeating patterns |
| Growing | 7–8 | Times tables of 2, 5, 10; division; story problems; numbers to 30 | Odd one out, analogies, matrices, sequences |
| Tricky | 9–10 | Tables to 12×12, division facts, numbers to 150 | Multiply-rule sequences |
| Expert | 11–12 | Two-digit multiplication, two-step story problems, numbers to 999 | Squares, triangular numbers, Fibonacci |

A five-year-old is never offered division; an eight-year-old is never offered
counting ducks. The **EASIER / JUST RIGHT / HARDER** buttons in each menu
shift one tier either way without changing the saved age.

**Number Blaster** — ten questions a round. Which of these appear depends on
the player's age:

| Mode | What it practises |
| --- | --- |
| Count | Counting a group of pictures |
| Add + | Addition, capped per tier |
| Take away − | Subtraction, never below zero |
| Times × | Multiplication, from the 2/5/10 tables up to two-digit |
| Share ÷ | Division, always exact — built from the answer up |
| Story | Word problems, using the player's own name |
| More or less | Comparing two numbers |

**Word Rocket** — a picture appears and the word sits underneath:

| Mode | What it practises |
| --- | --- |
| First letter | Initial sounds |
| Missing letter | Letter sounds anywhere in a word |
| Spell it! | Building the whole word, left to right |

**Pattern Power** — a sequence appears with the last slot blank:

| Mode | What it practises |
| --- | --- |
| Pictures | Repeating patterns (AB, ABB, AAB, ABC) |
| Colours | The same idea, without any picture naming |
| Numbers | Counting on and back in 1s, 2s, 5s and 10s |

**Logic Lab** — reasoning puzzles in the style of an IQ test, from about age
seven up:

| Mode | What it asks |
| --- | --- |
| Odd one out | Four figures; three share a property and one does not |
| Analogy | A is to B as C is to ? |
| Matrix | A grid where the row sets the shape and the column the colour, with one cell missing |
| Sequences | Number series: steps, doubling, alternating, squares, triangular numbers, Fibonacci |

The figures are drawn from primitives rather than sprites, so shape, colour
and size vary independently — that is what lets an item test one property
while deliberately scrambling the others.

Every item is built to have exactly **one** defensible answer. In odd-one-out
the properties that are not the point of the puzzle are laid out in pairs, so
none of them accidentally singles out a second figure. A puzzle with two
right answers marks a thinking child wrong, which is worse than no puzzle.

**Crystal Keys** — a typing tutor, for around ages 7-9. Four elemental realms,
which are really keyboard lessons in disguise:

| Realm | Keys it uses | What it practises |
| --- | --- | --- |
| 🌱 Earth | Home row only (`asdfghjkl`) | Finding the home keys without looking |
| 💧 Water | Adds the top row (`qwertyuiop`) | Reaching up and coming back |
| ☁️ Air | Adds the bottom row (`zxcvbnm`) | The whole alphabet |
| 🔥 Fire | Everything, longer words | Speed and stamina |

Each realm starts with pure drills (`asdf`, `jkl`) and moves on to themed
words. A wrong key never ends anything — the letter simply refuses to advance,
the way a real typing tutor works, so fingers learn the correct key instead of
racing past it. An on-screen keyboard lights up the next key to press, and
Caps Lock doesn't matter.

Finishing a realm earns **crystals**: one for completing it, one for 90%
accuracy or better, and one more for a flawless round. They're deliberately
rarer than stars.

Three difficulty levels (EASY / OK / HARD) set the number ranges in Number
Blaster. A six-year-old usually wants EASY or OK.

## How it plays

Pick a player (Juni, Sage or Other), pick a game, answer the round.
Answers can be clicked with the mouse or chosen with the `1` `2` `3` keys; in
Word Rocket the child can also just press the letter key.

A wrong answer costs nothing — it fades out, the game says TRY AGAIN, and
after two misses the right answer starts flashing yellow so nobody gets
stuck. A round always ends with confetti and a star count, never a "game
over".

Stars are saved per player in `saves/progress.json`, along with each game's
best score. Delete that file to reset everything.

### The scoreboard

The sixth tile on the shelf is each player's own scoreboard: total stars and
crystals, rounds played, and for every game how many rounds and the best
score so far, with a bar showing how close that is to a perfect round.
Clicking a game opens it mode by mode, so it is obvious that times tables
have been played twenty times and division twice.

Nothing here is competitive between players — a child sees only their own
record, and the only direction it moves is up.

### Sound

Every effect is a square, triangle, saw or noise wave built from scratch at
startup in `retro/sfx.py` — there are no audio files to lose. The set is small
on purpose, so each one means exactly one thing:

| Sound | Fires on |
| --- | --- |
| `click` / `select` / `back` | Moving around the menus |
| `correct` | A right answer, rising three notes |
| `wrong` | A wrong answer — soft and low, never a buzzer |
| `pop` | A letter dropping into place in Word Rocket |
| `launch` | The rocket taking off after a correct sum |
| `star` | Three correct in a row, so a streak is audible |
| `charge` | A crystal finishing charging in Crystal Keys |
| `record` | A new best score, once the stars finish landing |
| `fanfare` | The end of a round |

Two things climb rather than repeat: each letter typed in Crystal Keys plays
the next note of a rising pentatonic run, so a word resolves like a little
tune, and the stars on the results screen chime a step higher each, so a big
score sounds bigger than a small one.

Failure is deliberately gentle. The wrong-answer tone is a low triangle wave,
quieter than the success sounds, because a harsh buzzer teaches a child to
fear being wrong. `Ctrl-M` mutes everything.

### Keys

| Key | Does |
| --- | --- |
| `1` `2` `3` | Pick an answer |
| Mouse click | Pick an answer |
| Letter keys | Type, in Crystal Keys and Word Rocket |
| `Esc` | Back one screen |
| `Ctrl-F` / `Cmd-F` | Full screen on/off |
| `Ctrl-M` / `Cmd-M` | Mute/unmute |
| `Ctrl-Q` / `Cmd-Q` | Quit |

**No command is a bare key.** Every shortcut needs Ctrl or Cmd, so a plain
letter always belongs to the game — otherwise typing `f` in the Earth lesson
would toggle full screen instead of typing a letter, which is exactly the bug
that prompted the rule. `Esc` is the one exception, and it means "go back",
never a command.

On macOS, `Cmd-M` is the system shortcut for minimising a window and may be
swallowed before the game sees it. `Ctrl-M` always works.

## Making it your own

The project is meant to be tinkered with, ideally alongside the kids.

**Add a word to Word Rocket.** Draw a 16x16 picture in `retro/sprites.py` as a
grid of characters plus a colour key, register it in the `SPRITES` dict, then
add the word to `WORDS` in `games/word_rocket.py`. Only add words whose
picture is obvious at that size.

**Change the sums.** The range tables at the top of `games/math_blaster.py`
control every number, and `MODES_BY_TIER` decides which modes an age sees.

**Change what counts as which age.** `AGE_BANDS` in `retro/levels.py`.

**Change the patterns.** `UNITS` in `games/pattern_power.py` lists the
repeating shapes (AB, AAB and so on); add `(0, 1, 0, 2)` or similar for a
harder mix.

**Add typing words.** `LESSONS` in `games/crystal_keys.py`. Keep each word
inside its element's key set — the tests will tell you if you slip.

**Change the round length.** `ROUND_LENGTH` in either game.

**Add a whole new game.** Subclass `Scene` from `retro/app.py`, implement
`handle_event`, `update` and `draw`, hand your finished round to
`ResultsScene`, and add it to the `GAMES` list in `launcher.py`. The widgets
in `retro/ui.py` (buttons, panels, starfields, particles) and the sounds in
`retro/sfx.py` are shared by everything.

## Layout

```
launcher.py            Player picker and game shelf
games/math_blaster.py  Number Blaster
games/word_rocket.py   Word Rocket
games/pattern_power.py Pattern Power
games/crystal_keys.py  Crystal Keys, the typing tutor
games/logic_lab.py     Logic Lab, the reasoning puzzles
games/scoreboard.py    Per-player progress screens
retro/levels.py        Age to difficulty tier, in one place
retro/app.py           Window, scaling, scene stack, main loop
retro/ui.py            Buttons, text, panels, starfield, particles
retro/sprites.py       All the pixel art
retro/sfx.py           Synthesised sound effects
retro/results.py       Shared end-of-round screen
retro/progress.py      Star and best-score saving
retro/palette.py       Colours
tests/                 Checks on the question generators and the art
tools/screenshots.py   Regenerates the images in this README
docs/screenshots/      Those images
pyproject.toml         Dependencies and the retro-arcade command
uv.lock                The exact pygame build, pinned
```

## Tests

```sh
uv run python -m unittest discover tests   # or plain: python3 -m unittest discover tests
```

These cover the parts that would quietly teach a child something wrong: the
right answer is always among the choices, sums never exceed the level cap,
subtraction never goes negative, the number of pictures always matches the
answer, number sequences step evenly and never go below zero, every repeating
pattern genuinely repeats, and every sprite grid is well-formed.

They also guard the typing ladder: no lesson may use a key its element hasn't
introduced yet, and Earth stays strictly home row. That check earned its keep
immediately — it caught "river" and "stream" sitting in the Water lesson, both
of which need bottom-row keys the child hasn't met at that point.

The sound tests inspect the generated waveforms directly, since a synthesis
bug that produced silence or clipping would be invisible on screen: every
effect must be audible, must not clip, must match its recipe's duration, and
must actually be played by some game.

`tests/test_reasoning.py` guards the age ladder and the puzzles: an
eight-year-old must be offered times tables and never counting ducks, a
five-year-old must never meet division, division is always exact,
multiplication genuinely gets harder each tier, story problems use the
player's name and no gendered pronouns, matrix answers follow both their row
and their column, analogies repeat the first pair's change, sequences obey
their own rule — and no odd-one-out has a second defensible answer.

`tests/test_scoreboard.py` finishes a round of every mode through each game's
own code and checks the save key it writes is the key the scoreboard reads,
so a renamed mode cannot leave progress recorded but invisible.

`tests/test_packaging.py` covers the quiet failures: that the `retro-arcade`
entry point resolves, that the wheel ships every module the game imports,
that `requirements.txt` hasn't drifted from `pyproject.toml`, and that an
installed copy never writes a child's progress inside site-packages.
