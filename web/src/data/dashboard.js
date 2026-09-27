export const FEATURES = [
  {
    id: "projects",
    rgb: "0, 180, 255",
    color: "#00b4ff",
    colorEnd: "#0066cc",
    title: "پروژه‌های من",
    description: "مدیریت، پیگیری و مشاهده پروژه‌های جاری و تکمیل‌شده",
    figure: "documents",
    badge: "folder",
  },
  {
    id: "meetings",
    rgb: "191, 0, 255",
    color: "#bf00ff",
    colorEnd: "#9900cc",
    title: "جلسات من",
    description: "برنامه‌ریزی، گزارش و پیگیری\nجلسات سازمانی",
    figure: "calendar",
    badge: "calendar",
  },
  {
    id: "reports",
    rgb: "0, 255, 204",
    color: "#00ffcc",
    colorEnd: "#00cc99",
    title: "گزارش‌های من",
    description: "ثبت، مدیریت و دسترسی به\nگزارش‌های سازمانی",
    figure: "chartDoc",
    badge: "document",
  },
  {
    id: "members",
    rgb: "255, 0, 255",
    color: "#ff00ff",
    colorEnd: "#cc00cc",
    title: "اعضای سازمان من",
    description: "مدیریت، اعضا، گروه‌ها و ساختار\nسازمانی",
    figure: "users",
    badge: "users",
  },
  {
    id: "followups",
    rgb: "0, 204, 255",
    color: "#00ccff",
    colorEnd: "#0099ff",
    title: "پیگیری‌های من",
    description: "پیگیری و درخواست‌ها، امور و\nوظایف سازمانی",
    figure: "target",
    badge: "target",
  },
  {
    id: "notifications",
    rgb: "255, 153, 0",
    color: "#ff9900",
    colorEnd: "#ff6600",
    title: "اعلان‌های من",
    description: "دریافت و مدیریت اعلان‌ها\nو رویدادها",
    figure: "bell",
    badge: "bell",
    count: 3,
  },
];

export const MEDIA_TABS = [
  { id: "text", label: "متن", icon: "text" },
  { id: "audio", label: "صوت", icon: "audio" },
  { id: "video", label: "فیلم", icon: "video" },
  { id: "file", label: "فایل", icon: "file" },
];

export const QUICK_ACTIONS = [
  { id: "voice", label: "ضبط صدا", icon: "mic" },
  { id: "video", label: "ضبط فیلم", icon: "video" },
  { id: "file", label: "ضمیمه فایل", icon: "clip" },
];

export const RECENT_REPORTS = [
  {
    id: "r1",
    title: "گزارش جلسه شورای هماهنگی",
    date: "۱۴۰۴/۰۷/۲۳ - ۰:۳۴",
    kind: "text",
    badge: "متن",
  },
  {
    id: "r2",
    title: "ویدیوی بازدید میدانی",
    date: "۱۴۰۴/۰۷/۲۱ - ۱۵:۶",
    kind: "video",
    badge: "فیلم",
  },
  {
    id: "r3",
    title: "یادداشت صوتی",
    date: "۱۴۰۴/۰۷/۲۰ - ۰:۱۲",
    kind: "audio",
    badge: "صوت",
  },
  {
    id: "r4",
    title: "فایل تحلیلی پروژه",
    date: "۱۴۰۴/۰۷/۱۸ - ۱۴:۴۸",
    kind: "file",
    badge: "فایل",
  },
];

export const DOCK_ITEMS = [
  { id: "analytics", label: "تحلیل داده‌ها", sublabel: "تصمیم‌گیری بهتر", icon: "brain" },
  { id: "teams", label: "هماهنگی تیم‌ها", sublabel: "عملکرد بالاتر", icon: "users" },
  { id: "goals", label: "دستیابی به اهداف", sublabel: "آینده‌ای روشن‌تر", icon: "target" },
  { id: "security", label: "امنیت اطلاعات", sublabel: "اعتماد بیشتر", icon: "shield" },
];
