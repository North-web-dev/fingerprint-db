<!-- Thanks for contributing! See CONTRIBUTING.md for how to capture a real fingerprint. -->

## What does this PR do?

<!-- e.g. "Add Brave 1.70 (Chromium) profile" / "Re-measure firefox after v134" / "docs" -->

## If this adds or changes a fingerprint

**Provenance (required — this is what makes the entry citable):**

- **Browser / profile:** <!-- exact build + OS, e.g. Chrome 131.0.6778.86, Windows 11 -->
- **Client used to emit the handshake:** <!-- uTLS template (e.g. HelloChrome_Auto) OR real browser + automation -->
- **Reflector read back from:** <!-- e.g. https://tls.peet.ws/api/all -->
- **Date measured:** <!-- YYYY-MM-DD, matches the `measured` field -->

Confirm:

- [ ] Every value is **measured from a real handshake**, not guessed, hand-edited, or synthesized.
- [ ] `source` and `measured` are set on the new/changed entry.
- [ ] This is NOT the fingerprint of plain curl / requests / bare headless automation.

## Checks

- [ ] `python3 validate.py` passes
- [ ] `go test ./...` passes
- [ ] `python3 -c "import fingerprint_db; fingerprint_db.load()"` works
