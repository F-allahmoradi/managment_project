function $(id) {
  return document.getElementById(id);
}

const KIND_LABELS = {
  raw: "خام",
  entity: "موجودیت",
  intent: "نیت",
  intent_slot: "جزء نیت",
};
const KIND_CHECKS = [
  ["kind-raw", "raw"],
  ["kind-entity", "entity"],
  ["kind-intent", "intent"],
  ["kind-slot", "intent_slot"],
];
const SOURCE_LABELS = {
  meeting: "جلسه",
  message: "پیام",
  content: "متن",
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text != null) {
    node.textContent = text;
  }
  return node;
}

function showNodeError(id, message) {
  const node = $(id);
  if (!node) {
    return;
  }
  if (!message) {
    node.classList.add("hidden");
    node.textContent = "";
    return;
  }
  node.classList.remove("hidden");
  node.textContent = message;
}

function showError(message) {
  showNodeError("error", message);
}

function showIndexError(message) {
  showNodeError("index-error", message);
}

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return response.json();
}

function selectedKinds() {
  return KIND_CHECKS.filter(([id]) => $(id).checked).map(([, kind]) => kind);
}

function setKinds(kinds) {
  const wanted = new Set(kinds && kinds.length ? kinds : KIND_CHECKS.map(([, kind]) => kind));
  KIND_CHECKS.forEach(([id, kind]) => {
    $(id).checked = wanted.has(kind);
  });
}

function kindLabel(kind) {
  return KIND_LABELS[kind] || kind;
}

function sourceLabel(sourceType) {
  return SOURCE_LABELS[sourceType] || sourceType || "منبع";
}

function formatScore(score) {
  const value = Number(score);
  if (!Number.isFinite(value)) {
    return "—";
  }
  return value.toFixed(3);
}

function renderAnalyses(records) {
  const root = $("analyses");
  root.replaceChildren();
  if (!records || !records.length) {
    root.appendChild(el("p", "muted", "تحلیل ذخیره‌شده‌ای برای این بازیگر نیست. اول در استخراج ذخیره کن."));
    return;
  }
  records.forEach((row) => {
    const embedding = row.embedding || {};
    const indexed = Boolean(embedding.indexed);
    const card = el("div", "speech-card");
    const heading = el(
      "h3",
      null,
      `${sourceLabel(row.source_type)} #${row.source_id}`
    );
    const meta = el(
      "p",
      "muted",
      `تحلیل ${row.id} · نیت ${row.intent_count || 0} · ذکر ${row.mention_count || 0}`
    );
    const badge = el(
      "span",
      indexed ? "pill indexed" : "pill pending",
      indexed
        ? `برداری‌شده · ${embedding.card_count || 0} کارت`
        : "بدون بردار"
    );
    const counts = el(
      "p",
      "muted",
      indexed
        ? `خام ${embedding.raw_count || 0} · موجودیت ${embedding.entity_count || 0} · نیت ${embedding.intent_count || 0} · جزء ${embedding.intent_slot_count || 0}`
        : "با «امبد کن» یا «باقی‌مانده‌ها» برداری شود."
    );
    const button = el("button", indexed ? "ghost" : "primary", indexed ? "دوباره امبد کن" : "امبد کن");
    button.type = "button";
    button.addEventListener("click", () => indexOne(row.id, button));
    card.append(heading, meta, badge, counts, button);
    root.appendChild(card);
  });
}

async function loadAnalyses() {
  showIndexError("");
  $("index-status").textContent = "در حال خواندن…";
  try {
    const payload = await fetch("/api/analyses").then((item) => item.json());
    if (payload.status !== "success") {
      $("index-status").textContent = payload.message || "خواندن تحلیل ناموفق بود";
      return;
    }
    const count = (payload.records || []).length;
    const pending = (payload.records || []).filter((row) => !(row.embedding || {}).indexed).length;
    const modelBit = payload.model ? ` · ${payload.model}` : "";
    $("index-status").textContent = `${count} تحلیل · ${pending} بدون بردار${modelBit}`;
    renderAnalyses(payload.records);
  } catch (err) {
    $("index-status").textContent = "خواندن تحلیل ناموفق بود";
  }
}

async function indexOne(analysisId, button) {
  showIndexError("");
  showError("");
  $("index-status").textContent = `برداری تحلیل ${analysisId}…`;
  if (button) {
    button.disabled = true;
  }
  $("btn-pending").disabled = true;
  try {
    const payload = await postJson("/api/index", { analysis_id: analysisId });
    if (payload.status !== "success") {
      showIndexError(payload.message || "امبدینگ ناموفق بود");
      $("index-status").textContent = "ایندکس نشد";
      return;
    }
    $("index-status").textContent =
      `تحلیل ${payload.analysis_id}: خام ${payload.raw_count}، موجودیت ${payload.entity_count}، نیت ${payload.intent_count}، جزء ${payload.intent_slot_count}`;
    await loadAnalyses();
  } catch (err) {
    showIndexError("امبدینگ ناموفق بود");
    $("index-status").textContent = "ایندکس نشد";
  } finally {
    if (button) {
      button.disabled = false;
    }
    $("btn-pending").disabled = false;
  }
}

async function indexPending() {
  showIndexError("");
  showError("");
  $("index-status").textContent = "برداری باقی‌مانده‌ها…";
  $("btn-pending").disabled = true;
  try {
    const payload = await postJson("/api/index-pending", { limit: 20 });
    if (payload.status !== "success") {
      showIndexError(payload.message || "ایندکس باقی‌مانده ناموفق بود");
      return;
    }
    $("index-status").textContent = `${payload.indexed_count || 0} تحلیل برداری شد`;
    await loadAnalyses();
  } catch (err) {
    showIndexError("ایندکس باقی‌مانده ناموفق بود");
  } finally {
    $("btn-pending").disabled = false;
  }
}

function renderResults(payload) {
  const root = $("results");
  const records = payload.records || [];
  root.replaceChildren();
  if (!records.length) {
    root.classList.add("empty");
    root.textContent = "مورد مشابهی پیدا نشد. اگر فهرست بدون بردار است اول امبد کن.";
    return;
  }
  root.classList.remove("empty");
  records.forEach((row) => {
    const card = el("div", "speech-card");
    card.appendChild(
      el(
        "h3",
        null,
        `${sourceLabel(row.source_type)} #${row.source_id} · تحلیل ${row.analysis_id}`
      )
    );
    card.appendChild(
      el(
        "p",
        "muted",
        `امتیاز ${formatScore(row.score)} · ${(row.kinds || []).map(kindLabel).join("، ")}`
      )
    );
    const list = el("ul", "slot-list");
    (row.hits || []).forEach((hit) => {
      const item = document.createElement("li");
      const kind = el("strong", `kind-${hit.kind}`, kindLabel(hit.kind));
      item.append(kind, document.createTextNode(` (${formatScore(hit.score)}) — ${hit.text || ""}`));
      list.appendChild(item);
    });
    card.appendChild(list);
    root.appendChild(card);
  });
}

function searchBody() {
  const kinds = selectedKinds();
  const sourceType = $("source-type").value || null;
  return {
    query: $("query").value.trim(),
    kinds,
    source_type: sourceType,
    limit: 8,
  };
}

async function runSearch() {
  showError("");
  const body = searchBody();
  if (!body.query) {
    showError("سؤال خالی است");
    return;
  }
  $("search-status").textContent = "در حال جستجو…";
  $("btn-search").disabled = true;
  try {
    const payload = await postJson("/api/search", body);
    if (payload.status !== "success") {
      showError(payload.message || "جستجو ناموفق بود");
      $("search-status").textContent = "";
      return;
    }
    $("search-status").textContent = `${payload.hit_count || 0} منبع`;
    renderResults(payload);
  } catch (err) {
    showError("جستجو ناموفق بود");
    $("search-status").textContent = "";
  } finally {
    $("btn-search").disabled = false;
  }
}

function markActiveSample(sampleId) {
  document.querySelectorAll("#search-samples button[data-id]").forEach((button) => {
    button.classList.toggle("active", button.dataset.id === sampleId);
  });
}

function applySample(sample) {
  $("query").value = sample.query || "";
  setKinds(sample.kinds);
  $("sample-note").textContent = sample.expect || "";
  markActiveSample(sample.id);
  runSearch();
}

function renderSamples(samples) {
  const root = $("search-samples");
  root.replaceChildren();
  let lastGroup = null;
  (samples || []).forEach((sample) => {
    if (sample.group && sample.group !== lastGroup) {
      root.appendChild(el("span", "sample-group", sample.group));
      lastGroup = sample.group;
    }
    const button = el("button", "ghost", sample.label);
    button.type = "button";
    button.dataset.id = sample.id;
    button.title = sample.query || "";
    button.addEventListener("click", () => applySample(sample));
    root.appendChild(button);
  });
}

async function loadSearchSamples() {
  try {
    const payload = await fetch("/api/search-samples").then((item) => item.json());
    if (payload.status !== "success") {
      $("sample-note").textContent = payload.message || "";
      return;
    }
    renderSamples(payload.samples);
    $("sample-note").textContent = payload.message || "";
  } catch (err) {
    $("sample-note").textContent = "نمونه‌ها نیامدند.";
  }
}

function recordTitle(row) {
  return (
    row.title ||
    row.name ||
    row.message_template ||
    (row.source_type ? `${row.source_type} #${row.source_id}` : "") ||
    (row.id != null ? `#${row.id}` : "بدون عنوان")
  );
}

function recordMeta(row) {
  const skip = new Set([
    "title",
    "name",
    "message_template",
    "id",
    "text",
    "body",
    "embedding_vector",
  ]);
  return Object.entries(row)
    .filter(([key, value]) => !skip.has(key) && value != null && typeof value !== "object")
    .slice(0, 6)
    .map(([key, value]) => `${key}: ${value}`)
    .join(" · ");
}

function renderSnapshot(payload) {
  const root = $("snapshot-groups");
  root.innerHTML = "";
  const groups = payload.groups || [];
  if (!groups.length) {
    root.innerHTML = "<p class='muted'>نمایی برای نمایش نیست.</p>";
    return;
  }
  groups.forEach((group) => {
    const wrap = document.createElement("div");
    wrap.className = "group";
    const heading = document.createElement("h3");
    heading.textContent = group.title;
    wrap.appendChild(heading);
    if (group.error) {
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = group.error;
      wrap.appendChild(error);
      root.appendChild(wrap);
      return;
    }
    const records = group.records || [];
    if (!records.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "موردی نیست.";
      wrap.appendChild(empty);
    } else {
      records.forEach((row) => {
        const card = document.createElement("div");
        card.className = "speech-card";
        card.innerHTML = `<h3>${recordTitle(row)}</h3><p class="muted">${recordMeta(row)}</p>`;
        wrap.appendChild(card);
      });
    }
    root.appendChild(wrap);
  });
}

async function loadSnapshot(mcpId) {
  showNodeError("snapshot-error", "");
  $("snapshot-status").textContent = "در حال خواندن…";
  $("btn-snapshot").disabled = true;
  try {
    const payload = await fetch(`/api/mcp/${mcpId}`).then((item) => item.json());
    if (payload.status !== "success") {
      showNodeError("snapshot-error", payload.message || "خواندن ناموفق بود");
      $("snapshot-status").textContent = "";
      $("snapshot-groups").innerHTML = "";
      return;
    }
    $("snapshot-status").textContent = payload.message || "";
    renderSnapshot(payload);
  } finally {
    $("btn-snapshot").disabled = false;
  }
}

function extractSummary(payload) {
  const bits = [
    ["ذکر", payload.extracted_count || (payload.mentions || []).length],
    ["کلیدی", payload.keyword_count || (payload.keywords || []).length],
    ["موضوع", payload.topic_count || (payload.topics || []).length],
    ["ژانر", payload.discourse_count || (payload.discourses || []).length],
    ["نیت", payload.intent_count || (payload.intents || []).length],
  ];
  if (payload.sentiment && payload.sentiment.label) {
    bits.push(["احساس", payload.sentiment.label]);
  }
  return bits;
}

function nlpSummary(payload) {
  const bits = [
    ["فکت", payload.fact_count || (payload.facts || []).length],
    ["نقل‌قول", payload.quote_count || (payload.quotes || []).length],
  ];
  if (payload.explicitness_name) {
    bits.push(["صراحت", payload.explicitness_name]);
  }
  if (payload.frame && payload.frame.title) {
    bits.push(["قاب", payload.frame.title]);
  } else {
    bits.push(["قاب", "—"]);
  }
  return bits;
}

function renderChips(rootId, bits) {
  const chips = $(rootId);
  chips.innerHTML = "";
  bits.forEach(([label, value]) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = `${label}: ${value}`;
    chips.appendChild(chip);
  });
}

async function runExtract() {
  showNodeError("extract-error", "");
  const text = $("ner-text").value.trim();
  if (!text) {
    showNodeError("extract-error", "متن خالی است");
    return;
  }
  $("extract-status").textContent = "در حال استخراج…";
  $("btn-extract").disabled = true;
  try {
    const payload = await postJson("/api/mcp/ner/extract", { text });
    if (payload.status === "error") {
      showNodeError("extract-error", payload.message || "استخراج ناموفق بود");
      $("extract-status").textContent = "";
      return;
    }
    $("extract-status").textContent = payload.message || "استخراج شد";
    renderChips("extract-chips", extractSummary(payload));
    $("extract-json").textContent = JSON.stringify(payload, null, 2);
  } finally {
    $("btn-extract").disabled = false;
  }
}

async function loadSample() {
  const payload = await fetch("/api/mcp/ner/sample").then((item) => item.json());
  if (payload.status !== "success") {
    showNodeError("extract-error", payload.message || "نمونه نیامد");
    return;
  }
  $("ner-text").value = payload.text || "";
}

async function runNlpExtract() {
  showNodeError("nlp-error", "");
  const text = $("nlp-text").value.trim();
  if (!text) {
    showNodeError("nlp-error", "متن خالی است");
    return;
  }
  $("nlp-status").textContent = "در حال استخراج…";
  $("btn-nlp-extract").disabled = true;
  try {
    const payload = await postJson("/api/mcp/nlp/extract", { text });
    if (payload.status === "error") {
      showNodeError("nlp-error", payload.message || "استخراج ناموفق بود");
      $("nlp-status").textContent = "";
      return;
    }
    $("nlp-status").textContent = payload.message || "استخراج شد";
    renderChips("nlp-chips", nlpSummary(payload));
    $("nlp-json").textContent = JSON.stringify(payload, null, 2);
  } finally {
    $("btn-nlp-extract").disabled = false;
  }
}

async function loadNlpSample() {
  const payload = await fetch("/api/mcp/nlp/sample").then((item) => item.json());
  if (payload.status !== "success") {
    showNodeError("nlp-error", payload.message || "نمونه نیامد");
    return;
  }
  $("nlp-text").value = payload.text || "";
}

let sections = [];
let current = "embedding";

function panelFor(section) {
  if (section.ui === "embedding") {
    return "panel-embedding";
  }
  if (section.ui === "extract") {
    return "panel-extract";
  }
  if (section.ui === "nlp-extract") {
    return "panel-nlp";
  }
  if (section.ui === "empty") {
    return "panel-empty";
  }
  return "panel-snapshot";
}

function showPanel(id) {
  ["panel-embedding", "panel-extract", "panel-nlp", "panel-snapshot", "panel-empty"].forEach(
    (panel) => {
      $(panel).classList.toggle("hidden", panel !== id);
    }
  );
}

function activate(mcpId) {
  const section = sections.find((item) => item.id === mcpId) || sections[0];
  if (!section) {
    return;
  }
  current = section.id;
  if (location.hash.slice(1) !== current) {
    location.hash = current;
  }
  $("section-blurb").textContent = section.blurb;
  $("server-pill").textContent = section.server;
  document.querySelectorAll(".mcp-nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.id === current);
  });
  showPanel(panelFor(section));
  if (section.ui === "embedding") {
    loadAnalyses();
  } else if (section.ui === "snapshot") {
    $("snapshot-title").textContent = section.title;
    loadSnapshot(section.id);
  } else if (section.ui === "empty") {
    $("empty-blurb").textContent = section.blurb;
  }
}

function renderNav() {
  const nav = $("mcp-nav");
  nav.innerHTML = "";
  sections.forEach((section) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.id = section.id;
    button.textContent = section.title;
    button.addEventListener("click", () => activate(section.id));
    nav.appendChild(button);
  });
}

async function boot() {
  try {
    const payload = await fetch("/api/hub").then((item) => item.json());
    sections = payload.sections || [];
  } catch (err) {
    $("section-blurb").textContent = "کاتالوگ زمین بازی نیامد.";
    return;
  }
  renderNav();
  await loadSearchSamples();
  const wanted = location.hash.slice(1) || "embedding";
  activate(wanted);
}

$("btn-refresh").addEventListener("click", loadAnalyses);
$("btn-pending").addEventListener("click", indexPending);
$("btn-search").addEventListener("click", runSearch);
$("query").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    runSearch();
  }
});
$("btn-extract").addEventListener("click", runExtract);
$("btn-sample").addEventListener("click", loadSample);
$("btn-nlp-extract").addEventListener("click", runNlpExtract);
$("btn-nlp-sample").addEventListener("click", loadNlpSample);
$("btn-snapshot").addEventListener("click", () => loadSnapshot(current));
window.addEventListener("hashchange", () => {
  const wanted = location.hash.slice(1);
  if (wanted && wanted !== current) {
    activate(wanted);
  }
});
boot();
