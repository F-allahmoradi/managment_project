import { useEffect, useState } from "react";
import CosmicBackground from "@/components/layout/CosmicBackground.jsx";
import HomePage from "@/pages/HomePage.jsx";
import AuthPage from "@/pages/AuthPage.jsx";
import { currentUser, getAccessToken, logout, setAccessToken } from "@/lib/api.js";
import { leaveWebIndexOnMobile } from "@/lib/mobileGate.js";
import "@/pages/auth.css";

function modeFromHash() {
  return window.location.hash === "#register" ? "register" : "login";
}

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(() => Boolean(getAccessToken()));
  const [bootError, setBootError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [mode, setMode] = useState(modeFromHash);

  useEffect(() => {
    const onHash = () => setMode(modeFromHash());
    window.addEventListener("hashchange", onHash);
    const narrow = window.matchMedia("(max-width: 768px)");
    const onNarrow = () => leaveWebIndexOnMobile();
    narrow.addEventListener("change", onNarrow);
    return () => {
      window.removeEventListener("hashchange", onHash);
      narrow.removeEventListener("change", onNarrow);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function restore() {
      if (!getAccessToken()) {
        if (!cancelled) {
          setUser(null);
          setBootError("");
          setBooting(false);
        }
        return;
      }
      try {
        const payload = await currentUser();
        if (!cancelled) {
          setUser(payload.user);
          setBootError("");
        }
      } catch (error) {
        if (cancelled) {
          return;
        }
        if (error.status === 401) {
          setAccessToken("");
          setUser(null);
          setBootError("");
        } else {
          setBootError(error.message || "ارتباط با سرور برقرار نشد");
        }
      } finally {
        if (!cancelled) {
          setBooting(false);
        }
      }
    }

    if (getAccessToken()) {
      setBooting(true);
    }
    restore();
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  function chooseMode(next) {
    window.location.hash = next === "register" ? "register" : "login";
    setMode(next);
  }

  async function handleLogout() {
    await logout();
    setUser(null);
    window.location.hash = "login";
  }

  if (booting || (bootError && !user)) {
    return (
      <div className="auth-screen">
        <CosmicBackground />
        <section className="auth-status">
          <p>{booting ? "در حال بررسی نشست..." : bootError}</p>
          {!booting ? (
            <button type="button" onClick={() => setAttempt((value) => value + 1)}>
              تلاش دوباره
            </button>
          ) : null}
        </section>
      </div>
    );
  }

  if (!user) {
    return (
      <AuthPage
        mode={mode}
        onMode={chooseMode}
        onSuccess={(next) => {
          setUser(next);
          setBootError("");
          if (window.location.hash) {
            window.history.replaceState(null, "", window.location.pathname + window.location.search);
          }
        }}
      />
    );
  }

  return <HomePage user={user} onLogout={handleLogout} />;
}
