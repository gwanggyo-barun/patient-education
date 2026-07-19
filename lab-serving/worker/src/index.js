// lab-gate — Cloudflare Worker capability-URL gate for patient lab pages.
//
// The only public entrance to the private R2 bucket `clinic-lab`.
// A 256-bit capability token lives in the path: GET /r/<token>/<file?>
//   token = Python secrets.token_urlsafe(32) → 43 chars, [A-Za-z0-9_-]
//
// Flow:  token-format check → manifest lookup (revoked?) → expiry → R2 get →
//        hardened response headers.
//
// Security posture:
//   - Existence oracle avoidance: EVERY failure (bad token, unknown token,
//     revoked, missing object, traversal, wrong method) returns the SAME 404.
//   - Only expiry returns a distinct 410 (intentional: gives the patient an
//     actionable "ask the desk to re-issue" message; expiry is not secret).
//   - Path-traversal guard on the file segment.
//   - noindex / no-referrer / no-store / CSP hardening headers.
//   - /robots.txt → Disallow all (defence in depth; pages are noindex anyway).
//
// Deploy:  wrangler deploy  (bucket binding LAB → clinic-lab, see wrangler.toml)

// 256-bit token = token_urlsafe(32) = exactly 43 url-safe base64 chars.
const TOKEN_RE = /^\/r\/([A-Za-z0-9_-]{43})\/(.*)$/;

// Extension → Content-Type. Anything unlisted falls back to octet-stream
// (served as a download, never executed as an active type).
const CT = {
  html: "text/html; charset=utf-8",
  htm: "text/html; charset=utf-8",
  pdf: "application/pdf",
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  gif: "image/gif",
  webp: "image/webp",
  svg: "image/svg+xml",
  css: "text/css; charset=utf-8",
  js: "text/javascript; charset=utf-8",
  json: "application/json; charset=utf-8",
  ico: "image/x-icon",
  woff: "font/woff",
  woff2: "font/woff2",
  ttf: "font/ttf",
  txt: "text/plain; charset=utf-8",
};

// Content-Security-Policy: allow only self + data: URIs, plus the Pretendard
// font CDN (jsdelivr) that the clinic pages load for the Korean typeface.
// No scripts are permitted at all (no script-src → falls back to default-src
// 'self'; the lab pages are static). style-src allows inline because the
// self-contained build inlines the stylesheets.
const CSP = [
  "default-src 'self' data:",
  "img-src 'self' data:",
  "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
  "font-src 'self' data: https://cdn.jsdelivr.net",
  "script-src 'none'",
  "object-src 'none'",
  "base-uri 'none'",
  "frame-ancestors 'none'",
].join("; ");

// The one and only failure response. Kept byte-identical for every failure
// path so an attacker cannot distinguish "unknown token" from "revoked" from
// "missing file".
function deny() {
  return new Response("Not found", {
    status: 404,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "x-robots-tag": "noindex, nofollow, noarchive",
      "referrer-policy": "no-referrer",
      "cache-control": "no-store",
    },
  });
}

function expired() {
  return new Response(
    "이 안내는 만료되었습니다. 다음 내원 시 진료실에서 재발급을 요청해 주세요.",
    {
      status: 410,
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "x-robots-tag": "noindex, nofollow, noarchive",
        "referrer-policy": "no-referrer",
        "cache-control": "no-store",
      },
    }
  );
}

// _manifest.json shape:  { "<token>": { item, expires, revoked }, ... }
// Cached in Worker memory for 60s to avoid an R2 GET on every request.
let _man = null;
let _manAt = 0;
async function manifest(env) {
  const now = Date.now();
  if (_man && now - _manAt < 60000) return _man;
  const o = await env.LAB.get("_manifest.json");
  _man = o ? await o.json() : {};
  _manAt = now;
  return _man;
}

// Reject anything that could escape the token prefix or is otherwise unsafe as
// an R2 key segment. Returns true if the file path is safe.
function safeFile(file) {
  if (file.length > 256) return false;
  if (file.startsWith("/")) return false; // no absolute
  if (file.includes("\\")) return false; // no backslash
  if (/[\x00-\x1f]/.test(file)) return false; // no control chars
  // Split on "/" and reject empty / dot / dotdot segments (traversal).
  for (const seg of file.split("/")) {
    if (seg === "" || seg === "." || seg === "..") return false;
  }
  return true;
}

export default {
  async fetch(req, env) {
    // Only GET/HEAD reach content; everything else looks like "not found".
    if (req.method !== "GET" && req.method !== "HEAD") return deny();

    const url = new URL(req.url);

    // Defence in depth: crawlers get an explicit disallow-all.
    if (url.pathname === "/robots.txt") {
      return new Response("User-agent: *\nDisallow: /\n", {
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "x-robots-tag": "noindex, nofollow, noarchive",
          "cache-control": "no-store",
        },
      });
    }

    const m = url.pathname.match(TOKEN_RE);
    if (!m) return deny();

    const token = m[1];
    const file = m[2] || "index.html";
    if (!safeFile(file)) return deny();

    const meta = (await manifest(env))[token];
    if (!meta || meta.revoked) return deny();

    if (meta.expires && Date.now() > Date.parse(meta.expires)) return expired();

    const obj = await env.LAB.get(`r/${token}/${file}`);
    if (!obj) return deny();

    const ext = file.split(".").pop().toLowerCase();
    const headers = {
      "content-type": CT[ext] || "application/octet-stream",
      "x-robots-tag": "noindex, nofollow, noarchive",
      "referrer-policy": "no-referrer",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "content-security-policy": CSP,
    };
    // HEAD: return headers only, no body.
    return new Response(req.method === "HEAD" ? null : obj.body, { headers });
  },
};
