import type {
  ElectorateAlignment,
  DistrictOpinion,
  VotingData,
} from "@/lib/types";
import { formatPct } from "@/lib/format";

/**
 * Maps issue labels from MRP data to keywords we search for in vote descriptions.
 * Each entry: [MRP issue label, keywords to match in vote descriptions, "support" means Yea or Nay]
 */
const ISSUE_VOTE_MAP: {
  issue: string;
  keywords: string[];
  supportMeansYea: boolean;
}[] = [
  {
    issue: "Universal background checks for gun purchases",
    keywords: ["background check", "gun purchase"],
    supportMeansYea: true,
  },
  {
    issue: "Ban on assault-style weapons",
    keywords: ["assault weapon", "assault-style"],
    supportMeansYea: true,
  },
  {
    issue: "Abortion should always be legal",
    keywords: ["abortion", "reproductive right", "right to contraception"],
    supportMeansYea: true,
  },
  {
    issue: "Support the Affordable Care Act",
    keywords: ["affordable care act"],
    supportMeansYea: true,
  },
  {
    issue: "Regulate CO2 as a pollutant",
    keywords: ["carbon", "co2", "greenhouse gas", "emissions regulation"],
    supportMeansYea: true,
  },
  {
    issue: "Require minimum renewable fuel production",
    keywords: ["renewable fuel", "renewable energy standard", "clean energy"],
    supportMeansYea: true,
  },
  {
    issue: "Grant legal status to DACA recipients",
    keywords: ["daca", "dreamer", "deferred action"],
    supportMeansYea: true,
  },
  {
    issue: "Build a wall on the U.S.-Mexico border",
    keywords: ["border wall", "border barrier"],
    supportMeansYea: true,
  },
  {
    issue: "Require permits to carry concealed guns",
    keywords: ["concealed carry", "concealed weapon"],
    supportMeansYea: false, // permit requirement = restricting carry
  },
  {
    issue: "Prohibit all abortions after 20 weeks",
    keywords: ["20-week", "20 week", "late-term abortion", "pain-capable"],
    supportMeansYea: true,
  },
];

// Keywords indicating the bill inverts the expected position.
// e.g., "Born-Alive Abortion Survivors Protection Act" — voting Nay is
// the pro-choice position, so we flip the reported position.
const INVERSION_KEYWORDS = [
  "repeal", "rescind", "disapprov", "terminat", "eliminat",
  "prohibit", "block", "defund", "restrict", "ban on",
  "strike the", "nullif", "born-alive", "survivors protection",
  "pain-capable", "unborn child",
];

function isInverted(description: string): boolean {
  const desc = description.toLowerCase();
  return INVERSION_KEYWORDS.some((kw) => desc.includes(kw));
}

function findMemberPosition(
  issue: string,
  voting?: VotingData
): string | null {
  if (!voting?.recent_votes) return null;

  const mapping = ISSUE_VOTE_MAP.find((m) => m.issue === issue);
  if (!mapping) return null;

  // Search for a relevant vote (most recent first — already sorted)
  for (const vote of voting.recent_votes) {
    const desc = (vote.description || "").toLowerCase();
    const bill = (vote.bill || "").toLowerCase();
    const combined = `${desc} ${bill}`;

    // Skip procedural votes (but NOT "motion to suspend the rules and pass")
    const question = (vote.question || "").toLowerCase();
    if (
      question.includes("motion to table") ||
      question.includes("motion to recommit") ||
      question.includes("motion to commit") ||
      question.includes("motion to adjourn") ||
      question.includes("motion to discharge") ||
      question.includes("motion to reconsider") ||
      question.includes("motion to refer") ||
      question.includes("motion to instruct") ||
      question.includes("providing for consideration") ||
      question.includes("ordering the previous") ||
      question.includes("point of order") ||
      question.includes("cloture") ||
      question.includes("motion to proceed")
    ) {
      // But allow "motion to suspend the rules and pass/agree"
      if (question.includes("suspend the rules")) {
        // This is substantive — don't skip
      } else {
        continue;
      }
    }

    const matched = mapping.keywords.some((kw) => combined.includes(kw));
    if (matched && (vote.position === "Yea" || vote.position === "Nay")) {
      // If the bill inverts the issue (e.g., an anti-abortion bill matched
      // on "abortion" keyword), flip the position so scoring is correct.
      let position = vote.position;
      if (isInverted(vote.description || "")) {
        position = position === "Yea" ? "Nay" : "Yea";
      }
      return `Voted ${position}`;
    }
  }

  return null;
}

function isAligned(
  memberPosition: string,
  supportPct: number,
  issue: string
): boolean {
  const mapping = ISSUE_VOTE_MAP.find((m) => m.issue === issue);
  const majoritySupports = supportPct > 50;
  const votedYea = memberPosition.includes("Yea");

  if (!mapping) {
    // Default: majority support + Yea = aligned
    return majoritySupports === votedYea;
  }

  // If support means Yea, then majority support + Yea = aligned
  if (mapping.supportMeansYea) {
    return majoritySupports === votedYea;
  } else {
    // Support means Nay (e.g., "require permits" — supporting = restricting)
    return majoritySupports !== votedYea;
  }
}

interface ElectorateSectionProps {
  alignment: ElectorateAlignment;
  districtOpinion?: DistrictOpinion;
  voting?: VotingData;
}

export default function ElectorateSection({
  alignment,
  districtOpinion,
  voting,
}: ElectorateSectionProps) {
  // If we have live district data, use it instead of pre-computed alignment
  const useDistrictData = districtOpinion && districtOpinion.issues.length > 0;

  // Build highlights from district data + voting record
  const liveHighlights = useDistrictData
    ? districtOpinion.issues
        .map((issue) => {
          const memberPos = findMemberPosition(issue.issue, voting);
          if (!memberPos) return null;
          const aligned = isAligned(memberPos, issue.support_pct, issue.issue);
          return {
            issue: issue.issue,
            district_support_pct: issue.support_pct,
            margin_of_error: issue.margin_of_error,
            member_position: memberPos,
            aligned_with_electorate: aligned,
            aligned_with_donors: false,
          };
        })
        .filter(Boolean)
    : [];

  const highlights =
    liveHighlights.length > 0 ? liveHighlights : alignment.highlights;

  const issuesScored =
    liveHighlights.length > 0
      ? liveHighlights.length
      : alignment.issues_scored;

  const alignedCount = highlights.filter(
    (h) => h!.aligned_with_electorate
  ).length;
  const alignedPct =
    issuesScored > 0 ? Math.round((alignedCount / issuesScored) * 100) : 0;

  const districtLabel = districtOpinion?.district
    ? ` (${districtOpinion.district})`
    : "";

  return (
    <section>
      <h3 className="text-lg font-semibold">District alignment{districtLabel}</h3>
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
              Based on CES survey data (164K respondents, 2018-2021) processed
              with MRP. Estimates have ~&plusmn;7 point margins.
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
