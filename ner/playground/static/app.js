const TYPE_COLORS = {
  PERSON: "#5a9bd4",
  UNIT: "#5bb8a9",
  ORG: "#9b7ed9",
  PLACE: "#d4a15a",
  OBJECT: "#8a8a8a",
  PROJECT: "#6aae7a",
  TASK: "#c9a227",
  TIME: "#d46a9b",
  ROLE: "#7eb0d4",
  KEYWORD: "#c4c4c4",
};

const PANES = [
  "mentions",
  "keywords",
  "topics",
  "stance",
  "discourse",
  "intent",
  "rhetoric",
  "entities",
  "catalog",
  "trace",
  "json",
];

const GROUP_ORDER = [
  { id: "entity", name: "موجودیت" },
  { id: "discourse", name: "ژانر" },
  { id: "intent", name: "نیت" },
  { id: "rhetoric", name: "بیان" },
  { id: "joint", name: "ترکیبی" },
];

function $(id) {
  return document.getElementById(id);
}

function showPane(name) {
  PANES.forEach((pane) => {
    const node = $(`pane-${pane}`);
    if (node) node.classList.toggle("hidden", pane !== name);
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.pane === name);
  });
}

function renderLegend(types) {
  const root = $("legend");
  root.innerHTML = "";
  types.forEach((type) => {
    const item = document.createElement("span");
    item.className = "swatch";
    item.innerHTML = `<i style="background:${TYPE_COLORS[type] || "#666"}"></i>${type}`;
    root.appendChild(item);
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function rangesOverlap(left, right) {
  return left.start_offset < right.end_offset && right.start_offset < left.end_offset;
}

function highlightText(text, mentions, keywords) {
  const keywordSpans = (keywords || [])
    .filter((item) => !mentions.some((mention) => rangesOverlap(mention, item)))
    .map((item) => ({
      start_offset: item.start_offset,
      end_offset: item.end_offset,
      type: "KEYWORD",
      canonical_name: item.phrase,
    }));
  const sorted = [...mentions, ...keywordSpans].sort((a, b) => {
    if (a.start_offset !== b.start_offset) return a.start_offset - b.start_offset;
    return b.end_offset - a.end_offset;
  });
  let cursor = 0;
  let html = "";
  sorted.forEach((item) => {
    const start = Math.max(item.start_offset, cursor);
    const end = item.end_offset;
    if (end <= cursor || start >= text.length) return;
    html += escapeHtml(text.slice(cursor, start));
    const color = TYPE_COLORS[item.type] || "#666";
    const label = escapeHtml(item.type);
    const name = escapeHtml(item.canonical_name);
    html += `<mark style="background:${color}33; border-bottom: 2px solid ${color}" title="${label}: ${name}">${escapeHtml(
      text.slice(start, end),
    )}</mark>`;
    cursor = end;
  });
  html += escapeHtml(text.slice(cursor));
  return html;
}

function formatSlots(slots) {
  if (!slots || typeof slots !== "object") return "—";
  const parts = Object.entries(slots)
    .filter(([key, value]) => key && value)
    .map(([key, value]) => `${key}: ${value}`);
  return parts.length ? parts.join("؛ ") : "—";
}

function formatSlotList(slots) {
  if (!slots || typeof slots !== "object") return "";
  return Object.entries(slots)
    .filter(([key, value]) => key && value)
    .map(([key, value]) => `<li><strong>${escapeHtml(key)}:</strong> ${escapeHtml(value)}</li>`)
    .join("");
}

function formatMs(ms) {
  if (ms == null || ms === "") return "—";
  const value = Number(ms);
  if (!Number.isFinite(value)) return "—";
  if (value < 1000) return `${Math.round(value)}ms`;
  return `${(value / 1000).toFixed(1)}s`;
}

const TOOL_LABELS = {
  extract_entities: "موجودیت",
  extract_keywords: "کلمهٔ کلیدی",
  extract_topics: "موضوع",
  extract_sentiment: "احساس",
  extract_discourse: "ژانر",
  extract_intent: "نیت",
  extract_rhetoric: "بیان",
};

function tracesOf(payload) {
  if (!payload) return [];
  if (Array.isArray(payload.traces)) return payload.traces.filter(Boolean);
  if (payload.trace) return [payload.trace];
  return [];
}

function traceSummary(traces) {
  if (!traces.length) return "";
  return traces
    .map((item) => `${TOOL_LABELS[item.name] || item.name} ${formatMs(item.duration_ms)}`)
    .join(" · ");
}

function renderTable(rows, headers, root) {
  root.innerHTML = "";
  if (!rows.length) {
    root.innerHTML = '<p class="muted">موردی نیست.</p>';
    return;
  }
  const table = document.createElement("table");
  table.className = "data";
  table.innerHTML = `<thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>`;
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((cell) => {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  root.appendChild(table);
}

function primaryHit(hits) {
  const list = hits || [];
  return list.find((item) => item.is_primary) || list[0] || null;
}

function expectedValue(id) {
  const node = $(id);
  return node && node.value ? node.value.trim() : "";
}

function scoreFromHits(hits, expected) {
  const primary = primaryHit(hits);
  const got = primary && primary.code ? primary.code : null;
  const expectedCode = expected || null;
  return {
    name: primary && primary.name,
    got,
    expected: expectedCode,
    ok: expectedCode ? got === expectedCode : null,
    mention_text: (primary && primary.mention_text) || "",
    slots: (primary && primary.slots) || {},
    hits: hits || [],
    confidence: primary && primary.confidence,
  };
}

function attachSpeechScore(payload) {
  if (payload.speech_score) return payload;
  return {
    ...payload,
    speech_score: {
      discourse: scoreFromHits(payload.discourses, expectedValue("expected-discourse")),
      intent: scoreFromHits(payload.intents, expectedValue("expected-intent")),
      rhetoric: scoreFromHits(payload.rhetorics, expectedValue("expected-rhetoric")),
      intended_meaning: payload.intended_meaning || "",
    },
  };
}

function extrasHtml(hits) {
  const rest = (hits || []).filter((item) => !item.is_primary);
  if (!rest.length) return "";
  return `<p class="muted">فرعی: ${rest.map((item) => escapeHtml(item.name || item.code)).join("، ")}</p>`;
}

function scoreBadge(ok) {
  if (ok === true) return '<span class="badge-ok">خواند</span>';
  if (ok === false) return '<span class="badge-fail">نخواند</span>';
  return "";
}

function renderSpeechCard(title, layer) {
  if (!layer) return "";
  if (layer.error) {
    return `
      <article class="speech-card fail">
        <h3>${title}</h3>
        <p class="error">${escapeHtml(layer.error)}</p>
      </article>
    `;
  }
  if (!layer.name && !layer.got) {
    return `
      <article class="speech-card">
        <h3>${title}</h3>
        <p class="muted">چیزی پیدا نشد.</p>
        ${layer.expected ? `<p class="muted">انتظار: ${escapeHtml(layer.expected)}</p>` : ""}
      </article>
    `;
  }
  const tone = layer.ok === true ? "ok" : layer.ok === false ? "fail" : "";
  const slots = formatSlotList(layer.slots);
  return `
    <article class="speech-card ${tone}">
      <h3>${title} ${scoreBadge(layer.ok)}</h3>
      <p class="speech-main">${escapeHtml(layer.name || layer.got)}</p>
      ${layer.mention_text ? `<p>شاهد: ${escapeHtml(layer.mention_text)}</p>` : ""}
      ${layer.expected ? `<p class="muted">انتظار: ${escapeHtml(layer.expected)}</p>` : ""}
      ${slots ? `<ul class="slot-list">${slots}</ul>` : ""}
      ${extrasHtml(layer.hits)}
    </article>
  `;
}

function renderSpeechSummary(payload) {
  const box = $("speech-summary");
  const score = payload.speech_score;
  const hasHits =
    (payload.discourses || []).length ||
    (payload.intents || []).length ||
    (payload.rhetorics || []).length ||
    payload.intended_meaning;
  if (!score && !hasHits) {
    box.classList.add("hidden");
    box.innerHTML = "";
    return;
  }
  box.classList.remove("hidden");
  const discourse = (score && score.discourse) || scoreFromHits(payload.discourses, expectedValue("expected-discourse"));
  const intent = (score && score.intent) || scoreFromHits(payload.intents, expectedValue("expected-intent"));
  const rhetoric = (score && score.rhetoric) || scoreFromHits(payload.rhetorics, expectedValue("expected-rhetoric"));
  const meaning = payload.intended_meaning || (score && score.intended_meaning) || "";
  box.innerHTML = `
    ${renderSpeechCard("ژانر", discourse)}
    ${renderSpeechCard("نیت", intent)}
    ${renderSpeechCard("بیان", rhetoric)}
    ${meaning ? `<p class="muted" style="grid-column:1/-1">معنای مقصود: ${escapeHtml(meaning)}</p>` : ""}
  `;
}

function renderChips(payload) {
  const root = $("chips");
  root.innerHTML = "";
  const topics = payload.topics || [];
  const keywords = payload.keywords || [];
  const sentiment = payload.sentiment;
  const emotions = payload.emotions || [];
  const discourses = payload.discourses || [];
  const intents = payload.intents || [];
  const rhetorics = payload.rhetorics || [];
  if (
    !topics.length &&
    !keywords.length &&
    !sentiment &&
    !emotions.length &&
    !discourses.length &&
    !intents.length &&
    !rhetorics.length &&
    !payload.intended_meaning
  ) {
    root.classList.add("hidden");
    return;
  }
  root.classList.remove("hidden");
  if (sentiment) {
    const chip = document.createElement("span");
    chip.className = `chip stance ${sentiment.polarity}`;
    chip.textContent = `${sentiment.polarity_name} · ${sentiment.intensity_name}`;
    chip.title = "احساس کل متن";
    root.appendChild(chip);
  }
  emotions.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip emotion";
    chip.textContent = item.name;
    chip.title = "هیجان";
    root.appendChild(chip);
  });
  discourses.forEach((item) => {
    const chip = document.createElement("span");
    const discovered = item.discovered ? " discovered" : "";
    chip.className = item.is_primary ? `chip discourse primary${discovered}` : `chip discourse${discovered}`;
    let label = item.name;
    if (item.is_primary) label += " · اصلی";
    if (item.discovered) label += " · کشف‌شده";
    chip.textContent = label;
    chip.title = item.discovered ? `${item.code} (نوع کشف‌شده)` : item.code;
    root.appendChild(chip);
  });
  intents.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = item.is_primary ? "chip intent primary" : "chip intent";
    chip.textContent = item.is_primary ? `${item.name} · اصلی` : item.name;
    chip.title = item.code;
    root.appendChild(chip);
  });
  rhetorics.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = item.is_primary ? "chip rhetoric primary" : "chip rhetoric";
    chip.textContent = item.is_primary ? `${item.name} · اصلی` : item.name;
    chip.title = item.code;
    root.appendChild(chip);
  });
  if (payload.intended_meaning) {
    const chip = document.createElement("span");
    chip.className = "chip meaning";
    chip.textContent = "معنای مقصود";
    chip.title = payload.intended_meaning;
    root.appendChild(chip);
  }
  keywords.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip keyword";
    chip.textContent = item.phrase;
    chip.title = "کلمهٔ کلیدی";
    root.appendChild(chip);
  });
  topics.forEach((item) => {
    const chip = document.createElement("span");
    const discovered = item.discovered ? " discovered" : "";
    chip.className = item.is_primary ? `chip primary${discovered}` : `chip${discovered}`;
    const path = (item.path || []).join(" / ") || item.name;
    let label = item.is_primary ? `${path} · اصلی` : path;
    if (item.discovered) label += " · کشف‌شده";
    chip.textContent = label;
    chip.title = item.discovered ? `${item.code} (کشف‌شده)` : item.code;
    root.appendChild(chip);
  });
}

function setTabCount(pane, label, count, failed) {
  const tab = document.querySelector(`.tab[data-pane="${pane}"]`);
  if (!tab) return;
  tab.classList.toggle("tab-error", Boolean(failed));
  if (failed) {
    tab.textContent = `${label} (نیامد)`;
    return;
  }
  tab.textContent = `${label} (${count})`;
}

function renderPane(pane, error, rows, headers) {
  const root = $(`pane-${pane}`);
  if (error) {
    root.innerHTML = `<p class="error">${escapeHtml(error)}</p><p class="muted">همین لایه را جدا بزن یا همه را از نو اجرا کن.</p>`;
    return;
  }
  renderTable(rows, headers, root);
}

function renderResult(payload, sourceText) {
  const mentions = payload.mentions || [];
  const keywords = payload.keywords || [];
  const types = [...new Set(mentions.map((item) => item.type))];
  if (keywords.length) types.push("KEYWORD");
  renderLegend(types);
  renderChips(payload);
  renderSpeechSummary(payload);
  const box = $("highlight");
  box.classList.remove("empty");
  box.innerHTML = highlightText(sourceText, mentions, keywords) || escapeHtml(sourceText);
  const errors = payload.layer_errors || {};
  setTabCount("mentions", "ذکرها", mentions.length, errors.entities);
  setTabCount("keywords", "کلمات کلیدی", keywords.length, errors.keywords);
  setTabCount("topics", "موضوع", (payload.topics || []).length, errors.topics);
  setTabCount(
    "stance",
    "احساس",
    (payload.sentiment ? 1 : 0) + (payload.emotions || []).length,
    errors.sentiment,
  );
  setTabCount("discourse", "ژانر", (payload.discourses || []).length, errors.discourse);
  setTabCount("intent", "نیت", (payload.intents || []).length, errors.intent);
  setTabCount("rhetoric", "بیان", (payload.rhetorics || []).length, errors.rhetoric);
  setTabCount("entities", "canonical", (payload.entities || []).length, errors.entities);
  setTabCount("trace", "اجرا", tracesOf(payload).length);
  renderPane(
    "mentions",
    errors.entities,
    mentions.map((item) => [
      item.id != null ? String(item.id) : "—",
      item.type,
      item.canonical_name,
      item.mention_text,
      String(item.confidence),
      item.occurred_at || "—",
      item.status || "پیش‌نمایش",
    ]),
    ["id", "نوع", "canonical", "شاهد", "اطمینان", "زمان", "وضعیت"],
  );
  renderPane(
    "entities",
    errors.entities,
    (payload.entities || []).map((item) => [
      item.id != null ? String(item.id) : "—",
      item.type,
      item.canonical_name,
      String(item.mention_count),
      item.status || "پیش‌نمایش",
    ]),
    ["id", "نوع", "canonical", "تعداد ذکر", "وضعیت"],
  );
  renderPane(
    "keywords",
    errors.keywords,
    (payload.keywords || []).map((item) => [
      item.id != null ? String(item.id) : "—",
      item.phrase,
      item.mention_text,
      String(item.confidence),
    ]),
    ["id", "عبارت", "شاهد", "اطمینان"],
  );
  renderPane(
    "topics",
    errors.topics,
    (payload.topics || []).map((item) => [
      item.is_primary ? "اصلی" : "—",
      (item.path || []).join(" / ") || item.name,
      item.code,
      item.discovered ? "کشف‌شده" : "—",
      item.mention_text || "—",
      String(item.confidence),
    ]),
    ["اصلی", "مسیر", "کد", "منبع", "شاهد", "اطمینان"],
  );
  const stanceRows = [];
  if (payload.sentiment) {
    stanceRows.push([
      "قطبیت",
      payload.sentiment.polarity_name,
      payload.sentiment.intensity_name,
      payload.sentiment.mention_text || "—",
      String(payload.sentiment.confidence),
    ]);
  }
  (payload.emotions || []).forEach((item) => {
    stanceRows.push([
      "هیجان",
      item.name,
      item.intensity_name,
      item.mention_text || "—",
      String(item.confidence),
    ]);
  });
  renderPane("stance", errors.sentiment, stanceRows, ["لایه", "برچسب", "شدت", "شاهد", "اطمینان"]);
  renderPane(
    "discourse",
    errors.discourse,
    (payload.discourses || []).map((item) => [
      item.is_primary ? "اصلی" : "—",
      item.discovered ? "کشف‌شده" : "—",
      item.name,
      item.code,
      item.mention_text || "—",
      formatSlots(item.slots),
      item.type_schema && item.type_schema.definition ? item.type_schema.definition : "—",
      String(item.confidence),
    ]),
    ["اصلی", "نو", "ژانر", "کد", "شاهد", "نقش‌ها", "تعریف", "اطمینان"],
  );
  renderPane(
    "intent",
    errors.intent,
    (payload.intents || []).map((item) => [
      item.is_primary ? "اصلی" : "—",
      item.name,
      item.code,
      item.mention_text || "—",
      formatSlots(item.slots),
      String(item.confidence),
    ]),
    ["اصلی", "نیت", "کد", "شاهد", "نقش‌ها", "اطمینان"],
  );
  renderPane(
    "rhetoric",
    errors.rhetoric,
    (payload.rhetorics || []).map((item) => [
      item.is_primary ? "اصلی" : "—",
      item.name,
      item.code,
      item.mention_text || "—",
      formatSlots(item.slots),
      item.intended_meaning || payload.intended_meaning || "—",
      String(item.confidence),
    ]),
    ["اصلی", "بیان", "کد", "شاهد", "نقش‌ها", "مقصود", "اطمینان"],
  );
  renderTable(
    tracesOf(payload).map((item) => [
      TOOL_LABELS[item.name] || item.name,
      item.name,
      item.status || "—",
      formatMs(item.duration_ms),
      item.chain || "—",
      item.slowest_step
        ? `${item.slowest_step} ${formatMs(item.slowest_ms)}`
        : "—",
    ]),
    ["لایه", "ابزار", "وضعیت", "زمان", "مراحل", "کندترین"],
    $("pane-trace"),
  );
  $("pane-json").textContent = JSON.stringify(payload, null, 2);
}

let lastExtract = null;
let catalogs = null;

function setSaveEnabled(enabled) {
  const button = $("btn-save");
  if (button) button.disabled = !enabled;
}

function fillSelect(id, items) {
  const node = $(id);
  const current = node.value;
  node.innerHTML = '<option value="">بدون انتظار</option>';
  (items || []).forEach((item) => {
    const option = document.createElement("option");
    option.value = item.code;
    option.textContent = item.name;
    node.appendChild(option);
  });
  if (current && [...node.options].some((item) => item.value === current)) {
    node.value = current;
  }
}

function catalogBlock(title, rows, headers) {
  if (!rows.length) return "";
  return `
    <div class="catalog-block">
      <h3>${escapeHtml(title)} (${rows.length})</h3>
      <table class="data">
        <thead><tr>${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows
            .map(
              (row) =>
                `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderCatalog(payload) {
  const root = $("pane-catalog");
  const entityRows = (payload.entity_types || []).map((item) => [
    item.code,
    item.name,
    (item.aliases || []).join("، ") || "—",
  ]);
  const topicRows = (payload.topics || []).map((item) => [
    item.code,
    item.name,
    String(item.level || 1),
    item.definition || "—",
  ]);
  const polarityRows = (payload.polarities || []).map((item) => [item.code, item.name]);
  const emotionRows = (payload.emotions || []).map((item) => [item.code, item.name]);
  const speechRows = (items) =>
    (items || []).map((item) => [item.name, item.code, item.definition || "—"]);
  root.innerHTML = [
    catalogBlock("موجودیت", entityRows, ["کد", "نام", "هم‌معنی"]),
    catalogBlock("موضوع", topicRows, ["کد", "نام", "سطح", "تعریف"]),
    catalogBlock("قطبیت", polarityRows, ["کد", "نام"]),
    catalogBlock("هیجان", emotionRows, ["کد", "نام"]),
    catalogBlock("ژانر", speechRows(payload.discourses), ["نام", "کد", "تعریف"]),
    catalogBlock("نیت", speechRows(payload.intents), ["نام", "کد", "تعریف"]),
    catalogBlock("بیان", speechRows(payload.rhetorics), ["نام", "کد", "تعریف"]),
  ].join("");
}

function sampleKey(item, index) {
  return `${item.group || "x"}:${item.label || ""}:${index}`;
}

function setSample(item, index) {
  $("text").value = item.text || "";
  const note = item.note || "";
  $("sample-note").textContent = note;
  $("sample-note").classList.toggle("hidden", !note);
  $("expected-discourse").value = item.expected_discourse || "";
  $("expected-intent").value = item.expected_intent || "";
  $("expected-rhetoric").value = item.expected_rhetoric || "";
  $("error").classList.add("hidden");
  lastExtract = null;
  setSaveEnabled(false);
  $("speech-summary").classList.add("hidden");
  $("speech-summary").innerHTML = "";
  document.querySelectorAll("#samples button[data-sample]").forEach((button) => {
    button.classList.toggle("active", button.dataset.sample === sampleKey(item, index));
  });
}

function renderSamples(payload) {
  const root = $("samples");
  root.innerHTML = "";
  const samples = payload.samples || payload.examples || [];
  const groups = payload.groups && payload.groups.length ? payload.groups : GROUP_ORDER;
  groups.forEach((group) => {
    const items = samples
      .map((item, index) => ({ item, index }))
      .filter((row) => row.item.group === group.id);
    if (!items.length) return;
    const block = document.createElement("div");
    block.className = "sample-group";
    const label = document.createElement("p");
    label.className = "group-label";
    label.textContent = group.name;
    const row = document.createElement("div");
    row.className = "sample-row";
    items.forEach(({ item, index }) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "ghost";
      button.textContent = item.label || item.note || group.name;
      button.dataset.sample = sampleKey(item, index);
      button.title = item.note || item.text || "";
      button.addEventListener("click", () => setSample(item, index));
      row.appendChild(button);
    });
    block.appendChild(label);
    block.appendChild(row);
    root.appendChild(block);
  });
}

async function loadCatalogs() {
  const payload = await fetch("/api/catalogs").then((res) => res.json());
  catalogs = payload;
  fillSelect("expected-discourse", payload.discourses);
  fillSelect("expected-intent", payload.intents);
  fillSelect("expected-rhetoric", payload.rhetorics);
  renderSamples(payload);
  renderCatalog(payload);
  setTabCount("catalog", "کاتالوگ", (payload.samples || payload.examples || []).length);
}

async function postExtract(path, text, extra) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, ...(extra || {}) }),
  });
  let payload;
  try {
    payload = await response.json();
  } catch (err) {
    throw new Error("پاسخ استخراج خوانده نشد");
  }
  if (payload.status === "error") {
    const layer = LAYER_FA[payload.layer] || "";
    const msg = payload.message || "استخراج شکست خورد";
    throw new Error(layer ? `${layer}: ${msg}` : msg);
  }
  return payload;
}

function joinMessages(left, right) {
  if (!left) return right || "";
  if (!right || left.includes(right)) return left;
  return `${left}؛ ${right}`;
}

function dropCopyKeywords(keywords, mentions) {
  const names = new Set();
  (mentions || []).forEach((mention) => {
    if (mention.normalized_name) names.add(mention.normalized_name);
    if (mention.canonical_name) names.add(mention.canonical_name);
    if (mention.mention_text) names.add(mention.mention_text);
  });
  return (keywords || []).filter((item) => !names.has(item.phrase));
}

function applyExtract(payload, text, pane) {
  lastExtract = {
    text: payload.normalized_text || text,
    payload: attachSpeechScore({ ...payload, traces: tracesOf(payload) }),
  };
  renderResult(lastExtract.payload, lastExtract.text);
  showPane(pane || "mentions");
}

function mergeExtraLayer(name, part) {
  const current = lastExtract.payload;
  const next = { ...current };
  if (name === "keywords") {
    const keywords = dropCopyKeywords(part.keywords || [], current.mentions || []);
    next.keywords = keywords;
    next.keyword_count = keywords.length;
    next.message = joinMessages(next.message, part.message);
  } else if (name === "topics") {
    next.topics = part.topics || [];
    next.topic_count = part.topic_count || next.topics.length;
    next.message = joinMessages(next.message, part.message);
  } else if (name === "sentiment") {
    next.sentiment = part.sentiment || null;
    next.emotions = part.emotions || [];
    next.emotion_count = part.emotion_count || next.emotions.length;
    next.message = joinMessages(next.message, part.message);
  } else if (name === "discourse") {
    next.discourses = part.discourses || [];
    next.discourse_count = part.discourse_count || next.discourses.length;
    next.message = joinMessages(next.message, part.message);
  } else if (name === "intent") {
    next.intents = part.intents || [];
    next.intent_count = part.intent_count || next.intents.length;
    next.message = joinMessages(next.message, part.message);
  } else if (name === "rhetoric") {
    next.rhetorics = part.rhetorics || [];
    next.rhetoric_count = part.rhetoric_count || next.rhetorics.length;
    next.intended_meaning = part.intended_meaning || "";
    next.message = joinMessages(next.message, part.message);
  }
  lastExtract = { text: lastExtract.text, payload: attachSpeechScore(next) };
}

function extractErrorMessage(err) {
  const raw = err && err.message ? String(err.message) : "";
  if (err && err.name === "AbortError") return "زمان استخراج تمام شد";
  if (/Failed to fetch|NetworkError|network/i.test(raw)) {
    return "ارتباط با سرور قطع شد. اگر زمین بازی بسته است دوباره python -m playground را بزن.";
  }
  return raw || "استخراج شکست خورد";
}

function hitsOf(layer) {
  if (!layer || layer.error) return [];
  return layer.hits || [];
}

function tracesFromCheck(payload) {
  return ["discourse", "intent", "rhetoric"]
    .map((name) => payload[name] && payload[name].trace)
    .filter(Boolean);
}

function payloadFromCheck(check, text) {
  const previous =
    lastExtract && (lastExtract.text === text || lastExtract.payload.normalized_text === text)
      ? lastExtract.payload
      : {};
  return attachSpeechScore({
    ...previous,
    status: "success",
    message:
      check.ok === false
        ? "بعضی انتظارها نخواند"
        : check.ok === true
          ? "با انتظار یکی است"
          : check.message || "ژانر و نیت و بیان آمد",
    discourses: hitsOf(check.discourse),
    discourse_count: hitsOf(check.discourse).length,
    intents: hitsOf(check.intent),
    intent_count: hitsOf(check.intent).length,
    rhetorics: hitsOf(check.rhetoric),
    rhetoric_count: hitsOf(check.rhetoric).length,
    intended_meaning: check.intended_meaning || "",
    speech_score: check,
    traces: tracesFromCheck(check),
    normalized_text: previous.normalized_text || text,
  });
}

const LAYER_FA = {
  entities: "موجودیت",
  keywords: "کلمهٔ کلیدی",
  topics: "موضوع",
  sentiment: "احساس",
  discourse: "ژانر",
  intent: "نیت",
  rhetoric: "بیان",
};

const PANE_FOR_LAYER = {
  entities: "mentions",
  keywords: "keywords",
  topics: "topics",
  sentiment: "stance",
  discourse: "discourse",
  intent: "intent",
  rhetoric: "rhetoric",
};

function isTimeoutMessage(msg) {
  return /زمان پاسخ مدل|timeout/i.test(String(msg || ""));
}

async function extractLayerNamed(name, text, extra) {
  const path = `/api/extract/${name}`;
  try {
    return await postExtract(path, text, extra);
  } catch (err) {
    if (!isTimeoutMessage(err && err.message)) throw err;
    $("status").textContent = `${LAYER_FA[name]} زمانش تمام شد؛ یک‌بار دیگر…`;
    return postExtract(path, text, extra);
  }
}

async function extractAll(text) {
  lastExtract = null;
  const traces = [];
  const warnings = [];
  const layerErrors = {};

  async function runOne(name, extra) {
    $("status").textContent = `در حال استخراج ${LAYER_FA[name]}…`;
    const pane = PANE_FOR_LAYER[name];
    try {
      const part = await extractLayerNamed(name, text, extra);
      traces.push(...tracesOf(part));
      delete layerErrors[name];
      if (name === "entities") {
        applyExtract(
          { ...part, traces: [...traces], layer_errors: { ...layerErrors } },
          text,
          pane,
        );
      } else {
        mergeExtraLayer(name, part);
        applyExtract(
          { ...lastExtract.payload, traces: [...traces], layer_errors: { ...layerErrors } },
          lastExtract.text,
          pane,
        );
      }
    } catch (err) {
      const msg = (err && err.message) || LAYER_FA[name];
      warnings.push(`${LAYER_FA[name]}: ${msg}`);
      layerErrors[name] = msg;
      if (lastExtract) {
        applyExtract(
          { ...lastExtract.payload, traces: [...traces], layer_errors: { ...layerErrors } },
          lastExtract.text,
          pane,
        );
      }
    }
  }

  await runOne("entities", {});
  if (!lastExtract) {
    throw new Error(layerErrors.entities || "موجودیت نیامد");
  }
  await runOne("keywords", {});
  await runOne("topics", {});
  await runOne("rhetoric", {});
  const primaryRhetoric = (lastExtract.payload.rhetorics || []).find((item) => item.is_primary);
  const meaning =
    lastExtract.payload.intended_meaning && primaryRhetoric && primaryRhetoric.code !== "literal"
      ? lastExtract.payload.intended_meaning
      : "";
  const extra = meaning ? { intended_meaning: meaning } : {};
  await runOne("sentiment", extra);
  await runOne("discourse", extra);
  await runOne("intent", extra);
  applyExtract(
    { ...lastExtract.payload, traces: [...traces], layer_errors: { ...layerErrors } },
    lastExtract.text,
    "mentions",
  );
  const timing = traceSummary(traces);
  $("status").textContent = [lastExtract.payload.message || "انجام شد", timing]
    .filter(Boolean)
    .join(" · ");
  if (warnings.length) {
    $("error").textContent = `بعضی لایه‌ها نیامد: ${warnings.join("؛ ")}`;
    $("error").classList.remove("hidden");
  }
}

async function extractSpeech(text) {
  $("status").textContent = "در حال استخراج ژانر و نیت و بیان…";
  const payload = await postExtract("/api/check", text, {
    expected_discourse: expectedValue("expected-discourse") || undefined,
    expected_intent: expectedValue("expected-intent") || undefined,
    expected_rhetoric: expectedValue("expected-rhetoric") || undefined,
  });
  const merged = payloadFromCheck(payload, text);
  applyExtract(merged, text, "discourse");
  $("status").textContent = [merged.message || "انجام شد", formatMs(payload.duration_ms)]
    .filter(Boolean)
    .join(" · ");
}

async function extract(layer) {
  const text = $("text").value.trim();
  $("error").classList.add("hidden");
  if (!text) {
    $("error").textContent = "متن خالی است";
    $("error").classList.remove("hidden");
    return;
  }
  const buttons = document.querySelectorAll(".run-row button");
  buttons.forEach((item) => {
    item.disabled = true;
  });
  $("status").textContent =
    layer === "all"
      ? "در حال استخراج موجودیت…"
      : layer === "speech"
        ? "در حال استخراج ژانر و نیت و بیان…"
        : "در حال استخراج… معمولاً ۲۰ تا ۴۰ ثانیه طول می‌کشد.";
  try {
    if (layer === "all") {
      await extractAll(text);
      return;
    }
    if (layer === "speech") {
      await extractSpeech(text);
      return;
    }
    const payload = await postExtract(`/api/extract/${layer}`, text);
    const timing = traceSummary(tracesOf(payload));
    $("status").textContent = [payload.message || "انجام شد", timing].filter(Boolean).join(" · ");
    applyExtract(payload, text, {
      entities: "mentions",
      keywords: "keywords",
      topics: "topics",
      sentiment: "stance",
      discourse: "discourse",
      intent: "intent",
      rhetoric: "rhetoric",
    }[layer]);
  } catch (err) {
    $("error").textContent = extractErrorMessage(err);
    $("error").classList.remove("hidden");
    $("status").textContent = "";
  } finally {
    buttons.forEach((item) => {
      if (item.id === "btn-save") return;
      item.disabled = false;
    });
    setSaveEnabled(Boolean(lastExtract));
  }
}

$("btn-clear").addEventListener("click", () => {
  $("text").value = "";
  $("sample-note").classList.add("hidden");
  $("sample-note").textContent = "";
  $("status").textContent = "";
  $("expected-discourse").value = "";
  $("expected-intent").value = "";
  $("expected-rhetoric").value = "";
  lastExtract = null;
  setSaveEnabled(false);
  $("speech-summary").classList.add("hidden");
  $("speech-summary").innerHTML = "";
  document.querySelectorAll("#samples button[data-sample]").forEach((button) => {
    button.classList.remove("active");
  });
});
document.querySelectorAll(".run-row button[data-layer]").forEach((button) => {
  button.addEventListener("click", () => extract(button.dataset.layer));
});
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => showPane(tab.dataset.pane));
});

async function saveExtract() {
  if (!lastExtract) return;
  $("error").classList.add("hidden");
  const button = $("btn-save");
  button.disabled = true;
  $("status").textContent = "در حال ذخیره با وضعیت پیشنهادی…";
  try {
    const response = await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: lastExtract.text,
        source_type: "content",
        mentions: lastExtract.payload.mentions || [],
        keywords: lastExtract.payload.keywords || [],
        topics: lastExtract.payload.topics || [],
        sentiment: lastExtract.payload.sentiment || null,
        emotions: lastExtract.payload.emotions || [],
        discourses: lastExtract.payload.discourses || [],
        intents: lastExtract.payload.intents || [],
        rhetorics: lastExtract.payload.rhetorics || [],
        intended_meaning: lastExtract.payload.intended_meaning || undefined,
        model: lastExtract.payload.model || undefined,
      }),
    });
    const payload = await response.json();
    if (payload.status === "error") {
      throw new Error(payload.message || "ذخیره شکست خورد");
    }
    const merged = attachSpeechScore({
      ...lastExtract.payload,
      ...payload,
      speech_score: lastExtract.payload.speech_score,
    });
    lastExtract = { text: lastExtract.text, payload: merged };
    $("status").textContent =
      payload.message + (payload.id != null ? ` · تحلیل ${payload.id}` : "");
    renderResult(merged, lastExtract.text);
  } catch (err) {
    $("error").textContent = err.message;
    $("error").classList.remove("hidden");
    $("status").textContent = "";
    setSaveEnabled(true);
  }
}

$("btn-save").addEventListener("click", () => {
  saveExtract().catch((err) => {
    $("error").textContent = err.message;
    $("error").classList.remove("hidden");
    setSaveEnabled(true);
  });
});

loadCatalogs().catch((err) => {
  $("error").textContent = err.message || "کاتالوگ نیامد";
  $("error").classList.remove("hidden");
});
