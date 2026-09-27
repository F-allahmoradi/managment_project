"""توضیح کامل ابزارهای پردازش زبانی برای description روی سیم پروتکل."""

_INPUT = """
مجوز لازم:
    متن آزاد مجوز Resource/Action نمی‌خواهد.
    منبع جلسه Meeting/Read و دسترسی جلسه، پیام Message/Read و عضویت گفتگو.

ورودی:
    دقیقاً یکی از این دو:
    text متن غیرخالی،
    یا source_type (meeting / message) به‌همراه source_id.
    context اختیاری: جملات قبل یا بعد برای رفع ارجاع.

طراحی:
    فقط‌خواندنی است. INSERT نیست.
    نیت و ژانر با management-ner است.
""".strip()

EXTRACT_FACTS = f"""
از متن فکت ساخت‌یافته برمی‌دارد: مقدار/درصد، شرط، تغییر، علت، وضعیت.

چرا این ابزار:
    عدد و علت جدا از نیت شکایت است. هر فکت صریح یا مستنتج از شاهد است.
    عددِ غایب در متن فقط با تفریق یا جمع منابع صریح می‌ماند.
    حدس بی‌پایه حذف می‌شود. خروجی dropped_count تعداد ادعاهای حذف‌شده است.

خروجی:
    JSON با facts، explicitness (explicit / derived / none) و fact_count.

{_INPUT}
""".strip()

EXTRACT_QUOTES = f"""
نقل‌قول مستقیم و غیرمستقیم را برمی‌دارد.

چرا این ابزار:
    گوینده پیام ممکن است سخن واحد دیگری را گزارش کند
    («رفتم واحد مالی گفت»). attributed_to و quoted_text باید
    زیررشتهٔ متن باشند.

خروجی:
    JSON با quotes و quote_count.

{_INPUT}
""".strip()

EXTRACT_FRAME = f"""
قاب مسئله را جدا از نیت برمی‌دارد: عنوان، واحد، فرآیند، محدوده.

چرا این ابزار:
    کارت بعدی جدول issues است نه برچسب complaint.
    واحد و about باید در متن باشند. title می‌تواند برچسب کوتاه باشد.
    محدوده personal / unit / organizational است.
    ذخیره با create_issue در management-crud است؛ این ابزار INSERT ندارد.
    علت‌ها فکت kind برابر cause هستند و با link_issue_cause وصل می‌شوند.
    وظیفهٔ پیشنهادی از نیت extract_intent یا از همین قاب با create_task
    ساخته و با link_issue_task وصل می‌شود. اهمیت و فوریت و شدت و اثر
    از کاتالوگ seed با تأیید انسان است؛ این ابزار حدس امتیاز ندارد.
    موضوع و موجودیت ذخیره‌شدهٔ NER با link_issue_topic و
    link_issue_entity به همان مسئله وصل می‌شوند.

خروجی:
    JSON با frame یا null.

{_INPUT}
""".strip()
