import { NextRequest, NextResponse } from "next/server";
import { db } from "@/db";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";
import crypto from "crypto";

function verifyToken(userId: string, token: string): boolean {
  const secret = process.env.NEXTAUTH_SECRET || "changeme";
  const expected = crypto
    .createHmac("sha256", secret)
    .update(userId)
    .digest("hex");
  return crypto.timingSafeEqual(Buffer.from(token), Buffer.from(expected));
}

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const userId = searchParams.get("userId");
  const token = searchParams.get("token");

  if (!userId || !token) {
    return new NextResponse("Invalid unsubscribe link", { status: 400 });
  }

  if (!verifyToken(userId, token)) {
    return new NextResponse("Invalid unsubscribe link", { status: 403 });
  }

  await db
    .update(users)
    .set({ emailNotifications: false })
    .where(eq(users.id, userId));

  return new NextResponse(
    `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="font-family: -apple-system, sans-serif; max-width: 400px; margin: 60px auto; text-align: center; color: #333;">
  <h1 style="color: #d97706;">Daylight</h1>
  <p>You've been unsubscribed from weekly digest emails.</p>
  <p style="font-size: 14px; color: #777;">You can re-enable notifications anytime from your settings.</p>
</body>
</html>`,
    {
      headers: { "Content-Type": "text/html" },
    }
  );
}
