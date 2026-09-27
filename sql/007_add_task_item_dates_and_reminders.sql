-- تاریخ شروع/پایان زیرکار + اتصال یادآوری و پیگیری به task_items

BEGIN;

ALTER TABLE task_items ADD COLUMN IF NOT EXISTS start_date date;
ALTER TABLE task_items ADD COLUMN IF NOT EXISTS end_date date;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'task_items_dates_check'
    ) THEN
        ALTER TABLE task_items
            ADD CONSTRAINT task_items_dates_check CHECK (
                end_date IS NULL OR start_date IS NULL OR end_date >= start_date
            );
    END IF;
END $$;

COMMENT ON COLUMN task_items.start_date IS
    'شروع برنامه‌ریزی‌شده زیرکار؛ مبنای یادآوری شروع.';

COMMENT ON COLUMN task_items.end_date IS
    'پایان/مهلت زیرکار؛ مبنای یادآوری مهلت و پیگیری.';

CREATE INDEX IF NOT EXISTS task_items_end_date_idx
    ON task_items (end_date)
    WHERE end_date IS NOT NULL AND is_completed = false;

ALTER TABLE task_follow_ups ADD COLUMN IF NOT EXISTS task_item_id integer;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'task_follow_ups_task_item_id_fkey'
    ) THEN
        ALTER TABLE task_follow_ups
            ADD CONSTRAINT task_follow_ups_task_item_id_fkey
            FOREIGN KEY (task_item_id) REFERENCES task_items(id) ON DELETE CASCADE;
    END IF;
END $$;

COMMENT ON COLUMN task_follow_ups.task_item_id IS
    'اختیاری؛ اگر پر باشد پیگیری مخصوص همان زیرکار است.';

CREATE INDEX IF NOT EXISTS task_follow_ups_task_item_id_idx
    ON task_follow_ups (task_item_id, follow_up_date DESC)
    WHERE task_item_id IS NOT NULL;

ALTER TABLE reminders ADD COLUMN IF NOT EXISTS task_item_id integer;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'reminders_task_item_id_fkey'
    ) THEN
        ALTER TABLE reminders
            ADD CONSTRAINT reminders_task_item_id_fkey
            FOREIGN KEY (task_item_id) REFERENCES task_items(id) ON DELETE CASCADE;
    END IF;
END $$;

COMMENT ON COLUMN reminders.task_item_id IS
    'اختیاری؛ یادآوری مرتبط با زیرکار. scheduled_at/next_run_at می‌تواند از start_date/end_date زیرکار پر شود.';

CREATE INDEX IF NOT EXISTS reminders_task_item_id_idx
    ON reminders (task_item_id)
    WHERE task_item_id IS NOT NULL;

CREATE OR REPLACE FUNCTION task_follow_ups_validate_task_item()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_item_task_id integer;
BEGIN
    IF NEW.task_item_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT task_id INTO v_item_task_id
    FROM task_items
    WHERE id = NEW.task_item_id;

    IF v_item_task_id IS NULL THEN
        RAISE EXCEPTION 'task_item_id % does not exist', NEW.task_item_id;
    END IF;

    IF v_item_task_id IS DISTINCT FROM NEW.task_id THEN
        RAISE EXCEPTION 'task_item_id must belong to the same task_id';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS task_follow_ups_validate_task_item_trg ON task_follow_ups;

CREATE TRIGGER task_follow_ups_validate_task_item_trg
    BEFORE INSERT OR UPDATE ON task_follow_ups
    FOR EACH ROW
    EXECUTE FUNCTION task_follow_ups_validate_task_item();

COMMIT;
