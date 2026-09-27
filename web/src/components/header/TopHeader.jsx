import { useEffect, useState } from "react";
import { formatJalaliStamp } from "@/lib/jalali.js";
import {
  CalendarIcon,
  ChartIcon,
  FullscreenIcon,
  GearIcon,
  HeaderBellIcon,
  MenuIcon,
  NetworkLogo,
  UserSilhouette,
} from "@/components/icons/index.jsx";
import "./header.css";

export default function TopHeader({ menuOpen, onToggleMenu, user, onLogout }) {
  const [stamp, setStamp] = useState(() => formatJalaliStamp());
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    const id = setInterval(() => setStamp(formatJalaliStamp()), 60_000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onChange = () => setFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  const toggleFullscreen = async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await document.documentElement.requestFullscreen();
      }
    } catch {
      /* ignore */
    }
  };

  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || "کاربر";
  const roleLabel = user?.roles?.length ? user.roles.join("، ") : "بدون نقش";

  return (
    <header className="topbar">
      <div className="topbar-start">
        <div className="topbar-user">
          <span className="topbar-avatar" aria-hidden="true">
            <UserSilhouette />
          </span>
          <span className="topbar-user-copy">
            <strong>{fullName}</strong>
            <em>{roleLabel}</em>
          </span>
        </div>
        <button className="logout-btn" type="button" onClick={onLogout}>
          خروج
        </button>
        <button
          className="menu-btn"
          type="button"
          aria-label="گزارش‌ها"
          aria-expanded={menuOpen}
          onClick={onToggleMenu}
        >
          <MenuIcon />
        </button>
        <div className="topbar-actions">
          <button className="icon-btn" type="button" aria-label="اعلان‌ها">
            <HeaderBellIcon />
            <span className="icon-badge" />
          </button>
          <button className="icon-btn" type="button" aria-label="تنظیمات">
            <GearIcon />
          </button>
          <button
            className="icon-btn"
            type="button"
            aria-label={fullscreen ? "خروج از تمام‌صفحه" : "تمام‌صفحه"}
            onClick={toggleFullscreen}
          >
            <FullscreenIcon />
          </button>
        </div>
      </div>

      <div className="topbar-brand">
        <div className="brand-row">
          <NetworkLogo />
          <div className="topbar-titles">
            <h1>سامانه هوشمند مدیریت سازمان</h1>
            <p>همراه شما در تصمیم‌گیری‌های بهتر با داده‌های دقیق و تحلیل‌های هوشمند</p>
          </div>
        </div>
      </div>

      <div className="topbar-end">
        <div className="date-box">
          <CalendarIcon />
          {stamp}
        </div>
        <button className="feedback-btn" type="button">
          <ChartIcon />
          ثبت بازخوردی
        </button>
      </div>
    </header>
  );
}
