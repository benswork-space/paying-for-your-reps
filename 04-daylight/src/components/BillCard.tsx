import Link from "next/link";

interface BillCardProps {
  id: string;
  title: string;
  policyAreaName: string | null;
  introducedDate: string | null;
  latestActionDate: string | null;
  latestActionText: string | null;
  summaryStatus: string;
  trackingCount: number;
}

export function BillCard({
  id,
  title,
  policyAreaName,
  introducedDate,
  latestActionText,
  summaryStatus,
  trackingCount,
}: BillCardProps) {
  return (
    <Link
      href={`/bills/${id}`}
      className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-gray-900 line-clamp-2">
            {title}
          </h3>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            {policyAreaName && (
              <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700">
                {policyAreaName}
              </span>
            )}
            {introducedDate && <span>Introduced {introducedDate}</span>}
          </div>
          {latestActionText && (
            <p className="mt-2 text-xs text-gray-600 line-clamp-1">
              {latestActionText}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {summaryStatus === "done" && (
            <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
              Summarized
            </span>
          )}
          {trackingCount > 0 && (
            <span className="text-xs text-gray-400">
              {trackingCount.toLocaleString()} tracking
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
