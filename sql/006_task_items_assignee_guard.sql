-- فقط assignee تسک اجازه INSERT/UPDATE/DELETE روی task_items دارد.

BEGIN;

CREATE OR REPLACE FUNCTION app_current_user_id()
RETURNS integer
LANGUAGE sql
STABLE
AS $$
    SELECT NULLIF(current_setting('app.current_user_id', true), '')::integer;
$$;

COMMENT ON FUNCTION app_current_user_id IS
    'شناسه کاربر جاری سشن؛ اپ قبل از هر درخواست SET LOCAL app.current_user_id = ''...'' می‌زند.';

CREATE OR REPLACE FUNCTION task_items_enforce_assignee()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_assignee integer;
    v_parent_task_id integer;
    v_current_user integer;
BEGIN
    IF current_setting('app.enforce_task_items_assignee', true) = 'false' THEN
        RETURN COALESCE(NEW, OLD);
    END IF;

    v_current_user := app_current_user_id();
    IF v_current_user IS NULL THEN
        RAISE EXCEPTION 'app.current_user_id must be set before changing task_items';
    END IF;

    SELECT assigned_to_user_id INTO v_assignee
    FROM tasks
    WHERE id = COALESCE(NEW.task_id, OLD.task_id);

    IF v_assignee IS NULL THEN
        RAISE EXCEPTION 'Task has no assignee; task_items cannot be changed';
    END IF;

    IF v_current_user IS DISTINCT FROM v_assignee THEN
        RAISE EXCEPTION 'Only task assignee (user_id %) may change task_items', v_assignee;
    END IF;

    IF TG_OP = 'INSERT' THEN
        IF NEW.created_by_user_id IS DISTINCT FROM v_assignee THEN
            RAISE EXCEPTION 'created_by_user_id must equal task assignee';
        END IF;
        IF NEW.parent_item_id IS NOT NULL THEN
            SELECT task_id INTO v_parent_task_id
            FROM task_items
            WHERE id = NEW.parent_item_id;
            IF v_parent_task_id IS DISTINCT FROM NEW.task_id THEN
                RAISE EXCEPTION 'parent_item_id must belong to the same task';
            END IF;
        END IF;
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF NEW.task_id IS DISTINCT FROM OLD.task_id THEN
            RAISE EXCEPTION 'task_id cannot be changed';
        END IF;
        IF NEW.created_by_user_id IS DISTINCT FROM OLD.created_by_user_id THEN
            RAISE EXCEPTION 'created_by_user_id cannot be changed';
        END IF;
        IF NEW.is_completed THEN
            IF NEW.completed_by_user_id IS DISTINCT FROM v_assignee THEN
                RAISE EXCEPTION 'completed_by_user_id must equal task assignee when checking off';
            END IF;
            IF NEW.completed_at IS NULL THEN
                NEW.completed_at := CURRENT_TIMESTAMP;
            END IF;
        ELSE
            NEW.completed_at := NULL;
            NEW.completed_by_user_id := NULL;
        END IF;
        NEW.updated_at := CURRENT_TIMESTAMP;
        RETURN NEW;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS task_items_enforce_assignee_trg ON task_items;

CREATE TRIGGER task_items_enforce_assignee_trg
    BEFORE INSERT OR UPDATE OR DELETE ON task_items
    FOR EACH ROW
    EXECUTE FUNCTION task_items_enforce_assignee();

COMMENT ON TABLE task_items IS
    'جزئیات و زیرکارهای یک Task: تقسیم پلکانی، تیک زدن. فقط assigned_to_user_id می‌تواند بسازد/ویرایش/تیک بزند.';

COMMIT;
