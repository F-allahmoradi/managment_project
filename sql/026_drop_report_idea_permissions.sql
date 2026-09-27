-- مجوزهای جداول حذف‌شدهٔ reports و ideas_experiences را برمی‌دارد.

BEGIN;

DELETE FROM role_permissions rp
USING permissions p
WHERE rp.permission_id = p.id
  AND p.resource IN ('Report', 'IdeaExperience');

DELETE FROM permissions
WHERE resource IN ('Report', 'IdeaExperience');

COMMIT;
