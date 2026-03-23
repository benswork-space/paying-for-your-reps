export interface CongressBillListResponse {
  bills: CongressBillSummary[];
  pagination: {
    count: number;
    next?: string;
  };
}

export interface CongressBillSummary {
  congress: number;
  latestAction?: {
    actionDate: string;
    text: string;
  };
  number: number;
  originChamber: string;
  originChamberCode: string;
  title: string;
  type: string;
  updateDate: string;
  updateDateIncludingText: string;
  url: string;
}

export interface CongressBillDetail {
  bill: {
    actions: { count: number; url: string };
    amendments: { count: number; url: string };
    cboCostEstimates?: Array<{
      description: string;
      pubDate: string;
      title: string;
      url: string;
    }>;
    committeeReports?: Array<{ citation: string; url: string }>;
    committees: { count: number; url: string };
    congress: number;
    constitutionalAuthorityStatementText?: string;
    cosponsors: { count: number; url: string };
    introducedDate: string;
    latestAction?: { actionDate: string; text: string };
    laws?: Array<{ number: string; type: string }>;
    number: number;
    originChamber: string;
    policyArea?: { name: string };
    relatedBills: { count: number; url: string };
    sponsors?: Array<{
      bioguideId: string;
      district?: number;
      firstName: string;
      fullName: string;
      lastName: string;
      party: string;
      state: string;
      url: string;
    }>;
    subjects: { count: number; url: string };
    summaries: { count: number; url: string };
    textVersions: { count: number; url: string };
    title: string;
    type: string;
    updateDate: string;
  };
}

export interface CongressBillTextResponse {
  textVersions: Array<{
    date: string;
    formats: Array<{
      type: string;
      url: string;
    }>;
    type: string;
  }>;
}

export interface CongressBillSubjectsResponse {
  subjects: {
    legislativeSubjects: Array<{ name: string }>;
    policyArea?: { name: string };
  };
}

export interface CongressBillActionsResponse {
  actions: Array<{
    actionCode?: string;
    actionDate: string;
    sourceSystem: { code: number; name: string };
    text: string;
    type: string;
  }>;
}
