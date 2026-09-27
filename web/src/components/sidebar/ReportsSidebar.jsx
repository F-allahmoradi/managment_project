import { useState } from "react";
import { MEDIA_TABS, QUICK_ACTIONS, RECENT_REPORTS } from "@/data/dashboard.js";
import {
  ACTION_ICONS,
  ArrowLeftIcon,
  ChevronDownIcon,
  DotsIcon,
  KindIcon,
  SendIcon,
  ShieldCheckIcon,
  TAB_ICONS,
} from "@/components/icons/index.jsx";
import "./sidebar.css";

const tabIcons = TAB_ICONS();
const actionIcons = ACTION_ICONS();

export default function ReportsSidebar({ open, onClose }) {
  const [tab, setTab] = useState("text");
  const [draft, setDraft] = useState("");

  return (
    <aside className={`sidebar${open ? " is-open" : ""}`}>
      <div className="sidebar-head">
        <div className="sidebar-title">
          <ShieldCheckIcon />
          <h2>گزارش نویسی و ارتباطات</h2>
        </div>
        <button className="sidebar-close" type="button" aria-label="بستن" onClick={onClose}>
          ×
        </button>
      </div>

      <div className="media-tabs">
        {MEDIA_TABS.map((item) => {
          const Icon = tabIcons[item.icon];
          return (
            <button
              key={item.id}
              type="button"
              className={`media-tab${tab === item.id ? " is-active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              <Icon />
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="composer">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="گزارش خود را اینجا بنویسید..."
        />
        <ChevronDownIcon className="composer-chevron" />
        <button className="send-btn" type="button" aria-label="ارسال">
          <SendIcon />
        </button>
      </div>

      <div className="quick-actions">
        {QUICK_ACTIONS.map((item) => {
          const Icon = actionIcons[item.icon];
          return (
            <button key={item.id} type="button" className="quick-btn">
              <Icon />
              {item.label}
            </button>
          );
        })}
      </div>

      <h3 className="recent-title">گزارش‌های اخیر</h3>
      <ul className="recent-list">
        {RECENT_REPORTS.map((item) => (
          <li key={item.id} className={`recent-item is-${item.kind}`}>
            <span className={`recent-ico is-${item.kind}`}>
              <KindIcon kind={item.kind} />
            </span>
            <span className="recent-copy">
              <strong>{item.title}</strong>
              <em>{item.date}</em>
            </span>
            <span className={`recent-badge is-${item.kind}`}>{item.badge}</span>
            <button className="recent-menu" type="button" aria-label="گزینه‌ها">
              <DotsIcon />
            </button>
          </li>
        ))}
      </ul>

      <button className="view-all" type="button" onClick={onClose}>
        مشاهده همه گزارش‌ها
        <ArrowLeftIcon />
      </button>
    </aside>
  );
}
