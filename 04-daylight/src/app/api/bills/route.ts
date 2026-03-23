import { NextRequest, NextResponse } from "next/server";
import { db } from "@/db";
import { bills, billTracking, policyAreas } from "@/db/schema";
import { eq, desc, like, sql, and } from "drizzle-orm";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const policyAreaId = searchParams.get("policyAreaId");
  const search = searchParams.get("search");
  const page = parseInt(searchParams.get("page") || "1");
  const limit = parseInt(searchParams.get("limit") || "20");
  const offset = (page - 1) * limit;

  const conditions = [];
  if (policyAreaId) {
    conditions.push(eq(bills.policyAreaId, parseInt(policyAreaId)));
  }
  if (search) {
    conditions.push(like(bills.title, `%${search}%`));
  }

  const where = conditions.length > 0 ? and(...conditions) : undefined;

  const results = await db
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
      summaryStatus: bills.summaryStatus,
      policyAreaName: policyAreas.name,
      trackingCount: sql<number>`(SELECT COUNT(*) FROM ${billTracking} WHERE ${billTracking.billId} = ${bills.id})`,
    })
    .from(bills)
    .leftJoin(policyAreas, eq(bills.policyAreaId, policyAreas.id))
    .where(where)
    .orderBy(desc(bills.latestActionDate))
    .limit(limit)
    .offset(offset);

  return NextResponse.json({ bills: results, page, limit });
}
