#!/usr/bin/env python3
"""Standalone ZZZ stat calculator based on the Enka wrapper logic provided."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

PROP_ID_TO_NAME: dict[int, str] = {
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
}

ALL_PROPS = list({name for name in PROP_ID_TO_NAME.values()})


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class Layer:
    def __init__(self) -> None:
        self.props = {k: 0.0 for k in ALL_PROPS}

    def add(self, name: str, value: float) -> None:
        self.props[name] += value


class StatState:
    def __init__(self) -> None:
        self.layers: list[tuple[str, Layer]] = []

    def add(self, name: str, layer: Layer) -> None:
        self.layers.append((name, layer))

    def summed(self) -> Layer:
        out = Layer()
        for _, layer in self.layers:
            for key, value in layer.props.items():
                if key.startswith("SpRecover_"):
                    out.add(key, float(value))
                else:
                    out.add(key, math.floor(value))
        return out


def get_agent_data(avatar_id: int, level: int, promotion: int, core: int, avatars: Any) -> dict[str, Any]:
    excel = avatars[str(avatar_id)] if str(avatar_id) in avatars else avatars[avatar_id]
    layer_base: dict[int, float] = {int(k): float(v) for k, v in excel["BaseProps"].items()}
    layer_growth: dict[int, float] = {int(k): float(v) for k, v in excel.get("GrowthProps", {}).items()}
    promo_row = excel.get("PromotionProps", [])[promotion - 1] if excel.get("PromotionProps") else {}
    layer_promo: dict[int, float] = {int(k): float(v) for k, v in promo_row.items()}
    core_rows = excel.get("CoreEnhancementProps", [])
    core_row = core_rows[core] if core < len(core_rows) else {}
    layer_core: dict[int, float] = {int(k): float(v) for k, v in core_row.items()}
    return {
        "id": avatar_id, "level": level, "promotion": promotion, "core": core,
        "specialty": excel.get("ProfessionType"),
        "base": layer_base, "growth": layer_growth,
        "promotion_props": layer_promo, "core_props": layer_core,
    }


def property_name(prop_id: int) -> str:
    return PROP_ID_TO_NAME[prop_id]


def make_character_layer(agent: dict[str, Any]) -> Layer:
    out = Layer()
    level = int(agent["level"])
    base = agent["base"]
    growth = agent.get("growth", {})
    promo = agent.get("promotion_props", {})
    for prop_id, base_value in base.items():
        computed = base_value + (growth.get(prop_id, 0) / 10000.0) * (level - 1) + promo.get(prop_id, 0)
        out.add(property_name(prop_id), computed)
    return out


def make_core_layer(agent: dict[str, Any]) -> Layer:
    out = Layer()
    for prop_id, value in agent.get("core_props", {}).items():
        out.add(property_name(prop_id), value)
    return out


def make_weapon_layer(api_agent: dict[str, Any], weapons: dict[str, Any], weapon_level_rows, weapon_star_rows) -> Layer:
    w = api_agent["Weapon"]
    weapon_id = int(w["Id"])
    data = weapons[str(weapon_id)]
    rarity = int(data["Rarity"])
    lvl = int(w["Level"])
    break_level = int(w["BreakLevel"])
    level_row = next(r for r in weapon_level_rows if r["Rarity"] == rarity and r["Level"] == lvl)
    star_row = next(r for r in weapon_star_rows if r["Rarity"] == rarity and r["BreakLevel"] == break_level)

    out = Layer()
    main = data["MainStat"]
    sub = data["SecondaryStat"]
    main_value = math.floor(main["PropertyValue"] * (1 + level_row["EnhanceRate"] / 10000 + star_row["StarRate"] / 10000))
    sub_value = math.floor(sub["PropertyValue"] * (1 + star_row["RandRate"] / 10000))
    out.add(property_name(int(main["PropertyId"])), main_value)
    out.add(property_name(int(sub["PropertyId"])), sub_value)
    return out


def make_disc_layer(avatar: dict[str, Any], equipments: dict[str, Any], equipment_level_rows) -> Layer:
    out = Layer()
    for equip in avatar.get("EquippedList", []):
        disc = equip["Equipment"]
        disc_id = str(disc["Id"])
        disc_meta = equipments["Items"][disc_id]
        rarity = int(disc_meta["Rarity"])
        lvl = int(disc["Level"])
        level_row = next(r for r in equipment_level_rows if r["Rarity"] == rarity and r["Level"] == lvl)
        main = disc["MainPropertyList"][0]
        main_value = math.floor(main["PropertyValue"] * (1 + level_row["EnhanceRate"] / 10000))
        out.add(property_name(int(main["PropertyId"])), main_value)
        for sub in disc["RandomPropertyList"]:
            value = sub["PropertyValue"] * sub["PropertyLevel"]
            out.add(property_name(int(sub["PropertyId"])), value)
    return out


def make_set_layer(avatar: dict[str, Any], equipments: dict[str, Any]) -> Layer:
    counts: defaultdict[int, int] = defaultdict(int)
    for equip in avatar.get("EquippedList", []):
        disc = equip["Equipment"]
        sid = int(equipments["Items"][str(disc["Id"])]["SuitId"])
        counts[sid] += 1
    out = Layer()
    for sid, count in counts.items():
        if count < 2:
            continue
        bonus_props = equipments["Suits"][str(sid)].get("SetBonusProps", {})
        for prop_id, value in bonus_props.items():
            out.add(property_name(int(prop_id)), value)
    return out


def apply_corrections(agent: dict[str, Any], state: StatState) -> None:
    """Rupture specialty agents (e.g. Yixuan) convert part of ATK and HP
    into a separate 'Sheer Force' stat used for their damage instead of ATK.
    Formula: SkipDefAtk_Delta += floor(ATK * 0.3) + floor(HP * 0.1)
    """
    base = state.summed()
    if str(agent.get("specialty", "")).lower() == "rupture":
        atk = math.floor(base.props["Atk_Base"] * (1 + base.props["Atk_Ratio"] / 10000) + base.props["Atk_Delta"])
        hp = math.floor(base.props["HpMax_Base"] + math.ceil(base.props["HpMax_Base"] * base.props["HpMax_Ratio"] / 10000) + base.props["HpMax_Delta"])
        layer = Layer()
        layer.add("SkipDefAtk_Delta", math.floor(atk * 0.3))
        layer.add("SkipDefAtk_Delta", math.floor(hp * 0.1))
        state.add("Corrections", layer)


def prop(layer: Layer, name: str) -> float:
    return layer.props[name]


def final_stats(s: Layer) -> dict[str, float]:
    return {
        "HP": prop(s, "HpMax_Base") + math.ceil(prop(s, "HpMax_Base") * prop(s, "HpMax_Ratio") / 10000) + prop(s, "HpMax_Delta"),
        "ATK": prop(s, "Atk_Base") * (1 + prop(s, "Atk_Ratio") / 10000) + prop(s, "Atk_Delta"),
        "DEF": prop(s, "Def_Base") * (1 + prop(s, "Def_Ratio") / 10000) + prop(s, "Def_Delta"),
        "Impact": prop(s, "BreakStun_Base") * (1 + prop(s, "BreakStun_Ratio") / 10000),
        "CRIT Rate": prop(s, "Crit_Base") + prop(s, "Crit_Delta"),
        "CRIT DMG": prop(s, "CritDmg_Base") + prop(s, "CritDmg_Delta"),
        "PEN Ratio": prop(s, "PenRatio_Base") + prop(s, "PenRatio_Delta"),
        "PEN": prop(s, "PenDelta_Base") + prop(s, "PenDelta_Delta"),
        "Anomaly Proficiency": prop(s, "ElementMystery_Base") + prop(s, "ElementMystery_Delta"),
        "Anomaly Mastery": prop(s, "ElementAbnormalPower_Base") * (1 + prop(s, "ElementAbnormalPower_Ratio") / 10000) + prop(s, "ElementAbnormalPower_Delta"),
        "Sheer Force": prop(s, "SkipDefAtk_Base") + prop(s, "SkipDefAtk_Delta"),
        "Ice DMG": prop(s, "AddedDamageRatio_Ice_Base") + prop(s, "AddedDamageRatio_Ice_Delta"),
        "Ether DMG": prop(s, "AddedDamageRatio_Ether_Base") + prop(s, "AddedDamageRatio_Ether_Delta"),
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    api = load_json(base_dir / "1303558818.json")
    showcase = api["PlayerInfo"]["ShowcaseDetail"]
    avatars_list = showcase.get("AvatarList", [])

    weapons = load_json(base_dir / "weapons.json")
    equipments = load_json(base_dir / "equipments.json")
    avatars = load_json(base_dir / "avatars.json")

    wl = [{"Rarity": 4, "Level": 60, "EnhanceRate": 94090}]
    ws = [{"Rarity": 4, "BreakLevel": 5, "StarRate": 44610, "RandRate": 15000}]
    el = [{"Rarity": 4, "Level": 15, "EnhanceRate": 30000}]

    for avatar in avatars_list:
        avatar_id = int(avatar["Id"])
        agent = get_agent_data(
            avatar_id=avatar_id, level=int(avatar["Level"]),
            promotion=int(avatar["PromotionLevel"]), core=int(avatar["CoreSkillEnhancement"]),
            avatars=avatars,
        )
        state = StatState()
        state.add("Character", make_character_layer(agent))
        state.add("Core", make_core_layer(agent))
        state.add("W-Engine", make_weapon_layer(avatar, weapons, wl, ws))
        state.add("Drive Discs", make_disc_layer(avatar, equipments, el))
        state.add("Set Bonuses", make_set_layer(avatar, equipments))
        apply_corrections(agent, state)

        summed = state.summed()
        stats = final_stats(summed)

        print("-- Layer breakdown --")
        for name, layer in state.layers:
            nonzero = {k: math.floor(v) for k, v in layer.props.items() if v}
            print(f"{name}: {nonzero}")
        print()
        print("-- Final stats --")
        for name, value in stats.items():
            if name in {"CRIT Rate", "CRIT DMG", "PEN Ratio", "Ice DMG", "Ether DMG"}:
                print(f"{name:22}: {math.floor(value)/100:.1f}%")
            else:
                print(f"{name:22}: {math.floor(value):g}")


if __name__ == "__main__":
    main()