#!/usr/bin/env python3
"""Validate fingerprints.json against schema.json plus a few completeness checks.

Run locally or in CI:

    python3 validate.py

Exits non-zero (and prints what is wrong) if the dataset is invalid, so it is
safe to use as a required PR check. Pure stdlib + jsonschema.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "fingerprints.json")
SCHEMA = os.path.join(HERE, "schema.json")

# JA4 looks like: t13d1516h2_8daaf6152771_d8a2da3f94cd
JA4_RE = re.compile(r"^t\d{2}[di]\d{3,4}h[0-9a-z]+_[0-9a-f]{12}_[0-9a-f]{12}$")
# 32-hex MD5-style hash used for ja3_hash / akamai_hash / peetprint_hash
HEX32_RE = re.compile(r"^[0-9a-f]{32}$")


def fail(msg: str) -> None:
    print(f"  FAIL: {msg}")


def main() -> int:
    try:
        import jsonschema
    except ImportError:
        print("jsonschema not installed: pip install jsonschema", file=sys.stderr)
        return 2

    data = json.load(open(DATA, encoding="utf-8"))
    schema = json.load(open(SCHEMA, encoding="utf-8"))

    errors = 0

    # 1. JSON Schema
    try:
        jsonschema.validate(data, schema)
        print("schema: OK")
    except jsonschema.ValidationError as e:
        fail(f"schema: {e.message} (at {'/'.join(map(str, e.path))})")
        errors += 1

    browsers = data.get("browsers", {})
    if not browsers:
        fail("no browsers in dataset")
        errors += 1

    # 2. Per-entry completeness / sanity (what the Go test also asserts)
    for name, b in browsers.items():
        for field in ("utls_client_hello_id", "user_agent"):
            if not b.get(field):
                fail(f"{name}: empty {field}")
                errors += 1
        tls = b.get("tls", {})
        if not tls.get("ja3"):
            fail(f"{name}: empty tls.ja3")
            errors += 1
        ja4 = tls.get("ja4", "")
        if not ja4:
            fail(f"{name}: empty tls.ja4")
            errors += 1
        elif not JA4_RE.match(ja4):
            fail(f"{name}: tls.ja4 '{ja4}' does not look like a JA4 fingerprint")
            errors += 1
        for hname in ("ja3_hash", "peetprint_hash"):
            hv = tls.get(hname)
            if hv and not HEX32_RE.match(hv):
                fail(f"{name}: tls.{hname} '{hv}' is not a 32-char hex hash")
                errors += 1
        http2 = b.get("http2", {})
        if not http2.get("akamai_fingerprint"):
            fail(f"{name}: empty http2.akamai_fingerprint")
            errors += 1
        ah = http2.get("akamai_hash")
        if ah and not HEX32_RE.match(ah):
            fail(f"{name}: http2.akamai_hash '{ah}' is not a 32-char hex hash")
            errors += 1

    if errors:
        print(f"\nINVALID: {errors} problem(s) found.")
        return 1

    print(f"valid: {len(browsers)} browser(s) -> {', '.join(sorted(browsers))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
