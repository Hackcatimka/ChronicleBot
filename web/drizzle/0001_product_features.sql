ALTER TABLE `goals` ADD `category` text DEFAULT 'Growth' NOT NULL;
--> statement-breakpoint
ALTER TABLE `goals` ADD `deadline` text;
--> statement-breakpoint
ALTER TABLE `goals` ADD `status` text DEFAULT 'active' NOT NULL;
--> statement-breakpoint
ALTER TABLE `goals` ADD `completed_at` text;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `moment_goals` (
	`moment_id` integer NOT NULL,
	`goal_id` integer NOT NULL,
	FOREIGN KEY (`moment_id`) REFERENCES `moments`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`goal_id`) REFERENCES `goals`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `idx_moment_goals_pair` ON `moment_goals` (`moment_id`, `goal_id`);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_moment_goals_goal_id` ON `moment_goals` (`goal_id`);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `chronicle_settings` (
	`id` integer PRIMARY KEY NOT NULL,
	`display_name` text DEFAULT 'Alex' NOT NULL,
	`language` text DEFAULT 'en' NOT NULL,
	`tone` text DEFAULT 'thoughtful' NOT NULL,
	`timezone` text DEFAULT 'Europe/Moscow' NOT NULL,
	`reminders_enabled` integer DEFAULT 0 NOT NULL,
	`reminder_time` text DEFAULT '20:00' NOT NULL,
	`reminder_frequency` text DEFAULT 'daily' NOT NULL
);
--> statement-breakpoint
INSERT OR IGNORE INTO `chronicle_settings` (`id`) VALUES (1);
--> statement-breakpoint
PRAGMA optimize;
