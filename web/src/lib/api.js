/**
 * کلاینت HTTP نسخهٔ ۱.
 * توکن در localStorage می‌ماند تا صفحهٔ وب بعد از ورود همان کاربر را نگه دارد.
 * اگر VITE_API_BASE_URL خالی باشد، درخواست به همان مبدأ می‌رود و Vite در توسعه
 * آن را به سرور API پروکسی می‌کند.
 */

const TOKEN_KEY = "management_access_token";

export function apiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (configured) {
    return String(configured).replace(/\/$/, "");
  }
  return "";
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setAccessToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export async function login(username, password) {
  const payload = await request("/api/v1/auth/login", {
    method: "POST",
    body: { username, password },
    auth: false,
  });
  setAccessToken(payload.access_token);
  return payload;
}

export async function registerAccount(fields) {
  const payload = await request("/api/v1/auth/register", {
    method: "POST",
    body: fields,
    auth: false,
  });
  setAccessToken(payload.access_token);
  return payload;
}

export async function logout() {
  try {
    await request("/api/v1/auth/logout", { method: "POST" });
  } finally {
    setAccessToken("");
  }
}

export function currentUser() {
  return request("/api/v1/auth/me");
}

export function callTool(domain, tool, args = {}, method = "POST") {
  const path = `/api/v1/${domain}/tools/${tool}`;
  if (method === "GET") {
    return request(path, { method: "GET", query: args });
  }
  return request(path, { method: "POST", body: args });
}

export async function request(path, options = {}) {
  const headers = { Accept: "application/json" };
  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  let url = `${apiBaseUrl()}${path}`;
  if (options.query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(options.query)) {
      if (value !== undefined && value !== null && value !== "") {
        params.set(key, String(value));
      }
    }
    const query = params.toString();
    if (query) {
      url += `?${query}`;
    }
  }
  const init = { method: options.method || "GET", headers };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  let response;
  try {
    response = await fetch(url, init);
  } catch {
    const error = new Error("ارتباط با سرور برقرار نشد");
    error.code = "NETWORK";
    throw error;
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.status === "error") {
    const error = new Error(payload.message || "درخواست API ناموفق بود");
    error.status = response.status;
    error.code = payload.error_code;
    error.payload = payload;
    throw error;
  }
  return payload;
}
