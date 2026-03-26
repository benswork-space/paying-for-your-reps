// === ZIP Lookup ===

export interface ZipLookupEntry {
  state: string;
  district: string;
  ratio: number;
  member_ids: string[];
}

export interface ZipLookupResult {
  zip: string;
  entries: ZipLookupEntry[];
  members: MemberSummary[];
}

export interface MemberSummary {
  bioguide_id: string;
  name: string;
  party: string;
  chamber: "house" | "senate";
  state: string;
  district?: string;
  photo_url: string;
}

// === Full Member Data ===

export interface MemberData {
  bioguide_id: string;
  name: string;
  party: string;
  chamber: "house" | "senate";
  state: string;
  district?: string;
  photo_url: string;
  serving_since: number;
  years_in_office: number;
  gender?: "M" | "F";
  funding: FundingData;
  donor_alignment: DonorAlignment;
  electorate_alignment: ElectorateAlignment;
  links: MemberLinks;
}

export interface FundingData {
  cycle: string;
  total_raised: number;
  campaign_raised?: number;
  leadership_pac_raised?: number;
  top_industries: IndustryFunding[];
  campaign?: CommitteeDetail;
  leadership_pacs?: LeadershipPacDetail[];
}

export interface CommitteeDetail {
  committee_id: string;
  total_raised: number;
  individual_contributions: number;
  individual_itemized?: number;
  individual_unitemized?: number;
  pac_contributions: number;
  other_receipts?: number;
  top_employers: DonorDetail[];
  top_pac_donors: DonorDetail[];
}

export interface LeadershipPacDetail {
  committee_id: string;
  name: string;
  total_raised: number;
  top_employers: DonorDetail[];
  top_pac_donors: DonorDetail[];
}

export interface VoteRecord {
  roll_number: number;
  date: string;
  bill: string;
  description: string;
  question: string;
  position: string;
  result: string;
}

export interface VotingData {
  congress: number;
  chamber: string;
  ideology: {
    nominate_dim1: number;
    nominate_dim2: number;
    description: string;
  };
  vote_stats: {
    total_votes: number;
    yea: number;
    nay: number;
    absent_or_present: number;
  };
  recent_votes: VoteRecord[];
}

export interface IndustryFunding {
  code: string;
  name: string;
  amount: number;
  donors: DonorDetail[];
}

export interface DonorDetail {
  name: string;
  type: "PAC" | "Individual" | "Organization";
  amount: number;
}

export interface DonorAlignment {
  overall_pct: number;
  total_votes_scored: number;
  methodology_url: string;
  examples: AlignmentExample[];
}

export interface AlignmentExample {
  vote_description: string;
  industry?: string;
  industry_preferred?: string;
  donor_name?: string;
  donor_category?: string;
  donor_expected?: string;
  member_voted: string;
  aligned: boolean;
  confidence?: number;
  date?: string;
  bill?: string;
  bill_url?: string;
  donors?: string[];
  reason?: string;
}

export interface ElectorateAlignment {
  issues_scored: number;
  against_electorate_pct: number;
  highlights: ElectorateHighlight[];
  against_electorate_with_donors: ElectorateDonorConflict[];
}

export interface ElectorateHighlight {
  issue: string;
  district_support_pct: number;
  margin_of_error: number;
  member_position: string;
  aligned_with_electorate: boolean;
  aligned_with_donors: boolean;
}

export interface ElectorateDonorConflict {
  issue: string;
  district_support_pct: number;
  member_position: string;
  top_donor_interest: string;
  donor_preferred: string;
}

export interface MemberLinks {
  voting_record: string;
  opensecrets: string;
  official_website: string;
}

export interface DistrictIssue {
  issue: string;
  topic: string;
  support_pct: number;
  margin_of_error: number;
}

export interface DistrictOpinion {
  district: string;
  issues: DistrictIssue[];
}
