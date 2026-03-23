/**
 * Format a dollar amount for display.
 * e.g. 1500000 → "$1.5M", 45000 → "$45K", 800 → "$800"
 */
export function formatMoney(amount: number): string {
  if (amount >= 1_000_000) {
    const m = amount / 1_000_000;
    return `$${m % 1 === 0 ? m.toFixed(0) : m.toFixed(1)}M`;
  }
  if (amount >= 1_000) {
    const k = amount / 1_000;
    return `$${k % 1 === 0 ? k.toFixed(0) : k.toFixed(1)}K`;
  }
  return `$${amount.toLocaleString()}`;
}

/**
 * Format a percentage for display.
 */
export function formatPct(pct: number): string {
  return `${Math.round(pct)}%`;
}

/**
 * Get possessive pronoun based on gender.
 */
export function possessive(gender?: "M" | "F"): string {
  return gender === "F" ? "her" : "his";
}

/**
 * Get subject pronoun based on gender.
 */
export function pronoun(gender?: "M" | "F"): string {
  return gender === "F" ? "she" : "he";
}

/**
 * Get party display info.
 */
export function partyInfo(party: string): { label: string; color: string } {
  switch (party) {
    case "D":
      return { label: "Democrat", color: "#2563eb" };
    case "R":
      return { label: "Republican", color: "#dc2626" };
    case "I":
      return { label: "Independent", color: "#7c3aed" };
    default:
      return { label: party, color: "#6b7280" };
  }
}
