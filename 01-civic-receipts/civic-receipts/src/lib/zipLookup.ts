import type { ZipLookupResult, MemberSummary } from "./types";

// In production, this is loaded from the generated zip_lookup.json
// For now, we load the static data file
let zipData: Record<string, { entries: Array<{ state: string; district: string; ratio: number; member_ids: string[] }>; members: MemberSummary[] }> | null = null;

function getZipData() {
  if (!zipData) {
    try {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      zipData = require("../../public/data/zip_lookup.json");
    } catch {
      zipData = {};
    }
  }
  return zipData!;
}

export default function zipLookup(zip: string): ZipLookupResult | null {
  const data = getZipData();
  const entry = data[zip];

  if (!entry) {
    return null;
  }

  return {
    zip,
    entries: entry.entries,
    members: entry.members,
  };
}
