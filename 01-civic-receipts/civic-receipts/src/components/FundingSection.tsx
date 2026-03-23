"use client";

import { useState, useMemo } from "react";
import type { FundingData, DonorDetail } from "@/lib/types";
import { formatMoney, possessive } from "@/lib/format";
import FundingChart from "./FundingChart";

interface FundingSectionProps {
  funding: FundingData;
  gender?: "M" | "F";
}

interface UnifiedDonor {
  name: string;
  amount: number;
  type: "PAC" | "Individual" | "Organization";
  source: "campaign" | "leadership_pac";
  sourceName: string;
}

type FilterKey = "individual" | "pac";

export default function FundingSection({ funding, gender }: FundingSectionProps) {
  const hasCampaign = !!(funding.campaign && funding.campaign_raised);
  const hasLeadershipPac =
    funding.leadership_pacs && funding.leadership_pacs.length > 0;

  // Build unified donor list
  const allDonors = useMemo(() => {
    const donors: UnifiedDonor[] = [];

    if (funding.campaign) {
      for (const d of funding.campaign.top_employers) {
        donors.push({
          name: d.name,
          amount: d.amount,
          type: d.type || "Organization",
          source: "campaign",
          sourceName: "Campaign Committee",
        });
      }
      for (const d of funding.campaign.top_pac_donors) {
        donors.push({
          name: d.name,
          amount: d.amount,
          type: "PAC",
          source: "campaign",
          sourceName: "Campaign Committee",
        });
      }
    }

    if (funding.leadership_pacs) {
      for (const lp of funding.leadership_pacs) {
        for (const d of lp.top_employers) {
          donors.push({
            name: d.name,
            amount: d.amount,
            type: d.type || "Organization",
            source: "leadership_pac",
            sourceName: lp.name,
          });
        }
        for (const d of lp.top_pac_donors) {
          donors.push({
            name: d.name,
            amount: d.amount,
            type: "PAC",
            source: "leadership_pac",
            sourceName: lp.name,
          });
        }
      }
    }

    // Deduplicate: same donor may appear in campaign + leadership PAC
    // Merge by name, summing amounts, keeping highest source
    const merged = new Map<string, UnifiedDonor>();
    for (const d of donors) {
      const key = d.name;
      const existing = merged.get(key);
      if (existing) {
        existing.amount += d.amount;
        // If appears in both sources, label as "Multiple"
        if (existing.source !== d.source) {
          existing.sourceName = "Campaign + Leadership PAC";
        }
      } else {
        merged.set(key, { ...d });
      }
    }

    // Filter out refunds (negative amounts) and zero amounts
    return Array.from(merged.values())
      .filter((d) => d.amount > 0)
      .sort((a, b) => b.amount - a.amount);
  }, [funding]);

  const [filters, setFilters] = useState<Record<FilterKey, boolean>>({
    individual: true,
    pac: true,
  });

  function toggleFilter(key: FilterKey) {
    setFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  const filteredDonors = allDonors.filter((d) => {
    if (d.type === "PAC" && !filters.pac) return false;
    if (d.type !== "PAC" && !filters.individual) return false;
    return true;
  });

  return (
    <section>
      <h3 className="text-lg font-semibold">Where {possessive(gender)} money comes from</h3>
      <p className="mt-1 text-sm text-zinc-500">
        {funding.cycle} cycle &middot; {formatMoney(funding.total_raised)} total
        raised
        {hasCampaign && hasLeadershipPac && (
          <>
            {" "}
            ({formatMoney(funding.campaign_raised!)} campaign +{" "}
            {formatMoney(funding.leadership_pac_raised!)} leadership PAC)
          </>
        )}
      </p>

      {/* Funding split bar */}
      {hasCampaign && (
        <div className="mt-6">
          {(() => {
            const campaignPct = (funding.campaign_raised! / funding.total_raised) * 100;
            const leadershipPct = hasLeadershipPac
              ? (funding.leadership_pac_raised! / funding.total_raised) * 100
              : 0;

            return (
              <>
                <div className="flex h-8 overflow-hidden rounded-lg text-xs font-medium">
                  <div
                    className="flex items-center justify-center bg-blue-500 text-white transition-all"
                    style={{ width: `${campaignPct}%` }}
                  >
                    {campaignPct > 15 && formatMoney(funding.campaign_raised!)}
                  </div>
                  {hasLeadershipPac && (
                    <div
                      className="flex items-center justify-center bg-amber-500 text-white transition-all"
                      style={{ width: `${leadershipPct}%` }}
                    >
                      {leadershipPct > 15 && formatMoney(funding.leadership_pac_raised!)}
                    </div>
                  )}
                </div>
                <div className="mt-2 flex gap-4 text-xs text-zinc-600 dark:text-zinc-400">
                  <div className="flex items-center gap-1.5">
                    <div className="h-2.5 w-2.5 rounded-sm bg-blue-500" />
                    <Term
                      label="Campaign Committee"
                      explanation="The official fundraising committee for the candidate's election campaign. Contributions are limited by law to $3,300 per donor per election."
                    />
                    <span className="text-zinc-400">
                      {formatMoney(funding.campaign_raised!)}
                    </span>
                  </div>
                  {hasLeadershipPac &&
                    funding.leadership_pacs!.map((lp) => (
                      <div key={lp.committee_id} className="flex items-center gap-1.5">
                        <div className="h-2.5 w-2.5 rounded-sm bg-amber-500" />
                        <Term
                          label={lp.name}
                          explanation="A Leadership PAC is a political action committee controlled by a politician but not directly tied to their campaign. It can raise money from donors and distribute it to other candidates, parties, or political causes. Unlike campaign committees, leadership PACs cannot be used for the politician's own election."
                        />
                        <span className="text-zinc-400">
                          {formatMoney(lp.total_raised)}
                        </span>
                      </div>
                    ))}
                </div>
              </>
            );
          })()}
        </div>
      )}

      {/* Filter chips */}
      <h3 className="mt-6 text-lg font-semibold">
        Top contributors
      </h3>
      <p className="mt-0.5 text-xs text-zinc-400">
        Largest donors by employer and PAC. Individual contributions of $200 or
        less are not itemized by the FEC, so those donors&apos; names are not
        publicly available.
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        <FilterChip
          label="Individual donors"
          active={filters.individual}
          onToggle={() => toggleFilter("individual")}
        />
        <FilterChip
          label="PAC donors"
          active={filters.pac}
          onToggle={() => toggleFilter("pac")}
        />
      </div>

      {/* Scrollable donor list */}
      <div className="mt-3 max-h-80 overflow-y-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
        {filteredDonors.length === 0 ? (
          <p className="px-3 py-4 text-center text-sm text-zinc-400">
            No donors match the selected filters.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {filteredDonors.map((d, i) => (
              <li
                key={`${d.name}-${i}`}
                className="flex items-center justify-between gap-2 px-3 py-2 text-sm"
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium text-zinc-700 dark:text-zinc-300">
                    {d.name}
                  </div>
                  <div className="flex gap-2 text-xs text-zinc-400">
                    <span
                      className={
                        d.type === "PAC"
                          ? "text-amber-600 dark:text-amber-400"
                          : "text-blue-600 dark:text-blue-400"
                      }
                    >
                      {d.type === "PAC" ? "PAC" : "Employees of"}
                    </span>
                    <span>&middot;</span>
                    <span>{d.sourceName}</span>
                  </div>
                </div>
                <span className="shrink-0 font-mono text-sm font-medium text-zinc-900 dark:text-zinc-100">
                  {formatMoney(d.amount)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="mt-1 text-xs text-zinc-400">
        {filteredDonors.length} top contributors shown &middot;{" "}
        {formatMoney(filteredDonors.reduce((sum, d) => sum + d.amount, 0))}{" "}
        of {formatMoney(funding.total_raised)} total ({Math.round(
          (filteredDonors.reduce((sum, d) => sum + d.amount, 0) /
            funding.total_raised) *
            100
        )}%) &middot; Source:{" "}
        <a
          href="https://www.fec.gov"
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          FEC
        </a>
      </p>
    </section>
  );
}

function Term({
  label,
  explanation,
}: {
  label: string;
  explanation: string;
}) {
  const [showTip, setShowTip] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        type="button"
        className="border-b border-dashed border-zinc-400 dark:border-zinc-600"
        onClick={() => setShowTip(!showTip)}
        onMouseEnter={() => setShowTip(true)}
        onMouseLeave={() => setShowTip(false)}
        aria-label={`What is ${label}?`}
      >
        {label}
      </button>
      {showTip && (
        <span className="absolute bottom-full left-0 z-50 mb-2 w-64 rounded-lg bg-zinc-900 px-3 py-2 text-xs font-normal leading-relaxed text-white shadow-lg dark:bg-zinc-100 dark:text-zinc-900">
          {explanation}
        </span>
      )}
    </span>
  );
}

function FilterChip({
  label,
  active,
  onToggle,
}: {
  label: string;
  active: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
        active
          ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
          : "bg-zinc-100 text-zinc-400 line-through dark:bg-zinc-800 dark:text-zinc-500"
      }`}
    >
      {label}
    </button>
  );
}
