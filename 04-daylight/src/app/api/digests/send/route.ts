import { NextResponse } from "next/server";
import { generateWeeklyDigests } from "@/lib/digest";

export async function POST() {
  try {
    const result = await generateWeeklyDigests();
    return NextResponse.json(result);
  } catch (err) {
    return NextResponse.json(
      { error: `Digest generation failed: ${err}` },
      { status: 500 }
    );
  }
}
