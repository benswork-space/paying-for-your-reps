"use client";

import Image from "next/image";
import { useState } from "react";
import type { MemberData } from "@/lib/types";
import { partyInfo } from "@/lib/format";

interface RepHeaderProps {
  member: MemberData;
}

function MemberPhoto({ member }: { member: MemberData }) {
  const [error, setError] = useState(false);

  if (error || !member.photo_url) {
    // Fallback: initials on colored background
    const initials = member.name
      .split(" ")
      .filter((p) => !p.endsWith("."))
      .map((p) => p[0])
      .slice(0, 2)
      .join("");
    return (
      <div className="flex h-full w-full items-center justify-center bg-zinc-300 dark:bg-zinc-600">
        <span className="text-xl font-bold text-zinc-500 dark:text-zinc-300">
          {initials}
        </span>
      </div>
    );
  }

  return (
    <Image
      src={member.photo_url}
      alt={member.name}
      fill
      className="object-cover"
      sizes="80px"
      priority
      onError={() => setError(true)}
    />
  );
}

export default function RepHeader({ member }: RepHeaderProps) {
  const { label: partyLabel, color: partyColor } = partyInfo(member.party);
  const chamberLabel = member.chamber === "house" ? "House" : "Senate";
  const districtLabel =
    member.chamber === "house"
      ? `${member.state}-${member.district}`
      : member.state;

  return (
    <div className="flex items-center gap-4">
      <div className="relative h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-zinc-200 dark:bg-zinc-700">
        <MemberPhoto member={member} />
      </div>
      <div>
        <h2 className="text-xl font-bold">{member.name}</h2>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <span
            className="inline-block rounded-full px-2 py-0.5 text-xs font-semibold text-white"
            style={{ backgroundColor: partyColor }}
          >
            {partyLabel}
          </span>
          <span>
            {chamberLabel} &middot; {districtLabel}
          </span>
        </div>
        <p className="mt-1 text-sm text-zinc-500">
          Serving since {member.serving_since} &middot;{" "}
          {member.years_in_office} years
        </p>
      </div>
    </div>
  );
}
