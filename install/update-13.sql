
-- Bug 785 --
ALTER TABLE device ADD COLUMN deleted tinyint(1) NOT NULL DEFAULT 0;
