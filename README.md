python zzz_enka_stat_calc_multichar.py --api 1303558818.json --avatars avatars.json

## Output

For every agent in the showcase the script prints:

- Name, rank / element / specialty, Level, Promotion, Mindscape (M0-M6), Core Skill (A-F)
- Equipped W-Engine: name, rank, level, phase, mod level
- Drive Disc set summary plus per-slot detail (set name, rank, +level, main stat, each sub stat with roll count)
- Skill levels for every slot
- Layer breakdown (Character / Core / W-Engine / Drive Discs / Set Bonuses / Corrections) and the final stat sheet

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
