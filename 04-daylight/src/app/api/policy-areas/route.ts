import { NextResponse } from "next/server";
import { db } from "@/db";
import { policyAreas } from "@/db/schema";

export async function GET() {
  const areas = await db.select().from(policyAreas).orderBy(policyAreas.name);
  return NextResponse.json({ policyAreas: areas });
}
