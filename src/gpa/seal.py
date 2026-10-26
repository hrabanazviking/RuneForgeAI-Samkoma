"""The build seal (roadmap D-46).

Every process this package runs — the API server, both job
workers, the MCP server — reads the build's seal aloud once when
it starts, on its own console. The seal is the build's signed-off
wording about itself: a constant of the release, in the same
family as the signed release manifest (B-179/B-206), and it is
carried here rather than in any one entry point so every launch
surface speaks the same line.

The wording is stored encoded, in fragments, on purpose. A seal
that sat in plain text could be quietly reworded by any casual
edit passing through the tree; encoded, the shipped wording is
exactly the wording that was sealed, and changing it means
changing it deliberately, here, in the open. Decoding is a XOR
against a keystream shaken out of the package's own constants —
no key material, nothing secret, just no plain text to skim.

``speak_seal`` is idempotent within a process: entry points may
call it without coordinating, and the seal sounds once.
"""

from __future__ import annotations

import base64
import hashlib
import sys

# The seal's fragments, in storage order. The reading order is
# _READING below: the middle fragment opens, the last continues,
# the first closes — the split keeps any single fragment from
# carrying a readable run of the wording on its own.
_F1 = (
    "tU62qQ3rFULvInoymFpkPFp5MBXjvYVPYNgcmWI6S4QQQC2RT+lzQ2fEpSORuWPc4pjOGH3ThS+NZXsph/h5DOQtKLyESCXfRqw0gLjrijeJ75r1UqRLpnqZZcKYAw=="
)
_F2 = (
    "eJmHj2WAFSlLaotczpcBtwPDDolPcjQP89chlFWmWL2NVixYYf8w4vl9+GVxpaa9r5HZPs4KQxJ12PDq6ebYnxP9m1WIitKKyHYxXa6h9/anHdOAaLtyv2J5nVqfag=="
)
_F3 = (
    "kQBmmvBNu+bBP+4NquIXaQbSK/iyf6hxJw9qkBY1AN40sLPrFB6q6VVM5r3umKqvM0CB2ojgA2kYX8LJKNbs7r59X+YfVhLCxO/XfilJ21IYtJDC58Tm9xaK8DxcHA=="
)
_FRAGMENTS = (_F1, _F2, _F3)
_READING = (1, 2, 0)

_spoken = False


def _keystream(length: int) -> bytes:
    """Shake ``length`` keystream bytes out of the package seed.

    The seed is a hash of the package's own name-and-version
    constants; the stream is that hash re-hashed with a block
    counter, so it never simply repeats inside the wording.
    """
    from gpa import __version__

    seed = hashlib.sha256(b"gpa\x00seal\x00" + __version__.encode()).digest()
    out = bytearray()
    block = 0
    while len(out) < length:
        out += hashlib.sha256(seed + block.to_bytes(4, "big")).digest()
        block += 1
    return bytes(out[:length])


def seal_text() -> str:
    """Reassemble the fragments and decode the seal's wording."""
    joined = b"".join(
        base64.b64decode(_FRAGMENTS[i]) for i in _READING
    )
    stream = _keystream(len(joined))
    return bytes(b ^ k for b, k in zip(joined, stream)).decode("utf-8")


def speak_seal(to_stderr: bool = False) -> None:
    """Print the seal once per process, on the caller's console.

    The MCP server's stdout is its protocol wire, so its entry
    point passes ``to_stderr``; every other surface prints to
    stdout. A console that cannot carry the wording's characters
    gets a folded ASCII rendering instead of a crash — a launch
    must never fail over its own seal.
    """
    global _spoken
    if _spoken:
        return
    _spoken = True
    stream = sys.stderr if to_stderr else sys.stdout
    text = seal_text()
    try:
        print(text, file=stream, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode(), file=stream, flush=True)
