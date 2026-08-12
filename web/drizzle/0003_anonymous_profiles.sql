CREATE TABLE IF NOT EXISTS `chronicle_profiles` (
	`id` text PRIMARY KEY NOT NULL,
	`display_name` text DEFAULT 'Alex' NOT NULL,
	`language` text DEFAULT 'en' NOT NULL,
	`tone` text DEFAULT 'thoughtful' NOT NULL,
	`timezone` text DEFAULT 'Europe/Moscow' NOT NULL,
	`reminders_enabled` integer DEFAULT 0 NOT NULL,
	`reminder_time` text DEFAULT '20:00' NOT NULL,
	`reminder_frequency` text DEFAULT 'daily' NOT NULL,
	`onboarding_complete` integer DEFAULT 0 NOT NULL,
	`selected_areas` text DEFAULT '["Growth","Work","Relationships","Health","Creativity","Rest"]' NOT NULL
);
--> statement-breakpoint
ALTER TABLE `moments` ADD `profile_id` text DEFAULT 'legacy' NOT NULL;
--> statement-breakpoint
ALTER TABLE `goals` ADD `profile_id` text DEFAULT 'legacy' NOT NULL;
--> statement-breakpoint
INSERT OR IGNORE INTO `chronicle_profiles`
(`id`,`display_name`,`language`,`tone`,`timezone`,`reminders_enabled`,`reminder_time`,`reminder_frequency`,`onboarding_complete`,`selected_areas`)
SELECT 'legacy',`display_name`,`language`,`tone`,`timezone`,`reminders_enabled`,`reminder_time`,`reminder_frequency`,`onboarding_complete`,`selected_areas`
FROM `chronicle_settings` WHERE `id` = 1;
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_moments_profile_created_at` ON `moments` (`profile_id`,`created_at` DESC);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_goals_profile_status` ON `goals` (`profile_id`,`status`);
--> statement-breakpoint
PRAGMA optimize;
