const TOKEN_KEY = "management_access_token";

function onWebIndex() {
  const path = window.location.pathname;
  return path === "/" || path.endsWith("/index.html");
}

export function isMobileClient() {
  const ua = navigator.userAgent || "";
  if (/Android|iPhone|iPod|iPad|Mobile/i.test(ua)) {
    return true;
  }
  if (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1) {
    return true;
  }
  if (window.matchMedia("(max-width: 768px)").matches) {
    return true;
  }
  return window.matchMedia("(max-width: 1024px) and (pointer: coarse)").matches;
}

export function redirectToMobileHome() {
  let token = "";
  try {
    token = localStorage.getItem(TOKEN_KEY) || "";
  } catch {
    token = "";
  }
  window.location.replace(token ? "/admin-mobile.html" : "/mobile-auth.html");
}

export function leaveWebIndexOnMobile() {
  if (!onWebIndex() || !isMobileClient()) {
    return false;
  }
  redirectToMobileHome();
  return true;
}
