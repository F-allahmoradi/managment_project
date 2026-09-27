"""توضیح کامل هر ابزار CRUD برای description روی سیم پروتکل.

گام دوازده تشویق و تنبیه را ثبت می‌کند.
اعلان با ممیزی و با execution_logs فرق دارد.
"""

CREATE_USER = """
یک کاربر جدید در جدول users در PostgreSQL ثبت می‌کند.

چرا این ابزار:
    عملیات نوشتن کاربر جدا از نقش و پروژه است. فقط INSERT روی users
    انجام می‌شود تا ساخت کاربر از RBAC جدا بماند.

مجوز لازم:
    User/Create برای کاربر جاری (MCP_ACTOR_USER_ID یا MCP_ACTOR_USERNAME).

ورودی اجباری:
    first_name، last_name، username، password.

ورودی اختیاری:
    phone، email، is_active (پیش‌فرض true).

خروجی:
    JSON با status برابر success، id شناسه جدید، و message.
    خطای اعتبارسنجی یا مقدار تکراری با error_code برابر INVALID_INPUT
    برمی‌گردد. نبود مجوز PERMISSION_DENIED است.

زنجیره فراخوانی:
    1. require_permission User/Create
    2. validate_create_user — طول، قالب ایمیل، رمز غیرخالی
    3. insert_user — هش رمز و INSERT ستون‌های users
    4. format_success یا format_error

طراحی:
    ستون‌های id و created_at و password_hash از کلاینت گرفته نمی‌شوند.
    رمز خام هش PBKDF2 می‌شود و در پاسخ نمی‌آید.
    سقف زمانی کوئری و لاگ duration_ms از middleware موجود است.
""".strip()

GET_USER = """
یک کاربر را با شناسه از جدول users در PostgreSQL می‌خواند.

چرا این ابزار:
    بعد از ثبت کاربر، خواندن همان ردیف با id لازم است. فقط یک SELECT
    روی users انجام می‌شود تا get از list و update جدا بماند.

مجوز لازم:
    User/Read برای کاربر جاری.

چرا بدون صفحه‌بندی:
    خروجی یک رکورد است؛ limit و offset اینجا معنا ندارند.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با status برابر success، message، و ستون‌های عمومی همان کاربر.
    password و password_hash در پاسخ نیستند.
    اگر ردیف نباشد error_code برابر USER_NOT_FOUND است.
    خطای اعتبارسنجی با error_code برابر INVALID_INPUT برمی‌گردد.

زنجیره فراخوانی:
    1. require_permission User/Read
    2. validate_get_user — id مثبت
    3. fetch_user — SELECT ستون‌های عمومی
    4. format_success یا format_error

طراحی:
    SELECT * نیست؛ password_hash خوانده نمی‌شود.
    سقف زمانی کوئری و لاگ duration_ms از middleware موجود است.
""".strip()

LIST_USERS = """
چند کاربر را با صفحه‌بندی از جدول users در PostgreSQL می‌خواند.

چرا این ابزار:
    بعد از خواندن یک کاربر با شناسه، فهرست چند ردیف لازم است. فقط SELECT
    با LIMIT و OFFSET روی users انجام می‌شود تا list از get و update
    جدا بماند.

مجوز لازم:
    User/Read برای کاربر جاری.

چرا بدون فیلتر پیچیده:
    این گام فقط صفحه‌بندی است؛ شرط روی نام یا ایمیل در ابزار جدا می‌آید.

ورودی اختیاری:
    limit تعداد رکورد (پیش‌فرض ۱۰، حداکثر ۵۰) و offset (پیش‌فرض ۰).

خروجی:
    JSON با status برابر success، message، records، limit و offset.
    password_hash در هیچ ردیفی نیست.
    اگر limit بالای ۵۰ باشد error_code برابر INVALID_INPUT است.
    فهرست خالی خطا نیست.

زنجیره فراخوانی:
    1. require_permission User/Read
    2. validate_list_users — نوع و سقف limit و offset
    3. fetch_users — SELECT ستون‌های عمومی با LIMIT OFFSET
    4. format_success یا format_error

طراحی:
    SELECT * نیست؛ ترتیب پایدار با ORDER BY id DESC است.
    سقف زمانی کوئری و لاگ duration_ms از middleware موجود است.
""".strip()

UPDATE_USER = """
یک کاربر موجود در جدول users در PostgreSQL را به‌روز می‌کند.

چرا این ابزار:
    بعد از فهرست کاربران، تغییر همان ردیف لازم است. فقط UPDATE روی
    کاربر انجام می‌شود؛ ردیف جدید ساخته نمی‌شود تا update از create
    جدا بماند.

مجوز لازم:
    User/Update برای کاربر جاری.

چرا بدون حذف:
    DELETE مخرب است و ابزار جدا دارد.

ورودی اجباری:
    id عدد صحیح مثبت.

ورودی اختیاری:
    همان فیلدهای قابل‌نوشتن ساخت کاربر: first_name، last_name،
    username، password، phone، email، is_active.
    حداقل یکی باید بیاید. پیش‌فرض‌های create اینجا اعمال نمی‌شود.

خروجی:
    JSON با status برابر success، id همان شناسه، و message.
    اگر ردیف نباشد error_code برابر USER_NOT_FOUND است.
    اگر فیلد قابل‌به‌روزرسانی نیاید، اعتبارسنجی رد شود، یا مقدار یکتا
    تکراری باشد، error_code برابر INVALID_INPUT است.

زنجیره فراخوانی:
    1. require_permission User/Update
    2. validate_update_user — id و فیلدهای اختیاری
    3. update_user — هش رمز در صورت وجود و UPDATE ستون‌ها
    4. format_success یا format_error

طراحی:
    ستون‌های created_at و password_hash از کلاینت گرفته نمی‌شوند.
    اگر password بیاید دوباره هش می‌شود.
    id فقط برای WHERE است، نه برای عوض کردن شناسه.
    سقف زمانی کوئری و لاگ duration_ms از middleware موجود است.
""".strip()

DELETE_USER = """
یک کاربر موجود را با شناسه از جدول users در PostgreSQL حذف می‌کند.

چرا این ابزار:
    بعد از به‌روزرسانی کاربر، حذف همان ردیف لازم است. فقط DELETE روی
    users انجام می‌شود؛ ردیف جدید ساخته نمی‌شود تا delete از create
    جدا بماند.

مجوز لازم:
    User/Delete برای کاربر جاری.

چرا بدون نقش در SQL:
    این ابزار روی roles کوئری نمی‌زند. اگر ردیف وابسته با RESTRICT
    مانع شود، DATABASE_ERROR برمی‌گردد.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با status برابر success، id همان شناسه، و message.
    اگر ردیف نباشد error_code برابر USER_NOT_FOUND است.
    خطای اعتبارسنجی با error_code برابر INVALID_INPUT برمی‌گردد.

زنجیره فراخوانی:
    1. require_permission User/Delete
    2. validate_delete_user — id مثبت
    3. delete_user — DELETE همان ردیف
    4. format_success یا format_error

طراحی:
    فقط یک ردیف users حذف می‌شود.
    سقف زمانی کوئری و لاگ duration_ms از middleware موجود است.
""".strip()

CREATE_ROLE = """
یک نقش جدید در جدول roles در PostgreSQL ثبت می‌کند.

چرا این ابزار:
    نقش‌های seed از قبل هستند؛ این ابزار نقش سفارشی غیرسیستمی می‌سازد
    تا زنجیره کاربر ← نقش ← مجوز کامل شود.

چرا بدون is_system_role:
    نقش سیستمی فقط از seed می‌آید تا مدیر کل و بقیه دست‌نخورده بمانند.

ورودی اجباری:
    name.

ورودی اختیاری:
    description، is_active (پیش‌فرض true).

خروجی:
    JSON با status برابر success، id شناسه جدید، و message.
    نام تکراری با error_code برابر INVALID_INPUT برمی‌گردد.
""".strip()

GET_ROLE = """
یک نقش را با شناسه از جدول roles می‌خواند.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با ستون‌های نقش شامل is_system_role.
    اگر ردیف نباشد error_code برابر ROLE_NOT_FOUND است.
""".strip()

LIST_ROLES = """
چند نقش را با صفحه‌بندی از جدول roles می‌خواند.

نقش‌های seed مثل مدیر کل در همین فهرست می‌آیند؛ بازنویسی نمی‌شوند.

ورودی اختیاری:
    limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

UPDATE_ROLE = """
یک نقش موجود را به‌روز می‌کند.

نام نقش سیستمی عوض نمی‌شود تا seed دست‌نخورده بماند.

ورودی اجباری:
    id.

ورودی اختیاری:
    name، description، is_active. حداقل یکی لازم است.
""".strip()

DELETE_ROLE = """
یک نقش غیرسیستمی را حذف می‌کند.

نقش سیستمی مثل مدیر کل حذف نمی‌شود.

ورودی اجباری:
    id.
""".strip()

CREATE_PERMISSION = """
یک مجوز ریز Resource + Action در جدول permissions ثبت می‌کند.

مثال:
    name برابر ایجاد کاربر آزمایشی، resource برابر User، action برابر Create.

ورودی اجباری:
    name، resource، action.

خروجی:
    JSON با id مجوز جدید. جفت resource/action تکراری INVALID_INPUT است.
""".strip()

LIST_PERMISSIONS = """
مجوزهای ریز را با صفحه‌بندی می‌خواند.

مجوزهای seed مثل User/Create در همین فهرست هستند.

ورودی اختیاری:
    limit و offset؛ سقف ۵۰.
""".strip()

CREATE_ROLE_PERMISSION = """
یک مجوز را به یک نقش می‌دهد.

زنجیره:
    نقش ← role_permissions ← مجوز.

ورودی اجباری:
    role_id و permission_id.
""".strip()

DELETE_ROLE_PERMISSION = """
یک مجوز را از یک نقش می‌گیرد.

ورودی اجباری:
    id شناسه ردیف role_permissions.
""".strip()

LIST_ROLE_PERMISSIONS = """
اتصال‌های نقش-مجوز را با نام نقش و resource/action می‌خواند.

ورودی اختیاری:
    role_id برای فیلتر، limit و offset.
""".strip()

CREATE_USER_ROLE = """
یک نقش سیستمی را به یک کاربر می‌دهد.

بدون این اتصال، نقش روی کسی نمی‌نشیند و دروازه User کار نمی‌کند.
فقط مدیر کل با UserRole/Create این کار را می‌کند. مدیر سازمان
(نقش مدیر پروژه) از اینجا ساخته می‌شود، نه از ثبت‌نام.

ورودی اجباری:
    user_id و role_id.
""".strip()

DELETE_USER_ROLE = """
یک نقش را از یک کاربر می‌گیرد.

مجوز لازم:
    UserRole/Delete برای مدیر کل.

ورودی اجباری:
    id شناسه ردیف user_roles.
""".strip()

LIST_USER_ROLES = """
نقش‌های وصل‌شده به کاربران را می‌خواند.

مجوز لازم:
    UserRole/Read برای مدیر کل.

ورودی اختیاری:
    user_id برای فیلتر، limit و offset.
""".strip()

LIST_ASSIGNABLE_USERS = """
افرادی را فهرست می‌کند که سطح دسترسی‌شان تعیین می‌شود.

مدیر کل با UserRole/Create همهٔ کاربران فعال را می‌بیند تا مدیر
سازمان بسازد. مدیر پروژه با ProjectMember/Update فقط کسانی را
می‌بیند که خودشان ثبت‌نام کرده‌اند و نقش سیستمی‌شان کاربر است.
نقش داخل پروژه جدا، با create_project_member تعیین می‌شود.

ورودی اختیاری:
    limit و offset؛ سقف ۵۰.

خروجی:
    records با id، نام، نام کاربری و roles. password_hash نیست.
""".strip()

CREATE_PROJECT = """
یک پروژه جدید در جدول projects در PostgreSQL ثبت می‌کند.

چرا این ابزار:
    از این گام تقریباً همه چیز به پروژه وصل می‌شود. فقط INSERT روی
    projects است؛ وظیفه و جلسه اینجا ساخته نمی‌شوند.

قانون سازنده:
    کاربر جاری created_by می‌شود و همان لحظه با نقش داخل پروژه
    «مدیر پروژه» وارد project_members می‌شود تا پروژه بدون مسئول نماند.
    این نقش با نقش سراسری roles فرق دارد.

مجوز لازم:
    Project/Create برای کاربر جاری.

ورودی اجباری:
    name، و نوع پروژه (project_type یا project_type_id)،
    و وضعیت (project_status یا project_status_id).
    نام lookup از seed است؛ مثل نرم‌افزاری و در حال اجرا.

ورودی اختیاری:
    description، start_date، end_date.

خروجی:
    JSON با status برابر success، id شناسه جدید، و message.
    نبود مجوز PERMISSION_DENIED است.

زنجیره فراخوانی:
    1. require_permission Project/Create
    2. validate_create_project
    3. insert_project — INSERT پروژه و عضو سازنده در یک تراکنش
    4. format_success یا format_error
""".strip()

GET_PROJECT = """
یک پروژه را با شناسه می‌خواند؛ فقط اگر کاربر جاری عضو فعال آن باشد.

مجوز لازم:
    Project/Read و عضویت فعال در همان پروژه.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با ستون‌های پروژه شامل نام نوع و وضعیت.
    اگر ردیف نباشد PROJECT_NOT_FOUND است.
    اگر عضو فعال نباشد PERMISSION_DENIED است.
""".strip()

LIST_PROJECTS = """
پروژه‌هایی را فهرست می‌کند که کاربر جاری عضو فعال‌شان است.

این همان شروع Scope است: مجوز Project/Read همهٔ جدول را باز نمی‌کند.

مجوز لازم:
    Project/Read برای کاربر جاری.

ورودی اختیاری:
    limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. پروژهٔ دیگران در فهرست نیست.
    فهرست خالی خطا نیست.
""".strip()

UPDATE_PROJECT = """
یک پروژه موجود را به‌روز می‌کند؛ فقط اگر عضو فعال همان پروژه باشید.

محمد با Project/Update پروژهٔ مدیر دیگر را عوض نمی‌کند.

مجوز لازم:
    Project/Update و عضویت فعال در همان پروژه.

ورودی اجباری:
    id.

ورودی اختیاری:
    name، description، نوع، وضعیت، start_date، end_date.
    حداقل یکی لازم است. created_by عوض نمی‌شود.
""".strip()

DELETE_PROJECT = """
یک پروژه را حذف می‌کند؛ فقط اگر عضو فعال همان پروژه باشید.

اعضای پروژه با CASCADE پاک می‌شوند. اگر وظیفه، جلسه، گزارش،
یادآوری، گفتگو، مسئله یا تراکنش مالی داشته باشد حذف نمی‌شود.

مجوز لازم:
    Project/Delete و عضویت فعال در همان پروژه.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با id حذف‌شده.
    اگر ردیف نباشد PROJECT_NOT_FOUND است.
    اگر وابسته داشته باشد INVALID_INPUT است.
""".strip()

CREATE_PROJECT_MEMBER = """
یک کاربر را با نقش داخل پروژه به یک پروژه اضافه می‌کند.

نقش اینجا از project_roles است (مدیر پروژه، عضو، ناظر)، نه از roles.

مجوز لازم:
    ProjectMember/Update و عضویت فعال در همان پروژه.
    seed مجوز جدا برای Create عضو ندارد؛ افزودن عضو ویرایش اعضا است.

ورودی اجباری:
    project_id، user_id، و نقش (project_role یا project_role_id).

خروجی:
    JSON با id ردیف project_members.
    عضو تکراری INVALID_INPUT است.
    عضو جدید اعلان «افزوده شدن به پروژه» می‌گیرد.
""".strip()

LIST_PROJECT_MEMBERS = """
اعضای یک پروژه را می‌خواند؛ فقط اگر خودتان عضو فعال آن باشید.

مجوز لازم:
    ProjectMember/Read و عضویت فعال در همان پروژه.

ورودی اجباری:
    project_id.

ورودی اختیاری:
    limit و offset.
""".strip()

UPDATE_PROJECT_MEMBER = """
نقش داخل پروژه یا فعال/غیرفعال بودن یک عضویت را عوض می‌کند.

حذف عضو در این گام نیست؛ غیرفعال کردن همان محدوده را می‌بندد.

مجوز لازم:
    ProjectMember/Update و عضویت فعال در همان پروژه.

ورودی اجباری:
    id شناسه ردیف project_members.

ورودی اختیاری:
    project_role یا project_role_id، is_active. حداقل یکی لازم است.
""".strip()

CREATE_TASK = """
یک وظیفه جدید در جدول tasks در PostgreSQL ثبت می‌کند.

چرا این ابزار:
    کار باید روی یک پروژه باشد و از پیگیری جدا بماند. فقط INSERT
    روی tasks است؛ ردیف task_follow_ups ساخته نمی‌شود.

قانون مسئول:
    assigned_to_user_id اگر بیاید باید عضو فعال همان پروژه باشد.
    سازنده created_by_user_id می‌شود.

مجوز لازم:
    Task/Create و عضویت فعال در همان پروژه.

ورودی اجباری:
    project_id، title، و وضعیت (status یا status_id)،
    اولویت (priority یا priority_id)، اهمیت (importance یا importance_id).
    اولویت فوریت است (چقدر زود)؛ اهمیت اثر است (چقدر حیاتی). قاطی نکنید.
    نام lookup از seed است؛ مثل شروع نشده، فوری، حیاتی.

ورودی اختیاری:
    assigned_to_user_id، description، importance_percent،
    start_date، due_date.

خروجی:
    JSON با status برابر success، id شناسه جدید، و message.
    مسئول خارج از پروژه INVALID_INPUT است.
    نبود مجوز یا عضویت PERMISSION_DENIED است.

زنجیره فراخوانی:
    1. require_permission Task/Create
    2. validate_create_task
    3. require_active_project_member
    4. insert_task — INSERT روی tasks، اعلان مسئول، ردیف ممیزی
    5. format_success یا format_error
""".strip()

GET_TASK = """
یک وظیفه را با شناسه می‌خواند؛ فقط اگر کاربر جاری عضو فعال
پروژهٔ همان وظیفه باشد. پیگیری‌ها در این پاسخ نیستند.

مجوز لازم:
    Task/Read و عضویت فعال در پروژهٔ همان وظیفه.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با ستون‌های کار شامل نام وضعیت و اولویت و اهمیت.
    اگر ردیف نباشد TASK_NOT_FOUND است.
    اگر عضو فعال نباشد PERMISSION_DENIED است.
""".strip()

LIST_TASKS = """
وظایفی را فهرست می‌کند که روی پروژه‌های عضو فعال بودن کاربر جاری‌اند.

محمد با Task/Read وظیفهٔ پروژهٔ علی را نمی‌بیند.

مجوز لازم:
    Task/Read برای کاربر جاری.
    اگر project_id بیاید، عضویت فعال همان پروژه هم لازم است.

ورودی اختیاری:
    project_id برای محدود کردن به یک پروژه، limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

UPDATE_TASK = """
یک وظیفه موجود را به‌روز می‌کند؛ فقط اگر عضو فعال پروژهٔ همان
وظیفه باشید. عوض کردن وضعیت کار ردیف پیگیری نمی‌سازد.

مجوز لازم:
    Task/Update و عضویت فعال در پروژهٔ همان وظیفه.

ورودی اجباری:
    id.

ورودی اختیاری:
    title، description، assigned_to_user_id، وضعیت، اولویت، اهمیت،
    importance_percent، start_date، due_date، completed_at.
    حداقل یکی لازم است. project_id عوض نمی‌شود.
    مسئول جدید باید عضو فعال همان پروژه باشد.
""".strip()

DELETE_TASK = """
یک وظیفه را حذف می‌کند؛ فقط اگر عضو فعال پروژهٔ همان وظیفه باشید.

زیرکارها و پیگیری‌ها با CASCADE پاک می‌شوند. اتصال به موجودیت
تحلیل حذف را رد می‌کند.

مجوز لازم:
    Task/Delete و عضویت فعال در پروژهٔ همان وظیفه.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با id حذف‌شده.
    اگر ردیف نباشد TASK_NOT_FOUND است.
    اگر وابستهٔ RESTRICT داشته باشد INVALID_INPUT است.
""".strip()

CREATE_TASK_ITEM = """
یک زیرکار سطح اول یا تو در تو زیر یک Task ثبت می‌کند.

چرا این ابزار:
    چک‌لیست پلکانی داخل همان وظیفه است، نه وظیفهٔ جدید.
    parent_item_id خالی یعنی سطح اول؛ پر یعنی زیرمرحلهٔ همان Task.

قانون مسئول:
    فقط assigned_to_user_id همان وظیفه می‌تواند بسازد.
    سرویس قبل از SQL هویت را با SET LOCAL app.current_user_id
    روی سشن می‌گذارد تا تریگر دیتابیس همان قید را ببیند.
    غیرمسئول PERMISSION_DENIED می‌گیرد، نه خطای خام Postgres.

مجوز لازم:
    Task/Update و عضویت فعال در پروژهٔ همان وظیفه.

ورودی اجباری:
    task_id، title.

ورودی اختیاری:
    parent_item_id، description، sort_order، start_date، end_date.
    اگر sort_order نیاید بعدیِ همان سطح است.
    تاریخ فقط ذخیره می‌شود؛ reminders ساخته نمی‌شود.

خروجی:
    JSON با status برابر success و id زیرکار جدید.
""".strip()

LIST_TASK_ITEMS = """
زیرکارهای یک وظیفه را تخت و درختی برمی‌گرداند.

ترتیب هر سطح sort_order سپس id است. records فهرست تخت است؛
tree همان ردیف‌ها با children است.

مجوز لازم:
    Task/Read و عضویت فعال در پروژهٔ همان وظیفه.
    خواندن مال همهٔ اعضای فعال است؛ ساختن مال مسئول.

ورودی اجباری:
    task_id.

خروجی:
    JSON با records و tree. فهرست خالی خطا نیست.
    اگر وظیفه نباشد TASK_NOT_FOUND است.
""".strip()

UPDATE_TASK_ITEM = """
عنوان، ترتیب یا تاریخ یک زیرکار را به‌روز می‌کند.

تیک زدن مال complete_task_item است. task_id عوض نمی‌شود.
یادآوری از تاریخ ساخته نمی‌شود.

مجوز لازم:
    Task/Update، عضویت فعال، و مسئول بودن همان وظیفه.

ورودی اجباری:
    id.

ورودی اختیاری:
    title، description، sort_order، start_date، end_date.
    حداقل یکی لازم است.

خروجی:
    JSON با id. غیرمسئول PERMISSION_DENIED است.
""".strip()

COMPLETE_TASK_ITEM = """
یک زیرکار را تیک می‌زند (is_completed و completed_at).

completed_by_user_id همان مسئول است. is_completed برابر false
تیک را برمی‌دارد.

مجوز لازم:
    Task/Update، عضویت فعال، و مسئول بودن همان وظیفه.

ورودی اجباری:
    id.

ورودی اختیاری:
    is_completed؛ پیش‌فرض true.

خروجی:
    JSON با id. غیرمسئول PERMISSION_DENIED است.
""".strip()

DELETE_TASK_ITEM = """
یک زیرکار را حذف می‌کند؛ زیرمرحله‌ها با CASCADE پاک می‌شوند.

مجوز لازم:
    Task/Update نه Task/Delete؛ عضویت فعال؛ مسئول بودن همان وظیفه.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با id حذف‌شده.
    اگر ردیف نباشد TASK_ITEM_NOT_FOUND است.
""".strip()

CREATE_TASK_FOLLOW_UP = """
یک پیگیری جدا روی یک وظیفه در جدول task_follow_ups ثبت می‌کند.

چرا این ابزار:
    کار با پیگیری یکی نیست. تماس ۱۲ شهریور و پیام ۱۴ شهریور دو ردیف‌اند.
    وضعیت خود tasks اینجا عوض نمی‌شود.

مجوز لازم:
    TaskFollowUp/Create و عضویت فعال در پروژهٔ همان وظیفه.

ورودی اجباری:
    task_id، note، نوع (follow_up_type یا follow_up_type_id)،
    نتیجه (status یا status_id از task_follow_up_statuses).
    نام seed مثل تماس و منتظر پاسخ.

ورودی اختیاری:
    follow_up_date، next_follow_up_date.

خروجی:
    JSON با id ردیف جدید. نبود وظیفه TASK_NOT_FOUND است.
""".strip()

GET_TASK_FOLLOW_UP = """
یک پیگیری را با شناسه می‌خواند؛ فقط اگر عضو فعال پروژهٔ همان
وظیفه باشید.

مجوز لازم:
    TaskFollowUp/Read و عضویت فعال در پروژهٔ همان وظیفه.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با نوع، نتیجه، یادداشت و تاریخ پیگیری بعدی.
    اگر ردیف نباشد TASK_FOLLOW_UP_NOT_FOUND است.
""".strip()

LIST_TASK_FOLLOW_UPS = """
پیگیری‌های یک وظیفه را می‌خواند؛ فقط اگر خودتان عضو فعال
پروژهٔ همان وظیفه باشید.

مجوز لازم:
    TaskFollowUp/Read و عضویت فعال در پروژهٔ همان وظیفه.

ورودی اجباری:
    task_id.

ورودی اختیاری:
    limit و offset.

خروجی:
    JSON با records مرتب از جدید به قدیم. فهرست خالی خطا نیست.
""".strip()

CREATE_EXTERNAL_CONTACT = """
یک مخاطب خارج از سامانه را در جدول external_contacts ثبت می‌کند.

چرا این ابزار:
    کسانی که فقط پیام یا یادآوری می‌گیرند نباید حساب users داشته باشند.
    فقط INSERT روی external_contacts است؛ ردیف users ساخته نمی‌شود.

مجوز لازم:
    Message/Create برای کاربر جاری.

ورودی اجباری:
    name.

ورودی اختیاری:
    phone، email، telegram_id، is_active (پیش‌فرض true).

خروجی:
    JSON با status برابر success، id شناسه جدید، و message.
    مقدار یکتا تکراری INVALID_INPUT است.
    ارسال واقعی تلگرام/SMS در این گام نیست.
""".strip()

GET_EXTERNAL_CONTACT = """
یک مخاطب خارجی را با شناسه از external_contacts می‌خواند.

مجوز لازم:
    Message/Read برای کاربر جاری.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با نام و راه‌های تماس.
    اگر ردیف نباشد EXTERNAL_CONTACT_NOT_FOUND است.
""".strip()

LIST_EXTERNAL_CONTACTS = """
مخاطبان خارج از سامانه را با صفحه‌بندی می‌خواند.

مجوز لازم:
    Message/Read برای کاربر جاری.

ورودی اختیاری:
    limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

CREATE_CHAT = """
یک گفتگو در جدول chats می‌سازد؛ خصوصی یا روی پروژه.

چرا این ابزار:
    پیام داخل گفتگو است. سازنده همان لحظه عضو chat_members می‌شود
    تا گفتگو بدون عضو نماند.

قانون پروژه:
    گفتگوی پروژه باید project_id داشته باشد و سازنده عضو فعال همان
    پروژه باشد. گفتگوی خصوصی project_id ندارد.

مجوز لازم:
    Message/Create برای کاربر جاری.
    اگر project_id بیاید، عضویت فعال همان پروژه هم لازم است.

ورودی اجباری:
    title، و نوع (chat_type یا chat_type_id).
    نام lookup از seed است؛ مثل گفتگوی پروژه یا گفتگوی خصوصی.

ورودی اختیاری:
    project_id.

خروجی:
    JSON با id گفتگوی جدید.
""".strip()

GET_CHAT = """
یک گفتگو را با شناسه می‌خواند؛ فقط اگر کاربر جاری عضو همان گفتگو باشد.

مجوز لازم:
    Message/Read و عضویت در همان گفتگو.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با عنوان، نوع و project_id.
    اگر ردیف نباشد CHAT_NOT_FOUND است.
    اگر عضو نباشد PERMISSION_DENIED است.
""".strip()

LIST_CHATS = """
گفتگوهایی را فهرست می‌کند که کاربر جاری عضوشان است.

غیرعضو چت، گفتگوی دیگران را نمی‌بیند.

مجوز لازم:
    Message/Read برای کاربر جاری.
    اگر project_id بیاید، عضویت فعال همان پروژه هم لازم است.

ورودی اختیاری:
    project_id، limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

CREATE_CHAT_MEMBER = """
یک کاربر سامانه را به یک گفتگو اضافه می‌کند.

عضو گفتگو فقط از users است؛ مخاطب خارجی اینجا اضافه نمی‌شود.

اگر گفتگو به پروژه وصل باشد، کاربر جدید باید عضو فعال همان پروژه باشد.

مجوز لازم:
    Message/Create و عضویت خودتان در همان گفتگو.

ورودی اجباری:
    chat_id، user_id.

خروجی:
    JSON با id ردیف chat_members.
    عضو تکراری INVALID_INPUT است.
""".strip()

LIST_CHAT_MEMBERS = """
اعضای یک گفتگو را می‌خواند؛ فقط اگر خودتان عضو همان گفتگو باشید.

مجوز لازم:
    Message/Read و عضویت در همان گفتگو.

ورودی اجباری:
    chat_id.

ورودی اختیاری:
    limit و offset.
""".strip()

CREATE_MESSAGE = """
یک پیام متنی در جدول messages می‌فرستد و گیرنده‌ها را همان لحظه می‌سازد.

چرا این ابزار:
    متن در text است. content_id در این گام نوشته نمی‌شود.
    جدول message_recipients منبع حقیقت گیرنده است؛ این ابزار
    ردیف‌هایش را می‌سازد تا دو ابزار پشت سر هم لازم نباشد.

قانون گیرنده:
    حداقل یک گیرنده لازم است.
    recipient_user_id و recipient_external_contact_id اگر هر دو بیایند
    دو ردیف جدا می‌سازند. کاربر گیرنده باید عضو همین گفتگو باشد.
    مخاطب خارجی عضو چت نیست.

مجوز لازم:
    Message/Create و عضویت در همان گفتگو.

ورودی اجباری:
    chat_id، text،
    و حداقل یکی از recipient_user_id یا recipient_external_contact_id.
    در گفتگوی پروژه task_id اختیاری است و اگر بیاید باید در همان پروژه باشد.
    در گفتگوی خصوصی task_id نمی‌آید.

خروجی:
    JSON با id پیام جدید.
    بدون گیرنده یا متن خالی INVALID_INPUT است.
    نبود عضویت PERMISSION_DENIED است.
""".strip()

GET_MESSAGE = """
یک پیام را با شناسه می‌خواند؛ فقط اگر عضو گفتگوی همان پیام باشید.

مجوز لازم:
    Message/Read و عضویت در گفتگوی همان پیام.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با متن، تسک و فرستنده. content_id در پاسخ نیست.
    اگر ردیف نباشد MESSAGE_NOT_FOUND است.
""".strip()

LIST_MESSAGES = """
پیام‌هایی را فهرست می‌کند که روی گفتگوهای عضو بودن کاربر جاری‌اند.

غیرعضو چت پیام‌ها را در فهرست نمی‌بیند.

مجوز لازم:
    Message/Read برای کاربر جاری.
    اگر chat_id بیاید، عضویت همان گفتگو هم لازم است.

ورودی اختیاری:
    chat_id، limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

CREATE_MESSAGE_RECIPIENT = """
یک گیرنده به یک پیام موجود در message_recipients اضافه می‌کند.

قانون XOR:
    دقیقاً یکی از user_id یا external_contact_id باید بیاید.
    هر دو پر یا هر دو خالی قبل از INSERT رد می‌شود.

مجوز لازم:
    Message/Create و عضویت در گفتگوی همان پیام.

ورودی اجباری:
    message_id، و دقیقاً یکی از user_id یا external_contact_id.

خروجی:
    JSON با id ردیف جدید.
    نقض XOR با INVALID_INPUT است.
""".strip()

LIST_MESSAGE_RECIPIENTS = """
گیرنده‌های یک پیام را می‌خواند؛ فقط اگر عضو گفتگوی همان پیام باشید.

مجوز لازم:
    Message/Read و عضویت در گفتگوی همان پیام.

ورودی اجباری:
    message_id.

ورودی اختیاری:
    limit و offset.
""".strip()

LIST_NOTIFICATIONS = """
اعلان‌های داخل پنل خود کاربر جاری را از جدول notifications می‌خواند.

چرا این ابزار:
    اعلان با ممیزی فرق دارد: اینجا خبر رسیده به همین کاربر است،
    نه اینکه چه کسی موجودیت را عوض کرد. با execution_logs هم
    فرق دارد؛ آن تاریخچهٔ ارسال واقعی یادآوری است.

محدوده:
    فقط ردیف‌هایی که user_id برابر کاربر جاری است.
    کاربر دیگر اعلان شما را در فهرست نمی‌بیند.

مجوز لازم:
    کاربر جاری فعال. مجوز Resource/Action جدا برای صندوق اعلان نیست.

ورودی اختیاری:
    is_read برای فقط خوانده یا نخوانده، limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records شامل نوع seed مثل وظیفه جدید، عنوان، متن در
    message، و is_read. content_id در پاسخ نیست.
    فهرست خالی خطا نیست.
""".strip()

GET_NOTIFICATION = """
یک اعلان داخل پنل را با شناسه می‌خواند؛ فقط اگر مال خودتان باشد.

مجوز لازم:
    کاربر جاری فعال و مالک همان ردیف.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با نوع، عنوان، متن و is_read.
    اگر ردیف نباشد NOTIFICATION_NOT_FOUND است.
    اگر مال کاربر دیگر باشد PERMISSION_DENIED است.
""".strip()

MARK_NOTIFICATION_READ = """
اعلان خود کاربر را خوانده می‌کند؛ is_read را true می‌گذارد.

ساختن اعلان از چت نیست؛ create_task و create_project_member
خودشان اعلان می‌نویسند.

مجوز لازم:
    کاربر جاری فعال و مالک همان ردیف.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با id همان اعلان.
    اعلان دیگران PERMISSION_DENIED است.
""".strip()

LIST_AUDIT_LOGS = """
ردیف‌های ممیزی را از جدول audit_logs می‌خواند.

چرا این ابزار:
    ممیزی می‌گوید چه کسی کدام موجودیت را عوض کرد.
    مثال: علی وضعیت Task ۲۵ را از «در حال انجام» به «تکمیل شده» برد.
    old_value و new_value همان مقدار قدیم و جدیدند.
    با notifications و execution_logs قاطی نشود.

ساختن دستی:
    ابزار create_audit_log برای کاربر عادی نیست؛ نوشتن اثر جانبی
    همان ابزارهای قبلی است.

مجوز لازم:
    AuditLog/Read برای کاربر جاری؛ معمولاً مدیر کل یا ناظر.

ورودی اختیاری:
    entity مثل Task، entity_id، user_id عامل، limit و offset.

خروجی:
    JSON با records شامل action و entity و مقدار قدیم/جدید.
    فهرست خالی خطا نیست.
""".strip()

GET_AUDIT_LOG = """
یک ردیف ممیزی را با شناسه می‌خواند.

مجوز لازم:
    AuditLog/Read برای کاربر جاری.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با action، entity، entity_id، old_value و new_value.
    اگر ردیف نباشد AUDIT_LOG_NOT_FOUND است.
""".strip()

CREATE_PERFORMANCE_ACTION = """
یک تشویق یا تنبیه روی کاربر در performance_actions ثبت می‌کند.

چرا این ابزار:
    ارزیابی افراد رویداد جدا است؛ روی User فیلد Reward/Penalty
    نمی‌گذاریم. امتیاز به performance_scores می‌رود. اگر مبلغ نقدی
    باشد همان لحظه تراکنش با نوع پاداش یا جریمه ساخته می‌شود.

مجوز لازم:
    Performance/Create برای کاربر جاری.
    اگر project_id بیاید عضو فعال همان پروژه هم لازم است.

ورودی اجباری:
    user_id، reason، و نوع با action_type یا action_type_id
    مثل تقدیر، پاداش نقدی، اخطار، جریمه.

ورودی اختیاری:
    project_id، score، amount و account_id.
    امتیاز بدون مبلغ مجاز است. مبلغ بدون حساب رد می‌شود.

خروجی:
    JSON با status برابر success و id اقدام جدید.
    reason خالی INVALID_INPUT است. نبود مجوز PERMISSION_DENIED است.

زنجیره فراخوانی:
    1. require_permission Performance/Create
    2. اگر پروژه باشد require_active_project_member
    3. validate_create_performance_action
    4. insert_performance_action — اقدام، امتیاز، تراکنش نقدی
    5. format_success یا format_error

طراحی:
    ابزار جدا برای نوع و برای performance_scores نیست.
    داشبورد رتبه در stats و جلسه در این گام نیستند.
""".strip()

GET_PERFORMANCE_ACTION = """
یک اقدام تشویق یا تنبیه را با شناسه می‌خواند.

مجوز لازم:
    Performance/Read برای کاربر جاری.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با امتیاز، مبلغ، نوع، دلیل و financial_transaction_id.
    اگر ردیف نباشد PERFORMANCE_ACTION_NOT_FOUND است.
""".strip()

LIST_PERFORMANCE_ACTIONS = """
اقدام‌های تشویق و تنبیه را با صفحه‌بندی می‌خواند.

چرا این ابزار:
    فهرست یک کاربر امتیاز و مبلغ را جدا نشان می‌دهد.
    جمع performance_scores همان کاربر باید با مجموع امتیاز
    اقدام‌ها یکی باشد.

مجوز لازم:
    Performance/Read برای کاربر جاری.

ورودی اختیاری:
    user_id، project_id، limit و offset.

خروجی:
    JSON با records شامل score و amount جدا، type_name و type_category.
    فهرست خالی خطا نیست. داشبورد رتبه اینجا نیست.
""".strip()

CREATE_CONTENT = """
متن یا متادیتای صوت، تصویر و فایل را در contents ثبت می‌کند.

چرا این ابزار:
    محتوا زیرساخت مشترک است؛ جلسه، گزارش و پیام به همین ردیف وصل می‌شوند.
    آپلود واقعی روی S3 نیست. storage_key مسیر منطقی فایل است.

مجوز لازم:
    Content/Create برای کاربر جاری.

ورودی اجباری:
    نوع با content_kind یا content_kind_id
    (TEXT/متن، VOICE/صوت، IMAGE/تصویر یا FILE/فایل).
    برای TEXT فیلد text_body.
    برای VOICE و IMAGE و FILE فیلدهای storage_key، original_filename،
    mime_type و file_size_bytes.

ورودی اختیاری:
    برای فایل‌ها متن caption در text_body و duration_seconds.

خروجی:
    JSON با id محتوای جدید.
""".strip()

GET_CONTENT = """
یک محتوا را با شناسه از contents می‌خواند.

مجوز لازم:
    Content/Read برای کاربر جاری.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با نوع، متن، و در صورت فایل متادیتای media_files.
    اگر ردیف نباشد CONTENT_NOT_FOUND است.
""".strip()

LIST_CONTENTS = """
محتواهای فعال خود کاربر جاری را از جدید به قدیم فهرست می‌کند.

مجوز لازم:
    Content/Read برای کاربر جاری.

ورودی اختیاری:
    limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records شامل نوع، متن، و در صورت صوت متادیتای فایل.
    فهرست خالی خطا نیست. محتوای حذف‌شده نمی‌آید.
""".strip()

DELETE_CONTENT = """
یک محتوا را نرم‌حذف می‌کند تا در فهرست و خواندن دیده نشود.

مجوز لازم:
    Content/Delete برای کاربر جاری.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با id. ردیف در پایگاه می‌ماند و is_active خاموش می‌شود.
    اگر به project_documents وصل باشد حذف رد می‌شود.
    اگر ردیف نباشد یا قبلاً حذف شده باشد CONTENT_NOT_FOUND است.
""".strip()

SAVE_TEXT_ANALYSIS = """
خروجی استخراج NER را در جداول تحلیل متن PostgreSQL ذخیره می‌کند.

چرا این ابزار:
    NER فقط‌خواندنی است و INSERT ندارد. ثبت ذکر، موجودیت canonical،
    موضوع، قطبیت، هیجان، ژانر پیام، نیت و صنعت بیان مال CRUD است. وضعیت موجودیت
    پیشنهادی است تا نمایش استخراج برای بررسی دقت باقی بماند.

مجوز لازم:
    TextAnalysis/Create برای کاربر جاری.
    برای message عضویت گفتگو،
    برای meeting دسترسی جلسه، برای content سازنده همان محتوا.

ورودی اجباری:
    source_type یکی از meeting / message / content.

ورودی بر اساس منبع:
    برای meeting و message فیلد source_id.
    برای content یا source_id یا text؛ اگر فقط text باشد یک ردیف
    contents از نوع TEXT ساخته می‌شود.

ورودی اختیاری:
    model نام مدل استخراج، mentions، topics، sentiment، emotions،
    discourses، intents، rhetorics، facts، quotes، keywords. هر لایه شاهد mention_text را هم می‌نویسد.
    intents.slots اجزای پرشدهٔ نیت است. discourses.slots نقش ژانر
    است. rhetorics صنعت بیان است و intended_meaning بازنویسیٔ صریح غرض.
    facts مقدار، درصد، نقش total/part/remainder و صراحت explicit/derived
    را روی همان تحلیل می‌نویسد. quotes گوینده، شیوه مستقیم/غیرمستقیم،
    متن نقل، شاهد و آفست را روی همان تحلیل می‌نویسد.
    keywords عبارت کلیدی است: جدول keywords عبارت canonical،
    keyword_mentions ذکر روی همان متن خام با پروژه و صاحب متن.
    اگر ژانر discovered باشد نوع نو در discourse_types ساخته
    می‌شود.

خروجی:
    JSON با id تحلیل، mentions با شناسه ردیف، entities، keywords، topics،
    sentiment، emotions، discourses، intents، rhetorics، facts و quotes. شاهد هر لایه در
    mention_text است. status موجودیت‌ها candidate است.
    خطای اعتبارسنجی INVALID_INPUT است.
""".strip()

GET_TEXT_ANALYSIS = """
یک اجرای تحلیل متن را با ذکرها و موضوع و احساس و ژانر و نیت و بیان و فکت و نقل‌قول و کلمهٔ کلیدی می‌خواند.

مجوز لازم:
    TextAnalysis/Read و دسترسی به همان منبع عملیاتی.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با mentions، entities، keywords، topics، sentiment، emotions،
    discourses، intents، rhetorics، facts و quotes؛ شاهد هر لایه در mention_text است.
    اجزای نیت در intents.slots است. نقش ژانر در discourses.slots
    است. معنای مقصود در intended_meaning و rhetorics است.
    نوع کشف‌شده is_discovered دارد.
    اگر ردیف نباشد TEXT_ANALYSIS_NOT_FOUND است.
""".strip()

LIST_TEXT_ANALYSES = """
تحلیل‌های متن ساخته‌شده توسط کاربر جاری را با صفحه‌بندی می‌خواند.

مجوز لازم:
    TextAnalysis/Read برای کاربر جاری.

ورودی اختیاری:
    source_type، source_id، limit و offset.

خروجی:
    JSON با records شامل تعداد ذکر و موضوع و ژانر و نیت و فکت و نقل‌قول و کلمهٔ کلیدی.
    فهرست خالی خطا نیست.
""".strip()

CREATE_ISSUE = """
یک مسئله پروژه را در issues ثبت می‌کند و تحلیل متن را در issue_sources وصل می‌کند.

چرا این ابزار:
    extract_frame در nlp فقط‌خواندنی است و INSERT ندارد. عنوان و پروژه
    و وضعیت seed مال CRUD است. وضعیت پیش‌فرض «جدید» است. علت، وظیفه،
    اهمیت، فوریت و شدت در این گام نوشته نمی‌شوند. علت با ابزار جدا
    link_issue_cause است. وظیفه با create_task و link_issue_task است.
    امتیاز با set_issue_importance و set_issue_urgency و
    set_issue_severity و add_issue_impact است. موضوع و موجودیت NER
    با link_issue_topic و link_issue_entity است. اگر همین عنوان در
    همین پروژه باشد ردیف جدید ساخته نمی‌شود و تحلیل در issue_sources
    به همان مسئله وصل می‌گردد.

مجوز لازم:
    Issue/Create و عضویت فعال همان پروژه.
    برای analysis_id دسترسی به همان منبع عملیاتی تحلیل.

ورودی اجباری:
    project_id، title، analysis_id.

ورودی اختیاری:
    status نام یا کد seed مثل جدید / new، یا status_id.

خروجی:
    JSON با id مسئله، وضعیت، و sources شامل analysis_id.
    اگر تحلیل نباشد TEXT_ANALYSIS_NOT_FOUND است.
""".strip()

GET_ISSUE = """
یک مسئله را با شناسه از issues و منابع تحلیل می‌خواند.

مجوز لازم:
    Issue/Read و عضویت فعال پروژهٔ همان مسئله.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با عنوان، پروژه، وضعیت seed، sources، causes، tasks،
    importance، urgency، severity، impacts، topics و entities.
    اگر ردیف نباشد ISSUE_NOT_FOUND است.
""".strip()

LIST_ISSUES = """
مسائل قابل‌مشاهدهٔ کاربر جاری را با صفحه‌بندی می‌خواند.

مجوز لازم:
    Issue/Read برای کاربر جاری.

ورودی اختیاری:
    project_id، limit و offset.

خروجی:
    JSON با records شامل analysis_ids و causes و tasks و امتیاز و
    topics و entities هر مسئله.
    فهرست خالی خطا نیست.
""".strip()

LINK_ISSUE_CAUSE = """
دو مسئله را در issue_causes وصل می‌کند: مسئله ← علت، با سطح علت یا ریشه.

چرا این ابزار:
    فکت kind برابر cause در nlp فقط استخراج است. علت خودش یک مسئله است،
    نه فیلد متنی روی کارت معلول. سطح seed برابر cause یا root_cause است.
    زنجیره با چند ردیف ساخته می‌شود. وظیفه با link_issue_task است.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ هر دو مسئله.
    هر دو مسئله باید در یک پروژه باشند.

ورودی اجباری:
    issue_id مسئلهٔ معلول، cause_issue_id مسئلهٔ علت.

ورودی اختیاری:
    cause_level نام یا کد seed مثل علت / cause یا ریشه / root_cause،
    یا cause_level_id. پیش‌فرض «علت».

خروجی:
    JSON با id حلقه، cause_title و cause_level_code.
    خودوصل INVALID_INPUT است. جفت تکراری هم INVALID_INPUT است.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
""".strip()

LINK_ISSUE_TASK = """
مسئله را به وظیفهٔ موجود در issue_tasks وصل می‌کند.

چرا این ابزار:
    اقدام استخراج‌شده بعد از تأیید با create_task در tasks ثبت می‌شود.
    اینجا فقط لینک نازک است؛ وظیفه ساخته نمی‌شود. همان تحلیل مسئله
    در analysis_outputs با نوع task به tasks.id وصل می‌گردد.
    اهمیت، فوریت، شدت و issue_impacts اینجا نیستند؛ بعد از وصل وظیفه
    با set_issue_importance و set_issue_urgency و set_issue_severity
    و add_issue_impact نوشته می‌شوند.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ مسئله.
    وظیفه باید در همان پروژه باشد.

ورودی اجباری:
    issue_id، task_id.

خروجی:
    JSON با id حلقه، task_title و analysis_ids.
    جفت تکراری INVALID_INPUT است.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
    اگر وظیفه نباشد TASK_NOT_FOUND است.
""".strip()

SET_ISSUE_IMPORTANCE = """
اهمیت مسئله را از کاتالوگ task_importances در issue_importances می‌نویسد.

چرا این ابزار:
    وظیفه از قبل importance دارد؛ مسئله جدا است. حدس LLM نیست؛
    نام seed مثل زیاد کافی است. همان مقدار روی تحلیل مبدأ در
    text_analysis_importances نوشته می‌شود تا با کارت مسئله یکی بماند.
    موضوع و موجودیت اینجا نیست.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ مسئله.

ورودی اجباری:
    issue_id، و importance نام seed یا importance_id.

خروجی:
    JSON با importance_name و analysis_ids.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
""".strip()

SET_ISSUE_URGENCY = """
فوریت مسئله را از کاتالوگ task_priorities در issue_urgencies می‌نویسد.

چرا این ابزار:
    فوریت مسئله معمولاً همان اولویت وظیفهٔ وصل‌شده است. حدس LLM نیست.
    همان مقدار روی تحلیل مبدأ در text_analysis_urgencies نوشته می‌شود.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ مسئله.

ورودی اجباری:
    issue_id، و priority نام seed یا priority_id.

خروجی:
    JSON با priority_name و analysis_ids.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
""".strip()

SET_ISSUE_SEVERITY = """
شدت مسئله را از کاتالوگ severity_levels در issue_severities می‌نویسد.

چرا این ابزار:
    شدت از اهمیت و فوریت جدا است. حدس LLM نیست؛ نام یا کد seed
    مثل متوسط / medium کافی است. یادآوری اینجا ارسال نمی‌شود.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ مسئله.

ورودی اجباری:
    issue_id، و severity نام یا کد seed یا severity_id.

خروجی:
    JSON با severity_name و severity_code.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
""".strip()

ADD_ISSUE_IMPACT = """
یک اثر مسئله را با نوع از impact_types در issue_impacts می‌نویسد.

چرا این ابزار:
    اثر می‌گوید مسئله به زمان/هزینه/کیفیت/منابع انسانی چه می‌زند.
    هر فراخوانی یک نوع است. حدس LLM نیست؛ نام یا کد seed مثل
    کیفیت / quality یا منابع انسانی / hr کافی است.
    موضوع و موجودیت NER اینجا وصل نمی‌شود.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ مسئله.

ورودی اجباری:
    issue_id، و impact_type نام یا کد seed یا impact_type_id.

ورودی اختیاری:
    description؛ اگر نیاید نام نوع seed نوشته می‌شود.

خروجی:
    JSON با impact_type_name و description.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
""".strip()

LINK_ISSUE_TOPIC = """
موضوع ذخیره‌شدهٔ NER را در issue_topics به مسئله وصل می‌کند.

چرا این ابزار:
    موضوع روی text_analyses است نه روی خود مسئله. بدون این وصل هر
    گزارش یک تحلیل جدا می‌ماند. منبع همان text_analysis_topics است؛
    استخراج جدید نیست. فکت عددی و entity_relations اینجا نیستند.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ مسئله.
    موضوع باید روی یکی از تحلیل‌های issue_sources همین مسئله باشد.

ورودی اجباری:
    issue_id، و topic کد یا نام seed یا topic_id.

خروجی:
    JSON با topic_code و topic_name.
    جفت تکراری INVALID_INPUT است.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
""".strip()

LINK_ISSUE_ENTITY = """
موجودیت ذخیره‌شدهٔ NER را با نقش seed در issue_entities به مسئله وصل می‌کند.

چرا این ابزار:
    موجودیت روی ذکرهای تحلیل است نه روی کارت مسئله. نقش از
    issue_entity_roles است: مسئول / responsible، متأثر / affected،
    ذکرشده / mentioned. استخراج جدید، entity_relations و یادآوری
    اینجا نیستند.

مجوز لازم:
    Issue/Create و عضویت فعال پروژهٔ مسئله.
    موجودیت باید در ذکرهای یکی از تحلیل‌های مبدأ مسئله باشد.

ورودی اجباری:
    issue_id، entity_id.

ورودی اختیاری:
    role نام یا کد seed یا role_id. پیش‌فرض «ذکرشده».

خروجی:
    JSON با canonical_name، entity_type و role_code.
    جفت تکراری با همان نقش INVALID_INPUT است.
    اگر مسئله نباشد ISSUE_NOT_FOUND است.
""".strip()
