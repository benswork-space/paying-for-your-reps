import zipLookup from "@/lib/zipLookup";
import { loadMember, loadVotes } from "@/lib/data";
import RepTabBar from "@/components/RepTabBar";
import RepCard from "@/components/RepCard";
import InfoButton from "@/components/InfoButton";
import { notFound } from "next/navigation";

export default async function RepPage({
  params,
}: {
  params: Promise<{ zip: string; bioguideId: string }>;
}) {
  const { zip, bioguideId } = await params;
  const result = zipLookup(zip);

  if (!result || result.members.length === 0) {
    notFound();
  }

  const [member, voting] = await Promise.all([
    loadMember(bioguideId),
    loadVotes(bioguideId),
  ]);
  if (!member) {
    notFound();
  }

  return (
    <div className="flex flex-1 flex-col">
      <RepTabBar
        zip={zip}
        members={result.members}
        activeBioguideId={bioguideId}
        activeName={member.name}
      />

      <main className="flex-1 overflow-y-auto px-4 pb-8">
        <RepCard member={member} voting={voting} />
      </main>

      <InfoButton />
    </div>
  );
}
