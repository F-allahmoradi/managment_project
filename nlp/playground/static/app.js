const KIND_COLORS = {
  quantity: "#5a9bd4",
  condition: "#8a8a8a",
  change: "#d4a15a",
  cause: "#d46a6a",
  status: "#6aae7a",
  quote: "#9b7ed9",
  speaker: "#7eb0d4",
  frame: "#c9a227",
  task: "#3aa39a",
  score: "#c47a4a",
  topic: "#7a8fd4",
  entity: "#b07a9a",
};

const KIND_LABELS = {
  quantity: "مقدار",
  condition: "شرط",
  change: "تغییر",
  cause: "علت",
  status: "وضعیت",
  quote: "نقل‌قول",
  speaker: "گوینده",
  frame: "قاب",
  task: "وظیفه",
  score: "امتیاز",
  topic: "موضوع",
  entity: "موجودیت",
};

function $(id) {
  return document.getElementById(id);
}

function showPane(name) {
  ["facts", "causes", "task", "score", "ner", "quotes", "frame", "trace", "json"].forEach((pane) => {
    $(`pane-${pane}`).classList.toggle("hidden", pane !== name);
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
    item.innerHTML = `<i style="background:${KIND_COLORS[type] || "#666"}"></i>${KIND_LABELS[type] || type}`;
    root.appendChild(item);
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function spanOf(text, fragment, startOffset, endOffset) {
  if (
    Number.isInteger(startOffset) &&
    Number.isInteger(endOffset) &&
    startOffset >= 0 &&
    endOffset > startOffset &&
    endOffset <= text.length
  ) {
    return { start_offset: startOffset, end_offset: endOffset };
  }
  const needle = String(fragment || "");
  if (!needle) return null;
  const start = text.indexOf(needle);
  if (start < 0) return null;
  return { start_offset: start, end_offset: start + needle.length };
}

function highlightSpans(text, spans) {
  const sorted = [...spans].sort((a, b) => {
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
    const color = KIND_COLORS[item.type] || "#666";
    const label = escapeHtml(KIND_LABELS[item.type] || item.type);
    const name = escapeHtml(item.label || "");
    html += `<mark style="background:${color}33; border-bottom: 2px solid ${color}" title="${label}: ${name}">${escapeHtml(
      text.slice(start, end),
    )}</mark>`;
    cursor = end;
  });
  html += escapeHtml(text.slice(cursor));
  return html;
}

function formatMs(ms) {
  if (ms == null || ms === "") return "—";
  const value = Number(ms);
  if (!Number.isFinite(value)) return "—";
  if (value < 1000) return `${Math.round(value)}ms`;
  return `${(value / 1000).toFixed(1)}s`;
}

const TOOL_LABELS = {
  extract_facts: "فکت",
  extract_quotes: "نقل‌قول",
  extract_frame: "قاب مسئله",
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

function formatValue(item) {
  if (item.value == null || item.value === "") return "—";
  const unit = item.unit_name || item.unit || "";
  return unit ? `${item.value} ${unit}` : String(item.value);
}

function spansFrom(payload, text) {
  const spans = [];
  (payload.facts || []).forEach((item) => {
    const span = spanOf(text, item.mention_text, item.start_offset, item.end_offset);
    if (!span) return;
    spans.push({
      ...span,
      type: item.kind || "quantity",
      label: item.name || item.mention_text,
    });
  });
  (payload.quotes || []).forEach((item) => {
    const quoted = spanOf(text, item.quoted_text);
    if (quoted) {
      spans.push({ ...quoted, type: "quote", label: item.attributed_to || item.quoted_text });
    }
    const speaker = spanOf(text, item.attributed_to);
    if (speaker) {
      spans.push({ ...speaker, type: "speaker", label: item.attributed_to });
    }
  });
  if (payload.frame) {
    const frame = payload.frame;
    const span = spanOf(text, frame.mention_text || frame.about || frame.unit);
    if (span) {
      spans.push({ ...span, type: "frame", label: frame.title });
    }
  }
  return spans;
}

function renderChips(payload) {
  const root = $("chips");
  root.innerHTML = "";
  const facts = payload.facts || [];
  const quotes = payload.quotes || [];
  const frame = payload.frame;
  const suggested = suggestedTaskOf(payload);
  const scoring = scoringOf(payload);
  const topics = nerTopicsOf(payload);
  const entities = nerEntitiesOf(payload);
  if (
    !facts.length &&
    !quotes.length &&
    !frame &&
    !suggested &&
    !scoring &&
    !topics.length &&
    !entities.length &&
    !payload.explicitness_name
  ) {
    root.classList.add("hidden");
    return;
  }
  root.classList.remove("hidden");
  if (payload.explicitness_name) {
    const chip = document.createElement("span");
    chip.className = `chip explicitness ${payload.explicitness || ""}`;
    chip.textContent = payload.explicitness_name;
    chip.title = "صراحت کل متن";
    root.appendChild(chip);
  }
  facts.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = `chip fact ${item.kind || ""}`;
    chip.textContent = item.kind === "quantity" ? `${item.name} ${formatValue(item)}` : item.name;
    chip.title = `${item.kind_name || item.kind} · ${item.grounding_name || item.grounding}`;
    root.appendChild(chip);
  });
  quotes.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip quote";
    chip.textContent = item.attributed_to || item.mode_name || "نقل‌قول";
    chip.title = item.quoted_text || "";
    root.appendChild(chip);
  });
  if (frame) {
    const chip = document.createElement("span");
    chip.className = "chip frame";
    chip.textContent = frame.title;
    chip.title = [frame.unit, frame.process_name, frame.scope_name].filter(Boolean).join(" · ");
    root.appendChild(chip);
  }
  if (suggested) {
    const chip = document.createElement("span");
    chip.className = "chip task";
    chip.textContent = suggested.title || suggested.task_title;
    chip.title = suggested.created ? "جدید" : suggested.task_id != null ? "وصل‌شده" : "پیشنهادی";
    root.appendChild(chip);
  }
  if (scoring) {
    const chip = document.createElement("span");
    chip.className = "chip score";
    const impacts = impactLabels(scoring).join(" / ") || "—";
    chip.textContent = `${scoring.importance || "—"} · ${scoring.severity || "—"}`;
    chip.title = `فوریت ${scoring.urgency || "—"} · اثر ${impacts}`;
    root.appendChild(chip);
  }
  topics.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip topic";
    chip.textContent = item.name || item.topic_name || item.code || "موضوع";
    chip.title = item.code || "";
    root.appendChild(chip);
  });
  entities.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip entity";
    chip.textContent = item.canonical_name || "موجودیت";
    chip.title = `${item.type || ""} · ${item.role_name || item.role || ""}`.trim();
    root.appendChild(chip);
  });
}

function setTabCount(pane, label, count) {
  const tab = document.querySelector(`.tab[data-pane="${pane}"]`);
  if (tab) tab.textContent = `${label} (${count})`;
}

function causesOf(payload) {
  return (payload.facts || []).filter((item) => item.kind === "cause");
}

function suggestedTaskOf(payload) {
  if (!payload) return null;
  if (payload.task && (payload.task.title || payload.task.task_title)) {
    return payload.task;
  }
  return payload.suggested_task || null;
}

function scoringOf(payload) {
  if (!payload) return null;
  if (payload.scoring && (payload.scoring.importance || payload.scoring.severity)) {
    return payload.scoring;
  }
  return payload.suggested_scoring || null;
}

function impactLabels(scoring) {
  if (!scoring) return [];
  const rows = scoring.impacts || [];
  return rows.map((item) => {
    if (typeof item === "string") return item;
    return item.impact_type_name || item.impact_type || item.description || "";
  }).filter(Boolean);
}

function nerOf(payload) {
  if (!payload) return { topics: [], entities: [] };
  const linkedTopics = payload.topics || [];
  const linkedEntities = payload.entities || [];
  const suggestedTopics = payload.suggested_topics || [];
  const suggestedEntities = payload.suggested_entities || [];
  return {
    topics: linkedTopics.length ? linkedTopics : suggestedTopics,
    entities: linkedEntities.length ? linkedEntities : suggestedEntities,
  };
}

function nerPending(payload) {
  if (!payload || !scoringOf(payload)) return false;
  const suggested = (payload.suggested_topics || []).length + (payload.suggested_entities || []).length;
  if (!suggested) return false;
  const linked = (payload.topics || []).length + (payload.entities || []).length;
  return linked === 0;
}

function nerTopicsOf(payload) {
  if (!payload) return [];
  if (Array.isArray(payload.topics) && payload.topics.length) return payload.topics;
  return payload.suggested_topics || [];
}

function nerEntitiesOf(payload) {
  if (!payload) return [];
  if (Array.isArray(payload.entities) && payload.entities.length) return payload.entities;
  return payload.suggested_entities || [];
}

function nerLinked(payload) {
  if (!payload) return false;
  return Boolean((payload.topics || []).length || (payload.entities || []).length);
}

function renderResult(payload, sourceText) {
  const facts = payload.facts || [];
  const quotes = payload.quotes || [];
  const causes = causesOf(payload);
  const types = [...new Set(facts.map((item) => item.kind).filter(Boolean))];
  if (quotes.length) types.push("quote");
  if (payload.frame) types.push("frame");
  if (suggestedTaskOf(payload)) types.push("task");
  if (scoringOf(payload)) types.push("score");
  if (nerTopicsOf(payload).length) types.push("topic");
  if (nerEntitiesOf(payload).length) types.push("entity");
  renderLegend(types);
  renderChips(payload);
  const box = $("highlight");
  box.classList.remove("empty");
  const spans = spansFrom(payload, sourceText);
  box.innerHTML = highlightSpans(sourceText, spans) || escapeHtml(sourceText);
  setTabCount("facts", "فکت‌ها", facts.length);
  setTabCount("causes", "علت‌ها", causes.length);
  setTabCount("task", "وظیفه", suggestedTaskOf(payload) ? 1 : 0);
  const scoring = scoringOf(payload);
  setTabCount("score", "امتیاز", scoring ? 1 : 0);
  const topics = nerTopicsOf(payload);
  const entities = nerEntitiesOf(payload);
  setTabCount("ner", "موضوع و موجودیت", topics.length + entities.length);
  setTabCount("quotes", "نقل‌قول", quotes.length);
  setTabCount("frame", "قاب مسئله", payload.frame ? 1 : 0);
  setTabCount("trace", "اجرا", tracesOf(payload).length);
  renderTable(
    facts.map((item) => [
      item.fact_id || "—",
      item.kind_name || item.kind,
      item.name,
      formatValue(item),
      item.role && item.role !== "none" ? item.role : "—",
      item.grounding_name || item.grounding || "—",
      item.derivation || "—",
      item.mention_text || "—",
      String(item.confidence),
    ]),
    ["id", "نوع", "نام", "مقدار", "نقش", "صراحت", "حساب", "شاهد", "اطمینان"],
    $("pane-facts"),
  );
  const savedCauses = payload.causes || [];
  const savedByTitle = new Map(
    savedCauses.map((item) => [item.cause_title, item]),
  );
  renderTable(
    causes.map((item) => {
      const saved = savedByTitle.get(item.name) || {};
      return [
        item.name,
        item.effect || "—",
        item.grounding_name || item.grounding || "—",
        item.mention_text || "—",
        saved.cause_issue_id != null ? String(saved.cause_issue_id) : "پیشنهادی",
        saved.cause_level_name || saved.cause_level_code || "علت",
        saved.reused ? "موجود" : saved.cause_issue_id != null ? "جدید" : "—",
        String(item.confidence),
      ];
    }),
    ["عنوان علت", "معلول", "صراحت", "شاهد", "مسئله", "سطح", "وصل", "اطمینان"],
    $("pane-causes"),
  );
  const suggested = suggestedTaskOf(payload);
  renderTable(
    suggested
      ? [[
          suggested.title || suggested.task_title || "—",
          suggested.source === "intent" ? "نیت" : suggested.source === "frame" ? "قاب" : "—",
          suggested.task_id != null ? String(suggested.task_id) : "پیشنهادی",
          suggested.created ? "جدید" : suggested.task_id != null ? "موجود" : "—",
          Array.isArray(suggested.analysis_ids) && suggested.analysis_ids.length
            ? suggested.analysis_ids.join("، ")
            : "—",
        ]]
      : [],
    ["عنوان", "منبع", "وظیفه", "وضعیت", "تحلیل"],
    $("pane-task"),
  );
  renderTable(
    scoring
      ? [[
          scoring.importance || "—",
          scoring.urgency || "—",
          scoring.severity || "—",
          impactLabels(scoring).join(" / ") || "—",
          scoring.status === "saved" ? "ثبت‌شده" : "پیشنهادی",
        ]]
      : [],
    ["اهمیت", "فوریت", "شدت", "اثر", "وضعیت"],
    $("pane-score"),
  );
  const linked = nerLinked(payload);
  renderTable(
    [
      ...topics.map((item) => [
        item.name || item.topic_name || "—",
        item.code || item.topic_code || "—",
        item.topic_id != null ? String(item.topic_id) : "—",
        "موضوع",
        linked && (item.topic_id != null || item.topic_code) ? "وصل‌شده" : "پیشنهادی",
      ]),
      ...entities.map((item) => [
        item.canonical_name || "—",
        item.type || item.entity_type || "—",
        item.entity_id != null ? String(item.entity_id) : "—",
        item.role_name || item.role || "—",
        linked && item.role_code ? "وصل‌شده" : linked ? "وصل‌شده" : "پیشنهادی",
      ]),
    ],
    ["نام", "کد / نوع", "شناسه", "نقش", "وضعیت"],
    $("pane-ner"),
  );
  renderTable(
    quotes.map((item) => [
      item.mode_name || item.mode,
      item.attributed_to || "—",
      item.quoted_text || "—",
      item.mention_text || "—",
      String(item.confidence),
    ]),
    ["شیوه", "گوینده", "متن نسبت‌داده‌شده", "شاهد نقل", "اطمینان"],
    $("pane-quotes"),
  );
  renderTable(
    payload.frame
      ? [[
          payload.frame.title,
          payload.frame.unit || "—",
          payload.frame.process_name || payload.frame.process || "—",
          payload.frame.scope_name || payload.frame.scope || "—",
          payload.frame.about || "—",
          String(payload.frame.confidence),
        ]]
      : [],
    ["عنوان", "واحد", "فرآیند", "محدوده", "درباره", "اطمینان"],
    $("pane-frame"),
  );
  renderTable(
    tracesOf(payload).map((item) => [
      TOOL_LABELS[item.name] || item.name,
      item.name,
      item.status || "—",
      formatMs(item.duration_ms),
      item.chain || "—",
      item.slowest_step ? `${item.slowest_step} ${formatMs(item.slowest_ms)}` : "—",
    ]),
    ["لایه", "ابزار", "وضعیت", "زمان", "مراحل", "کندترین"],
    $("pane-trace"),
  );
  $("pane-json").textContent = JSON.stringify(payload, null, 2);
}

let lastExtract = null;

function setSaveEnabled(enabled) {
  const button = $("btn-save");
  if (button) button.disabled = !enabled;
}

async function loadSample() {
  const data = await fetch("/api/sample").then((res) => res.json());
  $("text").value = data.text || "";
  $("sample-note").textContent = data.note || "";
  $("sample-note").classList.remove("hidden");
}

async function postExtract(path, text) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  let payload;
  try {
    payload = await response.json();
  } catch (err) {
    throw new Error("پاسخ استخراج خوانده نشد");
  }
  if (payload.status === "error") {
    throw new Error(payload.message || "استخراج شکست خورد");
  }
  return payload;
}

function joinMessages(left, right) {
  if (!left) return right || "";
  if (!right || left.includes(right)) return left;
  return `${left}؛ ${right}`;
}

function applyExtract(payload, text, pane) {
  lastExtract = {
    text: payload.normalized_text || text,
    payload: { ...payload, traces: tracesOf(payload) },
  };
  renderResult(lastExtract.payload, lastExtract.text);
  showPane(pane || "facts");
}

function mergeExtraLayer(name, part) {
  const current = lastExtract.payload;
  const next = { ...current };
  if (name === "quotes") {
    next.quotes = part.quotes || [];
    next.quote_count = part.quote_count || next.quotes.length;
    next.message = joinMessages(next.message, part.message);
  } else if (name === "frame") {
    next.frame = part.frame || null;
    next.message = joinMessages(next.message, part.message);
  } else if (name === "facts") {
    next.facts = part.facts || [];
    next.fact_count = part.fact_count || next.facts.length;
    next.explicitness = part.explicitness;
    next.explicitness_name = part.explicitness_name;
    next.dropped_count = part.dropped_count || 0;
    next.message = joinMessages(next.message, part.message);
  }
  lastExtract = { text: lastExtract.text, payload: next };
}

function extractErrorMessage(err) {
  const raw = err && err.message ? String(err.message) : "";
  if (err && err.name === "AbortError") return "زمان استخراج تمام شد";
  if (/Failed to fetch|NetworkError|network/i.test(raw)) {
    return "ارتباط با سرور قطع شد. اگر زمین بازی بسته است دوباره python -m playground را بزن.";
  }
  return raw || "استخراج شکست خورد";
}

async function extractAll(text) {
  lastExtract = null;
  const traces = [];
  $("status").textContent = "در حال استخراج فکت…";
  const facts = await postExtract("/api/extract/facts", text);
  traces.push(...tracesOf(facts));
  applyExtract({ ...facts, traces: [...traces] }, text, "facts");
  $("status").textContent = `${facts.message || "فکت آمد"}؛ بقیه لایه‌ها…`;
  const extras = [
    ["quotes", "/api/extract/quotes"],
    ["frame", "/api/extract/frame"],
  ];
  const settled = await Promise.allSettled(
    extras.map(([name, path]) => postExtract(path, text).then((part) => [name, part])),
  );
  const warnings = [];
  settled.forEach((item, index) => {
    if (item.status === "fulfilled") {
      traces.push(...tracesOf(item.value[1]));
      mergeExtraLayer(item.value[0], item.value[1]);
      return;
    }
    warnings.push(item.reason && item.reason.message ? item.reason.message : extras[index][0]);
  });
  applyExtract({ ...lastExtract.payload, traces: [...traces] }, lastExtract.text, "facts");
  const timing = traceSummary(traces);
  $("status").textContent = [lastExtract.payload.message || "انجام شد", timing]
    .filter(Boolean)
    .join(" · ");
  if (warnings.length) {
    $("error").textContent = `بعضی لایه‌ها نیامد: ${warnings.join("؛ ")}`;
    $("error").classList.remove("hidden");
  }
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
      ? "در حال استخراج فکت…"
      : "در حال استخراج… معمولاً ۲۰ تا ۴۰ ثانیه طول می‌کشد.";
  try {
    if (layer === "all") {
      await extractAll(text);
      return;
    }
    const payload = await postExtract(`/api/extract/${layer}`, text);
    const timing = traceSummary(tracesOf(payload));
    $("status").textContent = [payload.message || "انجام شد", timing].filter(Boolean).join(" · ");
    applyExtract(payload, text, layer);
  } catch (err) {
    $("error").textContent = extractErrorMessage(err);
    $("error").classList.remove("hidden");
    $("status").textContent = "";
  } finally {
    buttons.forEach((item) => {
      if (item.id === "btn-save") return;
      item.disabled = false;
    });
    setSaveEnabled(Boolean(lastExtract && lastExtract.payload && lastExtract.payload.frame));
  }
}

$("btn-sample").addEventListener("click", () => {
  loadSample().catch((err) => {
    $("error").textContent = err.message;
    $("error").classList.remove("hidden");
  });
});
$("btn-clear").addEventListener("click", () => {
  $("text").value = "";
  $("sample-note").classList.add("hidden");
  $("status").textContent = "";
  lastExtract = null;
  setSaveEnabled(false);
});
document.querySelectorAll(".run-row button[data-layer]").forEach((button) => {
  button.addEventListener("click", () => extract(button.dataset.layer));
});
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => showPane(tab.dataset.pane));
});

async function saveIssue() {
  if (!lastExtract || !lastExtract.payload || !lastExtract.payload.frame) return;
  $("error").classList.add("hidden");
  const button = $("btn-save");
  button.disabled = true;
  const pendingNer = nerPending(lastExtract.payload);
  $("status").textContent = pendingNer
    ? "در حال وصل موضوع و موجودیت پیشنهادی به مسئله…"
    : "در حال ذخیره مسئله، علت‌ها، وظیفه، امتیاز، فکت‌ها و نقل‌قول‌های تأییدشده…";
  try {
    const suggested = suggestedTaskOf(lastExtract.payload);
    const body = {
      text: lastExtract.text,
      source_type: "content",
      frame: lastExtract.payload.frame,
      causes: causesOf(lastExtract.payload).map((item) => ({
        title: item.name,
        mention_text: item.mention_text,
        cause_level: "cause",
      })),
      task: suggested
        ? { title: suggested.title || suggested.task_title }
        : undefined,
      intents: lastExtract.payload.intents,
      facts: (lastExtract.payload.facts || []).map((item) => ({
        fact_id: item.fact_id || item.id,
        kind: item.kind,
        name: item.name,
        value: item.value,
        unit: item.unit,
        role: item.role,
        grounding: item.grounding,
        derivation: item.derivation,
        effect: item.effect,
        previous: item.previous,
        current: item.current,
        mention_text: item.mention_text,
        start_offset: item.start_offset,
        end_offset: item.end_offset,
        evidence_texts: item.evidence_texts,
        source_ids: item.source_ids,
        confidence: item.confidence,
      })),
      quotes: (lastExtract.payload.quotes || []).map((item) => ({
        mode: item.mode,
        attributed_to: item.attributed_to,
        quoted_text: item.quoted_text,
        mention_text: item.mention_text,
        start_offset: item.start_offset,
        end_offset: item.end_offset,
        confidence: item.confidence,
      })),
      analysis_id: lastExtract.payload.analysis_id || undefined,
      model: lastExtract.payload.model || undefined,
    };
    if (pendingNer) {
      body.topics = (lastExtract.payload.suggested_topics || []).map((item) => ({
        topic_id: item.topic_id,
        code: item.code,
      }));
      body.entities = (lastExtract.payload.suggested_entities || []).map((item) => ({
        entity_id: item.entity_id,
        role: item.role,
      }));
    }
    const response = await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (payload.status === "error") {
      throw new Error(payload.message || "ذخیره شکست خورد");
    }
    const merged = {
      ...lastExtract.payload,
      ...payload,
      frame: lastExtract.payload.frame,
      facts: Array.isArray(payload.facts) && payload.facts.length
        ? payload.facts
        : lastExtract.payload.facts || [],
      quotes: Array.isArray(payload.quotes) && payload.quotes.length
        ? payload.quotes
        : lastExtract.payload.quotes || [],
      causes: payload.causes || [],
      task: payload.task || lastExtract.payload.suggested_task || null,
      suggested_task: lastExtract.payload.suggested_task || null,
      scoring: payload.scoring || lastExtract.payload.suggested_scoring || null,
      suggested_scoring: lastExtract.payload.suggested_scoring || null,
      suggested_topics: payload.suggested_topics || lastExtract.payload.suggested_topics || [],
      suggested_entities: payload.suggested_entities || lastExtract.payload.suggested_entities || [],
      topics: payload.topics || [],
      entities: payload.entities || [],
    };
    lastExtract = { text: lastExtract.text, payload: merged };
    $("status").textContent = [
      payload.message,
      payload.id != null ? `مسئله ${payload.id}` : "",
      payload.reused ? "مسئله موجود" : "",
      payload.analysis_id != null ? `تحلیل ${payload.analysis_id}` : "",
      Array.isArray(payload.facts) && payload.facts.length
        ? `${payload.facts.length} فکت`
        : "",
      Array.isArray(payload.quotes) && payload.quotes.length
        ? `${payload.quotes.length} نقل‌قول`
        : "",
      Array.isArray(payload.causes) && payload.causes.length
        ? `${payload.causes.length} علت`
        : "",
      payload.task && payload.task.task_id != null
        ? `وظیفه ${payload.task.task_id}`
        : "",
      payload.scoring && payload.scoring.importance
        ? `اهمیت ${payload.scoring.importance}`
        : "",
      (payload.suggested_topics || []).length || (payload.suggested_entities || []).length
        ? `${(payload.suggested_topics || []).length} موضوع · ${(payload.suggested_entities || []).length} موجودیت`
        : "",
    ]
      .filter(Boolean)
      .join(" · ");
    renderResult(merged, lastExtract.text);
    if (nerPending(merged)) {
      showPane("ner");
    }
    setSaveEnabled(nerPending(merged));
  } catch (err) {
    $("error").textContent = err.message;
    $("error").classList.remove("hidden");
    $("status").textContent = "";
    setSaveEnabled(true);
  }
}

$("btn-save").addEventListener("click", () => {
  saveIssue().catch((err) => {
    $("error").textContent = err.message;
    $("error").classList.remove("hidden");
    setSaveEnabled(true);
  });
});
