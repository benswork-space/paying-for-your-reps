import { NextResponse } from "next/server";
import zipLookup from "@/lib/zipLookup";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ zip: string }> },
) {
  const { zip } = await params;
  const result = zipLookup(zip);

  if (!result || result.members.length === 0) {
    return NextResponse.json({ error: "ZIP not found" }, { status: 404 });
  }

  return NextResponse.json(result);
}
