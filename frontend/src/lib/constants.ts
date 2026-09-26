export const FEATURE_NAMES = [
  "decision_speed",
  "exploration",
  "risk_tolerance",
  "evidence_seeking",
  "reconsideration",
  "consistency",
  "novelty_seeking",
  "uncertainty_tolerance",
  "adaptability",
] as const;

export type FeatureName = (typeof FEATURE_NAMES)[number];

export const FEATURE_LABELS: Record<FeatureName, string> = {
  decision_speed: "Decision Speed",
  exploration: "Exploration",
  risk_tolerance: "Risk Preference",
  evidence_seeking: "Evidence Seeking",
  reconsideration: "Reconsideration",
  consistency: "Consistency",
  novelty_seeking: "Novelty Seeking",
  uncertainty_tolerance: "Uncertainty Tolerance",
  adaptability: "Adaptability",
};

export const FEATURE_DESCRIPTIONS: Record<FeatureName, string> = {
  decision_speed: "How quickly you tend to decide relative to the number of options.",
  exploration: "How many options you inspect before committing.",
  risk_tolerance: "Tendency toward higher- or lower-risk options when a spread exists.",
  evidence_seeking: "Whether you open additional information before deciding.",
  reconsideration: "How often you revisit or reverse a choice.",
  consistency: "How well a single stable policy describes your past choices.",
  novelty_seeking: "Tendency toward less familiar options.",
  uncertainty_tolerance: "How much missing information you accept before deciding.",
  adaptability: "How you respond when new information arrives mid-scenario.",
};

const KEY_TO_LABEL: Record<string, string> = FEATURE_LABELS as Record<string, string>;

export function humanizeFeatureKeys(text: string): string {
  if (!text) return text;
  let out = text;
  for (const [key, label] of Object.entries(KEY_TO_LABEL)) {
    const re = new RegExp(`\\b${key}\\b`, "g");
    out = out.replace(re, label);
  }
  out = out.replace(/\brisk tolerance\b/gi, "Risk Preference");
  return out;
}

export function axisStatusWord(n: number): string {
  if (n <= 0) return "Unobserved";
  if (n < 3) return "Early signal";
  if (n < 6) return "Emerging";
  return "Observed";
}