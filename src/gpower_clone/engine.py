"""gpower-clone hesap motoru: chi2-contingency (K4), a-priori ve post-hoc.

Tüm hesap ve doğrulama kuralları burada. CLI yalnızca argv -> sözlük -> JSON dönüşümü yapar.
Motor yalnızca standart kütüphaneyi (math, re, decimal) kullanır; numpy/scipy hiç yüklenmez
(süreç başlangıcı dahil 2 sn sınırı için). scipy yalnızca testlerde referans olarak kullanılır.
Kaynak: SPEC.md (K4) ve CONTRACT.md 1.0.0.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal

TEST_ID = "chi2-contingency"
IMPLEMENTED_MODES = ("a-priori", "post-hoc")
BONUS_MODES = ("compromise", "criterion", "sensitivity")  # henüz uygulanmadı

# Her mod için girdi alanları (sıra: eksik alan raporlama sırası) ve türleri.
MODE_FIELDS = {
    "a-priori": (("w", "float"), ("alpha", "float"), ("power", "float"), ("df", "int")),
    "post-hoc": (("w", "float"), ("alpha", "float"), ("n_total", "int"), ("df", "int")),
}

# SPEC.md Bölüm 5 özet kural listesi (karşılaştırmalar Decimal ile, kayan nokta hatası olmadan).
W_MIN = Decimal("1e-6")
P_MIN = Decimal("1e-7")
P_MAX = Decimal("0.9999999")  # 1 - 1e-7
N_MIN = 2  # CONTRACT Bölüm 5 (yalnızca girdi olarak; a-priori çıktısı 1 olabilir)
MAX_N = 2 ** 60  # çözücü üst sınırı; aşılırsa NO_SOLUTION

_FLOAT_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_INT_RE = re.compile(r"^[+-]?\d+$")


class GPowerError(Exception):
    """CONTRACT Bölüm 2.4 hata biçimi."""

    def __init__(self, code: str, message: str, field: str | None = None, exit_code: int = 2):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
        self.exit_code = exit_code

    def to_dict(self) -> dict:
        d = {"error": self.message, "code": self.code}
        if self.field is not None:
            d["field"] = self.field
        return d


# ===================================================================== matematik
# Düzenlenmiş eksik gama fonksiyonları P(a, x) ve Q(a, x) = 1 - P(a, x):
#   x < a + 1  -> seri açılımı (P doğrudan, Q = 1 - P)
#   x >= a + 1 -> sürekli kesir, değiştirilmiş Lentz (Q doğrudan, P = 1 - Q)
# Böylece küçük olan kuyruk her zaman çıkarma yapılmadan, göreli doğrulukla hesaplanır.
_FPMIN = 1e-300
_CF_EPS = 4e-16
_MAX_ITER = 5_000_000


def _gamma_pq(a: float, x: float) -> tuple[float, float]:
    """(P(a, x), Q(a, x)); a > 0."""
    if x <= 0.0:
        return 0.0, 1.0
    log_pref = a * math.log(x) - x - math.lgamma(a)
    if x < a + 1.0:
        ap = a
        delta = total = 1.0 / a
        for _ in range(_MAX_ITER):
            ap += 1.0
            delta *= x / ap
            total += delta
            if abs(delta) < abs(total) * 1e-17:
                break
        p = total * math.exp(log_pref)
        return p, 1.0 - p
    b = x + 1.0 - a
    c = 1.0 / _FPMIN
    d = 1.0 / b
    h = d
    for i in range(1, _MAX_ITER):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = b + an / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _CF_EPS:
            break
    q = h * math.exp(log_pref)
    return 1.0 - q, q


def _normal_upper_quantile(p: float) -> float:
    """Standart normalin üst kuyruk kuantili (Abramowitz-Stegun 26.2.23, ~4.5e-4 hata).
    Yalnızca kuantil aramasının başlangıç tahmini için kullanılır."""
    flip = p > 0.5
    pp = 1.0 - p if flip else p
    t = math.sqrt(-2.0 * math.log(pp))
    z = t - (2.515517 + 0.802853 * t + 0.010328 * t * t) / (
        1.0 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t ** 3)
    return -z if flip else z


def chi2_isf(alpha: float, df: int) -> float:
    """Merkezi chi2(df) dağılımının 1 - alpha kuantili: Q(df/2, x/2) = alpha çözümü."""
    a = df / 2.0
    use_upper = alpha <= 0.5
    target = alpha if use_upper else 1.0 - alpha  # 1 - alpha burada tam (Sterbenz)

    def resid(x: float) -> float:  # x'te azalan
        p, q = _gamma_pq(a, x / 2.0)
        return (q - target) if use_upper else (target - p)

    def pdf(x: float) -> float:
        y = x / 2.0
        return math.exp((a - 1.0) * math.log(y) - y - math.lgamma(a)) / 2.0

    # Başlangıç tahmini: Wilson-Hilferty
    z = _normal_upper_quantile(alpha)
    k = 2.0 / (9.0 * df)
    x = df * (1.0 - k + z * math.sqrt(k)) ** 3
    if not (x > 1e-12 and math.isfinite(x)):
        x = 1e-6

    # Kökü içine alan [lo, hi] aralığı
    if resid(x) > 0.0:
        lo, hi = x, x * 2.0
        while resid(hi) > 0.0:
            lo, hi = hi, hi * 2.0
    else:
        lo, hi = x / 2.0, x
        while resid(lo) < 0.0:
            lo, hi = lo / 2.0, lo

    # Newton; aralık dışına çıkarsa ikiye bölme
    x = 0.5 * (lo + hi) if x <= lo or x >= hi else x
    for _ in range(200):
        r = resid(x)
        if r == 0.0:
            return x
        if r > 0.0:
            lo = x
        else:
            hi = x
        d = pdf(x)
        xn = x + r / d if d > 0.0 else float("nan")
        if not (lo < xn < hi):
            xn = math.sqrt(lo * hi) if hi > 4.0 * lo else 0.5 * (lo + hi)
        if abs(xn - x) <= 4e-15 * xn:
            return xn
        x = xn
    return x


def critical_chi2(alpha: float, df: int) -> float:
    """Merkezi chi2(df) dağılımının 1 - alpha kuantili."""
    return chi2_isf(alpha, df)


_SUM_LIMIT = 5_000_000  # Poisson karışımında en fazla terim sayısı


def ncx2_sf(x: float, df: int, ncp: float) -> float:
    """Merkezsiz chi2(df, ncp) dağılımında x üstünde kalan olasılık.

    Poisson(ncp/2) ağırlıklı merkezi chi2(df + 2j) sağ kuyruklarının toplamı:
        sf = sum_j w_j Q(df/2 + j, x/2),   w_j = exp(-lam) lam^j / j!,  lam = ncp/2.
    Q(a + 1, y) = Q(a, y) + y^a e^-y / Gamma(a + 1) özyinelemesiyle yalnızca ilk terim doğrudan,
    gerisi O(1) toplamayla hesaplanır; tüm terimler pozitif olduğundan göreli doğruluk korunur.
    """
    if x <= 0.0:
        return 1.0
    a0 = df / 2.0
    y = x / 2.0
    if math.isinf(ncp):
        return 1.0
    lam = ncp / 2.0
    if lam <= 0.0:
        return _gamma_pq(a0, y)[1]

    if lam > 1e8:  # çok büyük ncp: dağılım normale çok yakın, uçlar çift duyarlılıkta 0/1
        z = (x - (df + ncp)) / math.sqrt(2.0 * (df + 2.0 * ncp))
        if z < -45.0:
            return 1.0
        if z > 45.0:
            return 0.0

    s = math.sqrt(lam)
    j_lo = max(0, int(lam - 12.0 * s - 10.0))
    j_hi = int(lam + 12.0 * s + 40.0)
    if j_hi - j_lo > _SUM_LIMIT:
        raise GPowerError("NO_SOLUTION", "ncp ve df birlikte çok büyük; güç hesaplanamadı", "w")

    a = a0 + j_lo
    q = _gamma_pq(a, y)[1]
    t = math.exp(a * math.log(y) - y - math.lgamma(a + 1.0))  # Q(a+1) - Q(a)
    w = math.exp(-lam + j_lo * math.log(lam) - math.lgamma(j_lo + 1.0))
    total = wsum = 0.0
    for j in range(j_lo, j_hi + 1):
        total += w * q
        wsum += w
        if w < 1e-40 and j > lam:
            break
        q = min(q + t, 1.0)
        t *= y / (a0 + j + 1.0)
        w *= lam / (j + 1.0)
    # Ağırlıklar toplamı 1 olmalı; büyük lam'da ln-gama yuvarlaması ortak bir ölçek hatası
    # bırakır, normalleştirme bunu giderir.
    return min(total / wsum, 1.0)


def _power_at(crit: float, df: int, ncp: float) -> float:
    return ncx2_sf(crit, df, ncp)


def power(w: float, alpha: float, n_total: int, df: int) -> float:
    return _power_at(critical_chi2(alpha, df), df, w * w * n_total)


def solve_n(w: float, alpha: float, target: float, df: int) -> int:
    """Gücün >= target olduğu en küçük pozitif tam sayı (alt sınır 1).

    Güç, n'de monoton artan olduğundan: üstel büyütmeyle aralık bulunur, sonra
    ikili aramayla daraltılır (~2*log2(N) değerlendirme; doğrusal tarama yok).
    """
    crit = critical_chi2(alpha, df)
    w2 = w * w

    def ok(n: int) -> bool:
        return _power_at(crit, df, w2 * n) >= target

    if ok(1):
        return 1
    lo, hi = 1, 2  # ok(lo) yanlış
    while not ok(hi):
        lo, hi = hi, hi * 2
        if hi > MAX_N:
            raise GPowerError("NO_SOLUTION", "Hedef güce ulaşan bir örneklem büyüklüğü bulunamadı", "power")
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi


# ================================================================== girdiler
def _parse(field: str, kind: str, raw: str):
    """Ham metni (Decimal) sayıya çevirir. Ondalık ayırıcı yalnızca nokta; yerel ayardan bağımsız."""
    if not isinstance(raw, str):
        raise GPowerError("INVALID_VALUE", f"{field} için geçersiz değer", field)
    s = raw.strip()
    if kind == "int":
        if not _INT_RE.match(s):
            raise GPowerError("INVALID_VALUE", f"{field} tam sayı olmalı: {raw!r}", field)
        return Decimal(s)
    if not _FLOAT_RE.match(s):
        raise GPowerError("INVALID_VALUE", f"{field} sayı olmalı (ondalık ayırıcı nokta): {raw!r}", field)
    d = Decimal(s)
    if not d.is_finite() or abs(float(d)) == float("inf"):
        raise GPowerError("INVALID_VALUE", f"{field} sonlu bir sayı olmalı: {raw!r}", field)
    return d


def _check_ranges(v: dict, mode: str) -> None:
    if v["w"] < W_MIN:
        raise GPowerError("OUT_OF_RANGE", "effect size w must be greater or equal 1e-06", "w")
    if not (P_MIN <= v["alpha"] <= P_MAX):
        raise GPowerError("OUT_OF_RANGE", "alpha is outside the admissible range [1e-07, 1-1e-07]", "alpha")
    if mode == "a-priori":
        if not (P_MIN <= v["power"] <= P_MAX):
            raise GPowerError("OUT_OF_RANGE", "power is outside the admissible range [1e-07, 1-1e-07]", "power")
    else:
        if v["n_total"] < N_MIN:
            raise GPowerError("OUT_OF_RANGE", "n_total must be at least 2", "n_total")
    if v["df"] < 1:
        raise GPowerError("OUT_OF_RANGE", "degrees of freedom must be greater or equal one", "df")


def _check_consistency(v: dict, mode: str) -> None:
    if mode == "a-priori" and v["power"] < v["alpha"]:
        raise GPowerError("INCONSISTENT", "power must be greater than or equal to alpha", "power")


def _ncp(w: float, n: int) -> float:
    """w^2 * n; temsil edilemeyecek kadar büyükse OUT_OF_RANGE (JSON'da Infinity olmaz)."""
    try:
        ncp = w * w * n
    except OverflowError:  # n çok büyük bir tam sayı
        ncp = math.inf
    if not math.isfinite(ncp):
        raise GPowerError("OUT_OF_RANGE", "w ve n_total birlikte çok büyük: ncp temsil edilemiyor", "w")
    return ncp


# ============================================================== giriş noktası
def execute(params: dict) -> dict:
    """params: ham metin değerleri olan sözlük ('test' ve 'mode' dahil). Sonuç sözlüğü ya da GPowerError."""
    for key in ("test", "mode"):
        if key not in params:
            raise GPowerError("MISSING_PARAM", f"--{key} verilmedi", key)
    if params["test"] != TEST_ID:
        raise GPowerError("UNSUPPORTED", f"Desteklenmeyen test: {params['test']!r}", "test")
    mode = params["mode"]
    if mode in BONUS_MODES:
        raise GPowerError("UNSUPPORTED", f"{mode} modu bu sürümde uygulanmadı", "mode")
    if mode not in IMPLEMENTED_MODES:
        raise GPowerError("UNSUPPORTED", f"Bilinmeyen mod: {mode!r}", "mode")

    spec = MODE_FIELDS[mode]
    allowed = {name for name, _ in spec} | {"test", "mode"}
    for key in params:  # 1. tanınmayan ya da modla ilgisiz alan
        if key not in allowed:
            raise GPowerError("UNKNOWN_PARAM", f"Bu mod için tanınmayan alan: --{key}", key)
    for name, _ in spec:  # 2. eksik alan
        if name not in params:
            raise GPowerError("MISSING_PARAM", f"Gerekli alan verilmedi: --{name}", name)

    v = {name: _parse(name, kind, params[name]) for name, kind in spec}  # 3. sayı biçimi
    _check_ranges(v, mode)  # 4. aralık
    _check_consistency(v, mode)  # 5. tutarlılık

    w, alpha, df = float(v["w"]), float(v["alpha"]), int(v["df"])
    crit = critical_chi2(alpha, df)

    if mode == "a-priori":
        _ncp(w, 1)  # w^2 taşıyorsa en baştan reddet
        n = solve_n(w, alpha, float(v["power"]), df)
        ncp = _ncp(w, n)
        return {"ncp": ncp, "critical_chi2": crit, "n_total": n,
                "actual_power": _power_at(crit, df, ncp)}

    n = int(v["n_total"])
    ncp = _ncp(w, n)
    return {"ncp": ncp, "critical_chi2": crit, "power": _power_at(crit, df, ncp)}
