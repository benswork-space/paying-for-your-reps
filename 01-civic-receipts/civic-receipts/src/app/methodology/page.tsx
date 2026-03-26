export default function MethodologyPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-3xl font-bold">Methodology</h1>

      <section className="mt-8">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Bill Classification
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          Both the donor alignment and district alignment scores depend on
          understanding what each bill{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            actually does
          </strong>
          , not just what its title says. Congressional bill titles are often
          misleading — for example, the &quot;Do No Harm in Medicaid Act&quot;
          actually cuts Medicaid, and the &quot;Protecting Prudent Investment of
          Retirement Savings Act&quot; rolls back pension investing rules that
          labor unions supported.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          We use{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            AI-assisted classification
          </strong>{" "}
          to analyze each bill&apos;s actual content and likely impact, rather
          than relying on keyword matching against titles. Each classification
          includes a confidence score and a plain-language explanation of what
          the bill does. Bills with vague titles that can&apos;t be confidently
          classified are excluded entirely. All classifications are cached as
          auditable JSON files in our GitHub repository.
        </p>
      </section>

      <hr className="my-8 border-zinc-200 dark:border-zinc-800" />

      <section>
        <h2
          id="donor-alignment"
          className="text-xl font-bold text-zinc-900 dark:text-zinc-100"
        >
          Donor Alignment Score
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          We estimate how often a representative&apos;s votes appear favorable
          or unfavorable to their top donor industries. Each rep&apos;s top 50
          PAC donors are categorized into{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            15 industry groups
          </strong>{" "}
          (defense contractors, healthcare, fossil fuels, labor unions, tech,
          finance, etc.) by matching PAC names against known patterns.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          For each bill, the AI classification determines whether donors in a
          given industry would likely prefer a Yea or Nay vote based on the
          bill&apos;s actual impact on that industry. We then check whether the
          rep&apos;s vote was favorable or unfavorable to their donors.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          This is an{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            approximation, not a definitive measure
          </strong>
          . Industries are not monolithic — a drug pricing bill might benefit
          hospitals but hurt pharmaceutical companies, even though both are
          classified as &quot;healthcare.&quot; We exclude bills where the
          industry preference is unclear or low-confidence.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          The alignment score is calculated as:
        </p>
        <div className="mt-2 rounded-lg bg-zinc-50 px-4 py-3 font-mono text-sm dark:bg-zinc-800">
          (votes favorable to donor industries) / (total scored votes where the
          member voted)
        </div>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          The overall score is a weighted average across top funding industries,
          weighted by donation amount.
        </p>
      </section>

      <hr className="my-8 border-zinc-200 dark:border-zinc-800" />

      <section>
        <h2
          id="electorate-alignment"
          className="text-xl font-bold text-zinc-900 dark:text-zinc-100"
        >
          District Alignment Score
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          We estimate district-level public opinion using{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            Multilevel Regression and Poststratification (MRP)
          </strong>{" "}
          applied to the{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            Cooperative Election Study (CES)
          </strong>
          , a large-scale academic survey conducted by Harvard/MIT with over
          164,000 respondents (2018-2021). MRP uses respondent demographics and
          geography to produce reliable opinion estimates for each congressional
          district, even where individual district sample sizes are small.
          Estimates have approximately{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            &plusmn;7 point margins of error
          </strong>
          .
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          We cover{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            10 policy issues
          </strong>{" "}
          across gun control, abortion, healthcare, climate/environment, and
          immigration. For each issue, we use the same AI-assisted bill
          classification to identify which bills are relevant and whether voting
          Yea supports or opposes the issue. We then compare the
          representative&apos;s effective position to their district&apos;s
          estimated opinion. A representative is counted as &quot;against their
          district&quot; when they vote against the position supported by an
          estimated majority of their constituents.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          For senators, we use the statewide average across all congressional
          districts in their state.{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            These are correlations, not proof of causation.
          </strong>{" "}
          Survey data reflects 2018-2021 opinion, which may differ from current
          views.
        </p>
      </section>

      <hr className="my-8 border-zinc-200 dark:border-zinc-800" />

      <section>
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Data Sources
        </h2>
        <ul className="mt-3 space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
          <li className="flex gap-2">
            <span className="shrink-0 font-semibold text-zinc-800 dark:text-zinc-200">
              Campaign finance:
            </span>
            <span>FEC bulk filings via OpenSecrets</span>
          </li>
          <li className="flex gap-2">
            <span className="shrink-0 font-semibold text-zinc-800 dark:text-zinc-200">
              Voting records:
            </span>
            <span>Voteview (UCLA/MIT), Congresses 114-119</span>
          </li>
          <li className="flex gap-2">
            <span className="shrink-0 font-semibold text-zinc-800 dark:text-zinc-200">
              Bill subjects:
            </span>
            <span>Congress.gov API (policy area classifications)</span>
          </li>
          <li className="flex gap-2">
            <span className="shrink-0 font-semibold text-zinc-800 dark:text-zinc-200">
              District opinion:
            </span>
            <span>
              Cooperative Election Study (CES) 2018-2021, processed with MRP
            </span>
          </li>
          <li className="flex gap-2">
            <span className="shrink-0 font-semibold text-zinc-800 dark:text-zinc-200">
              Member data:
            </span>
            <span>unitedstates/congress-legislators</span>
          </li>
          <li className="flex gap-2">
            <span className="shrink-0 font-semibold text-zinc-800 dark:text-zinc-200">
              ZIP-to-district:
            </span>
            <span>U.S. Census Bureau ZCTA relationship files</span>
          </li>
          <li className="flex gap-2">
            <span className="shrink-0 font-semibold text-zinc-800 dark:text-zinc-200">
              Bill classification:
            </span>
            <span>
              AI-assisted via Claude (Anthropic), cached as auditable JSON
            </span>
          </li>
        </ul>
      </section>

      <hr className="my-8 border-zinc-200 dark:border-zinc-800" />

      <section>
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Campaign Finance Data
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          Contribution data comes from FEC filings. We show contributions to
          both the representative&apos;s{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            campaign committee
          </strong>{" "}
          and any{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            leadership PACs
          </strong>{" "}
          they control.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          Individual contributions of{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            $200 or less are not itemized
          </strong>{" "}
          by the FEC. These donors&apos; names and employers are not publicly
          available, so they do not appear in the contributor list. For some
          representatives, unitemized small-dollar donations make up the
          majority of individual contributions.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          <strong className="text-zinc-800 dark:text-zinc-200">
            Contribution refunds
          </strong>{" "}
          (negative amounts) are filtered out of the contributor list. Refunds
          occur when a campaign returns money to a donor, typically because the
          contribution exceeded legal limits or was made in error. The refunded
          amounts are still reflected in the FEC&apos;s net totals.
        </p>
      </section>

      <hr className="my-8 border-zinc-200 dark:border-zinc-800" />

      <section>
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Transparency
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          All data processing code, bill classification caches, and scoring
          logic are open source. The bill classifications — including the
          confidence score and reasoning for each — can be inspected in the{" "}
          <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs dark:bg-zinc-800">
            scripts/.cache/
          </code>{" "}
          directory. You can inspect, critique, or propose changes on GitHub.
        </p>
      </section>

      <div className="mt-8">
        <a
          href="/"
          className="text-sm text-blue-600 hover:underline dark:text-blue-400"
        >
          &larr; Back to Paying for your Reps
        </a>
      </div>
    </main>
  );
}
