-- دادن و گرفتن نقش سیستمی فقط برای مدیر کل.
-- ثبت‌نام خودش نقش «کاربر» می‌دهد. مدیر سازمان را مدیر کل می‌سازد.

BEGIN;

INSERT INTO permissions (name, description, resource, action) VALUES
    ('دادن نقش کاربر', 'فقط مدیر کل مدیر سازمان می‌سازد', 'UserRole', 'Create'),
    ('گرفتن نقش کاربر', 'فقط مدیر کل نقش سیستمی را می‌گیرد', 'UserRole', 'Delete'),
    ('مشاهده نقش کاربر', 'فقط مدیر کل اتصال نقش را می‌بیند', 'UserRole', 'Read')
ON CONFLICT (resource, action) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'UserRole'
WHERE r.name = 'مدیر کل'
ON CONFLICT (role_id, permission_id) DO NOTHING;

COMMIT;
