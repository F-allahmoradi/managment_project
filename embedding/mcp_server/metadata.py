"""عنوان سرور و annotations ابزارهای امبدینگ و بازیابی معنایی."""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-embedding"
SERVER_TITLE = "امبدینگ و بازیابی متن تحلیل‌شده"
SERVER_DESCRIPTION = (
    "متن خام ذخیره‌شده، موجودیت، نیت و اجزای نیت را برداری می‌کند "
    "و موارد مشابه سؤال را برمی‌گرداند. آمار عملیاتی و استخراج NER اینجا نیست."
)
SERVER_INSTRUCTIONS = (
    "بعد از save_text_analysis در management-crud، "
    "index_text_analysis همان تحلیل را امبد می‌کند. "
    "برای تحلیل‌های قبلی index_pending_analyses. "
    "search_similar موارد مشابه را از متن خام و فکت استخراج‌شده می‌آورد؛ "
    "نزدیک‌ترین‌ها را Postgres با pgvector و ایندکس HNSW کسینوس می‌آورد. "
    "جواب نهایی را عامل از روی hitها می‌سازد. "
    "جواب نهایی را عامل از روی hitها می‌سازد. "
    "شمارش، مهلت و مبلغ مال management-stats است نه cosine. "
    "kinds را raw / entity / intent / intent_slot بگذارید؛ خالی یعنی همه. "
    "مدل امبدینگ از embedding_model در llm.yaml می‌آید."
)

READ_ONLY_EMBEDDING = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
WRITE_EMBEDDING = ToolAnnotations(
    read_only_hint=False,
    open_world_hint=True,
)

TITLE_INDEX_TEXT_ANALYSIS = "برداری‌کردن تحلیل متن"
TITLE_INDEX_PENDING_ANALYSES = "برداری‌کردن تحلیل‌های باقی‌مانده"
TITLE_SEARCH_SIMILAR = "جستجوی موارد مشابه"
