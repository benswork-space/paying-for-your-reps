import { Resend } from "resend";

function getResend() {
  return new Resend(process.env.RESEND_API_KEY);
}

interface DigestBill {
  id: string;
  title: string;
  plainSummary: string;
  policyAreaName: string | null;
  latestActionText: string | null;
  callScript: string;
}

export async function sendWeeklyDigest(
  email: string,
  name: string | null,
  bills: DigestBill[],
  unsubscribeUrl: string
) {
  const greeting = name ? `Hi ${name}` : "Hi";

  const billSections = bills
    .map(
      (bill) => `
## ${bill.title}
${bill.policyAreaName ? `**${bill.policyAreaName}**` : ""}

${bill.plainSummary.slice(0, 300)}${bill.plainSummary.length > 300 ? "..." : ""}

${bill.latestActionText ? `**Latest:** ${bill.latestActionText}` : ""}

[Read more and take action →](${process.env.NEXTAUTH_URL}/bills/${bill.id})

---`
    )
    .join("\n");

  const html = `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <h1 style="color: #d97706; font-size: 24px;">Daylight</h1>

  <p>${greeting},</p>

  <p>Here are the bills that matter to you this week. Each one is something you can act on right now.</p>

  ${bills
    .map(
      (bill) => `
  <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 16px 0;">
    <h2 style="font-size: 16px; margin: 0 0 8px 0;">${bill.title}</h2>
    ${bill.policyAreaName ? `<span style="background: #fffbeb; color: #b45309; padding: 2px 8px; border-radius: 12px; font-size: 12px;">${bill.policyAreaName}</span>` : ""}
    <p style="font-size: 14px; color: #555; margin: 12px 0;">${bill.plainSummary.slice(0, 300)}${bill.plainSummary.length > 300 ? "..." : ""}</p>
    ${bill.latestActionText ? `<p style="font-size: 13px; color: #777;"><strong>Latest:</strong> ${bill.latestActionText}</p>` : ""}
    <a href="${process.env.NEXTAUTH_URL}/bills/${bill.id}" style="display: inline-block; background: #f59e0b; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 14px; margin-top: 8px;">Read more & take action</a>
  </div>`
    )
    .join("")}

  <p style="font-size: 14px; color: #555; margin-top: 24px;">You'll never get more than one email per week from us.</p>

  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">

  <p style="font-size: 12px; color: #999;">
    <a href="${unsubscribeUrl}" style="color: #999;">Unsubscribe</a> ·
    Daylight — Making legislation readable, one bill at a time.
  </p>
</body>
</html>`;

  await getResend().emails.send({
    from: "Daylight <onboarding@resend.dev>",
    to: email,
    subject: `${bills.length} bill${bills.length !== 1 ? "s" : ""} you can act on this week`,
    html,
  });
}
