import base64
import json
import zlib
from typing import Any, Dict, List, Optional


def decode_export_string(s: str) -> Dict[str, Any]:
    """
    Supports:
      - WPE2J|<json>
      - WPE2|<base64>  (optionally zlib-compressed json)
    """
    if not s:
        raise ValueError("Empty export string")

    s = s.strip()

    if s.startswith("WPE2J|"):
        raw = s.split("|", 1)[1].strip()
        return json.loads(raw)

    if s.startswith("WPE2|"):
        raw = s.split("|", 1)[1].strip()

        # base64 decode
        try:
            b = base64.b64decode(raw)
        except Exception as e:
            raise ValueError(f"Invalid base64 in WPE2 export: {e}")

        # try zlib decompress, fallback to plain json bytes
        try:
            b2 = zlib.decompress(b)
        except Exception:
            b2 = b

        try:
            return json.loads(b2.decode("utf-8", errors="replace"))
        except Exception as e:
            raise ValueError(f"Invalid JSON after decode: {e}")

    raise ValueError("Unsupported export prefix (expected WPE2J| or WPE2|)")


def _sum_talent_points(tab: Dict[str, Any]) -> int:
    pts = 0
    for t in tab.get("talents", []) or []:
        try:
            pts += int(t.get("rank") or 0)
        except Exception:
            pass
    return pts


def _infer_spec(character: Dict[str, Any]) -> Optional[str]:
    talents = character.get("talents") or {}
    tabs: List[Dict[str, Any]] = talents.get("tabs") or []
    if not tabs:
        return None

    best_icon = None
    best_pts = -1
    for tab in tabs:
        pts = _sum_talent_points(tab)
        icon = tab.get("icon")  # e.g. "Fury"
        if pts > best_pts and icon:
            best_pts = pts
            best_icon = icon

    return best_icon


def _infer_role(class_file: str, spec: Optional[str]) -> str:
    cf = (class_file or "").upper()
    sp = (spec or "").lower()

    # very simple and practical mapping
    if cf == "WARRIOR":
        return "Tank" if sp == "protection" else "DPS"
    if cf == "PALADIN":
        if sp == "holy":
            return "Heal"
        if sp == "protection":
            return "Tank"
        return "DPS"
    if cf == "PRIEST":
        return "DPS" if sp == "shadow" else "Heal"
    if cf == "DRUID":
        if sp == "restoration":
            return "Heal"
        if sp == "feral":
            return "Tank"  # could be DPS too, but Tank is more useful default
        return "DPS"
    if cf == "SHAMAN":
        return "Heal" if sp == "restoration" else "DPS"

    # Hunter, Rogue, Mage, Warlock => DPS
    return "DPS"


def _extract_professions(character: Dict[str, Any]) -> List[str]:
    """
    Some exports use character.professions as list of strings,
    others list of dicts. We handle both.
    """
    profs = character.get("professions")
    if not profs:
        return []

    out: List[str] = []
    if isinstance(profs, list):
        for p in profs:
            if isinstance(p, str):
                if p.strip():
                    out.append(p.strip())
            elif isinstance(p, dict):
                name = (p.get("name") or "").strip()
                if name:
                    out.append(name)
    return out


def summarize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    meta = payload.get("meta") or {}
    character = payload.get("character") or {}
    core = character.get("core") or {}

    core_class = core.get("class") or {}
    core_race = core.get("race") or {}

    name = core.get("name")
    guid = core.get("guid")
    realm = core.get("realm")
    faction = core.get("faction")
    level = core.get("level")

    class_file = core_class.get("file") or core_class.get("name")
    race_file = core_race.get("file") or core_race.get("name")

    exported_at = meta.get("exportedAt")

    # guild name (may be missing)
    guild_name = None
    guild = payload.get("guild") or {}
    if isinstance(guild, dict):
        guild_name = guild.get("name") or None

    # infer spec + role
    spec = _infer_spec(character)
    role = _infer_role(str(class_file or ""), spec)

    professions = _extract_professions(character)

    return {
        "guid": guid,
        "name": name,
        "realm": realm,
        "level": level,
        "classFile": class_file,
        "raceFile": race_file,
        "faction": faction,
        "guildName": guild_name,
        "exportedAt": exported_at,

        # extra fields used by /api/import mirror into players
        "spec": spec,
        "role": role,
        "professions": professions,
        "language": (meta.get("locale") or "DE").replace("enUS", "EN").replace("deDE", "DE"),
    }
