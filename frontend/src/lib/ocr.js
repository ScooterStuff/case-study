// Photo -> model number: client-side OCR via Tesseract.js (lazy-loaded so it
// stays out of the initial bundle). The model-number extractor is pure and
// unit-tested separately from the OCR call.

// Common nameplate words and brand names we never want to pick as a model #.
const STOPWORDS = new Set([
  "MODEL", "SERIAL", "TYPE", "PART", "MFG", "MFD", "REV", "VERSION", "VOLT",
  "VOLTS", "VOLTAGE", "AMPS", "WATTS", "HZ", "KW", "MAX", "MIN", "MADE",
  "USA", "CHINA", "MEXICO", "WHIRLPOOL", "KENMORE", "GE", "LG", "SAMSUNG",
  "BOSCH", "MAYTAG", "FRIGIDAIRE", "KITCHENAID",
]);

// Rank a candidate token into one of two tiers (lower = better) or reject it.
//   Tier 1: a long pure-numeric run (>= 9 digits) -- Kenmore-style models.
//   Tier 2: an alphanumeric mix of letters + digits -- Whirlpool/GE/etc.
// Anything else (too short, too long, all letters, year, stopword) is rejected.
function tier(token) {
  if (token.length < 5 || token.length > 16) return null;
  if (STOPWORDS.has(token)) return null;
  if (/^\d{4}$/.test(token)) return null;       // looks like a year
  const hasLetter = /[A-Z]/.test(token);
  const hasDigit = /\d/.test(token);
  if (!hasDigit) return null;                    // pure word, never a model
  if (!hasLetter && token.length >= 9) return 1; // long numeric (Kenmore)
  if (hasLetter && hasDigit) return 2;           // alphanumeric mix
  return null;                                    // short pure numeric -> too noisy
}

export function extractModelNumber(text) {
  if (!text || typeof text !== "string") return null;
  const tokens = text
    .toUpperCase()
    .split(/[^A-Z0-9-]+/)
    .map((t) => t.replace(/-/g, ""))
    .filter(Boolean);

  // Pick the best tier; within a tier, longer wins (more letters/digits = more signal).
  let best = null;
  for (const t of tokens) {
    const tt = tier(t);
    if (tt == null) continue;
    if (
      best == null ||
      tt < best.tier ||
      (tt === best.tier && t.length > best.token.length)
    ) {
      best = { tier: tt, token: t };
    }
  }
  return best ? best.token : null;
}

// Lazy import so the 3MB Tesseract bundle isn't paid for unless someone uses it.
export async function runOcr(file, { onProgress } = {}) {
  if (!file) throw new Error("no file provided");
  const mod = await import(/* webpackChunkName: "tesseract" */ "tesseract.js");
  const Tesseract = mod.default || mod;
  const { data } = await Tesseract.recognize(file, "eng", {
    logger: (m) => {
      if (onProgress && m.status === "recognizing text") {
        onProgress(Math.round((m.progress || 0) * 100));
      }
    },
  });
  return data?.text || "";
}
