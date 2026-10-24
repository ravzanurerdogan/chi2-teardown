#!/usr/bin/env python3
"""Diferansiyel test: gpower-clone CLI'sini kâhinlerle karşılaştırır.

Kâhin 1: oracle/vectors.csv  (G*Power 3.1.9.7 arayüzünden okunan değerler)
Kâhin 2: statsmodels GofChisquarePower (bağımsız kütüphane, kesirli N verir)

Kullanım (repo kökünden):
  python tests/run_differential.py --cmd "python src/gpower-clone"
  python tests/run_differential.py --cmd "python src/gpower-clone" --n-random 500 --seed 1

Çıktı: tests/uyum_raporu.md ve tests/uyum_ayrintilari.csv
"""
import argparse, csv, json, math, os, random, shlex, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

TOL = 1e-6
# Ekranda yalnızca 5 anlamlı basamak görünen devasa N değerleri (v022, v023, v035)
N_APPROX = {"v022": 1.5443e13, "v023": 1.2763e13, "v035": 1.544e13}


def close(a, b):
    return abs(a - b) <= TOL or abs(a - b) <= TOL * max(abs(a), abs(b))


def run_cli(cmd, args):
    t0 = time.time()
    try:
        p = subprocess.run(cmd + args, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return None, -1, 30.0, "timeout"
    dt = time.time() - t0
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    if len(lines) != 1:
        return None, p.returncode, dt, f"stdout {len(lines)} satır (1 olmalı)"
    try:
        return json.loads(lines[0]), p.returncode, dt, ""
    except json.JSONDecodeError:
        return None, p.returncode, dt, "stdout JSON değil"


def f(x):
    return x if x != "" else None


def args_for(row):
    a = ["--test", "chi2-contingency", "--mode", row["mode"],
         "--w", row["w"], "--alpha", row["alpha"], "--df", row["df"]]
    if row["mode"] == "a-priori":
        a += ["--power", row["power"]]
    else:
        a += ["--n_total", row["n_total"]]
    return a


def expected_code(note):
    n = note.lower()
    if "power must be greater" in n or "message not recorded" in n:
        return "INCONSISTENT"
    return "OUT_OF_RANGE"


def check_oracle(cmd, row):
    out, rc, dt, problem = run_cli(cmd, args_for(row))
    res = {"id": row["id"], "kaynak": "G*Power", "girdi": f"w={row['w']} a={row['alpha']} p={row['power']} df={row['df']} N={row['n_total']}",
           "sure_s": round(dt, 2), "sonuc": "TAM", "aciklama": ""}
    if problem:
        res.update(sonuc="FARK", aciklama=problem); return res
    if row["note"].startswith("error"):
        if rc == 0 or "error" not in out:
            res.update(sonuc="FARK", aciklama="hata bekleniyordu, hesap döndü"); return res
        want = expected_code(row["note"])
        if out.get("code") != want:
            res.update(sonuc="UYARI", aciklama=f"code {out.get('code')} (beklenen {want})")
        return res
    if rc != 0 or "error" in out:
        res.update(sonuc="FARK", aciklama=f"hesap bekleniyordu, hata döndü: {out.get('error')}"); return res
    diffs = []
    if row["mode"] == "a-priori":
        if row["n_total"]:
            if out.get("n_total") != int(row["n_total"]):
                diffs.append(f"n_total {out.get('n_total')} != {row['n_total']}")
        elif row["id"] in N_APPROX:
            got = out.get("n_total")
            if not isinstance(got, int) or abs(got - N_APPROX[row["id"]]) > 1e-3 * N_APPROX[row["id"]]:
                diffs.append(f"n_total {got} ~ {N_APPROX[row['id']]:.4g} değil")
        if row["actual_power"] and not close(out.get("actual_power", math.nan), float(row["actual_power"])):
            diffs.append(f"actual_power {out.get('actual_power')} != {row['actual_power']}")
    else:
        if not close(out.get("power", math.nan), float(row["actual_power"])):
            diffs.append(f"power {out.get('power')} != {row['actual_power']}")
    for k, col in (("ncp", "ncp"), ("critical_chi2", "critical_chi2")):
        if row[col] and not close(out.get(k, math.nan), float(row[col])):
            diffs.append(f"{k} {out.get(k)} != {row[col]}")
    if diffs:
        res.update(sonuc="FARK", aciklama="; ".join(diffs))
    return res


def make_random(n, seed):
    from statsmodels.stats.power import GofChisquarePower
    rng = random.Random(seed)
    solver = GofChisquarePower()
    rows = []
    while len(rows) < n:
        w = round(rng.uniform(0.05, 0.8), 3)
        alpha = rng.choice([0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2])
        power = rng.choice([0.7, 0.8, 0.85, 0.9, 0.95, 0.99])
        df = rng.randint(1, 12)
        try:
            frac = float(solver.solve_power(effect_size=w, alpha=alpha, power=power, n_bins=df + 1))
        except Exception:
            continue
        if not (frac > 0 and math.isfinite(frac)):
            continue
        rows.append({"w": w, "alpha": alpha, "power": power, "df": df, "frac": frac})
    return rows


def check_random(cmd, i, r):
    row = {"mode": "a-priori", "w": str(r["w"]), "alpha": str(r["alpha"]), "power": str(r["power"]), "df": str(r["df"])}
    out, rc, dt, problem = run_cli(cmd, args_for(row))
    res = {"id": f"r{i:03d}", "kaynak": "statsmodels", "girdi": f"w={r['w']} a={r['alpha']} p={r['power']} df={r['df']}",
           "sure_s": round(dt, 2), "sonuc": "TAM", "aciklama": f"kesirli N={r['frac']:.4f}"}
    if problem or rc != 0 or "n_total" not in out:
        res.update(sonuc="FARK", aciklama=problem or str(out)); return res
    want = math.ceil(r["frac"])
    if out["n_total"] != want:
        res.update(sonuc="FARK", aciklama=f"n_total {out['n_total']} != ceil({r['frac']:.4f})={want}")
    elif out["actual_power"] < r["power"] - 1e-12:
        res.update(sonuc="FARK", aciklama="actual_power hedefin altında")
    return res


def make_wide(n, seed):
    """Uç değerler: w 0.001-2, alpha 1e-7-0.5, df 1-500, power 0.1-(1-1e-7). Kâhin: scipy."""
    from scipy.stats import chi2, ncx2
    rng = random.Random(seed + 1000)
    rows = []
    while len(rows) < n:
        w = round(10 ** rng.uniform(-3, 0.3), 6)
        alpha = float(f"{10 ** rng.uniform(-7, -0.3):.3g}")
        power = round(1 - 10 ** rng.uniform(-7, -0.05), 7)
        df = rng.randint(1, 50) if rng.random() < 0.7 else rng.randint(50, 500)
        if w < 1e-6 or not (1e-7 <= alpha <= 1 - 1e-7) or not (1e-7 <= power <= 1 - 1e-7) or power < alpha:
            continue
        crit = float(chi2.isf(alpha, df))
        pw = lambda N: float(ncx2.sf(crit, df, w * w * N))
        lo = hi = 1
        while pw(hi) < power:
            hi *= 2
            if hi > 1e15:
                break
        if hi > 1e15:
            continue
        while lo < hi:
            m = (lo + hi) // 2
            if pw(m) >= power:
                hi = m
            else:
                lo = m + 1
        rows.append({"w": w, "alpha": alpha, "power": power, "df": df, "n": lo, "crit": crit,
                     "act": pw(lo), "prev": pw(lo - 1) if lo > 1 else None})
    return rows


def check_wide(cmd, i, r):
    row = {"mode": "a-priori", "w": repr(r["w"]), "alpha": repr(r["alpha"]), "power": repr(r["power"]), "df": str(r["df"])}
    out, rc, dt, problem = run_cli(cmd, args_for(row))
    res = {"id": f"w{i:03d}", "kaynak": "scipy-genis", "girdi": f"w={r['w']} a={r['alpha']} p={r['power']} df={r['df']}",
           "sure_s": round(dt, 2), "sonuc": "TAM", "aciklama": f"scipy N={r['n']}"}
    if problem or rc != 0 or "n_total" not in out:
        res.update(sonuc="FARK", aciklama=problem or str(out)); return res
    diffs = []
    if out["n_total"] != r["n"]:
        # sınır belirsizliği: iki aday N'den biri hedefe 1e-9 kadar yakınsa uyarı
        near = abs(r["act"] - r["power"]) < 1e-9 or (r["prev"] is not None and abs(r["prev"] - r["power"]) < 1e-9)
        if near and abs(out["n_total"] - r["n"]) <= 1:
            res.update(sonuc="UYARI", aciklama=f"n_total {out['n_total']} vs scipy {r['n']} (güç hedefe 1e-9 yakın, sınır belirsizliği)")
            return res
        diffs.append(f"n_total {out['n_total']} != {r['n']}")
    elif not close(out.get("critical_chi2", math.nan), r["crit"]):
        diffs.append(f"critical_chi2 {out.get('critical_chi2')} != {r['crit']}")
    elif not close(out.get("actual_power", math.nan), r["act"]):
        diffs.append(f"actual_power {out.get('actual_power')} != {r['act']}")
    if diffs:
        res.update(sonuc="FARK", aciklama="; ".join(diffs))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help='örn: "python src/gpower-clone"')
    ap.add_argument("--oracle", default="oracle/vectors.csv")
    ap.add_argument("--n-random", type=int, default=500)
    ap.add_argument("--wide", type=int, default=0, help="uç değerli ek vektör sayısı (scipy kâhin)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out-dir", default="tests")
    a = ap.parse_args()
    cmd = shlex.split(a.cmd, posix=(os.name != "nt"))

    with open(a.oracle, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["test"] == "chi2-contingency"]
    results = []
    with ThreadPoolExecutor(a.jobs) as ex:
        results += list(ex.map(lambda r: check_oracle(cmd, r), rows))
        if a.n_random > 0:
            rnd = make_random(a.n_random, a.seed)
            results += list(ex.map(lambda t: check_random(cmd, *t), enumerate(rnd, 1)))
        if a.wide > 0:
            wd = make_wide(a.wide, a.seed)
            results += list(ex.map(lambda t: check_wide(cmd, *t), enumerate(wd, 1)))

    def stats(src):
        rs = [r for r in results if r["kaynak"] == src]
        return len(rs), sum(r["sonuc"] == "TAM" for r in rs), sum(r["sonuc"] == "UYARI" for r in rs), sum(r["sonuc"] == "FARK" for r in rs)

    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "uyum_ayrintilari.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=["id", "kaynak", "girdi", "sonuc", "aciklama", "sure_s"])
        wr.writeheader(); wr.writerows(results)

    g, s, wd_s = stats("G*Power"), stats("statsmodels"), stats("scipy-genis")
    ap_rows = [r for r in results if r["kaynak"] == "G*Power" and "a-priori" in
               next(x for x in rows if x["id"] == r["id"])["mode"] and not
               next(x for x in rows if x["id"] == r["id"])["note"].startswith("error") and
               next(x for x in rows if x["id"] == r["id"])["n_total"]]
    gate = sum(r["sonuc"] == "TAM" for r in ap_rows) / len(ap_rows) if ap_rows else 0
    slow = max((r["sure_s"] for r in results), default=0)
    lines = [
        "# Uyum raporu (diferansiyel test)", "",
        f"Komut: `{a.cmd}`  |  seed: {a.seed}", "",
        "| Kâhin | Vektör | Tam eşleşme | Uyarı | Fark |", "|---|---|---|---|---|",
        f"| G*Power (oracle/vectors.csv) | {g[0]} | {g[1]} | {g[2]} | {g[3]} |",
        f"| statsmodels (ceil N) | {s[0]} | {s[1]} | {s[2]} | {s[3]} |",
        f"| scipy, uç değerler (alpha 1e-7..0.5, df ..500, w 0.001..2) | {wd_s[0]} | {wd_s[1]} | {wd_s[2]} | {wd_s[3]} |", "",
        f"Kapı ölçümü (oracle a-priori, N bilinen satırlar): **%{gate*100:.1f}** tam N eşleşmesi (eşik %90).",
        f"En yavaş çağrı: {slow:.2f} s (sınır 2 s).", "",
        "## Uyuşmazlıklar ve uyarılar", ""]
    bad = [r for r in results if r["sonuc"] != "TAM"]
    lines += [f"- `{r['id']}` [{r['sonuc']}] {r['girdi']}: {r['aciklama']}" for r in bad] or ["Yok."]
    lines += ["", "Not: statsmodels kesirli N verir, G*Power yukarı yuvarlar. Burada beklenen N = ceil(kesirli N) alınmıştır.",
              "Her FARK satırı ya kodda bir hatadır ya da kaçırılmış bir kuraldır, açıklaması buraya yazılmalıdır."]
    with open(os.path.join(a.out_dir, "uyum_raporu.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if not any(r["sonuc"] == "FARK" for r in results) else 1)


if __name__ == "__main__":
    main()
