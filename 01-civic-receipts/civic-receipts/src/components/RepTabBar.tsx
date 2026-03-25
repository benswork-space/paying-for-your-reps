"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import type { MemberSummary } from "@/lib/types";
import { partyInfo } from "@/lib/format";

function TabPhoto({ name, photoUrl }: { name: string; photoUrl: string }) {
  const [error, setError] = useState(false);

  if (error || !photoUrl) {
    const initials = name
      .split(" ")
      .filter((p) => !p.endsWith("."))
      .map((p) => p[0])
      .slice(0, 2)
      .join("");
    return (
      <div className="flex h-full w-full items-center justify-center bg-zinc-300 dark:bg-zinc-600">
        <span className="text-xs font-bold text-zinc-500 dark:text-zinc-300">
          {initials}
        </span>
      </div>
    );
  }

  return (
    <Image
      src={photoUrl}
      alt={name}
      fill
      className="object-cover"
      sizes="32px"
      onError={() => setError(true)}
    />
  );
}

interface RepTabBarProps {
  zip: string;
  members: MemberSummary[];
  activeBioguideId: string;
  activeName?: string;
}

export default function RepTabBar({
  zip,
  members,
  activeBioguideId,
  activeName,
}: RepTabBarProps) {
  function handleShare() {
    const url = window.location.href;
    const text = activeName
      ? `See who funds ${activeName} and how they vote — Paying for your Reps`
      : `See who funds your representatives — Paying for your Reps`;
    if (navigator.share) {
      navigator.share({ title: "Paying for your Reps", text, url });
    } else {
      navigator.clipboard.writeText(`${text}\n${url}`);
      alert("Link copied to clipboard!");
    }
  }

  return (
    <nav
      className="flex items-center border-b border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-zinc-900"
      aria-label="Representatives"
    >
      <div className="flex flex-1 gap-1 overflow-x-auto">
        {members.map((m) => {
          const active = m.bioguide_id === activeBioguideId;
          const { color } = partyInfo(m.party);
          return (
            <Link
              key={m.bioguide_id}
              href={`/zip/${zip}/${m.bioguide_id}`}
              className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-zinc-100 dark:bg-zinc-800"
                  : "hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <div className="relative h-8 w-8 shrink-0 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                <TabPhoto name={m.name} photoUrl={m.photo_url} />
                <div
                  className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white dark:border-zinc-900"
                  style={{ backgroundColor: color }}
                />
              </div>
              <span className="whitespace-nowrap">{m.name.split(" ").pop()}</span>
            </Link>
          );
        })}
      </div>

      {/* Action icons */}
      <div className="ml-2 flex shrink-0 gap-1">
        <button
          onClick={handleShare}
          className="flex h-8 w-8 items-center justify-center rounded-full text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
          aria-label="Share"
          title="Share"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
        </button>
        <Link
          href="/"
          className="flex h-8 w-8 items-center justify-center rounded-full text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
          aria-label="New search"
          title="Search another ZIP"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </Link>
      </div>
    </nav>
  );
}
