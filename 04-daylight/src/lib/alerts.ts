import { db } from "@/db";
import { bills, billAlerts } from "@/db/schema";
import { eq, like, or } from "drizzle-orm";

const VOTE_KEYWORDS = [
  "passed",
  "failed",
  "agreed to",
  "rejected",
  "scheduled for",
  "reported by committee",
  "placed on calendar",
  "cloture",
  "motion to proceed",
];

export async function generateAlerts() {
  const results = { created: 0, errors: [] as string[] };

  // Find bills with action text matching vote/status keywords
  const conditions = VOTE_KEYWORDS.map((kw) =>
    like(bills.latestActionText, `%${kw}%`)
  );

  const matchingBills = await db.query.bills.findMany({
    where: or(...conditions),
  });

  for (const bill of matchingBills) {
    // Check if we already have an alert for this bill's latest action
    const existing = await db.query.billAlerts.findFirst({
      where: eq(billAlerts.billId, bill.id),
    });

    // Simple dedup: skip if we already have an alert for this bill
    // (In production, compare the action text/date)
    if (existing) continue;

    const isVote =
      bill.latestActionText &&
      ["passed", "failed", "agreed to", "rejected", "cloture"].some((kw) =>
        bill.latestActionText!.toLowerCase().includes(kw)
      );

    try {
      await db.insert(billAlerts).values({
        billId: bill.id,
        alertType: isVote ? "upcoming_vote" : "status_change",
        alertDate: bill.latestActionDate,
        message: bill.latestActionText || "Status update",
      });
      results.created++;
    } catch (err) {
      results.errors.push(`${bill.id}: ${err}`);
    }
  }

  return results;
}
