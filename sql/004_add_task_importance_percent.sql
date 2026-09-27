-- درصد اهمیت اختیاری برای tasks (اگر 003 را قبلاً بدون این ستون اجرا کرده‌اید).

BEGIN;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS importance_percent smallint;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'tasks_importance_percent_check'
    ) THEN
        ALTER TABLE tasks
            ADD CONSTRAINT tasks_importance_percent_check CHECK (
                importance_percent IS NULL
                OR (importance_percent >= 0 AND importance_percent <= 100)
            );
    END IF;
END $$;

COMMENT ON COLUMN tasks.importance_percent IS
    'درصد اهمیت اختیاری (۰ تا ۱۰۰). مکمل importance_id؛ خالی یعنی فقط سطح دسته‌بندی‌شده کافی است.';

CREATE INDEX IF NOT EXISTS tasks_importance_percent_idx
    ON tasks (project_id, importance_percent DESC NULLS LAST)
    WHERE importance_percent IS NOT NULL;

COMMIT;
