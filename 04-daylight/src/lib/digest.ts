import { db } from "@/db";
import {
  users,
  userInterests,
  bills,
  billSummaries,
  policyAreas,
  emailDigests,
} from "@/db/schema";
import { eq, inArray, gte, and, desc } from "drizzle-orm";
import { sendWeeklyDigest } from "./email";
import crypto from "crypto";

function generateUnsubscribeToken(userId: string): string {
  const secret = process.env.NEXTAUTH_SECRET || "changeme";
  return crypto
    .createHmac("sha256", secret)
    .update(userId)
    .digest("hex");
}

export async function generateWeeklyDigests() {
  const results = { sent: 0, skipped: 0, errors: [] as string[] };

  // Get all users with email notifications enabled
  const subscribedUsers = await db.query.users.findMany({
    where: eq(users.emailNotifications, true),
  });

  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  const oneWeekAgoStr = oneWeekAgo.toISOString().split("T")[0];

  for (const user of subscribedUsers) {
    try {
      // Get user's interests
      const interests = await db.query.userInterests.findMany({
        where: eq(userInterests.userId, user.id),
      });

      if (interests.length === 0) {
        results.skipped++;
        continue;
      }

      const policyAreaIds = interests.map((i) => i.policyAreaId);

      // Find bills matching interests with recent activity
      const recentBills = await db
        .select({
          id: bills.id,
          title: bills.title,
          latestActionText: bills.latestActionText,
          policyAreaName: policyAreas.name,
          plainSummary: billSummaries.plainSummary,
          callScript: billSummaries.callScript,
        })
        .from(bills)
        .innerJoin(billSummaries, eq(bills.id, billSummaries.billId))
        .leftJoin(policyAreas, eq(bills.policyAreaId, policyAreas.id))
        .where(
          and(
            inArray(bills.policyAreaId, policyAreaIds),
            gte(bills.latestActionDate, oneWeekAgoStr),
            eq(bills.summaryStatus, "done")
          )
        )
        .orderBy(desc(bills.latestActionDate))
        .limit(5);

      if (recentBills.length === 0) {
        results.skipped++;
        continue;
      }

      const token = generateUnsubscribeToken(user.id);
      const unsubscribeUrl = `${process.env.NEXTAUTH_URL}/api/unsubscribe?userId=${user.id}&token=${token}`;

      await sendWeeklyDigest(
        user.email,
        user.name,
        recentBills.map((b) => ({
          id: b.id,
          title: b.title,
          plainSummary: b.plainSummary,
          policyAreaName: b.policyAreaName,
          latestActionText: b.latestActionText,
          callScript: b.callScript,
        })),
        unsubscribeUrl
      );

      // Record digest
      await db.insert(emailDigests).values({
        userId: user.id,
        billIds: JSON.stringify(recentBills.map((b) => b.id)),
        status: "sent",
      });

      // Update last digest sent
      await db
        .update(users)
        .set({ lastDigestSentAt: new Date() })
        .where(eq(users.id, user.id));

      results.sent++;
    } catch (err) {
      results.errors.push(`${user.email}: ${err}`);
    }
  }

  return results;
}
