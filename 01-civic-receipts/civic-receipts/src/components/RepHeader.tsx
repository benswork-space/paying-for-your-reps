import Image from "next/image";
import type { MemberData } from "@/lib/types";
import { partyInfo } from "@/lib/format";

interface RepHeaderProps {
  member: MemberData;
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
        <Image
          src={member.photo_url}
          alt={member.name}
          fill
          className="object-cover"
          sizes="80px"
          priority
        />
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
