/**
 * نشست نسخهٔ موبایل.
 * توکن همان کلید وب است تا هر دو کلاینت یک ورود را بشناسند.
 * روی درگاه Vite درخواست نسبی است و پروکسی به API می‌رود.
 * در APK آدرس سرور از صفحه ورود در حافظه محلی ذخیره می‌شود.
 */
(function (global) {
  var TOKEN_KEY = "management_access_token";
  var SERVER_KEY = "management_api_base";
  var HOME = "admin-mobile.html";
  var AUTH = "mobile-auth.html";

  function isNativeShell() {
    var bridge = global.Capacitor;
    if (bridge && typeof bridge.isNativePlatform === "function" && bridge.isNativePlatform()) {
      return true;
    }
    return location.protocol === "capacitor:" || location.protocol === "ionic:";
  }

  function normalizeBase(value) {
    return String(value || "").trim().replace(/\/+$/, "");
  }

  function getApiBase() {
    return normalizeBase(localStorage.getItem(SERVER_KEY));
  }

  function setApiBase(value) {
    var text = normalizeBase(value);
    if (!text) {
      localStorage.removeItem(SERVER_KEY);
      return "";
    }
    if (!/^https?:\/\/\S+$/i.test(text)) {
      return null;
    }
    localStorage.setItem(SERVER_KEY, text);
    return text;
  }

  function needsServer() {
    return isNativeShell();
  }

  function apiBase() {
    if (location.port === "5188") {
      return "";
    }
    var saved = getApiBase();
    if (saved) {
      return saved;
    }
    if (isNativeShell() || location.port === "") {
      return "";
    }
    return "http://127.0.0.1:8080";
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || "";
  }

  function setToken(token) {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  function redirectIfAnonymous() {
    if (!getToken() && !location.pathname.endsWith(AUTH)) {
      location.replace(AUTH);
    }
  }

  function goHome() {
    location.replace(HOME);
  }

  function goAuth() {
    location.replace(AUTH);
  }

  async function request(path, options) {
    var settings = options || {};
    var headers = { Accept: "application/json" };
    if (settings.auth !== false) {
      var token = getToken();
      if (token) {
        headers.Authorization = "Bearer " + token;
      }
    }
    var url = apiBase() + path;
    if (settings.query) {
      var params = new URLSearchParams();
      Object.keys(settings.query).forEach(function (key) {
        var value = settings.query[key];
        if (value !== undefined && value !== null && value !== "") {
          params.set(key, String(value));
        }
      });
      var query = params.toString();
      if (query) {
        url += (url.indexOf("?") === -1 ? "?" : "&") + query;
      }
    }
    var init = { method: settings.method || "GET", headers: headers };
    if (settings.body !== undefined) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(settings.body);
    }
    var response;
    try {
      response = await fetch(url, init);
    } catch (networkError) {
      var offline = new Error("ارتباط با سرور برقرار نشد");
      offline.status = 0;
      throw offline;
    }
    var payload = {};
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = {};
    }
    if (!response.ok || payload.status === "error") {
      var error = new Error(payload.message || "درخواست ناموفق بود");
      error.status = response.status;
      throw error;
    }
    return payload;
  }

  async function currentUser() {
    if (!getToken()) {
      goAuth();
      return null;
    }
    try {
      var payload = await request("/api/v1/auth/me");
      return payload.user || null;
    } catch (error) {
      if (error.status === 401 || error.status === 403) {
        setToken("");
        goAuth();
        return null;
      }
      throw error;
    }
  }

  async function login(username, password) {
    var payload = await request("/api/v1/auth/login", {
      method: "POST",
      auth: false,
      body: { username: username, password: password },
    });
    setToken(payload.access_token);
    return payload.user;
  }

  async function registerAccount(fields) {
    var payload = await request("/api/v1/auth/register", {
      method: "POST",
      auth: false,
      body: fields,
    });
    setToken(payload.access_token);
    return payload.user;
  }

  async function logout() {
    try {
      if (getToken()) {
        await request("/api/v1/auth/logout", { method: "POST" });
      }
    } finally {
      setToken("");
      goAuth();
    }
  }

  async function transcribeAudio(blob) {
    var headers = { Accept: "application/json" };
    var token = getToken();
    if (token) headers.Authorization = "Bearer " + token;
    headers["Content-Type"] = (blob && blob.type) || "audio/webm";
    var response;
    try {
      response = await fetch(apiBase() + "/api/v1/stt/transcribe", {
        method: "POST",
        headers: headers,
        body: blob,
      });
    } catch (networkError) {
      throw new Error("ارتباط با سرور برقرار نشد");
    }
    var payload = {};
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = {};
    }
    if (!response.ok || payload.status === "error") {
      throw new Error(payload.message || "تبدیل صدا به متن انجام نشد");
    }
    return (payload.transcribed_text || "").trim();
  }

  async function saveSpeech(text, blob) {
    var headers = { Accept: "application/json" };
    var token = getToken();
    if (token) headers.Authorization = "Bearer " + token;
    var body = new FormData();
    body.append("text", text);
    if (blob) {
      var name = "voice.webm";
      var type = (blob.type || "").split(";")[0];
      if (type.indexOf("mp4") !== -1 || type.indexOf("aac") !== -1) name = "voice.m4a";
      body.append("file", blob, name);
    }
    var response;
    try {
      response = await fetch(apiBase() + "/api/v1/stt/save", {
        method: "POST",
        headers: headers,
        body: body,
      });
    } catch (networkError) {
      throw new Error("ارتباط با سرور برقرار نشد");
    }
    var payload = {};
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = {};
    }
    if (!response.ok || payload.status === "error") {
      throw new Error(payload.message || "ذخیرهٔ صوت و متن انجام نشد");
    }
    return payload;
  }

  async function saveMedia(file) {
    var headers = { Accept: "application/json" };
    var token = getToken();
    if (token) headers.Authorization = "Bearer " + token;
    var body = new FormData();
    body.append("file", file, file.name || "upload");
    var response;
    try {
      response = await fetch(apiBase() + "/api/v1/media/save", {
        method: "POST",
        headers: headers,
        body: body,
      });
    } catch (networkError) {
      throw new Error("ارتباط با سرور برقرار نشد");
    }
    var payload = {};
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = {};
    }
    if (!response.ok || payload.status === "error") {
      throw new Error(payload.message || "ذخیرهٔ فایل انجام نشد");
    }
    return payload;
  }

  function analyzeSource(sourceType, sourceId) {
    return request("/api/v1/text-analyses", {
      method: "POST",
      body: { source_type: sourceType, source_id: sourceId },
    });
  }

  function previewAnalysis(sourceType, sourceId) {
    return request("/api/v1/text-analyses/preview", {
      method: "POST",
      body: { source_type: sourceType, source_id: sourceId },
    });
  }

  function commitAnalysis(fields) {
    return request("/api/v1/text-analyses/commit", {
      method: "POST",
      body: { fields: fields },
    });
  }

  function callTool(domain, tool, args, method) {
    var path = "/api/v1/" + domain + "/tools/" + tool;
    if (method === "GET") {
      return request(path, { method: "GET", query: args || {} });
    }
    return request(path, { method: "POST", body: args || {} });
  }

  global.MobileSession = {
    getToken: getToken,
    setToken: setToken,
    getApiBase: getApiBase,
    setApiBase: setApiBase,
    needsServer: needsServer,
    redirectIfAnonymous: redirectIfAnonymous,
    goHome: goHome,
    currentUser: currentUser,
    login: login,
    registerAccount: registerAccount,
    logout: logout,
    request: request,
    transcribeAudio: transcribeAudio,
    saveSpeech: saveSpeech,
    saveMedia: saveMedia,
    analyzeSource: analyzeSource,
    previewAnalysis: previewAnalysis,
    commitAnalysis: commitAnalysis,
    callTool: callTool,
  };
})(window);
