#!/usr/bin/env node
// measure.mjs — automated, TRUTHFUL fingerprint measurement for fingerprint-db.
//
// Launches the REAL browser engines that Playwright bundles — Chromium, Firefox,
// WebKit — and makes each one perform a genuine TLS + HTTP/2 handshake against our
// live reflector (https://fp.shshbshsnang.shop/api/all). The reflector reads the
// handshake back and reports ja3 / ja3_hash / ja4 / ja4h / akamai_h2. We also
// measure `curl --http2` as a baseline non-browser client.
//
// HONESTY (read this):
//   * Playwright's bundled Chromium is NOT Google Chrome stable. It is the
//     open-source Chromium build Playwright ships. We label it exactly as
//     "Chromium <version>" (the ENGINE, from browser.version()), never "Chrome".
//   * Same for Firefox and WebKit: these are Playwright's bundled engine builds,
//     not necessarily the exact shipping Firefox / Safari. They are CURRENT,
//     REAL-ENGINE measurements — fresh and honest, which is the whole point.
//   * Every value here comes from a real handshake read back off the wire. We
//     never invent a fingerprint. ja3_hash comes straight from the reflector.
//     akamai_hash is md5(akamai_fingerprint) — the reflector's own definition of
//     that hash, computed from the measured string, not guessed.
//   * If the reflector is unreachable, this script EXITS NON-ZERO and writes
//     nothing, so the pipeline fails loudly instead of emitting stale/fake data.
//
// Output: writes a JSON object of fresh entries to the path given as argv[2]
// (default: ./live.json) and prints it to stdout.

import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { promisify } from 'node:util';
import { chromium, firefox, webkit } from 'playwright-core';

const execFileP = promisify(execFile);

const REFLECTOR = process.env.FP_REFLECTOR || 'https://fp.shshbshsnang.shop/api/all';
const REFLECTOR_HOST = new URL(REFLECTOR).host;
const OUT = process.argv[2] || new URL('./live.json', import.meta.url).pathname;
const TODAY = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
const NOW = new Date().toISOString();

const md5 = (s) => createHash('md5').update(s, 'utf8').digest('hex');

// Pull the fields we keep out of a raw reflector response. Throws if the
// response is missing the core fields (so a broken reflector fails the run).
function shape(raw, { engine, version, method }) {
  const ja3 = raw.ja3;
  const ja4 = raw.ja4;
  const akamai = raw.akamai_h2;
  const ua = raw.user_agent;
  if (!ja3 || !ja4 || !akamai) {
    throw new Error(
      `reflector returned incomplete fingerprint (ja3/ja4/akamai_h2 missing): ${JSON.stringify(raw).slice(0, 300)}`
    );
  }
  return {
    engine,
    version,
    user_agent: ua || '',
    tls: {
      ja3,
      // ja3_hash straight from the reflector; fall back to md5(ja3) (same defn).
      ja3_hash: raw.ja3_hash || md5(ja3),
      ja4,
    },
    http2: {
      // The reflector's akamai_h2 string is the Akamai HTTP/2 fingerprint.
      akamai_fingerprint: akamai,
      // akamai_hash = md5 of the fingerprint string (reflector's definition),
      // computed from the measured value — deterministic, not fabricated.
      akamai_hash: md5(akamai),
    },
    ja4h: raw.ja4h || '',
    provenance: {
      source: REFLECTOR_HOST,
      method,
      measured: TODAY,
      measured_at: NOW,
    },
  };
}

// Measure one Playwright engine by doing a real fetch from inside the browser
// (uses the browser's own TLS + HTTP/2 stack — that is the fingerprint we want).
// Accurate engine display names (don't mislabel: WebKit, not "Webkit").
const DISPLAY = { chromium: 'Chromium', firefox: 'Firefox', webkit: 'WebKit' };

async function measureBrowser(name, launcher) {
  let browser;
  try {
    browser = await launcher.launch({ headless: true });
    const version = browser.version();
    const engineLabel = `${DISPLAY[name] || name} ${version}`;
    const context = await browser.newContext();
    const page = await context.newPage();

    // Navigate directly to the reflector: the navigation itself is the real
    // TLS + HTTP/2 handshake we want measured. Then read the JSON body back.
    const resp = await page.goto(REFLECTOR, { waitUntil: 'load', timeout: 30000 });
    if (!resp || !resp.ok()) {
      throw new Error(`navigation to reflector failed: HTTP ${resp ? resp.status() : 'no response'}`);
    }
    const bodyText = await page.evaluate(() => document.body.innerText);
    let raw;
    try {
      raw = JSON.parse(bodyText);
    } catch (e) {
      throw new Error(`reflector body is not JSON: ${bodyText.slice(0, 200)}`);
    }

    const entry = shape(raw, {
      engine: engineLabel,
      version,
      method: `playwright ${name} ${version}`,
    });
    console.error(`  [ok] ${name}: ${engineLabel} -> ja4=${entry.tls.ja4}`);
    return entry;
  } finally {
    if (browser) await browser.close();
  }
}

// Baseline non-browser client: real curl with HTTP/2.
async function measureCurl() {
  const { stdout } = await execFileP(
    'curl',
    ['-s', '--http2', '--max-time', '30', REFLECTOR],
    { maxBuffer: 10 * 1024 * 1024 }
  );
  const raw = JSON.parse(stdout);
  // curl version string, e.g. "curl 7.81.0"
  let version = 'unknown';
  try {
    const v = await execFileP('curl', ['--version'], { maxBuffer: 1024 * 1024 });
    const m = v.stdout.match(/^curl\s+([\d.]+)/);
    if (m) version = m[1];
  } catch {}
  const entry = shape(raw, {
    engine: `curl ${version}`,
    version,
    method: `curl --http2 ${version}`,
  });
  console.error(`  [ok] curl: curl ${version} -> ja4=${entry.tls.ja4}`);
  return entry;
}

async function main() {
  console.error(`fingerprint-db measure: reflector=${REFLECTOR} date=${TODAY}`);

  const live = {};
  const targets = [
    ['chromium', chromium],
    ['firefox', firefox],
    ['webkit', webkit],
  ];

  for (const [name, launcher] of targets) {
    live[name] = await measureBrowser(name, launcher);
  }
  live['curl'] = await measureCurl();

  // Sanity: must have at least the three browser engines, or fail loudly.
  for (const req of ['chromium', 'firefox', 'webkit']) {
    if (!live[req] || !live[req].tls.ja4) {
      throw new Error(`missing measurement for ${req} — refusing to write partial data`);
    }
  }

  const out = {
    measured: TODAY,
    measured_at: NOW,
    reflector: REFLECTOR_HOST,
    note:
      'Real-engine fingerprints measured via Playwright-bundled browsers. ' +
      'Chromium != Google Chrome stable; Firefox/WebKit are Playwright engine builds. ' +
      'Current + honest, not shipping-browser equivalents.',
    engines: live,
  };

  writeFileSync(OUT, JSON.stringify(out, null, 2) + '\n');
  console.error(`wrote ${OUT}`);
  process.stdout.write(JSON.stringify(out, null, 2) + '\n');
}

main().catch((err) => {
  console.error('MEASURE FAILED:', err && err.stack ? err.stack : err);
  console.error('Refusing to write stale/fake data. Exiting non-zero.');
  process.exit(1);
});
