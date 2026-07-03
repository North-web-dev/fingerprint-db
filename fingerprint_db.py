"""Load current browser TLS (JA3/JA4) + HTTP/2 (Akamai) fingerprints."""
from __future__ import annotations
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fingerprints.json")


def load() -> dict:
    with open(_PATH, encoding="utf-8") as f:
        return json.load(f)


def get(name: str) -> dict:
    db = load()
    b = db["browsers"].get(name)
    if b is None:
        raise KeyError(f"unknown browser: {name!r} (have: {', '.join(db['browsers'])})")
    return b


def names() -> list:
    return list(load()["browsers"])


if __name__ == "__main__":
    import sys
    print(json.dumps(get(sys.argv[1]) if len(sys.argv) > 1 else load(), indent=2))
