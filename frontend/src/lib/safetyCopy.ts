/**
 * Centralized guard against unsupported claims.
 *
 * Every user-facing string that MIRROR shows — including LLM narration —
 * must pass through `assertSafeCopy` or be rejected. The bans here reflect
 * the project's core principle: we model observable interaction behavior,
 * not private mental states.
 */

const BANNED_PATTERNS: { pattern: RegExp; reason: string }[] = [
  // Mind-reading claims
  { pattern: /\b(read(s|ing)?\s+your\s+mind)\b/i, reason: "mind-reading claim" },
  { pattern: /\b(inside\s+your\s+(head|mind|brain))\b/i, reason: "mind-reading claim" },
  { pattern: /\bknow(s|ing)?\s+what\s+you('| a)?re\s+thinking\b/i, reason: "mind-reading claim" },
  { pattern: /\bunderstands?\s+your\s+mind\b/i, reason: "mind-reading claim" },

  // Certainty claims
  { pattern: /\byou\s+will\s+(definitely|certainly|surely)\b/i, reason: "certainty claim" },
  { pattern: /\byou\s+always\s+choose\b/i, reason: "certainty claim" },
  { pattern: /\bperfect\s+prediction\b/i, reason: "certainty claim" },
  { pattern: /\b100%\s+(certain|sure|accurate)\b/i, reason: "certainty claim" },

  // Psychological diagnosis
  { pattern: /\byou\s+are\s+(an?\s+)?(impulsive|neurotic|introvert|extrovert|type\s+[a-z])\b/i, reason: "psychological diagnosis" },
  { pattern: /\byour\s+personality\s+(is|type)\b/i, reason: "psychological diagnosis" },
  { pattern: /\bdiagnos(e|is|ing)\b/i, reason: "clinical claim" },
  { pattern: /\bmental\s+(health|illness|disorder)\b/i, reason: "clinical claim" },

  // Intelligence scoring
  { pattern: /\byour\s+intelligence\b/i, reason: "intelligence scoring" },
  { pattern: /\bIQ\b/, reason: "intelligence scoring" },
];

export interface SafetyCheck {
  ok: boolean;
  violations: { reason: string; match: string }[];
}

export function checkCopy(text: string): SafetyCheck {
  if (!text) return { ok: true, violations: [] };
  const violations: { reason: string; match: string }[] = [];
  for (const { pattern, reason } of BANNED_PATTERNS) {
    const m = text.match(pattern);
    if (m) {
      violations.push({ reason, match: m[0] });
    }
  }
  return { ok: violations.length === 0, violations };
}

/**
 * Throws in development if the text contains a banned claim.
 * In production, logs a console warning and returns a safe fallback.
 */
export function assertSafeCopy(text: string, fallback: string): string {
  const result = checkCopy(text);
  if (result.ok) return text;
  const msg = `Banned copy in "${text}": ${result.violations
    .map((v) => v.reason)
    .join(", ")}`;
  if (process.env.NODE_ENV !== "production") {
    throw new Error(msg);
  }
  // eslint-disable-next-line no-console
  console.warn(msg);
  return fallback;
}