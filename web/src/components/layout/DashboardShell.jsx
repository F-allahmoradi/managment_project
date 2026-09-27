import "./shell.css";
import CosmicBackground from "./CosmicBackground.jsx";
import TopHeader from "@/components/header/TopHeader.jsx";
import ReportsSidebar from "@/components/sidebar/ReportsSidebar.jsx";
import FeatureGrid from "@/components/platforms/FeatureGrid.jsx";
import BottomNav from "@/components/dock/BottomNav.jsx";

export default function DashboardShell({
  user,
  onLogout,
  sidebarOpen,
  onToggleSidebar,
  onCloseSidebar,
}) {
  return (
    <div className="shell">
      <CosmicBackground />
      <TopHeader menuOpen={sidebarOpen} onToggleMenu={onToggleSidebar} user={user} onLogout={onLogout} />
      {sidebarOpen ? <button className="scrim" type="button" aria-label="بستن پنل" onClick={onCloseSidebar} /> : null}
      <div className="shell-body">
        <ReportsSidebar open={sidebarOpen} onClose={onCloseSidebar} />
        <main className="shell-main">
          <FeatureGrid />
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
