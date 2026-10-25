const FIRST = 0x3d000;
const LAST = 0x3fc3f;
const $ = (id) => document.getElementById(id);
const label = (cp) => `U+${cp.toString(16).toUpperCase()}`;
const format = new Intl.NumberFormat("en-US");
const ui = Object.fromEntries([
  "coverageSummary", "coveredCount", "repertoireCount", "coveragePercent", "missingCount", "coverageEdition", "coverageMeter",
  "atlasSearch", "searchInput", "resetFilters", "rangeSelect", "coverageFilter", "atlasWeight", "atlasWeightValue", "glyphSize", "glyphSizeValue",
  "rangeMap", "rangeSummary", "resultsStatus", "pageSize", "atlasFontStatus", "characterGrid", "emptyState", "firstPage", "previousPage", "nextPage", "lastPage",
  "pageForm", "pageNumber", "pageCount", "glyphDialog", "dialogCoverage", "dialogGlyph", "dialogTitle", "dialogCode", "dialogModern", "copyGlyph", "svgSource", "unicodeInfo", "copyStatus",
].map((id) => [id, $(id)]));
const modernBySeal = new Map();
const sealByModern = new Map();
let coverage;
let included = new Set();
let allCharacters = [];
let matches = [];
let page = 1;
let pages = 1;
let selectedCodepoint;
let debounce;
let copyTimer;
let fontRequest = 0;
let navigationTimer;

function integer(value, fallback, min, max) {
  const number = Number(value);
  return Number.isInteger(number) && number >= min && number <= max ? number : fallback;
}

function readState() {
  clearTimeout(debounce);
  const params = new URLSearchParams(location.hash.slice(1));
  ui.searchInput.value = (params.get("q") ?? "").slice(0, 80);
  const range = params.get("range") ?? "all";
  ui.rangeSelect.value = Array.from(ui.rangeSelect.options).some((option) => option.value === range) ? range : "all";
  ui.coverageFilter.value = ["all", "included", "missing"].includes(params.get("coverage")) ? params.get("coverage") : "all";
  ui.pageSize.value = ["64", "128", "256"].includes(params.get("perPage")) ? params.get("perPage") : "128";
  ui.atlasWeight.value = String(integer(params.get("weight"), 400, 300, 700));
  ui.glyphSize.value = String(integer(params.get("size"), 64, 40, 104));
  page = integer(params.get("page"), 1, 1, 11328);
  setAppearance();
}

function writeState(replace = false) {
  const params = new URLSearchParams();
  if (ui.searchInput.value.trim()) params.set("q", ui.searchInput.value.trim());
  if (ui.rangeSelect.value !== "all") params.set("range", ui.rangeSelect.value);
  if (ui.coverageFilter.value !== "all") params.set("coverage", ui.coverageFilter.value);
  if (ui.pageSize.value !== "128") params.set("perPage", ui.pageSize.value);
  if (ui.atlasWeight.value !== "400") params.set("weight", ui.atlasWeight.value);
  if (ui.glyphSize.value !== "64") params.set("size", ui.glyphSize.value);
  if (page !== 1) params.set("page", String(page));
  const next = location.pathname + location.search + (params.size ? `#${params}` : "");
  if (next !== location.pathname + location.search + location.hash) history[replace ? "replaceState" : "pushState"](null, "", next);
}

function setAppearance() {
  document.documentElement.style.setProperty("--weight", ui.atlasWeight.value);
  document.documentElement.style.setProperty("--atlas-size", `${ui.glyphSize.value}px`);
  ui.atlasWeightValue.value = ui.atlasWeight.value;
  ui.glyphSizeValue.value = `${ui.glyphSize.value} px`;
}

function codepointsForQuery(query) {
  if (!query) return null;
  const range = /^(?:U\+|0x)?([0-9a-f]{4,6})\s*[-–]\s*(?:U\+|0x)?([0-9a-f]{4,6})$/i.exec(query);
  if (range) {
    const a = parseInt(range[1], 16);
    const b = parseInt(range[2], 16);
    return new Set(allCharacters.filter((cp) => cp >= Math.min(a, b) && cp <= Math.max(a, b)));
  }
  const result = new Set();
  for (const token of query.split(/[\s,，;；]+/u).filter(Boolean)) {
    const code = /^(?:U\+|0x)?([0-9a-f]{4,6})$/i.exec(token);
    const characters = code ? (parseInt(code[1], 16) <= 0x10ffff ? [String.fromCodePoint(parseInt(code[1], 16))] : []) : Array.from(token);
    for (const character of characters) {
      const cp = character.codePointAt(0);
      if (cp >= FIRST && cp <= LAST) result.add(cp);
      for (const seal of sealByModern.get(cp) ?? []) result.add(seal);
    }
  }
  return result;
}

function applyFilters() {
  const query = codepointsForQuery(ui.searchInput.value.trim());
  const range = ui.rangeSelect.value === "all" ? null : coverage.chunks.find((chunk) => chunk.first.toString(16) === ui.rangeSelect.value);
  matches = allCharacters.filter((cp) => (!query || query.has(cp)) && (!range || (cp >= range.first && cp <= range.last)) &&
    (ui.coverageFilter.value === "all" || included.has(cp) === (ui.coverageFilter.value === "included")));
  pages = Math.max(1, Math.ceil(matches.length / Number(ui.pageSize.value)));
  page = Math.min(page, pages);
  renderPage();
}

async function checkFonts(characters) {
  const request = ++fontRequest;
  if (!characters || !document.fonts?.load) {
    ui.atlasFontStatus.textContent = "";
    return;
  }
  ui.atlasFontStatus.textContent = "Loading this page’s glyphs…";
  ui.atlasFontStatus.dataset.state = "loading";
  try {
    const faces = await document.fonts.load(`${ui.atlasWeight.value} 32px Seal`, characters);
    if (!faces.length) throw new Error("No matching font face");
    if (request !== fontRequest) return;
    ui.atlasFontStatus.textContent = "Sealie is ready · Select a character for details and copying.";
    ui.atlasFontStatus.dataset.state = "ready";
  } catch {
    if (request !== fontRequest) return;
    ui.atlasFontStatus.textContent = "These glyphs could not load. Reload the page to try again.";
    ui.atlasFontStatus.dataset.state = "error";
  }
}

function renderPage() {
  const start = (page - 1) * Number(ui.pageSize.value);
  const visible = matches.slice(start, start + Number(ui.pageSize.value));
  const fragment = document.createDocumentFragment();
  let fontText = "";
  for (const cp of visible) {
    const supported = included.has(cp);
    const modern = modernBySeal.get(cp);
    const card = document.createElement("button");
    card.type = "button";
    card.className = `atlas-card ${supported ? "is-included" : "is-missing"}`;
    card.dataset.codepoint = cp.toString(16).toUpperCase();
    card.setAttribute("aria-label", `${label(cp)}${modern ? `, modern equivalent ${String.fromCodePoint(modern)}` : ""}, ${supported ? "included" : "missing"}. Show details.`);
    const glyph = document.createElement("span");
    glyph.className = "atlas-glyph seal-font";
    glyph.setAttribute("aria-hidden", "true");
    glyph.textContent = supported ? String.fromCodePoint(cp) : "—";
    const code = document.createElement("span");
    code.className = "atlas-code";
    code.textContent = label(cp);
    const caption = document.createElement("span");
    caption.className = modern > 0xffff ? "atlas-modern is-code" : "atlas-modern";
    caption.textContent = modern ? (modern > 0xffff ? label(modern) : String.fromCodePoint(modern)) : "·";
    const status = document.createElement("span");
    status.className = supported ? "included-dot" : "missing-dot";
    status.setAttribute("aria-hidden", "true");
    card.append(status, glyph, code, caption);
    card.addEventListener("click", () => openCharacter(cp));
    fragment.append(card);
    if (supported) fontText += String.fromCodePoint(cp);
  }
  ui.characterGrid.replaceChildren(fragment);
  ui.characterGrid.setAttribute("aria-busy", "false");
  ui.emptyState.hidden = visible.length > 0;
  ui.emptyState.textContent = ui.coverageFilter.value === "missing" && !coverage.missing_count
    ? "No missing characters. Sealie covers every character in this Small Seal repertoire."
    : "No matching characters. Try a modern Chinese character, a Small Seal character, or a codepoint such as U+3D55D.";
  ui.resultsStatus.textContent = visible.length ? `${format.format(start + 1)}–${format.format(start + visible.length)} of ${format.format(matches.length)} characters` : "0 matching characters";
  ui.pageNumber.value = String(page);
  ui.pageNumber.max = String(pages);
  ui.pageCount.textContent = `of ${format.format(pages)}`;
  ui.firstPage.disabled = ui.previousPage.disabled = page <= 1;
  ui.lastPage.disabled = ui.nextPage.disabled = page >= pages;
  for (const tile of ui.rangeMap.children) tile.setAttribute("aria-pressed", String(tile.dataset.range === ui.rangeSelect.value));
  checkFonts(fontText);
}

function openCharacter(cp) {
  selectedCodepoint = cp;
  clearTimeout(copyTimer);
  const supported = included.has(cp);
  const modern = modernBySeal.get(cp);
  ui.dialogGlyph.textContent = supported ? String.fromCodePoint(cp) : "—";
  ui.dialogTitle.textContent = label(cp);
  ui.dialogCode.textContent = `${label(cp)} · decimal ${cp}`;
  ui.dialogModern.textContent = modern ? `${modern <= 0xffff ? String.fromCodePoint(modern) + " · " : ""}${label(modern)}` : "No modern equivalent listed";
  ui.dialogCoverage.textContent = supported ? "Included in Sealie" : "Missing from Sealie";
  ui.copyGlyph.disabled = !supported;
  ui.copyGlyph.textContent = "Copy character";
  ui.copyStatus.textContent = "";
  ui.svgSource.href = `https://github.com/iebb/sealie/blob/main/svg/U${cp.toString(16).toUpperCase()}.svg`;
  ui.svgSource.hidden = !supported;
  ui.unicodeInfo.href = `https://util.unicode.org/UnicodeJsps/character.jsp?a=${cp.toString(16).toUpperCase()}`;
  ui.glyphDialog.showModal();
}

async function copyCharacter() {
  const text = String.fromCodePoint(selectedCodepoint);
  try {
    if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
    await navigator.clipboard.writeText(text);
  } catch {
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("aria-label", "Small Seal character to copy");
    ui.glyphDialog.append(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    ui.copyGlyph.focus();
    if (!copied) {
      ui.copyStatus.textContent = `Copy this character: ${text}`;
      return;
    }
  }
  ui.copyGlyph.textContent = "Copied";
  ui.copyStatus.textContent = `Copied Small Seal ${label(selectedCodepoint)}.`;
  copyTimer = setTimeout(() => { ui.copyGlyph.textContent = "Copy character"; }, 1800);
}

function changeFilters(replace = false) {
  if (!coverage) return;
  page = 1;
  applyFilters();
  writeState(replace);
}

function goToPage(target) {
  if (!coverage) return;
  page = Math.max(1, Math.min(pages, target));
  renderPage();
  writeState();
  ui.resultsStatus.scrollIntoView({ block: "start", behavior: "auto" });
}

ui.atlasSearch.addEventListener("submit", (event) => { event.preventDefault(); clearTimeout(debounce); changeFilters(); });
ui.searchInput.addEventListener("input", () => { clearTimeout(debounce); debounce = setTimeout(() => changeFilters(true), 180); });
for (const control of [ui.rangeSelect, ui.coverageFilter, ui.pageSize]) control.addEventListener("change", () => changeFilters());
ui.resetFilters.addEventListener("click", () => { clearTimeout(debounce); ui.searchInput.value = ""; ui.rangeSelect.value = "all"; ui.coverageFilter.value = "all"; changeFilters(); });
ui.atlasWeight.addEventListener("input", () => { setAppearance(); writeState(true); });
ui.glyphSize.addEventListener("input", () => { setAppearance(); writeState(true); });
ui.firstPage.addEventListener("click", () => goToPage(1));
ui.previousPage.addEventListener("click", () => goToPage(page - 1));
ui.nextPage.addEventListener("click", () => goToPage(page + 1));
ui.lastPage.addEventListener("click", () => goToPage(pages));
ui.pageForm.addEventListener("submit", (event) => { event.preventDefault(); goToPage(integer(ui.pageNumber.value, page, 1, pages)); });
ui.copyGlyph.addEventListener("click", copyCharacter);
ui.glyphDialog.addEventListener("click", (event) => { if (event.target === ui.glyphDialog) { const rect = ui.glyphDialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) ui.glyphDialog.close(); } });
function restoreNavigation() {
  clearTimeout(navigationTimer);
  navigationTimer = setTimeout(() => { if (coverage) { readState(); applyFilters(); } }, 0);
}
window.addEventListener("popstate", restoreNavigation);
window.addEventListener("hashchange", restoreNavigation);

async function initialize() {
  try {
    const [coverageResponse, mapResponse] = await Promise.all([
      fetch(new URL("coverage.json", import.meta.url)),
      fetch(new URL("character-map.json", import.meta.url)),
    ]);
    if (!coverageResponse.ok || !mapResponse.ok) throw new Error("Character data could not load");
    const [data, mapping] = await Promise.all([coverageResponse.json(), mapResponse.json()]);
    if (data.schema_version !== 1 || data.first !== FIRST || data.last !== LAST || !Array.isArray(data.supported_ranges) || !Array.isArray(data.chunks) || !Array.isArray(mapping.entries)) throw new Error("Unexpected coverage data");
    for (const [first, last] of data.supported_ranges) {
      if (!Number.isInteger(first) || !Number.isInteger(last) || first < FIRST || last > LAST || first > last) throw new Error("Invalid coverage range");
      for (let cp = first; cp <= last; cp++) included.add(cp);
    }
    if (included.size !== data.glyph_count || data.repertoire_count !== LAST - FIRST + 1 || data.missing_count !== data.repertoire_count - included.size) throw new Error("Coverage counts do not match");
    for (const [seal, modern] of mapping.entries) {
      if (!Number.isInteger(seal) || seal < FIRST || seal > LAST || !Number.isInteger(modern) || modern < 0 || modern > 0x10ffff || (modern >= 0xd800 && modern <= 0xdfff)) throw new Error("Invalid character mapping");
      if (!modern) continue;
      modernBySeal.set(seal, modern);
      const equivalents = sealByModern.get(modern) ?? [];
      equivalents.push(seal);
      sealByModern.set(modern, equivalents);
    }
    coverage = data;
    allCharacters = Array.from({ length: LAST - FIRST + 1 }, (_, index) => FIRST + index);
    ui.coveredCount.textContent = format.format(data.glyph_count);
    ui.repertoireCount.textContent = `/ ${format.format(data.repertoire_count)}`;
    const percent = data.glyph_count / data.repertoire_count * 100;
    ui.coveragePercent.textContent = `${Number(percent.toFixed(2))}%`;
    ui.missingCount.textContent = format.format(data.missing_count);
    ui.coverageEdition.textContent = `Sealie ${data.version} · Unicode ${data.unicode_version.replace(/\.0$/, "")}`;
    ui.coverageMeter.setAttribute("aria-valuenow", String(percent));
    ui.coverageMeter.firstElementChild.style.width = `${percent}%`;
    ui.coverageSummary.setAttribute("aria-busy", "false");
    let complete = 0;
    for (const chunk of data.chunks) {
      const option = document.createElement("option");
      option.value = chunk.first.toString(16);
      option.textContent = `${label(chunk.first)}–${label(chunk.last)}`;
      ui.rangeSelect.append(option);
      const total = chunk.last - chunk.first + 1;
      const full = chunk.count === total;
      if (full) complete++;
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = `range-tile ${full ? "is-complete" : chunk.count ? "is-partial" : "is-missing"}`;
      tile.dataset.range = option.value;
      tile.textContent = chunk.first.toString(16).toUpperCase();
      tile.title = `${option.textContent}: ${chunk.count}/${total} included`;
      tile.setAttribute("aria-label", tile.title);
      tile.setAttribute("aria-pressed", "false");
      tile.addEventListener("click", () => { ui.rangeSelect.value = option.value; page = 1; applyFilters(); writeState(); ui.resultsStatus.scrollIntoView({ block: "start", behavior: "auto" }); });
      ui.rangeMap.append(tile);
    }
    ui.rangeSummary.textContent = `${complete}/${data.chunks.length} ranges complete`;
    readState();
    applyFilters();
    document.documentElement.dataset.coverageReady = "true";
  } catch (error) {
    document.documentElement.dataset.coverageReady = "error";
    ui.characterGrid.setAttribute("aria-busy", "false");
    ui.coverageSummary.setAttribute("aria-busy", "false");
    ui.resultsStatus.textContent = "Character data could not load. Please reload the page to try again.";
    ui.resultsStatus.dataset.state = "error";
    console.error("Sealie coverage:", error);
  }
}

initialize();
