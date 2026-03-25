import type { ElectorateAlignment } from "@/lib/types";
import { formatPct } from "@/lib/format";
import ReportIssueButton from "./ReportIssueButton";

interface ReportCtx {
  zip: string;
  bioguideId: string;
  memberName: string;
}

interface ElectorateSectionProps {
  alignment: ElectorateAlignment;
  reportCtx: ReportCtx;
}

export default function ElectorateSection({
  alignment,
  reportCtx,
}: ElectorateSectionProps) {
  // Use pre-computed alignment from the backend pipeline, which uses
  // policy_area matching with party-line context, double-negative detection,
  // and other heuristics that can't easily be replicated client-side.
  const highlights = alignment.highlights;
  const issuesScored = alignment.issues_scored;

  const alignedCount = highlights.filter(
    (h) => h.aligned_with_electorate
  ).length;
  const alignedPct =
    issuesScored > 0 ? Math.round((alignedCount / issuesScored) * 100) : 0;

  return (
    <section>
      <h3 className="text-lg font-semibold">District alignment</h3>
      <p className="mt-1 text-sm text-zinc-500">
        How often they vote the way your district wants on key issues
      </p>

      {/* Alignment slider */}
      {issuesScored > 0 && (
        <div className="mt-4 space-y-2">
          <div className="space-y-0">
            <div className="relative" style={{ paddingTop: "12px" }}>
              <div
                className="absolute top-0 -translate-x-1/2 text-zinc-700 dark:text-zinc-300"
                style={{ left: `${alignedPct}%` }}
              >
                &#9660;
              </div>
              <div
                className="h-2 w-full rounded-full"
                style={{
                  background: "linear-gradient(to right, #22c55e, #eab308)",
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-zinc-400 mt-1">
              <span>Less aligned</span>
              <span>More aligned</span>
            </div>
          </div>
          <div className="text-sm text-zinc-600 dark:text-zinc-400">
            <p>
              Apparent alignment with district opinion based on {issuesScored}{" "}
              scored issues.
            </p>
            <p className="mt-1 text-xs text-zinc-400">
              Based on{" "}
              <a
                href="https://cces.gov.harvard.edu/"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-zinc-600"
              >
                CES survey
              </a>{" "}
              data (164K respondents, 2018-2021) processed with MRP. Estimates
              have ~&plusmn;7 point margins.{" "}
              <ReportIssueButton {...reportCtx} section="electorate" />
            </p>
          </div>
        </div>
      )}

      {/* Highlights */}
      {highlights.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-zinc-500">Key issues</h4>
          {highlights.map((h, i) => {
            if (!h) return null;
            return (
              <div
                key={i}
                className={`rounded-lg border p-3 text-sm ${
                  h.aligned_with_electorate
                    ? "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950"
                    : "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
                }`}
              >
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  {h.issue}
                </p>
                <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-zinc-600 dark:text-zinc-400">
                  <span>
                    District:{" "}
                    <strong>{formatPct(h.district_support_pct)}</strong> support
                    <span className="text-xs text-zinc-400">
                      {" "}
                      (&plusmn;{h.margin_of_error})
                    </span>
                  </span>
                  <span>
                    Rep:{" "}
                    <strong>
                      {h.member_position}
                      {h.aligned_with_electorate
                        ? ", with district"
                        : ", against district"}
                    </strong>
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {issuesScored === 0 && (
        <p className="mt-4 text-sm text-zinc-400">
          No district alignment data available yet.
        </p>
      )}
    </section>
  );
}
