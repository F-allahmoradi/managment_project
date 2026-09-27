-- کاتالوگ ژانر و نیت استخراج متن برای پایگاه‌های از قبل seedشده.
-- جداول عملیاتی را تغییر نمی‌دهد. INSERT تحلیل نیست.

BEGIN;

UPDATE discourse_types SET
    description = 'الزام از موضع اختیار؛ آمر و مأمور و تکلیف لازم است',
    is_active = true
WHERE code = 'order';

UPDATE discourse_types SET
    description = 'تصمیم استنادپذیر با مرجع تصویب رسمی',
    is_active = true
WHERE code = 'resolution';

UPDATE discourse_types SET
    description = 'انتخاب قطعی گرفته‌شده؛ هنوز توصیه نیست',
    is_active = true
WHERE code = 'decision';

UPDATE discourse_types SET
    description = 'طلب انجام کار بدون اعمال قدرت',
    is_active = true
WHERE code = 'request';

UPDATE discourse_types SET
    description = 'طلب دانستن؛ مطلوب عمل نیست',
    is_active = true
WHERE code = 'question';

UPDATE discourse_types SET
    description = 'ریسک نزدیک؛ اختلال رخ‌داده مسئله است',
    is_active = true
WHERE code = 'warning';

UPDATE discourse_types SET
    description = 'روش حل مسئلهٔ حاضر',
    is_active = true
WHERE code = 'solution';

UPDATE discourse_types SET
    description = 'توصیهٔ اجرایی خطاب به تصمیم‌گیر',
    is_active = true
WHERE code = 'suggestion';

UPDATE discourse_types SET
    description = 'طرح نو بدون خطاب اجرایی',
    is_active = true
WHERE code = 'idea';

UPDATE discourse_types SET
    description = 'مانع یا اختلال نیازمند رسیدگی؛ شامل مشکل',
    is_active = true
WHERE code = 'issue';

UPDATE discourse_types SET
    description = 'حاصل تمام‌شدهٔ کار یا آزمون',
    is_active = true
WHERE code = 'result';

UPDATE discourse_types SET
    description = 'بررسی با شاهد و استنتاج',
    is_active = true
WHERE code = 'analysis';

UPDATE discourse_types SET
    description = 'روشن کردن معنا نه راه‌حل',
    is_active = true
WHERE code = 'interpretation';

UPDATE discourse_types SET
    description = 'ارزیابی کار یا خروجی مشخص',
    is_active = true
WHERE code = 'feedback';

UPDATE discourse_types SET
    description = 'روایت گذشته با پیامد و درس',
    is_active = true
WHERE code = 'experience';

UPDATE discourse_types SET
    description = 'ابلاغ یک‌طرفه خبر به جمع',
    is_active = true
WHERE code = 'announcement';

UPDATE discourse_types SET
    description = 'روایت وضعیت یا وقایع؛ رخداد جدا نیست',
    is_active = true
WHERE code = 'report';

UPDATE discourse_types SET
    description = 'ثبت کوتاه بدون انتظار واکنش فوری',
    is_active = true
WHERE code = 'note';

UPDATE discourse_types SET
    description = 'پر کردن مجهول قبلی',
    is_active = true
WHERE code = 'answer';

UPDATE discourse_types SET
    description = 'فقط وقتی هیچ ژانر دیگری پر نشود',
    is_active = true
WHERE code = 'message';

UPDATE discourse_types SET
    description = 'ادغام‌شده در مسئله؛ برای استخراج فعال نیست',
    is_active = false
WHERE code = 'problem';

UPDATE discourse_types SET
    description = 'ادغام‌شده در گزارش یا نتیجه؛ برای استخراج فعال نیست',
    is_active = false
WHERE code = 'action';

UPDATE discourse_types SET
    description = 'ادغام‌شده در گزارش؛ برای استخراج فعال نیست',
    is_active = false
WHERE code = 'event';

UPDATE intents SET
    description = 'شاکی، مشتکی‌عنه، مورد اختلاف و خواسته لازم است',
    is_active = true
WHERE code = 'complaint';

UPDATE intents SET
    description = 'مخالفت با حکم یا برداشت بدون لزوماً جبران',
    is_active = true
WHERE code = 'objection';

UPDATE intents SET
    description = 'نپذیرفتن پیشنهاد یا تحویل روی میز',
    is_active = true
WHERE code = 'reject';

UPDATE intents SET
    description = 'پذیرفتن پیشنهاد یا تحویل روی میز',
    is_active = true
WHERE code = 'approve';

UPDATE intents SET
    description = 'مخاطب باید انتخاب کند نه لزوماً اجرا',
    is_active = true
WHERE code = 'request_decision';

UPDATE intents SET
    description = 'مخاطب باید کاری انجام دهد',
    is_active = true
WHERE code = 'request_action';

UPDATE intents SET
    description = 'مورد باز قبلی معطل مانده',
    is_active = true
WHERE code = 'follow_up';

UPDATE intents SET
    description = 'مخاطب باید چیزی بگوید یا بفرستد',
    is_active = true
WHERE code = 'request_info';

UPDATE intents SET
    description = 'مسئله بدون مقصرسازی و طلب جبران',
    is_active = true
WHERE code = 'report_problem';

UPDATE intents SET
    description = 'فقط دانستن؛ غرض دیگری نیست',
    is_active = true
WHERE code = 'inform';

UPDATE intents SET
    description = 'تکرار ژانر؛ برای استخراج نیت فعال نیست',
    is_active = false
WHERE code IN ('suggest', 'question', 'answer', 'warn');

COMMIT;
