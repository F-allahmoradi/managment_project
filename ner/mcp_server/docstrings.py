"""توضیح کامل ابزارهای استخراج برای description روی سیم پروتکل."""

_INPUT = """
مجوز لازم:
    متن آزاد مجوز Resource/Action نمی‌خواهد.
    منبع جلسه Meeting/Read و دسترسی جلسه، پیام Message/Read و عضویت گفتگو.

ورودی:
    دقیقاً یکی از این دو:
    text متن غیرخالی،
    یا source_type (meeting / message) به‌همراه source_id.

طراحی:
    فقط‌خواندنی است. INSERT نیست.
    ذخیره با save_text_analysis در management-crud است؛ وضعیت پیشنهادی.
""".strip()

EXTRACT_ENTITIES = f"""
از متن گزارش، جلسه یا پیام فقط موجودیت نام‌دار استخراج می‌کند:
PERSON / UNIT / ORG / PLACE / OBJECT / PROJECT / TASK / TIME / ROLE.

چرا این ابزار:
    لایه span باید فرد، واحد، سازمان، مکان، شیء، پروژه، وظیفه، زمان و
    نقش را با شاهد دقیق دربیاورد. موضوع و احساس ابزار جدا هستند.
    برای TIME تاریخ از شاهد فارسی به occurred_at تبدیل می‌شود.

خروجی:
    JSON با mentions و entities.
    برای TIME در صورت تبدیل، occurred_at هم می‌آید.

{_INPUT}
""".strip()

EXTRACT_KEYWORDS = f"""
از متن فقط کلمه و عبارت کلیدی آزاد استخراج می‌کند.

چرا این ابزار:
    عبارت ۱ تا ۵ کلمه‌ای موضوعی است، نه نام فرد و نه نوع موجودیت.
    خروجی برای ذخیره در keywords و keyword_mentions آماده است ولی INSERT در NER نیست.

خروجی:
    JSON با keywords و شاهد داخل متن.

{_INPUT}
""".strip()

EXTRACT_TOPICS = f"""
متن را روی درخت سلسله‌مراتبی topics طبقه‌بندی می‌کند.

چرا این ابزار:
    اول حوزه از کاتالوگ بسته است (مالی → پرداخت → تأخیر پرداخت).
    اگر هیچ گره نخورد موضوع واقعی متن کشف می‌شود (discovered)
    و با نام فارسی برمی‌گردد؛ خالی نمی‌ماند و به management پرتاب نمی‌شود.

خروجی:
    JSON با topics؛ یک موضوع is_primary دارد. موضوع نو discovered است.

{_INPUT}
""".strip()

EXTRACT_SENTIMENT = f"""
قطبیت کل متن و هیجان را جدا از موجودیت برمی‌دارد.

چرا این ابزار:
    احساس طبقه‌بندی است نه ذکر. جدول هدف text_analysis_sentiments
    و text_analysis_emotions است. برای کنایه قطبیت مقصود را بزن نه ظاهر.
    اگر intended_meaning از extract_rhetoric آمده باشد همان را بده.
    INSERT نمی‌شود.

خروجی:
    JSON با sentiment (حداکثر یکی) و emotions.

{_INPUT}
""".strip()

EXTRACT_DISCOURSE = f"""
ژانر / نوع پیام را جدا از موجودیت و نیت برمی‌دارد.

چرا این ابزار:
    شکل کنش است نه غرض گوینده و نه موضوع حوزه. کاتالوگ
    discourse_types است (مسئله، درخواست، تصمیم، مصوبه، ...).
    نقش‌های اجباری هر قالب باید از متن پر شود. اگر هیچ قالبی
    نخورد ولی کنش ساخت‌یافته بود، نوع نو با ساختار خودش برمی‌گردد
    و به زور در قالب موجود نمی‌رود. کنایه ژانر جدا نیست.
    intended_meaning اختیاری از extract_rhetoric.
    جدول هدف text_analysis_discourses است. INSERT نیست.

خروجی:
    JSON با discourses؛ یک ژانر is_primary دارد.
    نوع کشف‌شده discovered و type_schema دارد.

{_INPUT}
""".strip()

EXTRACT_INTENT = f"""
نیت گوینده و مسیر رسیدگی را جدا از ژانر برمی‌دارد.

چرا این ابزار:
    یک مسئله می‌تواند گزارش مشکل، درخواست اقدام، پیگیری یا شکایت
    باشد. کاتالوگ بسته intents است. سؤال و پیشنهاد و هشدار اینجا
    نیستند چون ژانرند. کنایه و طنز نیت جدا نیستند.
    intended_meaning اختیاری از extract_rhetoric.
    جدول هدف text_analysis_intents است.
    INSERT نمی‌شود.

خروجی:
    JSON با intents؛ یک نیت is_primary دارد.

{_INPUT}
""".strip()

EXTRACT_RHETORIC = f"""
صنعت بیان و معنای مقصود را جدا از ژانر و نیت برمی‌دارد.

چرا این ابزار:
    کنایه، طعنه، طنز، استعاره، تشبیه، اغراق، کم‌گویی و سؤال بلاغی
    مسیر رسیدگی نیستند. اعتراض کنایه‌ای همچنان اعتراض است.
    کاتالوگ بسته rhetoric_types است. معنای مقصود بازنویسیٔ صریح
    غرض است تا نیت و ژانر و احساس روی آن اجرا شوند.
    جدول هدف text_analysis_rhetorics است. INSERT نمی‌شود.

خروجی:
    JSON با rhetorics، یک صنعت is_primary، و intended_meaning.

{_INPUT}
""".strip()
