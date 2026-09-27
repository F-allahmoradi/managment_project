-- مجوز ذخیره تحلیل متن و نوع منبع content برای پیش‌نویس playground.
-- جداول عملیاتی را تغییر نمی‌دهد.

BEGIN;

INSERT INTO analysis_source_types (code, name, description, is_active) VALUES
    ('content', 'محتوا', 'جدول contents؛ پیش‌نویس متن آزاد playground', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (name, description, resource, action) VALUES
    ('ثبت تحلیل متن', NULL, 'TextAnalysis', 'Create'),
    ('مشاهده تحلیل متن', NULL, 'TextAnalysis', 'Read')
ON CONFLICT (resource, action) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'مدیر کل'
  AND p.resource = 'TextAnalysis'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'TextAnalysis'
WHERE r.name = 'مدیر پروژه'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'TextAnalysis'
  AND p.action IN ('Create', 'Read')
WHERE r.name = 'کاربر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'TextAnalysis'
WHERE r.name = 'تحلیلگر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'TextAnalysis' AND p.action = 'Read'
WHERE r.name = 'ناظر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

COMMIT;
