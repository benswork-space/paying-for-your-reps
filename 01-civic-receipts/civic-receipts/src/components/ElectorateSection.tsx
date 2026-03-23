import type { ElectorateAlignment } from "@/lib/types";
import { formatPct } from "@/lib/format";

interface ElectorateSectionProps {
  alignment: ElectorateAlignment;
}

export default function ElectorateSection({
  alignment,
}: ElectorateSectionProps) {
  return (
    <section>
      <h3 className="text-lg font-semibold">District alignment</h3>
      <p className="mt-1 text-sm text-zinc-500">
        How often they vote the way your district wants on key issues
      </p>

      {/* Alignment slider */}
      <div className="mt-4 space-y-2">
        <div className="space-y-0">
          <div className="relative" style={{ paddingTop: "12px" }}>
            <div
              className="absolute top-0 -translate-x-1/2 text-zinc-700 dark:text-zinc-300"
              style={{ left: `${100 - alignment.against_electorate_pct}%` }}
            >
              &#9660;
            </div>
            <div
              className="h-2 w-full rounded-full"
              style={{ background: "linear-gradient(to right, #22c55e, #eab308)" }}
            />
          </div>
          <div className="flex justify-between text-xs text-zinc-400 mt-1">
            <span>Less aligned</span>
            <span>More aligned</span>
          </div>
        </div>
        <div className="text-sm text-zinc-600 dark:text-zinc-400">
          <p>
            Apparent alignment with district opinion based on{" "}
            {alignment.issues_scored} scored issues.
          </p>
          <p className="mt-1 text-xs text-zinc-400">
            Based on CES survey data (164K respondents, 2018-2021) processed
            with MRP. Estimates have ~&plusmn;7 point margins.
          </p>
        </div>
      </div>

      {/* Highlights */}
      {alignment.highlights.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-zinc-500">Key issues</h4>
          {alignment.highlights.map((h, i) => (
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
                  District: <strong>{formatPct(h.district_support_pct)}</strong>{" "}
                  support
                  <span className="text-xs text-zinc-400">
                    {" "}
                    (&plusmn;{h.margin_of_error})
                  </span>
                </span>
                <span>
                  Rep: <strong>{h.member_position}</strong>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Against electorate + with donors */}
      {alignment.against_electorate_with_donors.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-red-600 dark:text-red-400">
            Voted against district, with donors
          </h4>
          {alignment.against_electorate_with_donors.map((c, i) => (
            <div
              key={i}
              className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm dark:border-red-900 dark:bg-red-950"
            >
              <p className="font-medium text-zinc-900 dark:text-zinc-100">
                {c.issue}
              </p>
              <p className="mt-1 text-zinc-600 dark:text-zinc-400">
                {formatPct(c.district_support_pct)} of district supports this,
                but rep {c.member_position.toLowerCase()}.{" "}
                <strong>{c.top_donor_interest}</strong> preferred:{" "}
                {c.donor_preferred}.
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
