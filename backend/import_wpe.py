import base64
import json
import zlib

def _inflate(data: bytes) -> str:
    # Erst normales zlib, dann raw deflate
    try:
        return zlib.decompress(data).decode("utf-8")
    except Exception:
        return zlib.decompress(data, -zlib.MAX_WBITS).decode("utf-8")

def decode_export_string(export_string: str) -> dict:
    if not isinstance(export_string, str) or len(export_string) < 10:
        raise ValueError("exportString invalid")

    if export_string.startswith("WPE2J|"):
        json_text = export_string[len("WPE2J|"):]
        return json.loads(json_text)

    if export_string.startswith("WPE2|"):
        b64 = export_string[len("WPE2|"):].strip()
        compressed = base64.b64decode(b64)
        json_text = _inflate(compressed)
        return json.loads(json_text)

    raise ValueError("Unknown export prefix")

def summarize_payload(payload: dict) -> dict:
    core = (payload.get("character") or {}).get("core") or {}
    guild = ((payload.get("guild") or {}).get("summary")) or {}
    meta = payload.get("meta") or {}

    return {
        "guid": core.get("guid") or None,
        "name": core.get("name") or "",
        "realm": core.get("realm") or "",
        "level": core.get("level"),
        "classFile": ((core.get("class") or {}).get("file")) if isinstance(core.get("class"), dict) else None,
        "raceFile": ((core.get("race") or {}).get("file")) if isinstance(core.get("race"), dict) else None,
        "faction": core.get("faction"),
        "guildName": guild.get("name"),
        "exportedAt": meta.get("exportedAt"),
    }
