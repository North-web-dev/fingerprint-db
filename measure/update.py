#!/usr/bin/env python3
"""Fold fresh measurements (measure/live.json) into fingerprints.json.

Reads the JSON produced by measure.mjs and writes/refreshes a top-level `live`
section in fingerprints.json, keyed by engine. The hand-curated `browsers`
section is NEVER touched — the two live side by side.

Rules (see the provenance policy):
  * Only measured values are written. Nothing is guessed.
  * If live.json is missing, empty, or missing any of the three browser engines
    (chromium/firefox/webkit) with a well-formed JA4, this FAILS LOUDLY and
    writes nothing — the pipeline must never commit stale/partial/fake data.
  * A previously-measured value is only ever replaced by a newer measured value,
    never by a guess.

Usage:
    python3 measure/update.py [measure/live.json] [fingerprints.json]
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

JA4_RE = re.compile(r"^t\d{2}[di]\d{3,4}h[0-9a-z]+_[0-9a-f]{12}_[0-9a-f]{12}$")
HEX32_RE = re.compile(r"^[0-9a-f]{32}$")
REQUIRED_ENGINES = ("chromium", "firefox", "webkit")


def die(msg: str) -> None:
    print(f"update.py: FATAL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    live_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "live.json")
    data_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "fingerprints.json")

    if not os.path.exists(live_path):
        die(f"{live_path} not found — measure.mjs must run (and succeed) first")

    try:
        live = json.load(open(live_path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        die(f"could not read {live_path}: {e}")

    engines = live.get("engines") or {}
    measured = live.get("measured")
    if not measured:
        die("live.json has no 'measured' date")
    if not engines:
        die("live.json has no engines — refusing to write empty/stale data")

    # Hard gate: all three real browser engines must be present and well-formed.
    for name in REQUIRED_ENGINES:
        e = engines.get(name)
        if not e:
            die(f"missing required engine '{name}' in live.json")
        ja4 = e.get("tls", {}).get("ja4", "")
        if not JA4_RE.match(ja4):
            die(f"engine '{name}' has malformed/empty JA4 {ja4!r} — refusing to write")

    # Format-sanity every engine's hashes (reject anything that isn't a real hash).
    for name, e in engines.items():
        for hv in (e.get("tls", {}).get("ja3_hash"), e.get("http2", {}).get("akamai_hash")):
            if hv and not HEX32_RE.match(hv):
                die(f"engine '{name}' has non-hex hash {hv!r}")
        if not e.get("tls", {}).get("ja3"):
            die(f"engine '{name}' has empty tls.ja3")
        if not e.get("http2", {}).get("akamai_fingerprint"):
            die(f"engine '{name}' has empty http2.akamai_fingerprint")
        prov = e.get("provenance") or {}
        if not (prov.get("source") and prov.get("method") and prov.get("measured")):
            die(f"engine '{name}' is missing provenance (source/method/measured)")

    try:
        data = json.load(open(data_path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        die(f"could not read {data_path}: {e}")

    # Write the live section. This is the only thing we add/replace.
    data["live"] = {
        "updated": measured,
        "reflector": live.get("reflector", ""),
        "note": live.get("note", ""),
        "engines": engines,
    }
    # metadata values are strings (the Go loader types metadata as map[string]string).
    data.setdefault("metadata", {})["live_updated"] = measured

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(
        f"update.py: wrote live section ({len(engines)} engines, measured {measured}) "
        f"into {os.path.relpath(data_path, os.getcwd())}"
    )
    for name in sorted(engines):
        e = engines[name]
        print(f"  {name}: {e.get('engine')} ja4={e['tls']['ja4']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
