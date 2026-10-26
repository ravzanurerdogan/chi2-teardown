"""gpower-clone MCP sunucusu (stdio).  Çalıştırma:  python src/mcp_server.py

Tek araç: power_analysis. Hesap mantığı burada YOKTUR: araç, CLI ile aynı `gpower_clone.cli.run_params`
fonksiyonunu çağırır; o da `gpower_clone.engine.execute`'u çalıştırır. Bu yüzden çıktı CLI'nin
stdout'undaki tek satır JSON ile birebir aynıdır. Hata durumunda istisna fırlatılmaz; aynı hata JSON'u
({"error", "code", "field"}) metin olarak döner. Doğrulamayı tamamen motor yapar.

`mcp` paketi yalnızca bu dosyada import edilir (motor ve CLI yalnızca standart kütüphane kullanır).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # `python src/mcp_server.py` her yerden çalışsın

try:
    from mcp.server.fastmcp import FastMCP  # mcp 1.x
except ImportError:  # mcp 2.x: FastMCP, MCPServer olarak yeniden adlandırıldı (aynı arayüz)
    from mcp.server.mcpserver import MCPServer as FastMCP

from gpower_clone.cli import run_params

mcp = FastMCP("gpower-clone")


def _text(value) -> str:
    """Araç değerini CLI'nin aldığı ham metne çevirir (float -> repr: yuvarlamasız, gidiş-dönüş güvenli)."""
    if isinstance(value, float):
        return repr(value)
    return str(value)  # bool -> 'True' gibi; motor INVALID_VALUE ile reddeder


def run_tool(params: dict) -> str:
    """Ham metin değerli sözlüğü CLI ile aynı kod yolundan çalıştırır; tek satır JSON metni döner."""
    _exit_code, line = run_params(params)
    return line


@mcp.tool()
def power_analysis(
    test: str,
    mode: str,
    w: float | None = None,
    alpha: float | None = None,
    power: float | None = None,
    beta_alpha_ratio: float | None = None,
    df: int | float | None = None,
    n_total: int | float | None = None,
) -> str:
    """G*Power benzeri güç analizi (χ² olumsallık tablosu: test="chi2-contingency").

    mode "a-priori": w, alpha, power, df verilir -> ncp, critical_chi2, n_total, actual_power döner.
    mode "post-hoc": w, alpha, n_total, df verilir -> ncp, critical_chi2, power döner.
    Yalnızca verilen (null olmayan) alanlar motora iletilir; eksik, ilgisiz ya da geçersiz değerler
    {"error", "code", "field"} biçiminde bir JSON metniyle bildirilir (istisna fırlatılmaz).
    """
    candidates = (("w", w), ("alpha", alpha), ("power", power),
                  ("beta_alpha_ratio", beta_alpha_ratio), ("df", df), ("n_total", n_total))
    params = {"test": test, "mode": mode}
    params.update({name: _text(value) for name, value in candidates if value is not None})
    return run_tool(params)


if __name__ == "__main__":
    mcp.run()  # varsayılan taşıma: stdio
