-- افزودن ساعت پایان به meetings (برای برنامه‌ریزی چند جلسه در یک روز)

BEGIN;

ALTER TABLE meetings
    ADD COLUMN IF NOT EXISTS scheduled_end_at timestamp without time zone;

ALTER TABLE meetings
    ADD COLUMN IF NOT EXISTS ended_at timestamp without time zone;

-- پر کردن scheduled_end_at برای رکوردهای قدیمی (اگر وجود داشته باشد)
UPDATE meetings
SET scheduled_end_at = scheduled_at + (duration_minutes * interval '1 minute')
WHERE scheduled_end_at IS NULL;

ALTER TABLE meetings
    ALTER COLUMN scheduled_end_at SET NOT NULL;

ALTER TABLE meetings
    DROP CONSTRAINT IF EXISTS meetings_schedule_window_check;

ALTER TABLE meetings
    ADD CONSTRAINT meetings_schedule_window_check CHECK (scheduled_end_at > scheduled_at);

ALTER TABLE meetings
    DROP CONSTRAINT IF EXISTS meetings_actual_times_check;

ALTER TABLE meetings
    ADD CONSTRAINT meetings_actual_times_check CHECK (
        ended_at IS NULL OR held_at IS NULL OR ended_at >= held_at
    );

COMMENT ON COLUMN meetings.scheduled_end_at IS
    'پایان برنامه‌ریزی‌شده؛ برای چیدن چند جلسه در یک روز و تشخیص تداخل.';

COMMENT ON COLUMN meetings.ended_at IS
    'پایان واقعی جلسه پس از برگزاری؛ held_at زمان شروع واقعی است.';

CREATE INDEX IF NOT EXISTS meetings_manager_time_range_idx
    ON meetings (manager_user_id, scheduled_at, scheduled_end_at);

COMMIT;
