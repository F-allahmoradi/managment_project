-- داده‌های پایهٔ lookup. کاربر نمونه ساخته نمی‌شود.

BEGIN;

INSERT INTO roles (name, description, is_system_role, is_active) VALUES
    ('مدیر کل', 'دسترسی کامل به سامانه', true, true),
    ('مدیر پروژه', 'مدیریت پروژه، اعضا، وظایف و گزارش‌ها', true, true),
    ('کاربر', 'کاربر عادی سامانه', true, true),
    ('ناظر', 'مشاهده و نظارت بدون تغییر عملیاتی', false, true),
    ('تحلیلگر', 'گزارش و تحلیل عملکرد و پروژه', false, true),
    ('مسئول مالی', 'حساب‌ها و تراکنش‌های مالی', false, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description, resource, action) VALUES
    ('ایجاد کاربر', NULL, 'User', 'Create'),
    ('مشاهده کاربر', NULL, 'User', 'Read'),
    ('ویرایش کاربر', NULL, 'User', 'Update'),
    ('حذف کاربر', NULL, 'User', 'Delete'),
    ('ایجاد پروژه', NULL, 'Project', 'Create'),
    ('مشاهده پروژه', NULL, 'Project', 'Read'),
    ('ویرایش پروژه', NULL, 'Project', 'Update'),
    ('حذف پروژه', NULL, 'Project', 'Delete'),
    ('مشاهده اعضا', NULL, 'ProjectMember', 'Read'),
    ('ویرایش اعضا', NULL, 'ProjectMember', 'Update'),
    ('ایجاد وظیفه', NULL, 'Task', 'Create'),
    ('مشاهده وظیفه', NULL, 'Task', 'Read'),
    ('ویرایش وظیفه', NULL, 'Task', 'Update'),
    ('حذف وظیفه', NULL, 'Task', 'Delete'),
    ('ایجاد پیگیری وظیفه', NULL, 'TaskFollowUp', 'Create'),
    ('مشاهده پیگیری وظیفه', NULL, 'TaskFollowUp', 'Read'),
    ('ارسال پیام', NULL, 'Message', 'Create'),
    ('مشاهده پیام', NULL, 'Message', 'Read'),
    ('ایجاد یادآوری', NULL, 'Reminder', 'Create'),
    ('مشاهده یادآوری', NULL, 'Reminder', 'Read'),
    ('ارسال یادآوری', NULL, 'Reminder', 'Dispatch'),
    ('ایجاد جلسه', NULL, 'Meeting', 'Create'),
    ('مشاهده جلسه', NULL, 'Meeting', 'Read'),
    ('ویرایش جلسه', NULL, 'Meeting', 'Update'),
    ('حذف جلسه', NULL, 'Meeting', 'Delete'),
    ('ایجاد برنامه جلسه', NULL, 'MeetingSchedule', 'Create'),
    ('مشاهده برنامه جلسه', NULL, 'MeetingSchedule', 'Read'),
    ('ویرایش برنامه جلسه', NULL, 'MeetingSchedule', 'Update'),
    ('حذف برنامه جلسه', NULL, 'MeetingSchedule', 'Delete'),
    ('همگام‌سازی جلسه', NULL, 'MeetingSync', 'Execute'),
    ('ایجاد محتوا', NULL, 'Content', 'Create'),
    ('مشاهده محتوا', NULL, 'Content', 'Read'),
    ('حذف محتوا', NULL, 'Content', 'Delete'),
    ('مشاهده مالی', NULL, 'Finance', 'Read'),
    ('ثبت تراکنش مالی', NULL, 'Finance', 'Create'),
    ('ثبت تشویق و تنبیه', NULL, 'Performance', 'Create'),
    ('مشاهده عملکرد', NULL, 'Performance', 'Read'),
    ('مشاهده ممیزی', NULL, 'AuditLog', 'Read'),
    ('ثبت تحلیل متن', NULL, 'TextAnalysis', 'Create'),
    ('مشاهده تحلیل متن', NULL, 'TextAnalysis', 'Read'),
    ('ثبت مسئله', NULL, 'Issue', 'Create'),
    ('مشاهده مسئله', NULL, 'Issue', 'Read')
ON CONFLICT (resource, action) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'مدیر کل'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource IN (
    'Project', 'ProjectMember', 'Task', 'TaskFollowUp',
    'Message', 'Reminder',
    'Meeting', 'MeetingSchedule', 'MeetingSync', 'Performance', 'Content',
    'TextAnalysis', 'Issue'
)
WHERE r.name = 'مدیر پروژه'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.action = 'Read'
  AND p.resource IN (
      'Project', 'ProjectMember', 'Task', 'TaskFollowUp',
      'Message', 'Reminder',
      'Meeting', 'MeetingSchedule', 'TextAnalysis', 'Issue'
  )
WHERE r.name = 'کاربر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON (
    (p.resource = 'Task' AND p.action IN ('Create', 'Update'))
    OR (p.resource = 'Message' AND p.action = 'Create')
    OR (p.resource = 'Meeting' AND p.action = 'Read')
    OR (p.resource = 'TextAnalysis' AND p.action = 'Create')
    OR (p.resource = 'Issue' AND p.action = 'Create')
)
WHERE r.name = 'کاربر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.action = 'Read'
WHERE r.name = 'ناظر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.action = 'Read'
  AND p.resource IN (
      'Project', 'Task', 'TaskFollowUp',
      'Performance', 'Finance', 'AuditLog',
      'TextAnalysis', 'Issue'
  )
WHERE r.name = 'تحلیلگر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'TextAnalysis' AND p.action = 'Create'
WHERE r.name = 'تحلیلگر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'Issue' AND p.action = 'Create'
WHERE r.name = 'تحلیلگر'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.resource = 'Finance'
WHERE r.name = 'مسئول مالی'
ON CONFLICT (role_id, permission_id) DO NOTHING;

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

INSERT INTO project_types (name, description, is_active) VALUES
    ('نرم‌افزاری', NULL, true),
    ('تحقیقاتی', NULL, true),
    ('فرهنگی', NULL, true),
    ('اجرایی', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO project_statuses (name, description, is_active) VALUES
    ('در انتظار شروع', NULL, true),
    ('در حال اجرا', NULL, true),
    ('متوقف', NULL, true),
    ('تکمیل شده', NULL, true),
    ('لغو شده', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO project_roles (name, description, is_active) VALUES
    ('مدیر پروژه', 'مدیر همان پروژه', true),
    ('عضو', 'عضو اجرایی پروژه', true),
    ('ناظر', 'ناظر پروژه', true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO task_statuses (name, description, is_active) VALUES
    ('شروع نشده', NULL, true),
    ('در حال انجام', NULL, true),
    ('در انتظار', NULL, true),
    ('تکمیل شده', NULL, true),
    ('لغو شده', NULL, true),
    ('نیازمند اصلاح', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO task_priorities (name, level, is_active) VALUES
    ('کم', 1, true),
    ('متوسط', 2, true),
    ('زیاد', 3, true),
    ('فوری', 4, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO task_importances (name, level, is_active) VALUES
    ('کم', 1, true),
    ('متوسط', 2, true),
    ('زیاد', 3, true),
    ('حیاتی', 4, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO follow_up_types (name, description, is_active) VALUES
    ('تماس', NULL, true),
    ('پیام', NULL, true),
    ('جلسه', NULL, true),
    ('یادآوری', NULL, true),
    ('پیگیری حضوری', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO task_follow_up_statuses (name, description, is_active) VALUES
    ('منتظر پاسخ', NULL, true),
    ('پاسخ داده', NULL, true),
    ('بسته شده', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO meeting_types (name, description, is_active) VALUES
    ('جلسه تیم', 'جلسه دوره‌ای با اعضای پروژه', true),
    ('مذاکره خارجی', 'جلسه با افراد خارج از سامانه', true),
    ('مذاکره حقوقی', 'مذاکره قبل از شکایت یا settlement', true),
    ('مذاکره مدیران', 'مذاکره اولیه بین مدیران بدون پروژه', true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO meeting_statuses (name, description, is_active) VALUES
    ('برنامه‌ریزی شده', NULL, true),
    ('برگزار شده', NULL, true),
    ('لغو شده', NULL, true),
    ('ضبط شده', NULL, true),
    ('همگام‌سازی شده', NULL, true)
ON CONFLICT (name) DO NOTHING;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'content_kinds'
    ) THEN
        INSERT INTO content_kinds (code, name, description, is_active) VALUES
            ('TEXT', 'متن', 'متن ساده یا caption', true),
            ('VOICE', 'صوت', 'پیام صوتی / ویس', true),
            ('IMAGE', 'تصویر', 'عکس', true),
            ('FILE', 'فایل', 'سند، PDF، Excel و...', true)
        ON CONFLICT (code) DO NOTHING;
    END IF;
END $$;

INSERT INTO chat_types (name) VALUES
    ('گفتگوی خصوصی'),
    ('گفتگوی تیم'),
    ('گفتگوی پروژه')
ON CONFLICT (name) DO NOTHING;

INSERT INTO reminder_types (name, description, is_active) VALUES
    ('یک‌باره', NULL, true),
    ('دوره‌ای', NULL, true),
    ('پیگیری', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO reminder_frequencies (name, description, is_active) VALUES
    ('یک‌باره', NULL, true),
    ('روزانه', NULL, true),
    ('هفتگی', NULL, true),
    ('ماهانه', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO reminder_statuses (name, description, is_active) VALUES
    ('فعال', NULL, true),
    ('تکمیل شده', NULL, true),
    ('متوقف', NULL, true),
    ('لغو شده', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO follow_up_state_statuses (name, description, is_active) VALUES
    ('در انتظار', 'منتظر پاسخ گیرنده', true),
    ('پاسخ داده', NULL, true),
    ('سقف تکرار تمام', NULL, true),
    ('متوقف', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_types (name, description, is_active) VALUES
    ('وظیفه جدید', NULL, true),
    ('گزارش جدید', NULL, true),
    ('یادآوری', NULL, true),
    ('تغییر وضعیت Task', NULL, true),
    ('افزوده شدن به پروژه', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO financial_account_types (name, description, is_active) VALUES
    ('بودجه پروژه', NULL, true),
    ('صندوق پروژه', NULL, true),
    ('حساب سازمان', NULL, true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO transaction_types (name) VALUES
    ('دریافت'),
    ('پرداخت'),
    ('انتقال'),
    ('بازگشت وجه'),
    ('پاداش'),
    ('جریمه')
ON CONFLICT (name) DO NOTHING;

INSERT INTO financial_categories (name, description) VALUES
    ('حقوق', NULL),
    ('تجهیزات', NULL),
    ('تبلیغات', NULL),
    ('حمل‌ونقل', NULL),
    ('پذیرایی', NULL),
    ('آموزش', NULL)
ON CONFLICT (name) DO NOTHING;

INSERT INTO performance_action_types (name, category) VALUES
    ('پاداش نقدی', 'REWARD'),
    ('امتیاز مثبت', 'REWARD'),
    ('تقدیر', 'REWARD'),
    ('مرخصی تشویقی', 'REWARD'),
    ('اخطار', 'PENALTY'),
    ('امتیاز منفی', 'PENALTY'),
    ('کسر پاداش', 'PENALTY'),
    ('جریمه', 'PENALTY')
ON CONFLICT (name) DO NOTHING;

INSERT INTO analysis_source_types (code, name, description, is_active) VALUES
    ('meeting', 'جلسه', 'جدول meetings', true),
    ('message', 'پیام', 'جدول messages', true),
    ('task', 'وظیفه', 'جدول tasks', true),
    ('task_follow_up', 'پیگیری وظیفه', 'جدول task_follow_ups', true),
    ('project_document', 'مستند پروژه', 'جدول project_documents', true),
    ('content', 'محتوا', 'جدول contents؛ پیش‌نویس متن آزاد playground', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO discourse_types (code, name, description, is_active) VALUES
    ('order', 'دستور', 'الزام از موضع اختیار؛ آمر و مأمور و تکلیف لازم است', true),
    ('resolution', 'مصوبه', 'تصمیم استنادپذیر با مرجع تصویب رسمی', true),
    ('decision', 'تصمیم', 'انتخاب قطعی گرفته‌شده؛ هنوز توصیه نیست', true),
    ('request', 'درخواست', 'طلب انجام کار بدون اعمال قدرت', true),
    ('question', 'سؤال', 'طلب دانستن؛ مطلوب عمل نیست', true),
    ('warning', 'هشدار', 'ریسک نزدیک؛ اختلال رخ‌داده مسئله است', true),
    ('solution', 'راهکار', 'روش حل مسئلهٔ حاضر', true),
    ('suggestion', 'پیشنهاد', 'توصیهٔ اجرایی خطاب به تصمیم‌گیر', true),
    ('idea', 'ایده', 'طرح نو بدون خطاب اجرایی', true),
    ('issue', 'مسئله', 'مانع یا اختلال نیازمند رسیدگی؛ شامل مشکل', true),
    ('result', 'نتیجه', 'حاصل تمام‌شدهٔ کار یا آزمون', true),
    ('analysis', 'تحلیل', 'بررسی با شاهد و استنتاج', true),
    ('interpretation', 'توضیح و تفسیر', 'روشن کردن معنا نه راه‌حل', true),
    ('feedback', 'بازخورد', 'ارزیابی کار یا خروجی مشخص', true),
    ('experience', 'تجربه', 'روایت گذشته با پیامد و درس', true),
    ('announcement', 'اطلاعیه', 'ابلاغ یک‌طرفه خبر به جمع', true),
    ('report', 'گزارش', 'روایت وضعیت یا وقایع؛ رخداد جدا نیست', true),
    ('note', 'یادداشت', 'ثبت کوتاه بدون انتظار واکنش فوری', true),
    ('answer', 'پاسخ', 'پر کردن مجهول قبلی', true),
    ('message', 'پیام', 'فقط وقتی هیچ ژانر دیگری پر نشود', true),
    ('problem', 'مشکل', 'ادغام‌شده در مسئله؛ برای استخراج فعال نیست', false),
    ('action', 'اقدام', 'ادغام‌شده در گزارش یا نتیجه؛ برای استخراج فعال نیست', false),
    ('event', 'رخداد', 'ادغام‌شده در گزارش؛ برای استخراج فعال نیست', false)
ON CONFLICT (code) DO NOTHING;

INSERT INTO intents (code, name, description, is_active) VALUES
    ('complaint', 'شکایت', 'شاکی، مشتکی‌عنه، مورد اختلاف و خواسته لازم است', true),
    ('objection', 'اعتراض', 'مخالفت با حکم یا برداشت بدون لزوماً جبران', true),
    ('reject', 'رد', 'نپذیرفتن پیشنهاد یا تحویل روی میز', true),
    ('approve', 'تأیید', 'پذیرفتن پیشنهاد یا تحویل روی میز', true),
    ('request_decision', 'درخواست تصمیم', 'مخاطب باید انتخاب کند نه لزوماً اجرا', true),
    ('request_action', 'درخواست اقدام', 'مخاطب باید کاری انجام دهد', true),
    ('follow_up', 'پیگیری', 'مورد باز قبلی معطل مانده', true),
    ('request_info', 'درخواست اطلاعات', 'مخاطب باید چیزی بگوید یا بفرستد', true),
    ('report_problem', 'گزارش مشکل', 'مسئله بدون مقصرسازی و طلب جبران', true),
    ('inform', 'اطلاع‌رسانی', 'فقط دانستن؛ غرض دیگری نیست', true),
    ('suggest', 'پیشنهاد', 'تکرار ژانر؛ برای استخراج نیت فعال نیست', false),
    ('question', 'سؤال', 'تکرار ژانر؛ برای استخراج نیت فعال نیست', false),
    ('answer', 'پاسخ', 'تکرار ژانر؛ برای استخراج نیت فعال نیست', false),
    ('warn', 'هشدار', 'تکرار ژانر؛ برای استخراج نیت فعال نیست', false)
ON CONFLICT (code) DO NOTHING;

INSERT INTO rhetoric_types (code, name, description, is_active) VALUES
    ('sarcasm', 'طعنه', 'کنایهٔ نیش‌دار خطاب به فرد یا واحد', true),
    ('irony', 'کنایه', 'معنا خلاف ظاهر است', true),
    ('rhetorical_question', 'سؤال بلاغی', 'ظاهر سؤال، غرض اعتراض یا فشار است', true),
    ('humor', 'طنز', 'شوخی؛ ممکن است اعتراض را بپوشاند', true),
    ('metaphor', 'استعاره', 'چیزی به‌جای چیز دیگر بدون ادات تشبیه', true),
    ('simile', 'تشبیه', 'مانند یا مثل برای رساندن معنا', true),
    ('hyperbole', 'اغراق', 'بزرگ‌نمایی برای فشار', true),
    ('understatement', 'کم‌گویی', 'کوچک‌نمایی برای اعتراض', true),
    ('literal', 'صریح', 'فقط وقتی هیچ صنعت دیگری پر نشود', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO fact_kinds (code, name, description, is_active) VALUES
    ('quantity', 'مقدار', 'عدد یا درصد که در متن آمده یا از عددهای صریح قابل محاسبه است', true),
    ('condition', 'شرط', 'قیدی که وقوع یا پذیرش به آن وابسته است', true),
    ('change', 'تغییر', 'فرق وضعیت فعلی با قبل؛ کاهش، افزایش، جایگزینی', true),
    ('cause', 'علت', 'نسبت علت و معلول که شاهدش در متن باشد', true),
    ('status', 'وضعیت', 'وضع فعلی کار یا واحد، بدون عدد الزامی', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO fact_units (code, name, description, is_active) VALUES
    ('percent', 'درصد', NULL, true),
    ('amount', 'مبلغ', NULL, true),
    ('count', 'تعداد', NULL, true),
    ('duration', 'مدت', NULL, true),
    ('ratio', 'نسبت', NULL, true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO fact_quantity_roles (code, name, description, is_active) VALUES
    ('total', 'کل', NULL, true),
    ('part', 'جزء', NULL, true),
    ('remainder', 'باقی‌مانده', NULL, true),
    ('none', 'بدون نقش', NULL, true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO fact_groundings (code, name, description, is_active) VALUES
    ('explicit', 'صریح', 'خودِ مقدار یا ادعا زیررشتهٔ متن است', true),
    ('derived', 'مستنتج از شاهد', 'مقدار در متن نیست ولی از فکت‌های صریح با عمل مجاز به‌دست می‌آید', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO fact_derivations (code, name, description, is_active) VALUES
    ('subtract', 'تفریق', 'مقدار = منبع اول منهای مجموع بقیه', true),
    ('add', 'جمع', 'مقدار = مجموع منابع', true),
    ('remainder', 'باقی‌مانده', 'مقدار = کل منهای اجزا', true),
    ('from_evidence', 'از شاهد متن', 'استنتاج غیرعددی؛ همهٔ evidence_texts باید در متن باشند', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO quote_modes (code, name, description, is_active) VALUES
    ('direct', 'مستقیم', 'نقل قول با علامت یا بازنویسی نزدیک «گفت که …»', true),
    ('indirect', 'غیرمستقیم', 'گزارش سخن دیگری بدون لزوماً گیومه؛ «رفتم واحد مالی گفت»', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO entity_types (code, name, is_active) VALUES
    ('PERSON', 'فرد', true),
    ('UNIT', 'واحد', true),
    ('ORG', 'سازمان', true),
    ('PLACE', 'مکان', true),
    ('OBJECT', 'شیء', true),
    ('PROJECT', 'پروژه', true),
    ('TASK', 'وظیفه', true),
    ('TIME', 'زمان', true),
    ('ROLE', 'نقش', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO entity_statuses (code, name, is_active) VALUES
    ('candidate', 'پیشنهادی', true),
    ('confirmed', 'تأییدشده', true),
    ('rejected', 'ردشده', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO relation_types (code, name, is_active) VALUES
    ('causes', 'علت', true),
    ('responsible_for', 'مسئولیت', true),
    ('impacts', 'پیامد', true),
    ('depends_on', 'وابستگی', true),
    ('contradicts', 'تناقض', true),
    ('related_to', 'مرتبط', true),
    ('assigned_to', 'واگذاری', true),
    ('occurred_at', 'زمان وقوع', true),
    ('part_of', 'جزء', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO polarities (code, name, is_active) VALUES
    ('positive', 'مثبت', true),
    ('negative', 'منفی', true),
    ('neutral', 'خنثی', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO emotions (code, name, is_active) VALUES
    ('frustration', 'خستگی و نارضایتی', true),
    ('anger', 'خشم', true),
    ('worry', 'نگرانی', true),
    ('satisfaction', 'رضایت', true),
    ('confidence', 'اطمینان', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO intensity_levels (code, name, level, is_active) VALUES
    ('low', 'کم', 1, true),
    ('medium', 'متوسط', 2, true),
    ('high', 'زیاد', 3, true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO severity_levels (code, name, level, is_active) VALUES
    ('low', 'کم', 1, true),
    ('medium', 'متوسط', 2, true),
    ('high', 'زیاد', 3, true),
    ('critical', 'بحرانی', 4, true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO issue_statuses (code, name, is_active) VALUES
    ('new', 'جدید', true),
    ('open', 'باز', true),
    ('reviewing', 'در حال بررسی', true),
    ('waiting', 'در انتظار', true),
    ('referred', 'ارجاع شده', true),
    ('in_progress', 'در حال انجام', true),
    ('done', 'انجام شده', true),
    ('resolved', 'حل شده', true),
    ('closed', 'بسته شده', true),
    ('cancelled', 'لغو شده', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO cause_levels (code, name, level, is_active) VALUES
    ('cause', 'علت', 1, true),
    ('root_cause', 'ریشه', 2, true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO issue_entity_roles (code, name, is_active) VALUES
    ('responsible', 'مسئول', true),
    ('affected', 'متأثر', true),
    ('mentioned', 'ذکرشده', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO impact_types (code, name, is_active) VALUES
    ('time', 'زمان', true),
    ('cost', 'هزینه', true),
    ('budget', 'بودجه', true),
    ('quality', 'کیفیت', true),
    ('sales', 'فروش', true),
    ('customer', 'مشتری', true),
    ('revenue', 'درآمد', true),
    ('hr', 'منابع انسانی', true),
    ('goal', 'اهداف پروژه', true),
    ('risk', 'ریسک', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO analysis_output_types (code, name, is_active) VALUES
    ('task', 'وظیفه', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO topics (code, name, level, is_active) VALUES
    ('finance', 'مالی', 1, true),
    ('tech', 'فنی', 1, true),
    ('sales', 'فروش', 1, true),
    ('marketing', 'بازاریابی', 1, true),
    ('procurement', 'تدارکات', 1, true),
    ('hr', 'منابع انسانی', 1, true),
    ('legal', 'حقوقی', 1, true),
    ('management', 'هماهنگی و مدیریت', 1, true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO topics (parent_id, code, name, level, is_active)
SELECT id, 'finance.payment', 'پرداخت', 2, true
FROM topics WHERE code = 'finance'
ON CONFLICT (code) DO NOTHING;

INSERT INTO topics (parent_id, code, name, level, is_active)
SELECT id, 'finance.payment.delay', 'تأخیر پرداخت', 3, true
FROM topics WHERE code = 'finance.payment'
ON CONFLICT (code) DO NOTHING;

INSERT INTO topics (parent_id, code, name, level, is_active)
SELECT id, 'tech.software', 'نرم‌افزار', 2, true
FROM topics WHERE code = 'tech'
ON CONFLICT (code) DO NOTHING;

INSERT INTO topics (parent_id, code, name, level, is_active)
SELECT id, 'tech.hardware', 'سخت‌افزار', 2, true
FROM topics WHERE code = 'tech'
ON CONFLICT (code) DO NOTHING;

INSERT INTO topics (parent_id, code, name, level, is_active)
SELECT id, 'tech.test', 'تست', 2, true
FROM topics WHERE code = 'tech'
ON CONFLICT (code) DO NOTHING;

INSERT INTO topics (parent_id, code, name, level, is_active)
SELECT id, 'tech.software.auth', 'احراز هویت', 3, true
FROM topics WHERE code = 'tech.software'
ON CONFLICT (code) DO NOTHING;

COMMIT;
