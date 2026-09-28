#!/bin/bash
# فقط روی volume خالی اجرا می‌شود (docker-entrypoint-initdb.d).
# ترتیب صریح است تا پیشوند تکراری مثل 003_ فایل‌ها را جابه‌جا نکند.

set -euo pipefail

SQL_DIR="${SQL_DIR:-/sql}"
files=(
  001_schema.sql
  002_seed.sql
  003_api_sessions.sql
  003_meetings.sql
  003_add_task_importance.sql
  004_meetings_end_time.sql
  004_add_task_importance_percent.sql
  005_add_task_items.sql
  006_task_items_assignee_guard.sql
  007_add_task_item_dates_and_reminders.sql
  008_add_project_documents_and_contents.sql
  009_add_idea_experience_decision.sql
  010_add_text_analysis.sql
  011_text_analysis_crud.sql
  012_speech_act_catalog.sql
  013_add_mention_text_to_analysis.sql
  014_add_intent_slots_and_embeddings.sql
  015_pgvector_hnsw.sql
  016_discovered_discourse_types.sql
  017_add_rhetoric_types.sql
  018_add_issue_crud.sql
  019_add_text_analysis_facts.sql
  020_add_text_analysis_quotes.sql
  021_soft_delete_columns.sql
  022_add_text_analysis_keywords.sql
  023_content_soft_delete.sql
  024_keywords_and_source_lineage.sql
  025_message_task_drop_manual_genres.sql
  026_drop_report_idea_permissions.sql
  027_private_chat_messages.sql
  028_user_role_admin_only.sql
  029_optional_message_task.sql
)

for name in "${files[@]}"; do
  path="${SQL_DIR}/${name}"
  if [ ! -f "${path}" ]; then
    echo "SQL file missing: ${path}" >&2
    exit 1
  fi
  echo "Applying ${name}"
  psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" -f "${path}"
done
