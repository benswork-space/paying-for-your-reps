import { NextResponse } from "next/server";
import { summarizePendingBills } from "@/lib/summarize";

export async function POST() {
  try {
    const result = await summarizePendingBills();
    return NextResponse.json(result);
  } catch (err) {
    return NextResponse.json(
      { error: `Batch summarization failed: ${err}` },
      { status: 500 }
    );
  }
}
