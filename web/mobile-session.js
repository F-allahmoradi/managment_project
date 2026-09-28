/**
 * نشست نسخهٔ موبایل.
 * توکن همان کلید وب است تا هر دو کلاینت یک ورود را بشناسند.
 * روی سایت و درگاه Vite درخواست به همان مبدأ می‌رود.
 * در APK آدرس عمومی هنگام ساخت در BAKED_API_BASE می‌نشیند.
 */
(function (global) {
  var TOKEN_KEY = "management_access_token";
  var SERVER_KEY = "management_api_base";
  var HOME = "admin-mobile.html";
  var AUTH = "mobile-auth.html";
  var BAKED_API_BASE = "http://45.156.186.141";

  function isNativeShell() {
    var bridge = global.Capacitor;
    if (bridge && typeof bridge.isNativePlatform === "function" && bridge.isNativePlatform()) {
      return true;
    }
    return location.protocol === "capacitor:" || location.protocol === "ionic:";
  }

  function normalizeBase(value) {
    var text = String(value || "").trim();
    if (!text) {
      return "";
    }
    try {
      var parsed = new URL(text);
      if (parsed.protocol === "http:" || parsed.protocol === "https:") {
        return parsed.origin;
      }
    } catch (ignored) {}
    text = text.replace(/\/+$/, "");
    text = text.replace(/\/api\/v1$/i, "").replace(/\/api$/i, "");
    return text.replace(/\/+$/, "");
  }

  function nativeHttp() {
    var cap = global.Capacitor;
    if (!cap || !cap.Plugins) {
      return null;
    }
    return cap.Plugins.CapacitorHttp || null;
  }

  function failureMessage(payload, status) {
    if (payload && payload.message) {
      return payload.message;
    }
    if (status === 404) {
      return "این آدرس API ندارد. فقط ریشه را بنویسید، مثلاً http://45.156.186.141";
    }
    if (status === 502 || status === 503) {
      return "وب‌سرور بالا است ولی برنامهٔ API جواب نمی‌دهد";
    }
    if (status) {
      return "سرور پاسخ درستی نداد (" + status + ")";
    }
    return "درخواست ناموفق بود";
  }

  function throwIfFailed(payload, status) {
    var body = payload && typeof payload === "object" ? payload : {};
    if ((status && (status < 200 || status >= 300)) || body.status === "error") {
      var error = new Error(failureMessage(body, status));
      error.status = status || 0;
      throw error;
    }
    return body;
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

  function bakedApiBase() {
    return normalizeBase(BAKED_API_BASE);
  }

  function needsServer() {
    return isNativeShell() && !bakedApiBase() && !getApiBase();
  }

  function apiBase() {
    if (location.port === "5188") {
      return "";
    }
    if (!isNativeShell()) {
      return "";
    }
    var baked = bakedApiBase();
    if (baked) {
      return baked;
    }
    return getApiBase();
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
    var method = settings.method || "GET";
    if (settings.body !== undefined) {
      headers["Content-Type"] = "application/json";
    }
    var plugin = isNativeShell() ? nativeHttp() : null;
    if (plugin) {
      try {
        var native = await plugin.request({
          url: url,
          method: method,
          headers: headers,
          data: settings.body !== undefined ? settings.body : undefined,
          connectTimeout: 180000,
          readTimeout: 180000,
        });
        var nativePayload = native.data;
        if (typeof nativePayload === "string") {
          try {
            nativePayload = JSON.parse(nativePayload);
          } catch (parseNative) {
            nativePayload = {};
          }
        }
        return throwIfFailed(nativePayload, native.status);
      } catch (nativeError) {
        if (nativeError && nativeError.status) {
          throw nativeError;
        }
        var blocked = new Error(
          "ارتباط با سرور برقرار نشد. آدرس را این‌طور بنویسید: http://آی‌پی بدون پورت ۸۰۸۰"
        );
        blocked.status = 0;
        throw blocked;
      }
    }
    var init = { method: method, headers: headers };
    if (settings.body !== undefined) {
      init.body = JSON.stringify(settings.body);
    }
    var response;
    try {
      response = await fetch(url, init);
    } catch (networkError) {
      var offline = new Error(
        "ارتباط با سرور برقرار نشد. آدرس را این‌طور بنویسید: http://آی‌پی بدون پورت ۸۰۸۰"
      );
      offline.status = 0;
      throw offline;
    }
    var payload = {};
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = {};
    }
    return throwIfFailed(payload, response.status);
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

  function blobToBase64(blob) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onloadend = function () {
        var result = String(reader.result || "");
        var comma = result.indexOf(",");
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  async function transcribeAudio(blob) {
    if (!blob || !blob.size) {
      throw new Error("فایل صوتی خالی است");
    }
    var encoded = await blobToBase64(blob);
    var payload = await request("/api/v1/stt/transcribe", {
      method: "POST",
      body: {
        audio_base64: encoded,
        mime_type: (blob.type || "audio/webm").split(";")[0],
      },
    });
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

  function previewFinished(snapshot) {
    if (!snapshot || typeof snapshot !== "object") return true;
    if (snapshot.status === "error" || snapshot.phase === "error") return true;
    if (snapshot.ready === true || snapshot.phase === "done") return true;
    if (!snapshot.job_id) return true;
    return false;
  }

  async function previewAnalysis(sourceType, sourceId, onProgress) {
    var snapshot = await request("/api/v1/text-analyses/preview", {
      method: "POST",
      body: { source_type: sourceType, source_id: sourceId },
    });
    var jobId = snapshot.job_id;
    if (typeof onProgress === "function" && snapshot && snapshot.message) {
      onProgress(snapshot);
    }
    if (jobId) {
      var deadline = Date.now() + 180000;
      while (!previewFinished(snapshot)) {
        if (Date.now() > deadline) {
          var timeout = new Error("استخراج بیش از حد طول کشید");
          timeout.status = 504;
          throw timeout;
        }
        await new Promise(function (resolve) { setTimeout(resolve, 700); });
        snapshot = await pollAnalysis(jobId);
        if (typeof onProgress === "function") onProgress(snapshot);
      }
    }
    if (snapshot.phase === "error" || snapshot.status === "error") {
      var failed = new Error(snapshot.message || "استخراج انجام نشد");
      failed.status = 503;
      throw failed;
    }
    if (jobId && snapshot.phase && snapshot.phase !== "done") {
      var unfinished = new Error(snapshot.message || "استخراج هنوز تمام نشده");
      unfinished.status = 503;
      throw unfinished;
    }
    return snapshot;
  }

  function pollAnalysis(jobId) {
    return request("/api/v1/text-analyses/preview/" + encodeURIComponent(jobId), {
      method: "GET",
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
    bakedApiBase: bakedApiBase,
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
    pollAnalysis: pollAnalysis,
    commitAnalysis: commitAnalysis,
    callTool: callTool,
  };
})(window);
