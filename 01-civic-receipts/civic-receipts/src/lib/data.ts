import type { MemberData, VotingData, DistrictOpinion } from "./types";
import { readFile } from "fs/promises";
import path from "path";

const membersDir = path.join(process.cwd(), "public", "data", "members");
const districtsDir = path.join(process.cwd(), "public", "data", "districts");

export async function loadMember(
  bioguideId: string
): Promise<MemberData | null> {
  try {
    const filePath = path.join(membersDir, `${bioguideId}.json`);
    const raw = await readFile(filePath, "utf-8");
    return JSON.parse(raw) as MemberData;
  } catch {
    return null;
  }
}

export async function loadVotes(
  bioguideId: string
): Promise<VotingData | null> {
  try {
    const filePath = path.join(membersDir, `${bioguideId}_votes.json`);
    const raw = await readFile(filePath, "utf-8");
    return JSON.parse(raw) as VotingData;
  } catch {
    return null;
  }
}

export async function loadDistrict(
  districtCode: string
): Promise<DistrictOpinion | null> {
  try {
    const filePath = path.join(districtsDir, `${districtCode}.json`);
    const raw = await readFile(filePath, "utf-8");
    return JSON.parse(raw) as DistrictOpinion;
  } catch {
    return null;
  }
}
