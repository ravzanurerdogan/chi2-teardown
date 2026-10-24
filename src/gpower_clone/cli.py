"""İnce CLI katmanı: argv -> sözlük -> engine.execute -> tek satır JSON."""
from __future__ import annotations

import json
import sys

from .engine import GPowerError, execute

CONTRACT_VERSION = "1.0.0"
TEAM_NAME = "takim-adi"  # TODO: takım adınızı yazın


def _version() -> dict:
    py = ".".join(str(x) for x in sys.version_info[:3])
    return {"contract_version": CONTRACT_VERSION, "name": TEAM_NAME,
            "engine": f"python {py} (yalnizca standart kutuphane)"}


def parse_args(argv: list) -> dict:
    """`--alan değer` çiftlerini sözlüğe çevirir. Değer olarak '-0.3' gibi negatif sayılar geçerlidir."""
    params: dict = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--") or len(tok) == 2:
            raise GPowerError("UNKNOWN_PARAM", f"Beklenmeyen argüman: {tok!r}", tok)
        name = tok[2:]
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            raise GPowerError("INVALID_VALUE", f"--{name} için değer verilmedi", name)
        if name in params:
            raise GPowerError("INVALID_VALUE", f"--{name} birden fazla kez verildi", name)
        params[name] = argv[i + 1]
        i += 2
    return params


def main(argv: list | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        if argv == ["--version"]:
            print(json.dumps(_version()))
            return 0
        print(json.dumps(execute(parse_args(argv))))
        return 0
    except GPowerError as e:
        print(json.dumps(e.to_dict()))
        return e.exit_code
    except Exception as e:  # beklenmeyen durum: çıkış kodu 1
        import traceback

        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"error": f"Beklenmeyen iç hata: {e}", "code": "INTERNAL"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
