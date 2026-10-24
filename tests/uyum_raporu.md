# Uyum raporu (diferansiyel test)

Komut: `python src\gpower-clone`  |  seed: 1

| Kâhin | Vektör | Tam eşleşme | Uyarı | Fark |
|---|---|---|---|---|
| G*Power (oracle/vectors.csv) | 50 | 50 | 0 | 0 |
| statsmodels (ceil N) | 500 | 500 | 0 | 0 |
| scipy, uç değerler (alpha 1e-7..0.5, df ..500, w 0.001..2) | 300 | 298 | 1 | 1 |

Kapı ölçümü (oracle a-priori, N bilinen satırlar): **%100.0** tam N eşleşmesi (eşik %90).
En yavaş çağrı: 0.35 s (sınır 2 s).

## Uyuşmazlıklar ve uyarılar

- `w194` [FARK] w=0.001099 a=1.5e-06 p=0.9999998 df=406: n_total 304543956 != 304543958
- `w241` [UYARI] w=0.001897 a=0.00123 p=0.9999989 df=331: n_total 72322400 vs scipy 72322401 (güç hedefe 1e-9 yakın, sınır belirsizliği)

Not: statsmodels kesirli N verir, G*Power yukarı yuvarlar. Burada beklenen N = ceil(kesirli N) alınmıştır.
Her FARK satırı ya kodda bir hatadır ya da kaçırılmış bir kuraldır, açıklaması buraya yazılmalıdır.
