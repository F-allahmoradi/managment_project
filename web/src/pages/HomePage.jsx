import { useState } from "react";
import DashboardShell from "@/components/layout/DashboardShell.jsx";

export default function HomePage({ user, onLogout }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <DashboardShell
      user={user}
      onLogout={onLogout}
      sidebarOpen={sidebarOpen}
      onToggleSidebar={() => setSidebarOpen((open) => !open)}
      onCloseSidebar={() => setSidebarOpen(false)}
    />
  );
}
