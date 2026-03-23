import type {
  CongressBillListResponse,
  CongressBillDetail,
  CongressBillTextResponse,
  CongressBillSubjectsResponse,
  CongressBillActionsResponse,
} from "@/types/congress-api";

const BASE_URL = "https://api.congress.gov/v3";

function getApiKey(): string {
  const key = process.env.CONGRESS_API_KEY;
  if (!key) throw new Error("CONGRESS_API_KEY is not set");
  return key;
}

async function fetchApi<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`);
  url.searchParams.set("api_key", getApiKey());
  url.searchParams.set("format", "json");
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`Congress.gov API error: ${res.status} ${res.statusText} for ${path}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchRecentBills(
  congress: number = 119,
  offset: number = 0,
  limit: number = 250
): Promise<CongressBillListResponse> {
  return fetchApi<CongressBillListResponse>(`/bill/${congress}`, {
    sort: "updateDate+desc",
    offset: offset.toString(),
    limit: limit.toString(),
  });
}

export async function fetchBillDetail(
  congress: number,
  type: string,
  number: number
): Promise<CongressBillDetail> {
  return fetchApi<CongressBillDetail>(`/bill/${congress}/${type.toLowerCase()}/${number}`);
}

export async function fetchBillSubjects(
  congress: number,
  type: string,
  number: number
): Promise<CongressBillSubjectsResponse> {
  return fetchApi<CongressBillSubjectsResponse>(
    `/bill/${congress}/${type.toLowerCase()}/${number}/subjects`
  );
}

export async function fetchBillText(
  congress: number,
  type: string,
  number: number
): Promise<CongressBillTextResponse> {
  return fetchApi<CongressBillTextResponse>(
    `/bill/${congress}/${type.toLowerCase()}/${number}/text`
  );
}

export async function fetchBillActions(
  congress: number,
  type: string,
  number: number
): Promise<CongressBillActionsResponse> {
  return fetchApi<CongressBillActionsResponse>(
    `/bill/${congress}/${type.toLowerCase()}/${number}/actions`
  );
}

export async function fetchBillFullText(textUrl: string): Promise<string> {
  const res = await fetch(textUrl);
  if (!res.ok) {
    throw new Error(`Failed to fetch bill text: ${res.status}`);
  }
  const html = await res.text();
  // Strip HTML tags to get plain text
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}
