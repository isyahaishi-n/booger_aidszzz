"use strict";

/* ===================== property metadata ===================== */

const PROP_ID_TO_NAME = {
  11101: "HpMax_Base", 11102: "HpMax_Ratio", 11103: "HpMax_Delta",
  12101: "Atk_Base", 12102: "Atk_Ratio", 12103: "Atk_Delta",
  12201: "BreakStun_Base", 12202: "BreakStun_Ratio",
  12301: "SkipDefAtk_Base", 12303: "SkipDefAtk_Delta",
  13101: "Def_Base", 13102: "Def_Ratio", 13103: "Def_Delta",
  20101: "Crit_Base", 20103: "Crit_Delta",
  21101: "CritDmg_Base", 21103: "CritDmg_Delta",
  23101: "PenRatio_Base", 23103: "PenRatio_Delta",
  23201: "PenDelta_Base", 23203: "PenDelta_Delta",
  30501: "SpRecover_Base", 30502: "SpRecover_Ratio", 30503: "SpRecover_Delta",
  31201: "ElementMystery_Base", 31203: "ElementMystery_Delta",
  31401: "ElementAbnormalPower_Base", 31402: "ElementAbnormalPower_Ratio", 31403: "ElementAbnormalPower_Delta",
  31501: "AddedDamageRatio_Physics_Base", 31503: "AddedDamageRatio_Physics_Delta",
  31601: "AddedDamageRatio_Fire_Base", 31603: "AddedDamageRatio_Fire_Delta",
  31701: "AddedDamageRatio_Ice_Base", 31703: "AddedDamageRatio_Ice_Delta",
  31801: "AddedDamageRatio_Elec_Base", 31803: "AddedDamageRatio_Elec_Delta",
  31901: "AddedDamageRatio_Ether_Base", 31903: "AddedDamageRatio_Ether_Delta",
  32001: "RpRecover_Base", 32002: "RpRecover_Ratio", 32003: "RpRecover_Delta",
  32201: "SkipDefDamageRatio_Base", 32203: "SkipDefDamageRatio_Delta",
  32301: "AddedDamageRatio_Wind_Base", 32303: "AddedDamageRatio_Wind_Delta",
};

const PROP_DISPLAY = {
  11101: ["HP", false], 11102: ["HP", true], 11103: ["HP", false],
  12101: ["ATK", false], 12102: ["ATK", true], 12103: ["ATK", false],
  12201: ["Impact", false], 12202: ["Impact", true],
  12301: ["Sheer Force", false], 12303: ["Sheer Force", false],
  13101: ["DEF", false], 13102: ["DEF", true], 13103: ["DEF", false],
  20101: ["CRIT Rate", true], 20103: ["CRIT Rate", true],
  21101: ["CRIT DMG", true], 21103: ["CRIT DMG", true],
  23101: ["PEN Ratio", true], 23103: ["PEN Ratio", true],
  23201: ["PEN", false], 23203: ["PEN", false],
  30501: ["Energy Regen", false], 30502: ["Energy Regen", true], 30503: ["Energy Regen", false],
  31201: ["Anomaly Proficiency", false], 31203: ["Anomaly Proficiency", false],
  31401: ["Anomaly Mastery", false], 31402: ["Anomaly Mastery", true], 31403: ["Anomaly Mastery", false],
  31501: ["Physical DMG", true], 31503: ["Physical DMG", true],
  31601: ["Fire DMG", true], 31603: ["Fire DMG", true],
  31701: ["Ice DMG", true], 31703: ["Ice DMG", true],
  31801: ["Electric DMG", true], 31803: ["Electric DMG", true],
  31901: ["Ether DMG", true], 31903: ["Ether DMG", true],
  32001: ["Decibel Regen", false], 32002: ["Decibel Regen", true], 32003: ["Decibel Regen", false],
  32201: ["Sheer DMG", true], 32203: ["Sheer DMG", true],
  32301: ["Wind DMG", true], 32303: ["Wind DMG", true],
};

const SKILL_INDEX_TO_NAME = {
  0: "Basic Attack", 2: "Dodge", 6: "Assist",
  1: "Special Attack", 3: "Chain Attack", 5: "Core Skill",
};
const CORE_LETTERS = ["-", "A", "B", "C", "D", "E", "F"];
const RANKS = { 2: "B", 3: "A", 4: "S" };

const ELEMENTS = {
  Fire: { name: "Fire", color: "#ff5449" },
  Ice: { name: "Ice", color: "#48c8ff" },
  Elec: { name: "Electric", color: "#b458ff" },
  Ether: { name: "Ether", color: "#d9e55c" },
  Physics: { name: "Physical", color: "#cdd3de" },
  Wind: { name: "Wind", color: "#41f2a6" },
  FireFrost: { name: "Frostburn", color: "#8fd8ff" },
  AuricEther: { name: "Auric Ink", color: "#ffd24d" },
  Lumen: { name: "Lumen", color: "#fff0a8" },
  ZhenZhenAssault: { name: "Assault", color: "#ff9e64" },
};

const PROFESSIONS = {
  Attack: { name: "Attack", color: "#ff5449" },
  Stun: { name: "Stun", color: "#ffd24d" },
  Anomaly: { name: "Anomaly", color: "#b458ff" },
  Support: { name: "Support", color: "#41f2a6" },
  Defense: { name: "Defense", color: "#48c8ff" },
  Rupture: { name: "Rupture", color: "#ff9e64" },
};

/* ===================== state ===================== */

const G = {
  avatars: null, weapons: null, equipments: null, locale: null,
  mindscapes: null, mindscapeProps: null,
  weaponLevels: null, weaponStars: null, equipmentLevels: null,
};
let showcase = null; // current player showcase data

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html !== undefined) n.innerHTML = html;
  return n;
};
const ESC_CODES = { "&": 38, "<": 60, ">": 62, '"': 34, "'": 39 };
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => "&#" + ESC_CODES[c] + ";");

const fmtNum = (n) => Math.round(n).toLocaleString("en-US");

/* ===================== damage calculation section ===================== */

const CALC = {
  monsters: [],            // cached /api/monsters
  current: null,           // {avatarId, name}
  enemy: { name: "Tyrfing", level: 60, stunned: false },
};

function monsterIconUrl(mon) {
  if (!mon.icon_url) return null;
  const slug = mon.icon_url.split("/").pop();
  return `/img/monster/${encodeURIComponent(slug)}`;
}

async function loadMonsterList() {
  if (CALC.monsters.length) return CALC.monsters;
  const res = await fetch("/api/monsters");
  if (!res.ok) throw new Error("Failed to load monster list");
  const data = await res.json();
  CALC.monsters = data.monsters || [];
  return CALC.monsters;
}

function renderCalcTarget() {
  const box = $("#calc-target");
  box.innerHTML = "";

  // enemy picker
  const wrap = el("div", "enemy-picker");
  wrap.appendChild(el("span", "enemy-label", "Enemy"));

  const search = el("input", "enemy-search");
  search.type = "search";
  search.placeholder = "Search monster…";
  search.value = CALC.enemy.name;
  wrap.appendChild(search);

  const lvl = el("input", "enemy-level");
  lvl.type = "number";
  lvl.min = 1; lvl.max = 80;
  lvl.value = CALC.enemy.level;
  wrap.appendChild(el("span", "enemy-label", "Lv."));
  wrap.appendChild(lvl);

  const stunBtn = el("button", "btn" + (CALC.enemy.stunned ? "" : " btn-ghost"));
  stunBtn.textContent = CALC.enemy.stunned ? "Stunned ✓" : "Stunned";
  stunBtn.title = "Stun Modifier: damage × (1 + StunDamageTakenRatio)";
  wrap.appendChild(stunBtn);

  box.appendChild(wrap);

  // dropdown results container
  const drop = el("div", "enemy-drop hidden");
  box.appendChild(drop);

  function showDrop(filter) {
    const f = (filter || "").toLowerCase();
    const hits = CALC.monsters.filter((m) => m.name.toLowerCase().includes(f)).slice(0, 60);
    drop.innerHTML = "";
    for (const m of hits) {
      const row = el("div", "enemy-row");
      const ic = monsterIconUrl(m);
      if (ic) {
        const im = el("img", "enemy-icon");
        im.src = ic; im.alt = ""; im.loading = "lazy";
        im.onerror = () => { im.style.visibility = "hidden"; };
        row.appendChild(im);
      } else {
        row.appendChild(el("span", "enemy-icon enemy-icon-ph", "◈"));
      }
      const nm = el("div", "enemy-row-name");
      nm.appendChild(el("div", "nm", esc(m.name)));
      const meta = [m.rank, m.size, m.faction].filter(Boolean).join(" · ");
      nm.appendChild(el("div", "meta", esc(meta)));
      row.appendChild(nm);
      if (m.rarity) row.appendChild(el("span", "enemy-rarity", "★".repeat(Math.min(4, m.rarity))));
      row.addEventListener("click", () => {
        CALC.enemy.name = m.name;
        search.value = m.name;
        drop.classList.add("hidden");
        runCalc();
      });
      drop.appendChild(row);
    }
    drop.classList.toggle("hidden", !hits.length);
  }

  search.addEventListener("input", () => showDrop(search.value));
  search.addEventListener("focus", () => showDrop(search.value));
  search.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const exact = CALC.monsters.find((m) => m.name.toLowerCase() === search.value.trim().toLowerCase());
      if (exact) { CALC.enemy.name = exact.name; drop.classList.add("hidden"); runCalc(); }
      else showDrop(search.value);
    }
  });
  document.addEventListener("click", (e) => {
    if (!wrap.contains(e.target)) drop.classList.add("hidden");
  });

  lvl.addEventListener("change", () => {
    CALC.enemy.level = Math.max(1, Math.min(80, parseInt(lvl.value, 10) || 60));
    lvl.value = CALC.enemy.level;
    runCalc();
  });
  stunBtn.addEventListener("click", () => {
    CALC.enemy.stunned = !CALC.enemy.stunned;
    stunBtn.textContent = CALC.enemy.stunned ? "Stunned ✓" : "Stunned";
    stunBtn.className = "btn" + (CALC.enemy.stunned ? "" : " btn-ghost");
    runCalc();
  });
}

async function openCalc(apiAvatar) {
  CALC.current = { avatarId: apiAvatar.Id };
  const excel = G.avatars[String(apiAvatar.Id)];
  const name = excel ? localize(excel.Name, String(apiAvatar.Id)) : `#${apiAvatar.Id}`;
  $("#calc-title").textContent = `Damage — ${name} Lv.${apiAvatar.Level}`;
  $("#calc-section").classList.remove("hidden");
  renderCalcTarget();
  $("#calc-body").innerHTML = `<div class="calc-loading">Calculating…</div>`;
  $("#calc-section").scrollIntoView({ behavior: "smooth", block: "start" });
  await runCalc();
}

async function runCalc() {
  if (!CALC.current || !showcase) return;
  const body = $("#calc-body");
  body.innerHTML = `<div class="calc-loading">Calculating…</div>`;
  try {
    const res = await fetch("/api/calc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        showcase,
        avatar_id: CALC.current.avatarId,
        enemy: CALC.enemy.name,
        enemy_level: CALC.enemy.level,
        stunned: CALC.enemy.stunned,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    renderCalcResult(data);
  } catch (e) {
    body.innerHTML = `<div class="status error">${esc(e.message || "Calculation failed")}</div>`;
  }
}

function renderCalcResult(r) {
  const body = $("#calc-body");
  body.innerHTML = "";

  // enemy summary strip
  const e = r.enemy;
  const strip = el("div", "calc-enemy-strip");
  const ic = e.icon_url ? `/img/monster/${encodeURIComponent(e.icon_url.split("/").pop())}` : null;
  if (ic) {
    const im = el("img", "enemy-portrait");
    im.src = ic; im.alt = e.name;
    im.onerror = () => { im.style.visibility = "hidden"; };
    strip.appendChild(im);
  }
  const info = el("div", "enemy-info");
  info.appendChild(el("div", "nm", `${esc(e.name)} <span class="lvl">Lv.${e.level}</span>`));
  const resParts = Object.entries(e.res_pct || {}).filter(([, v]) => v)
    .map(([k, v]) => `${k} ${v > 0 ? "+" : ""}${Math.round(v * 100)}%`);
  const meta = [
    `DEF ${fmtNum(e.def_val)}`, `HP ${fmtNum(e.hp_val)}`,
    `Stun DMG taken +${Math.round(e.stun_taken_pct * 100)}%`,
    resParts.length ? `RES ${resParts.join(", ")}` : null,
    e.rank, e.faction,
  ].filter(Boolean);
  info.appendChild(el("div", "meta", esc(meta.join(" · "))));
  strip.appendChild(info);
  body.appendChild(strip);

  // active buffs (toggles)
  const active = (r.toggles || []).filter((t) => t.enabled);
  if (active.length) {
    const buffs = el("div", "calc-buffs");
    buffs.appendChild(el("span", "buff-label", "Active buffs:"));
    for (const t of active) {
      buffs.appendChild(el("span", "buff-chip",
        `${esc(t.source_name)} <b>+${t.value}${t.unit === "percent" ? "%" : ""} ${esc(t.stat)}</b>`));
    }
    body.appendChild(buffs);
  }

  // damage table
  if (!r.rows.length) {
    body.appendChild(el("div", "calc-empty",
      "No skill data to calculate (agent without gear?)."));
    return;
  }
  const table = el("table", "calc-table");
  table.innerHTML = `
    <thead><tr>
      <th>Skill</th><th>Hit</th><th class="num">Mult</th>
      <th class="num">Non-Crit</th><th class="num">Crit</th>
      <th class="num">${r.stunned ? "Non-Crit (stunned)" : "If Stunned"}</th>
    </tr></thead>`;
  const tbody = el("tbody");
  let lastSkill = null;
  for (const row of r.rows) {
    const tr = el("tr");
    if (row.damage_pct <= 0 && row.daze_pct > 0) {
      // daze-only hit
      tr.className = "daze-row";
      tr.innerHTML = `
        <td>${row.skill === lastSkill ? "" : esc(row.skill)}</td>
        <td>${esc(row.hit)}</td>
        <td class="num" colspan="4">(daze-only) daze ${row.daze_pct.toFixed(1)}%</td>`;
      lastSkill = row.skill;
      tbody.appendChild(tr);
      continue;
    }
    tr.innerHTML = `
      <td>${row.skill === lastSkill ? "" : `<b>${esc(row.skill)}</b>`}</td>
      <td>${esc(row.hit)}</td>
      <td class="num">${row.damage_pct.toFixed(1)}%</td>
      <td class="num">${fmtNum(row.non_crit)}</td>
      <td class="num crit">${fmtNum(row.crit)}</td>
      <td class="num">${fmtNum(row.stun_non_crit)}</td>`;
    lastSkill = row.skill;
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  body.appendChild(table);
}

/* ===================== helpers ===================== */

function localize(key, fallback) {
  if (!key) return fallback;
  return G.locale[key] || key;
}

function findRow(rows, match) {
  return rows.find((r) => Object.entries(match).every(([k, v]) => r[k] === v));
}

function propName(id) {
  return PROP_ID_TO_NAME[id] || String(id);
}

function formatProp(id, value) {
  const [label, isPct] = PROP_DISPLAY[id] || [propName(id), false];
  if (isPct) return `${label} ${(value / 100).toFixed(1)}%`;
  return `${label} ${Math.floor(value)}`;
}

function effectiveSkillLevel(base, mindscape) {
  let bump = 0;
  if (mindscape >= 3) bump += 2;
  if (mindscape >= 5) bump += 2;
  return base + bump;
}

/* ===================== stat engine (port of the python calculator) ===================== */

function newLayer() {
  const l = {};
  for (const name of new Set(Object.values(PROP_ID_TO_NAME))) l[name] = 0;
  return l;
}

function addProp(l, id, value) {
  const n = propName(id);
  l[n] = (l[n] || 0) + value;
}

function computeStats(apiAvatar) {
  const excel = G.avatars[String(apiAvatar.Id)];
  if (!excel) return null;

  const level = apiAvatar.Level;
  const promotion = apiAvatar.PromotionLevel;
  const core = apiAvatar.CoreSkillEnhancement;
  const mindscape = apiAvatar.TalentLevel || 0;

  const L = newLayer();

  // --- character: base + growth + promotion ---
  const base = excel.BaseProps || {};
  const growth = excel.GrowthProps || {};
  const promoRow = (excel.PromotionProps || [])[promotion - 1] || {};
  for (const [pid, baseVal] of Object.entries(base)) {
    const id = Number(pid);
    const v = baseVal + ((growth[pid] || 0) / 10000) * (level - 1) + (promoRow[pid] || 0);
    addProp(L, id, v);
  }

  // --- core skill enhancement ---
  const coreRow = (excel.CoreEnhancementProps || [])[core] || {};
  for (const [pid, v] of Object.entries(coreRow)) addProp(L, Number(pid), v);

  // --- weapon ---
  const w = apiAvatar.Weapon;
  if (w) {
    const wmeta = G.weapons[String(w.Id)];
    if (wmeta) {
      const rarity = wmeta.Rarity;
      const lvlRow = findRow(G.weaponLevels, { Rarity: rarity, Level: w.Level });
      const starRow = findRow(G.weaponStars, { Rarity: rarity, BreakLevel: w.BreakLevel });
      if (lvlRow && starRow) {
        const main = wmeta.MainStat;
        const sub = wmeta.SecondaryStat;
        const mainVal = Math.floor(main.PropertyValue * (1 + lvlRow.EnhanceRate / 10000 + starRow.StarRate / 10000));
        const subVal = Math.floor(sub.PropertyValue * (1 + starRow.RandRate / 10000));
        addProp(L, main.PropertyId, mainVal);
        addProp(L, sub.PropertyId, subVal);
      }
    }
  }

  // --- drive discs ---
  const suitCounts = {};
  for (const equip of apiAvatar.EquippedList || []) {
    const disc = equip.Equipment;
    const meta = G.equipments.Items[String(disc.Id)];
    if (!meta) continue;
    const lvlRow = findRow(G.equipmentLevels, { Rarity: meta.Rarity, Level: disc.Level });
    if (lvlRow) {
      const main = disc.MainPropertyList[0];
      const mainVal = Math.floor(main.PropertyValue * (1 + lvlRow.EnhanceRate / 10000));
      addProp(L, main.PropertyId, mainVal);
    }
    for (const sub of disc.RandomPropertyList || []) {
      addProp(L, sub.PropertyId, sub.PropertyValue * sub.PropertyLevel);
    }
    const sid = String(meta.SuitId);
    suitCounts[sid] = (suitCounts[sid] || 0) + 1;
  }

  // --- set bonuses (2pc) ---
  for (const [sid, count] of Object.entries(suitCounts)) {
    if (count < 2) continue;
    const suit = G.equipments.Suits[sid];
    if (!suit || !suit.SetBonusProps) continue;
    for (const [pid, v] of Object.entries(suit.SetBonusProps)) addProp(L, Number(pid), v);
  }

  // --- mindscape stat props (unconditional only) ---
  const msProps = (G.mindscapeProps && G.mindscapeProps[String(apiAvatar.Id)]) || {};
  for (let m = 1; m <= mindscape; m++) {
    const entry = msProps[String(m)];
    if (entry && entry.unconditional) {
      for (const [pid, v] of Object.entries(entry.props || {})) addProp(L, Number(pid), v);
    }
  }

  // --- floor everything except SpRecover ---
  for (const k of Object.keys(L)) {
    if (k.startsWith("SpRecover_")) L[k] = L[k];
    else L[k] = Math.floor(L[k]);
  }

  // --- rupture correction (Sheer Force) ---
  if ((excel.ProfessionType || "").toLowerCase() === "rupture") {
    const atk = Math.floor(L.Atk_Base * (1 + L.Atk_Ratio / 10000) + L.Atk_Delta);
    const hp = Math.floor(L.HpMax_Base + Math.ceil(L.HpMax_Base * L.HpMax_Ratio / 10000) + L.HpMax_Delta);
    L.SkipDefAtk_Delta += Math.floor(atk * 0.3) + Math.floor(hp * 0.1);
  }

  // --- final stats ---
  const p = (n) => L[n] || 0;
  return {
    "HP": p("HpMax_Base") + Math.ceil(p("HpMax_Base") * p("HpMax_Ratio") / 10000) + p("HpMax_Delta"),
    "ATK": p("Atk_Base") * (1 + p("Atk_Ratio") / 10000) + p("Atk_Delta"),
    "DEF": p("Def_Base") * (1 + p("Def_Ratio") / 10000) + p("Def_Delta"),
    "Impact": p("BreakStun_Base") * (1 + p("BreakStun_Ratio") / 10000),
    "CRIT Rate": p("Crit_Base") + p("Crit_Delta"),
    "CRIT DMG": p("CritDmg_Base") + p("CritDmg_Delta"),
    "PEN Ratio": p("PenRatio_Base") + p("PenRatio_Delta"),
    "PEN": p("PenDelta_Base") + p("PenDelta_Delta"),
    "Anomaly Proficiency": p("ElementMystery_Base") + p("ElementMystery_Delta"),
    "Anomaly Mastery": p("ElementAbnormalPower_Base") * (1 + p("ElementAbnormalPower_Ratio") / 10000) + p("ElementAbnormalPower_Delta"),
    "Energy Regen": (p("SpRecover_Base") * (1 + p("SpRecover_Ratio") / 10000) + p("SpRecover_Delta")) / 100,
    "Sheer Force": p("SkipDefAtk_Base") + p("SkipDefAtk_Delta"),
    "Physical DMG": p("AddedDamageRatio_Physics_Base") + p("AddedDamageRatio_Physics_Delta"),
    "Fire DMG": p("AddedDamageRatio_Fire_Base") + p("AddedDamageRatio_Fire_Delta"),
    "Ice DMG": p("AddedDamageRatio_Ice_Base") + p("AddedDamageRatio_Ice_Delta"),
    "Electric DMG": p("AddedDamageRatio_Elec_Base") + p("AddedDamageRatio_Elec_Delta"),
    "Ether DMG": p("AddedDamageRatio_Ether_Base") + p("AddedDamageRatio_Ether_Delta"),
    "Wind DMG": p("AddedDamageRatio_Wind_Base") + p("AddedDamageRatio_Wind_Delta"),
    "Sheer DMG": p("SkipDefDamageRatio_Base") + p("SkipDefDamageRatio_Delta"),
  };
}

const PCT_STATS = new Set([
  "CRIT Rate", "CRIT DMG", "PEN Ratio", "Physical DMG", "Fire DMG",
  "Ice DMG", "Electric DMG", "Ether DMG", "Wind DMG", "Sheer DMG",
]);

function fmtStat(name, value) {
  if (PCT_STATS.has(name)) return (Math.floor(value) / 100).toFixed(1) + "%";
  if (name === "Energy Regen") return String(Math.round(value * 100) / 100);
  return String(Math.floor(value));
}

/* ===================== rendering ===================== */

function setStatus(msg, isError) {
  const s = $("#status");
  if (!msg) { s.classList.add("hidden"); return; }
  s.textContent = msg;
  s.classList.toggle("error", !!isError);
  s.classList.remove("hidden");
}

function renderPlayer(api) {
  const box = $("#player");
  const soc = api.PlayerInfo && api.PlayerInfo.SocialDetail;
  if (!soc) { box.classList.add("hidden"); return; }
  const pd = soc.ProfileDetail || {};
  const profAvatar = G.avatars[String(pd.AvatarId)];
  const img = profAvatar ? profAvatar.CircleIcon : null;
  const platform = { 1: "iOS", 2: "Android", 3: "PC", 4: "PS5" }[pd.PlatformType] || "?";
  box.innerHTML = "";
  if (img) {
    const av = el("img", "player-avatar");
    av.src = img;
    av.alt = "";
    box.appendChild(av);
  }
  const info = el("div", "player-info");
  info.appendChild(el("div", "player-name", esc(pd.Nickname || "Agent")));
  info.appendChild(el("div", "player-meta", `Lv.${pd.Level || "?"} · UID ${pd.Uid || "?"} · ${platform}`));
  if (soc.Comment) info.appendChild(el("div", "player-desc", esc(soc.Comment)));
  box.appendChild(info);
  box.classList.remove("hidden");
}

function charCard(apiAvatar) {
  const excel = G.avatars[String(apiAvatar.Id)];
  const card = el("div", "char-card");
  if (!excel) {
    card.innerHTML = `<div class="body"><div class="name">Unknown #${esc(apiAvatar.Id)}</div></div>`;
    return card;
  }

  const stats = computeStats(apiAvatar) || {};
  const rank = RANKS[excel.Rarity] || "?";
  const elems = excel.ElementTypes || [];
  const mainElem = elems[elems.length - 1] || "Physics";
  const elemMeta = ELEMENTS[mainElem] || { name: mainElem, color: "#999" };
  const profMeta = PROFESSIONS[excel.ProfessionType] || { name: excel.ProfessionType, color: "#999" };
  const name = localize(excel.Name, String(apiAvatar.Id));
  const core = apiAvatar.CoreSkillEnhancement;
  const coreLetter = CORE_LETTERS[core] || String(core);

  // banner
  const banner = el("div", "banner");
  const img = el("img", "portrait");
  img.src = excel.Image;
  img.alt = name;
  banner.appendChild(img);
  const badges = el("div", "badges");
  badges.appendChild(el("span", `badge rank-${rank}`, esc(rank)));
  const eb = el("span", "badge elem");
  eb.style.color = elemMeta.color;
  eb.style.borderColor = elemMeta.color + "80";
  eb.textContent = elemMeta.name;
  badges.appendChild(eb);
  const pb = el("span", "badge");
  pb.style.color = profMeta.color;
  pb.style.borderColor = profMeta.color + "80";
  pb.textContent = profMeta.name;
  badges.appendChild(pb);
  banner.appendChild(badges);
  card.appendChild(banner);

  // body
  const body = el("div", "body");
  const nameRow = el("div", "name-row");
  nameRow.appendChild(el("div", "name", esc(name)));
  nameRow.appendChild(el("div", "lvl", `Lv.${apiAvatar.Level} · M${apiAvatar.TalentLevel || 0} · Core ${coreLetter}`));
  body.appendChild(nameRow);

  const w = apiAvatar.Weapon;
  if (w) {
    const wmeta = G.weapons[String(w.Id)];
    if (wmeta) {
      const wname = localize(wmeta.ItemName, String(w.Id));
      const wrank = RANKS[wmeta.Rarity] || "?";
      body.appendChild(el("div", "sub", `${esc(wname)} · ${wrank}-rank · Lv.${w.Level}`));
    }
  }

  const statsGrid = el("div", "stats");
  for (const key of ["HP", "ATK", "DEF", "CRIT Rate", "CRIT DMG"]) {
    const v = stats[key];
    if (v === undefined) continue;
    const row = el("div", "stat");
    row.appendChild(el("span", "k", esc(key)));
    row.appendChild(el("span", "v" + (PCT_STATS.has(key) ? " pct" : ""), esc(fmtStat(key, v))));
    statsGrid.appendChild(row);
  }
  body.appendChild(statsGrid);

  // calc button — terpisah dari click-card (card click = modal detail)
  const calcBtn = el("button", "calc-btn", "⚔ Calculate");
  calcBtn.title = "Hitung damage vs monster pilihan";
  calcBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    openCalc(apiAvatar);
  });
  body.appendChild(calcBtn);
  card.appendChild(body);

  card.addEventListener("click", () => openModal(apiAvatar));
  return card;
}

function renderChars(api) {
  const grid = $("#chars");
  grid.innerHTML = "";
  const list = (api.PlayerInfo && api.PlayerInfo.ShowcaseDetail && api.PlayerInfo.ShowcaseDetail.AvatarList) || [];
  if (!list.length) {
    setStatus("This player's showcase is empty (agents hidden in-game).", true);
    return;
  }
  for (const av of list) grid.appendChild(charCard(av));
}

/* ===================== modal ===================== */

function gearRow(icon, name, sub, statsHtml) {
  const row = el("div", "gear-row");
  const im = el("img", "gear-icon");
  im.src = icon;
  im.alt = "";
  im.onerror = () => { im.style.visibility = "hidden"; };
  row.appendChild(im);
  const main = el("div", "gear-main");
  main.appendChild(el("div", "gear-name", name));
  if (sub) main.appendChild(el("div", "gear-sub", sub));
  if (statsHtml) main.appendChild(el("div", "gear-stats", statsHtml));
  row.appendChild(main);
  return row;
}

function openModal(apiAvatar) {
  const excel = G.avatars[String(apiAvatar.Id)];
  const modal = $("#modal");
  const backdrop = $("#modal-backdrop");
  modal.innerHTML = "";
  if (!excel) return;

  const stats = computeStats(apiAvatar) || {};
  const rank = RANKS[excel.Rarity] || "?";
  const elems = excel.ElementTypes || [];
  const mainElem = elems[elems.length - 1] || "Physics";
  const elemMeta = ELEMENTS[mainElem] || { name: mainElem, color: "#999" };
  const profMeta = PROFESSIONS[excel.ProfessionType] || { name: excel.ProfessionType, color: "#999" };
  const name = localize(excel.Name, String(apiAvatar.Id));
  const mindscape = apiAvatar.TalentLevel || 0;
  const core = apiAvatar.CoreSkillEnhancement;
  const coreLetter = CORE_LETTERS[core] || String(core);

  // head
  const head = el("div", "modal-head");
  const img = el("img", "portrait");
  img.src = excel.Image;
  head.appendChild(img);
  const close = el("button", "modal-close", "✕");
  close.addEventListener("click", closeModal);
  head.appendChild(close);
  const title = el("div", "modal-title");
  title.appendChild(el("div", "name", esc(name)));
  title.appendChild(el("div", "sub",
    `${esc(rank)}-rank · <span style="color:${elemMeta.color}">${esc(elemMeta.name)}</span> · <span style="color:${profMeta.color}">${esc(profMeta.name)}</span> · Lv.${apiAvatar.Level} · M${mindscape} · Core ${esc(coreLetter)}`));
  head.appendChild(title);
  modal.appendChild(head);

  const body = el("div", "modal-body");

  // stats table
  body.appendChild(el("div", "section-title", "Stats"));
  const table = el("table", "stat-table");
  for (const [key, value] of Object.entries(stats)) {
    if (value === 0 && !["HP", "ATK", "DEF"].includes(key)) continue;
    const tr = el("tr");
    const td1 = el("td", "", esc(key));
    const td2 = el("td", PCT_STATS.has(key) ? "pct" : "", esc(fmtStat(key, value)));
    tr.appendChild(td1);
    tr.appendChild(td2);
    table.appendChild(tr);
  }
  body.appendChild(table);

  // weapon
  const w = apiAvatar.Weapon;
  if (w) {
    const wmeta = G.weapons[String(w.Id)];
    if (wmeta) {
      body.appendChild(el("div", "section-title", "W-Engine"));
      const wname = localize(wmeta.ItemName, String(w.Id));
      const wrank = RANKS[wmeta.Rarity] || "?";
      const lvlRow = findRow(G.weaponLevels, { Rarity: wmeta.Rarity, Level: w.Level });
      const starRow = findRow(G.weaponStars, { Rarity: wmeta.Rarity, BreakLevel: w.BreakLevel });
      let statsHtml = "";
      if (lvlRow && starRow && wmeta.MainStat) {
        const mv = Math.floor(wmeta.MainStat.PropertyValue * (1 + lvlRow.EnhanceRate / 10000 + starRow.StarRate / 10000));
        const sv = Math.floor(wmeta.SecondaryStat.PropertyValue * (1 + starRow.RandRate / 10000));
        statsHtml = `${esc(formatProp(wmeta.MainStat.PropertyId, mv))} · ${esc(formatProp(wmeta.SecondaryStat.PropertyId, sv))}`;
      }
      body.appendChild(gearRow(wmeta.ImagePath, esc(wname),
        `${esc(wrank)}-rank · Lv.${w.Level} · Mod ${w.BreakLevel}`, statsHtml));
    }
  }

  // drive discs
  const equipped = [...(apiAvatar.EquippedList || [])].sort((a, b) => a.Slot - b.Slot);
  if (equipped.length) {
    body.appendChild(el("div", "section-title", "Drive Discs"));
    for (const eq of equipped) {
      const disc = eq.Equipment;
      const meta = G.equipments.Items[String(disc.Id)];
      if (!meta) continue;
      const suit = G.equipments.Suits[String(meta.SuitId)];
      const suitName = suit ? localize(suit.Name, String(meta.SuitId)) : "?";
      const dr = RANKS[meta.Rarity] || "?";
      const lvlRow = findRow(G.equipmentLevels, { Rarity: meta.Rarity, Level: disc.Level });
      let statsHtml = "";
      if (lvlRow && disc.MainPropertyList && disc.MainPropertyList[0]) {
        const main = disc.MainPropertyList[0];
        const mv = Math.floor(main.PropertyValue * (1 + lvlRow.EnhanceRate / 10000));
        statsHtml = `<b>${esc(formatProp(main.PropertyId, mv))}</b>`;
        for (const sub of disc.RandomPropertyList || []) {
          const total = sub.PropertyValue * sub.PropertyLevel;
          statsHtml += ` · ${esc(formatProp(sub.PropertyId, total))}`;
        }
      }
      body.appendChild(gearRow(suit ? suit.Icon : "", esc(suitName),
        `Slot ${eq.Slot} · ${esc(dr)}-rank · +${disc.Level}`, statsHtml));
    }
  }

  // skills
  const skills = [...(apiAvatar.SkillLevelList || [])].sort((a, b) => a.Index - b.Index);
  if (skills.length) {
    body.appendChild(el("div", "section-title", "Skills"));
    const list = el("div", "skill-list");
    for (const sk of skills) {
      const label = SKILL_INDEX_TO_NAME[sk.Index] || `Skill ${sk.Index}`;
      const base = sk.Level;
      const eff = effectiveSkillLevel(base, mindscape);
      const item = el("div", "skill-item");
      item.appendChild(el("div", "sk-name", esc(label)));
      const lvl = el("div", "sk-lvl", String(eff));
      if (eff !== base) {
        lvl.innerHTML = `${base} → ${eff} <span class="sk-bump">M${mindscape}</span>`;
      }
      item.appendChild(lvl);
      list.appendChild(item);
    }
    body.appendChild(list);
  }

  // mindscapes
  const msData = G.mindscapes && (G.mindscapes[name] || G.mindscapes[Object.keys(G.mindscapes).find((k) => localize(G.avatars[String(apiAvatar.Id)] && G.avatars[String(apiAvatar.Id)].Name, "") === k)] );
  if (msData) {
    body.appendChild(el("div", "section-title", "Mindscape Cinema"));
    const grid = el("div", "mindscape-grid");
    for (let m = 1; m <= 6; m++) {
      const entry = msData[String(m)];
      if (!entry) continue;
      const card = el("div", "ms-card" + (m <= mindscape ? "" : " locked"));
      card.appendChild(el("div", "ms-title", `M${m} · ${esc(entry.title || "")}`));
      card.appendChild(el("div", "ms-desc", esc(entry.desc || "")));
      grid.appendChild(card);
    }
    body.appendChild(grid);
  }

  modal.appendChild(body);
  backdrop.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  $("#modal-backdrop").classList.add("hidden");
  document.body.style.overflow = "";
}

/* ===================== data loading ===================== */

async function loadGameData() {
  const res = await fetch("/api/data");
  if (!res.ok) throw new Error("Failed to load game data");
  const data = await res.json();
  G.avatars = data.avatars;
  G.weapons = data.weapons;
  G.equipments = data.equipments;
  G.locale = data.locale;
  G.mindscapes = data.mindscapes;
  G.mindscapeProps = data.mindscapeProps;
  G.weaponLevels = data.weaponLevels;
  G.weaponStars = data.weaponStars;
  G.equipmentLevels = data.equipmentLevels;
}

async function loadShowcase(url) {
  setStatus("Loading…");
  $("#chars").innerHTML = "";
  $("#player").classList.add("hidden");
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    showcase = data;
    setStatus("");
    renderPlayer(data);
    renderChars(data);
  } catch (e) {
    setStatus(e.message || "Failed to load showcase", true);
  }
}

/* ===================== boot ===================== */

async function boot() {
  $("#uid-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const uid = $("#uid-input").value.trim();
    if (!/^\d{6,12}$/.test(uid)) {
      setStatus("Please enter a valid UID (6-12 digits).", true);
      return;
    }
    loadShowcase(`/api/uid/${uid}`);
  });
  $("#btn-sample").addEventListener("click", () => loadShowcase("/api/local"));
  $("#modal-backdrop").addEventListener("click", (e) => {
    if (e.target === $("#modal-backdrop")) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
  $("#calc-close").addEventListener("click", () => {
    $("#calc-section").classList.add("hidden");
    CALC.current = null;
  });

  try {
    await loadGameData();
    loadShowcase("/api/local"); // start with bundled sample
    loadMonsterList().catch(() => {}); // preload monster list (background)
  } catch (e) {
    setStatus("Failed to load game data: " + e.message, true);
  }
}

boot();