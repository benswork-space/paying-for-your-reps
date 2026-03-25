import { NextResponse } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);
const REPORT_EMAIL = process.env.REPORT_EMAIL;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { zip, bioguideId, memberName, section, description, userEmail } =
      body;

    if (!description || !description.trim()) {
      return NextResponse.json(
        { error: "Description is required" },
        { status: 400 },
      );
    }

    if (!REPORT_EMAIL) {
      console.error("REPORT_EMAIL not configured in environment");
      return NextResponse.json(
        { error: "Report submission is not configured" },
        { status: 500 },
      );
    }

    const subject = `[Civic Receipts] Issue report: ${memberName || bioguideId} (${zip})`;

    const htmlBody = `
      <h2>Issue Report</h2>
      <table style="border-collapse:collapse;">
        <tr><td style="padding:4px 12px 4px 0;font-weight:bold;">ZIP Code</td><td>${zip || "N/A"}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;font-weight:bold;">Representative</td><td>${memberName || "N/A"} (${bioguideId || "N/A"})</td></tr>
        <tr><td style="padding:4px 12px 4px 0;font-weight:bold;">Section</td><td>${section || "N/A"}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;font-weight:bold;">Reporter Email</td><td>${userEmail || "Not provided"}</td></tr>
      </table>
      <h3>Description</h3>
      <p style="white-space:pre-wrap;">${description}</p>
    `;

    await resend.emails.send({
      from: "Civic Receipts <onboarding@resend.dev>",
      to: REPORT_EMAIL,
      subject,
      html: htmlBody,
      replyTo: userEmail || undefined,
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Failed to send report:", error);
    return NextResponse.json(
      { error: "Failed to send report" },
      { status: 500 },
    );
  }
}
