"""عنوان سرور و annotations ابزارهای فکت و نقل‌قول و قاب مسئله."""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-nlp"
SERVER_TITLE = "پردازش زبانی"
SERVER_DESCRIPTION = (
    "از متن گزارش، جلسه یا پیام فکت عددی، شرط، علت، تغییر، نقل‌قول "
    "و قاب مسئله را با شاهد داخل متن استخراج می‌کند؛ چیزی در PostgreSQL "
    "نمی‌نویسد. ذخیره قاب با create_issue و علت با link_issue_cause "
    "و وظیفه با create_task و link_issue_task در management-crud است. "
    "امتیاز مسئله با set_issue_importance و set_issue_urgency و "
    "set_issue_severity و add_issue_impact است؛ استخراج اهمیت نیست. "
    "موضوع و موجودیت ذخیره‌شدهٔ NER با link_issue_topic و "
    "link_issue_entity به مسئله وصل می‌شود. "
    "نیت و ژانر و موجودیت مال management-ner است."
)
SERVER_INSTRUCTIONS = (
    "سه ابزار جدا: extract_facts (مقدار، درصد، شرط، علت، تغییر، وضعیت و "
    "صراحت explicit/derived)، extract_quotes (نقل مستقیم/غیرمستقیم و "
    "گوینده جمله داخلی)، extract_frame (عنوان، واحد، فرآیند، محدوده). "
    "عددِ نیامده در متن فقط اگر تفریق/جمع منابع صریح درست باشد می‌ماند. "
    "حدس بی‌شاهد حذف می‌شود. INSERT در این سرور نیست. "
    "ذخیره قاب با create_issue و علت‌های تأییدشده با link_issue_cause "
    "و وظیفهٔ پیشنهادی با create_task و link_issue_task "
    "و امتیاز با set_issue_importance و set_issue_urgency و "
    "set_issue_severity و add_issue_impact "
    "و موضوع و موجودیت ذخیره‌شده با link_issue_topic و "
    "link_issue_entity "
    "و فکت‌ها و نقل‌قول‌های تأییدشده با save_text_analysis "
    "در management-crud و تأیید انسان در playground است. "
    "متن آزاد با فیلد text می‌آید. منبع ذخیره‌شده با source_type "
    "(meeting یا message) و source_id. "
    "context اختیاری برای جملات قبل/بعد است؛ شاهد از متن اصلی است. "
    "نام مدل از config/llm.yaml و کلید از NLP_LLM_API_KEY می‌آید."
)

READ_ONLY_NLP = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)

TITLE_EXTRACT_FACTS = "استخراج فکت مقید به شاهد"
TITLE_EXTRACT_QUOTES = "استخراج نقل‌قول"
TITLE_EXTRACT_FRAME = "استخراج قاب مسئله"
