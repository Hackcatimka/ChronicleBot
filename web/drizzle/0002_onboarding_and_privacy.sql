ALTER TABLE `chronicle_settings` ADD `onboarding_complete` integer DEFAULT 0 NOT NULL;
--> statement-breakpoint
ALTER TABLE `chronicle_settings` ADD `selected_areas` text DEFAULT '["Growth","Work","Relationships","Health","Creativity","Rest"]' NOT NULL;
--> statement-breakpoint
UPDATE `chronicle_settings` SET `onboarding_complete` = 1
WHERE `id` = 1
AND (EXISTS (SELECT 1 FROM `moments` LIMIT 1) OR EXISTS (SELECT 1 FROM `goals` LIMIT 1));
--> statement-breakpoint
PRAGMA optimize;
