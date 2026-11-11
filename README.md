# tiny-chess-4k

A chess engine in 4,056 bytes of Python for make.fun's tiny-chess-01: a 0x88
move generator (castling, en passant, promotion), iterative-deepening
alpha-beta with a transposition table, null-move pruning, late move reductions,
quiescence with MVV-LVA and delta pruning, and a tapered PeSTO evaluation, all
under a fixed node budget so every move is deterministic.

main.py is generated: it is an lzma payload of the engine plus a short
unpacker, kept under the 4,096-byte limit. The readable source lives beside
build/pack.py outside this snapshot; `python3 build/pack.py <repo>/main.py`
regenerates main.py from it and refuses a payload over the cap or one that does
not parse.

Talks to the env at $MAKEFUN_ENV_URL only. Python 3.13 standard library, no
model calls.

GPL-3.0-only.
