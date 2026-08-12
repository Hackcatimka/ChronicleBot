import { integer, real, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const moments = sqliteTable("moments", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  content: text("content").notNull(),
  category: text("category").notNull().default("Growth"),
  mood: text("mood").notNull().default("Proud"),
  isFavorite: integer("is_favorite", { mode: "boolean" }).notNull().default(false),
  createdAt: text("created_at").notNull(),
  profileId: text("profile_id").notNull().default("legacy"),
});

export const goals = sqliteTable("goals", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  description: text("description").notNull().default(""),
  targetSteps: integer("target_steps").notNull().default(10),
  completedSteps: integer("completed_steps").notNull().default(0),
  category: text("category").notNull().default("Growth"),
  deadline: text("deadline"),
  status: text("status").notNull().default("active"),
  completedAt: text("completed_at"),
  createdAt: text("created_at").notNull(),
  profileId: text("profile_id").notNull().default("legacy"),
});

export const momentGoals = sqliteTable("moment_goals", {
  momentId: integer("moment_id").notNull().references(() => moments.id, { onDelete: "cascade" }),
  goalId: integer("goal_id").notNull().references(() => goals.id, { onDelete: "cascade" }),
});

export const chronicleSettings = sqliteTable("chronicle_settings", {
  id: integer("id").primaryKey(),
  displayName: text("display_name").notNull().default("Alex"),
  language: text("language").notNull().default("en"),
  tone: text("tone").notNull().default("thoughtful"),
  timezone: text("timezone").notNull().default("Europe/Moscow"),
  remindersEnabled: integer("reminders_enabled", { mode: "boolean" }).notNull().default(false),
  reminderTime: text("reminder_time").notNull().default("20:00"),
  reminderFrequency: text("reminder_frequency").notNull().default("daily"),
  onboardingComplete: integer("onboarding_complete", { mode: "boolean" }).notNull().default(false),
  selectedAreas: text("selected_areas").notNull().default('["Growth","Work","Relationships","Health","Creativity","Rest"]'),
});

export const chronicleProfiles = sqliteTable("chronicle_profiles", {
  id: text("id").primaryKey(),
  displayName: text("display_name").notNull().default("Alex"),
  language: text("language").notNull().default("en"),
  tone: text("tone").notNull().default("thoughtful"),
  timezone: text("timezone").notNull().default("Europe/Moscow"),
  remindersEnabled: integer("reminders_enabled", { mode: "boolean" }).notNull().default(false),
  reminderTime: text("reminder_time").notNull().default("20:00"),
  reminderFrequency: text("reminder_frequency").notNull().default("daily"),
  onboardingComplete: integer("onboarding_complete", { mode: "boolean" }).notNull().default(false),
  selectedAreas: text("selected_areas").notNull().default('["Growth","Work","Relationships","Health","Creativity","Rest"]'),
  createdAt: text("created_at").notNull().default(""),
  lastActiveAt: text("last_active_at").notNull().default(""),
});

export const aiSettings = sqliteTable("ai_settings", {
  id: integer("id").primaryKey(),
  provider: text("provider").notNull().default("gemini"),
  grokModel: text("grok_model").notNull().default("grok-4.5"),
  geminiModel: text("gemini_model").notNull().default("gemini-3.6-flash"),
  updatedAt: text("updated_at").notNull(),
});

export const aiUsage = sqliteTable("ai_usage", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  provider: text("provider").notNull(),
  model: text("model").notNull(),
  profileId: text("profile_id").notNull(),
  feature: text("feature").notNull().default("reflection"),
  inputTokens: integer("input_tokens").notNull().default(0),
  outputTokens: integer("output_tokens").notNull().default(0),
  reasoningTokens: integer("reasoning_tokens").notNull().default(0),
  totalTokens: integer("total_tokens").notNull().default(0),
  estimatedCostUsd: real("estimated_cost_usd").notNull().default(0),
  latencyMs: integer("latency_ms").notNull().default(0),
  status: text("status").notNull().default("success"),
  errorCode: text("error_code"),
  createdAt: text("created_at").notNull(),
});
