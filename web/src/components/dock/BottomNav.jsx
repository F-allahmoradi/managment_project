import { DOCK_ITEMS } from "@/data/dashboard.js";
import { NAV_ICONS } from "@/components/icons/index.jsx";
import "./dock.css";

export default function BottomNav() {
  return (
    <nav className="dock" aria-label="میانبرهای سامانه">
      {DOCK_ITEMS.map((item) => {
        const Icon = NAV_ICONS[item.icon];
        return (
          <button key={item.id} type="button" className="dock-item">
            <span className="dock-ico">
              <Icon />
            </span>
            <strong>{item.label}</strong>
            <em>{item.sublabel}</em>
          </button>
        );
      })}
    </nav>
  );
}
