ALTER TABLE `chronicle_profiles` ADD `created_at` text DEFAULT '' NOT NULL;
--> statement-breakpoint
ALTER TABLE `chronicle_profiles` ADD `last_active_at` text DEFAULT '' NOT NULL;
--> statement-breakpoint
UPDATE `chronicle_profiles` SET `created_at` = datetime('now') WHERE `created_at` = '';
--> statement-breakpoint
UPDATE `chronicle_profiles` SET `last_active_at` = `created_at` WHERE `last_active_at` = '';
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_profiles_created_at` ON `chronicle_profiles` (`created_at` DESC);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_profiles_last_active_at` ON `chronicle_profiles` (`last_active_at` DESC);
--> statement-breakpoint
PRAGMA optimize;
