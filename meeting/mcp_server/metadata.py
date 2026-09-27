"""عنوان سرور و annotations ابزارهای جلسه.

ضبط صوت/متن در contents (crud) ساخته می‌شود؛ این سرور record و sync دارد.
"""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-meeting"
SERVER_TITLE = "جلسات سامانه مدیریت"
SERVER_DESCRIPTION = (
    "الگوی تکرار، نمونهٔ جلسه، ضبط و همگام‌سازی به پروژه را در PostgreSQL "
    "ثبت می‌کند. محتوا در crud ساخته می‌شود."
)
SERVER_INSTRUCTIONS = (
    "create_meeting_schedule الگوی مدیر را با روز هفتهٔ ایرانی "
    "(۰=شنبه تا ۶=جمعه) و ساعت ذخیره می‌کند. project_id اختیاری است. "
    "generate_meetings از روی الگو برای هفتهٔ هدف یک ردیف meetings "
    "می‌سازد؛ پیش‌فرض هفتهٔ بعد است. اگر همان ساعت پر باشد جلسه "
    "ساخته نمی‌شود و هفتهٔ بعد در suggested_at پیشنهاد می‌شود. "
    "create_meeting یک جلسه مشخص می‌سازد؛ تداخل همان قانون را دارد "
    "ولی با MEETING_SLOT_CONFLICT برمی‌گردد. "
    "update_meeting عنوان، زمان، مکان و پروژه را عوض می‌کند؛ فقط مدیر "
    "همان جلسه و با Meeting/Update. جلسهٔ لغو شده ویرایش نمی‌شود. "
    "cancel_meeting وضعیت را به لغو شده می‌برد؛ ردیف حذف نمی‌شود. "
    "create_meeting_participant دقیقاً یکی از user_id یا "
    "external_contact_id را می‌پذیرد. "
    "visibility از الان ذخیره می‌شود: PRIVATE یا RESTRICTED یا PROJECT. "
    "create_content مال سرور crud است. record_meeting همان content_id "
    "را به جلسه وصل می‌کند و وضعیت را ضبط شده می‌کند. "
    "sync_meeting برای جلسه تیم با PROJECT در صورت مسئول، tasks را "
    "می‌سازد و اگر chat_id بیاید پیام چت با همان تسک می‌گذارد. "
    "مذاکره خارجی/حقوقی با confirm همگام می‌شود. جلسه PRIVATE بدون "
    "پروژه همگام نمی‌شود. خروجی‌ها در meeting_sync_items لینک می‌شوند."
)

TITLE_CREATE_MEETING_SCHEDULE = "ثبت الگوی جلسه"
TITLE_GET_MEETING_SCHEDULE = "خواندن الگوی جلسه"
TITLE_LIST_MEETING_SCHEDULES = "فهرست الگوهای جلسه"
TITLE_CREATE_MEETING = "ثبت جلسه"
TITLE_GET_MEETING = "خواندن جلسه"
TITLE_LIST_MEETINGS = "فهرست جلسات"
TITLE_UPDATE_MEETING = "به‌روزرسانی جلسه"
TITLE_CANCEL_MEETING = "لغو جلسه"
TITLE_CREATE_MEETING_PARTICIPANT = "افزودن شرکت‌کننده جلسه"
TITLE_GENERATE_MEETINGS = "چیدن جلسات از روی الگو"
TITLE_RECORD_MEETING = "ضبط جلسه"
TITLE_SYNC_MEETING = "همگام‌سازی جلسه"

READ_ONLY_MEETING = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
WRITE_MEETING = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    open_world_hint=True,
)
