-- مجوز ثبت و مشاهده مسئله برای ابزارهای نازک CRUD.
-- جداول issues و issue_sources از قبل در اسکیما هستند.

BEGIN;

INSERT INTO permissions (name, description, resource, action) VALUES
    ('ثبت مسئله', NULL, 'Issue', 'Create'),
    ('مشاهده مسئله', NULL, 'Issue', 'Read')
ON CONFLICT (resource, action) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'مدیر کل'
  AND p.resource = 'Issue'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'Issue'
WHERE r.name = 'مدیر پروژه'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'Issue'
  AND p.action IN ('Create', 'Read')
WHERE r.name = 'کاربر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'Issue'
WHERE r.name = 'تحلیلگر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'Issue' AND p.action = 'Read'
WHERE r.name = 'ناظر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

COMMIT;
