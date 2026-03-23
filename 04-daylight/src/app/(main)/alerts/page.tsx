import { requireAuth } from "@/lib/auth-helpers";
import { db } from "@/db";
import { billAlerts, billTracking, bills } from "@/db/schema";
import { eq, inArray, desc } from "drizzle-orm";
import Link from "next/link";

export default async function AlertsPage() {
  const session = await requireAuth();

  // Get bills the user is tracking
  const tracked = await db.query.billTracking.findMany({
    where: eq(billTracking.userId, session.user.id),
  });

  const trackedBillIds = tracked.map((t) => t.billId);

  if (trackedBillIds.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
          <p>You&apos;re not tracking any bills yet.</p>
          <p className="mt-1">
            Track bills from your{" "}
            <Link href="/dashboard" className="text-amber-600 underline">
              feed
            </Link>{" "}
            to get alerts about upcoming votes and status changes.
          </p>
        </div>
      </div>
    );
  }

  const alerts = await db
    .select({
      id: billAlerts.id,
      alertType: billAlerts.alertType,
      alertDate: billAlerts.alertDate,
      message: billAlerts.message,
      createdAt: billAlerts.createdAt,
      billId: bills.id,
      billTitle: bills.title,
    })
    .from(billAlerts)
    .innerJoin(bills, eq(billAlerts.billId, bills.id))
    .where(inArray(billAlerts.billId, trackedBillIds))
    .orderBy(desc(billAlerts.createdAt))
    .limit(50);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
      <p className="mt-1 text-sm text-gray-500">
        Updates on bills you&apos;re tracking.
      </p>

      {alerts.length === 0 ? (
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
          No alerts yet. We&apos;ll notify you here when bills you&apos;re
          tracking have upcoming votes or status changes.
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {alerts.map((alert) => (
            <Link
              key={alert.id}
              href={`/bills/${alert.billId}`}
              className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      alert.alertType === "upcoming_vote"
                        ? "bg-red-50 text-red-700"
                        : "bg-blue-50 text-blue-700"
                    }`}
                  >
                    {alert.alertType === "upcoming_vote"
                      ? "Upcoming Vote"
                      : "Status Change"}
                  </span>
                  <h3 className="mt-1 text-sm font-semibold text-gray-900">
                    {alert.billTitle}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600">{alert.message}</p>
                </div>
                {alert.alertDate && (
                  <span className="shrink-0 text-xs text-gray-400">
                    {alert.alertDate}
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
