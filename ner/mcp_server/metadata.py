"""عنوان سرور و annotations ابزارهای استخراج متن پروژه."""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-ner"
SERVER_TITLE = "استخراج متن پروژه"
SERVER_DESCRIPTION = (
    "از متن گزارش، جلسه یا پیام موجودیت، کلمهٔ کلیدی، موضوع، احساس، "
    "ژانر پیام، نیت و صنعت بیان را با ابزارهای جدا استخراج می‌کند؛ چیزی در "
    "PostgreSQL نمی‌نویسد. ذخیره با save_text_analysis در management-crud است."
)
SERVER_INSTRUCTIONS = (
    "هفت ابزار جدا: extract_entities (ذکر PERSON تا ROLE، از جمله OBJECT "
    "و TIME با occurred_at)، extract_keywords (عبارت کلیدی)، "
    "extract_topics (درخت حوزه با path)، extract_sentiment "
    "(قطبیت و هیجان)، extract_discourse (ژانر / نوع پیام)، "
    "extract_intent (نیت / مسیر رسیدگی)، extract_rhetoric "
    "(کنایه، طعنه، طنز، استعاره و معنای مقصود). هر ابزار یک درخواست مدل جدا است. "
    "برای متن غیرصریح اول extract_rhetoric، بعد نیت و ژانر و احساس را با "
    "intended_meaning صدا بزن. INSERT در این سرور نیست؛ بعد از نمایش، ثبت با "
    "save_text_analysis در management-crud و وضعیت پیشنهادی است. بعد از ذخیره، "
    "index_text_analysis در management-embedding همان تحلیل را امبد می‌کند. "
    "متن آزاد با فیلد text می‌آید. منبع ذخیره‌شده با source_type "
    "(meeting یا message) و source_id. "
    "نام مدل از config/llm.yaml و کلید از NER_LLM_API_KEY می‌آید."
)

READ_ONLY_NER = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)

TITLE_EXTRACT_ENTITIES = "استخراج موجودیت از متن پروژه"
TITLE_EXTRACT_KEYWORDS = "استخراج کلمهٔ کلیدی"
TITLE_EXTRACT_TOPICS = "طبقه‌بندی موضوع"
TITLE_EXTRACT_SENTIMENT = "تحلیل احساس"
TITLE_EXTRACT_DISCOURSE = "طبقه‌بندی نوع پیام"
TITLE_EXTRACT_INTENT = "طبقه‌بندی نیت"
TITLE_EXTRACT_RHETORIC = "طبقه‌بندی صنعت بیان"
