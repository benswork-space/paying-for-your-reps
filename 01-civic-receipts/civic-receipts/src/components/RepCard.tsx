import type { MemberData, VotingData } from "@/lib/types";
import RepHeader from "./RepHeader";
import FundingSection from "./FundingSection";
import VotingSection from "./VotingSection";
import DonorAlignmentSection from "./DonorAlignmentSection";
import ElectorateSection from "./ElectorateSection";
import SourceLinks from "./SourceLinks";
import ShareButton from "./ShareButton";

interface RepCardProps {
  member: MemberData;
  voting: VotingData | null;
}

export default function RepCard({ member, voting }: RepCardProps) {
  return (
    <article className="mx-auto w-full max-w-lg space-y-10 py-4">
      <RepHeader member={member} />
      <FundingSection funding={member.funding} gender={member.gender} />
      <DonorAlignmentSection alignment={member.donor_alignment} />
      <ElectorateSection alignment={member.electorate_alignment} />
      {voting && (
        <VotingSection
          voting={voting}
          congressGovUrl={member.links.voting_record}
        />
      )}
      <SourceLinks links={member.links} />
      <ShareButton member={member} />
    </article>
  );
}
