CREATE TABLE IF NOT EXISTS `ai_settings` (
	`id` integer PRIMARY KEY NOT NULL,
	`provider` text DEFAULT 'gemini' NOT NULL,
	`grok_model` text DEFAULT 'grok-4.5' NOT NULL,
	`gemini_model` text DEFAULT 'gemini-3.6-flash' NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `ai_usage` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`provider` text NOT NULL,
	`model` text NOT NULL,
	`profile_id` text NOT NULL,
	`feature` text DEFAULT 'reflection' NOT NULL,
	`input_tokens` integer DEFAULT 0 NOT NULL,
	`output_tokens` integer DEFAULT 0 NOT NULL,
	`reasoning_tokens` integer DEFAULT 0 NOT NULL,
	`total_tokens` integer DEFAULT 0 NOT NULL,
	`estimated_cost_usd` real DEFAULT 0 NOT NULL,
	`latency_ms` integer DEFAULT 0 NOT NULL,
	`status` text DEFAULT 'success' NOT NULL,
	`error_code` text,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_ai_usage_created_at` ON `ai_usage` (`created_at` DESC);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_ai_usage_provider_created_at` ON `ai_usage` (`provider`,`created_at` DESC);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_ai_usage_profile_created_at` ON `ai_usage` (`profile_id`,`created_at` DESC);
--> statement-breakpoint
INSERT OR IGNORE INTO `ai_settings` (`id`,`provider`,`grok_model`,`gemini_model`,`updated_at`)
VALUES (1,'gemini','grok-4.5','gemini-3.6-flash',datetime('now'));
--> statement-breakpoint
PRAGMA optimize;
