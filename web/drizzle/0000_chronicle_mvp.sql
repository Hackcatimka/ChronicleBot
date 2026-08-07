CREATE TABLE IF NOT EXISTS `moments` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`title` text NOT NULL,
	`content` text NOT NULL,
	`category` text DEFAULT 'Growth' NOT NULL,
	`mood` text DEFAULT 'Proud' NOT NULL,
	`is_favorite` integer DEFAULT 0 NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `goals` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`title` text NOT NULL,
	`description` text DEFAULT '' NOT NULL,
	`target_steps` integer DEFAULT 10 NOT NULL,
	`completed_steps` integer DEFAULT 0 NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_moments_created_at` ON `moments` (`created_at` DESC);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_moments_category_created_at` ON `moments` (`category`, `created_at` DESC);
--> statement-breakpoint
PRAGMA optimize;
