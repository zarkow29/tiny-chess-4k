# tiny-chess-01 starter (MIT, see LICENSE): a working entry to start from.
# It plays every game of the gauntlet through the env at MAKEFUN_ENV_URL:
# POST /game {} serves the game in play, POST /move {game, move} plays a
# move, and the loop ends when the env answers status "done".
#
# Its chess is one line deep: of the legal moves the env lists, it plays the
# one that captures the most valuable piece, read from the FEN. Ties go, in
# order, to the better promotion, the cheaper moving piece, then the first
# move in UCI order. No clock and no random: the same position always gets
# the same move, so the trial's replay matches.
#
# Make it stronger with a real search under a fixed node or depth budget,
# never a clock. The rule: this file is the whole engine, at most 4,096
# bytes as committed, Python 3.13 standard library only.

import json
import os
import sys
import urllib.error
import urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

# Piece values by FEN letter, case-insensitive. The king is never captured;
# its 100 only ranks it last as the moving piece.
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100}


def post(path, body):
    """POST a JSON body to the env and return its JSON answer."""
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")


def board_of(fen):
    """The FEN's pieces as {square: letter}, e.g. {"e1": "K", "e8": "k"}."""
    board = {}
    for i, row in enumerate(fen.split()[0].split("/")):
        file = 0
        for c in row:
            if c.isdigit():
                file += int(c)
            else:
                board["abcdefgh"[file] + str(8 - i)] = c
                file += 1
    return board


def choose(fen, legal):
    """The legal UCI move that takes the most, with the fixed tie-break."""
    board = board_of(fen)

    def rank(move):
        mover = board[move[:2]].lower()
        victim = board.get(move[2:4])
        if victim is None and mover == "p" and move[0] != move[2]:
            victim = "p"  # en passant: the pawn taken is beside the target
        taken = VALUE[victim.lower()] if victim else 0
        promo = VALUE[move[4]] if len(move) == 5 else 0
        return (-taken, -promo, VALUE[mover], move)

    return min(legal, key=rank)


while True:
    g = post("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        g = post("/move", {"game": g["game"], "move": choose(g["fen"], g["legal_moves"])})
    print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)
print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)
