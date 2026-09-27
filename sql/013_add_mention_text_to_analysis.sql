-- شاهد کوتاه استخراج‌شده روی موضوع، احساس، ژانر و نیت.
-- ردیف‌های قبلی خالی می‌مانند. INSERT تحلیل نیست.

BEGIN;

ALTER TABLE text_analysis_topics
    ADD COLUMN IF NOT EXISTS mention_text character varying(300) NOT NULL DEFAULT '';

ALTER TABLE text_analysis_sentiments
    ADD COLUMN IF NOT EXISTS mention_text character varying(300) NOT NULL DEFAULT '';

ALTER TABLE text_analysis_emotions
    ADD COLUMN IF NOT EXISTS mention_text character varying(300) NOT NULL DEFAULT '';

ALTER TABLE text_analysis_discourses
    ADD COLUMN IF NOT EXISTS mention_text character varying(300) NOT NULL DEFAULT '';

ALTER TABLE text_analysis_intents
    ADD COLUMN IF NOT EXISTS mention_text character varying(300) NOT NULL DEFAULT '';

COMMIT;
