"""
damage_calc.py — W-Engine passive layer + set 4pc conditional + formula
damage final, kalibrasi ke ground truth 1086/2961 (Miyabi vs Tyrfing L60).

Dibangun di atas fondasi yang udah tervalidasi:
- verify.py / zzz_enka_stat_calc_multichar.py -> stat panel (ATK/DEF/CRIT/dst)
- skill_lookup.py -> skill multiplier per hit
- wengine.md -> formula & kalibrasi manual yang mau dijadiin kode di sini

Formula (dari wiki ZZZ Damage page + wengine.md, terverifikasi manual):
    ATK_combat = ATK_panel * (1 + Bonus%_cond) + Flat_cond
    DEFmult    = 794 / (max(DEF_enemy*(1-PENratio) - PEN, 0) + 794)
    RESmult    = 1 - RES_enemy
    NonCrit    = ATK_combat * skill_mult% * DEFmult * RESmult
    Crit       = NonCrit * (1 + CRIT_DMG_combat%)
"""

import json
import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_textmap(base_path="TextMap_ENTemplateTb.json",
                  overwrite_path="TextMap_ENOverwriteTemplateTb.json") -> dict:
    """TextMap utama + Overwrite di-merge (Overwrite menang kalau ada duplikat)."""
    textmap = load_json(base_path)
    overwrite = load_json(overwrite_path)
    merged = dict(textmap)
    merged.update(overwrite)
    return merged


def resolve_text(key: str, textmap: dict) -> str:
    if not key:
        return ""
    return textmap.get(key, key)


def strip_color_tags(text: str) -> str:
    return re.sub(r"</?color(=#?[0-9A-Fa-f]+)?>", "", text)


# ---------------------------------------------------------------------------
# W-Engine passive
# ---------------------------------------------------------------------------

# Regex buat pola stat sederhana yang selalu aktif (unconditional):
# "Increases ATK by 12%." / "Increases CRIT Rate by 8%." dst.
_SIMPLE_STAT_RE = re.compile(
    r"Increases\s+([A-Za-z ]+?)\s+by\s+(\d+(?:\.\d+)?)%",
    re.IGNORECASE,
)

# Mapping nama stat dalam teks -> internal (samain sama PERCENT_PROPERTY_IDS
# vocabulary dari fetch.py biar konsisten)
_STAT_NAME_MAP = {
    "atk": "attackRate",
    "hp": "hpRate",
    "def": "defenseRate",
    "crit rate": "critRate",
    "crit dmg": "critDamage",
    "anomaly proficiency": "anomalyProficiency",
    "pen ratio": "penRate",
    "impact": "impact",
    "energy regen": "energyRegen",
}


def get_weapon_passive_row(weapon_talent_rows: list, weapon_id: int, phase: int) -> dict | None:
    """Cari baris passive weapon_id di phase tertentu (1-5 = S1-S5).
    Kalau phase yang diminta > phase max weapon ini, clamp ke max yang ada
    (passive nggak turun kalau weapon di-refine, cuma naik).
    """
    candidates = [r for r in weapon_talent_rows if r["COEEBFOBGND"] == weapon_id]
    if not candidates:
        return None
    max_phase = max(r["APAEMLCPFID"] for r in candidates)
    use_phase = min(phase, max_phase)
    matches = [r for r in candidates if r["APAEMLCPFID"] == use_phase]
    return matches[0] if matches else None


def parse_weapon_passive(row: dict, textmap: dict) -> dict:
    """Return {"title": str, "desc": str, "unconditional_bonuses": [{"stat", "value_pct"}],
    "raw_conditional_text": str} -- yang unconditional di-parse otomatis
    (pola "Increases X by Y%"), sisanya (kondisional/trigger) dibiarkan
    sebagai teks mentah buat direview manual.
    """
    title = strip_color_tags(resolve_text(row["CLCDDKNHEMN"], textmap))
    desc_raw = resolve_text(row["POLEJGCKKFI"], textmap)
    desc = strip_color_tags(desc_raw)

    bonuses = []
    for m in _SIMPLE_STAT_RE.finditer(desc):
        stat_text = m.group(1).strip().lower()
        value = float(m.group(2))
        stat_key = _STAT_NAME_MAP.get(stat_text)
        if stat_key:
            bonuses.append({"stat": stat_key, "value_pct": value, "raw_text": stat_text})

    return {
        "title": title,
        "desc": desc,
        "unconditional_bonuses": bonuses,
        "raw_full_text": desc,
    }


# ---------------------------------------------------------------------------
# Set 4pc (dan 2pc, buat kelengkapan/cross-check)
# ---------------------------------------------------------------------------

def get_set_bonus_text(suit_id: int, textmap: dict) -> dict:
    """Return {"2pc": str, "4pc": str} teks mentah (belum di-parse kondisi)."""
    two = strip_color_tags(resolve_text(f"EquipmentSuit_{suit_id}_2_des", textmap))
    four = strip_color_tags(resolve_text(f"EquipmentSuit_{suit_id}_4_des", textmap))
    return {"2pc": two, "4pc": four}


def parse_4pc_unconditional(text: str) -> list:
    """Sama kayak weapon passive: cuma nangkep pola 'X increases by Y%' yang
    keliatan always-on (biasanya kalimat pertama sebelum 'When ...').
    Kalimat kedua dst yang kondisional dibiarkan mentah.
    """
    # Ambil kalimat pertama aja (heuristic: unconditional biasanya di depan,
    # sebelum "When"/"If"/"Upon")
    first_sentence_match = re.split(r"\s+(?:When|If|Upon)\b", text, maxsplit=1)
    first_sentence = first_sentence_match[0]
    bonuses = []
    for m in _SIMPLE_STAT_RE.finditer(first_sentence):
        stat_text = m.group(1).strip().lower()
        value = float(m.group(2))
        stat_key = _STAT_NAME_MAP.get(stat_text)
        if stat_key:
            bonuses.append({"stat": stat_key, "value_pct": value})
    return bonuses


# ---------------------------------------------------------------------------
# Formula damage final
# ---------------------------------------------------------------------------

@dataclass
class EnemyStats:
    def_val: float
    res_pct: dict  # {"Physical": 0.0, "Ice": -0.20, ...} -- persen sebagai fraksi


@dataclass
class CombatModifiers:
    """Bonus yang UDAH digabung dari semua sumber conditional (W-Engine
    passive unconditional, set 4pc unconditional, dll) -- ini yang beda
    dari stat panel biasa.
    """
    atk_bonus_pct_cond: float = 0.0   # penjumlahan semua %ATK conditional
    atk_flat_cond: float = 0.0
    crit_dmg_bonus_pct_cond: float = 0.0
    crit_rate_bonus_pct_cond: float = 0.0


def compute_def_mult(enemy_def: float, pen_ratio_pct: float, pen_flat: float) -> float:
    """DEFmult = 794 / (max(DEF*(1-PENratio) - PEN, 0) + 794)
    Formula ini utk attacker level 60+ (konstanta 794 spesifik level itu).
    """
    effective_def = max(enemy_def * (1 - pen_ratio_pct / 100) - pen_flat, 0)
    return 794 / (effective_def + 794)


def compute_res_mult(res_pct: float) -> float:
    """RESmult = 1 - RES (RES dalam fraksi, misal -0.20 utk RES -20%)."""
    return 1 - res_pct


def compute_final_damage(
    atk_panel: float,
    skill_mult_pct: float,
    crit_dmg_panel_pct: float,
    enemy: EnemyStats,
    element: str,
    pen_ratio_pct: float = 0.0,
    pen_flat: float = 0.0,
    mods: CombatModifiers = None,
) -> dict:
    """Formula lengkap, gabungin stat panel + combat modifiers -> non-crit & crit damage."""
    mods = mods or CombatModifiers()

    atk_combat = atk_panel * (1 + mods.atk_bonus_pct_cond / 100) + mods.atk_flat_cond
    crit_dmg_combat = crit_dmg_panel_pct + mods.crit_dmg_bonus_pct_cond

    def_mult = compute_def_mult(enemy.def_val, pen_ratio_pct, pen_flat)
    res_pct = enemy.res_pct.get(element, 0.0)
    res_mult = compute_res_mult(res_pct)

    non_crit = atk_combat * (skill_mult_pct / 100) * def_mult * res_mult
    crit = non_crit * (1 + crit_dmg_combat / 100)

    return {
        "atk_combat": atk_combat,
        "def_mult": def_mult,
        "res_mult": res_mult,
        "crit_dmg_combat_pct": crit_dmg_combat,
        "non_crit": non_crit,
        "crit": crit,
    }


# ---------------------------------------------------------------------------
# Kalibrasi ke ground truth (Miyabi vs Tyrfing L60)
# ---------------------------------------------------------------------------

def run_calibration():
    textmap = load_textmap()
    weapon_talent = load_json("WeaponTalentTemplateTb.json")
    wt_rows = weapon_talent[list(weapon_talent.keys())[0]] if len(weapon_talent) == 1 else weapon_talent

    # --- W-Engine passive: Fusion Compiler (14118), phase 1 (S1) ---
    passive_row = get_weapon_passive_row(wt_rows, weapon_id=14118, phase=1)
    passive = parse_weapon_passive(passive_row, textmap)
    print("=== W-Engine Passive: Fusion Compiler S1 ===")
    print(f"  Title: {passive['title']}")
    print(f"  Unconditional bonuses (auto-parsed): {passive['unconditional_bonuses']}")
    print(f"  Full text: {passive['desc'][:80]}...")
    print()

    # --- Set 4pc: Branch & Blade Song (suit 32700) ---
    set_text = get_set_bonus_text(32700, textmap)
    four_pc_bonuses = parse_4pc_unconditional(set_text["4pc"])
    print("=== Set 4pc: Branch & Blade Song ===")
    print(f"  2pc: {set_text['2pc']}")
    print(f"  4pc text: {set_text['4pc']}")
    print(f"  4pc auto-parsed unconditional bonuses: {four_pc_bonuses}")
    print("  NOTE: '+30% CRIT DMG when Anomaly Mastery >= 115' itu kondisional")
    print("        stat-threshold, BUKAN pure unconditional -- regex simple ini")
    print("        nggak nangkep syarat AM>=115-nya, cuma nangkep angkanya.")
    print("        Utk kalibrasi ini, syaratnya kepenuhi (AM Miyabi = 116).")
    print()

    # --- Gabungin ke CombatModifiers, pake data dari wengine.md ---
    # Fusion Compiler S1: +12% ATK unconditional
    # B&BS 4pc: +30% CRIT DMG (kondisional AM>=115, terpenuhi di kasus ini)
    mods = CombatModifiers(
        atk_bonus_pct_cond=12.0,
        crit_dmg_bonus_pct_cond=30.0,
    )

    enemy = EnemyStats(
        def_val=572,
        res_pct={"Physical": 0.0, "Fire": 0.0, "Ice": -0.20, "Electric": 0.0,
                  "Ether": -0.20, "Wind": 0.0},
    )

    result = compute_final_damage(
        atk_panel=2715.64,
        skill_mult_pct=54.4,       # Kazahana hit-1
        crit_dmg_panel_pct=142.8,  # CRIT DMG panel Miyabi
        enemy=enemy,
        element="Physical",
        pen_ratio_pct=24.0,
        pen_flat=18,
        mods=mods,
    )

    print("=== Kalibrasi: Miyabi Kazahana hit-1 vs Tyrfing L60 ===")
    print(f"  ATK combat: {result['atk_combat']:.2f}")
    print(f"  DEF mult: {result['def_mult']:.5f}")
    print(f"  RES mult: {result['res_mult']:.2f}")
    print(f"  CRIT DMG combat: {result['crit_dmg_combat_pct']:.1f}%")
    print(f"  Non-crit: {result['non_crit']:.1f}  (ground truth: 1086)")
    print(f"  Crit:     {result['crit']:.1f}  (ground truth: 2961)")
    print()
    print(f"  Selisih non-crit: {abs(result['non_crit'] - 1086):.2f} "
          f"({abs(result['non_crit'] - 1086)/1086*100:.3f}%)")
    print(f"  Selisih crit: {abs(result['crit'] - 2961):.2f} "
          f"({abs(result['crit'] - 2961)/2961*100:.3f}%)")


if __name__ == "__main__":
    run_calibration()
