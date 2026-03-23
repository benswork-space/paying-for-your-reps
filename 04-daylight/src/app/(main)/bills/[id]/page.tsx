import { db } from "@/db";
import { bills, billSummaries, billTracking, policyAreas } from "@/db/schema";
import { eq, sql } from "drizzle-orm";
import { notFound } from "next/navigation";
import { ActionPanel } from "@/components/ActionPanel";
import { TrackButton } from "@/components/TrackButton";

export default async function BillDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const [bill] = await db
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
      trackingCount:
        sql<number>`(SELECT COUNT(*) FROM ${billTracking} WHERE ${billTracking.billId} = ${bills.id})`,
    })
    .from(bills)
    .leftJoin(policyAreas, eq(bills.policyAreaId, policyAreas.id))
    .where(eq(bills.id, id))
    .limit(1);

  if (!bill) notFound();

  const summary = await db.query.billSummaries.findFirst({
    where: eq(billSummaries.billId, id),
  });

  const sponsors = bill.sponsors ? JSON.parse(bill.sponsors) : [];

  return (
    <div className="mx-auto max-w-3xl">
      {/* Header */}
      <div className="mb-6">
        {bill.policyAreaName && (
          <span className="inline-block rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
            {bill.policyAreaName}
          </span>
        )}
        <h1 className="mt-2 text-2xl font-bold text-gray-900">{bill.title}</h1>
        <div className="mt-2 flex flex-wrap gap-3 text-sm text-gray-500">
          <span>
            {bill.billType.toUpperCase()} {bill.billNumber}
          </span>
          <span>{bill.congress}th Congress</span>
          {bill.introducedDate && <span>Introduced {bill.introducedDate}</span>}
          {bill.originChamber && <span>{bill.originChamber}</span>}
        </div>
        {sponsors.length > 0 && (
          <p className="mt-2 text-sm text-gray-600">
            Sponsored by{" "}
            {sponsors
              .map(
                (s: { name: string; party: string; state: string }) =>
                  `${s.name} (${s.party}-${s.state})`
              )
              .join(", ")}
          </p>
        )}
      </div>

      {/* Summary */}
      {summary ? (
        <div className="space-y-6">
          <section>
            <h2 className="text-lg font-semibold text-gray-900">
              Plain English Summary
            </h2>
            <div className="mt-2 text-gray-700 leading-relaxed whitespace-pre-line">
              {summary.plainSummary}
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900">Key Impacts</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-gray-700">
              {(JSON.parse(summary.keyImpacts) as string[]).map(
                (impact, i) => (
                  <li key={i}>{impact}</li>
                )
              )}
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900">
              Who This Affects
            </h2>
            <p className="mt-2 text-gray-700">{summary.whoAffected}</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900">
              Current Status
            </h2>
            <p className="mt-2 text-gray-700">
              {summary.statusPlainLanguage}
            </p>
          </section>

          {/* Actions */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900">Take Action</h2>
            <div className="mt-3">
              <ActionPanel
                callScript={summary.callScript}
                letterTemplate={summary.letterTemplate}
                billTitle={bill.title}
                billUrl={
                  typeof window !== "undefined"
                    ? window.location.href
                    : `/bills/${bill.id}`
                }
              />
            </div>
          </section>
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center">
          {bill.summaryStatus === "processing" ? (
            <p className="text-gray-500">
              Summary is being generated... Check back shortly.
            </p>
          ) : bill.summaryStatus === "error" ? (
            <p className="text-red-500">
              Summary generation encountered an error. It will be retried.
            </p>
          ) : (
            <p className="text-gray-500">
              Summary pending. This bill will be summarized soon.
            </p>
          )}
        </div>
      )}

      {/* Tracking & social proof */}
      <div className="mt-8 flex items-center justify-between rounded-lg border border-gray-200 p-4">
        <span className="text-sm text-gray-600">
          {bill.trackingCount.toLocaleString()} people tracking this bill
        </span>
        <TrackButton billId={bill.id} />
      </div>

      {/* Link to Congress.gov */}
      {bill.congressGovUrl && (
        <div className="mt-4 text-center">
          <a
            href={bill.congressGovUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-amber-600 hover:text-amber-700 underline"
          >
            View full bill text on Congress.gov
          </a>
        </div>
      )}

      <p className="mt-6 text-xs text-gray-400 text-center">
        AI-generated summary. Always read the full bill text for complete details.
      </p>
    </div>
  );
}
