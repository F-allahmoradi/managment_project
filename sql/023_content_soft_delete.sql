-- حذف نرم contents و مجوز Content/Delete برای صوت/متن اشتباه.

BEGIN;

ALTER TABLE contents
    ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

INSERT INTO permissions (name, description, resource, action) VALUES
    ('حذف محتوا', NULL, 'Content', 'Delete')
ON CONFLICT (resource, action) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'مدیر کل'
  AND p.resource = 'Content'
  AND p.action = 'Delete'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'Content' AND p.action = 'Delete'
WHERE r.name = 'مدیر پروژه'
ON CONFLICT (role_id, permission_id) DO NOTHING;

COMMIT;
