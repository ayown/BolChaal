// BolChaal — Frontend Logic

const API = "http://localhost:8000";
const MAX = 1000;
const HISTORY_KEY = "bolchaal_history";
const HISTORY_MAX = 25;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const srcSelect    = document.getElementById("src-lang-select");
const sourceText   = document.getElementById("source-text");
const outputText   = document.getElementById("output-text");
const translateBtn = document.getElementById("translate-btn");
const clearBtn     = document.getElementById("clear-btn");
const copyBtn      = document.getElementById("copy-btn");
const copyIcon     = document.getElementById("copy-icon");
const charCount    = document.getElementById("char-count");
const statusDot    = document.getElementById("status-dot");
const statusText   = document.getElementById("status-text");
const hinglishBadge = document.getElementById("hinglish-badge");
const errorBanner  = document.getElementById("error-banner");
const errorText    = document.getElementById("error-text");
const detectedLang    = document.getElementById("detected-lang");
const timeTaken       = document.getElementById("time-taken");
const btnIdle         = translateBtn.querySelector(".btn-idle");
const btnLoading      = translateBtn.querySelector(".btn-loading");
const historySection  = document.getElementById("history-section");
const historyList     = document.getElementById("history-list");
const historyCount    = document.getElementById("history-count");
const clearHistoryBtn = document.getElementById("clear-history-btn");

// ── State ─────────────────────────────────────────────────────────────────────
let busy = false;
let lastOutput = "";

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
    await Promise.all([checkHealth(), loadLanguages()]);
    renderHistory();
    sourceText.focus();
}

// ── Health ────────────────────────────────────────────────────────────────────
async function checkHealth() {
    try {
        const res = await fetch(`${API}/health`, { signal: AbortSignal.timeout(5000) });
        if (!res.ok) throw new Error();
        const data = await res.json();

        if (data.model_loaded) {
            setStatus("online", "Model ready");
        } else {
            setStatus("loading", "Loading model...");
            setTimeout(checkHealth, 5000);
        }
    } catch {
        setStatus("offline", "Backend offline");
        showError(
            "Cannot reach the backend. Start the server with: " +
            "cd backend && python main.py"
        );
    }
}

function setStatus(state, label) {
    statusDot.className = `status-dot ${state}`;
    statusText.textContent = label;
}

// ── Languages ─────────────────────────────────────────────────────────────────
async function loadLanguages() {
    try {
        const res = await fetch(`${API}/languages`);
        const data = await res.json();

        srcSelect.innerHTML = "";
        for (const lang of data.languages) {
            const opt = document.createElement("option");
            opt.value = lang.code;
            opt.textContent = lang.name;
            srcSelect.appendChild(opt);
        }
        srcSelect.value = "eng_Latn";
        onLangChange();
    } catch {
        srcSelect.innerHTML = `<option value="eng_Latn">English</option>`;
    }
}

function onLangChange() {
    if (srcSelect.value === "hinglish") {
        hinglishBadge.classList.remove("hidden");
        sourceText.placeholder = "Type Hinglish, e.g.: kaise ho? bahut accha laga.";
    } else {
        hinglishBadge.classList.add("hidden");
        sourceText.placeholder = "Type or paste your text here...";
    }
}

// ── Char counter ──────────────────────────────────────────────────────────────
function onInput() {
    const n = sourceText.value.length;
    charCount.textContent = `${n} / ${MAX}`;
    charCount.classList.remove("warn", "danger");
    if (n >= 950) charCount.classList.add("danger");
    else if (n >= 750) charCount.classList.add("warn");
}

// ── Clear ─────────────────────────────────────────────────────────────────────
function clearAll() {
    sourceText.value = "";
    onInput();
    outputText.innerHTML = `<span class="placeholder-text">Translation will appear here...</span>`;
    lastOutput = "";
    detectedLang.classList.add("hidden");
    timeTaken.classList.add("hidden");
    hideError();
    sourceText.focus();
}

// ── Translate ─────────────────────────────────────────────────────────────────
async function translate() {
    const text = sourceText.value.trim();
    if (!text || busy) return;

    const lang = srcSelect.value;
    if (!lang) return;

    hideError();
    setLoading(true);

    try {
        const res = await fetch(`${API}/translate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, src_lang: lang }),
            signal: AbortSignal.timeout(90000),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();
        lastOutput = data.translated_text;
        outputText.textContent = data.translated_text;

        saveToHistory({
            srcLangCode: lang,
            srcLangName: srcSelect.options[srcSelect.selectedIndex].text,
            source:      sourceText.value.trim(),
            translation: data.translated_text,
        });

        if (data.detected_as) {
            const label = data.detected_as === "hin_Deva" ? "Detected: Hindi" : "Detected: English";
            detectedLang.textContent = label;
            detectedLang.classList.remove("hidden");
        } else {
            detectedLang.classList.add("hidden");
        }

        timeTaken.textContent = `${data.time_taken_ms} ms`;
        timeTaken.classList.remove("hidden");

    } catch (e) {
        if (e.name === "TimeoutError") {
            showError("Timed out — the model may still be loading. Try again in a moment.");
        } else {
            showError(`Translation failed: ${e.message}`);
        }
        outputText.innerHTML = `<span class="placeholder-text">Translation will appear here...</span>`;
    } finally {
        setLoading(false);
    }
}

function setLoading(state) {
    busy = state;
    translateBtn.disabled = state;

    if (state) {
        btnIdle.classList.add("hidden");
        btnLoading.classList.remove("hidden");
        outputText.classList.add("is-translating");
        outputText.innerHTML = `<span class="placeholder-text">Translating...</span>`;
        lastOutput = "";
        detectedLang.classList.add("hidden");
        timeTaken.classList.add("hidden");
    } else {
        btnIdle.classList.remove("hidden");
        btnLoading.classList.add("hidden");
        outputText.classList.remove("is-translating");
    }
}

// ── Copy ──────────────────────────────────────────────────────────────────────
async function copyOutput() {
    if (!lastOutput) return;
    try {
        await navigator.clipboard.writeText(lastOutput);
        copyBtn.classList.add("success");
        copyIcon.innerHTML = `<polyline points="20 6 9 17 4 12"/>`;
        copyIcon.setAttribute("xmlns", "http://www.w3.org/2000/svg");

        setTimeout(() => {
            copyBtn.classList.remove("success");
            copyIcon.innerHTML = `
                <rect x="9" y="9" width="13" height="13" rx="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
            `;
        }, 2000);
    } catch {
        showError("Could not copy — try selecting the text manually.");
    }
}

// ── Error ─────────────────────────────────────────────────────────────────────
function showError(msg) {
    errorText.textContent = msg;
    errorBanner.classList.remove("hidden");
}

function hideError() {
    errorBanner.classList.add("hidden");
}

// ── Events ────────────────────────────────────────────────────────────────────
srcSelect.addEventListener("change", onLangChange);
sourceText.addEventListener("input", onInput);
clearBtn.addEventListener("click", clearAll);
copyBtn.addEventListener("click", copyOutput);
translateBtn.addEventListener("click", translate);

document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") translate();
});

clearHistoryBtn.addEventListener("click", clearHistory);

// ── History ───────────────────────────────────────────────────────────────────
function getHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    } catch {
        return [];
    }
}

function saveToHistory({ srcLangCode, srcLangName, source, translation }) {
    const history = getHistory();
    history.unshift({
        id:          Date.now().toString(),
        srcLangCode,
        srcLangName,
        source,
        translation,
        timestamp:   Date.now(),
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, HISTORY_MAX)));
    renderHistory();
}

function deleteHistoryItem(id) {
    const updated = getHistory().filter(item => item.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    renderHistory();
}

function clearHistory() {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
}

function restoreHistoryItem(item) {
    sourceText.value = item.source;
    onInput();

    // Restore dropdown — fall back to English if the saved code isn't in the list
    const opt = [...srcSelect.options].find(o => o.value === item.srcLangCode);
    srcSelect.value = opt ? item.srcLangCode : "eng_Latn";
    onLangChange();

    lastOutput = item.translation;
    outputText.textContent = item.translation;
    detectedLang.classList.add("hidden");
    timeTaken.classList.add("hidden");
    hideError();

    // Scroll to translator smoothly
    document.getElementById("translator").scrollIntoView({ behavior: "smooth", block: "start" });
}

function timeAgo(timestamp) {
    const diff = Math.floor((Date.now() - timestamp) / 1000);
    if (diff < 60)        return "just now";
    if (diff < 3600)      return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400)     return `${Math.floor(diff / 3600)}h ago`;
    return new Date(timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function renderHistory() {
    const history = getHistory();

    if (history.length === 0) {
        historySection.classList.add("hidden");
        return;
    }

    historySection.classList.remove("hidden");
    historyCount.textContent = history.length;

    historyList.innerHTML = "";

    for (const item of history) {
        const el = document.createElement("div");
        el.className = "history-item";
        el.dataset.id = item.id;
        el.innerHTML = `
            <div class="history-body">
                <div class="history-meta">
                    <span class="history-lang">${escHtml(item.srcLangName)}</span>
                    <span class="history-time">${timeAgo(item.timestamp)}</span>
                </div>
                <div class="history-source">${escHtml(truncate(item.source, 80))}</div>
                <div class="history-divider">↓</div>
                <div class="history-translation">${escHtml(truncate(item.translation, 80))}</div>
            </div>
            <button class="history-delete-btn" title="Remove" aria-label="Remove from history">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        `;

        // Restore on item click
        el.addEventListener("click", () => restoreHistoryItem(item));

        // Delete on button click (stop propagation so restore doesn't also fire)
        el.querySelector(".history-delete-btn").addEventListener("click", (e) => {
            e.stopPropagation();
            el.style.opacity = "0";
            el.style.transform = "translateX(8px)";
            el.style.transition = "opacity 0.18s ease, transform 0.18s ease";
            setTimeout(() => deleteHistoryItem(item.id), 180);
        });

        historyList.appendChild(el);
    }
}

function truncate(str, max) {
    return str.length <= max ? str : str.slice(0, max) + "…";
}

function escHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ── Start ─────────────────────────────────────────────────────────────────────
init();
