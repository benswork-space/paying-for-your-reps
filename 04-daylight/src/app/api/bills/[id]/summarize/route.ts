import { NextResponse } from "next/server";
import { summarizeBillById } from "@/lib/summarize";

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const result = await summarizeBillById(id);
    return NextResponse.json({ success: true, summary: result });
  } catch (err) {
    return NextResponse.json(
      { error: `Summarization failed: ${err}` },
      { status: 500 }
    );
  }
}
