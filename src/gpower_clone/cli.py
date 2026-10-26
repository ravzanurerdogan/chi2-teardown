"""İnce CLI katmanı: argv -> sözlük -> engine.execute -> tek satır JSON.

JSON üretimi ve hata dönüşümü `run_params` / `run` içinde tek yerdedir; MCP sunucusu
(src/mcp_server.py) aynı `run_params` fonksiyonunu kullanır, böylece iki yolun çıktısı birebir aynıdır.
"""
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


def _guarded(compute) -> tuple[int, str]:
    """compute() bir JSON metni döndürür. İstisnalar hata JSON'una çevrilir.

    Dönüş: (çıkış kodu, stdout'a yazılacak tek satır JSON; satır sonu hariç).
    """
    try:
        return 0, compute()
    except GPowerError as e:
        return e.exit_code, json.dumps(e.to_dict())
    except Exception as e:  # beklenmeyen durum: çıkış kodu 1
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1, json.dumps({"error": f"Beklenmeyen iç hata: {e}", "code": "INTERNAL"})


def run_params(params: dict) -> tuple[int, str]:
    """Ham metin değerli alan sözlüğünü motora verir (CLI ve MCP ortak yolu)."""
    return _guarded(lambda: json.dumps(execute(params)))


def run(argv: list) -> tuple[int, str]:
    """argv'yi çalıştırır; (çıkış kodu, tek satır JSON) döner."""
    def compute() -> str:
        if argv == ["--version"]:
            return json.dumps(_version())
        return json.dumps(execute(parse_args(argv)))

    return _guarded(compute)


def main(argv: list | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    code, line = run(argv)
    print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
