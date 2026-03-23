"use client";

import { useState } from "react";

export default function InfoButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-4 z-40 flex h-10 w-10 items-center justify-center rounded-full border border-zinc-300 bg-white shadow-md transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800"
        aria-label="About this data"
      >
        <span className="text-lg font-serif font-semibold text-zinc-500 dark:text-zinc-400">
          i
        </span>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          onClick={(e) => {
            if (e.target === e.currentTarget) setOpen(false);
          }}
        >
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl dark:bg-zinc-900">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">About this data</h2>
              <button
                onClick={() => setOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
                aria-label="Close"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mt-4 space-y-4 text-sm text-zinc-600 dark:text-zinc-400">
              <div>
                <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                  Data sources
                </h3>
                <ul className="mt-1 ml-4 list-disc space-y-1">
                  <li>
                    <strong>Campaign finance:</strong> FEC filings via{" "}
                    <a
                      href="https://www.opensecrets.org"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-zinc-900 dark:hover:text-zinc-200"
                    >
                      OpenSecrets
                    </a>
                  </li>
                  <li>
                    <strong>Voting records:</strong>{" "}
                    <a
                      href="https://www.congress.gov"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-zinc-900 dark:hover:text-zinc-200"
                    >
                      Congress.gov
                    </a>{" "}
                    and{" "}
                    <a
                      href="https://github.com/unitedstates/congress"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-zinc-900 dark:hover:text-zinc-200"
                    >
                      unitedstates/congress
                    </a>
                  </li>
                  <li>
                    <strong>District opinion:</strong>{" "}
                    <a
                      href="https://cces.gov.harvard.edu/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-zinc-900 dark:hover:text-zinc-200"
                    >
                      Cooperative Election Study
                    </a>{" "}
                    (MRP estimates, ±7 point margin)
                  </li>
                  <li>
                    <strong>Member data:</strong>{" "}
                    <a
                      href="https://github.com/unitedstates/congress-legislators"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-zinc-900 dark:hover:text-zinc-200"
                    >
                      unitedstates/congress-legislators
                    </a>
                  </li>
                  <li>
                    <strong>ZIP-to-district mapping:</strong> U.S. Census
                    Bureau ZCTA relationship files
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                  Methodology
                </h3>
                <p className="mt-1">
                  <strong>Donor alignment</strong>{" "}measures how often a
                  representative&apos;s votes match the expected preferences
                  of their top donor industries. Industry-to-vote mappings
                  are sourced from interest group scorecards where possible
                  and are{" "}
                  <a
                    href="https://github.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-zinc-900 dark:hover:text-zinc-200"
                  >
                    published openly
                  </a>
                  .
                </p>
                <p className="mt-2">
                  <strong>District alignment</strong>{" "}compares estimated
                  district-level public opinion (via Yale YCOM) with the
                  representative&apos;s actual votes on corresponding
                  legislation.
                </p>
              </div>

              <div className="rounded-lg bg-zinc-100 p-3 dark:bg-zinc-800">
                <p className="text-xs">
                  <strong className="text-zinc-900 dark:text-zinc-100">
                    Correlation ≠ causation.
                  </strong>{" "}
                  Representatives may receive donations because of
                  pre-existing positions, not the other way around. We show
                  connections — you decide what they mean.
                </p>
              </div>

              <a
                href="/methodology"
                className="inline-block text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
              >
                Full methodology →
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
