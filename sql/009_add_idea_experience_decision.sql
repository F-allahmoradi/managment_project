-- برای پایگاه‌هایی که قبل از افزودن نوع «تصمیم» به idea_experience_types ساخته شده‌اند.
-- روی نصب تازه لازم نیست؛ 002_seed.sql از قبل این ردیف را دارد.

BEGIN;

INSERT INTO idea_experience_types (name, description, is_active) VALUES
    ('تصمیم', 'تصمیم گرفته‌شده در جلسه', true)
ON CONFLICT (name) DO NOTHING;

COMMIT;
