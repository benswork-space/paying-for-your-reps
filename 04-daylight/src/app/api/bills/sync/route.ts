import { NextResponse } from "next/server";
import { syncRecentBills } from "@/lib/bill-sync";

export async function POST() {
  try {
    const result = await syncRecentBills();
    return NextResponse.json(result);
  } catch (err) {
    return NextResponse.json(
      { error: `Sync failed: ${err}` },
      { status: 500 }
    );
  }
}
