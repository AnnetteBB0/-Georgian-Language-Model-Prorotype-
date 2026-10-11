// Configuration
const API_URL = window.CGC_API_URL || "http://127.0.0.1:8000";
const AUTO_CHECK_DEBOUNCE_MS = 1200;

// DOM element references
const inputText = document.getElementById("input-text");
const overlay = document.getElementById("overlay");
const checkButton = document.getElementById("check-button");
const checkSpelling = document.getElementById("check-spelling");
const checkGrammar = document.getElementById("check-grammar");
const checkStyle = document.getElementById("check-style");
const autoCheck = document.getElementById("auto-check");
const toggleRulesButton = document.getElementById("toggle-rules");
const statusEl = document.getElementById("status");
const issuesEl = document.getElementById("issues");
const statsEl = document.getElementById("stats");
const engineEl = document.getElementById("engine");
const engineLabel = document.getElementById("engine-label");
const enginePlugins = document.getElementById("engine-plugins");
const rulesTableBody = document.querySelector("#rules-table tbody");

// State
let latestAnnotations = [];
let debounceTimer = null;
let currentRequestId = 0;
let engineStatusLoaded = false;

// =============================================================================
// Utility Functions
// =============================================================================

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderOverlay(text, annotations) {
  if (!text) {
    overlay.innerHTML = "";
    return;
  }

  const sorted = [...annotations].sort((left, right) => left.start - right.start);
  let html = "";
  let cursor = 0;

  for (const annotation of sorted) {
    if (annotation.start < cursor || annotation.end <= annotation.start) {
      continue;
    }

    html += escapeHtml(text.slice(cursor, annotation.start));
    const marked = escapeHtml(text.slice(annotation.start, annotation.end));
    const title = annotation.short_message
      ? `${annotation.short_message} — ${annotation.message}`
      : annotation.message;
    html += `<span class="mark ${annotation.type}" title="${escapeHtml(
      title
    )}" data-rule="${escapeHtml(annotation.rule_id || "")}">${marked}</span>`;
    cursor = annotation.end;
  }

  html += escapeHtml(text.slice(cursor));
  overlay.innerHTML = html;
}

// =============================================================================
// Source Badge Helpers
// =============================================================================

function sourceToBadgeClass(source) {
  if (!source) return "source-unknown";
  if (source.startsWith("builtin-core")) return "source-builtin";
  if (source.startsWith("stanza")) return "source-stanza";
  if (source.startsWith("Rules/")) return "source-rules";
  if (source.startsWith("grammar2")) return "source-grammar2";
  if (source.startsWith("georgian_grammar") || source === "desktop-georgian-grammar-rules")
    return "source-desktop";
  if (source === "rules1.json (Verbal System)" || source === "verbal_system_checker.py" || source.startsWith("verbal_system"))
    return "source-verbal";
  if (source === "gr.json" || source.startsWith("gr.json")) return "source-gr";
  if (source.includes("grammar2")) return "source-grammar2";
  if (source === "alignment-checker") return "source-rules";
  return "source-unknown";
}

function sourceToShortLabel(source) {
  if (!source) return "unknown";
  if (source === "builtin-core") return "Core";
  if (source === "stanza-optional") return "Stanza";
  if (source === "Rules/alignment_checker.py") return "Rules";
  if (source === "grammar2/Agreement rules.py" || source === "grammar2-agreement")
    return "G2";
  if (
    source === "georgian_grammar/georgian_grammar_rules.py" ||
    source === "desktop-georgian-grammar-rules"
  )
    return "Desktop";
  if (source === "rules1.json (Verbal System)") return "Verbal";
  if (source === "verbal_system_checker.py") return "Verbal";
  if (source === "gr.json") return "GR";
  if (source.startsWith("grammar2") || source.includes("grammar2")) return "G2";
  if (source.startsWith("georgian_grammar")) return "Desktop";
  if (source.startsWith("verbal_system")) return "Verbal";
  if (source.startsWith("gr.json")) return "GR";
  return source.slice(0, 14);
}

// =============================================================================
// Rendering Functions
// =============================================================================

function renderIssues(annotations) {
  issuesEl.innerHTML = "";

  if (!annotations.length) {
    issuesEl.innerHTML =
      '<p class="empty-state">No issues found — looks good!</p>';
    return;
  }

  const counts = { spelling: 0, grammar: 0, style: 0 };
  annotations.forEach((a) => {
    if (counts[a.type] !== undefined) counts[a.type]++;
  });

  annotations.forEach((annotation, index) => {
    const card = document.createElement("article");
    card.className = "issue";
    card.dataset.index = index;
    card.dataset.rule = annotation.rule_id || "";

    const header = document.createElement("div");
    header.className = "issue-header";

    const type = document.createElement("span");
    type.className = `issue-type ${annotation.type}`;
    type.textContent = annotation.type;

    const wordAndSource = document.createElement("div");
    wordAndSource.className = "issue-right";

    const word = document.createElement("span");
    word.className = "issue-word";
    word.textContent = annotation.word || textSlice(annotation);

    const source = document.createElement("span");
    source.className = `source ${sourceToBadgeClass(annotation.source)}`;
    source.title = `Source plugin: ${annotation.source || "unknown"} · Rule: ${
      annotation.rule_id || "n/a"
    }`;
    source.textContent = `${sourceToShortLabel(annotation.source)} · ${
      annotation.rule_id ? annotation.rule_id.split(":").pop() : "—"
    }`;

    wordAndSource.append(word, source);

    header.append(type, wordAndSource);

    const message = document.createElement("p");
    message.className = "issue-message";
    message.textContent = annotation.message;

    card.append(header, message);

    if (annotation.replacements?.length) {
      const replacements = document.createElement("div");
      replacements.className = "issue-replacements";

      annotation.replacements.forEach((replacement) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "replacement";
        button.textContent = replacement;
        button.addEventListener("click", () =>
          applyReplacement(index, replacement)
        );
        replacements.append(button);
      });

      card.append(replacements);
    }

    issuesEl.append(card);
  });
}

function renderStats(meta) {
  if (!meta) {
    statsEl.innerHTML = "";
    return;
  }

  const statItems = [
    { label: "Words", value: meta.word_count ?? "—" },
    { label: "Unique words", value: meta.unique_word_count ?? "—" },
    { label: "Sentences", value: meta.sentence_count ?? "—" },
    {
      label: "Avg word (chars)",
      value: meta.avg_word_length_chars ?? "—",
    },
    {
      label: "Avg sentence",
      value: meta.avg_sentence_length_words
        ? `${meta.avg_sentence_length_words} w`
        : "—",
    },
    {
      label: "Lexical diversity",
      value:
        meta.lexical_diversity !== undefined && meta.lexical_diversity !== null
          ? Math.round(meta.lexical_diversity * 100) + "%"
          : "—",
    },
  ];

  if (meta.active_rule_ids?.length) {
    statItems.push({
      label: "Active rules",
      value: meta.active_rule_ids.length,
    });
  }

  statsEl.innerHTML = statItems
    .map(
      (s) => `
      <div class="stat-card">
        <div class="stat-label">${s.label}</div>
        <div class="stat-value">${s.value}</div>
      </div>
    `
    )
    .join("");
}

function renderEngine(meta, pluginsPayload) {
  engineLabel.textContent = `Engine: ${
    meta?.grammar_engine || "rules+optional-stanza+gr.json"
  }`;

  if (pluginsPayload) {
    const plugins = Object.entries(pluginsPayload).map(([name, info]) => {
      const extraMeta = info.meta
        ? Object.entries(info.meta)
            .map(([k, v]) => `${k}=${v}`)
            .join(", ")
        : "";
      const statusClass = info.available ? "ok" : "fail";
      const statusText = info.available ? "loaded" : "unavailable";
      const err = info.loading_error
        ? `<span class="plugin-err" title="${escapeHtml(info.loading_error)}">· error</span>`
        : "";
      return `
        <div class="plugin ${statusClass}">
          <div class="plugin-name">
            <span>${escapeHtml(name)}</span>
            <span class="plugin-status">${statusText} ${err}</span>
          </div>
          <div class="plugin-meta">
            <strong>${info.rule_count ?? 0}</strong> rules
            ${extraMeta ? `<span class="plugin-stats">${escapeHtml(extraMeta)}</span>` : ""}
          </div>
        </div>`;
    });
    enginePlugins.innerHTML = plugins.join("");
  } else {
    // Fallback: render plugin counts from the meta returned by /v1/check
    const fromMeta = [];
    if (meta?.alignment_lexicon_size !== undefined) {
      fromMeta.push(
        `<div class="plugin ok"><div class="plugin-name"><span>Rules/alignment_checker.py</span><span class="plugin-status">loaded</span></div><div class="plugin-meta"><strong>${meta.alignment_lexicon_size}</strong> alignment lexicon entries</div></div>`
      );
    }
    if (meta?.grammar2_postposition_count !== undefined) {
      fromMeta.push(
        `<div class="plugin ok"><div class="plugin-name"><span>grammar2/Agreement rules.py</span><span class="plugin-status">loaded</span></div><div class="plugin-meta"><strong>${
          meta.grammar2_postposition_count +
          meta.grammar2_confusable_count +
          meta.grammar2_proper_noun_count +
          meta.grammar2_double_negative_patterns
        }</strong> rule data sources</div></div>`
      );
    }
    if (meta?.desktop_postposition_count !== undefined) {
      fromMeta.push(
        `<div class="plugin ok"><div class="plugin-name"><span>georgian_grammar/georgian_grammar_rules.py</span><span class="plugin-status">loaded</span></div><div class="plugin-meta"><strong>${
          (meta.desktop_postposition_count || 0) +
          (meta.desktop_adjective_paradigms || 0) +
          (meta.desktop_possessive_paradigms || 0)
        }</strong> paradigms</div></div>`
      );
    }
    if (meta?.stanza_used) {
      fromMeta.push(
        `<div class="plugin ok"><div class="plugin-name"><span>stanza-optional</span><span class="plugin-status">loaded</span></div><div class="plugin-meta">Morphological tagger was used</div></div>`
      );
    }
    if (meta?.gr_preverb_count !== undefined) {
      fromMeta.push(
        `<div class="plugin ok"><div class="plugin-name"><span>gr.json</span><span class="plugin-status">loaded</span></div><div class="plugin-meta"><strong>${
          (meta.gr_preverb_count || 0) +
          (meta.gr_interrogative_count || 0) +
          (meta.gr_thematic_suffix_count || 0) +
          (meta.gr_negation_particle_count || 0)
        }</strong> rule data sources</div></div>`
      );
    }
    enginePlugins.innerHTML = fromMeta.join("");
  }
}

function renderRulesTable(rules) {
  rulesTableBody.innerHTML = rules
    .map(
      (r) => `
      <tr>
        <td><code>${escapeHtml(r.rule_id)}</code></td>
        <td><span class="mini-type ${escapeHtml(r.type)}">${escapeHtml(
          r.type
        )}</span></td>
        <td class="source ${sourceToBadgeClass(r.source)}">${escapeHtml(
          r.source
        )}</td>
        <td>${escapeHtml(r.short_name)} — ${escapeHtml(r.description)}</td>
      </tr>`
    )
    .join("");
}

// =============================================================================
// API Interaction
// =============================================================================

async function ensureEngineData() {
  if (engineStatusLoaded) return;
  try {
    const [engResp, rulesResp] = await Promise.all([
      fetch(`${API_URL}/v1/engine`).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API_URL}/v1/rules`).then((r) => (r.ok ? r.json() : null)),
    ]);
    if (engResp) {
      renderEngine(engResp, engResp.plugins);
    }
    if (rulesResp?.rules) {
      renderRulesTable(rulesResp.rules);
    }
    engineStatusLoaded = true;
  } catch {
    // Rules/engine data is informational; don't block check functionality
  }
}

// =============================================================================
// Text Manipulation
// =============================================================================

function textSlice(annotation) {
  return inputText.value.slice(annotation.start, annotation.end);
}

function applyReplacement(annotationIndex, replacement) {
  const annotation = latestAnnotations[annotationIndex];
  if (!annotation) {
    return;
  }

  const text = inputText.value;
  inputText.value =
    text.slice(0, annotation.start) + replacement + text.slice(annotation.end);

  latestAnnotations = latestAnnotations
    .map((a, i) => {
      if (i === annotationIndex) return null;
      const diff = replacement.length - (annotation.end - annotation.start);
      if (a.start >= annotation.end) {
        return { ...a, start: a.start + diff, end: a.end + diff };
      }
      if (a.end <= annotation.start) return a;
      return null;
    })
    .filter(Boolean);

  renderOverlay(inputText.value, latestAnnotations);
  renderIssues(latestAnnotations);
}

// =============================================================================
// Auto-Check Scheduling
// =============================================================================

function scheduleAutoCheck() {
  if (!autoCheck.checked) return;
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(checkText, AUTO_CHECK_DEBOUNCE_MS);
}

// =============================================================================
// Main Check Function
// =============================================================================

async function checkText() {
  const text = inputText.value;
  if (!text.trim()) {
    statusEl.textContent = "Enter some text to check.";
    latestAnnotations = [];
    renderOverlay(text, latestAnnotations);
    renderIssues(latestAnnotations);
    statsEl.innerHTML = "";
    return;
  }

  const requestId = ++currentRequestId;
  checkButton.disabled = true;
  statusEl.textContent = "Checking…";
  ensureEngineData();

  try {
    const response = await fetch(`${API_URL}/v1/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        options: {
          check_spelling: checkSpelling.checked,
          check_grammar: checkGrammar.checked,
          check_style: checkStyle.checked,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Request failed (${response.status})`);
    }

    const payload = await response.json();

    if (requestId !== currentRequestId) return;

    latestAnnotations = payload.annotations || [];
    renderOverlay(text, latestAnnotations);
    renderIssues(latestAnnotations);
    renderStats(payload.meta);
    renderEngine(payload.meta, null);

    const byType = { spelling: 0, grammar: 0, style: 0 };
    latestAnnotations.forEach((a) => {
      if (byType[a.type] !== undefined) byType[a.type]++;
    });
    const issueCount = latestAnnotations.length;
    const spellMs = payload.meta?.spell_ms ?? 0;
    const grammarMs = payload.meta?.grammar_ms ?? 0;
    const breakdown =
      issueCount > 0
        ? ` (${Object.entries(byType)
            .filter(([, v]) => v > 0)
            .map(([k, v]) => `${v} ${k}`)
            .join(", ")})`
        : "";
    statusEl.textContent =
      issueCount === 0
        ? `No issues found (${spellMs + grammarMs} ms).`
        : `${issueCount} issue${issueCount === 1 ? "" : "s"} found${breakdown} (${
            spellMs + grammarMs
          } ms).`;
  } catch (error) {
    if (requestId !== currentRequestId) return;
    statusEl.textContent =
      error.message || "Could not reach the checker API.";
    latestAnnotations = [];
    renderOverlay(text, latestAnnotations);
    renderIssues(latestAnnotations);
  } finally {
    if (requestId === currentRequestId) {
      checkButton.disabled = false;
    }
  }
}

// =============================================================================
// Event Listeners
// =============================================================================

toggleRulesButton.addEventListener("click", async () => {
  const willShow = engineEl.hidden;
  engineEl.hidden = !willShow;
  toggleRulesButton.classList.toggle("active", willShow);
  if (willShow) {
    await ensureEngineData();
  }
});

inputText.addEventListener("input", () => {
  renderOverlay(inputText.value, latestAnnotations);
  scheduleAutoCheck();
});

inputText.addEventListener("scroll", () => {
  overlay.scrollTop = inputText.scrollTop;
  overlay.scrollLeft = inputText.scrollLeft;
});

inputText.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    checkText();
  }
});

checkButton.addEventListener("click", checkText);
renderOverlay(inputText.value, latestAnnotations);
