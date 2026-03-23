import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

export interface BillSummaryResult {
  plainSummary: string;
  keyImpacts: string[];
  whoAffected: string;
  statusPlainLanguage: string;
  callScript: string;
  letterTemplate: string;
}

const SYSTEM_PROMPT = `You are a nonpartisan legislative analyst. Your job is to translate bills from legalese into plain English that any citizen can understand.

Rules:
- Present facts without advocacy. Describe what the bill does, not whether it is good or bad.
- Write at an 8th grade reading level. No jargon.
- Be specific about concrete effects on people's lives.
- The call script should be a 30-second phone call script for calling a representative.
- The letter template should have [YOUR NAME] and [YOUR ADDRESS] placeholders.

You MUST respond with valid JSON matching this exact schema:
{
  "plainSummary": "2-3 paragraph summary in plain English",
  "keyImpacts": ["impact 1", "impact 2", "impact 3"],
  "whoAffected": "1-2 sentences on who this bill most directly affects",
  "statusPlainLanguage": "Current status in plain English",
  "callScript": "30-second phone call script",
  "letterTemplate": "3-paragraph letter template with placeholders"
}`;

export async function summarizeBill(
  billTitle: string,
  billText: string,
  policyArea: string | null,
  latestAction: string | null
): Promise<BillSummaryResult> {
  const userPrompt = `Translate this bill into plain English.

Title: ${billTitle}
${policyArea ? `Policy Area: ${policyArea}` : ""}
${latestAction ? `Latest Action: ${latestAction}` : ""}

Bill Text:
${billText.slice(0, 15000)}`;

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2000,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userPrompt }],
  });

  const content = message.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type from Claude");
  }

  // Extract JSON from response (handle markdown code blocks)
  let jsonStr = content.text;
  const jsonMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (jsonMatch) {
    jsonStr = jsonMatch[1];
  }

  return JSON.parse(jsonStr.trim()) as BillSummaryResult;
}
