"""عنوان سرور و annotations ابزارهای CRUD.

نام و توضیح خود سرور اینجا است. ابزارهای تشویق و تنبیه
و محتوا در همین سرور ثبت می‌شوند. جلسه سرور جدا است.
"""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-crud"
SERVER_TITLE = "CRUD سامانه مدیریت"
SERVER_DESCRIPTION = (
    "ثبت، خواندن، فهرست، به‌روزرسانی و حذف موجودیت‌های سامانه مدیریت پروژه "
    "را انجام می‌دهد. محتوا زیرساخت مشترک متن و صوت است؛ جلسه سرور جدا است."
)
SERVER_INSTRUCTIONS = (
    "ابزارهای User فقط با مجوز Resource/Action همان کاربر جاری اجرا می‌شوند: "
    "create_user با User/Create، list_users و get_user با User/Read، "
    "update_user با User/Update، delete_user با User/Delete. "
    "کاربر جاری از MCP_ACTOR_USER_ID یا MCP_ACTOR_USERNAME خوانده می‌شود. "
    "نقش سیستم با tools نقش و مجوز جدا از نقش داخل پروژه است. "
    "create_user_role و delete_user_role و list_user_roles فقط با UserRole "
    "و برای مدیر کل است. list_assignable_users برای مدیر کل همه را و برای "
    "مدیر پروژه فقط ثبت‌نام‌شده‌های نقش کاربر را نشان می‌دهد. "
    "create_project با Project/Create سازنده را مدیر همان پروژه می‌کند. "
    "list_projects و get_project و update_project و delete_project فقط "
    "پروژه‌هایی را می‌بینند که کاربر عضو فعال‌شان است. "
    "delete_project با Project/Delete پروژهٔ بدون وظیفه و جلسه را حذف "
    "می‌کند؛ عضوها CASCADE می‌شوند و وابسته‌های RESTRICT حذف را رد می‌کنند. "
    "create_project_member و update_project_member با ProjectMember/Update "
    "و عضویت فعال همان پروژه کار می‌کنند. "
    "create_task با Task/Create روی پروژه‌ای که عضو فعال آن هستید کار "
    "می‌کند؛ مسئول باید عضو فعال همان پروژه باشد. "
    "list_tasks فقط وظایف همان پروژه‌ها را نشان می‌دهد. "
    "delete_task با Task/Delete همان وظیفه را حذف می‌کند؛ زیرکار و "
    "پیگیری CASCADE می‌شوند. "
    "create_task_follow_up یک رخداد پیگیری جدا است؛ عوض کردن وضعیت کار "
    "ردیف پیگیری نمی‌سازد. "
    "create_task_item و update_task_item و complete_task_item و "
    "delete_task_item فقط برای مسئول همان وظیفه است؛ عضو دیگر پروژه "
    "حتی با Task/Update خطای دامنه می‌گیرد. list_task_items درخت "
    "زیرکار را با ترتیب sort_order نشان می‌دهد. start_date و end_date "
    "فقط ذخیره می‌شوند؛ reminders خودکار ساخته نمی‌شود. "
    "create_external_contact مخاطب خارج از سامانه است و ردیف users نمی‌سازد. "
    "create_chat گفتگوی خصوصی یا پروژه می‌سازد و سازنده را عضو می‌کند. "
    "create_chat_member فقط کاربر سامانه را عضو می‌کند. "
    "create_message متن را در گفتگوی پروژه (با پروژه؛ تسک اختیاری) یا در گفتگوی خصوصی بدون تسک می‌گذارد و "
    "گیرنده‌ها را همان لحظه در message_recipients می‌سازد؛ ژانر از "
    "save_text_analysis بعد از استخراج و تأیید می‌آید. content_id "
    "در این گام خالی می‌ماند. "
    "هر گیرنده دقیقاً یکی از user یا external_contact است. "
    "list_messages فقط گفتگوهایی را نشان می‌دهد که کاربر عضوشان است. "
    "list_notifications فقط اعلان داخل پنل خود کاربر را نشان می‌دهد؛ "
    "create_task برای مسئول اعلان «وظیفه جدید» می‌نویسد و "
    "create_project_member برای عضو جدید «افزوده شدن به پروژه». "
    "متن اعلان در message است و content_id خالی می‌ماند. "
    "list_audit_logs با مجوز AuditLog/Read است؛ ساختن دستی ممیزی نیست. "
    "notifications با audit_logs و با execution_logs فرق دارد. "
    "create_performance_action تشویق یا تنبیه است؛ روی User فیلد "
    "امتیاز یا مبلغ نمی‌گذارد. reason اجباری است. "
    "امتیاز بدون مبلغ تراکنش نمی‌سازد؛ مبلغ همان لحظه تراکنش پاداش "
    "یا جریمه می‌سازد و financial_transaction_id را پر می‌کند. "
    "اگر score باشد یک ردیف performance_scores با همان دلیل ساخته می‌شود. "
    "list_performance_actions امتیاز و مبلغ را جدا نشان می‌دهد. "
    "create_content متن یا متادیتای صوت را در contents می‌گذارد؛ "
    "آپلود واقعی S3 نیست و storage_key کافی است. فقط TEXT و VOICE. "
    "get_content همان ردیف را با نوع و متادیتای فایل می‌خواند. "
    "list_contents فقط محتواهای فعال خود کاربر را نشان می‌دهد. "
    "delete_content با Content/Delete محتوا را نرم‌حذف می‌کند؛ "
    "اگر به مستند پروژه وصل باشد حذف رد می‌شود. "
    "save_text_analysis خروجی extract_* سرور NER را در جداول تحلیل "
    "با وضعیت پیشنهادی می‌نویسد؛ نمایش و بررسی دقت جدا می‌ماند. "
    "منبع meeting/message با source_id است. برای متن آزاد "
    "playground نوع content با text یک ردیف contents هم می‌سازد. "
    "get_text_analysis همان ذکرها و موضوع و احساس و ژانر و نیت و فکت "
    "و نقل‌قول و کلمهٔ کلیدی ذخیره‌شده را برمی‌گرداند. list_text_analyses فقط تحلیل‌های خود کاربر است. "
    "create_issue کارت مسئله را با عنوان و پروژه و وضعیت seed می‌نویسد "
    "و همان تحلیل را از طریق issue_sources وصل می‌کند. استخراج در nlp "
    "می‌ماند. علت با link_issue_cause است: دو issue_id و سطح cause یا "
    "root_cause. وظیفه با create_task ساخته می‌شود و با link_issue_task "
    "به مسئله وصل می‌گردد؛ همان تحلیل در analysis_outputs به tasks.id "
    "می‌رسد. اهمیت مسئله با set_issue_importance، فوریت با "
    "set_issue_urgency، شدت با set_issue_severity و اثر با "
    "add_issue_impact از کاتالوگ seed نوشته می‌شود؛ حدس LLM نیست. "
    "موضوع ذخیره‌شدهٔ NER با link_issue_topic و موجودیت با "
    "link_issue_entity و نقش seed مسئول/متأثر/ذکرشده به همان مسئله "
    "وصل می‌شود؛ استخراج جدید نیست. عنوان تکراری در همان پروژه همان "
    "مسئله را با issue_sources دوباره پیدا می‌کند. "
    "list_issues فقط مسائل پروژه‌هایی را نشان می‌دهد که کاربر عضو فعال‌شان است. "
    "برای نوع و وضعیت و نقش داخل پروژه و وضعیت و اولویت و اهمیت کار "
    "و نوع گفتگو و نوع اعلان "
    "و نوع تشویق/تنبیه ابزار جدا نیست؛ نام seed مثل تقدیر یا اخطار کافی است. "
    "ارسال واقعی تلگرام/SMS مال reminder است و جلسه سرور جدا است."
)

TITLE_CREATE_USER = "ثبت کاربر"
TITLE_GET_USER = "خواندن کاربر"
TITLE_LIST_USERS = "فهرست کاربران"
TITLE_LIST_ASSIGNABLE_USERS = "فهرست افراد قابل تعیین دسترسی"
TITLE_UPDATE_USER = "به‌روزرسانی کاربر"
TITLE_DELETE_USER = "حذف کاربر"

TITLE_CREATE_ROLE = "ثبت نقش"
TITLE_GET_ROLE = "خواندن نقش"
TITLE_LIST_ROLES = "فهرست نقش‌ها"
TITLE_UPDATE_ROLE = "به‌روزرسانی نقش"
TITLE_DELETE_ROLE = "حذف نقش"

TITLE_CREATE_PERMISSION = "ثبت مجوز"
TITLE_LIST_PERMISSIONS = "فهرست مجوزها"

TITLE_CREATE_ROLE_PERMISSION = "دادن مجوز به نقش"
TITLE_DELETE_ROLE_PERMISSION = "گرفتن مجوز از نقش"
TITLE_LIST_ROLE_PERMISSIONS = "فهرست مجوزهای نقش"

TITLE_CREATE_USER_ROLE = "دادن نقش به کاربر"
TITLE_DELETE_USER_ROLE = "گرفتن نقش از کاربر"
TITLE_LIST_USER_ROLES = "فهرست نقش‌های کاربر"

TITLE_CREATE_PROJECT = "ثبت پروژه"
TITLE_GET_PROJECT = "خواندن پروژه"
TITLE_LIST_PROJECTS = "فهرست پروژه‌ها"
TITLE_UPDATE_PROJECT = "به‌روزرسانی پروژه"
TITLE_DELETE_PROJECT = "حذف پروژه"

TITLE_CREATE_PROJECT_MEMBER = "افزودن عضو پروژه"
TITLE_LIST_PROJECT_MEMBERS = "فهرست اعضای پروژه"
TITLE_UPDATE_PROJECT_MEMBER = "به‌روزرسانی عضو پروژه"

TITLE_CREATE_TASK = "ثبت وظیفه"
TITLE_GET_TASK = "خواندن وظیفه"
TITLE_LIST_TASKS = "فهرست وظایف"
TITLE_UPDATE_TASK = "به‌روزرسانی وظیفه"
TITLE_DELETE_TASK = "حذف وظیفه"

TITLE_CREATE_TASK_ITEM = "ثبت زیرکار"
TITLE_LIST_TASK_ITEMS = "فهرست زیرکارها"
TITLE_UPDATE_TASK_ITEM = "به‌روزرسانی زیرکار"
TITLE_COMPLETE_TASK_ITEM = "تیک زدن زیرکار"
TITLE_DELETE_TASK_ITEM = "حذف زیرکار"

TITLE_CREATE_TASK_FOLLOW_UP = "ثبت پیگیری وظیفه"
TITLE_GET_TASK_FOLLOW_UP = "خواندن پیگیری وظیفه"
TITLE_LIST_TASK_FOLLOW_UPS = "فهرست پیگیری‌های وظیفه"

TITLE_CREATE_EXTERNAL_CONTACT = "ثبت مخاطب خارجی"
TITLE_GET_EXTERNAL_CONTACT = "خواندن مخاطب خارجی"
TITLE_LIST_EXTERNAL_CONTACTS = "فهرست مخاطبان خارجی"

TITLE_CREATE_CHAT = "ساخت گفتگو"
TITLE_GET_CHAT = "خواندن گفتگو"
TITLE_LIST_CHATS = "فهرست گفتگوها"

TITLE_CREATE_CHAT_MEMBER = "افزودن عضو گفتگو"
TITLE_LIST_CHAT_MEMBERS = "فهرست اعضای گفتگو"

TITLE_CREATE_MESSAGE = "ارسال پیام"
TITLE_GET_MESSAGE = "خواندن پیام"
TITLE_LIST_MESSAGES = "فهرست پیام‌ها"

TITLE_CREATE_MESSAGE_RECIPIENT = "افزودن گیرنده پیام"
TITLE_LIST_MESSAGE_RECIPIENTS = "فهرست گیرنده‌های پیام"

TITLE_LIST_NOTIFICATIONS = "فهرست اعلان‌ها"
TITLE_GET_NOTIFICATION = "خواندن اعلان"
TITLE_MARK_NOTIFICATION_READ = "خوانده‌کردن اعلان"

TITLE_LIST_AUDIT_LOGS = "فهرست ممیزی"
TITLE_GET_AUDIT_LOG = "خواندن ممیزی"

TITLE_CREATE_PERFORMANCE_ACTION = "ثبت تشویق و تنبیه"
TITLE_GET_PERFORMANCE_ACTION = "خواندن اقدام عملکرد"
TITLE_LIST_PERFORMANCE_ACTIONS = "فهرست اقدامات عملکرد"

TITLE_CREATE_CONTENT = "ثبت محتوا"
TITLE_GET_CONTENT = "خواندن محتوا"
TITLE_LIST_CONTENTS = "فهرست محتواها"
TITLE_DELETE_CONTENT = "حذف محتوا"

TITLE_SAVE_TEXT_ANALYSIS = "ذخیره تحلیل متن"
TITLE_GET_TEXT_ANALYSIS = "خواندن تحلیل متن"
TITLE_LIST_TEXT_ANALYSES = "فهرست تحلیل‌های متن"

TITLE_CREATE_ISSUE = "ثبت مسئله"
TITLE_GET_ISSUE = "خواندن مسئله"
TITLE_LIST_ISSUES = "فهرست مسائل"
TITLE_LINK_ISSUE_CAUSE = "وصل علت مسئله"
TITLE_LINK_ISSUE_TASK = "وصل وظیفه به مسئله"
TITLE_SET_ISSUE_IMPORTANCE = "تنظیم اهمیت مسئله"
TITLE_SET_ISSUE_URGENCY = "تنظیم فوریت مسئله"
TITLE_SET_ISSUE_SEVERITY = "تنظیم شدت مسئله"
TITLE_ADD_ISSUE_IMPACT = "افزودن اثر مسئله"
TITLE_LINK_ISSUE_TOPIC = "وصل موضوع به مسئله"
TITLE_LINK_ISSUE_ENTITY = "وصل موجودیت به مسئله"

READ_ONLY_CRUD = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
WRITE_CRUD = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    open_world_hint=True,
)
DESTRUCTIVE_CRUD = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    open_world_hint=True,
)
