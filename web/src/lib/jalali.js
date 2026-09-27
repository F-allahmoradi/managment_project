export function formatJalaliStamp(date = new Date()) {
  const weekday = new Intl.DateTimeFormat("fa-IR", { weekday: "long" }).format(date);
  const parts = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const get = (type) => parts.find((part) => part.type === type)?.value ?? "";
  return `${get("year")}/${get("month")}/${get("day")} ${weekday}`;
}
