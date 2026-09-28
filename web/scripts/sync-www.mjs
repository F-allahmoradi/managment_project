import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const www = join(webRoot, "www");

const pages = [
  "admin-mobile.html",
  "mobile-auth.html",
  "meetings.html",
  "calendar.html",
  "new-meeting.html",
  "meeting-details.html",
  "projects.html",
  "new-project-mobile.html",
  "project-details.html",
  "project-team.html",
  "project-note.html",
  "members-groups.html",
  "tasks.html",
  "task-details.html",
  "chats.html",
  "chat.html",
  "progress.html",
  "reports.html",
  "embedding.html",
  "semantic.html",
  "raw-comment.html",
  "notifications.html",
];

const assets = ["mobile-app.js", "mobile-session.js", "mobile-ui.css", "mobile-shell.css"];

rmSync(www, { recursive: true, force: true });
mkdirSync(www, { recursive: true });

for (const name of pages.concat(assets)) {
  cpSync(join(webRoot, name), join(www, name));
}
cpSync(join(webRoot, "fonts"), join(www, "fonts"), { recursive: true });

writeFileSync(
  join(www, "index.html"),
  `<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>سامانه مدیریت</title>
  <script>
    var token = "";
    try { token = localStorage.getItem("management_access_token") || ""; } catch (error) {}
    location.replace(token ? "admin-mobile.html" : "mobile-auth.html");
  </script>
</head>
<body></body>
</html>
`
);

function publicApiBase() {
  const fromEnv = String(process.env.MANAGEMENT_PUBLIC_URL || "").trim().replace(/\/+$/, "");
  if (fromEnv) {
    return fromEnv;
  }
  try {
    const line = readFileSync(join(webRoot, "mobile-api-base.txt"), "utf8")
      .split(/\r?\n/)
      .map((item) => item.trim())
      .find((item) => item && !item.startsWith("#"));
    return String(line || "").replace(/\/+$/, "");
  } catch (ignored) {
    return "";
  }
}

const baked = publicApiBase();
if (baked) {
  if (!/^https?:\/\/\S+$/i.test(baked)) {
    throw new Error("MANAGEMENT_PUBLIC_URL باید با http:// یا https:// شروع شود");
  }
  const sessionPath = join(www, "mobile-session.js");
  const source = readFileSync(sessionPath, "utf8");
  const marker = /var BAKED_API_BASE = .*?;/;
  if (!marker.test(source)) {
    throw new Error("نشان BAKED_API_BASE در mobile-session.js پیدا نشد");
  }
  const next = source.replace(marker, "var BAKED_API_BASE = " + JSON.stringify(baked) + ";");
  writeFileSync(sessionPath, next);
  console.log("آدرس APK:", baked);
} else {
  console.log("آدرس APK خالی است؛ فقط برای تست شبکهٔ محلی فیلد ورود دیده می‌شود");
}

const extras = readdirSync(webRoot).filter((name) => name.endsWith(".html") && !pages.includes(name) && name !== "index.html");
if (extras.length) {
  console.log("صفحات خارج از APK:", extras.join(", "));
}
console.log("www آماده شد");
