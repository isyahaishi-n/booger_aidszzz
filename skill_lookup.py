"""
Skill multiplier lookup — Tahap 1, 2 & 4 dari plan wiring damage calculator.

Tahap 1: Index semua baris AvatarSkillTemplateTb.json per (avatar_id, skill_type).
Tahap 2: Given (avatar_id, skill_type, level), hitung Damage%/Daze% tiap hit
          di bawah skill_type itu, pake formula yang udah diverifikasi:
              Damage(level) = IKAABAIDFAO + (level-1) * DGHHKAHHIPM
              Daze(level)   = OMFJHOLBIKA + (level-1) * KICLLNBEAEN
Tahap 4: Nama skill bahasa Inggris via dua mekanisme:
          a) EXPLICIT (utama, baru): parse field KLPLBBJABBL di baris
             PDJMFJOFNEF==1 AvatarSkillDesTemplateTb.json -- berisi referensi
             eksplisit "{Skill:<hit_id>, Prop:1001/1002}" yang menautkan hit
             row ke section title. Coverage 91.4% hit playable. Ini resolve
             7 karakter anomali grouping (1031, 1041, ..., 1551).
          b) HEURISTIC (fallback): grouping sekuensial N-hit-per-nama.

SkillType (GLENCFMNKMF) per README hasil decode:
    0 = Basic Attack
    1 = Special Attack (EX)
    2 = Dodge
    3 = Chain Attack + Ultimate (dua hit row terpisah, satu level number)
    5 = Core Skill
    6 = Assist
"""

import json
import re
from collections import defaultdict

SKILL_TYPE_NAMES = {
    0: "Basic Attack",
    1: "Special Attack",
    2: "Dodge",
    3: "Chain Attack / Ultimate",
    5: "Core Skill",
    6: "Assist",
}


def load_skill_template(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_skill_index(skill_template: dict) -> dict:
    """Tahap 1: {avatar_id: {skill_type: [row, row, ...]}}

    avatar_id diambil dari 4 digit pertama DALBKGGEJEF (skill ID), yang
    sudah dikonfirmasi cocok sama Avatar ID di avatars.json (contoh: 1011xxx -> Anby).
    """
    index = defaultdict(lambda: defaultdict(list))
    rows = skill_template["MLOEFHJHCID"]

    for row in rows:
        skill_id = row["DALBKGGEJEF"]
        avatar_id = int(str(skill_id)[:4])
        skill_type = row["GLENCFMNKMF"]
        index[avatar_id][skill_type].append(row)

    return index


def compute_damage(row: dict, level: int) -> float:
    """Damage(level) = IKAABAIDFAO + (level-1)*DGHHKAHHIPM, in percent."""
    base = row["IKAABAIDFAO"]
    growth = row["DGHHKAHHIPM"]
    return (base + (level - 1) * growth) / 100


def compute_daze(row: dict, level: int) -> float:
    """Daze(level) = OMFJHOLBIKA + (level-1)*KICLLNBEAEN, in percent."""
    base = row["OMFJHOLBIKA"]
    growth = row["KICLLNBEAEN"]
    return (base + (level - 1) * growth) / 100


def get_skill_multipliers(index: dict, avatar_id: int, skill_type: int, level: int) -> list:
    """Returns a list of {hit_id, damage_pct, daze_pct} for every hit row
    under this avatar's skill_type, at the given level.

    Baris dengan IKAABAIDFAO=0 DAN OMFJHOLBIKA=0 di-skip -- itu slot
    placeholder/nggak kepake (dikonfirmasi lewat Miyabi SkillType 3:
    2 dari 6 baris kosong total di semua field, bukan hit sungguhan).
    """
    rows = index.get(avatar_id, {}).get(skill_type, [])
    results = []
    for row in rows:
        if row["IKAABAIDFAO"] == 0 and row["OMFJHOLBIKA"] == 0:
            continue
        results.append({
            "hit_id": row["DALBKGGEJEF"],
            "damage_pct": compute_damage(row, level),
            "daze_pct": compute_daze(row, level),
        })
    return results


def load_locs(path: str, lang: str = "en") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get(lang, {})


def load_textmap(path: str = "TextMap_ENTemplateTb.json") -> dict:
    """Load TextMap EN (flat dict {text_key: english_text}, ~411k entries).

    Key-nya langsung string deskriptif kayak 'Anbi_Skill_Normal_Title' --
    sama persis dengan isi LECKPHICFOA/DLADMENPFPD di skill template.

    Kalau `TextMap_ENOverwriteTemplateTb.json` ada di folder yang sama,
    entri-nya di-merge di atas (overwrite menang — itu tabel supplement
    buat key yang belum ada di TextMap utama, mis.
    'Remielle_Skill_FinishEx_Title').
    """
    import os
    with open(path, "r", encoding="utf-8") as f:
        textmap = json.load(f)
    overwrite_path = os.path.join(os.path.dirname(path) or ".", "TextMap_ENOverwriteTemplateTb.json")
    if os.path.exists(overwrite_path):
        with open(overwrite_path, "r", encoding="utf-8") as f:
            textmap.update(json.load(f))
    return textmap


# Referensi "{Skill:<id>, Prop:<prop>}" di field KLPLBBJABBL
_SKILL_REF_PATTERN = re.compile(r"\{Skill:(\d+),\s*Prop:(\d+)\}")


def build_explicit_name_map(des_template: dict) -> dict:
    """Tahap 4 (explicit): {hit_id: [title_key, ...]} dari KLPLBBJABBL.

    Struktur AvatarSkillDesTemplateTb.json punya 2 lapis baris:
    - PDJMFJOFNEF==0: entri skill "lengkap" (LECKPHICFOA=title key,
      DLADMENPFPD=desc key) -- dipakai get_skill_names().
    - PDJMFJOFNEF==1: baris property untuk display in-game. Baris dengan
      DLADMENPFPD berakhiran '_Title' dan KLPLBBJABBL kosong = header
      section; baris berikutnya dengan KLPLBBJABBL berisi referensi
      eksplisit "{Skill:1091027, Prop:1001}" (Prop 1001=DamageRatio,
      1002=BreakStunRatio) menautkan hit_id ke section title itu.

    Hit yang TIDAK pernah direferensikan = hit tersembunyi (follow-up /
    varian enhance internal yang nggak ditampilkan di UI game) -- contoh:
    1031107-13 (Billy EX Special volley varian), 1091035 (Miyabi, 720%
    konstan). Untuk itu name=None tapi multiplier tetap valid.

    7 hit ter-map ke >1 title (varian enhance yang shared, mis.
    Astra Singing Exit/Perfect) -- disimpan semua, urutan kemunculan.
    """
    hit_titles = defaultdict(list)
    current_title = None
    for row in des_template["MLOEFHJHCID"]:
        if row.get("PDJMFJOFNEF") != 1:
            continue
        desc_key = row.get("DLADMENPFPD") or ""
        if desc_key.endswith("_Title") and not row.get("KLPLBBJABBL"):
            current_title = desc_key
            continue
        for skill_id, _prop in _SKILL_REF_PATTERN.findall(row.get("KLPLBBJABBL") or ""):
            titles = hit_titles[int(skill_id)]
            if current_title not in titles:
                titles.append(current_title)
    return dict(hit_titles)


def resolve_title(title_key: str, textmap: dict) -> str:
    """Title key -> English text; fallback ke key mentah kalau ga ketemu."""
    return textmap.get(title_key, title_key)


def get_skill_names(des_template: dict, avatar_id: int, skill_type: int) -> list:
    """Tahap 4 (partial): nama sub-skill non-kosong di bawah avatar+skill_type.
    Cuma reliable kalau jumlah nama == jumlah hit row (contoh: SkillType 3
    selalu 2 nama = Chain Attack + Ultimate). Untuk skill_type dengan hit
    row lebih banyak dari nama (misal Basic Attack 11 hit vs 2 nama), ini
    TIDAK dijamin urutannya cocok 1:1 ke hit row — masih perlu decode field
    lain (PDJMFJOFNEF/ACOLKGPPGKK/ONMHBHPOLHI) buat presisi penuh.
    """
    rows = des_template["MLOEFHJHCID"]
    names = [
        r["LECKPHICFOA"] for r in rows
        if r["PJABHBNCJOI"] == avatar_id and r["GLENCFMNKMF"] == skill_type
        and r["LECKPHICFOA"]
    ]
    return names


def compute_damage_output(index: dict, avatar_id: int, skill_type: int, level: int,
                           atk: float, des_template: dict = None, loc: dict = None,
                           name_map: dict = None, textmap: dict = None) -> list:
    """Tahap 3: gabungin multiplier ke ATK final -> raw damage per hit.
    Tahap 4: kasih nama.

    Prioritas naming:
    1. EXPLICIT name_map (dari build_explicit_name_map) + textmap --
       referensi eksplisit KLPLBBJABBL, coverage 91.4% hit playable.
       Ini juga yang resolve 7 karakter anomali grouping.
    2. HEURISTIC lama: kalau jumlah_hit % jumlah_nama == 0, grup hit
       berurutan ke tiap nama (inferensi, hanya reliable untuk kasus
       1 hit/nama).
    3. name=None -- hit tersembunyi / nggak bisa dipastikan. Angka
       multiplier tetap valid.

    Hit tanpa referensi eksplisis diberi flag is_hidden=True (follow-up
    internal yang tidak tampil di UI game).
    """
    multipliers = get_skill_multipliers(index, avatar_id, skill_type, level)

    # --- explicit naming ---
    explicit_names = {}
    if name_map is not None:
        for i, m in enumerate(multipliers):
            titles = name_map.get(m["hit_id"])
            if titles:
                if textmap is not None:
                    explicit_names[i] = " / ".join(resolve_title(t, textmap) for t in titles)
                else:
                    explicit_names[i] = " / ".join(titles)

    # --- heuristic fallback (hanya untuk hit yang belum kena explicit) ---
    heuristic_names = {}
    hits_per_name = 1
    if des_template is not None:
        candidate_names = get_skill_names(des_template, avatar_id, skill_type)
        unnamed_count = len(multipliers) - len(explicit_names)
        if candidate_names and unnamed_count > 0 and unnamed_count % len(candidate_names) == 0:
            hits_per_name = unnamed_count // len(candidate_names)
            unnamed_idx = 0
            for i, m in enumerate(multipliers):
                if i in explicit_names:
                    continue
                name_idx = unnamed_idx // hits_per_name
                hit_in_group = unnamed_idx % hits_per_name
                key = candidate_names[name_idx]
                base_name = loc.get(key, key) if loc is not None else key
                heuristic_names[i] = (
                    base_name if hits_per_name == 1
                    else f"{base_name} (hit {hit_in_group + 1}/{hits_per_name})"
                )
                unnamed_idx += 1

    results = []
    for i, m in enumerate(multipliers):
        if i in explicit_names:
            name, is_hidden = explicit_names[i], False
        elif i in heuristic_names:
            name, is_hidden = heuristic_names[i], False
        else:
            name, is_hidden = None, True
        results.append({
            "hit_id": m["hit_id"],
            "name": name,
            "is_hidden": is_hidden,
            "damage_pct": m["damage_pct"],
            "daze_pct": m["daze_pct"],
            "raw_damage": atk * m["damage_pct"] / 100,
        })
    return results


def main():
    skill_template = load_skill_template("AvatarSkillTemplateTb.json")
    index = build_skill_index(skill_template)
    des_template = load_skill_template("AvatarSkillDesTemplateTb.json")
    name_map = build_explicit_name_map(des_template)
    textmap = load_textmap()

    print(f"Indexed {len(index)} avatars, explicit name map: {len(name_map)} hit ids.")

    print()
    print("=" * 60)
    print("TEST 1: Anby (1011), SkillType 3 (Chain Attack / Ultimate), Level 12")
    print("=" * 60)
    results = compute_damage_output(index, avatar_id=1011, skill_type=3, level=12,
                                    atk=2000, name_map=name_map, textmap=textmap)
    for r in results:
        print(f"  {r['name']}: DMG {r['damage_pct']:.1f}%  |  Daze {r['daze_pct']:.1f}%")
    print("Expected (verified ke Prydwen):")
    print("  Chain Attack: DMG 1085.8%  |  Daze 216.0%")
    print("  Ultimate:     DMG 3026.2%  |  Daze 1487.7%")

    print()
    print("=" * 60)
    print("TEST 2: Miyabi (1091) charge attack (Shimotsuki), Level 1 vs 12")
    print("=" * 60)
    for lvl in (1, 12):
        results = get_skill_multipliers(index, avatar_id=1091, skill_type=0, level=lvl)
        print(f"  Level {lvl}:")
        for r in results:
            titles = name_map.get(r["hit_id"])
            name = resolve_title(titles[0], textmap) if titles else "(hidden)"
            print(f"    {r['hit_id']}  {name:45s} DMG {r['damage_pct']:7.1f}%  Daze {r['daze_pct']:7.1f}%")
    print("Expected (verified ke wiki):")
    print("  1091027 Charge Lv.1: LV1 454.7%  / LV12 910.1%")
    print("  1091028 Charge Lv.2: LV1 858.1%  / LV12 1717.2%")
    print("  1091029 Charge Lv.3: LV1 2141.1% / LV12 4282.8%")

    print()
    print("=" * 60)
    print("TEST 3: Anomali grouping 1551 (7 hit / 2 nama basic attack), Lv 12")
    print("=" * 60)
    results = compute_damage_output(index, avatar_id=1551, skill_type=0, level=12,
                                    atk=2000, name_map=name_map, textmap=textmap)
    for r in results:
        hidden = " [HIDDEN]" if r["is_hidden"] else ""
        print(f"  {r['hit_id']}  {str(r['name']):50s} DMG {r['damage_pct']:7.1f}%{hidden}")
    print("  -> anomali lama (7 % 2 != 0) sekarang ter-resolve explicit:")

    print()
    print("=" * 60)
    print("TEST 4: Hidden hits Billy (1031) EX Special, Lv 12")
    print("=" * 60)
    results = compute_damage_output(index, avatar_id=1031, skill_type=1, level=12,
                                    atk=2000, name_map=name_map, textmap=textmap)
    for r in results:
        hidden = " [HIDDEN]" if r["is_hidden"] else ""
        print(f"  {r['hit_id']}  {str(r['name']):50s} DMG {r['damage_pct']:7.1f}%{hidden}")


if __name__ == "__main__":
    main()
