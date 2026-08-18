python zzz_enka_stat_calc_multichar.py --api 1303558818.json --avatars avatars.json

Add `--with-conditional` to also count Mindscape buffs that need a combat trigger.

## Output

For every agent in the showcase the script prints:

- Name, rank / element / specialty, Level, Promotion, Mindscape (M0-M6), Core Skill (A-F)
- Equipped W-Engine: name, rank, level, phase, mod level
- Drive Disc set summary plus per-slot detail (set name, rank, +level, main stat, each sub stat with roll count)
- Unlocked Mindscape nodes, each tagged `[in stats]`, `[conditional - not in stats]`, `[not in stats]`, or `(skill Lv. +2)`
- Skill levels as reported by Enka, plus a footnote for the odd-Mindscape bonus (see below)

- Layer breakdown (Character / Core / Mindscape / W-Engine / Drive Discs / Set Bonuses / Corrections) and the final stat sheet

## Mindscapes

`mindscapes.json` (built by `extract.py` from the EN text map) is **display text only** -
`title` / `desc` / `odd_level_skill_bump`, no property ids. Agent lookup uses the
`avatars.json` name suffix, e.g. `Avatar_Male_Size03_PanYinhu` -> `PanYinhu`.

Descriptions are deliberately **not** regex-parsed: of 174 even-level entries only 14
lack a conditional keyword, so most effects are combat-state buffs, damage multipliers,
RES ignores or stat-scaling conversions rather than stat-sheet numbers.

Instead, the numbers the calculator applies live in `mindscape_props.json`:

```json
"1091": { "2": { "props": { "20103": 1500 }, "unconditional": false,
                 "note": "CRIT Rate +15% upon entering the battlefield" } }
```

`unconditional: true` is always counted; `false` needs `--with-conditional`. Empty
`props` plus a `note` records effects that cannot be expressed as a flat stat. Odd
Mindscape levels are never added to the stat layer - they only change skill levels,
not the stat sheet.

## Skill levels: known limitation

Enka's `SkillLevelList` is the **only** source of skill levels available. Neither the
local `avatars.json` nor Enka's upstream copy ships per-agent *base* skill levels
(both expose only `BaseProps` / `GrowthProps` / `PromotionProps` /
`CoreEnhancementProps`). Two consequences:

1. **Chain Attack is missing.** Index 4 is absent from `SkillLevelList` for every
   avatar in the payload, at every Mindscape level. It is printed as
   `n/a  (not included in the Enka payload)` rather than silently skipped.
2. **The M1/M3/M5 `+2` bump cannot be split out.** An earlier version printed
   `12  (base 6 +6 from M1/M3/M5)`, which assumed the API numbers already contain
   the bump. That assumption is not supported by the data: avatar `1091` is at **M0**
   - so it has no bump at all - yet already reports Basic Attack 12 / Special Attack
   12, the trained cap. Reconstructing a "base" by subtracting the bump would invent
   numbers. The script now prints the API values verbatim and notes the bump
   separately.

Getting true `base + 2 x count(M1,M3,M5)` values needs a skill-level table from a
different data source (e.g. a game `Avatar*SkillTemplateTb` dump); there is no way to
derive them from this payload.



## Data files


| File | Purpose |
| --- | --- |
| `1303558818.json` | Enka showcase payload (agents, W-Engines, Drive Discs) |
| `avatars.json` | Agent metadata: BaseProps / GrowthProps / PromotionProps / CoreEnhancementProps |
| `weapons.json` | W-Engine metadata: Rarity, MainStat, SecondaryStat |
| `equipments.json` | Drive Disc items + suit set bonuses |
| `WeaponLevelTemplateTb.json` | W-Engine level enhance rates (rarity 2-4, Lv 0-60) |
| `WeaponStarTemplateTb.json` | W-Engine mod/star rates (rarity 2-4, BreakLevel 0-5) |
| `EquipmentLevelTemplateTb.json` | Drive Disc level enhance rates (R2 -> +9, R3 -> +12, R4 -> +15) |
| `locale_en.json` | English names for agents / W-Engines / disc sets |
| `mindscapes.json` | Mindscape display text (title / desc), produced by `extract.py` |
| `mindscape_props.json` | Machine-readable Mindscape stat effects consumed by the Mindscape layer |


The `*TemplateTb.json` dumps store rows under the root key `MLOEFHJHCID` with
obfuscated field names. The script de-obfuscates them via the maps at the top of
`zzz_enka_stat_calc_multichar.py`:

```
APDCBEGPHJO = Rarity        GJGMIBEOBHP = Level
EOMOGNMMOEJ = EnhanceRate   LMBCLMNIJNA = BreakLevel
EENDAEFLEJO = StarRate      IIPAHNFIJOH = RandRate
```

Refresh `locale_en.json` (names only) with:

```
python -c "import urllib.request,json;d=json.load(urllib.request.urlopen('https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/zzz/locs.json'))['en'];json.dump({k:v for k,v in d.items() if k.startswith(('Avatar_','Item_Weapon_','EquipmentSuit_'))},open('locale_en.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)"
```
