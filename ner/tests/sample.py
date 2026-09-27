"""نمونه طلایی برای سنجش دقت استخراج موجودیت."""

SAMPLE_TEXT = """
گزارش پیشرفت پروژهٔ پل رودخانه — ۱۷ شهریور ۱۴۰۴

صبح در کارگاه جنوبی، خانم سارا احمدی مدیر پروژه گفت واحد مالی شرکت پارس‌سازه هنوز تسک «پرداخت پیمانکار فاز ۲» را نبسته است. نقش مسئول مالی با آقای رضا کریمی است. سرور پشتیبان دیشب قطع شد و تا چهارشنبه ۲۵ شهریور ۱۴۰۴ ساعت ۱۶ باید بالا بیاید. پیمانکار هم درخواست کرده جرثقیل موبیل به محوطهٔ شمالی منتقل شود.
""".strip()

GOLD_MENTIONS = [
    {"type": "PROJECT", "canonical_name": "پل رودخانه", "mention_text": "پروژهٔ پل رودخانه"},
    {"type": "TIME", "canonical_name": "۱۷ شهریور ۱۴۰۴", "mention_text": "۱۷ شهریور ۱۴۰۴"},
    {"type": "PLACE", "canonical_name": "کارگاه جنوبی", "mention_text": "کارگاه جنوبی"},
    {"type": "PERSON", "canonical_name": "سارا احمدی", "mention_text": "سارا احمدی"},
    {"type": "ROLE", "canonical_name": "مدیر پروژه", "mention_text": "مدیر پروژه"},
    {"type": "UNIT", "canonical_name": "واحد مالی", "mention_text": "واحد مالی"},
    {"type": "ORG", "canonical_name": "پارس‌سازه", "mention_text": "شرکت پارس‌سازه"},
    {"type": "TASK", "canonical_name": "پرداخت پیمانکار فاز ۲", "mention_text": "پرداخت پیمانکار فاز ۲"},
    {"type": "ROLE", "canonical_name": "مسئول مالی", "mention_text": "مسئول مالی"},
    {"type": "PERSON", "canonical_name": "رضا کریمی", "mention_text": "رضا کریمی"},
    {"type": "OBJECT", "canonical_name": "سرور پشتیبان", "mention_text": "سرور پشتیبان"},
    {"type": "TIME", "canonical_name": "۲۵ شهریور ۱۴۰۴ ساعت ۱۶", "mention_text": "چهارشنبه ۲۵ شهریور ۱۴۰۴ ساعت ۱۶"},
    {"type": "OBJECT", "canonical_name": "جرثقیل موبیل", "mention_text": "جرثقیل موبیل"},
    {"type": "PLACE", "canonical_name": "محوطهٔ شمالی", "mention_text": "محوطهٔ شمالی"},
]
