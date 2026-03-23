export default function MethodologyPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-3xl font-bold">Methodology</h1>

      <section className="mt-8">
        <h2
          id="donor-alignment"
          className="text-xl font-bold text-zinc-900 dark:text-zinc-100"
        >
          Donor Alignment Score
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          We calculate how often a representative&apos;s votes align with the
          expected preferences of their top donor industries. The mapping
          between industries and votes is maintained in a publicly available
          file in our GitHub repository.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          Where possible, we source these mappings from{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            interest group scorecards
          </strong>{" "}
          (e.g., Chamber of Commerce, League of Conservation Voters) so the
          classifications come from the industries themselves, not from us.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          The alignment score is calculated as:
        </p>
        <div className="mt-2 rounded-lg bg-zinc-50 px-4 py-3 font-mono text-sm dark:bg-zinc-800">
          (votes matching industry preference) / (total scored votes where the
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
          164,000 respondents (2018-2021). MRP uses respondent demographics
          and geography to produce reliable opinion estimates for each
          congressional district, even where individual district sample sizes
          are small. Estimates have approximately{" "}
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
          immigration. For each issue, we compare the district&apos;s
          estimated opinion to how the representative actually voted on
          related legislation. A representative is counted as
          &quot;against their district&quot; when they vote against the
          position supported by an estimated majority of their constituents.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          For senators, we use the statewide average across all
          congressional districts in their state.{" "}
          <strong className="text-zinc-800 dark:text-zinc-200">
            These are correlations, not proof of causation.
          </strong>{" "}
          Survey data reflects 2018-2021 opinion, which may differ from
          current views.
        </p>
      </section>

      <hr className="my-8 border-zinc-200 dark:border-zinc-800" />

      <section>
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Data Sources
        </h2>
        <ul className="mt-3 space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
          <li className="flex gap-2">
            <span className="font-semibold text-zinc-800 dark:text-zinc-200">
              Campaign finance:
            </span>
            <span>FEC filings via OpenSecrets bulk data</span>
          </li>
          <li className="flex gap-2">
            <span className="font-semibold text-zinc-800 dark:text-zinc-200">
              Voting records:
            </span>
            <span>
              Voteview (UCLA/MIT) and unitedstates/congress
            </span>
          </li>
          <li className="flex gap-2">
            <span className="font-semibold text-zinc-800 dark:text-zinc-200">
              District opinion:
            </span>
            <span>
              Cooperative Election Study (CES) 2018-2021, processed with MRP
            </span>
          </li>
          <li className="flex gap-2">
            <span className="font-semibold text-zinc-800 dark:text-zinc-200">
              Member data:
            </span>
            <span>unitedstates/congress-legislators</span>
          </li>
          <li className="flex gap-2">
            <span className="font-semibold text-zinc-800 dark:text-zinc-200">
              ZIP-to-district mapping:
            </span>
            <span>U.S. Census Bureau ZCTA relationship files</span>
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
          occur when a campaign returns money to a donor, typically because
          the contribution exceeded legal limits or was made in error. The
          refunded amounts are still reflected in the FEC&apos;s net totals.
        </p>
      </section>

      <hr className="my-8 border-zinc-200 dark:border-zinc-800" />

      <section>
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Transparency
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          All data processing code and the industry-to-vote mapping file are
          open source. You can inspect, critique, or propose changes on GitHub.
        </p>
      </section>

      <div className="mt-8">
        <a
          href="/"
          className="text-sm text-blue-600 hover:underline dark:text-blue-400"
        >
          &larr; Back to Civic Receipts
        </a>
      </div>
    </main>
  );
}
