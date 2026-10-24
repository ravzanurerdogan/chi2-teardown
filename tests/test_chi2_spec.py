"""SPEC.md (K4, chi2-contingency) tablolarından türetilmiş testler.

Bu testler motordan (gpower_clone.engine) önce yazılmıştır. Değerler SPEC.md ve
CONTRACT.md Bölüm 9'daki tablolardan birebir alınmıştır.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# Kod ya src\ altında (gpower-chi2\src\gpower_clone) ya da proje kökünde olabilir.
SRC = ROOT / "src" if (ROOT / "src" / "gpower_clone").is_dir() else ROOT
sys.path.insert(0, str(SRC))

from gpower_clone.engine import GPowerError, execute, power  # noqa: E402

# CLI, başlatıcı dosyaya ya da __main__.py'ye bağımlı olmadan doğrudan cli.main ile çalıştırılır.
CLI = [sys.executable, "-c", "import sys; from gpower_clone.cli import main; sys.exit(main())"]
CLI_ENV = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"}


def close(a, b, tol=1e-6):
    """CONTRACT Bölüm 6: mutlak ya da göreli fark <= 1e-6."""
    diff = abs(a - b)
    return diff <= tol or diff <= tol * abs(b)


def rows(text):
    return [[c.strip() for c in line.split("|")] for line in text.strip().splitlines()]


# id | w | alpha | power | df | ncp | critical_chi2 | n_total | actual_power
A_PRIORI = rows("""
v001 | 0.3 | 0.05 | 0.95 | 2 | 15.4800000 | 5.9914645 | 172 | 0.9504692
v002 | 0.3 | 0.05 | 0.95 | 1 | 13.0500000 | 3.8414588 | 145 | 0.9507851
v003 | 0.3 | 0.05 | 0.95 | 3 | 17.1900000 | 7.8147279 | 191 | 0.9502399
v004 | 0.3 | 0.05 | 0.95 | 4 | 18.6300000 | 9.4877290 | 207 | 0.9506581
v005 | 0.1 | 0.05 | 0.95 | 2 | 15.4500000 | 5.9914645 | 1545 | 0.9500866
v006 | 0.5 | 0.05 | 0.95 | 2 | 15.5000000 | 5.9914645 | 62 | 0.9507228
v007 | 0.3 | 0.01 | 0.95 | 2 | 20.7000000 | 9.2103404 | 230 | 0.9505563
v008 | 0.3 | 0.10 | 0.95 | 2 | 13.0500000 | 4.6051702 | 145 | 0.9503684
v009 | 0.3 | 0.05 | 0.80 | 2 | 9.7200000 | 5.9914645 | 108 | 0.8036939
v010 | 0.3 | 0.05 | 0.90 | 2 | 12.6900000 | 5.9914645 | 141 | 0.9008626
v011 | 0.3 | 0.05 | 0.99 | 2 | 21.4200000 | 5.9914645 | 238 | 0.9900681
v012 | 0.3 | 0.05 | 0.95 | 6 | 20.8800000 | 12.5915872 | 232 | 0.9502375
v013 | 0.3 | 0.05 | 0.95 | 10 | 24.3900000 | 18.3070381 | 271 | 0.9500419
v014 | 0.05 | 0.05 | 0.95 | 2 | 15.4450000 | 5.9914645 | 6178 | 0.9500226
v015 | 0.01 | 0.05 | 0.95 | 2 | 15.4433000 | 5.9914645 | 154433 | 0.9500008
v016 | 0.9 | 0.05 | 0.95 | 2 | 16.2000000 | 5.9914645 | 20 | 0.9588793
v017 | 1.0 | 0.05 | 0.95 | 2 | 16.0000000 | 5.9914645 | 16 | 0.9566863
v018 | 0.3 | 0.001 | 0.95 | 2 | 27.6300000 | 13.8155106 | 307 | 0.9508431
v036 | 0.3 | 0.0000001 | 0.95 | 2 | 52.5600000 | 32.2361913 | 584 | 0.9505492
v037 | 0.3 | 0.00000011 | 0.95 | 2 | 52.2900000 | 32.0455709 | 581 | 0.9503838
v039 | 0.3 | 0.5 | 0.95 | 2 | 6.3900000 | 1.3862944 | 71 | 0.9510871
v040 | 0.3 | 0.05 | 0.9999999 | 2 | 56.7900000 | 5.9914645 | 631 | 0.9999999
v041 | 0.3 | 0.9 | 0.95 | 2 | 1.5300000 | 0.2107210 | 17 | 0.9515995
v047 | 0.3 | 0.05 | 0.95 | 100 | 56.8800000 | 124.3421134 | 632 | 0.9501569
pub | 0.3 | 0.05 | 0.95 | 5 | 19.8000000 | 11.0704977 | 220 | 0.9502155
""")

# id | w | alpha | power | n_total | ncp | critical_chi2 | actual_power   (df = 2)
SMALL_N = rows("""
v019 | 0.3 | 0.05 | 0.06 | 2 | 0.18 | 5.9914645 | 0.0637738
v020 | 0.3 | 0.05 | 0.05 | 1 | 0.09 | 5.9914645 | 0.0568148
v048 | 5 | 0.05 | 0.95 | 1 | 25.0 | 5.9914645 | 0.9964734
v049 | 0.3 | 0.95 | 0.95 | 1 | 0.09 | 0.1025866 | 0.9521454
v050 | 0.3 | 0.9999999 | 0.9999999 | 1 | 0.09 | 0.0000002 | 0.9999999
""")

# id | w | alpha | n_total | df | ncp | critical_chi2 | power
POST_HOC = rows("""
v029 | 0.3 | 0.05 | 100 | 2 | 9.0000000 | 5.9914645 | 0.7706831
v030 | 0.1 | 0.05 | 200 | 2 | 2.0000000 | 5.9914645 | 0.2255449
v031 | 0.5 | 0.05 | 50 | 4 | 12.5000000 | 9.4877290 | 0.8203819
v032 | 0.3 | 0.05 | 10 | 2 | 0.9000000 | 5.9914645 | 0.1238530
pub | 0.3 | 0.05 | 100 | 5 | 9.0000000 | 11.0704977 | 0.6235846
""")

# id | w | alpha | power | df | code | field
INVALID = rows("""
v024 | 0 | 0.05 | 0.95 | 2 | OUT_OF_RANGE | w
v025 | -0.3 | 0.05 | 0.95 | 2 | OUT_OF_RANGE | w
v033 | 0.0000005 | 0.05 | 0.95 | 2 | OUT_OF_RANGE | w
v034 | 0.0000009999 | 0.05 | 0.95 | 2 | OUT_OF_RANGE | w
v026 | 0.3 | 0.05 | 0.95 | 0 | OUT_OF_RANGE | df
v027 | 0.3 | 0 | 0.95 | 2 | OUT_OF_RANGE | alpha
v028 | 0.3 | 1 | 0.95 | 2 | OUT_OF_RANGE | alpha
v044 | 0.3 | 0.0000000999 | 0.95 | 2 | OUT_OF_RANGE | alpha
v045 | 0.3 | 0.05 | 1 | 2 | OUT_OF_RANGE | power
v046 | 0.3 | 0.05 | 0.99999999 | 2 | OUT_OF_RANGE | power
v021 | 0.3 | 0.05 | 0.04 | 2 | INCONSISTENT | power
v038 | 0.3 | 0.9999999 | 0.95 | 2 | INCONSISTENT | power
v042 | 0.3 | 0.99 | 0.95 | 2 | INCONSISTENT | power
v043 | 0.3 | 0.999999 | 0.95 | 2 | INCONSISTENT | power
""")

# w | alpha | power   (df = 2): sınırdaki değerler kabul edilir
BOUNDARY_OK = rows("""
0.000001 | 0.05 | 0.95
0.0000010001 | 0.05 | 0.95
0.3 | 0.0000001 | 0.95
0.3 | 0.05 | 0.9999999
0.3 | 0.05 | 0.05
0.3 | 0.95 | 0.95
0.3 | 0.9999999 | 0.9999999
""")


def ap(w, alpha, pw, df):
    return execute({"test": "chi2-contingency", "mode": "a-priori",
                    "w": w, "alpha": alpha, "power": pw, "df": df})


def ph(w, alpha, n, df):
    return execute({"test": "chi2-contingency", "mode": "post-hoc",
                    "w": w, "alpha": alpha, "n_total": n, "df": df})


# ---------------------------------------------------------------- a priori
@pytest.mark.parametrize("r", A_PRIORI, ids=[r[0] for r in A_PRIORI])
def test_a_priori_vectors(r):
    _id, w, alpha, pw, df, ncp, crit, n, actual = r
    out = ap(w, alpha, pw, df)
    assert out["n_total"] == int(n)
    assert isinstance(out["n_total"], int)
    assert close(out["ncp"], float(ncp))
    assert close(out["critical_chi2"], float(crit))
    assert close(out["actual_power"], float(actual))
    assert out["actual_power"] >= float(pw)


@pytest.mark.parametrize("r", A_PRIORI + [r[:4] + ["2"] + [r[5], r[6], r[4], r[7]] for r in SMALL_N],
                         ids=[r[0] for r in A_PRIORI] + [r[0] for r in SMALL_N])
def test_n_is_minimal(r):
    """n_total hedefi sağlayan en küçük pozitif tamsayıdır (N-1 sağlamaz)."""
    _id, w, alpha, pw, df, *_ = r
    out = ap(w, alpha, pw, df)
    n = out["n_total"]
    assert power(float(w), float(alpha), n, int(df)) >= float(pw)
    if n > 1:
        assert power(float(w), float(alpha), n - 1, int(df)) < float(pw)


def test_rounds_up_not_below_target():
    assert power(0.3, 0.05, 171, 2) == pytest.approx(0.9493, abs=1e-4)
    out = ap("0.3", "0.05", "0.95", "2")
    assert out["n_total"] == 172 and out["actual_power"] >= 0.95


@pytest.mark.parametrize("r", SMALL_N, ids=[r[0] for r in SMALL_N])
def test_small_n_lower_bound(r):
    _id, w, alpha, pw, n, ncp, crit, actual = r
    out = ap(w, alpha, pw, "2")
    assert out["n_total"] == int(n)
    assert close(out["ncp"], float(ncp))
    assert close(out["critical_chi2"], float(crit))
    assert close(out["actual_power"], float(actual))


def test_huge_n_fast_and_integer():
    t0 = time.perf_counter()
    out = ap("0.000001", "0.05", "0.95", "2")
    assert time.perf_counter() - t0 < 2.0
    assert isinstance(out["n_total"], int)
    assert out["n_total"] == pytest.approx(1.5443e13, rel=1e-4)
    assert close(out["ncp"], 15.4432356)
    assert close(out["critical_chi2"], 5.9914645)
    assert close(out["actual_power"], 0.95)
    out2 = ap("0.0000010001", "0.05", "0.95", "2")
    assert out2["n_total"] == pytest.approx(1.544e13, rel=1e-3)


# ----------------------------------------------------------------- post hoc
@pytest.mark.parametrize("r", POST_HOC, ids=[r[0] for r in POST_HOC])
def test_post_hoc_vectors(r):
    _id, w, alpha, n, df, ncp, crit, pw = r
    out = ph(w, alpha, n, df)
    assert close(out["ncp"], float(ncp))
    assert close(out["critical_chi2"], float(crit))
    assert close(out["power"], float(pw))


# ------------------------------------------------------------------ hatalar
@pytest.mark.parametrize("r", INVALID, ids=[r[0] for r in INVALID])
def test_invalid_inputs(r):
    _id, w, alpha, pw, df, code, field = r
    with pytest.raises(GPowerError) as ei:
        ap(w, alpha, pw, df)
    assert ei.value.code == code
    assert ei.value.field == field
    assert ei.value.exit_code == 2


@pytest.mark.parametrize("r", BOUNDARY_OK, ids=[f"{r[0]}-{r[1]}-{r[2]}" for r in BOUNDARY_OK])
def test_boundary_values_accepted(r):
    w, alpha, pw = r
    out = ap(w, alpha, pw, "2")
    assert out["n_total"] >= 1


def test_post_hoc_ranges():
    with pytest.raises(GPowerError) as ei:
        ph("0.3", "0.05", "1", "2")
    assert (ei.value.code, ei.value.field) == ("OUT_OF_RANGE", "n_total")
    with pytest.raises(GPowerError) as ei:
        ph("0.3", "0.05", "100", "0")
    assert (ei.value.code, ei.value.field) == ("OUT_OF_RANGE", "df")


# ---------------------------------------------------------------------- CLI
def run_cli(*args):
    p = subprocess.run([*CLI, *args], capture_output=True, text=True, encoding="utf-8", timeout=10, cwd=SRC, env=CLI_ENV)
    return p.returncode, p.stdout, p.stderr


PUB = ["--test", "chi2-contingency", "--mode", "a-priori", "--w", "0.3",
       "--alpha", "0.05", "--power", "0.95", "--df", "5"]


def test_cli_success_single_line_json_with_integer_n():
    code, out, _ = run_cli(*PUB)
    assert code == 0
    assert out.count("\n") == 1 and out.endswith("\n")
    assert '"n_total": 220,' in out or '"n_total":220,' in out
    d = json.loads(out)
    assert d["n_total"] == 220 and isinstance(d["n_total"], int)
    assert close(d["ncp"], 19.8) and close(d["critical_chi2"], 11.0704977)
    assert close(d["actual_power"], 0.9502155)


def test_cli_post_hoc():
    code, out, _ = run_cli("--test", "chi2-contingency", "--mode", "post-hoc", "--w", "0.3",
                           "--alpha", "0.05", "--n_total", "100", "--df", "5")
    d = json.loads(out)
    assert code == 0 and close(d["power"], 0.6235846)


def test_cli_missing_param():
    code, out, _ = run_cli(*PUB[:-2])
    d = json.loads(out)
    assert code == 2 and d["code"] == "MISSING_PARAM" and d["field"] == "df" and "error" in d


def test_cli_unrelated_param_in_post_hoc():
    code, out, _ = run_cli("--test", "chi2-contingency", "--mode", "post-hoc", "--w", "0.3",
                           "--alpha", "0.05", "--n_total", "100", "--df", "5", "--power", "0.9")
    d = json.loads(out)
    assert code == 2 and d["code"] == "UNKNOWN_PARAM" and d["field"] == "power"


def test_cli_unknown_param():
    code, out, _ = run_cli(*PUB, "--foo", "1")
    assert code == 2 and json.loads(out)["code"] == "UNKNOWN_PARAM"


def test_cli_unsupported_mode_and_test():
    code, out, _ = run_cli("--test", "chi2-contingency", "--mode", "foo")
    assert code == 2 and json.loads(out)["code"] == "UNSUPPORTED"
    code, out, _ = run_cli("--test", "bar", "--mode", "a-priori")
    assert code == 2 and json.loads(out)["code"] == "UNSUPPORTED"


def test_cli_invalid_value():
    args = list(PUB)
    args[args.index("--w") + 1] = "abc"
    code, out, _ = run_cli(*args)
    d = json.loads(out)
    assert code == 2 and d["code"] == "INVALID_VALUE" and d["field"] == "w"


def test_cli_non_integer_df():
    args = list(PUB)
    args[args.index("--df") + 1] = "2.5"
    code, out, _ = run_cli(*args)
    assert code == 2 and json.loads(out)["code"] == "INVALID_VALUE"


def test_cli_negative_value_is_a_value_not_a_flag():
    args = list(PUB)
    args[args.index("--w") + 1] = "-0.3"
    code, out, _ = run_cli(*args)
    d = json.loads(out)
    assert code == 2 and d["code"] == "OUT_OF_RANGE" and d["field"] == "w"


def test_cli_inconsistent():
    args = list(PUB)
    args[args.index("--power") + 1] = "0.04"
    code, out, _ = run_cli(*args)
    d = json.loads(out)
    assert code == 2 and d["code"] == "INCONSISTENT" and d["field"] == "power"


def test_cli_version():
    code, out, _ = run_cli("--version")
    d = json.loads(out)
    assert code == 0 and d["contract_version"] == "1.0.0" and "name" in d and "engine" in d


def test_cli_huge_n_within_two_seconds():
    t0 = time.perf_counter()
    code, out, _ = run_cli("--test", "chi2-contingency", "--mode", "a-priori", "--w", "0.000001",
                           "--alpha", "0.05", "--power", "0.95", "--df", "2")
    assert code == 0 and time.perf_counter() - t0 < 2.0
    assert isinstance(json.loads(out)["n_total"], int)


def test_cli_deterministic():
    assert run_cli(*PUB) == run_cli(*PUB)


# ------------------------------------------- taşma: JSON'da Infinity/NaN olmamalı
@pytest.mark.parametrize("mode,extra", [
    ("post-hoc", {"n_total": "100"}),
    ("post-hoc", {"n_total": "1" + "0" * 400}),
    ("a-priori", {"power": "0.95"}),
])
def test_overflowing_ncp_is_rejected_not_infinity(mode, extra):
    w = "1e200" if extra.get("n_total", "") != "1" + "0" * 400 else "0.3"
    with pytest.raises(GPowerError) as ei:
        execute({"test": "chi2-contingency", "mode": mode, "w": w, "alpha": "0.05", "df": "5", **extra})
    assert ei.value.code == "OUT_OF_RANGE" and ei.value.exit_code == 2


def test_cli_output_is_strict_json_for_huge_but_finite_values():
    code, out, _ = run_cli("--test", "chi2-contingency", "--mode", "post-hoc", "--w", "100000",
                           "--alpha", "0.05", "--n_total", "1000000000000", "--df", "5")
    assert code == 0
    d = json.loads(out, parse_constant=lambda c: pytest.fail(f"geçersiz JSON sabiti: {c}"))
    assert d["power"] == 1.0
