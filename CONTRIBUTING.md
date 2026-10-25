# Contributing to fingerprint-db

Thanks for helping keep this dataset accurate. This repo holds **measured** browser
TLS (JA3/JA4) and HTTP/2 (Akamai) fingerprints. The single rule that makes the
dataset worth citing:

> **Never guess, hand-edit, or synthesize a fingerprint. Every value must come from
> an actual handshake you measured, and the PR must say how you measured it.**

A fabricated or "looks about right" entry is worse than no entry. If you are not
sure a value is real, do not submit it.

## What you can contribute

- A **new browser/profile** (e.g. a new stable Chrome/Firefox/Safari major, Brave,
  a mobile browser, a specific uTLS `*_Auto` template).
- A **re-measurement** of an existing entry after a browser or uTLS update
  (update the value **and** bump `measured`).
- Fixes to loaders, schema, docs, or CI.

## How to capture a real fingerprint

You need two things: a client that emits the handshake, and a reflector that reads
it back and reports JA3/JA4/Akamai.

### Reflector

Use **[tls.peet.ws](https://tls.peet.ws)** — the JSON endpoint is
`https://tls.peet.ws/api/all`. It returns `tls.ja3`, `tls.ja3_hash`, `tls.ja4`,
`tls.peetprint_hash`, and `http2.akamai_fingerprint` / `http2.akamai_fingerprint_hash`
for the connecting client. (Any equivalent reflector is fine — e.g. a self-hosted
[ja3er](https://github.com/salesforce/ja3)-style endpoint — as long as you record
which one in the PR.)

### Client — two accepted methods

**Method A — uTLS template (how the existing entries were made).** This is what the
dataset is keyed on (`utls_client_hello_id`), so it is the preferred method.

```go
// go run . ; prints the api/all JSON for the chosen template
package main

import (
	"fmt"
	"io"
	"net/http"

	tls "github.com/refraction-networking/utls"
)

func main() {
	spec := tls.HelloChrome_Auto // swap for the profile you are measuring
	dialConn, _ := tls.Dial("tcp", "tls.peet.ws:443",
		&tls.Config{ServerName: "tls.peet.ws"})
	_ = spec
	// Use utls.UClient with the ClientHelloID to control the handshake; then
	// send: GET /api/all HTTP/1.1 over the uTLS conn (or use an http.Transport
	// wired to a utls dialer) and read the JSON body.
	req, _ := http.NewRequest("GET", "https://tls.peet.ws/api/all", nil)
	_ = req
	_ = dialConn
	fmt.Println("see utls examples: github.com/refraction-networking/utls")
}
```

Record the exact `tls.HelloXxx_Auto` ID you used — that becomes
`utls_client_hello_id`.

**Method B — a real browser.** Open `https://tls.peet.ws/api/all` in the actual
browser (or drive it with Playwright/Selenium) and copy the JSON. Note the exact
browser build and OS. Use this when there is no uTLS template; set
`utls_client_hello_id` to the closest template or `""` and say so in the PR.

> Headless-automation defaults (plain `curl`, Python `requests`, bare headless
> Chromium) have their **own** fingerprints that do not match a real stable browser.
> Do not submit those as browser entries.

## The fields to fill

Add your entry under `browsers` in [`fingerprints.json`](fingerprints.json):

```json
"brave": {
  "utls_client_hello_id": "HelloChrome_Auto",
  "user_agent": "Mozilla/5.0 ... Brave/1.70 ...",
  "source": "tls.peet.ws",
  "measured": "2026-10-25",
  "tls": {
    "ja3": "771,4865-...",
    "ja3_hash": "<32 hex>",
    "ja4": "t13d1516h2_8daaf6152771_d8a2da3f94cd",
    "peetprint_hash": "<32 hex>"
  },
  "http2": {
    "akamai_fingerprint": "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p",
    "akamai_hash": "<32 hex>"
  }
}
```

| Field | Required | From the reflector |
|---|---|---|
| `utls_client_hello_id` | yes | the uTLS template you emitted (or closest + note) |
| `user_agent` | yes | the client's real UA string |
| `source` | recommended | the reflector host, e.g. `tls.peet.ws` |
| `measured` | recommended | ISO date you measured (`YYYY-MM-DD`) |
| `tls.ja3` | yes | `tls.ja3` |
| `tls.ja3_hash` | recommended | `tls.ja3_hash` |
| `tls.ja4` | yes | `tls.ja4` |
| `tls.peetprint_hash` | optional | `tls.peetprint_hash` |
| `http2.akamai_fingerprint` | yes | `http2.akamai_fingerprint` |
| `http2.akamai_hash` | recommended | `http2.akamai_fingerprint_hash` |

## Validate before you open the PR

```bash
pip install jsonschema
python3 validate.py          # schema + completeness + JA4/hash sanity checks
go test ./...                # loader + "every known browser is complete"
python3 -c "import fingerprint_db; print(fingerprint_db.names())"
```

CI runs the same `validate.py` on every push and PR, so a malformed entry fails the
check automatically.

## PR checklist

The [pull request template](.github/PULL_REQUEST_TEMPLATE.md) asks you to confirm:

- [ ] Values are **measured**, not guessed or edited by hand.
- [ ] The PR states the **client** (uTLS template / real browser build) and the
      **reflector** used, so the measurement is reproducible.
- [ ] `source` and `measured` are set on new/updated entries.
- [ ] `python3 validate.py` and `go test ./...` pass locally.

By contributing you agree your contribution is licensed under the repo's
[MIT License](LICENSE).
