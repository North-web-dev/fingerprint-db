# fingerprint-db

A small, **measured** database of current browser **TLS (JA3/JA4)** and
**HTTP/2 (Akamai)** fingerprints — as JSON, with Go and Python loaders.

Values are not guessed: each entry is measured by emitting the browser's
handshake (via [uTLS](https://github.com/refraction-networking/utls) `*_Auto`
templates) and reading it back from [tls.peet.ws](https://tls.peet.ws). Useful
for anti-bot research, building browser-impersonating clients, and validating
that a fingerprint matches a real browser.

## What's inside — [`fingerprints.json`](fingerprints.json)

Per browser (`chrome`, `firefox`, `safari`, `edge`, `ios`):

```json
"chrome": {
  "utls_client_hello_id": "HelloChrome_Auto",
  "user_agent": "Mozilla/5.0 … Chrome/131.0.0.0 …",
  "tls":   { "ja3": "771,4865-…", "ja3_hash": "…", "ja4": "t13d1516h2_8daaf6152771_d8a2da3f94cd", "peetprint_hash": "…" },
  "http2": { "akamai_fingerprint": "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p", "akamai_hash": "…" }
}
```

## Use it

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

## Schema

[`schema.json`](schema.json) (JSON Schema draft-07) — CI validates
`fingerprints.json` against it on every push.

## License

MIT — see [LICENSE](LICENSE).
