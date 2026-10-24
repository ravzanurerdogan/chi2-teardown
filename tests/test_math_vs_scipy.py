"""Saf `math` ile yazılan dağılım fonksiyonlarının scipy ile karşılaştırması.

scipy yalnızca burada, referans olarak kullanılır. Motor (engine.py) scipy/numpy'ı hiç yüklemez.
"""
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" if (ROOT / "src" / "gpower_clone").is_dir() else ROOT
sys.path.insert(0, str(SRC))

from gpower_clone import engine  # noqa: E402

stats = pytest.importorskip("scipy.stats")

DFS = [1, 2, 3, 4, 5, 6, 10, 25, 100, 500, 2000]


def rel(a, b):
    return abs(a - b) / max(abs(b), 1e-300)


# ------------------------------------------------------------ χ² kuantili
@pytest.mark.parametrize("df", DFS)
@pytest.mark.parametrize("alpha", [1e-7, 1e-5, 0.001, 0.01, 0.05, 0.1, 0.5, 0.9, 0.99, 0.999999, 0.9999999])
def test_chi2_isf_matches_scipy(df, alpha):
    got = engine.critical_chi2(alpha, df)
    want = float(stats.chi2.isf(alpha, df))
    assert rel(got, want) < 1e-10, (df, alpha, got, want)


def test_chi2_isf_random():
    rng = random.Random(11)
    worst = 0.0
    for _ in range(1500):
        df = rng.choice(DFS + [rng.randint(1, 300)])
        alpha = 10 ** rng.uniform(-7, -4e-7)
        worst = max(worst, rel(engine.critical_chi2(alpha, df), float(stats.chi2.isf(alpha, df))))
    assert worst < 1e-10, worst


# ------------------------------------------------ merkezsiz χ² (güç = sf)
@pytest.mark.parametrize("df", [1, 2, 5, 10, 100, 1000])
@pytest.mark.parametrize("ncp", [1e-12, 1e-6, 0.09, 1.0, 9.0, 19.8, 56.8, 250.0, 5000.0])
def test_ncx2_sf_matches_scipy(df, ncp):
    for alpha in (1e-7, 0.001, 0.05, 0.5, 0.9, 0.9999999):
        x = float(stats.chi2.isf(alpha, df))
        got = engine._power_at(x, df, ncp)
        try:
            want = float(stats.ncx2.sf(x, df, ncp))
        except OverflowError:  # scipy'nin kendisi bu noktada referans üretemiyor
            assert got == pytest.approx(1.0, abs=1e-12)
            continue
        assert abs(got - want) < 1e-12 and (want < 1e-9 or rel(got, want) < 1e-9), (df, ncp, alpha, got, want)


def test_ncx2_sf_random():
    rng = random.Random(5)
    worst = 0.0
    for _ in range(2500):
        df = rng.choice([1, 2, 3, 5, 10, 50, 100, 300])
        alpha = 10 ** rng.uniform(-7, -4e-7)
        ncp = 10 ** rng.uniform(-12, 3.5)
        x = float(stats.chi2.isf(alpha, df))
        worst = max(worst, abs(engine._power_at(x, df, ncp) - float(stats.ncx2.sf(x, df, ncp))))
    assert worst < 1e-12, worst


def test_ncx2_sf_huge_ncp_is_fast_and_saturates():
    import time
    t0 = time.perf_counter()
    assert engine._power_at(engine.critical_chi2(0.05, 2), 2, 1e12) == pytest.approx(1.0, abs=1e-15)
    assert engine._power_at(5.99, 2, 1e15) == pytest.approx(1.0, abs=1e-15)
    assert time.perf_counter() - t0 < 1.0


# ---------------------------------------- uçtan uca: aynı N, aynı güç
def test_solver_same_n_as_scipy_reference():
    def ref_power(w, alpha, n, df):
        return float(stats.ncx2.sf(stats.chi2.isf(alpha, df), df, w * w * n))

    rng = random.Random(3)
    for _ in range(120):
        w = rng.choice([0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2])
        alpha = rng.choice([1e-7, 0.001, 0.01, 0.05, 0.1, 0.5])
        pw = rng.choice([0.5, 0.8, 0.9, 0.95, 0.99, 0.9999])
        df = rng.choice([1, 2, 3, 5, 8, 20, 100])
        if pw < alpha:
            continue
        n = engine.solve_n(w, alpha, pw, df)
        assert ref_power(w, alpha, n, df) >= pw
        if n > 1:
            assert ref_power(w, alpha, n - 1, df) < pw, (w, alpha, pw, df, n)


# -------------------------------------------- motor scipy/numpy yüklemez
def _loaded_after(code):
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=SRC)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def test_engine_never_imports_numpy_or_scipy():
    code = (
        "import sys\n"
        "from gpower_clone import engine\n"
        "engine.execute({'test':'chi2-contingency','mode':'a-priori','w':'0.3','alpha':'0.05','power':'0.95','df':'5'})\n"
        "engine.execute({'test':'chi2-contingency','mode':'post-hoc','w':'0.3','alpha':'0.05','n_total':'100','df':'5'})\n"
        "print(sorted(m for m in ('numpy','scipy') if m in sys.modules))\n"
    )
    assert _loaded_after(code) == "[]"


def test_cli_never_imports_numpy_or_scipy():
    code = (
        "import sys, io\n"
        "from gpower_clone.cli import main\n"
        "sys.stdout = io.StringIO()\n"
        "main(['--test','chi2-contingency','--mode','a-priori','--w','0.3','--alpha','0.05','--power','0.95','--df','5'])\n"
        "main(['--version'])\n"
        "sys.stdout = sys.__stdout__\n"
        "print(sorted(m for m in ('numpy','scipy') if m in sys.modules))\n"
    )
    assert _loaded_after(code) == "[]"
