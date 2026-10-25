# fingerprint-db

![entries](https://img.shields.io/badge/entries-5-blue) ![license](https://img.shields.io/badge/license-MIT-green)

A small, **measured** database of current browser **TLS (JA3/JA4)** and
**HTTP/2 (Akamai)** fingerprints — as JSON, with Go and Python loaders.

Values are not guessed: each entry is measured by emitting the browser's
handshake (via [uTLS](https://github.com/refraction-networking/utls) `*_Auto`
templates) and reading it back from [tls.peet.ws](https://tls.peet.ws). Useful
for anti-bot research, building browser-impersonating clients, and validating
that a fingerprint matches a real browser.

**Current coverage: 5 profiles** — `chrome`, `edge`, `firefox`, `safari`, `ios`.
See [`fingerprints.json`](fingerprints.json) for the exact measured values and
`metadata.updated` for when they were last re-measured.

## Schema

Each entry is one browser profile. Structure (full JSON Schema:
[`schema.json`](schema.json), draft-07):

| Field | Meaning |
|---|---|
| `utls_client_hello_id` | uTLS template that reproduces this handshake (the reproduction key) |
| `user_agent` | the browser's real User-Agent string |
| `tls.ja3` / `tls.ja3_hash` | JA3 string and its MD5 hash |
| `tls.ja4` | JA4 fingerprint (`t13d1516h2_…`) |
| `tls.peetprint_hash` | peet.ws's own TLS hash |
| `http2.akamai_fingerprint` / `http2.akamai_hash` | Akamai HTTP/2 fingerprint and hash |
| `source`, `measured` | *(recommended on new entries)* reflector + ISO measurement date |

```json
"chrome": {
  "utls_client_hello_id": "HelloChrome_Auto",
  "user_agent": "Mozilla/5.0 … Chrome/131.0.0.0 …",
  "tls":   { "ja3": "771,4865-…", "ja3_hash": "…", "ja4": "t13d1516h2_8daaf6152771_d8a2da3f94cd", "peetprint_hash": "…" },
  "http2": { "akamai_fingerprint": "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p", "akamai_hash": "…" }
}
```

## Load it

**Go:**
```go
import fp "github.com/North-web-dev/fingerprint-db"

b, _ := fp.Get("chrome")
fmt.Println(b.TLS.JA4, b.HTTP2.AkamaiFingerprint, b.UTLSClientHelloID)
```

**Python:**
```python
import fingerprint_db
b = fingerprint_db.get("chrome")
print(b["tls"]["ja4"], b["http2"]["akamai_fingerprint"])
print(fingerprint_db.names())   # ['chrome', 'edge', 'firefox', 'ios', 'safari']
```

**Anything else:** it's just `fingerprints.json` — read it directly.

## Notes

- JA3/JA4 vary slightly with the measuring tool and GREASE handling; values here
  are measured via uTLS `*_Auto` templates against tls.peet.ws.
- `utls_client_hello_id` is the reproduction key — pass it to uTLS to emit the
  same handshake (that's how [impersonate-http](https://github.com/North-web-dev/impersonate-http)
  consumes this DB).
- Profiles track the current stable browser as uTLS updates; re-measured on
  refresh (see `metadata.updated`).

## Provenance policy

This dataset is only useful if every value is real. **Nothing in it is guessed,
hand-edited, or synthesized** — each entry is a fingerprint read back from a
reflector after a real handshake. New entries should carry `source` (the
reflector) and `measured` (ISO date) so the measurement is traceable. If a value
can't be measured, it doesn't go in.

## Contributing

PRs adding new profiles or re-measuring existing ones are welcome — this is how
the dataset stays current. [`CONTRIBUTING.md`](CONTRIBUTING.md) explains exactly
how to capture a real fingerprint (which tool, which reflector, which fields), and
every push/PR runs `validate.py` in CI against [`schema.json`](schema.json) plus
completeness and JA4/hash format checks:

```bash
pip install jsonschema
python3 validate.py
go test ./...
```

## Support

⭐ Star the repo if it helped. If this dataset saves you time, you can support development:

| Coin | Address |
|---|---|
| **BTC** | `bc1q0sfghv7yfl594gjurhyhlhdgm0dtwh4dkjha36` |
| **ETH / USDT-ERC20 / BNB-BEP20** | `0xB827b5a8B6c5111946c5D872933b2C23484E87dE` |
| **SOL** | `3ch5aHrPp3CierhiNXmqmtFH2dMHh6Gfv7a97KtLMMCh` |
| **USDT-TRC20 / TRX** | `TUAyz7TjgJdFVD2oFHWUUTNrzzAnBRgySG` |
| **TON** | `UQAJmYVuR3hh02etjaPKJF-h6jcpdSnq9ZIFvI64NEskS6tx` |

## License

MIT — see [LICENSE](LICENSE).
