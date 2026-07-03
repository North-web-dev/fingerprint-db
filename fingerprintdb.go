// Package fingerprintdb serves current browser TLS (JA3/JA4) and HTTP/2 (Akamai)
// fingerprints from an embedded, measured JSON database.
package fingerprintdb

import (
	_ "embed"
	"encoding/json"
	"fmt"
)

//go:embed fingerprints.json
var raw []byte

type TLS struct {
	JA3           string `json:"ja3"`
	JA3Hash       string `json:"ja3_hash"`
	JA4           string `json:"ja4"`
	PeetprintHash string `json:"peetprint_hash"`
}

type HTTP2 struct {
	AkamaiFingerprint string `json:"akamai_fingerprint"`
	AkamaiHash        string `json:"akamai_hash"`
}

type Browser struct {
	UTLSClientHelloID string `json:"utls_client_hello_id"`
	UserAgent         string `json:"user_agent"`
	TLS               TLS    `json:"tls"`
	HTTP2             HTTP2  `json:"http2"`
}

type DB struct {
	Metadata map[string]string  `json:"metadata"`
	Browsers map[string]Browser `json:"browsers"`
}

// Load parses the embedded database.
func Load() (*DB, error) {
	var db DB
	if err := json.Unmarshal(raw, &db); err != nil {
		return nil, err
	}
	return &db, nil
}

// Get returns the fingerprint for a browser name (chrome/firefox/safari/edge/ios).
func Get(name string) (Browser, error) {
	db, err := Load()
	if err != nil {
		return Browser{}, err
	}
	b, ok := db.Browsers[name]
	if !ok {
		return Browser{}, fmt.Errorf("fingerprintdb: unknown browser %q", name)
	}
	return b, nil
}

// Names returns the available browser names.
func Names() []string {
	db, err := Load()
	if err != nil {
		return nil
	}
	out := make([]string, 0, len(db.Browsers))
	for k := range db.Browsers {
		out = append(out, k)
	}
	return out
}
