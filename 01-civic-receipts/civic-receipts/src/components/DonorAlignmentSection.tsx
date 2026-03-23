import type { DonorAlignment } from "@/lib/types";

interface DonorAlignmentSectionProps {
  alignment: DonorAlignment;
}

export default function DonorAlignmentSection({
  alignment,
}: DonorAlignmentSectionProps) {
  return (
    <section>
      <h3 className="text-lg font-semibold">Donor alignment</h3>
      <p className="mt-1 text-sm text-zinc-500">
        How often their votes align with their top donors&apos; interests
      </p>

      {/* Alignment slider */}
      <div className="mt-4 space-y-2">
        <div className="space-y-0">
          <div className="relative" style={{ paddingTop: "12px" }}>
            <div
              className="absolute top-0 -translate-x-1/2 text-zinc-700 dark:text-zinc-300"
              style={{ left: `${alignment.overall_pct}%` }}
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
            Apparent alignment with donor interests based on{" "}
            {alignment.total_votes_scored} scored votes.
          </p>
          <a
            href={alignment.methodology_url}
            className="mt-1 inline-block text-xs text-zinc-400 underline hover:text-zinc-600"
          >
            How we calculate this
          </a>
        </div>
      </div>

      {/* Examples */}
      {alignment.examples.length > 0 && (
        <div className="mt-6 space-y-2">
          <h4 className="text-sm font-medium text-zinc-500">Notable votes</h4>
          {alignment.examples.map((ex, i) => (
            <div
              key={i}
              className={`rounded-lg border p-3 text-sm ${
                ex.aligned
                  ? "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950"
                  : "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  {ex.vote_description}
                </p>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${
                    ex.aligned
                      ? "bg-amber-200 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                      : "bg-green-200 text-green-800 dark:bg-green-900 dark:text-green-200"
                  }`}
                >
                  {ex.aligned ? "More aligned" : "Less aligned"}
                </span>
              </div>
              <p className="mt-1 text-zinc-600 dark:text-zinc-400">
                Rep voted {ex.member_voted}, and has top donor(s) from the{" "}
                <strong>{ex.industry.replace(/[()]/g, "")}</strong> industry
              </p>
              {ex.bill_url && (
                <a
                  href={ex.bill_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-block text-xs text-zinc-400 underline"
                >
                  View bill &rarr;
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
