const FIRST_SEAL = 0x3d000;
const LAST_SEAL = 0x3fc3f;
const PRESETS = {
  dao: "道可道，非常道。\n名可名，非常名。",
  moon: "明月幾時有？\n把酒問青天。",
  heaven: "天地玄黃",
  learning: "學而時習",
};
const modernToSeal = new Map();
const sealToModern = new Map();
const selectedForms = new Map();
const ui = Object.fromEntries([
  "weight", "weightValue", "fontSize", "fontSizeValue", "sampleText", "specimenPreview",
  "conversionStatus", "fontStatus", "gridToggle", "copyText", "lookupForm", "lookupInput",
  "lookupStatus", "lookupResults",
].map((id) => [id, document.getElementById(id)]));
let mapReady = false;
let lastConvertedText = "";
let fontRequest = 0;
let fontTimer;
let copyTimer;
const copyButtonContent = Array.from(ui.copyText.childNodes, (node) => node.cloneNode(true));

const codeLabel = (cp) => `U+${cp.toString(16).toUpperCase().padStart(4, "0")}`;
const isSeal = (cp) => cp >= FIRST_SEAL && cp <= LAST_SEAL;
const isPunctuation = (character) => /[\p{P}\p{Z}\s]/u.test(character);

function convertText(text) {
  const tokens = [];
  const unknown = new Set();
  let rendered = 0;
  for (const character of text) {
    const cp = character.codePointAt(0);
    if (isSeal(cp)) {
      tokens.push({ text: character, kind: "seal", title: codeLabel(cp) });
      rendered += 1;
      continue;
    }
    const choices = modernToSeal.get(character);
    if (choices?.length) {
      const selected = selectedForms.get(character);
      const target = choices.includes(selected) ? selected : choices[0];
      tokens.push({ text: String.fromCodePoint(target), kind: "seal", title: `${character} → ${codeLabel(target)}` });
      rendered += 1;
    } else {
      const punctuation = isPunctuation(character);
      tokens.push({ text: character, kind: punctuation ? "punctuation" : "unmapped", title: punctuation ? "" : `No mapped Small Seal form for ${character}` });
      if (!punctuation) unknown.add(character);
    }
  }
  return { tokens, text: tokens.map((token) => token.text).join(""), rendered, unknown };
}

function setFontStatus(text, state = "ready") {
  ui.fontStatus.textContent = text;
  ui.fontStatus.dataset.state = state;
}

function checkFont(text) {
  clearTimeout(fontTimer);
  const request = ++fontRequest;
  const sealText = Array.from(text).filter((character) => isSeal(character.codePointAt(0))).join("");
  if (!sealText) {
    setFontStatus("Ready for your text");
    return;
  }
  if (!document.fonts?.load) {
    setFontStatus("Live font specimen");
    return;
  }
  fontTimer = setTimeout(async () => {
    if (request !== fontRequest) return;
    setFontStatus("Loading Sealie…", "loading");
    try {
      const faces = await document.fonts.load(`${ui.weight.value} 32px Seal`, sealText);
      if (request !== fontRequest) return;
      if (!faces.length) throw new Error("No matching font face");
      setFontStatus("Sealie is ready");
    } catch {
      if (request === fontRequest) setFontStatus("Font could not load. Please reload the page.", "error");
    }
  }, 100);
}

function renderSpecimen() {
  const source = ui.sampleText.value;
  const converted = convertText(source);
  lastConvertedText = converted.text;
  ui.specimenPreview.classList.toggle("is-empty", !source.trim());
  ui.specimenPreview.setAttribute("aria-label", source.trim() ? `Small Seal rendering of ${source}` : "Enter text to try Sealie");
  if (!source.trim()) {
    ui.specimenPreview.textContent = "A little history starts with a word.";
  } else {
    const fragment = document.createDocumentFragment();
    for (const token of converted.tokens) {
      const span = document.createElement("span");
      span.className = token.kind;
      span.textContent = token.text;
      if (token.title) span.title = token.title;
      fragment.append(span);
    }
    ui.specimenPreview.replaceChildren(fragment);
  }
  ui.conversionStatus.dataset.unmappedCount = String(converted.unknown.size);
  ui.conversionStatus.dataset.renderedCount = String(converted.rendered);
  if (!mapReady) {
    ui.conversionStatus.textContent = "Character mapping is unavailable. Direct Small Seal characters still work; please reload to convert modern Chinese.";
  } else if (!source.trim()) {
    ui.conversionStatus.textContent = "Type a few characters, or choose a literature sample above.";
  } else {
    const count = `${converted.rendered} Small Seal character${converted.rendered === 1 ? "" : "s"}`;
    const unlisted = Array.from(converted.unknown);
    const suffix = unlisted.length ? ` · Unmapped, shown in gray: ${unlisted.slice(0, 12).join(" ")}${unlisted.length > 12 ? " …" : ""}` : " · All characters with a mapped form are converted.";
    ui.conversionStatus.textContent = count + suffix;
  }
  checkFont(converted.text);
}

function setWeight() {
  document.documentElement.style.setProperty("--weight", ui.weight.value);
  ui.weightValue.value = ui.weight.value;
  ui.weight.setAttribute("aria-valuetext", `${ui.weight.value}, ${Number(ui.weight.value) < 400 ? "Light" : Number(ui.weight.value) < 600 ? "Regular to Medium" : "Semibold to Bold"}`);
}

function setSize() {
  document.documentElement.style.setProperty("--specimen-size", `${ui.fontSize.value}px`);
  ui.fontSizeValue.value = `${ui.fontSize.value} px`;
}

function lookup() {
  ui.lookupResults.replaceChildren();
  ui.lookupStatus.dataset.state = "ready";
  if (!mapReady) {
    ui.lookupStatus.textContent = "Character data is not ready. Please reload if this message remains.";
    return;
  }
  const query = ui.lookupInput.value.trim();
  let character;
  let exactSeal;
  const match = /^(?:U\+|0x)?([0-9a-f]{4,6})$/i.exec(query);
  if (match) {
    const cp = Number.parseInt(match[1], 16);
    if (cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff)) {
      ui.lookupStatus.textContent = "That is not a valid Unicode codepoint.";
      ui.lookupStatus.dataset.state = "error";
      return;
    }
    if (isSeal(cp)) exactSeal = cp;
    else character = String.fromCodePoint(cp);
  } else if (Array.from(query).length === 1) {
    const cp = query.codePointAt(0);
    if (isSeal(cp)) exactSeal = cp;
    else character = query;
  } else {
    ui.lookupStatus.textContent = "Enter one modern Chinese character or one Small Seal codepoint, such as 道 or U+3D55D.";
    ui.lookupStatus.dataset.state = "error";
    return;
  }
  if (exactSeal !== undefined) character = sealToModern.get(exactSeal);
  const choices = exactSeal !== undefined ? [exactSeal] : (modernToSeal.get(character) ?? []);
  if (!choices.length) {
    ui.lookupStatus.textContent = `No modern-to-Small-Seal mapping is recorded for ${character || query}. Try another character or an encoded codepoint in U+3D000–U+3FC3F.`;
    ui.lookupStatus.dataset.state = "error";
    return;
  }
  const selected = selectedForms.get(character) ?? modernToSeal.get(character)?.[0];
  ui.lookupStatus.textContent = `${character ? `${character} · ` : ""}${choices.length} encoded form${choices.length === 1 ? "" : "s"}${choices.length > 1 ? " · Select a form to use it in the live specimen." : ""}`;
  const fragment = document.createDocumentFragment();
  for (const cp of choices) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "glyph-card";
    card.dataset.codepoint = codeLabel(cp);
    card.setAttribute("aria-label", `Use ${codeLabel(cp)}${character ? ` for ${character}` : ""} in the specimen`);
    card.setAttribute("aria-pressed", String(cp === selected));
    const glyph = document.createElement("span");
    glyph.className = "glyph seal-font";
    glyph.textContent = String.fromCodePoint(cp);
    glyph.setAttribute("aria-hidden", "true");
    const code = document.createElement("span");
    code.className = "glyph-code";
    code.textContent = codeLabel(cp);
    const caption = document.createElement("span");
    caption.className = "glyph-caption";
    caption.textContent = character ? `Modern: ${character}` : "Small Seal";
    card.append(glyph, code, caption);
    card.addEventListener("click", () => {
      if (character) selectedForms.set(character, cp);
      for (const peer of ui.lookupResults.querySelectorAll(".glyph-card")) peer.setAttribute("aria-pressed", String(peer === card));
      renderSpecimen();
      ui.lookupStatus.textContent = `${codeLabel(cp)} selected${character ? ` for ${character}` : ""}. This form is now used wherever that modern character appears in your specimen.`;
    });
    fragment.append(card);
  }
  ui.lookupResults.append(fragment);
}

async function copySpecimen() {
  if (!lastConvertedText) return;
  let copied = false;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(lastConvertedText);
      copied = true;
    }
  } catch { /* A local fallback is useful when clipboard permission is unavailable. */ }
  if (!copied) {
    const temporary = document.createElement("textarea");
    temporary.value = lastConvertedText;
    temporary.setAttribute("aria-label", "Small Seal text to copy");
    temporary.style.cssText = "position:fixed;left:-9999px;top:0;";
    document.body.append(temporary);
    temporary.select();
    try { copied = document.execCommand("copy"); } catch { copied = false; }
    temporary.remove();
    ui.copyText.focus();
  }
  clearTimeout(copyTimer);
  ui.copyText.textContent = copied ? "Copied Small Seal" : "Copy unavailable — select the specimen text";
  copyTimer = setTimeout(() => { ui.copyText.replaceChildren(...copyButtonContent.map((node) => node.cloneNode(true))); }, 2400);
}

ui.weight.addEventListener("input", setWeight);
ui.fontSize.addEventListener("input", setSize);
ui.sampleText.addEventListener("input", () => {
  for (const button of document.querySelectorAll("[data-preset]")) button.setAttribute("aria-pressed", "false");
  renderSpecimen();
});
ui.gridToggle.addEventListener("click", () => {
  const enabled = ui.gridToggle.getAttribute("aria-pressed") !== "true";
  ui.gridToggle.setAttribute("aria-pressed", String(enabled));
  ui.gridToggle.setAttribute("aria-label", `${enabled ? "Hide" : "Show"} specimen grid`);
  ui.specimenPreview.classList.toggle("show-grid", enabled);
});
ui.copyText.addEventListener("click", copySpecimen);
ui.lookupForm.addEventListener("submit", (event) => { event.preventDefault(); lookup(); });
for (const button of document.querySelectorAll("[data-preset]")) {
  button.addEventListener("click", () => {
    const value = PRESETS[button.dataset.preset];
    if (!value) return;
    ui.sampleText.value = value;
    for (const peer of document.querySelectorAll("[data-preset]")) peer.setAttribute("aria-pressed", String(peer === button));
    renderSpecimen();
  });
}
if (matchMedia("(max-width: 700px)").matches) ui.fontSize.value = "64";
setWeight();
setSize();

async function initialize() {
  try {
    const response = await fetch(new URL("character-map.json", import.meta.url));
    if (!response.ok) throw new Error(`Character data returned ${response.status}`);
    const data = await response.json();
    if (data.schema_version !== 1 || !Array.isArray(data.entries) || data.entries.length !== 11328) throw new Error("Unexpected character map");
    for (const [seal, modern] of data.entries) {
      if (!Number.isInteger(seal) || !isSeal(seal) || !Number.isInteger(modern) || modern < 0 || modern > 0x10ffff) throw new Error("Invalid character mapping");
      const character = String.fromCodePoint(modern);
      const forms = modernToSeal.get(character) ?? [];
      forms.push(seal);
      modernToSeal.set(character, forms);
      sealToModern.set(seal, character);
    }
    for (const forms of modernToSeal.values()) forms.sort((a, b) => a - b);
    mapReady = true;
    document.documentElement.dataset.mapReady = "true";
    renderSpecimen();
    lookup();
  } catch (error) {
    document.documentElement.dataset.mapReady = "error";
    ui.lookupStatus.textContent = "Character data could not load. Please reload the page. Direct Small Seal text still works in the specimen.";
    ui.lookupStatus.dataset.state = "error";
    renderSpecimen();
    console.error("Sealie character map:", error);
  }
}
initialize();
