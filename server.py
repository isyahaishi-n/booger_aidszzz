#!/usr/bin/env python3
"""Local server for the ZZZ Enka showcase viewer.

Endpoints:
  GET /                  -> site/index.html
  GET /static/<file>     -> site assets
  GET /api/data          -> combined game data (avatars, weapons, discs, locale, ...)
  GET /api/uid/<uid>     -> proxies https://enka.network/api/zzz/uid/<uid>
  GET /api/local         -> bundled sample showcase (1303558818.json)
  GET /ui/zzz/<file>     -> proxies https://enka.network/ui/zzz/<file> (disk-cached)

Stdlib only - no dependencies.
"""
from __future__ import annotations

import json
import mimetypes
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SITE_DIR = BASE_DIR / "site"
CACHE_DIR = BASE_DIR / ".imgcache"
SAMPLE = BASE_DIR / "1303558818.json"
ENKA_API = "https://enka.network/api/zzz/uid/"
ENKA_UI = "https://enka.network/ui/zzz/"
UA = {"User-Agent": "Mozilla/5.0 (zzz-showcase-local/1.0)"}

# --- obfuscated template tables -------------------------------------------
TB_ROOT_KEY = "MLOEFHJHCID"

WEAPON_LEVEL_FIELDS = {
    "APDCBEGPHJO": "Rarity",
    "GJGMIBEOBHP": "Level",
    "EOMOGNMMOEJ": "EnhanceRate",
}
WEAPON_STAR_FIELDS = {
    "APDCBEGPHJO": "Rarity",
    "LMBCLMNIJNA": "BreakLevel",
    "EENDAEFLEJO": "StarRate",
    "IIPAHNFIJOH": "RandRate",
}
EQUIPMENT_LEVEL_FIELDS = {
    "APDCBEGPHJO": "Rarity",
    "GJGMIBEOBHP": "Level",
    "EOMOGNMMOEJ": "EnhanceRate",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_template_table(path: Path, field_map: dict) -> list[dict]:
    raw = load_json(path)
    rows = raw[TB_ROOT_KEY] if isinstance(raw, dict) and TB_ROOT_KEY in raw else raw
    out = []
    for row in rows:
        out.append({name: int(row[key]) for key, name in field_map.items() if key in row})
    return out


def build_game_data() -> dict:
    return {
        "avatars": load_json(BASE_DIR / "avatars.json"),
        "weapons": load_json(BASE_DIR / "weapons.json"),
        "equipments": load_json(BASE_DIR / "equipments.json"),
        "locale": load_json(BASE_DIR / "locale_en.json"),
        "mindscapes": load_json(BASE_DIR / "mindscapes.json"),
        "mindscapeProps": load_json(BASE_DIR / "mindscape_props.json"),
        "weaponLevels": load_template_table(BASE_DIR / "WeaponLevelTemplateTb.json", WEAPON_LEVEL_FIELDS),
        "weaponStars": load_template_table(BASE_DIR / "WeaponStarTemplateTb.json", WEAPON_STAR_FIELDS),
        "equipmentLevels": load_template_table(BASE_DIR / "EquipmentLevelTemplateTb.json", EQUIPMENT_LEVEL_FIELDS),
    }


GAME_DATA = None  # populated lazily on first /api/data request


def fetch(url: str, timeout: int = 25) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "application/octet-stream")


class Handler(BaseHTTPRequestHandler):
    server_version = "ZZZShowcase/1.0"

    # ---- helpers ----
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self._send(200, path.read_bytes(), ctype, {"Cache-Control": "max-age=60"})

    def log_message(self, fmt, *args) -> None:
        pass  # keep the console quiet

    # ---- routes ----
    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        try:
            if path in ("/", "/index.html"):
                self._send_file(SITE_DIR / "index.html")

            elif path.startswith("/static/"):
                rel = path[len("/static/"):]
                target = (SITE_DIR / "static" / rel).resolve()
                if not str(target).startswith(str(SITE_DIR.resolve())):
                    self._send(403, b"Forbidden", "text/plain; charset=utf-8")
                    return
                self._send_file(target)

            elif path == "/api/data":
                global GAME_DATA
                if GAME_DATA is None:
                    GAME_DATA = build_game_data()
                self._send_json(GAME_DATA)

            elif path == "/api/local":
                if SAMPLE.is_file():
                    self._send(200, SAMPLE.read_bytes(), "application/json; charset=utf-8")
                else:
                    self._send_json({"error": "no bundled sample"}, 404)

            elif path.startswith("/api/uid/"):
                uid = path[len("/api/uid/"):]
                if not re.fullmatch(r"\d{6,12}", uid):
                    self._send_json({"error": "Invalid UID"}, 400)
                    return
                try:
                    body, ctype = fetch(ENKA_API + uid)
                    self._send(200, body, ctype)
                except urllib.error.HTTPError as e:
                    msg = {404: "Player not found (check UID / showcase visibility)"}.get(
                        e.code, f"Enka returned HTTP {e.code}"
                    )
                    self._send(e.code, json.dumps({"error": msg}).encode("utf-8"), "application/json; charset=utf-8")
                except Exception as e:
                    self._send_json({"error": f"Could not reach enka.network: {e}"}, 502)

            elif path.startswith("/ui/zzz/"):
                name = path[len("/ui/zzz/"):]
                if not re.fullmatch(r"[\w.\-]+", name):
                    self._send(403, b"Forbidden", "text/plain; charset=utf-8")
                    return
                cache = CACHE_DIR / name
                if cache.is_file():
                    ctype = mimetypes.guess_type(str(cache))[0] or "image/png"
                    self._send(200, cache.read_bytes(), ctype, {"Cache-Control": "max-age=86400"})
                    return
                try:
                    body, ctype = fetch(ENKA_UI + name)
                    CACHE_DIR.mkdir(exist_ok=True)
                    cache.write_bytes(body)
                    self._send(200, body, ctype, {"Cache-Control": "max-age=86400"})
                except Exception:
                    self._send(404, b"Image not found", "text/plain; charset=utf-8")

            else:
                self._send(404, b"Not found", "text/plain; charset=utf-8")

        except BrokenPipeError:
            pass
        except Exception as e:
            try:
                self._send_json({"error": str(e)}, 500)
            except Exception:
                pass


def main() -> None:
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    CACHE_DIR.mkdir(exist_ok=True)
    print(f"ZZZ Showcase server running at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()