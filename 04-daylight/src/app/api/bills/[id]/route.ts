import { NextResponse } from "next/server";
import { db } from "@/db";
import { bills, billSummaries, billTracking, policyAreas } from "@/db/schema";
import { eq, sql } from "drizzle-orm";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const bill = await db
    .select({
      id: bills.id,
      title: bills.title,
      billType: bills.billType,
      billNumber: bills.billNumber,
      congress: bills.congress,
      introducedDate: bills.introducedDate,
      latestActionDate: bills.latestActionDate,
      latestActionText: bills.latestActionText,
      originChamber: bills.originChamber,
      sponsors: bills.sponsors,
      congressGovUrl: bills.congressGovUrl,
      summaryStatus: bills.summaryStatus,
      policyAreaName: policyAreas.name,
      trackingCount: sql<number>`(SELECT COUNT(*) FROM ${billTracking} WHERE ${billTracking.billId} = ${bills.id})`,
    })
    .from(bills)
    .leftJoin(policyAreas, eq(bills.policyAreaId, policyAreas.id))
    .where(eq(bills.id, id))
    .limit(1);

  if (bill.length === 0) {
    return NextResponse.json({ error: "Bill not found" }, { status: 404 });
  }

  // Get summary if available
  const summary = await db.query.billSummaries.findFirst({
    where: eq(billSummaries.billId, id),
  });

  return NextResponse.json({
    ...bill[0],
    sponsors: bill[0].sponsors ? JSON.parse(bill[0].sponsors) : [],
    summary: summary
      ? {
          plainSummary: summary.plainSummary,
          keyImpacts: JSON.parse(summary.keyImpacts),
          whoAffected: summary.whoAffected,
          statusPlainLanguage: summary.statusPlainLanguage,
          callScript: summary.callScript,
          letterTemplate: summary.letterTemplate,
        }
      : null,
  });
}
