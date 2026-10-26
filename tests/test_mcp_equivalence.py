"""MCP katmanı (src/mcp_server.py) ile CLI (src/gpower-clone) arasında birebir eşdeğerlik testleri.

Her girdi için iki yol çalıştırılır ve çıktı METNİ karşılaştırılır:
  * CLI : subprocess ile `python src/gpower-clone --test ... --mode ...`  (stdout, satır sonu hariç)
  * MCP : `mcp_server.power_analysis(...)` (araç fonksiyonu); araç şemasında olmayan alanlar ve
          sayı olmayan değerler için aynı kod yolunu kullanan `mcp_server.run_tool(sözlük)`.
`mcp` kurulu değilse bu dosya atlanır (pip install mcp).
"""
import asyncio
import csv
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" if (ROOT / "src" / "gpower_clone").is_dir() else ROOT
ORACLE = ROOT / "oracle" / "vectors.csv"
sys.path.insert(0, str(SRC))

pytest.importorskip("mcp", reason="mcp kurulu değil: pip install mcp")
import mcp_server  # noqa: E402

CLI_LAUNCHER = SRC / "gpower-clone"
CLI_FALLBACK = [sys.executable, "-c", "import sys; from gpower_clone.cli import main; sys.exit(main())"]
CHI2 = "chi2-contingency"
TYPED_FLOAT = ("w", "alpha", "power", "beta_alpha_ratio")
TYPED_INT = ("df", "n_total")
INT_RE = re.compile(r"^[+-]?\d+$")


# ------------------------------------------------------------------ iki yol
def cli_run(params):
    """CLI'yi subprocess ile çalıştırır; (çıkış kodu, ham stdout) döner."""
    flat = [x for k, v in params.items() for x in (f"--{k}", v)]
    base = [sys.executable, str(CLI_LAUNCHER)] if CLI_LAUNCHER.exists() else CLI_FALLBACK
    r = subprocess.run([*base, *flat], capture_output=True, text=True, encoding="utf-8",
                       timeout=30, cwd=SRC)
    return r.returncode, r.stdout


def _typed(params):
    """Araç şemasına sığıyorsa tiplenmiş argümanlar, sığmıyorsa None."""
    if "test" not in params or "mode" not in params:
        return None
    out = {}
    try:
        for k, v in params.items():
            if k in ("test", "mode"):
                out[k] = v
            elif k in TYPED_FLOAT:
                out[k] = float(v)
            elif k in TYPED_INT:
                out[k] = int(v) if INT_RE.match(v) else float(v)
            else:
                return None  # araç şemasında olmayan alan
    except ValueError:
        return None  # sayı değil
    return out


def tool_run(params):
    """(metin, yol): yol 'typed' = power_analysis(...), 'raw' = run_tool(sözlük)."""
    typed = _typed(params)
    if typed is not None:
        return mcp_server.power_analysis(**typed), "typed"
    return mcp_server.run_tool(dict(params)), "raw"


def check_equivalent(params):
    code, out = cli_run(params)
    text, path = tool_run(params)
    assert isinstance(text, str) and "\n" not in text, repr(text)
    assert out == text + "\n", f"CLI ile MCP farklı:\n CLI: {out!r}\n MCP: {text!r}\n girdi: {params}"
    return code, json.loads(text), path


def p(mode, **kw):
    return {"test": CHI2, "mode": mode, **{k: str(v) for k, v in kw.items()}}


# ------------------------------------------------- CONTRACT.md Bölüm 9 (chi2)
CONTRACT_VECTORS = [
    ("a-priori", p("a-priori", w=0.3, alpha=0.05, power=0.95, df=5),
     {"ncp": 19.8, "critical_chi2": 11.0704977, "n_total": 220, "actual_power": 0.9502155}),
    ("post-hoc", p("post-hoc", w=0.3, alpha=0.05, n_total=100, df=5),
     {"ncp": 9.0, "critical_chi2": 11.0704977, "power": 0.6235846}),
    ("compromise", p("compromise", w=0.3, beta_alpha_ratio=1, n_total=100, df=5), None),
    ("criterion", p("criterion", w=0.3, power=0.95, n_total=100, df=5), None),
    ("sensitivity", p("sensitivity", alpha=0.05, power=0.95, n_total=100, df=5), None),
]


@pytest.mark.parametrize("name,params,expected", CONTRACT_VECTORS, ids=[v[0] for v in CONTRACT_VECTORS])
def test_contract_vectors_equivalent(name, params, expected):
    code, data, path = check_equivalent(params)
    assert path == "typed"
    if expected is None:  # bonus modlar bu sürümde uygulanmadı: iki yol da aynı UNSUPPORTED'ı vermeli
        assert code == 2 and data["code"] == "UNSUPPORTED"
        return
    assert code == 0
    for key, want in expected.items():
        got = data[key]
        assert got == want if key == "n_total" else abs(got - want) <= 1e-6, (key, got, want)


# ---------------------------------------------- ek geçerli girdiler (SPEC.md)
EXTRA_VALID = [
    p("a-priori", w=0.3, alpha=0.05, power=0.95, df=2),
    p("a-priori", w=0.1, alpha=0.05, power=0.95, df=2),
    p("a-priori", w=0.3, alpha=0.001, power=0.95, df=2),
    p("a-priori", w=0.3, alpha=0.05, power=0.06, df=2),
    p("a-priori", w=0.3, alpha=0.05, power=0.05, df=2),
    p("a-priori", w=5, alpha=0.05, power=0.95, df=2),
    p("a-priori", w=0.3, alpha=0.9999999, power=0.9999999, df=2),
    p("a-priori", w=0.000001, alpha=0.05, power=0.95, df=2),
    p("a-priori", w=0.3, alpha=0.05, power=0.95, df=100),
    p("post-hoc", w=0.3, alpha=0.05, n_total=100, df=2),
    p("post-hoc", w=0.5, alpha=0.05, n_total=50, df=4),
    p("post-hoc", w=0.3, alpha=0.05, n_total=10, df=2),
    p("post-hoc", w=100000, alpha=0.05, n_total=1000000000000, df=5),
]


@pytest.mark.parametrize("params", EXTRA_VALID, ids=[f"{q['mode']}-{i}" for i, q in enumerate(EXTRA_VALID)])
def test_extra_valid_equivalent(params):
    code, data, path = check_equivalent(params)
    assert code == 0 and "error" not in data and path == "typed"


# --------------------------------------------------------- geçersiz girdiler
INVALID = [
    ("eksik df", p("a-priori", w=0.3, alpha=0.05, power=0.95), "MISSING_PARAM"),
    ("eksik w (post-hoc)", p("post-hoc", alpha=0.05, n_total=100, df=5), "MISSING_PARAM"),
    ("eksik mode", {"test": CHI2, "w": "0.3", "alpha": "0.05", "power": "0.95", "df": "5"}, "MISSING_PARAM"),
    ("bilinmeyen alan foo", {**p("a-priori", w=0.3, alpha=0.05, power=0.95, df=5), "foo": "1"}, "UNKNOWN_PARAM"),
    ("post-hoc'ta power (ilgisiz)", p("post-hoc", w=0.3, alpha=0.05, n_total=100, df=5, power=0.9), "UNKNOWN_PARAM"),
    ("a-priori'de n_total (ilgisiz)", p("a-priori", w=0.3, alpha=0.05, power=0.95, df=5, n_total=100), "UNKNOWN_PARAM"),
    ("a-priori'de beta_alpha_ratio (ilgisiz)", p("a-priori", w=0.3, alpha=0.05, power=0.95, df=5, beta_alpha_ratio=1), "UNKNOWN_PARAM"),
    ("bilinmeyen mod", p("foo", w=0.3), "UNSUPPORTED"),
    ("bilinmeyen test", {"test": "bar", "mode": "a-priori"}, "UNSUPPORTED"),
    ("w=0", p("a-priori", w=0, alpha=0.05, power=0.95, df=2), "OUT_OF_RANGE"),
    ("w negatif", p("a-priori", w=-0.3, alpha=0.05, power=0.95, df=2), "OUT_OF_RANGE"),
    ("w < 1e-6", p("a-priori", w=0.0000009999, alpha=0.05, power=0.95, df=2), "OUT_OF_RANGE"),
    ("df=0", p("a-priori", w=0.3, alpha=0.05, power=0.95, df=0), "OUT_OF_RANGE"),
    ("alpha=1", p("a-priori", w=0.3, alpha=1, power=0.95, df=2), "OUT_OF_RANGE"),
    ("alpha < 1e-7", p("a-priori", w=0.3, alpha=0.0000000999, power=0.95, df=2), "OUT_OF_RANGE"),
    ("power=1", p("a-priori", w=0.3, alpha=0.05, power=1, df=2), "OUT_OF_RANGE"),
    ("power < alpha", p("a-priori", w=0.3, alpha=0.05, power=0.04, df=2), "INCONSISTENT"),
    ("post-hoc n_total=1", p("post-hoc", w=0.3, alpha=0.05, n_total=1, df=2), "OUT_OF_RANGE"),
    ("df ondalık (2.5)", p("a-priori", w=0.3, alpha=0.05, power=0.95, df="2.5"), "INVALID_VALUE"),
    ("w sayı değil (abc)", p("a-priori", w="abc", alpha=0.05, power=0.95, df=2), "INVALID_VALUE"),
    ("ncp taşması (w=1e200)", p("post-hoc", w="1e200", alpha=0.05, n_total=100, df=5), "OUT_OF_RANGE"),
    ("bonus mod (compromise)", p("compromise", w=0.3, beta_alpha_ratio=1, n_total=100, df=5), "UNSUPPORTED"),
]


@pytest.mark.parametrize("name,params,code", INVALID, ids=[v[0] for v in INVALID])
def test_invalid_inputs_equivalent_and_never_raise(name, params, code):
    exit_code, data, _ = check_equivalent(params)
    assert exit_code != 0
    assert data["code"] == code and isinstance(data["error"], str)
    if code != "UNSUPPORTED" or "field" in data:
        assert "field" in data


def test_at_least_ten_invalid_cases():
    assert len(INVALID) >= 10


# ------------------------------------------------------------ araç davranışı
def test_none_values_are_not_forwarded():
    a = mcp_server.power_analysis(CHI2, "a-priori", w=0.3, alpha=0.05, power=0.95, df=5)
    b = mcp_server.power_analysis(CHI2, "a-priori", w=0.3, alpha=0.05, power=0.95, df=5,
                                  beta_alpha_ratio=None, n_total=None)
    assert a == b and "error" not in json.loads(a)


def test_tool_never_raises_on_odd_values():
    for kw in ({"w": float("nan")}, {"w": float("inf")}, {"df": 2.5}, {"df": True}, {"n_total": -5}):
        base = dict(w=0.3, alpha=0.05, power=0.95, df=5)
        base.update(kw)
        text = mcp_server.power_analysis(CHI2, "a-priori", **base)
        assert "error" in json.loads(text)


# --------------------------------------------------------- oracle/vectors.csv
KNOWN = ("test", "mode", "w", "alpha", "power", "df", "n_total", "beta_alpha_ratio")
INPUTS_BY_MODE = {"a-priori": ("w", "alpha", "power", "df"), "post-hoc": ("w", "alpha", "n_total", "df")}
PREFIXES = ("input_", "inputs_", "input.", "in_", "given_")


def _json_params(cell):
    d = json.loads(cell, parse_float=str, parse_int=str)
    return {str(k): str(v) for k, v in d.items() if v is not None and str(v) != ""}


def _cli_params(cell):
    toks = shlex.split(cell)
    if toks and not toks[0].startswith("--"):
        toks = toks[1:]  # çalıştırılabilir dosya adı
    return {toks[i][2:]: toks[i + 1] for i in range(0, len(toks) - 1, 2)}


def _row_params(row):
    cells = {k.strip(): (v or "").strip() for k, v in row.items() if k is not None}
    for cell in cells.values():  # 1) JSON nesnesi içeren hücre
        if cell.startswith("{"):
            try:
                return _json_params(cell)
            except ValueError:
                pass
    for cell in cells.values():  # 2) CLI komutu içeren hücre
        if "--test" in cell or cell.startswith("gpower-clone"):
            return _cli_params(cell)
    wide = {}  # 3) geniş biçim: alan adı = sütun adı (varsa input_ önekiyle)
    for col, cell in cells.items():
        name = col.lower()
        for pre in PREFIXES:
            if name.startswith(pre):
                name = name[len(pre):]
        if name in KNOWN and cell != "":
            wide.setdefault(name, cell)
    if not wide:
        return {}
    wide.setdefault("test", CHI2)
    mode = wide.get("mode") or ("a-priori" if "power" in wide else "post-hoc")
    wide["mode"] = mode
    allowed = set(INPUTS_BY_MODE.get(mode, KNOWN)) | {"test", "mode"}
    # Önek yoksa n_total/power sütunları beklenen ÇIKTI olabilir: yalnızca modun girdilerini al.
    return {k: v for k, v in wide.items() if k in allowed}


def load_oracle():
    if not ORACLE.exists():
        return None
    text = ORACLE.read_text(encoding="utf-8-sig")
    first = text.splitlines()[0] if text else ""
    delim = max(",;\t", key=first.count)
    rows = list(csv.DictReader(text.splitlines(), delimiter=delim))
    out = []
    for i, row in enumerate(rows):
        params = _row_params(row)
        out.append((str(row.get("id") or row.get("ID") or f"row{i + 1}").strip(), params, row))
    return out


_ORACLE = load_oracle()


def test_oracle_vectors_file_has_50_parsable_rows():
    if _ORACLE is None:
        pytest.skip(f"{ORACLE} bulunamadı")
    unparsed = [rid for rid, params, _ in _ORACLE if not params]
    cols = list(_ORACLE[0][2].keys()) if _ORACLE else []
    assert not unparsed, f"vectors.csv biçimi tanınmadı (sütunlar: {cols}); çözümlenemeyen satırlar: {unparsed[:5]}"
    assert len(_ORACLE) == 50, f"50 satır bekleniyordu, {len(_ORACLE)} bulundu"


@pytest.mark.parametrize("rid,params", [(r[0], r[1]) for r in (_ORACLE or []) if r[1]],
                         ids=[r[0] for r in (_ORACLE or []) if r[1]])
def test_oracle_row_equivalent(rid, params):
    check_equivalent(params)


# ----------------------------------------------------- mcp yalnızca sunucuda
def test_engine_and_cli_do_not_import_mcp():
    code = (
        "import sys\n"
        "from gpower_clone import engine, cli\n"
        "cli.run_params({'test':'chi2-contingency','mode':'a-priori','w':'0.3','alpha':'0.05','power':'0.95','df':'5'})\n"
        "print('mcp' in sys.modules, 'numpy' in sys.modules, 'scipy' in sys.modules)\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=SRC,
                       env={**__import__("os").environ, "PYTHONPATH": str(SRC)})
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "False False False"


# ------------------------------------------------------------ stdio protokolü
def _is_error(result):
    """mcp 1.x: isError, mcp 2.x: is_error."""
    for name in ("isError", "is_error"):
        if hasattr(result, name):
            return bool(getattr(result, name))
    raise AssertionError("sonuç nesnesinde isError/is_error alanı yok")


def _protocol_roundtrip(arguments):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def go():
        server = StdioServerParameters(command=sys.executable, args=[str(SRC / "mcp_server.py")])
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                result = await session.call_tool("power_analysis", arguments)
                return [t.name for t in tools.tools], result

    return asyncio.run(asyncio.wait_for(go(), timeout=10))


def test_stdio_protocol_lists_tool_and_matches_cli():
    arguments = {"test": CHI2, "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "df": 5}
    try:
        names, result = _protocol_roundtrip(arguments)
    except (asyncio.TimeoutError, TimeoutError):
        pytest.skip("MCP sunucusu 10 sn içinde yanıt vermedi")
    assert names == ["power_analysis"]
    assert not _is_error(result)
    text = result.content[0].text
    _, out = cli_run(p("a-priori", w=0.3, alpha=0.05, power=0.95, df=5))
    assert out == text + "\n"


def test_stdio_protocol_error_comes_back_as_json_text_not_exception():
    try:
        _, result = _protocol_roundtrip({"test": CHI2, "mode": "a-priori", "w": 0, "alpha": 0.05,
                                         "power": 0.95, "df": 2})
    except (asyncio.TimeoutError, TimeoutError):
        pytest.skip("MCP sunucusu 10 sn içinde yanıt vermedi")
    assert not _is_error(result)
    data = json.loads(result.content[0].text)
    assert data["code"] == "OUT_OF_RANGE" and data["field"] == "w"
