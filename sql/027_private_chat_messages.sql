-- گفتگوی خصوصی بدون پروژه و بدون تسک؛ گفتگوی پروژه همچنان تسک می‌خواهد.

BEGIN;

ALTER TABLE messages
    ALTER COLUMN task_id DROP NOT NULL;

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
        IF NEW.task_id IS NOT NULL THEN
            RAISE EXCEPTION 'private chat must not have a task';
        END IF;
        IF NEW.sender_user_id IS NOT NULL AND NOT EXISTS (
            SELECT 1
            FROM chat_members
            WHERE chat_id = NEW.chat_id
              AND user_id = NEW.sender_user_id
        ) THEN
            RAISE EXCEPTION 'sender must be a chat member';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.task_id IS NULL THEN
        RAISE EXCEPTION 'project chat message must have a task';
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

COMMENT ON TABLE messages IS
    'متن خام نظر. در گفتگوی پروژه به تسک همان پروژه وصل است؛ در گفتگوی خصوصی task_id خالی می‌ماند.';

COMMENT ON COLUMN messages.task_id IS
    'تسک بستر نظر در گفتگوی پروژه؛ برای گفتگوی خصوصی خالی است.';

COMMIT;
