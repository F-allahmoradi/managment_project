/**
 * اتصال صفحات موبایل به API نسخهٔ ۱.
 * فهرست‌ها و فرم‌ها از ابزارهای دامنه می‌خوانند و می‌نویسند.
 */
(function (global) {
  var S = global.MobileSession;

  function pageName() {
    return (document.body && document.body.dataset.page) || "";
  }

  function param(name) {
    return new URLSearchParams(location.search).get(name) || "";
  }

  function toast(message) {
    var existing = document.querySelector(".toast");
    if (existing) existing.remove();
    var el = document.createElement("div");
    el.className = "toast";
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(function () {
      el.remove();
    }, 4200);
  }

  function tool(domain, name, args) {
    return S.callTool(domain, name, args || {});
  }

  async function listAll(domain, name, extra) {
    var records = [];
    var offset = 0;
    var limit = 50;
    for (var i = 0; i < 4; i += 1) {
      var payload = await tool(domain, name, Object.assign({ limit: limit, offset: offset }, extra || {}));
      var page = payload.records || [];
      records = records.concat(page);
      if (page.length < limit) break;
      offset += limit;
    }
    return records;
  }

  function faStamp(value) {
    if (!value) return "—";
    var date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(date);
  }

  function faTime(value) {
    if (!value) return "—";
    var date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("fa-IR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  function displayName(row) {
    if (!row) return "کاربر";
    var name = [row.first_name, row.last_name].filter(Boolean).join(" ");
    return name || row.username || ("#" + row.id);
  }

  function userOptionLabel(row) {
    var name = displayName(row);
    if (row.username && name !== row.username) return name + " · " + row.username;
    return name;
  }

  function isDirector(user) {
    return ((user && user.roles) || []).indexOf("مدیر کل") !== -1;
  }

  function canSendReminder(user) {
    var roles = (user && user.roles) || [];
    return roles.indexOf("مدیر کل") !== -1 || roles.indexOf("مدیر پروژه") !== -1;
  }

  function canManage(user) {
    return canSendReminder(user);
  }

  function personId(row) {
    return Number((row && (row.user_id || row.id)) || 0);
  }

  function personRole(row) {
    return (row && (row.project_role_name || row.username || "")) || "";
  }

  function chatHrefForPerson(row) {
    return "chat.html?user_id=" + personId(row);
  }

  function renderPersonRows(container, people, me) {
    if (!container) return;
    var myId = Number(me && me.id);
    var rows = (people || []).filter(function (row) {
      var id = personId(row);
      return id && id !== myId;
    });
    if (!rows.length) {
      empty(container, "فرد دیگری برای گفتگو نیست.");
      return;
    }
    container.innerHTML = "";
    rows.forEach(function (row) {
      var wrap = document.createElement("div");
      wrap.className = "person-row";
      wrap.innerHTML =
        '<div class="person-copy"><strong></strong><em></em></div><a class="chat-chip" href="' +
        chatHrefForPerson(row) +
        '">گفتگو</a>';
      wrap.querySelector("strong").textContent = displayName(row);
      wrap.querySelector("em").textContent = personRole(row);
      container.appendChild(wrap);
    });
  }

  function mergePeople(base, extra) {
    var seen = {};
    var out = [];
    function add(row) {
      var id = personId(row);
      if (!id || seen[id]) return;
      seen[id] = true;
      out.push(row);
    }
    (base || []).forEach(add);
    (extra || []).forEach(add);
    return out;
  }

  async function loadChatPeers(me) {
    var chats = await listAll("crud", "list_chats");
    var people = [];
    for (var i = 0; i < chats.length; i += 1) {
      var members = await listAll("crud", "list_chat_members", { chat_id: chats[i].id });
      members.forEach(function (row) {
        if (Number(row.user_id) === Number(me.id)) return;
        people.push({
          id: row.user_id,
          user_id: row.user_id,
          username: row.username,
        });
      });
    }
    return people;
  }

  async function loadChatPeople(user, projectId) {
    if (projectId) {
      return listAll("crud", "list_project_members", { project_id: projectId });
    }
    var peers = [];
    try {
      peers = await loadChatPeers(user);
    } catch (ignored) {}
    if (isDirector(user)) {
      return mergePeople(await loadUsers(), peers);
    }
    var projects = await loadProjects();
    var people = [];
    for (var i = 0; i < projects.length; i += 1) {
      var members = await listAll("crud", "list_project_members", { project_id: projects[i].id });
      members.forEach(function (row) {
        people.push(row);
      });
    }
    return mergePeople(people, peers);
  }

  function parseDay(value) {
    if (!value) return null;
    var date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function daysBetween(from, to) {
    var start = parseDay(from);
    var end = parseDay(to);
    if (!start || !end) return null;
    return Math.round((end.getTime() - start.getTime()) / 86400000);
  }

  function formatDays(count) {
    if (count == null) return "—";
    if (count < 0) return faDigits(Math.abs(count)) + " روز گذشته";
    if (count === 0) return "امروز";
    return faDigits(count) + " روز";
  }

  function todayStamp() {
    var now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), now.getDate());
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value == null || value === "" ? "—" : String(value);
  }

  function empty(container, message) {
    container.innerHTML = "";
    var note = document.createElement("p");
    note.className = "empty-note";
    note.textContent = message;
    container.appendChild(note);
  }

  function cardLink(href, html) {
    var a = document.createElement("a");
    a.className = "meet";
    a.href = href;
    a.innerHTML = html;
    return a;
  }

  function faDigits(value) {
    return String(value).replace(/\d/g, function (digit) {
      return "۰۱۲۳۴۵۶۷۸۹"[digit];
    });
  }

  function jalaliParts(date) {
    var parts = new Intl.DateTimeFormat("en-US-u-ca-persian", {
      year: "numeric",
      month: "numeric",
      day: "numeric",
    }).formatToParts(date);
    function pick(type) {
      var found = parts.find(function (part) { return part.type === type; });
      return Number(found ? found.value : 0);
    }
    return {
      year: pick("year"),
      month: pick("month"),
      day: pick("day"),
      monthName: new Intl.DateTimeFormat("fa-IR-u-ca-persian", { month: "long" }).format(date),
    };
  }

  function jalaliToGregorian(jy, jm, jd) {
    var year = jy - 979;
    var month = jm - 1;
    var day = jd - 1;
    var dayNo = 365 * year + Math.floor(year / 33) * 8 + Math.floor(((year % 33) + 3) / 4);
    var i;
    for (i = 0; i < month; i += 1) dayNo += i < 6 ? 31 : 30;
    dayNo += day;
    var gDay = dayNo + 79;
    var gy = 1600 + 400 * Math.floor(gDay / 146097);
    gDay %= 146097;
    var leap = true;
    if (gDay >= 36525) {
      gDay -= 1;
      gy += 100 * Math.floor(gDay / 36524);
      gDay %= 36524;
      if (gDay >= 365) gDay += 1;
      else leap = false;
    }
    gy += 4 * Math.floor(gDay / 1461);
    gDay %= 1461;
    if (gDay >= 366) {
      leap = false;
      gDay -= 1;
      gy += Math.floor(gDay / 365);
      gDay %= 365;
    }
    var gd = gDay + 1;
    var lengths = [0, 31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    var gm;
    for (gm = 1; gm <= 12 && gd > lengths[gm]; gm += 1) gd -= lengths[gm];
    return { year: gy, month: gm, day: gd };
  }

  function isoFromJalali(jy, jm, jd, startHHmm) {
    var g = jalaliToGregorian(jy, jm, jd);
    var parts = String(startHHmm || "10:00").split(":");
    var pad = function (n) { return String(n).padStart(2, "0"); };
    return (
      g.year + "-" + pad(g.month) + "-" + pad(g.day) +
      "T" + pad(Number(parts[0] || 10)) + ":" + pad(Number(parts[1] || 0)) + ":00"
    );
  }

  function minutesBetween(startHHmm, endHHmm) {
    var a = String(startHHmm || "10:00").split(":");
    var b = String(endHHmm || "11:00").split(":");
    var start = Number(a[0]) * 60 + Number(a[1]);
    var end = Number(b[0]) * 60 + Number(b[1]);
    var diff = end - start;
    return diff > 0 ? diff : 60;
  }

  function padClock(n) {
    return String(n).padStart(2, "0");
  }

  function hhmmFromParts(hourEl, minuteEl) {
    return padClock(Number((hourEl && hourEl.value) || 10)) + ":" + padClock(Number((minuteEl && minuteEl.value) || 0));
  }

  function fillClockSelect(select, count, step) {
    if (!select || select.options.length) return;
    var i;
    for (i = 0; i < count; i += step) {
      var option = document.createElement("option");
      option.value = String(i);
      option.textContent = faDigits(padClock(i));
      select.appendChild(option);
    }
  }

  function setClockSelect(select, value) {
    if (!select) return;
    var snapped = Number(value);
    if (select.id && select.id.indexOf("minute") !== -1) snapped = Math.round(snapped / 5) * 5;
    if (snapped >= 60) snapped = 55;
    select.value = String(snapped);
    if (select.value !== String(snapped) && select.options.length) select.selectedIndex = 0;
  }

  function addMinutesToHHmm(startHHmm, minutes) {
    var parts = String(startHHmm || "10:00").split(":");
    var total = Number(parts[0]) * 60 + Number(parts[1]) + Number(minutes || 0);
    if (total < 0) total = 0;
    if (total > 23 * 60 + 55) total = 23 * 60 + 55;
    return padClock(Math.floor(total / 60)) + ":" + padClock(total % 60);
  }

  function knownDurationValue(minutes) {
    var known = { 15: 1, 30: 1, 45: 1, 60: 1, 90: 1, 120: 1, 180: 1 };
    return known[minutes] ? String(minutes) : "custom";
  }

  function paintMeetingClock(startHHmm, endHHmm) {
    var start = String(startHHmm || "10:00").split(":");
    var end = String(endHHmm || "11:00").split(":");
    setClockSelect(document.getElementById("meeting-hour"), start[0]);
    setClockSelect(document.getElementById("meeting-minute"), start[1]);
    setClockSelect(document.getElementById("meeting-end-hour"), end[0]);
    setClockSelect(document.getElementById("meeting-end-minute"), end[1]);
    syncMeetingClock(false);
  }

  function syncMeetingClock(fromDuration) {
    var hourEl = document.getElementById("meeting-hour");
    var minEl = document.getElementById("meeting-minute");
    var endHourEl = document.getElementById("meeting-end-hour");
    var endMinEl = document.getElementById("meeting-end-minute");
    var startEl = document.getElementById("meeting-start");
    var endEl = document.getElementById("meeting-end");
    var isoEl = document.getElementById("meeting-scheduled-iso");
    var minsEl = document.getElementById("meeting-duration-mins");
    var durationEl = document.getElementById("meeting-duration");
    var durationPick = document.getElementById("meeting-duration-pick");
    if (!hourEl || !minEl) return;
    var start = hhmmFromParts(hourEl, minEl);
    var end;
    if (fromDuration && durationPick && durationPick.value !== "custom") {
      end = addMinutesToHHmm(start, Number(durationPick.value));
      setClockSelect(endHourEl, end.split(":")[0]);
      setClockSelect(endMinEl, end.split(":")[1]);
    } else {
      end = hhmmFromParts(endHourEl, endMinEl);
    }
    var minutes = minutesBetween(start, end);
    if (startEl) startEl.value = start;
    if (endEl) endEl.value = end;
    if (minsEl) minsEl.value = String(minutes);
    if (durationEl) durationEl.value = durationLabel(minutes);
    if (durationPick && !fromDuration) durationPick.value = knownDurationValue(minutes);
    if (isoEl) isoEl.value = "";
  }

  function bindMeetingClock() {
    var hourEl = document.getElementById("meeting-hour");
    var minEl = document.getElementById("meeting-minute");
    var endHourEl = document.getElementById("meeting-end-hour");
    var endMinEl = document.getElementById("meeting-end-minute");
    var durationPick = document.getElementById("meeting-duration-pick");
    if (!hourEl) return;
    fillClockSelect(hourEl, 24, 1);
    fillClockSelect(endHourEl, 24, 1);
    fillClockSelect(minEl, 60, 5);
    fillClockSelect(endMinEl, 60, 5);
    var now = new Date();
    var startMins = now.getHours() * 60 + Math.ceil(now.getMinutes() / 5) * 5;
    if (startMins >= 24 * 60) startMins = 23 * 60;
    var start = padClock(Math.floor(startMins / 60)) + ":" + padClock(startMins % 60);
    paintMeetingClock(start, addMinutesToHHmm(start, 60));
    [hourEl, minEl].forEach(function (el) {
      el.addEventListener("change", function () { syncMeetingClock(true); });
    });
    [endHourEl, endMinEl].forEach(function (el) {
      if (el) el.addEventListener("change", function () { syncMeetingClock(false); });
    });
    if (durationPick) {
      durationPick.addEventListener("change", function () {
        if (durationPick.value === "custom") return;
        syncMeetingClock(true);
      });
    }
  }

  var TEHRAN = { lat: 35.6892, lng: 51.3890 };

  function neshanMapsUrl(lat, lng, query) {
    if (lat && lng) return "https://neshan.org/maps/@" + lat + "," + lng + ",16z";
    return "https://neshan.org/maps/search/" + encodeURIComponent(query || "تهران");
  }

  function googleMapsFaUrl(lat, lng, query) {
    if (lat && lng) {
      return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(lat + "," + lng) + "&hl=fa";
    }
    return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(query || "تهران، ایران") + "&hl=fa";
  }

  function applyMeetingPlace(place) {
    var locEl = document.getElementById("meeting-location");
    if (!locEl || !place) return;
    locEl.value = place.label || "";
    locEl.dataset.lat = place.lat != null ? String(place.lat) : "";
    locEl.dataset.lng = place.lng != null ? String(place.lng) : "";
  }

  async function searchIranPlaces(query) {
    var url =
      "https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=8" +
      "&countrycodes=ir&accept-language=fa&q=" + encodeURIComponent(query);
    var res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("جستجوی نقشه الان در دسترس نیست");
    return (await res.json()).map(function (row) {
      return { label: row.display_name, lat: Number(row.lat), lng: Number(row.lon) };
    });
  }

  function loadLeaflet() {
    return new Promise(function (resolve, reject) {
      if (global.L) {
        resolve(global.L);
        return;
      }
      if (!document.getElementById("leaflet-css")) {
        var css = document.createElement("link");
        css.id = "leaflet-css";
        css.rel = "stylesheet";
        css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(css);
      }
      var script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.onload = function () { resolve(global.L); };
      script.onerror = function () { reject(new Error("نقشه بارگذاری نشد")); };
      document.head.appendChild(script);
    });
  }

  function openMapPicker() {
    closeCalendarSheet();
    var locEl = document.getElementById("meeting-location");
    var current = {
      label: (locEl && locEl.value) || "تهران",
      lat: Number((locEl && locEl.dataset.lat) || TEHRAN.lat),
      lng: Number((locEl && locEl.dataset.lng) || TEHRAN.lng),
    };
    var sheet = document.createElement("div");
    sheet.className = "cal-sheet";
    sheet.id = "calendar-sheet";
    sheet.innerHTML =
      "<div class='cal-panel' role='dialog' aria-label='انتخاب مکان'>" +
      "<h2>آدرس روی نقشه ایران</h2>" +
      "<p class='hint'>جستجو روی نقشهٔ ایران است. بعد از انتخاب می‌توانید همان نقطه را در نشان یا گوگل‌مپ فارسی باز کنید.</p>" +
      "<label class='box'><input id='map-query' type='search' placeholder='مثلاً میدان آزادی، تهران'></label>" +
      "<div class='cal-actions' style='margin-top:8px'>" +
      "<button type='button' id='map-search'>جستجو</button>" +
      "<button type='button' id='map-here'>موقعیت من</button>" +
      "</div>" +
      "<div id='meeting-map'></div>" +
      "<div id='map-hits'></div>" +
      "<div class='cal-actions'>" +
      "<button type='button' id='map-neshan'>نشان</button>" +
      "<button type='button' id='map-gmaps'>گوگل‌مپ فارسی</button>" +
      "</div>" +
      "<div class='cal-actions'>" +
      "<button type='button' id='cal-cancel'>انصراف</button>" +
      "<button type='button' class='ok' id='map-ok'>ثبت این آدرس</button>" +
      "</div></div>";
    document.body.appendChild(sheet);
    var picked = { label: current.label, lat: current.lat, lng: current.lng };
    var map;
    var marker;
    function setPicked(place) {
      picked = place;
      if (marker && map) marker.setLatLng([place.lat, place.lng]);
      if (map) map.setView([place.lat, place.lng], 16);
    }
    function renderHits(rows) {
      var box = document.getElementById("map-hits");
      if (!box) return;
      box.innerHTML = rows.map(function (row, index) {
        return "<button class='map-hit' type='button' data-index='" + index + "'>" + escapeHtml(row.label) + "</button>";
      }).join("") || "<p class='hint'>نتیجه‌ای پیدا نشد.</p>";
      box.querySelectorAll(".map-hit").forEach(function (btn) {
        btn.addEventListener("click", function () {
          setPicked(rows[Number(btn.getAttribute("data-index"))]);
        });
      });
    }
    async function runSearch() {
      var query = ((document.getElementById("map-query") || {}).value || "").trim();
      if (!query) {
        toast("آدرس را بنویسید");
        return;
      }
      try {
        var rows = await searchIranPlaces(query);
        renderHits(rows);
        if (rows[0]) setPicked(rows[0]);
      } catch (error) {
        toast(error.message);
      }
    }
    sheet.addEventListener("click", function (event) {
      if (event.target === sheet) closeCalendarSheet();
    });
    document.getElementById("cal-cancel").addEventListener("click", closeCalendarSheet);
    document.getElementById("map-search").addEventListener("click", runSearch);
    document.getElementById("map-query").addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        runSearch();
      }
    });
    document.getElementById("map-here").addEventListener("click", function () {
      if (!navigator.geolocation) {
        toast("موقعیت روی این دستگاه در دسترس نیست");
        return;
      }
      navigator.geolocation.getCurrentPosition(function (pos) {
        setPicked({
          label: "موقعیت فعلی (" + pos.coords.latitude.toFixed(5) + "، " + pos.coords.longitude.toFixed(5) + ")",
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
      }, function () {
        toast("اجازهٔ موقعیت داده نشد");
      }, { enableHighAccuracy: true, timeout: 8000 });
    });
    document.getElementById("map-neshan").addEventListener("click", function () {
      window.open(neshanMapsUrl(picked.lat, picked.lng, picked.label), "_blank", "noopener");
    });
    document.getElementById("map-gmaps").addEventListener("click", function () {
      window.open(googleMapsFaUrl(picked.lat, picked.lng, picked.label), "_blank", "noopener");
    });
    document.getElementById("map-ok").addEventListener("click", function () {
      applyMeetingPlace(picked);
      closeCalendarSheet();
    });
    loadLeaflet().then(function (L) {
      map = L.map("meeting-map").setView([picked.lat, picked.lng], 14);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
      }).addTo(map);
      marker = L.marker([picked.lat, picked.lng]).addTo(map);
      map.on("click", function (event) {
        setPicked({
          label: "نقطه انتخاب‌شده (" + event.latlng.lat.toFixed(5) + "، " + event.latlng.lng.toFixed(5) + ")",
          lat: event.latlng.lat,
          lng: event.latlng.lng,
        });
      });
      setTimeout(function () { map.invalidateSize(); }, 80);
    }).catch(function () {
      document.getElementById("meeting-map").innerHTML =
        "<p class='hint'>کاشی نقشه بارگذاری نشد. از جستجو، نشان یا گوگل‌مپ فارسی استفاده کنید.</p>";
    });
    if ((locEl && locEl.value || "").trim()) {
      document.getElementById("map-query").value = locEl.value;
    }
  }

  function deviceCalendar() {
    var cap = global.Capacitor;
    if (!cap) return null;
    if (cap.Plugins && cap.Plugins.DeviceCalendar) return cap.Plugins.DeviceCalendar;
    if (typeof cap.registerPlugin === "function") {
      try {
        return cap.registerPlugin("DeviceCalendar");
      } catch (ignored) {
        return null;
      }
    }
    return null;
  }

  function localIsoFromMs(ms) {
    var date = new Date(ms);
    var pad = function (n) { return String(n).padStart(2, "0"); };
    return (
      date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate()) +
      "T" + pad(date.getHours()) + ":" + pad(date.getMinutes()) + ":00"
    );
  }

  function hhmmFromMs(ms) {
    var date = new Date(ms);
    var pad = function (n) { return String(n).padStart(2, "0"); };
    return pad(date.getHours()) + ":" + pad(date.getMinutes());
  }

  function durationFromEvent(event) {
    if (event.allDay) return 60;
    var minutes = Math.round((Number(event.endMs) - Number(event.startMs)) / 60000);
    if (minutes < 15) return 15;
    if (minutes > 12 * 60) return 12 * 60;
    return minutes;
  }

  function eventStartDate(event) {
    var raw = new Date(event.startMs);
    if (event.allDay) {
      return new Date(raw.getUTCFullYear(), raw.getUTCMonth(), raw.getUTCDate(), 10, 0, 0);
    }
    return raw;
  }

  function durationLabel(minutes) {
    if (minutes >= 60 && minutes % 60 === 0) return faDigits(minutes / 60) + " ساعت";
    return faDigits(minutes) + " دقیقه";
  }

  function importedEventStore(userId) {
    return "calendar_imported_" + String(userId || "anon");
  }

  function readImportedIds(userId) {
    try {
      var parsed = JSON.parse(localStorage.getItem(importedEventStore(userId)) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (ignored) {
      return [];
    }
  }

  function writeImportedIds(userId, ids) {
    localStorage.setItem(importedEventStore(userId), JSON.stringify(ids.slice(-400)));
  }

  async function loadCalendarEvents() {
    var plugin = deviceCalendar();
    if (!plugin || typeof plugin.listEvents !== "function") {
      throw new Error("این قابلیت روی APK اندروید کار می‌کند. تقویم گوگل را روی گوشی همگام کنید.");
    }
    var now = Date.now();
    var payload = await plugin.listEvents({
      fromMs: now - 6 * 60 * 60 * 1000,
      toMs: now + 60 * 24 * 60 * 60 * 1000,
      googleOnly: true,
    });
    return payload || { events: [] };
  }

  function closeCalendarSheet() {
    var sheet = document.getElementById("calendar-sheet");
    if (sheet) sheet.remove();
  }

  function openCalendarSheet(options) {
    closeCalendarSheet();
    var events = options.events || [];
    var mode = options.mode;
    var sheet = document.createElement("div");
    sheet.className = "cal-sheet";
    sheet.id = "calendar-sheet";
    var rows = events.map(function (event, index) {
      var control = mode === "fill"
        ? "<input type='radio' name='cal-pick' value='" + index + "'" + (index === 0 ? " checked" : "") + ">"
        : "<input type='checkbox' data-index='" + index + "' checked>";
      return (
        "<label class='cal-event'>" + control +
        "<span><strong>" + escapeHtml(event.title || "بدون عنوان") + "</strong>" +
        "<span>" + faStamp(event.startMs) + " · " + (event.allDay ? "تمام‌روز" : faTime(event.startMs) + " - " + faTime(event.endMs)) +
        (event.calendarName ? " · " + escapeHtml(event.calendarName) : "") +
        (event.location ? " · " + escapeHtml(event.location) : "") +
        "</span></span></label>"
      );
    }).join("");
    var note = options.usedGoogle
      ? "رویدادهای تقویم گوگل روی همین گوشی."
      : "رویداد از تقویم گوشی آمد. اگر حساب گوگل سینک باشد، جلسات گوگل هم در همین فهرست هستند.";
    sheet.innerHTML =
      "<div class='cal-panel' role='dialog' aria-label='تقویم گوگل'>" +
      "<h2>انتخاب از تقویم</h2>" +
      "<p class='hint'>" + note + " اگر جلسه از قبل ثبت شده باشد دوباره ساخته نمی‌شود.</p>" +
      (options.projectHtml || "") +
      "<div id='cal-event-list'>" + (rows || "<p class='hint'>رویداد نزدیک‌ی پیدا نشد.</p>") + "</div>" +
      "<div class='cal-actions'>" +
      "<button type='button' id='cal-cancel'>انصراف</button>" +
      "<button type='button' class='ok' id='cal-ok'>" + (mode === "fill" ? "پر کردن فرم" : "ثبت در جلسات") + "</button>" +
      "</div></div>";
    document.body.appendChild(sheet);
    sheet.addEventListener("click", function (event) {
      if (event.target === sheet) closeCalendarSheet();
    });
    document.getElementById("cal-cancel").addEventListener("click", closeCalendarSheet);
    document.getElementById("cal-ok").addEventListener("click", function () {
      var picked = [];
      if (mode === "fill") {
        var radio = sheet.querySelector("input[name='cal-pick']:checked");
        if (radio) picked.push(events[Number(radio.value)]);
      } else {
        sheet.querySelectorAll("input[type='checkbox'][data-index]:checked").forEach(function (box) {
          picked.push(events[Number(box.getAttribute("data-index"))]);
        });
      }
      if (!picked.length) {
        toast("حداقل یک رویداد را انتخاب کنید");
        return;
      }
      var projectSelect = document.getElementById("cal-project");
      options.onPick(picked, Number((projectSelect && projectSelect.value) || 0));
    });
  }

  function applyCalendarEventToForm(event) {
    var start = eventStartDate(event);
    var minutes = durationFromEvent(event);
    var startHHmm = hhmmFromMs(start.getTime());
    var endDate = new Date(start.getTime() + minutes * 60000);
    var titleEl = document.getElementById("meeting-title");
    var locEl = document.getElementById("meeting-location");
    var descEl = document.getElementById("desc");
    var startEl = document.getElementById("meeting-start");
    var endEl = document.getElementById("meeting-end");
    var isoEl = document.getElementById("meeting-scheduled-iso");
    var minsEl = document.getElementById("meeting-duration-mins");
    var durationEl = document.getElementById("meeting-duration");
    var dateInput = document.getElementById("meeting-date");
    var days = document.getElementById("days");
    var monthLabel = document.getElementById("meeting-month");
    if (titleEl) titleEl.value = event.title || "";
    if (locEl) locEl.value = event.location || "";
    if (descEl && event.description) descEl.value = event.description;
    paintMeetingClock(startHHmm, hhmmFromMs(endDate.getTime()));
    if (startEl) startEl.value = startHHmm;
    if (endEl) endEl.value = hhmmFromMs(endDate.getTime());
    if (minsEl) minsEl.value = String(minutes);
    if (durationEl) durationEl.value = durationLabel(minutes);
    if (isoEl) isoEl.value = localIsoFromMs(start.getTime());
    var parts = jalaliParts(start);
    if (days) {
      days.dataset.jy = String(parts.year);
      days.dataset.jm = String(parts.month);
    }
    if (monthLabel) monthLabel.textContent = parts.monthName + " " + faDigits(parts.year);
    if (dateInput) {
      dateInput.value = faDigits(
        parts.year + "/" + String(parts.month).padStart(2, "0") + "/" + String(parts.day).padStart(2, "0")
      );
    }
    document.querySelectorAll(".day.sel").forEach(function (el) { el.classList.remove("sel"); });
    var dayBtn = document.querySelector('.day[data-day="' + parts.day + '"]');
    if (dayBtn) dayBtn.classList.add("sel");
  }

  async function importCalendarEvents(picked, projectId) {
    var user = await S.currentUser();
    var userId = user && user.id;
    var seen = readImportedIds(userId);
    var existing = [];
    try {
      existing = await listAll("meeting", "list_meetings");
    } catch (ignored) {}
    var existingKeys = {};
    existing.forEach(function (row) {
      existingKeys[(row.title || "") + "|" + String(row.scheduled_at || "").slice(0, 16)] = true;
    });
    var created = 0;
    var skipped = 0;
    for (var i = 0; i < picked.length; i += 1) {
      var event = picked[i];
      var start = eventStartDate(event);
      var scheduledAt = localIsoFromMs(start.getTime());
      var key = (event.title || "") + "|" + scheduledAt.slice(0, 16);
      if (seen.indexOf(event.id) !== -1 || existingKeys[key]) {
        skipped += 1;
        continue;
      }
      await tool("meeting", "create_meeting", {
        title: event.title || "جلسه تقویم",
        scheduled_at: scheduledAt,
        meeting_type: "جلسه تیم",
        duration_minutes: durationFromEvent(event),
        project_id: projectId || undefined,
        visibility: projectId ? "PROJECT" : "PRIVATE",
        location: event.location || undefined,
      });
      seen.push(event.id);
      existingKeys[key] = true;
      created += 1;
    }
    writeImportedIds(userId, seen);
    return { created: created, skipped: skipped };
  }

  async function startCalendarImport(mode) {
    try {
      var payload = await loadCalendarEvents();
      var events = payload.events || [];
      if (!events.length) {
        toast("رویدادی در تقویم گوگل یا تقویم گوشی پیدا نشد");
        return;
      }
      var projectHtml = "";
      if (mode === "import") {
        var projects = [];
        try { projects = await loadProjects(); } catch (ignored) {}
        projectHtml =
          "<div class='field'><div class='label'>پروژه (اختیاری)</div><label class='box'>" +
          "<select id='cal-project'><option value=''>بدون پروژه</option>" +
          projects.map(function (row) {
            return "<option value='" + row.id + "'>" + escapeHtml(row.name) + "</option>";
          }).join("") +
          "</select></label></div>";
      }
      openCalendarSheet({
        events: events,
        mode: mode,
        usedGoogle: payload.usedGoogleFilter || payload.googleCalendars,
        projectHtml: projectHtml,
        onPick: async function (picked, projectId) {
          try {
            if (mode === "fill") {
              applyCalendarEventToForm(picked[0]);
              closeCalendarSheet();
              toast("زمان و عنوان از تقویم پر شد");
              return;
            }
            var result = await importCalendarEvents(picked, projectId);
            closeCalendarSheet();
            toast(faDigits(result.created) + " جلسه ثبت شد" + (result.skipped ? "، " + faDigits(result.skipped) + " تکراری رد شد" : ""));
            await bootMeetings();
          } catch (error) {
            toast(error.message);
          }
        },
      });
    } catch (error) {
      toast(error.message);
    }
  }

  function nowIso() {
    return new Date().toISOString().slice(0, 19);
  }

  async function fillSelect(select, records, labelFn, valueFn) {
    if (!select) return;
    var current = select.value;
    select.innerHTML = "";
    var blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "انتخاب کنید";
    select.appendChild(blank);
    records.forEach(function (row) {
      var option = document.createElement("option");
      option.value = String(valueFn ? valueFn(row) : row.id);
      option.textContent = labelFn(row);
      select.appendChild(option);
    });
    if (current) select.value = current;
  }

  async function loadProjects() {
    return listAll("crud", "list_projects");
  }

  async function loadUsers() {
    return listAll("crud", "list_users");
  }

  async function loadAssignable() {
    return listAll("crud", "list_assignable_users");
  }

  function systemRoles(row) {
    return String((row && row.roles) || "");
  }

  function isOrgManagerRole(row) {
    var roles = systemRoles(row);
    return roles.indexOf("مدیر پروژه") !== -1 || roles.indexOf("مدیر کل") !== -1;
  }

  async function fillBadge() {
    var badges = document.querySelectorAll(".badge");
    if (!badges.length) return;
    try {
      var payload = await tool("crud", "list_notifications", { is_read: false, limit: 50, offset: 0 });
      var count = (payload.records || []).length;
      badges.forEach(function (badge) {
        badge.textContent = String(count);
        badge.style.display = count ? "grid" : "none";
        var wrap = badge.closest(".bell-wrap, .bell, .hdr-tools");
        if (wrap) wrap.setAttribute("aria-label", count + " اعلان");
      });
    } catch (error) {
      badges.forEach(function (badge) {
        badge.style.display = "none";
      });
    }
  }

  function bindBells() {
    document.querySelectorAll(".bell-wrap, .bell").forEach(function (el) {
      el.style.cursor = "pointer";
      el.addEventListener("click", function () {
        location.href = "notifications.html";
      });
    });
  }

  function haystack(row) {
    return Object.keys(row || {})
      .map(function (key) {
        var value = row[key];
        return value == null ? "" : String(value);
      })
      .join(" ")
      .toLowerCase();
  }

  function matches(row, query) {
    if (!query) return true;
    return haystack(row).indexOf(query.toLowerCase()) !== -1;
  }

  var IDLE_STEPS = "۱ ضبط صدا  ·  ۲ تبدیل به متن  ·  ۳ بازبینی در همین کادر";

  function setButtonLabel(button, label, text) {
    if (label) label.textContent = text;
    else if (!button.querySelector("svg")) button.textContent = text;
  }

  function isRowLayout(el) {
    var style = getComputedStyle(el);
    if (style.display === "grid") return true;
    if (style.display !== "flex" && style.display !== "inline-flex") return false;
    return style.flexDirection === "row" || style.flexDirection === "row-reverse";
  }

  function bindSpeechButton(button, onText) {
    if (!button) return;
    var label = button.querySelector("span");
    var idleLabel = label ? label.textContent : button.textContent;
    var stepsId = button.getAttribute("data-steps");
    var steps = stepsId ? document.getElementById(stepsId) : null;
    if (!steps) {
      steps = document.createElement("p");
      steps.className = "voice-steps";
      var node = button;
      while (node.parentElement && isRowLayout(node.parentElement)) {
        node = node.parentElement;
      }
      node.insertAdjacentElement("afterend", steps);
    }
    steps.textContent = IDLE_STEPS;

    var recorder = null;
    var chunks = [];
    var recording = false;
    var busy = false;
    var liveText = "";
    var speechRec = null;

    function resetButton() {
      recording = false;
      button.classList.remove("recording");
      button.disabled = false;
      setButtonLabel(button, label, idleLabel);
    }

    function stopLiveSpeech() {
      if (!speechRec) return;
      try {
        speechRec.stop();
      } catch (ignored) {}
      speechRec = null;
    }

    function startLiveSpeech() {
      liveText = "";
      var Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!Ctor) return;
      try {
        speechRec = new Ctor();
        speechRec.lang = "fa-IR";
        speechRec.continuous = true;
        speechRec.interimResults = true;
        speechRec.onresult = function (event) {
          var parts = [];
          for (var i = 0; i < event.results.length; i += 1) {
            parts.push(event.results[i][0].transcript);
          }
          liveText = parts.join(" ").replace(/\s+/g, " ").trim();
        };
        speechRec.onerror = function () {};
        speechRec.start();
      } catch (ignored) {
        speechRec = null;
        liveText = "";
      }
    }

    button.addEventListener("click", async function () {
      if (busy) return;
      if (recording && recorder) {
        recorder.stop();
        return;
      }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || typeof MediaRecorder === "undefined") {
        toast("ضبط صدا در این مرورگر فعال نیست");
        return;
      }
      var stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (error) {
        var name = error && error.name;
        if (name === "NotAllowedError" || name === "PermissionDeniedError") {
          toast("اجازه میکروفون داده نشد. از تنظیمات گوشی اجازه ضبط صدا را بدهید");
        } else if (name === "NotFoundError") {
          toast("میکروفونی روی دستگاه پیدا نشد");
        } else if (location.protocol === "http:") {
          toast("ضبط صدا فقط روی ارتباط امن کار می‌کند");
        } else {
          toast("اجازه میکروفون داده نشد");
        }
        return;
      }
      chunks = [];
      var mimeTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/aac"];
      var mime = "";
      mimeTypes.forEach(function (type) {
        if (!mime && MediaRecorder.isTypeSupported(type)) mime = type;
      });
      recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      recorder.ondataavailable = function (event) {
        if (event.data && event.data.size) chunks.push(event.data);
      };
      recorder.onstop = async function () {
        stream.getTracks().forEach(function (track) { track.stop(); });
        stopLiveSpeech();
        recording = false;
        busy = true;
        button.disabled = true;
        setButtonLabel(button, label, "در حال تبدیل");
        steps.textContent = "مرحله ۲: فایل ضبط‌شده به متن فارسی تبدیل می‌شود";
        var blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
        try {
          await new Promise(function (resolve) { setTimeout(resolve, 120); });
          var text = liveText;
          if (!text) {
            text = await S.transcribeAudio(blob);
          } else {
            steps.textContent = "مرحله ۲: متن هنگام ضبط آماده شد";
          }
          if (!text) {
            toast("صحبتی تشخیص داده نشد");
            steps.textContent = IDLE_STEPS;
            return;
          }
          steps.textContent = "مرحله ۳: متن آماده شد";
          busy = false;
          resetButton();
          var result = onText(text, blob);
          if (result && typeof result.then === "function") result = await result;
          steps.textContent = typeof result === "string" && result ? result : "مرحله ۳: صوت و متن هر دو ذخیره شد";
        } catch (error) {
          steps.textContent = IDLE_STEPS;
          toast(error.message || "تبدیل صدا به متن انجام نشد");
        } finally {
          busy = false;
          resetButton();
        }
      };
      recorder.start(250);
      recording = true;
      button.classList.add("recording");
      setButtonLabel(button, label, "پایان ضبط");
      steps.textContent = "مرحله ۱: در حال ضبط. برای رفتن به تبدیل، دوباره بزنید";
      startLiveSpeech();
    });
  }

  async function saveTextContent(text) {
    var payload = await tool("crud", "create_content", {
      content_kind: "TEXT",
      text_body: text,
    });
    return payload.id;
  }

  async function saveCaptured(text, blob) {
    if (blob && blob.size) {
      var saved = await S.saveSpeech(text, blob);
      return saved.id;
    }
    return saveTextContent(text);
  }

  function clipOf(area) {
    return area && area._voiceBlob ? area._voiceBlob : null;
  }

  function keepClip(area, blob) {
    if (area) area._voiceBlob = blob || null;
  }

  var FA_CODE = {
    PERSON: "فرد",
    UNIT: "واحد",
    ORG: "سازمان",
    PLACE: "مکان",
    OBJECT: "شیء",
    PROJECT: "پروژه",
    TASK: "وظیفه",
    TIME: "زمان",
    ROLE: "نقش",
    positive: "مثبت",
    negative: "منفی",
    neutral: "خنثی",
    low: "کم",
    medium: "متوسط",
    high: "زیاد",
    frustration: "خستگی و نارضایتی",
    anger: "خشم",
    worry: "نگرانی",
    satisfaction: "رضایت",
    confidence: "اطمینان",
    quantity: "مقدار",
    condition: "شرط",
    change: "تغییر",
    cause: "علت",
    status: "وضعیت",
    percent: "درصد",
    amount: "مبلغ",
    count: "تعداد",
    duration: "مدت",
    ratio: "نسبت",
    explicit: "صریح",
    derived: "مستنتج از شاهد",
    total: "کل",
    part: "جزء",
    remainder: "باقی‌مانده",
    none: "بدون نقش",
    subtract: "تفریق",
    add: "جمع",
    from_evidence: "از شاهد متن",
    direct: "مستقیم",
    indirect: "غیرمستقیم",
    personal: "شخصی",
    unit: "واحدی",
    organizational: "سازمانی",
    request_handling: "پاسخگویی به درخواست‌ها",
    payment: "پرداخت",
    staffing: "تأمین نیرو",
    procurement: "تدارکات",
    reporting: "گزارش‌دهی",
    operations: "عملیات جاری",
    other: "سایر",
  };

  function faOf(code, persian) {
    var en = String(code || "").trim();
    var name = String(persian || FA_CODE[en] || "").trim();
    if (name && en && name !== en) return name + " (" + en + ")";
    return name || en;
  }

  function formatConfidence(value) {
    var number = Number(value);
    if (!isFinite(number)) return "";
    var percent = number <= 1 ? Math.round(number * 100) : Math.round(number);
    return percent + "٪";
  }

  function reviewMeta(item, extra) {
    var bits = extra ? extra.slice() : [];
    var witness = item && (item.mention_text || item.evidence);
    if (witness) bits.push("شاهد: «" + witness + "»");
    if (item && item.confidence != null && item.confidence !== "") {
      var shown = formatConfidence(item.confidence);
      if (shown) bits.push("اطمینان مدل: " + shown);
    }
    return bits.join(" · ");
  }

  function reviewItem(text, meta) {
    return meta ? { text: text, meta: meta } : text;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function reviewLines(fields) {
    var blocks = [];
    if (fields.intended_meaning) {
      blocks.push({ title: "معنای مقصود", lines: [fields.intended_meaning] });
    }
    if (fields.frame && (fields.frame.title || fields.frame.scope || fields.frame.process)) {
      var frame = fields.frame;
      var frameLines = [];
      if (frame.title) frameLines.push("عنوان: " + frame.title);
      if (frame.unit) frameLines.push("واحد: " + frame.unit);
      if (frame.process || frame.process_name) {
        frameLines.push("فرآیند: " + faOf(frame.process, frame.process_name));
      }
      if (frame.scope || frame.scope_name) {
        frameLines.push("محدوده: " + faOf(frame.scope, frame.scope_name));
      }
      if (frame.about) frameLines.push("درباره: " + frame.about);
      var frameMeta = reviewMeta(frame);
      if (frameMeta) frameLines.push(frameMeta);
      if (frameLines.length) blocks.push({ title: "قاب مسئله", lines: frameLines });
    }
    if (fields.sentiment && (fields.sentiment.polarity || fields.sentiment.intensity || fields.sentiment.polarity_name)) {
      var sentiment = fields.sentiment;
      var stance = [faOf(sentiment.polarity, sentiment.polarity_name), faOf(sentiment.intensity, sentiment.intensity_name)].filter(Boolean).join(" · ");
      blocks.push({
        title: "قطبیت",
        lines: [reviewItem(stance, reviewMeta(sentiment))],
      });
    }
    var mentions = (fields.mentions || []).map(function (item) {
      var label = [faOf(item.type, item.type_name), item.canonical_name || item.mention_text || ""].filter(Boolean).join(" · ");
      return reviewItem(label, reviewMeta(item));
    }).filter(Boolean);
    if (mentions.length) blocks.push({ title: "موجودیت‌ها", lines: mentions });
    var keywords = (fields.keywords || []).map(function (item) {
      return reviewItem(item.phrase || "", reviewMeta(item));
    }).filter(function (line) { return line && (line.text || line); });
    if (keywords.length) blocks.push({ title: "کلمه‌های کلیدی", lines: keywords });
    var topics = (fields.topics || []).map(function (item) {
      return reviewItem(faOf(item.code, item.name), reviewMeta(item));
    }).filter(Boolean);
    if (topics.length) blocks.push({ title: "موضوع‌ها", lines: topics });
    var emotions = (fields.emotions || []).map(function (item) {
      var label = [faOf(item.emotion, item.name), faOf(item.intensity, item.intensity_name)].filter(Boolean).join(" · ");
      return reviewItem(label, reviewMeta(item));
    }).filter(Boolean);
    if (emotions.length) blocks.push({ title: "هیجان‌ها", lines: emotions });
    [
      ["discourses", "ژانرها"],
      ["intents", "نیت‌ها"],
      ["rhetorics", "بیان"],
    ].forEach(function (group) {
      var lines = (fields[group[0]] || []).map(function (item) {
        var label = faOf(item.code, item.name);
        if (item.is_primary) label += " · اصلی";
        return reviewItem(label, reviewMeta(item));
      }).filter(Boolean);
      if (lines.length) blocks.push({ title: group[1], lines: lines });
    });
    var causes = (fields.facts || []).filter(function (item) { return item.kind === "cause"; });
    var otherFacts = (fields.facts || []).filter(function (item) { return item.kind !== "cause"; });
    if (causes.length) {
      blocks.push({
        title: "علت و معلول",
        lines: causes.map(function (item) {
          var extra = [];
          if (item.effect) extra.push("معلول: " + item.effect);
          if (item.grounding || item.grounding_name) extra.push("صراحت: " + faOf(item.grounding, item.grounding_name));
          return reviewItem(faOf(item.kind, item.kind_name) + (item.name ? " · " + item.name : ""), reviewMeta(item, extra));
        }),
      });
    }
    if (otherFacts.length) {
      blocks.push({
        title: "فکت‌ها",
        lines: otherFacts.map(function (item) {
          var extra = [];
          if (item.value != null && item.value !== "") {
            extra.push("مقدار: " + item.value + (item.unit || item.unit_name ? " " + faOf(item.unit, item.unit_name) : ""));
          }
          if (item.role && item.role !== "none") extra.push("نقش: " + faOf(item.role, item.role_name));
          if (item.previous || item.current) {
            extra.push("از «" + (item.previous || "—") + "» به «" + (item.current || "—") + "»");
          }
          if (item.grounding || item.grounding_name) extra.push("صراحت: " + faOf(item.grounding, item.grounding_name));
          return reviewItem(faOf(item.kind, item.kind_name) + (item.name ? " · " + item.name : ""), reviewMeta(item, extra));
        }),
      });
    }
    var quotes = (fields.quotes || []).map(function (item) {
      var label = faOf(item.mode, item.mode_name);
      var body = (item.attributed_to ? item.attributed_to + ": " : "") + (item.quoted_text || "");
      if (body.trim()) label = label ? label + " · " + body : body;
      return reviewItem(label, reviewMeta(item));
    }).filter(Boolean);
    if (quotes.length) blocks.push({ title: "نقل‌قول‌ها", lines: quotes });
    return blocks;
  }

  function openReview(preview) {
    return new Promise(function (resolve) {
      var fields = preview.fields || {};
      var sheet = document.createElement("div");
      sheet.className = "review-sheet";
      var blocks = reviewLines(fields);
      var body = blocks.length
        ? blocks.map(function (block) {
            return (
              "<section class='review-group'><strong>" +
              block.title +
              "</strong><ul>" +
              block.lines.map(function (line) {
                var text = typeof line === "string" ? line : line.text;
                var meta = typeof line === "string" ? "" : line.meta;
                if (!text && !meta) return "";
                return "<li>" + escapeHtml(text) + (meta ? "<span class='review-meta'>" + escapeHtml(meta) + "</span>" : "") + "</li>";
              }).join("") +
              "</ul></section>"
            );
          }).join("")
        : "<p class='review-note'>موردی از این متن استخراج نشد.</p>";
      var warn = preview.layer_errors && Object.keys(preview.layer_errors).length
        ? "<p class='review-note'>برخی لایه‌ها نیامدند.</p>"
        : "";
      sheet.innerHTML =
        "<div class='review-card' role='dialog' aria-modal='true'>" +
        "<h2>موارد استخراج‌شده</h2>" +
        "<p class='review-note'>متن ذخیره شده است. اگر صوت بوده، خود فایل هم مانده. با تأیید، همین موارد در پایگاه می‌نشینند.</p>" +
        warn +
        body +
        "<div class='review-actions'>" +
        "<button class='primary-btn' type='button' data-act='save'>ذخیره در پایگاه</button>" +
        "<button class='ghost-btn' type='button' data-act='cancel'>انصراف</button>" +
        "</div></div>";
      document.body.appendChild(sheet);
      sheet.addEventListener("click", async function (event) {
        var act = event.target && event.target.getAttribute("data-act");
        if (!act) return;
        if (act === "cancel") {
          sheet.remove();
          toast("متن خام ماند؛ موارد استخراج ذخیره نشد");
          resolve(null);
          return;
        }
        var button = event.target;
        button.disabled = true;
        try {
          var saved = await S.commitAnalysis(fields);
          sheet.remove();
          var embedded = saved.embedding && saved.embedding.status === "success";
          toast("موارد استخراج ذخیره شد" + (saved.id ? " (#" + saved.id + ")" : "") + (embedded ? " و امبد شد" : ""));
          resolve(saved);
        } catch (error) {
          button.disabled = false;
          toast(error.message || "ذخیرهٔ استخراج انجام نشد");
        }
      });
    });
  }

  async function analyzeSaved(sourceType, sourceId) {
    toast("متن خام ذخیره شد. در حال استخراج…");
    try {
      var preview = await S.previewAnalysis(sourceType, sourceId);
      return await openReview(preview);
    } catch (error) {
      toast("متن خام ذخیره شد، اما استخراج انجام نشد: " + error.message);
      return null;
    }
  }

  var homeUserId = 0;
  var homeProfile = null;
  var homeRestoring = false;

  function homeMemoryKey() {
    return "management_home_thread_" + homeUserId;
  }

  function persistHomeThread() {
    if (!homeUserId || homeRestoring) return;
    var thread = document.getElementById("home-thread");
    if (!thread) return;
    var turns = [];
    thread.querySelectorAll("article.turn").forEach(function (item) {
      var role = item.classList.contains("turn-bot") ? "bot" : "user";
      var html = item.innerHTML.replace(/src="blob:[^"]*"/g, 'src=""');
      turns.push({ role: role, html: html });
    });
    turns = turns.slice(-24);
    var payloads = [JSON.stringify(turns)];
    var slim = turns.map(function (turn) {
      return {
        role: turn.role,
        html: String(turn.html || "").replace(/\ssrc="data:[^"]*"/g, ""),
      };
    });
    payloads.push(JSON.stringify(slim.slice(-16)));
    payloads.push(JSON.stringify(slim.slice(-8).map(function (turn) {
      return { role: turn.role, html: String(turn.html || "").replace(/<img[^>]*>/g, "") };
    })));
    for (var i = 0; i < payloads.length; i += 1) {
      try {
        localStorage.setItem(homeMemoryKey(), payloads[i]);
        return;
      } catch (error) {}
    }
  }

  function restoreHomeThread() {
    if (!homeUserId) return;
    var raw = "";
    try {
      raw = localStorage.getItem(homeMemoryKey()) || "";
    } catch (error) {
      return;
    }
    if (!raw) return;
    var turns = [];
    try {
      turns = JSON.parse(raw);
    } catch (error) {
      return;
    }
    if (!turns || !turns.length) return;
    homeRestoring = true;
    turns.forEach(function (turn) {
      if (!turn || (turn.role !== "user" && turn.role !== "bot") || !turn.html) return;
      pushHomeTurn(turn.role, turn.html);
    });
    homeRestoring = false;
  }

  function openHomeThread() {
    var body = document.querySelector(".chat-body");
    var thread = document.getElementById("home-thread");
    if (body) body.classList.add("is-talking");
    if (thread) thread.hidden = false;
    return thread;
  }

  function pushHomeTurn(role, html) {
    var thread = openHomeThread();
    if (!thread) return null;
    var item = document.createElement("article");
    item.className = "turn turn-" + role;
    item.innerHTML = html;
    thread.appendChild(item);
    thread.scrollTop = thread.scrollHeight;
    persistHomeThread();
    return item;
  }

  function imageDataUrl(file) {
    return new Promise(function (resolve) {
      if (!file || String(file.type || "").indexOf("image/") !== 0) {
        resolve("");
        return;
      }
      var reader = new FileReader();
      reader.onerror = function () { resolve(""); };
      reader.onload = function () {
        var img = new Image();
        img.onload = function () {
          var maxEdge = 720;
          var scale = Math.min(1, maxEdge / Math.max(img.width || 1, img.height || 1));
          var canvas = document.createElement("canvas");
          canvas.width = Math.max(1, Math.round((img.width || 1) * scale));
          canvas.height = Math.max(1, Math.round((img.height || 1) * scale));
          var ctx = canvas.getContext("2d");
          if (!ctx) {
            resolve("");
            return;
          }
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          try {
            resolve(canvas.toDataURL("image/jpeg", 0.72));
          } catch (error) {
            resolve("");
          }
        };
        img.onerror = function () { resolve(""); };
        img.src = String(reader.result || "");
      };
      reader.readAsDataURL(file);
    });
  }

  function bindHomeUpload(buttonId, inputId, label) {
    var button = document.getElementById(buttonId);
    var input = document.getElementById(inputId);
    if (!button || !input || button.dataset.bound) return;
    button.dataset.bound = "1";
    button.addEventListener("click", function () {
      input.click();
    });
    input.addEventListener("change", async function () {
      var file = input.files && input.files[0];
      input.value = "";
      if (!file) return;
      var queryInput = document.getElementById("home-query");
      var query = queryInput ? String(queryInput.value || "").trim() : "";
      var pending = pushHomeTurn("user", "<p>در حال ارسال " + escapeHtml(label) + "…</p>");
      try {
        var preview = await imageDataUrl(file);
        var saved = await S.saveMedia(file);
        var html = mediaTurnHtml(file, saved, label, preview);
        if (query) {
          if (pending) pending.remove();
          if (queryInput) queryInput.value = "";
          await answerHome(query, { userHtml: html + "<p>" + escapeHtml(query) + "</p>" });
          return;
        }
        if (pending) pending.innerHTML = html;
        if (label === "عکس") {
          pushHomeTurn("bot", "<p>عکس در گفتگو ماند. نام پروژه یا فرد را بنویسید یا بگویید تا درصد پیشرفت بیاید.</p>");
        }
        persistHomeThread();
      } catch (error) {
        if (pending) pending.innerHTML = "<p>" + escapeHtml(error.message || "ارسال انجام نشد") + "</p>";
        persistHomeThread();
      }
    });
  }

  function mediaTurnHtml(file, saved, label, previewUrl) {
    var name = escapeHtml(file.name || label);
    var note = saved && saved.id ? " (شماره " + saved.id + ")" : "";
    var type = file.type || "";
    if (type.indexOf("image/") === 0 && previewUrl) {
      return "<p>" + escapeHtml(label) + note + "</p><img alt=\"" + name + "\" src=\"" + previewUrl + "\">";
    }
    if (type.indexOf("video/") === 0) {
      return "<p>" + escapeHtml(label) + note + "</p><video controls src=\"" + URL.createObjectURL(file) + "\"></video>";
    }
    return "<p>" + escapeHtml(label) + " «" + name + "»" + note + "</p>";
  }

  async function bootHome() {
    var user = await S.currentUser();
    if (!user) return;
    homeUserId = Number(user.id || user.user_id || 0);
    homeProfile = user;
    setText("session-name", displayName(user));
    setText("session-role", (user.roles && user.roles[0]) || "کاربر");
    var hints = document.querySelectorAll(".chat-body > .hint");
    var queryBox = document.getElementById("home-query");
    if (isDirector(user)) {
      if (hints[0]) hints[0].textContent = "نام پروژه یا فرد را بگویید.";
      if (hints[1]) hints[1].textContent = "پیشرفت و گزارش همان محدوده می‌آید.";
      if (queryBox) queryBox.placeholder = "جستجو در پروژه‌ها و افراد...";
    } else if (canManage(user)) {
      if (hints[0]) hints[0].textContent = "درباره پروژه‌ها و اعضای خودتان بپرسید.";
      if (hints[1]) hints[1].textContent = "افراد دیگر سازمان‌ها اینجا نمی‌آیند.";
      if (queryBox) queryBox.placeholder = "جستجو در پروژه‌ها و اعضای خودتان...";
    } else {
      if (hints[0]) hints[0].textContent = "درباره تسک خودتان یا گزارشی که داده‌اید بپرسید.";
      if (hints[1]) hints[1].textContent = "سطح دسترسی داخل پروژه را مدیر پروژه تعیین می‌کند.";
      if (queryBox) queryBox.placeholder = "تسک‌ها و گزارش‌های خودتان...";
    }
    if (!canManage(user)) {
      document.querySelectorAll(".cta-project, .cta-meet").forEach(function (link) {
        link.hidden = true;
      });
    }
    restoreHomeThread();
    var logout = document.getElementById("logout");
    if (logout) logout.addEventListener("click", function () { S.logout(); });

    var composer = document.getElementById("home-composer");
    var input = document.getElementById("home-query");
    if (composer) {
      composer.addEventListener("submit", function (event) {
        event.preventDefault();
        var text = (input && input.value) || "";
        if (input) input.value = "";
        answerHome(text);
      });
    }
    bindSpeechButton(document.getElementById("home-voice"), async function (text, blob) {
      var note = "";
      if (blob && blob.size) {
        try {
          var saved = await S.saveSpeech(text, blob);
          if (saved && saved.id) note = " (شماره " + saved.id + ")";
        } catch (error) {
          toast(error.message || "ذخیرهٔ صوت انجام نشد");
        }
      }
      var userHtml = "<p>" + escapeHtml(text) + "</p>";
      if (blob && blob.size) userHtml += "<p>صوت ثبت شد" + note + ".</p>";
      await answerHome(text, { userHtml: userHtml });
      return "مرحله ۳: جواب سؤال آماده شد";
    });
    var textBtn = document.getElementById("home-text");
    if (textBtn && input) {
      textBtn.addEventListener("click", function () {
        input.focus();
      });
    }
    bindHomeUpload("home-file", "home-file-pick", "فایل");
    bindHomeUpload("home-image", "home-image-pick", "عکس");
    bindHomeUpload("home-video", "home-video-pick", "فیلم");
  }

  function foldFa(value) {
    return String(value || "")
      .replace(/[يی]/g, "ی")
      .replace(/[كک]/g, "ک")
      .replace(/[أإآ]/g, "ا")
      .replace(/\s+/g, " ")
      .trim();
  }

  function personName(row) {
    return [row.first_name, row.last_name].filter(Boolean).join(" ").trim() || row.username || "";
  }

  async function answerHome(raw, options) {
    options = options || {};
    var query = foldFa(raw);
    if (!query) {
      toast(canManage(homeProfile) ? "نام پروژه یا فرد را بگویید" : "تسک یا گزارش خود را بگویید");
      return;
    }
    var userHtml = options.userHtml || ("<p>" + escapeHtml(String(raw).trim()) + "</p>");
    pushHomeTurn("user", userHtml);
    var panel = pushHomeTurn("bot", "<p>در حال پیدا کردن…</p>");
    try {
      if (!canManage(homeProfile)) {
        await showOwnWork(panel, query, String(raw).trim());
        return;
      }
      var projects = await loadProjects();
      var users = isDirector(homeProfile) ? await loadUsers() : await loadAssignable();
      var wantsProject = query.indexOf("پروژه") !== -1;
      var project = null;
      projects.forEach(function (row) {
        var name = foldFa(row.name);
        if (name && query.indexOf(name) !== -1 && (!project || name.length > foldFa(project.name).length)) {
          project = row;
        }
      });
      var person = null;
      users.forEach(function (row) {
        var full = foldFa(personName(row));
        var first = foldFa(row.first_name);
        var hit = (full.length > 1 && query.indexOf(full) !== -1) || (first.length > 1 && query.indexOf(first) !== -1);
        if (hit && (!person || full.length > foldFa(personName(person)).length)) person = row;
      });
      if (wantsProject && project) {
        await showProjectBrief(panel, project);
        return;
      }
      if (person && !wantsProject) {
        await showPersonBrief(panel, person);
        return;
      }
      if (project) {
        await showProjectBrief(panel, project);
        return;
      }
      if (person) {
        await showPersonBrief(panel, person);
        return;
      }
      var similar = await tool("embedding", "search_similar", { query: String(raw).trim(), limit: 6 });
      var records = similar.records || [];
      if (records.length && panel) {
        panel.innerHTML = semanticPanelHtml(records);
        return;
      }
      if (panel) panel.innerHTML = "<p>مورد مشابهی در بردارها پیدا نشد.</p>";
    } catch (error) {
      if (panel) panel.innerHTML = "<p>" + escapeHtml(error.message) + "</p>";
    } finally {
      persistHomeThread();
      if (panel && panel.parentNode) panel.parentNode.scrollTop = panel.parentNode.scrollHeight;
    }
  }

  async function showProjectBrief(panel, project) {
    if (!panel) return;
    var progress = {};
    try {
      progress = await tool("stats", "get_project_progress", { project_id: project.id });
    } catch (ignored) {}
    var percent = progress.progress_percent != null ? progress.progress_percent : "—";
    var reports = [];
    try {
      var chats = await listAll("crud", "list_chats", { project_id: project.id });
      var chatIds = {};
      chats.forEach(function (row) { chatIds[row.id] = true; });
      var messages = await listAll("crud", "list_messages");
      reports = messages.filter(function (row) {
        return chatIds[row.chat_id] || Number(row.project_id) === Number(project.id);
      }).slice(0, 6);
    } catch (ignored) {}
    var lines = reports.length
      ? reports.map(function (row) {
          return "<li>" + escapeHtml(String(row.text || row.task_title || "").slice(0, 180)) + "</li>";
        }).join("")
      : "<li>گزارشی ثبت نشده.</li>";
    panel.innerHTML =
      "<h2>" + escapeHtml(project.name) + "</h2>" +
      "<p class='brief-percent'>پیشرفت " + escapeHtml(String(percent)) + "٪</p>" +
      "<p>" + escapeHtml(project.project_status_name || "") + "</p>" +
      "<strong>گزارش‌ها</strong><ul>" + lines + "</ul>" +
      "<a href='project-details.html?id=" + project.id + "'>جزئیات پروژه</a>";
  }

  async function showPersonBrief(panel, person) {
    if (!panel) return;
    var userId = Number(person.user_id || person.id);
    var rows = [];
    try {
      var payload = await tool("stats", "get_member_workload", { user_id: userId });
      rows = payload.records || [];
    } catch (ignored) {}
    var open = 0;
    var done = 0;
    var late = 0;
    rows.forEach(function (row) {
      open += Number(row.open_tasks || 0);
      done += Number(row.completed_tasks || 0);
      late += Number(row.overdue_tasks || 0);
    });
    var total = open + done;
    var percent = total ? Math.round((done / total) * 100) : 0;
    panel.innerHTML =
      "<h2>" + escapeHtml(personName(person)) + "</h2>" +
      "<p class='brief-percent'>پیشرفت " + percent + "٪</p>" +
      "<ul><li>وظیفهٔ باز: " + open + "</li><li>تکمیل‌شده: " + done + "</li><li>عقب‌افتاده: " + late + "</li></ul>";
  }

  async function showOwnWork(panel, query, raw) {
    if (!panel) return;
    var tasks = [];
    var reports = [];
    try {
      tasks = await listAll("crud", "list_tasks");
      tasks = tasks.filter(function (row) {
        return Number(row.assigned_to_user_id) === homeUserId;
      });
    } catch (ignored) {}
    try {
      var messages = await listAll("crud", "list_messages");
      reports = messages.filter(function (row) {
        return Number(row.sender_user_id) === homeUserId;
      });
    } catch (ignored) {}
    var task = null;
    tasks.forEach(function (row) {
      var title = foldFa(row.title);
      if (title && query.indexOf(title) !== -1 && (!task || title.length > foldFa(task.title).length)) {
        task = row;
      }
    });
    var report = null;
    reports.forEach(function (row) {
      var text = foldFa(row.text);
      if (text && text.length > 1 && query.indexOf(text.slice(0, 40)) !== -1) report = row;
    });
    var asksOwn = /تسک|وظیفه|گزارش|کار من|پیشرفت/.test(query);
    if (!task && !report && !asksOwn) {
      try {
        var similar = await tool("embedding", "search_similar", { query: raw, limit: 6 });
        var records = similar.records || [];
        if (records.length) {
          panel.innerHTML = semanticPanelHtml(records);
          return;
        }
      } catch (ignored) {}
    }
    if (task) {
      var related = reports.filter(function (row) {
        return Number(row.task_id) === Number(task.id);
      }).slice(0, 6);
      var lines = related.length
        ? related.map(function (row) {
            return "<li>" + escapeHtml(String(row.text || "").slice(0, 180)) + "</li>";
          }).join("")
        : "<li>گزارشی برای این تسک نداده‌اید.</li>";
      panel.innerHTML =
        "<h2>" + escapeHtml(task.title || "") + "</h2>" +
        "<p>" + escapeHtml(task.status_name || "") + "</p>" +
        "<strong>گزارش‌های شما</strong><ul>" + lines + "</ul>" +
        "<a href='task-details.html?id=" + task.id + "'>جزئیات تسک</a>";
      return;
    }
    var taskLines = tasks.length
      ? tasks.slice(0, 8).map(function (row) {
          return "<li>" + escapeHtml(row.title || "") + " · " + escapeHtml(row.status_name || "") + "</li>";
        }).join("")
      : "<li>تسکی به شما سپرده نشده.</li>";
    var reportLines = reports.length
      ? reports.slice(0, 6).map(function (row) {
          return "<li>" + escapeHtml(String(row.text || row.task_title || "").slice(0, 180)) + "</li>";
        }).join("")
      : "<li>گزارشی نفرستاده‌اید.</li>";
    panel.innerHTML =
      "<h2>کارهای شما</h2><strong>تسک‌ها</strong><ul>" + taskLines +
      "</ul><strong>گزارش‌ها</strong><ul>" + reportLines + "</ul>";
  }

  async function bootMeetings() {
    var importBtn = document.getElementById("import-calendar");
    var importBar = document.getElementById("import-calendar-bar");
    if (importBtn && !importBtn.dataset.bound) {
      importBtn.dataset.bound = "1";
      importBtn.addEventListener("click", function () { startCalendarImport("import"); });
    }
    if (importBar && !importBar.dataset.bound) {
      importBar.dataset.bound = "1";
      importBar.addEventListener("click", function () { startCalendarImport("import"); });
    }
    var list = document.getElementById("meeting-list");
    if (!list) return;
    try {
      var records = await listAll("meeting", "list_meetings");
      if (!records.length) {
        empty(list, "جلسه‌ای ثبت نشده. از خانه جلسه جدید بسازید.");
        return;
      }
      list.innerHTML = "";
      records.forEach(function (row) {
        var waiting = row.status_name === "برنامه‌ریزی شده";
        list.appendChild(
          cardLink(
            "meeting-details.html?id=" + row.id,
            '<span class="tag' + (waiting ? " wait" : "") + '">' +
              (row.status_name || "جلسه") +
              "</span><h2>" +
              (row.title || "بدون عنوان") +
              "</h2><p>" +
              (row.location || row.meeting_type_name || "") +
              '</p><div class="meta"><div><span>تاریخ </span>' +
              faStamp(row.scheduled_at) +
              "</div><div><span>ساعت </span>" +
              faTime(row.scheduled_at) +
              (row.scheduled_end_at ? " - " + faTime(row.scheduled_end_at) : "") +
              "</div></div>"
          )
        );
      });
    } catch (error) {
      empty(list, error.message);
    }
  }

  function paintMeetingDate() {
    var days = document.getElementById("days");
    var selected = document.querySelector(".day.sel");
    var dateInput = document.getElementById("meeting-date");
    if (!days || !selected || !dateInput) return;
    var day = String(selected.dataset.day || "").padStart(2, "0");
    var month = String(days.dataset.jm || "").padStart(2, "0");
    dateInput.value = faDigits(days.dataset.jy + "/" + month + "/" + day);
  }

  async function bootNewMeeting() {
    var user = await S.currentUser();
    if (!user) return;
    if (!canManage(user)) {
      toast("ثبت جلسه برای مدیر سازمان است");
      location.replace("meetings.html");
      return;
    }
    setText("session-name", displayName(user));
    setText("session-hello", "سلام " + displayName(user));
    bindMeetingClock();
    var back = document.getElementById("meeting-back");
    var presetProject = Number(param("project_id") || 0);
    if (back && presetProject) back.href = "project-details.html?id=" + presetProject;
    var mapBtn = document.getElementById("open-map-picker");
    if (mapBtn) mapBtn.addEventListener("click", openMapPicker);
    var today = jalaliParts(new Date());
    var days = document.getElementById("days");
    var monthLabel = document.getElementById("meeting-month");
    if (days) {
      days.dataset.jy = String(today.year);
      days.dataset.jm = String(today.month);
    }
    if (monthLabel) monthLabel.textContent = today.monthName + " " + faDigits(today.year);
    document.querySelectorAll(".day.sel").forEach(function (el) { el.classList.remove("sel"); });
    var todayBtn = document.querySelector('.day[data-day="' + today.day + '"]');
    if (todayBtn) todayBtn.classList.add("sel");
    paintMeetingDate();
    if (days) {
      days.addEventListener("click", function (event) {
        var day = event.target.closest(".day[data-day]");
        if (!day) return;
        document.querySelectorAll(".day.sel").forEach(function (el) { el.classList.remove("sel"); });
        day.classList.add("sel");
        var isoEl = document.getElementById("meeting-scheduled-iso");
        if (isoEl) isoEl.value = "";
        paintMeetingDate();
      });
    }
    var projectSelect = document.getElementById("meeting-project");
    if (projectSelect) {
      try {
        await fillSelect(projectSelect, await loadProjects(), function (row) {
          return row.name;
        });
        if (presetProject) projectSelect.value = String(presetProject);
      } catch (error) {
        toast(error.message);
      }
    }
    var submit = document.getElementById("meeting-submit");
    var send = document.getElementById("meeting-send");
    if (!submit && !send) return;
    async function createMeeting() {
      var titleEl = document.getElementById("meeting-title");
      var hint = document.querySelector(".hint");
      var title = (titleEl && titleEl.value || "").trim() || ((hint && hint.value) || "").trim();
      if (!title) {
        toast("عنوان جلسه لازم است");
        return;
      }
      if (titleEl && !titleEl.value.trim() && hint) titleEl.value = title;
      var start = document.getElementById("meeting-hour")
        ? hhmmFromParts(document.getElementById("meeting-hour"), document.getElementById("meeting-minute"))
        : ((document.getElementById("meeting-start") || {}).value || "10:00");
      var end = document.getElementById("meeting-end-hour")
        ? hhmmFromParts(document.getElementById("meeting-end-hour"), document.getElementById("meeting-end-minute"))
        : ((document.getElementById("meeting-end") || {}).value || "11:00");
      var day = Number((document.querySelector(".day.sel") || {}).dataset.day) || today.day;
      var isoPreset = ((document.getElementById("meeting-scheduled-iso") || {}).value || "").trim();
      var projectId = Number((projectSelect && projectSelect.value) || 0);
      var locationText = ((document.getElementById("meeting-location") || {}).value || "").trim();
      var desc = ((document.getElementById("desc") || {}).value || "").trim();
      if (submit) submit.disabled = true;
      if (send) send.disabled = true;
      try {
        var created = await tool("meeting", "create_meeting", {
          title: title,
          scheduled_at: isoPreset || isoFromJalali(Number(days.dataset.jy), Number(days.dataset.jm), day, start),
          meeting_type: "جلسه تیم",
          duration_minutes: minutesBetween(start, end),
          project_id: projectId || undefined,
          visibility: projectId ? "PROJECT" : "PRIVATE",
          location: locationText || undefined,
        });
        if (desc) {
          var descArea = document.getElementById("desc");
          var contentId = await saveCaptured(desc, clipOf(descArea));
          keepClip(descArea, null);
          await tool("meeting", "record_meeting", { id: created.id, content_id: contentId });
          await analyzeSaved("meeting", created.id);
        }
        location.replace("meeting-details.html?id=" + created.id);
      } catch (error) {
        toast(error.message);
        if (submit) submit.disabled = false;
        if (send) send.disabled = false;
      }
    }
    if (submit) submit.addEventListener("click", createMeeting);
    if (send) send.addEventListener("click", createMeeting);
    var fillCal = document.getElementById("fill-from-calendar");
    if (fillCal) fillCal.addEventListener("click", function () { startCalendarImport("fill"); });
    bindSpeechButton(document.getElementById("meeting-voice"), function (text, blob) {
      var area = document.getElementById("desc");
      if (area) {
        area.value = (area.value ? area.value + "\n" : "") + text;
        keepClip(area, blob);
        area.dispatchEvent(new Event("input"));
      }
      toast("متن صدا آماده است. با ثبت جلسه، صوت و متن هر دو ذخیره می‌شوند");
    });
  }

  async function bootMeetingDetails() {
    var id = Number(param("id"));
    if (!id) {
      toast("شناسه جلسه نیست");
      return;
    }
    try {
      var meeting = await tool("meeting", "get_meeting", { id: id });
      setText("meeting-title", meeting.title);
      setText("meeting-lead", meeting.meeting_type_name || meeting.location || "");
      setText("meeting-status", meeting.status_name);
      setText("meeting-location", meeting.location || "—");
      setText("meeting-time", faTime(meeting.scheduled_at) + (meeting.scheduled_end_at ? " - " + faTime(meeting.scheduled_end_at) : ""));
      setText("meeting-date", faStamp(meeting.scheduled_at));
      var summary = "وضعیت: " + (meeting.status_name || "—");
      if (meeting.content_id) {
        try {
          var content = await tool("crud", "get_content", { id: meeting.content_id });
          summary = content.text_body || summary;
        } catch (ignored) {}
      }
      setText("meeting-summary", summary);
      var box = document.getElementById("meeting-people");
      if (box) {
        box.innerHTML = "";
        (meeting.participants || []).forEach(function (person) {
          var item = document.createElement("article");
          item.className = "msg";
          item.innerHTML =
            '<div class="msg-body"><div class="msg-meta"><span class="msg-name">' +
            (person.role || "شرکت‌کننده") +
            "</span></div><div class=\"bubble\"><p>کاربر " +
            (person.user_id || person.external_contact_id || "—") +
            "</p></div></div>";
          box.appendChild(item);
        });
        if (!(meeting.participants || []).length) {
          box.textContent = "شرکت‌کننده‌ای ثبت نشده.";
        }
      }
    } catch (error) {
      toast(error.message);
    }
    var form = document.getElementById("meeting-record");
    if (form) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        var note = document.getElementById("meeting-note");
        var text = ((note && note.value) || "").trim();
        if (!text) {
          toast("متن ضبط خالی است");
          return;
        }
        try {
          var contentId = await saveCaptured(text, clipOf(note));
          keepClip(note, null);
          await tool("meeting", "record_meeting", { id: id, content_id: contentId });
          toast("ضبط جلسه ذخیره شد");
          await analyzeSaved("meeting", id);
          setText("meeting-summary", text);
        } catch (error) {
          toast(error.message);
        }
      });
    }
    bindSpeechButton(document.getElementById("meeting-record-voice"), function (text, blob) {
      var area = document.getElementById("meeting-note");
      if (area) {
        area.value = (area.value ? area.value + "\n" : "") + text;
        keepClip(area, blob);
      }
      toast("متن صدا آماده است. با ارسال، صوت و متن ذخیره می‌شوند");
    });
  }

  async function bootProjects() {
    var list = document.getElementById("project-list");
    if (!list) return;
    try {
      var records = await loadProjects();
      if (!records.length) {
        empty(list, "پروژه‌ای ندارید. پروژه جدید بسازید.");
        return;
      }
      list.innerHTML = "";
      records.forEach(function (row) {
        list.appendChild(
          cardLink(
            "project-details.html?id=" + row.id,
            '<span class="tag wait">' +
              (row.project_status_name || "") +
              "</span><h2>" +
              (row.name || "") +
              "</h2><p>" +
              (row.description || row.project_type_name || "") +
              '</p><div class="meta"><div><span>شروع </span>' +
              faStamp(row.start_date) +
              "</div><div><span>نوع </span>" +
              (row.project_type_name || "") +
              "</div></div>"
          )
        );
      });
    } catch (error) {
      empty(list, error.message);
    }
  }

  async function bootNewProject() {
    var form = document.getElementById("project-form");
    var submit = document.getElementById("project-submit");
    var send = document.getElementById("project-send");
    var addMember = document.getElementById("project-add-member");
    if (!form && !submit && !send) return;

    var user = await S.currentUser();
    if (!user) return;
    if (!canManage(user)) {
      toast("ساخت پروژه برای مدیر سازمان است");
      location.replace("projects.html");
      return;
    }

    var list = document.getElementById("project-member-list");
    if (list) {
      list.innerHTML =
        "<div class='live-member'><span>" +
        displayName(user) +
        "</span><em>مدیر پروژه بعد از ثبت</em></div>";
    }

    var startEl = document.getElementById("project-start");
    var endEl = document.getElementById("project-end");
    if (startEl && !startEl.value) {
      var today = new Date();
      var later = new Date();
      later.setDate(later.getDate() + 30);
      startEl.value = today.toISOString().slice(0, 10);
      if (endEl) endEl.value = later.toISOString().slice(0, 10);
    }

    var picked = [];
    var people = [];
    var picker = document.getElementById("project-member-picker");

    function paintPicked() {
      if (!list) return;
      var creator =
        "<div class='live-member'><span>" +
        displayName(user) +
        "</span><em>مدیر پروژه بعد از ثبت</em></div>";
      var extra = picked
        .map(function (row) {
          return (
            "<div class='live-member'><span>" +
            displayName(row) +
            "</span><em>" +
            (row.username || "") +
            "</em></div>"
          );
        })
        .join("");
      list.innerHTML = creator + extra;
    }

    function paintPicker() {
      if (!picker) return;
      picker.innerHTML = "";
      var others = people.filter(function (row) {
        return Number(row.id) !== Number(user.id);
      });
      if (!others.length) {
        picker.innerHTML = "<p class='member-note'>کاربری برای انتخاب نیست.</p>";
        return;
      }
      others.forEach(function (row) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "member-pick";
        var chosen = picked.some(function (item) { return item.id === row.id; });
        if (chosen) button.classList.add("on");
        button.innerHTML =
          "<span>" + displayName(row) + "</span><em>" + (chosen ? "انتخاب شد" : row.username || "") + "</em>";
        button.addEventListener("click", function () {
          if (chosen) {
            picked = picked.filter(function (item) { return item.id !== row.id; });
          } else {
            picked.push(row);
          }
          paintPicker();
          paintPicked();
        });
        picker.appendChild(button);
      });
    }

    paintPicked();
    if (addMember) {
      addMember.addEventListener("click", async function () {
        if (!picker) return;
        var open = !picker.hidden;
        if (open) {
          picker.hidden = true;
          return;
        }
        picker.hidden = false;
        if (!people.length) {
          try {
            people = await loadAssignable();
          } catch (error) {
            toast(error.message);
            return;
          }
        }
        paintPicker();
      });
    }

    bindSpeechButton(document.getElementById("project-voice"), function (text) {
      var area = document.getElementById("project-desc");
      if (area) area.value = (area.value ? area.value + "\n" : "") + text;
      var bubble = document.querySelector(".chat-card .bubble p");
      if (bubble) bubble.textContent = text;
      toast("متن صدا آماده است و با ایجاد پروژه ذخیره می‌شود");
    });

    async function createProject() {
      var nameEl = document.getElementById("project-name");
      var name = ((nameEl && nameEl.value) || "").trim();
      if (!name) {
        toast("نام پروژه لازم است");
        return;
      }
      if (submit) submit.disabled = true;
      if (send) send.disabled = true;
      try {
        var typeEl = document.getElementById("project-type");
        var statusEl = document.getElementById("project-status");
        var descEl = document.getElementById("project-desc");
        var startEl = document.getElementById("project-start");
        var endEl = document.getElementById("project-end");
        var startValue = (startEl && startEl.value) || "";
        var endValue = (endEl && endEl.value) || "";
        if (!startValue || !endValue) {
          toast("زمان آغاز و پایان لازم است");
          if (submit) submit.disabled = false;
          if (send) send.disabled = false;
          return;
        }
        var created = await tool("crud", "create_project", {
          name: name,
          description: ((descEl && descEl.value) || "").trim() || undefined,
          project_type: (typeEl && typeEl.value) || "اجرایی",
          project_status: (statusEl && statusEl.value) || "در انتظار شروع",
          start_date: startValue,
          end_date: endValue,
        });
        for (var i = 0; i < picked.length; i += 1) {
          await tool("crud", "create_project_member", {
            project_id: created.id,
            user_id: picked[i].id,
            project_role: "عضو",
          });
        }
        location.replace("project-details.html?id=" + created.id);
      } catch (error) {
        toast(error.message);
        if (submit) submit.disabled = false;
        if (send) send.disabled = false;
      }
    }

    if (form) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        await createProject();
      });
    }
    if (submit) submit.addEventListener("click", createProject);
    if (send) send.addEventListener("click", createProject);
  }

  async function bootProjectDetails() {
    var id = Number(param("id"));
    if (!id) {
      try {
        var records = await loadProjects();
        if (records[0]) {
          location.replace("project-details.html?id=" + records[0].id);
          return;
        }
        toast("پروژه‌ای نیست");
        return;
      } catch (error) {
        toast(error.message);
        return;
      }
    }
    try {
      var project = await tool("crud", "get_project", { id: id });
      setText("project-status-pill", project.project_status_name);
      setText("project-title", project.name);
      setText("project-lead", project.description || project.project_type_name || "");
      setText("project-end", faStamp(project.end_date));
      setText("project-start", faStamp(project.start_date));
      setText("project-desc", project.description || "توضیحی ثبت نشده.");
      setText("project-mini-status", project.project_status_name);
      setText("project-mini-type", project.project_type_name);
      var members = await listAll("crud", "list_project_members", { project_id: id });
      setText("project-team-count", members.length + " نفر");
      var team = document.getElementById("project-team");
      if (team) {
        team.innerHTML = members.length
          ? members.map(function (row) {
              return "<div class='person'><strong>" + (row.username || "") + "</strong><em>" + (row.project_role_name || "") + "</em></div>";
            }).join("")
          : "<p>عضوی نیست</p>";
      }
      var tasks = [];
      try {
        tasks = await listAll("crud", "list_tasks", { project_id: id });
      } catch (ignored) {}
      setText("project-task-count", tasks.length);
      var goals = document.getElementById("project-goals");
      if (goals) {
        goals.innerHTML = tasks.length
          ? tasks.map(function (row) {
              return "<li><span>" + (row.title || "") + "</span></li>";
            }).join("")
          : "<li><span>وظیفه‌ای ثبت نشده.</span></li>";
      }
      try {
        var meetings = await listAll("meeting", "list_meetings");
        var related = meetings.filter(function (row) { return Number(row.project_id) === id; });
        setText("project-meeting-count", related.length);
      } catch (ignored) {
        setText("project-meeting-count", "—");
      }
      var meetLink = document.getElementById("project-new-meeting");
      if (meetLink) meetLink.href = "new-meeting.html?project_id=" + id;
      var reportLink = document.getElementById("project-reports");
      if (reportLink) reportLink.href = "reports.html";
      var reportsTab = document.querySelector('.tab[href="reports.html"]');
      if (reportsTab) reportsTab.href = "reports.html";
      try {
        var progress = await tool("stats", "get_project_progress", { project_id: id });
        var percent = progress.progress_percent != null ? progress.progress_percent : progress.percent;
        if (percent != null) setText("project-progress", percent + "٪");
      } catch (ignored) {
        setText("project-progress", "—");
      }
      var noteTask = document.getElementById("project-note-task");
      if (noteTask) {
        await fillSelect(noteTask, tasks, function (row) { return row.title; });
        if (!tasks.length) {
          noteTask.innerHTML = "<option value=''>اول یک وظیفه بسازید</option>";
        } else if (!noteTask.value) {
          noteTask.value = String(tasks[0].id);
        }
      }
      var noteForm = document.getElementById("project-note");
      if (noteForm && !noteForm.dataset.bound) {
        noteForm.dataset.bound = "1";
        noteForm.addEventListener("submit", async function (event) {
          event.preventDefault();
          var tid = Number((noteTask && noteTask.value) || 0);
          var body = document.getElementById("project-note-body");
          var text = ((body && body.value) || "").trim();
          if (!tid) {
            toast("برای ثبت، یک وظیفه انتخاب کنید");
            return;
          }
          if (!text) {
            toast("متن لازم است");
            return;
          }
          try {
            var user = await S.currentUser();
            if (!user) return;
            await saveCaptured(text, clipOf(body));
            keepClip(body, null);
            var chatId = await ensureProjectChat(id, project.name);
            var posted = await tool("crud", "create_message", {
              chat_id: chatId,
              task_id: tid,
              text: text,
              recipient_user_id: user.id,
            });
            await analyzeSaved("message", posted.id);
            if (body) body.value = "";
          } catch (error) {
            toast(error.message);
          }
        });
      }
      bindSpeechButton(document.getElementById("project-note-voice"), function (text, blob) {
        var area = document.getElementById("project-note-body");
        if (area) {
          area.value = (area.value ? area.value + "\n" : "") + text;
          keepClip(area, blob);
        }
        toast("متن صدا آماده است. با ثبت، صوت و متن ذخیره می‌شوند و استخراج نشان داده می‌شود");
      });
      var tasksTab = document.getElementById("tab-tasks");
      if (tasksTab) tasksTab.href = "tasks.html?project_id=" + id;
      var peopleTab = document.getElementById("tab-people");
      if (peopleTab) peopleTab.href = "members-groups.html?project_id=" + id;
      var chatsTab = document.getElementById("tab-chats");
      if (chatsTab) chatsTab.href = "chats.html?project_id=" + id;
      var progressTab = document.querySelector('.tab[href="progress.html"]');
      if (progressTab) progressTab.href = "progress.html?project_id=" + id;
      var seeAll = document.querySelector(".see-all");
      if (seeAll) seeAll.href = "members-groups.html?project_id=" + id;
    } catch (error) {
      toast(error.message);
    }
  }

  async function bootPeople() {
    var list = document.getElementById("people-list");
    var search = document.getElementById("people-search");
    var projectId = Number(param("project_id") || 0);
    var cache = [];
    var viewer = await S.currentUser();
    if (!viewer) return;
    var orgRoleId = 0;
    if (isDirector(viewer)) {
      try {
        var roleRows = await listAll("crud", "list_roles");
        roleRows.forEach(function (row) {
          if (row.name === "مدیر پروژه") orgRoleId = row.id;
        });
      } catch (ignored) {}
    }

    function render(query) {
      if (!list) return;
      var rows = cache.filter(function (row) {
        return matches(row, query);
      });
      if (!rows.length) {
        empty(list, "فردی پیدا نشد.");
        return;
      }
      list.innerHTML = "";
      rows.forEach(function (row) {
        var wrap = document.createElement("div");
        wrap.className = "mem";
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "mem-pick";
        btn.innerHTML =
          '<span class="mtext"><strong>' +
          displayName(row) +
          "</strong><em>" +
          (row.username || "") +
          (row.project_role_name ? " · " + row.project_role_name : "") +
          "</em></span>";
        btn.addEventListener("click", function () {
          showPerson(row);
        });
        wrap.appendChild(btn);
        var peer = personId(row);
        if (peer) {
          var chat = document.createElement("a");
          chat.className = "chat-chip";
          chat.href = chatHrefForPerson(row);
          chat.textContent = "گفتگو";
          wrap.appendChild(chat);
        }
        list.appendChild(wrap);
      });
      if (rows[0]) showPerson(rows[0]);
    }

    async function showPerson(row) {
      setText("person-detail-name", displayName(row));
      setText("person-detail-role", row.project_role_name || row.username || "کاربر");
      var chatLink = document.getElementById("person-chat-link");
      var userId = Number(row.user_id || row.id || 0);
      if (chatLink) {
        chatLink.hidden = !userId;
        chatLink.href = "chat.html?user_id=" + userId;
      }
      var promote = document.getElementById("person-promote");
      if (promote) promote.remove();
      var canPromote =
        isDirector(viewer) &&
        orgRoleId &&
        !projectId &&
        userId &&
        Object.prototype.hasOwnProperty.call(row, "roles") &&
        !isOrgManagerRole(row);
      if (canPromote && chatLink && chatLink.parentNode) {
        promote = document.createElement("button");
        promote.type = "button";
        promote.id = "person-promote";
        promote.className = "ghost-btn";
        promote.textContent = "تبدیل به مدیر سازمان";
        promote.addEventListener("click", async function () {
          try {
            await tool("crud", "create_user_role", { user_id: userId, role_id: orgRoleId });
            toast("مدیر سازمان شد");
            location.reload();
          } catch (error) {
            toast(error.message);
          }
        });
        chatLink.parentNode.appendChild(promote);
      }
      var activity = document.getElementById("person-activity");
      if (!activity) return;
      activity.innerHTML = "";
      var userId = Number(row.user_id || row.id || 0);
      try {
        var tasks = await listAll("crud", "list_tasks", projectId ? { project_id: projectId } : {});
        var mine = tasks.filter(function (task) {
          return Number(task.assigned_to_user_id) === userId;
        });
        if (!mine.length) {
          empty(activity, "وظیفه‌ای برای این فرد نیست.");
          return;
        }
        mine.forEach(function (task) {
          var item = document.createElement("p");
          item.className = "bubble";
          item.textContent = (task.title || "") + " · " + (task.status_name || "");
          activity.appendChild(item);
        });
      } catch (error) {
        empty(activity, error.message);
      }
    }

    try {
      if (projectId) {
        cache = await listAll("crud", "list_project_members", { project_id: projectId });
        cache = cache.map(function (row) {
          return Object.assign({}, row, { username: row.username, first_name: row.username });
        });
      } else if (canManage(viewer)) {
        cache = await loadAssignable();
      } else {
        cache = await loadChatPeople(viewer, 0);
      }
      render("");
    } catch (error) {
      if (list) empty(list, error.message);
    }
    if (search) {
      search.addEventListener("input", function () {
        render(search.value);
      });
    }
    var roleField = document.getElementById("person-role-field");
    if (roleField) roleField.hidden = true;
    var form = document.getElementById("person-form");
    if (form) form.hidden = !isDirector(viewer);
    if (form && isDirector(viewer)) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        try {
          var created = await tool("crud", "create_user", {
            first_name: document.getElementById("person-first").value.trim(),
            last_name: document.getElementById("person-last").value.trim(),
            username: document.getElementById("person-user").value.trim(),
            password: document.getElementById("person-pass").value,
            phone: document.getElementById("person-phone").value.trim() || undefined,
          });
          if (!orgRoleId) throw new Error("نقش مدیر پروژه در سامانه نیست");
          await tool("crud", "create_user_role", {
            user_id: created.id,
            role_id: orgRoleId,
          });
          toast("مدیر سازمان ساخته شد");
          location.reload();
        } catch (error) {
          toast(error.message);
        }
      });
    }
    var memberForm = document.getElementById("member-form");
    if (memberForm) memberForm.hidden = !canManage(viewer);
    if (memberForm && canManage(viewer)) {
      var projectField = document.getElementById("member-project-field");
      if (!projectId && projectField) {
        projectField.hidden = false;
        try {
          await fillSelect(
            document.getElementById("member-project"),
            await loadProjects(),
            function (row) { return row.name; }
          );
        } catch (error) {
          toast(error.message);
        }
      }
      try {
        await fillSelect(
          document.getElementById("member-user"),
          await loadAssignable(),
          displayName,
          function (row) { return row.user_id || row.id; }
        );
      } catch (error) {
        toast(error.message);
      }
      memberForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        try {
          var memberRole = (document.getElementById("member-role").value || "").trim();
          if (!memberRole) {
            toast("نقش در پروژه لازم است");
            return;
          }
          var targetProject = projectId || Number(document.getElementById("member-project").value || 0);
          if (!targetProject) {
            toast("پروژه را انتخاب کنید");
            return;
          }
          await tool("crud", "create_project_member", {
            project_id: targetProject,
            user_id: Number(document.getElementById("member-user").value),
            project_role: memberRole,
          });
          toast("دسترسی پروژه ثبت شد");
          location.reload();
        } catch (error) {
          toast(error.message);
        }
      });
    }
  }

  async function bootTasks() {
    var list = document.getElementById("task-list");
    var projectSelect = document.getElementById("task-project");
    var assigneeSelect = document.getElementById("task-assignee");
    var preset = Number(param("project_id") || 0);
    try {
      var projects = await loadProjects();
      await fillSelect(projectSelect, projects, function (row) { return row.name; });
      if (preset) projectSelect.value = String(preset);
    } catch (error) {
      toast(error.message);
    }

    async function refreshAssignees() {
      var pid = Number(projectSelect.value || 0);
      if (!pid || !assigneeSelect) return;
      try {
        var members = await listAll("crud", "list_project_members", { project_id: pid });
        await fillSelect(assigneeSelect, members, function (row) {
          return row.username + " · " + (row.project_role_name || "");
        }, function (row) {
          return row.user_id;
        });
      } catch (error) {
        toast(error.message);
      }
    }

    async function renderList() {
      if (!list) return;
      try {
        var pid = Number(projectSelect && projectSelect.value || 0);
        var records = await listAll("crud", "list_tasks", pid ? { project_id: pid } : {});
        if (!records.length) {
          empty(list, "وظیفه‌ای نیست.");
          return;
        }
        list.innerHTML = "";
        records.forEach(function (row) {
          list.appendChild(cardLink(
            "task-details.html?id=" + row.id,
            '<span class="tag">' +
              (row.status_name || "") +
              "</span><h2>" +
              (row.title || "") +
              "</h2><p>" +
              (row.description || row.project_name || "") +
              '</p><div class="meta"><div><span>اولویت </span>' +
              (row.priority_name || "") +
              "</div><div><span>مسئول </span>" +
              (row.assigned_to_username || "—") +
              "</div></div>"
          ));
        });
      } catch (error) {
        empty(list, error.message);
      }
    }

    if (projectSelect) {
      projectSelect.addEventListener("change", function () {
        refreshAssignees();
        renderList();
      });
    }
    await refreshAssignees();
    await renderList();

    var form = document.getElementById("task-form");
    if (form) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        var pid = Number(projectSelect.value || 0);
        if (!pid) {
          toast("اول پروژه را بسازید یا انتخاب کنید");
          return;
        }
        try {
          await tool("crud", "create_task", {
            project_id: pid,
            title: document.getElementById("task-title").value.trim(),
            description: document.getElementById("task-desc").value.trim() || undefined,
            status: document.getElementById("task-status").value,
            priority: document.getElementById("task-priority").value,
            importance: document.getElementById("task-importance").value,
            assigned_to_user_id: Number(assigneeSelect.value || 0) || undefined,
            start_date: (document.getElementById("task-start") && document.getElementById("task-start").value) || undefined,
            due_date: document.getElementById("task-due").value || undefined,
          });
          toast("وظیفه ثبت شد");
          form.reset();
          if (preset) projectSelect.value = String(preset);
          await renderList();
        } catch (error) {
          toast(error.message);
        }
      });
    }
  }

  async function addChatMemberQuiet(chatId, userId) {
    if (!chatId || !userId) return;
    try {
      await tool("crud", "create_chat_member", { chat_id: chatId, user_id: userId });
    } catch (ignored) {}
  }

  async function ensureProjectChat(projectId, projectName) {
    var chats = await listAll("crud", "list_chats", { project_id: projectId });
    var chatId;
    if (chats.length) {
      chatId = chats[0].id;
    } else {
      var created = await tool("crud", "create_chat", {
        title: (projectName || "پروژه") + " · گفتگو",
        chat_type: "گفتگوی پروژه",
        project_id: projectId,
      });
      chatId = created.id;
    }
    try {
      var members = await listAll("crud", "list_project_members", { project_id: projectId });
      for (var i = 0; i < members.length; i += 1) {
        await addChatMemberQuiet(chatId, members[i].user_id);
      }
    } catch (ignored) {}
    return chatId;
  }

  async function findOrCreatePrivateChat(peerId, me, title) {
    var chats = await listAll("crud", "list_chats");
    for (var i = 0; i < chats.length; i += 1) {
      var row = chats[i];
      if (row.project_id || row.chat_type_name !== "گفتگوی خصوصی") continue;
      var members = await listAll("crud", "list_chat_members", { chat_id: row.id });
      var ids = members.map(function (member) { return Number(member.user_id); });
      if (ids.indexOf(Number(peerId)) !== -1 && ids.indexOf(Number(me.id)) !== -1) {
        return row.id;
      }
    }
    var created = await tool("crud", "create_chat", {
      title: title || "گفتگوی خصوصی",
      chat_type: "گفتگوی خصوصی",
    });
    try {
      await tool("crud", "create_chat_member", { chat_id: created.id, user_id: peerId });
    } catch (error) {
      var msg = (error && error.message) || "";
      if (msg.indexOf("از قبل عضو") === -1) throw error;
    }
    return created.id;
  }

  async function postChatMessage(chatId, text, taskId, members, myId) {
    var others = (members || []).filter(function (member) {
      return Number(member.user_id) !== Number(myId);
    });
    var first = others[0] || (members && members[0]);
    if (!first) throw new Error("گیرنده‌ای در گفتگو نیست");
    var args = { chat_id: chatId, text: text, recipient_user_id: first.user_id };
    if (taskId) args.task_id = Number(taskId);
    var posted = await tool("crud", "create_message", args);
    for (var i = 1; i < others.length; i += 1) {
      try {
        await tool("crud", "create_message_recipient", {
          message_id: posted.id,
          user_id: others[i].user_id,
        });
      } catch (ignored) {}
    }
    return posted;
  }

  async function bootChats() {
    var list = document.getElementById("people-chat-list");
    var search = document.getElementById("people-search");
    var user = await S.currentUser();
    if (!user) return;
    var projectId = Number(param("project_id") || 0);
    var cache = [];
    function paint(query) {
      var rows = cache.filter(function (row) {
        return matches(row, query);
      });
      renderPersonRows(list, rows, user);
    }
    try {
      cache = await loadChatPeople(user, projectId);
      paint("");
    } catch (error) {
      if (list) empty(list, error.message);
    }
    if (search) {
      search.addEventListener("input", function () {
        paint(search.value);
      });
    }
  }

  async function bootChat() {
    var user = await S.currentUser();
    if (!user) return;
    var chatId = Number(param("id") || 0);
    var peerId = Number(param("user_id") || 0);
    var taskId = Number(param("task_id") || 0);
    var projectId = Number(param("project_id") || 0);
    try {
      if (!chatId && peerId) {
        chatId = await findOrCreatePrivateChat(peerId, user);
        history.replaceState({}, "", "chat.html?id=" + chatId);
      }
      if (!chatId && projectId) {
        location.replace("chats.html?project_id=" + projectId);
        return;
      }
      if (!chatId) {
        toast("گفتگو پیدا نشد");
        return;
      }
      var chat = await tool("crud", "get_chat", { id: chatId });
      setText("chat-title", chat.title);
      var members = await listAll("crud", "list_chat_members", { chat_id: chatId });
      setText("chat-meta", members.map(function (row) { return row.username; }).join(" · ") || "—");
      var taskField = document.getElementById("chat-task-field");
      var taskSelect = document.getElementById("chat-task");
      if (chat.project_id && taskField && taskSelect) {
        taskField.hidden = false;
        var tasks = await listAll("crud", "list_tasks", { project_id: chat.project_id });
        await fillSelect(taskSelect, tasks, function (row) { return row.title; });
        if (taskId) taskSelect.value = String(taskId);
      }
      async function renderThread() {
        var thread = document.getElementById("chat-thread");
        if (!thread) return;
        var messages = await listAll("crud", "list_messages", { chat_id: chatId });
        messages = messages.slice().reverse();
        if (taskId) {
          messages = messages.filter(function (row) {
            return Number(row.task_id) === taskId;
          });
        }
        if (!messages.length) {
          empty(thread, "هنوز پیامی نیست.");
          return;
        }
        thread.innerHTML = "";
        messages.forEach(function (row) {
          var bubble = document.createElement("div");
          bubble.className = "bubble-msg " + (Number(row.sender_user_id) === Number(user.id) ? "out" : "in");
          bubble.innerHTML =
            "<div>" +
            (row.text || "") +
            "</div><small>" +
            (row.sender_username || "") +
            (row.task_title ? " · " + row.task_title : "") +
            " · " +
            faStamp(row.created_at) +
            "</small>";
          thread.appendChild(bubble);
        });
      }
      await renderThread();
      var form = document.getElementById("chat-form");
      if (form && !form.dataset.bound) {
        form.dataset.bound = "1";
        form.addEventListener("submit", async function (event) {
          event.preventDefault();
          var body = document.getElementById("chat-body");
          var text = ((body && body.value) || "").trim();
          if (!text) return;
          try {
            var chosenTask = taskSelect && taskSelect.value ? Number(taskSelect.value) : taskId;
            if (chat.project_id && !chosenTask) {
              toast("برای گفتگوی پروژه یک وظیفه انتخاب کنید");
              return;
            }
            await postChatMessage(
              chatId,
              text,
              chat.project_id ? chosenTask : 0,
              members,
              user.id
            );
            if (body) body.value = "";
            members = await listAll("crud", "list_chat_members", { chat_id: chatId });
            await renderThread();
          } catch (error) {
            toast(error.message);
          }
        });
      }
    } catch (error) {
      toast(error.message);
    }
  }

  function taskElapsed(task) {
    return daysBetween(task.start_date || task.created_at, todayStamp());
  }

  function taskRemaining(task) {
    if (!task.due_date) return null;
    return daysBetween(todayStamp(), task.due_date);
  }

  async function bootTaskDetails() {
    var id = Number(param("id"));
    var user = await S.currentUser();
    if (!id || !user) return;
    try {
      var task = await tool("crud", "get_task", { id: id });
      setText("task-title", task.title);
      setText("task-desc", task.description || task.project_name || "");
      setText("task-status-pill", task.status_name);
      var statusSelect = document.getElementById("task-status");
      if (statusSelect && task.status_name) statusSelect.value = task.status_name;
      setText("task-elapsed", formatDays(taskElapsed(task)));
      setText("task-remaining", formatDays(taskRemaining(task)));
      var itemsPayload = { records: [] };
      try {
        itemsPayload = await tool("crud", "list_task_items", { task_id: id });
      } catch (ignored) {}
      var items = itemsPayload.records || [];
      var done = items.filter(function (row) { return row.is_completed; }).length;
      var percent = items.length ? Math.round((done / items.length) * 100) : (task.status_name === "تکمیل شده" ? 100 : 0);
      setText("task-progress", faDigits(percent) + "٪");
      var list = document.getElementById("item-list");
      if (list) {
        if (!items.length) {
          empty(list, "زیرکاری ثبت نشده.");
        } else {
          list.innerHTML = "";
          items.forEach(function (row) {
            var article = document.createElement("article");
            article.className = "meet item-row" + (row.is_completed ? " done" : "");
            article.innerHTML =
              '<input type="checkbox" ' +
              (row.is_completed ? "checked" : "") +
              ' data-id="' +
              row.id +
              '"><div><h2>' +
              (row.title || "") +
              "</h2><p>" +
              (row.description || "") +
              "</p><div class='meta'><span>مهلت </span>" +
              faStamp(row.end_date) +
              "</div></div>";
            var box = article.querySelector("input");
            box.addEventListener("change", async function () {
              try {
                await tool("crud", "complete_task_item", {
                  id: row.id,
                  is_completed: box.checked,
                });
                location.reload();
              } catch (error) {
                box.checked = !box.checked;
                toast(error.message);
              }
            });
            list.appendChild(article);
          });
        }
      }
      var peopleBox = document.getElementById("task-people");
      if (peopleBox) {
        try {
          var mates = await listAll("crud", "list_project_members", { project_id: task.project_id });
          renderPersonRows(peopleBox, mates, user);
        } catch (error) {
          empty(peopleBox, error.message);
        }
      }
      var statusForm = document.getElementById("task-status-form");
      if (statusForm && !statusForm.dataset.bound) {
        statusForm.dataset.bound = "1";
        statusForm.addEventListener("submit", async function (event) {
          event.preventDefault();
          try {
            await tool("crud", "update_task", {
              id: id,
              status: document.getElementById("task-status").value,
            });
            toast("وضعیت ذخیره شد");
            location.reload();
          } catch (error) {
            toast(error.message);
          }
        });
      }
      var itemForm = document.getElementById("item-form");
      if (itemForm && !itemForm.dataset.bound) {
        itemForm.dataset.bound = "1";
        itemForm.addEventListener("submit", async function (event) {
          event.preventDefault();
          try {
            await tool("crud", "create_task_item", {
              task_id: id,
              title: document.getElementById("item-title").value.trim(),
              start_date: document.getElementById("item-start").value || undefined,
              end_date: document.getElementById("item-end").value || undefined,
            });
            toast("زیرکار ثبت شد");
            location.reload();
          } catch (error) {
            toast(error.message);
          }
        });
      }
    } catch (error) {
      toast(error.message);
    }
  }

  async function bootProgress() {
    var user = await S.currentUser();
    if (!user) return;
    var projectId = Number(param("project_id") || 0);
    var list = document.getElementById("mine-list");
    try {
      var tasks = await listAll("crud", "list_tasks", projectId ? { project_id: projectId } : {});
      var mine = tasks.filter(function (row) {
        return Number(row.assigned_to_user_id) === Number(user.id);
      });
      var done = mine.filter(function (row) { return row.status_name === "تکمیل شده"; }).length;
      var open = mine.length - done;
      var percent = mine.length ? Math.round((done / mine.length) * 100) : 0;
      setText("mine-percent", faDigits(percent) + "٪");
      setText("mine-done", faDigits(done));
      setText("mine-open", faDigits(open));
      var elapsedParts = mine.map(taskElapsed).filter(function (value) { return value != null; });
      var remainingParts = mine.map(taskRemaining).filter(function (value) { return value != null; });
      var elapsedAvg = elapsedParts.length
        ? Math.round(elapsedParts.reduce(function (sum, value) { return sum + value; }, 0) / elapsedParts.length)
        : null;
      var remainingMin = remainingParts.length ? Math.min.apply(null, remainingParts) : null;
      setText("mine-elapsed", formatDays(elapsedAvg));
      setText("mine-remaining", formatDays(remainingMin));
      if (!list) return;
      if (!mine.length) {
        empty(list, "وظیفه‌ای به نام شما نیست.");
        return;
      }
      list.innerHTML = "";
      mine.forEach(function (row) {
        list.appendChild(cardLink(
          "task-details.html?id=" + row.id,
          '<span class="tag">' +
            (row.status_name || "") +
            "</span><h2>" +
            (row.title || "") +
            "</h2><p>" +
            (row.project_name || "") +
            '</p><div class="meta"><div><span>رفته </span>' +
            formatDays(taskElapsed(row)) +
            "</div><div><span>باقی </span>" +
            formatDays(taskRemaining(row)) +
            "</div></div>"
        ));
      });
    } catch (error) {
      if (list) empty(list, error.message);
    }
  }

  async function bootReports() {
    var list = document.getElementById("search-list");
    var input = document.getElementById("search-query");
    var projectSelect = document.getElementById("report-project");
    var taskSelect = document.getElementById("report-task");
    var user = await S.currentUser();
    if (!user) return;
    if (param("q") && input) input.value = param("q");
    var projects = [];
    try {
      projects = await loadProjects();
      await fillSelect(projectSelect, projects, function (row) { return row.name; });
    } catch (error) {
      toast(error.message);
    }

    async function refreshTasks() {
      var pid = Number(projectSelect && projectSelect.value || 0);
      if (!pid) {
        await fillSelect(taskSelect, [], function (row) { return row.title; });
        return;
      }
      var tasks = await listAll("crud", "list_tasks", { project_id: pid });
      await fillSelect(taskSelect, tasks, function (row) { return row.title; });
    }

    if (projectSelect) {
      projectSelect.addEventListener("change", function () {
        refreshTasks().catch(function (error) { toast(error.message); });
      });
    }
    await refreshTasks();

    async function runSearch() {
      var q = (input && input.value || "").trim();
      if (!list) return;
      try {
        var meetings = await listAll("meeting", "list_meetings");
        var messages = await listAll("crud", "list_messages");
        var hits = meetings
          .filter(function (row) { return matches(row, q); })
          .map(function (row) {
            return { kind: "جلسه", title: row.title, body: row.location || row.status_name, href: "meeting-details.html?id=" + row.id, at: row.scheduled_at };
          })
          .concat(
            messages
              .filter(function (row) { return matches(row, q); })
              .map(function (row) {
                return {
                  kind: "پیام",
                  title: row.task_title || row.chat_title,
                  body: row.text,
                  href: "reports.html",
                  at: row.created_at,
                };
              })
          );
        if (!hits.length) {
          empty(list, q ? "نتیجه‌ای پیدا نشد." : "جلسه‌ای یا پیامی نیست.");
          return;
        }
        list.innerHTML = "";
        hits.forEach(function (hit) {
          list.appendChild(
            cardLink(
              hit.href,
              '<span class="tag wait">' +
                hit.kind +
                "</span><h2>" +
                (hit.title || "") +
                "</h2><p>" +
                String(hit.body || "").slice(0, 220) +
                '</p><div class="meta"><div><span>تاریخ </span>' +
                faStamp(hit.at) +
                "</div></div>"
            )
          );
        });
      } catch (error) {
        empty(list, error.message);
      }
    }

    if (input) {
      input.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          runSearch();
        }
      });
    }
    var searchBtn = document.getElementById("search-go");
    if (searchBtn) searchBtn.addEventListener("click", runSearch);
    await runSearch();

    var form = document.getElementById("report-form");
    if (form) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        var pid = Number(projectSelect.value || 0);
        var tid = Number(taskSelect && taskSelect.value || 0);
        var text = document.getElementById("report-body").value.trim();
        if (!pid) {
          toast("پروژه لازم است");
          return;
        }
        if (!tid) {
          toast("وظیفه لازم است");
          return;
        }
        if (!text) {
          toast("متن لازم است");
          return;
        }
        try {
          var project = projects.find(function (row) { return Number(row.id) === pid; }) || {};
          var chatId = await ensureProjectChat(pid, project.name);
          var posted = await tool("crud", "create_message", {
            chat_id: chatId,
            task_id: tid,
            text: text,
            recipient_user_id: user.id,
          });
          toast("پیام خام ذخیره شد");
          await analyzeSaved("message", posted.id);
          form.reset();
          if (projectSelect) projectSelect.value = String(pid);
          await refreshTasks();
          await runSearch();
        } catch (error) {
          toast(error.message);
        }
      });
    }
    var reportVoice = document.getElementById("report-voice");
    bindSpeechButton(reportVoice, function (text) {
      var area = document.getElementById("report-body");
      if (area) area.value = (area.value ? area.value + "\n" : "") + text;
      toast("مرحله ۳: متن آماده ثبت است");
    });
    if (param("mode") === "voice" && reportVoice) {
      reportVoice.scrollIntoView({ block: "center" });
    }

    var semanticInput = document.getElementById("semantic-query");
    var semanticList = document.getElementById("semantic-list");
    var semanticBtn = document.getElementById("semantic-go");
    async function runSemantic() {
      var q = (semanticInput && semanticInput.value || "").trim();
      if (!semanticList) return;
      if (!q) {
        empty(semanticList, "برای جستجوی معنایی یک عبارت بنویسید.");
        return;
      }
      if (semanticBtn) semanticBtn.disabled = true;
      try {
        var similar = await tool("embedding", "search_similar", { query: q, limit: 8 });
        paintSemantic(semanticList, similar.records || []);
      } catch (error) {
        empty(semanticList, error.message);
      } finally {
        if (semanticBtn) semanticBtn.disabled = false;
      }
    }
    if (semanticBtn) semanticBtn.addEventListener("click", runSemantic);
    if (semanticInput) {
      semanticInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          runSemantic();
        }
      });
    }
    var embedBtn = document.getElementById("embed-pending");
    var embedStatus = document.getElementById("embed-status");
    if (embedBtn) {
      embedBtn.addEventListener("click", async function () {
        embedBtn.disabled = true;
        if (embedStatus) embedStatus.textContent = "در حال امبد کردن…";
        try {
          var stored = await tool("embedding", "index_pending_analyses", { limit: 5 });
          var count = Number(stored.indexed_count || 0);
          var text = count ? faDigits(count) + " تحلیل امبد شد." : "تحلیل بدون بردار نمانده است.";
          if (embedStatus) embedStatus.textContent = text;
          toast(text);
        } catch (error) {
          if (embedStatus) embedStatus.textContent = error.message;
          toast(error.message);
        } finally {
          embedBtn.disabled = false;
        }
      });
    }
  }

  var KIND_FA = { raw: "متن خام", entity: "موجودیت", intent: "نیت", intent_slot: "جزء نیت" };
  var SOURCE_FA = { meeting: "جلسه", message: "پیام", content: "محتوا" };

  function sourceHref(row) {
    if (!row || !row.source_id) return "";
    if (row.source_type === "meeting") return "meeting-details.html?id=" + row.source_id;
    if (row.source_type === "message") return "chats.html";
    return "";
  }

  function semanticCardHtml(row) {
    var hits = (row.hits || []).slice(0, 3);
    var body = hits.map(function (hit) {
      var kind = KIND_FA[hit.kind] || hit.kind || "";
      return "<li><span>" + escapeHtml(kind) + "</span> " + escapeHtml(String(hit.text || "").slice(0, 180)) + "</li>";
    }).join("");
    var score = row.score != null ? Math.round(Number(row.score) * 100) : null;
    return (
      '<span class="tag wait">' +
      escapeHtml(SOURCE_FA[row.source_type] || row.source_type || "مشابه") +
      "</span><h2>شباهت " +
      (score != null ? faDigits(score) + "٪" : "—") +
      "</h2>" +
      (body ? "<ul class='semantic-hits'>" + body + "</ul>" : "")
    );
  }

  function paintSemantic(list, records) {
    if (!records.length) {
      empty(list, "مورد مشابهی در بردارها پیدا نشد.");
      return;
    }
    list.innerHTML = "";
    records.forEach(function (row) {
      var html = semanticCardHtml(row);
      var href = sourceHref(row);
      if (href) {
        list.appendChild(cardLink(href, html));
        return;
      }
      var article = document.createElement("article");
      article.className = "meet";
      article.innerHTML = html;
      list.appendChild(article);
    });
  }

  function semanticPanelHtml(records) {
    return (
      "<h2>موارد مشابه</h2><ul class='semantic-hits'>" +
      records.map(function (row) {
        var score = row.score != null ? Math.round(Number(row.score) * 100) : null;
        var lead = (row.hits && row.hits[0] && row.hits[0].text) || "";
        var href = sourceHref(row);
        var title = escapeHtml(SOURCE_FA[row.source_type] || "منبع") + (score != null ? " · " + faDigits(score) + "٪" : "");
        var line = "<li><span>" + title + "</span> " + escapeHtml(String(lead).slice(0, 180));
        if (href) line += " <a href='" + href + "'>باز کردن</a>";
        return line + "</li>";
      }).join("") +
      "</ul>"
    );
  }

  async function bootNotifications() {
    var list = document.getElementById("notice-list");
    var sentList = document.getElementById("notice-sent");
    var sentWrap = document.getElementById("notice-sent-wrap");
    var form = document.getElementById("notice-form");
    var typeSelect = document.getElementById("notice-type");
    var frequencySelect = document.getElementById("notice-frequency");
    var user = await S.currentUser();
    var canSend = canSendReminder(user);
    if (form) form.hidden = !canSend;
    if (sentWrap) sentWrap.hidden = !canSend;

    function syncFrequency() {
      if (!typeSelect || !frequencySelect) return;
      if (typeSelect.value === "یک‌باره") {
        frequencySelect.value = "یک‌باره";
        return;
      }
      if (frequencySelect.value === "یک‌باره") frequencySelect.value = "هفتگی";
    }

    if (typeSelect) {
      typeSelect.addEventListener("change", syncFrequency);
      syncFrequency();
    }

    async function renderInbox() {
      try {
        var records = await listAll("crud", "list_notifications");
        if (!records.length) {
          empty(list, "اعلانی برای این حساب نیست.");
          return;
        }
        list.innerHTML = "";
        records.forEach(function (row) {
          var item = document.createElement("button");
          item.type = "button";
          item.className = "meet";
          item.style.width = "calc(100% - 32px)";
          item.style.textAlign = "right";
          item.innerHTML =
            '<span class="tag' +
            (row.is_read ? " wait" : "") +
            '">' +
            (row.notification_type_name || "") +
            "</span><h2>" +
            (row.title || "") +
            "</h2><p>" +
            (row.message || "") +
            "</p>";
          item.addEventListener("click", async function () {
            try {
              if (!row.is_read) await tool("crud", "mark_notification_read", { id: row.id });
              await renderInbox();
              await fillBadge();
            } catch (error) {
              toast(error.message);
            }
          });
          list.appendChild(item);
        });
      } catch (error) {
        empty(list, error.message);
      }
    }

    async function renderSent() {
      if (!canSend || !sentList) return;
      try {
        var records = await listAll("reminder", "list_reminders");
        records = records.filter(function (row) {
          return Number(row.created_by_user_id) === Number(user.id);
        });
        if (!records.length) {
          empty(sentList, "هنوز یادآوری نفرستاده‌اید.");
          return;
        }
        sentList.innerHTML = "";
        records.forEach(function (row) {
          var article = document.createElement("article");
          article.className = "meet";
          article.innerHTML =
            '<span class="tag wait">' +
            (row.reminder_type_name || "") +
            " · " +
            (row.frequency_name || "") +
            "</span><h2>" +
            (row.title || "") +
            "</h2><p>" +
            (row.message_template || "") +
            "</p>";
          sentList.appendChild(article);
        });
      } catch (error) {
        empty(sentList, error.message);
      }
    }

    await renderInbox();
    await renderSent();
    if (canSend) {
      var noticeProject = document.getElementById("notice-project");
      var noticeUser = document.getElementById("notice-user");
      async function fillRecipients() {
        var pid = Number((noticeProject && noticeProject.value) || 0);
        var recipients;
        if (pid) {
          recipients = await listAll("crud", "list_project_members", { project_id: pid });
        } else if (isDirector(user)) {
          recipients = await loadUsers();
        } else {
          recipients = await loadChatPeople(user, 0);
        }
        await fillSelect(
          noticeUser,
          recipients,
          userOptionLabel,
          function (row) { return row.user_id || row.id; }
        );
      }
      try {
        await fillSelect(noticeProject, await loadProjects(), function (row) { return row.name; });
      } catch (ignored) {}
      if (noticeProject) noticeProject.addEventListener("change", function () {
        fillRecipients().catch(function (error) { toast(error.message); });
      });
      try {
        await fillRecipients();
      } catch (error) {
        toast(error.message);
      }
    }
    if (form && canSend) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        var userId = Number(document.getElementById("notice-user").value || 0);
        if (!userId) {
          toast("گیرنده را انتخاب کنید");
          return;
        }
        syncFrequency();
        var recipientLabel = (document.getElementById("notice-user").selectedOptions[0] || {}).textContent || "گیرنده";
        try {
          var created = await tool("reminder", "create_reminder", {
            title: document.getElementById("notice-title").value.trim(),
            message_template: document.getElementById("notice-body").value.trim(),
            scheduled_at: nowIso(),
            reminder_type: typeSelect.value,
            frequency: frequencySelect.value,
            status: "فعال",
            target_user_id: userId,
            project_id: Number(document.getElementById("notice-project").value || 0) || undefined,
          });
          await tool("reminder", "send_reminder", { reminder_id: created.id });
          toast("برای «" + recipientLabel + "» در صندوق اعلان‌های همان حساب ثبت شد");
          form.reset();
          syncFrequency();
          await renderInbox();
          await renderSent();
          await fillBadge();
        } catch (error) {
          toast(error.message);
        }
      });
    }
  }

  async function boot() {
    bindBells();
    fillBadge();
    var page = pageName();
    try {
      if (page === "home") await bootHome();
      if (page === "meetings") await bootMeetings();
      if (page === "new-meeting") await bootNewMeeting();
      if (page === "meeting-details") await bootMeetingDetails();
      if (page === "projects") await bootProjects();
      if (page === "new-project") await bootNewProject();
      if (page === "project-details") await bootProjectDetails();
      if (page === "people") await bootPeople();
      if (page === "tasks") await bootTasks();
      if (page === "task-details") await bootTaskDetails();
      if (page === "chats") await bootChats();
      if (page === "chat") await bootChat();
      if (page === "progress") await bootProgress();
      if (page === "reports") await bootReports();
      if (page === "notifications") await bootNotifications();
    } catch (error) {
      toast(error.message || "خطای پیش‌بینی‌نشده");
    }
  }

  global.MobileApp = { boot: boot, toast: toast };
  document.addEventListener("DOMContentLoaded", boot);
})(window);
