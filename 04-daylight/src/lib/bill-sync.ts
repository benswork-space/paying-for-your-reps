import { db } from "@/db";
import { bills, policyAreas } from "@/db/schema";
import { eq } from "drizzle-orm";
import {
  fetchRecentBills,
  fetchBillDetail,
  fetchBillSubjects,
  fetchBillText,
} from "./congress-api";

function makeBillId(congress: number, type: string, number: number): string {
  return `${congress}-${type.toLowerCase()}-${number}`;
}

export async function syncRecentBills(congress: number = 119) {
  const result = { synced: 0, errors: [] as string[] };

  let response;
  try {
    response = await fetchRecentBills(congress);
  } catch (err) {
    result.errors.push(`Failed to fetch bill list: ${err}`);
    return result;
  }

  for (const billSummary of response.bills) {
    const billId = makeBillId(billSummary.congress, billSummary.type, billSummary.number);

    try {
      // Check if bill already exists
      const existing = await db.query.bills.findFirst({
        where: eq(bills.id, billId),
      });

      if (existing) {
        // Update if the latestAction has changed
        if (
          billSummary.latestAction &&
          existing.latestActionDate !== billSummary.latestAction.actionDate
        ) {
          await db
            .update(bills)
            .set({
              latestActionDate: billSummary.latestAction.actionDate,
              latestActionText: billSummary.latestAction.text,
              updatedAt: new Date(),
            })
            .where(eq(bills.id, billId));
          result.synced++;
        }
        continue;
      }

      // Fetch detail and subjects for new bills
      const [detail, subjects] = await Promise.all([
        fetchBillDetail(billSummary.congress, billSummary.type, billSummary.number),
        fetchBillSubjects(billSummary.congress, billSummary.type, billSummary.number),
      ]);

      // Look up policy area ID
      let policyAreaId: number | null = null;
      const policyAreaName =
        detail.bill.policyArea?.name || subjects.subjects?.policyArea?.name;
      if (policyAreaName) {
        const area = await db.query.policyAreas.findFirst({
          where: eq(policyAreas.name, policyAreaName),
        });
        policyAreaId = area?.id ?? null;
      }

      // Fetch text URL
      let textUrl: string | null = null;
      try {
        const textData = await fetchBillText(
          billSummary.congress,
          billSummary.type,
          billSummary.number
        );
        // Prefer HTML format
        const latestVersion = textData.textVersions?.[0];
        if (latestVersion) {
          const htmlFormat = latestVersion.formats.find(
            (f) => f.type === "Formatted Text"
          );
          const xmlFormat = latestVersion.formats.find(
            (f) => f.type === "Formatted XML"
          );
          textUrl = htmlFormat?.url || xmlFormat?.url || latestVersion.formats[0]?.url || null;
        }
      } catch {
        // Text not available yet — that's fine
      }

      const sponsors = detail.bill.sponsors?.map((s) => ({
        name: s.fullName,
        party: s.party,
        state: s.state,
      }));

      await db.insert(bills).values({
        id: billId,
        congress: billSummary.congress,
        billType: billSummary.type.toLowerCase(),
        billNumber: billSummary.number,
        title: billSummary.title,
        introducedDate: detail.bill.introducedDate,
        policyAreaId,
        latestActionDate: billSummary.latestAction?.actionDate ?? null,
        latestActionText: billSummary.latestAction?.text ?? null,
        originChamber: billSummary.originChamber,
        sponsors: sponsors ? JSON.stringify(sponsors) : null,
        congressGovUrl: `https://www.congress.gov/bill/${billSummary.congress}th-congress/${billSummary.originChamber.toLowerCase()}-bill/${billSummary.number}`,
        textUrl,
        rawJson: JSON.stringify(detail.bill),
        summaryStatus: "pending",
      });

      result.synced++;
    } catch (err) {
      result.errors.push(`Failed to sync ${billId}: ${err}`);
    }
  }

  return result;
}
