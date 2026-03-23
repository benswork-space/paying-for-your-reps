import { db } from "@/db";
import { bills, billSummaries, policyAreas } from "@/db/schema";
import { eq } from "drizzle-orm";
import { summarizeBill } from "./claude";
import { fetchBillFullText } from "./congress-api";
import crypto from "crypto";

export async function summarizeBillById(billId: string) {
  const bill = await db.query.bills.findFirst({
    where: eq(bills.id, billId),
  });

  if (!bill) throw new Error(`Bill ${billId} not found`);
  if (bill.summaryStatus === "done") return;

  // Mark as processing
  await db
    .update(bills)
    .set({ summaryStatus: "processing", updatedAt: new Date() })
    .where(eq(bills.id, billId));

  try {
    // Get bill text
    let billText = "";
    if (bill.textUrl) {
      try {
        billText = await fetchBillFullText(bill.textUrl);
      } catch {
        // Fall back to title + raw JSON summary info
      }
    }

    // If no text available, use title and any info from the raw JSON
    if (!billText) {
      billText = bill.title;
      if (bill.rawJson) {
        try {
          const raw = JSON.parse(bill.rawJson);
          if (raw.constitutionalAuthorityStatementText) {
            billText += "\n\n" + raw.constitutionalAuthorityStatementText;
          }
        } catch {
          // ignore
        }
      }
    }

    // Get policy area name
    let policyAreaName: string | null = null;
    if (bill.policyAreaId) {
      const area = await db.query.policyAreas.findFirst({
        where: eq(policyAreas.id, bill.policyAreaId),
      });
      policyAreaName = area?.name ?? null;
    }

    const result = await summarizeBill(
      bill.title,
      billText,
      policyAreaName,
      bill.latestActionText
    );

    const textHash = crypto
      .createHash("md5")
      .update(billText)
      .digest("hex");

    await db.insert(billSummaries).values({
      billId,
      plainSummary: result.plainSummary,
      keyImpacts: JSON.stringify(result.keyImpacts),
      whoAffected: result.whoAffected,
      statusPlainLanguage: result.statusPlainLanguage,
      callScript: result.callScript,
      letterTemplate: result.letterTemplate,
      billTextHash: textHash,
    });

    await db
      .update(bills)
      .set({ summaryStatus: "done", updatedAt: new Date() })
      .where(eq(bills.id, billId));

    return result;
  } catch (err) {
    await db
      .update(bills)
      .set({ summaryStatus: "error", updatedAt: new Date() })
      .where(eq(bills.id, billId));
    throw err;
  }
}

export async function summarizePendingBills(batchSize: number = 5) {
  const pending = await db.query.bills.findMany({
    where: eq(bills.summaryStatus, "pending"),
    limit: batchSize,
  });

  const results = { processed: 0, errors: [] as string[] };

  for (const bill of pending) {
    try {
      await summarizeBillById(bill.id);
      results.processed++;
    } catch (err) {
      results.errors.push(`${bill.id}: ${err}`);
    }
  }

  return results;
}
