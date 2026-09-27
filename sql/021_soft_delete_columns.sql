-- حذف نرم: ستون is_active برای جداولی که قبلاً فقط DELETE داشتند.

ALTER TABLE user_roles
    ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

ALTER TABLE role_permissions
    ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

ALTER TABLE task_items
    ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
