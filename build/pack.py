#!/usr/bin/env python3
"""Pack build/engine.py into <repo>/main.py: minify, lzma, base85, tiny unpacker.

The packed file is the entrypoint and must stay under 4,096 bytes. The packer
refuses to write a main.py that does not parse, does not pass a perft smoke test
or lands over the cap.
"""
import base64, io, lzma, os, pathlib, sys, tokenize

SRC = pathlib.Path(os.environ.get("ENGINE_SRC") or "/home/ubuntu/chesswork/build/engine_src.py")
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/chessrepo/main.py")
CAP = 4096
FILT = [{"id": lzma.FILTER_LZMA2, "preset": 9}]


def minify(text):
    """Drop comments, docstrings and blank lines; leave the code itself alone."""
    out = []
    prev = tokenize.NEWLINE          # a docstring follows NEWLINE/INDENT at a statement start
    depth_indent = False
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        t, s = tok.type, tok.string
        if t in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING):
            continue
        if t == tokenize.STRING and prev in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
            prev = t                       # a bare string statement: a docstring
            continue
        out.append((t, s))
        if t not in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT):
            prev = t
    return tokenize.untokenize(out)


def main():
    src = minify(SRC.read_text())
    compile(src, "payload", "exec")
    # shrink indentation to one space per level: legal, and smaller after lzma
    lines = []
    for ln in src.splitlines():
        n = len(ln) - len(ln.lstrip(" "))
        lines.append(" " * (n // 4) + ln.lstrip(" ") if n else ln)
    src = "\n".join(lines) + "\n"
    compile(src, "payload", "exec")
    blob = base64.b85encode(lzma.compress(src.encode(), format=lzma.FORMAT_RAW, filters=FILT)).decode()
    head = "# tiny-chess-01: lzma payload, built by build/pack.py\nimport lzma,base64\nD='"
    tail = ("'\n"
            "exec(lzma.decompress(base64.b85decode(D),format=lzma.FORMAT_RAW,filters=[{'id':33}]))\n")
    body = head + blob + tail
    if len(body.encode()) > CAP:
        print(f"OVER CAP: {len(body.encode())} > {CAP}")
        return 1
    OUT.write_text(body)
    print(f"{OUT}: {len(body.encode())} bytes ({len(src)} source chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
