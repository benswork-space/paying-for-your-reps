import type { MemberData, VotingData, DistrictOpinion } from "@/lib/types";
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
  districtOpinion?: DistrictOpinion | null;
  zip: string;
}

export default function RepCard({ member, voting, districtOpinion, zip }: RepCardProps) {
  const reportCtx = { zip, bioguideId: member.bioguide_id, memberName: member.name };

  return (
    <article className="mx-auto w-full max-w-lg space-y-10 py-4">
      <RepHeader member={member} />
      <FundingSection funding={member.funding} gender={member.gender} />
      <DonorAlignmentSection alignment={member.donor_alignment} reportCtx={reportCtx} />
      <ElectorateSection alignment={member.electorate_alignment} reportCtx={reportCtx} />
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
