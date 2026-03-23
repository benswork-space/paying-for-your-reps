"use client";

import type { MemberData } from "@/lib/types";
import { formatPct } from "@/lib/format";

interface ShareButtonProps {
  member: MemberData;
}

export default function ShareButton({ member }: ShareButtonProps) {
  async function handleShare() {
    const text = `${member.name} (${member.party}) — ${formatPct(member.donor_alignment.overall_pct)} aligned with donors, ${formatPct(100 - member.electorate_alignment.against_electorate_pct)} aligned with district. See the full receipt:`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: `Civic Receipt: ${member.name}`,
          text,
          url: window.location.href,
        });
      } catch {
        // User cancelled share
      }
    } else {
      await navigator.clipboard.writeText(`${text} ${window.location.href}`);
      alert("Link copied to clipboard!");
    }
  }

  return (
    <button
      onClick={handleShare}
      className="flex w-full items-center justify-center gap-2 rounded-full bg-zinc-900 px-6 py-3 font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
    >
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
      </svg>
      Share this receipt
    </button>
  );
}
