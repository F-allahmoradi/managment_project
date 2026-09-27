-- پیام خام فقط با کاربر، پروژه (از چت) و تسک ذخیره می‌شود.
-- ژانر و موجودیت از استخراج می‌آید، نه از reports / ideas_experiences / message_types.

BEGIN;

ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS task_id integer;

UPDATE messages m
SET task_id = t.id
FROM chats c
JOIN LATERAL (
    SELECT id
    FROM tasks
    WHERE project_id = c.project_id
    ORDER BY id
    LIMIT 1
) t ON true
WHERE m.chat_id = c.id
  AND m.task_id IS NULL
  AND c.project_id IS NOT NULL;

DELETE FROM message_recipients
WHERE message_id IN (SELECT id FROM messages WHERE task_id IS NULL);

DELETE FROM meeting_sync_items
WHERE message_id IN (SELECT id FROM messages WHERE task_id IS NULL);

DELETE FROM text_analyses a
USING analysis_source_types st
WHERE a.source_type_id = st.id
  AND st.code = 'message'
  AND a.source_id IN (SELECT id FROM messages WHERE task_id IS NULL);

DELETE FROM messages WHERE task_id IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'messages_task_id_fkey'
    ) THEN
        ALTER TABLE messages
            ADD CONSTRAINT messages_task_id_fkey
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE RESTRICT;
    END IF;
END
$$;

ALTER TABLE messages
    ALTER COLUMN task_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS messages_task_id_idx ON messages (task_id);

CREATE OR REPLACE FUNCTION messages_validate_task()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_chat_project integer;
    v_task_project integer;
BEGIN
    SELECT project_id INTO v_chat_project FROM chats WHERE id = NEW.chat_id;
    IF v_chat_project IS NULL THEN
        RAISE EXCEPTION 'chat must belong to a project';
    END IF;
    SELECT project_id INTO v_task_project FROM tasks WHERE id = NEW.task_id;
    IF v_task_project IS NULL THEN
        RAISE EXCEPTION 'task not found';
    END IF;
    IF v_task_project IS DISTINCT FROM v_chat_project THEN
        RAISE EXCEPTION 'task must belong to the same project as the chat';
    END IF;
    IF NEW.sender_user_id IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM project_members
        WHERE project_id = v_chat_project
          AND user_id = NEW.sender_user_id
          AND is_active
    ) THEN
        RAISE EXCEPTION 'sender must be an active project member';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS messages_validate_task_trg ON messages;
CREATE TRIGGER messages_validate_task_trg
    BEFORE INSERT OR UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION messages_validate_task();

ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_message_type_id_fkey;
ALTER TABLE messages DROP COLUMN IF EXISTS message_type_id;
DROP TABLE IF EXISTS message_types;

DELETE FROM meeting_sync_items
WHERE report_id IS NOT NULL OR idea_experience_id IS NOT NULL;

ALTER TABLE meeting_sync_items DROP CONSTRAINT IF EXISTS meeting_sync_items_report_id_fkey;
ALTER TABLE meeting_sync_items DROP CONSTRAINT IF EXISTS meeting_sync_items_idea_experience_id_fkey;
ALTER TABLE meeting_sync_items DROP CONSTRAINT IF EXISTS meeting_sync_items_one_target;

ALTER TABLE meeting_sync_items DROP COLUMN IF EXISTS report_id;
ALTER TABLE meeting_sync_items DROP COLUMN IF EXISTS idea_experience_id;

ALTER TABLE meeting_sync_items
    ADD CONSTRAINT meeting_sync_items_one_target CHECK (
        ((task_id IS NOT NULL)::integer + (message_id IS NOT NULL)::integer) = 1
    );

COMMENT ON TABLE meeting_sync_items IS
    'ردیابی خروجی sync جلسه به وظیفه یا پیام چت پروژه.';

DELETE FROM content_attachments
WHERE attachable_type IN ('report', 'idea_experience');

ALTER TABLE content_attachments DROP CONSTRAINT IF EXISTS content_attachments_attachable_type_check;
ALTER TABLE content_attachments
    ADD CONSTRAINT content_attachments_attachable_type_check CHECK (
        attachable_type IN (
            'message',
            'notification',
            'task_follow_up',
            'reminder',
            'meeting'
        )
    );

DELETE FROM text_analyses a
USING analysis_source_types st
WHERE a.source_type_id = st.id
  AND st.code IN ('report', 'idea_experience');

DELETE FROM analysis_outputs o
USING analysis_output_types t
WHERE o.output_type_id = t.id
  AND t.code = 'idea_experience';

DELETE FROM analysis_source_types WHERE code IN ('report', 'idea_experience');
DELETE FROM analysis_output_types WHERE code = 'idea_experience';

DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS report_types;
DROP TABLE IF EXISTS ideas_experiences;
DROP TABLE IF EXISTS idea_experience_types;

UPDATE text_analyses a
SET project_id = c.project_id
FROM analysis_source_types st, messages m, chats c
WHERE st.id = a.source_type_id
  AND st.code = 'message'
  AND m.id = a.source_id
  AND c.id = m.chat_id
  AND a.project_id IS NULL;

COMMIT;
