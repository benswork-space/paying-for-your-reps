import { requireAuth } from "@/lib/auth-helpers";
import { db } from "@/db";
import { bills, userInterests, policyAreas, billTracking } from "@/db/schema";
import { eq, desc, inArray, sql } from "drizzle-orm";
import { BillCard } from "@/components/BillCard";
import Link from "next/link";

export default async function DashboardPage() {
  const session = await requireAuth();

  // Get user's interests
  const interests = await db.query.userInterests.findMany({
    where: eq(userInterests.userId, session.user.id),
  });

  if (interests.length === 0) {
    return (
      <div className="py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Welcome to Daylight</h1>
        <p className="mt-2 text-gray-600">
          Tell us what you care about so we can show you relevant bills.
        </p>
        <Link
          href="/onboarding"
          className="mt-4 inline-block rounded-md bg-amber-500 px-6 py-2 font-medium text-white hover:bg-amber-600"
        >
          Pick your interests
        </Link>
      </div>
    );
  }

  const policyAreaIds = interests.map((i) => i.policyAreaId);

  const matchingBills = await db
    .select({
      id: bills.id,
      title: bills.title,
      introducedDate: bills.introducedDate,
      latestActionDate: bills.latestActionDate,
      latestActionText: bills.latestActionText,
      summaryStatus: bills.summaryStatus,
      policyAreaName: policyAreas.name,
      trackingCount:
        sql<number>`(SELECT COUNT(*) FROM ${billTracking} WHERE ${billTracking.billId} = ${bills.id})`,
    })
    .from(bills)
    .leftJoin(policyAreas, eq(bills.policyAreaId, policyAreas.id))
    .where(inArray(bills.policyAreaId, policyAreaIds))
    .orderBy(desc(bills.latestActionDate))
    .limit(50);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Your Bill Feed</h1>
      <p className="mt-1 text-sm text-gray-500">
        Bills matching your interests, sorted by recent activity.
      </p>

      {matchingBills.length === 0 ? (
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
          No bills matching your interests yet. Bills are synced periodically —
          check back soon.
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {matchingBills.map((bill) => (
            <BillCard key={bill.id} {...bill} />
          ))}
        </div>
      )}
    </div>
  );
}
