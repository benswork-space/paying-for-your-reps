import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { db } from "@/db";
import { billTracking } from "@/db/schema";
import { and, eq, sql } from "drizzle-orm";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = await auth();

  let isTracking = false;
  if (session?.user?.id) {
    const existing = await db.query.billTracking.findFirst({
      where: and(
        eq(billTracking.userId, session.user.id),
        eq(billTracking.billId, id)
      ),
    });
    isTracking = !!existing;
  }

  const [{ count }] = await db
    .select({ count: sql<number>`COUNT(*)` })
    .from(billTracking)
    .where(eq(billTracking.billId, id));

  return NextResponse.json({ isTracking, count });
}

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const existing = await db.query.billTracking.findFirst({
    where: and(
      eq(billTracking.userId, session.user.id),
      eq(billTracking.billId, id)
    ),
  });

  if (existing) {
    await db
      .delete(billTracking)
      .where(
        and(
          eq(billTracking.userId, session.user.id),
          eq(billTracking.billId, id)
        )
      );
  } else {
    await db.insert(billTracking).values({
      userId: session.user.id,
      billId: id,
    });
  }

  const [{ count }] = await db
    .select({ count: sql<number>`COUNT(*)` })
    .from(billTracking)
    .where(eq(billTracking.billId, id));

  return NextResponse.json({ isTracking: !existing, count });
}
