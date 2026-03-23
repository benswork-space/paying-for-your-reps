import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { db } from "@/db";
import { userInterests } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const interests = await db.query.userInterests.findMany({
    where: eq(userInterests.userId, session.user.id),
  });

  return NextResponse.json({
    policyAreaIds: interests.map((i) => i.policyAreaId),
  });
}

export async function PUT(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { policyAreaIds } = await request.json();

  if (!Array.isArray(policyAreaIds) || policyAreaIds.length === 0) {
    return NextResponse.json(
      { error: "Select at least one interest" },
      { status: 400 }
    );
  }

  // Delete existing and insert new
  await db.delete(userInterests).where(eq(userInterests.userId, session.user.id));

  await db.insert(userInterests).values(
    policyAreaIds.map((id: number) => ({
      userId: session.user.id,
      policyAreaId: id,
    }))
  );

  return NextResponse.json({ success: true });
}
