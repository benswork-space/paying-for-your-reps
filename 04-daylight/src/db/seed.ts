import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { policyAreas } from "./schema";
import path from "path";

const POLICY_AREAS = [
  "Agriculture and Food",
  "Animals",
  "Armed Forces and National Security",
  "Arts, Culture, Religion",
  "Civil Rights and Liberties, Minority Issues",
  "Commerce",
  "Congress",
  "Crime and Law Enforcement",
  "Economics and Public Finance",
  "Education",
  "Emergency Management",
  "Energy",
  "Environmental Protection",
  "Families",
  "Finance and Financial Sector",
  "Foreign Trade and International Finance",
  "Government Operations and Politics",
  "Health",
  "Housing and Community Development",
  "Immigration",
  "International Affairs",
  "Labor and Employment",
  "Law",
  "Native Americans",
  "Public Lands and Natural Resources",
  "Science, Technology, Communications",
  "Social Sciences and History",
  "Social Welfare",
  "Sports and Recreation",
  "Taxation",
  "Transportation and Public Works",
  "Water Resources Development",
];

async function seed() {
  const dbPath = path.join(process.cwd(), "daylight.db");
  const sqlite = new Database(dbPath);
  sqlite.pragma("journal_mode = WAL");
  const db = drizzle(sqlite);

  console.log("Seeding policy areas...");

  for (const name of POLICY_AREAS) {
    await db
      .insert(policyAreas)
      .values({ name })
      .onConflictDoNothing();
  }

  console.log(`Seeded ${POLICY_AREAS.length} policy areas.`);
  sqlite.close();
}

seed().catch(console.error);
