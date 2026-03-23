import { sqliteTable, text, integer, primaryKey } from "drizzle-orm/sqlite-core";

// ── Users & Auth ──────────────────────────────────────────────

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  name: text("name"),
  email: text("email").notNull().unique(),
  emailVerified: integer("email_verified", { mode: "timestamp" }),
  hashedPassword: text("hashed_password"),
  state: text("state"), // 2-letter state code, e.g. "CA"
  image: text("image"),
  emailNotifications: integer("email_notifications", { mode: "boolean" }).notNull().default(true),
  lastDigestSentAt: integer("last_digest_sent_at", { mode: "timestamp" }),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});

export const accounts = sqliteTable("accounts", {
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  type: text("type").notNull(),
  provider: text("provider").notNull(),
  providerAccountId: text("provider_account_id").notNull(),
  refresh_token: text("refresh_token"),
  access_token: text("access_token"),
  expires_at: integer("expires_at"),
  token_type: text("token_type"),
  scope: text("scope"),
  id_token: text("id_token"),
  session_state: text("session_state"),
}, (table) => [
  primaryKey({ columns: [table.provider, table.providerAccountId] }),
]);

export const sessions = sqliteTable("sessions", {
  sessionToken: text("session_token").primaryKey(),
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  expires: integer("expires", { mode: "timestamp" }).notNull(),
});

export const verificationTokens = sqliteTable("verification_tokens", {
  identifier: text("identifier").notNull(),
  token: text("token").notNull(),
  expires: integer("expires", { mode: "timestamp" }).notNull(),
}, (table) => [
  primaryKey({ columns: [table.identifier, table.token] }),
]);

// ── Policy Areas & User Interests ────────────────────────────

export const policyAreas = sqliteTable("policy_areas", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  name: text("name").notNull().unique(),
});

export const userInterests = sqliteTable("user_interests", {
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  policyAreaId: integer("policy_area_id").notNull().references(() => policyAreas.id, { onDelete: "cascade" }),
}, (table) => [
  primaryKey({ columns: [table.userId, table.policyAreaId] }),
]);

// ── Bills ─────────────────────────────────────────────────────

export const bills = sqliteTable("bills", {
  id: text("id").primaryKey(), // format: "{congress}-{type}-{number}", e.g. "119-hr-1234"
  congress: integer("congress").notNull(),
  billType: text("bill_type").notNull(),
  billNumber: integer("bill_number").notNull(),
  title: text("title").notNull(),
  introducedDate: text("introduced_date"),
  policyAreaId: integer("policy_area_id").references(() => policyAreas.id),
  latestActionDate: text("latest_action_date"),
  latestActionText: text("latest_action_text"),
  originChamber: text("origin_chamber"),
  sponsors: text("sponsors"), // JSON string
  congressGovUrl: text("congress_gov_url"),
  textUrl: text("text_url"),
  rawJson: text("raw_json"),
  summaryStatus: text("summary_status").notNull().default("pending"), // pending | processing | done | error
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});

export const billSummaries = sqliteTable("bill_summaries", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  billId: text("bill_id").notNull().references(() => bills.id, { onDelete: "cascade" }),
  plainSummary: text("plain_summary").notNull(),
  keyImpacts: text("key_impacts").notNull(), // JSON array
  whoAffected: text("who_affected").notNull(),
  statusPlainLanguage: text("status_plain_language").notNull(),
  callScript: text("call_script").notNull(),
  letterTemplate: text("letter_template").notNull(),
  billTextHash: text("bill_text_hash"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});

export const billTracking = sqliteTable("bill_tracking", {
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  billId: text("bill_id").notNull().references(() => bills.id, { onDelete: "cascade" }),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
}, (table) => [
  primaryKey({ columns: [table.userId, table.billId] }),
]);

export const billAlerts = sqliteTable("bill_alerts", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  billId: text("bill_id").notNull().references(() => bills.id, { onDelete: "cascade" }),
  alertType: text("alert_type").notNull(), // "upcoming_vote" | "status_change"
  alertDate: text("alert_date"),
  message: text("message").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});

// ── Email Digests ─────────────────────────────────────────────

export const emailDigests = sqliteTable("email_digests", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  sentAt: integer("sent_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  billIds: text("bill_ids").notNull(), // JSON array of bill IDs
  status: text("status").notNull().default("sent"), // sent | failed
});
