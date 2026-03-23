"use client";

import { useState } from "react";
import type { VotingData, VoteRecord } from "@/lib/types";

interface VotingSectionProps {
  voting: VotingData;
  congressGovUrl: string;
}

export default function VotingSection({
  voting,
  congressGovUrl,
}: VotingSectionProps) {
  const [showAll, setShowAll] = useState(false);
  const visibleVotes = showAll
    ? voting.recent_votes
    : voting.recent_votes.slice(0, 10);

  const { total_votes } = voting.vote_stats;

  return (
    <section>
      <h3 className="text-lg font-semibold">Voting record</h3>
      <p className="mt-1 text-sm text-zinc-500">
        {voting.congress}th Congress &middot; {total_votes} votes cast
      </p>

      {/* Recent votes */}
      <div className="mt-3">
        <div className="space-y-1">
          {visibleVotes.map((v) => (
            <VoteRow key={`${v.roll_number}-${v.position}`} vote={v} />
          ))}
        </div>
        {voting.recent_votes.length > 10 && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="mt-2 text-sm text-blue-600 hover:underline dark:text-blue-400"
          >
            {showAll
              ? "Show fewer"
              : `Show all ${voting.recent_votes.length} votes`}
          </button>
        )}
      </div>

      <a
        href={congressGovUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 inline-block text-sm text-blue-600 hover:underline dark:text-blue-400"
      >
        Full voting record on Congress.gov &rarr;
      </a>
    </section>
  );
}

function VoteRow({ vote }: { vote: VoteRecord }) {
  const desc = vote.description || vote.question || "Vote";
  const positionColor =
    vote.position === "Yea"
      ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
      : vote.position === "Nay"
        ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
        : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400";

  return (
    <div className="flex items-start gap-2 rounded px-2 py-1.5 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
      <span
        className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${positionColor}`}
      >
        {vote.position}
      </span>
      <div className="min-w-0">
        <span className="text-zinc-700 dark:text-zinc-300">
          {desc.length > 80 ? desc.slice(0, 80) + "…" : desc}
        </span>
        {vote.bill && (
          <span className="ml-1 text-xs text-zinc-400">{vote.bill}</span>
        )}
        <span className="ml-1 text-xs text-zinc-400">{vote.date}</span>
      </div>
    </div>
  );
}
