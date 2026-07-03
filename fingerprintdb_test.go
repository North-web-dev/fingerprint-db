package fingerprintdb

import "testing"

func TestLoad(t *testing.T) {
	db, err := Load()
	_ = db
	if err != nil {
		t.Fatal(err)
	}
	for _, n := range []string{"chrome", "firefox", "safari", "edge", "ios"} {
		b, err := Get(n)
		if err != nil || b.TLS.JA4 == "" || b.HTTP2.AkamaiFingerprint == "" || b.UTLSClientHelloID == "" {
			t.Fatalf("browser %q incomplete: %+v (err=%v)", n, b, err)
		}
	}
}

func TestUnknown(t *testing.T) {
	if _, err := Get("nope"); err == nil {
		t.Fatal("expected error for unknown browser")
	}
}
