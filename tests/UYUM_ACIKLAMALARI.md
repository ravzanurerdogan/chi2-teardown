# Uyum raporu açıklamaları (tests/uyum_raporu.md'deki FARK ve UYARI satırları)

Komut: `python tests/run_differential.py --cmd "python src/gpower-clone" --n-random 500 --wide 300` (seed 1).
Sonuç: oracle 50/50, statsmodels 500/500, scipy uç değerli 300 vektörün 298'i tam, 1 UYARI, 1 FARK.

## w194 (FARK) ve w241 (UYARI): aynı sebep, motorda küçük bir sayısal hata

| Satır | Girdi | Motor N | Doğru N | Motorun N'deki gücü | Hedef güç |
|---|---|---|---|---|---|
| w194 | w=0.001099, alpha=1.5e-06, power=0.9999998, df=406 | 304543956 | 304543958 | 0.99999979999995 | 0.9999998 |
| w241 | w=0.001897, alpha=0.00123, power=0.9999989, df=331 | 72322400 | 72322401 | 0.99999889999998 | 0.9999989 |

"Doğru N", bağımsız ve yüksek hassasiyetli (60 basamaklı, Poisson karışımı serisi) bir hesapla bulundu. Bu hesapta motorun verdiği N'de güç hedefin 2e-14 ile 4e-14 altında kalıyor, yani motor hedefi karşılamayan bir N'yi kabul ediyor. scipy de aynı sonucu veriyor (scipy hatalı değil).

Sebep: motorun kendi yazdığı güç hesabında yaklaşık 1e-13 mertebesinde mutlak sayısal hata var. Bu hata yalnızca güç hedefi 1'e çok yakın (≥ 0.999998) ve N çok büyük (≥ 7e7) olduğunda N'yi 1-2 birim kaydırabiliyor. Normal ve sınır vektörlerinde (oracle, statsmodels, 298 uç vektör) görülmedi.

Kapıya etkisi: yok. Bu vektörler klinik olarak anlamsız büyüklükte örneklem gerektiriyor.

G*Power ile karşılaştırma: bu iki vektör G*Power'da denenmedi, bu yüzden motorun bu uç noktalarda G*Power ile uyuşup uyuşmadığı bilinmiyor.
