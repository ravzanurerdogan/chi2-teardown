# LEDGER.md: kanıt defteri

Etiketler: **[DOK]** kılavuzda, makalede ya da hocanın belgesinde yazıyor. **[REA]** binary'den kanıtlandı (adres ya da dize referansıyla, REA/Ghidra statik analizi, dosya çalıştırılmadı). **[AJAN]** ajanın çıkarımı, kanıtı yok.
Ek bölüm **[GÖZLEM]**: G*Power arayüzünden (kâhin) okunan davranış. Bunlar [REA] değildir, puan beklenmez; SPEC.md'nin kaynağıdır.

Kapsam notu: Söküm χ² olumsallık tablosuyla ilgili dizeler ve bir doğrulama fonksiyonuyla sınırlı kaldı. Antigravity kotası dolduğu için hesap motorunun (güç ve N çözücüsü) içine girilmedi. Hesap davranışı bu yüzden [GÖZLEM] ve [DOK] ile tanımlandı.

## 1. Hedef ve araçlar

- Dosya: `GPowerNT.exe` (G*Power 3.1.9.7, Windows). PE32, x86. Pakette `GPower.exe` adlı ayrı bir dosya yoktu.
- SHA-256: `c63e6a133eb6372932f810c08cc33dc35a06d1ddb658f897bd6c34a754efc812`
- Kanıt: `docs/screenshots/07-gpower-sha256.png` (orijinal), `07b-gpower-kopya-sha256.png` (incelenen kopya). REA'nın `open_binary` çıktısındaki `sha256` aynı değeri verdi (ekran görüntüsü alınamadı).
- REA 6.7.0 (`rea-agents`), Ghidra 12.1.4, OpenJDK 21.0.12.1. Kanıt: `docs/screenshots/01-capabilities-ghidra-checks.png`, `05-antigravity-java-ok-true.png`, `06-antigravity-rea-ghidra-kontrol.png` (devamı `06-...kontrol1.png`).
- Hedef dosyanın kopyası sabit bir klasörde (`C:\gpower-target`) incelendi ve hash'i doğrulandı. Dosya çalıştırılmadı.

## 2. [REA] Dize bulguları (search_strings)

Kanıt: `docs/screenshots/09-rea-chi-dizeleri.png` (devamı `09-...dizeleri1.png`), `09c-rea-noncentral-effectsize.png` (devamı `09c-...effectsize1.png`).

| Adres | Dize (kısa) |
|---|---|
| `0x5c6dd4` | "Goodness-of-fit tests: Contingency tables" |
| `0x5c6b00` | "χ² tests" |
| `0x5cec5c` | "CEff_CHI_GoF_Cont" |
| `0x60d5f8` | RTTI: `.?AVCEff_CHI_GoF_Cont@@` |
| `0x60c8e0` | RTTI: `.?AVPowerChiCont@@` |
| `0x60c8c8` | RTTI: `.?AVPowerChi@@` |
| `0x60c8fc` | RTTI: `.?AVPowerChiOneVar@@` |
| `0x60c450` | RTTI: `.?AVChiDistribution@@` |
| `0x5e3764`, `0x5e376c`, `0x5e3774` | "chi2cdf", "chi2inv", "chi2pdf" |
| `0x5c3d98`-`0x5c3e40` | "ChiDist-Cdf: ..." hata mesajları (parametre aralık dışı vb.) |
| `0x5c3e5c`-`0x5c3f14` | "ChiDist-Quantile: ..." hata mesajları |
| `0x5c3d48` | "noncentrality lambda" |
| `0x5c55fc` | "Noncentrality parameter λ" |
| `0x5c55a8` | "Effect size w" |
| `0x5c6e00` | "Effect size conventions" (w = .10 küçük, .30 orta, .50 büyük) |
| `0x5c67d0` | "In a priori calculations the effect size must not be zero." |
| `0x5cc7c8` | "The effect size is too low!" |
| `0x5cc9e8` | "The effect size is outside the admissible range [" |
| `0x5ccf14` | "No solution found for the requested effect size!" |

Not: Ajan aynı dizeyi iki farklı cevapta biraz farklı adres aralıklarıyla yazdı; ikisi tutarlı.

## 3. [REA] Çapraz referanslar ve fonksiyon

Kanıt: `docs/screenshots/10-rea-xrefs.png`, `11-rea-fonksiyon-487d20.png`.

- `0x5c67d0` ("effect size must not be zero") dizesine `0x487d87` adresi referans veriyor.
- `0x5c55fc` ("Noncentrality parameter λ") dizesine `0x609414` adresi referans veriyor (dizelerin ve RTTI'nin bulunduğu 0x60xxxx bölgesi; kod olmadığı yorumu [AJAN], bkz. bölüm 6).
- `0x487d87`, `FUN_00487d20` (`0x487d20`-`0x487dfc`) fonksiyonunun içinde.
- `FUN_00487d20`: iki `double` parametrenin farkının mutlak değerini 1e-06 ile `<=` karşılaştırır. Koşul sağlanınca yukarıdaki mesajı üretir ve 0 döndürür, aksi halde 1 döndürür. (Sözde kod bu repoda yoktur; yalnızca adres ve bu kısa betim.)

## 4. [DOK] Kılavuz ve ders belgesi kaynaklı

- Merkezsiz parametre: λ = w² · N ve güç, merkezsiz χ²(df, λ) dağılımından hesaplanır (yayımlanmış yöntem). Sözleşme örnekleri bunu doğruluyor (`CONTRACT.md` Bölüm 4.4, 9).
- Cohen eşikleri w: 0.1, 0.3, 0.5 (`CONTRACT.md` Bölüm 10). Aynı eşikler binary'de de var (`0x5c6e00`, [REA]).
- G*Power N'yi yukarı yuvarlar, R `pwr` ve Python `statsmodels` kesirli N verir (ödev metni, "Kâhin" bölümü).
- CLI, hata kodları ve karşılaştırma toleransı: `CONTRACT.md`.

## 5. [GÖZLEM] G*Power arayüzünden okunan davranış (kâhin)

Veri: `oracle/vectors.csv`, ekran görüntüleri: `oracle/screenshots/`. Bunlar [REA] değildir.

- N, gücün hedefe eşit ya da büyük olduğu en küçük tam sayıdır (örnek: N=171'de güç 0.9493, N=172'de 0.9504692; v001).
- Güç ≥ alpha olmalı, eşitlik kabul (v020, v049, v050 kabul; v021, v038, v042 red).
- w ≥ 1e-6 kabul (v022, v035 kabul; v033, v034, v024 red). Mesaj: "effect size w must be greater 1e-06" (eşitlik kabul edilmesine rağmen).
- alpha ve güç [1e-7, 1-1e-7] aralığında kabul (v036, v040 kabul; v044, v045, v046, v027, v028 red).
- df ≥ 1 (v026 red).
- N=1 geçerli bir sonuç (v020, v048, v049, v050).
- Çok küçük w için N devasa olur (v022: ~1.5443e13) ve ekranda 5 anlamlı basamakla bilimsel gösterimde yazılır.

## 6. [AJAN] Doğrulanmamış ya da çürütülen çıkarımlar

- **Çürütüldü.** `FUN_00487d20`'deki iki sayının "etki büyüklüğü ya da H0/H1" olduğu ve "fark ≤ 1e-6 ise w sıfır sayılıp reddedilir" yorumu. Oracle'da w = 1e-6 kabul edildi (v022) ve gözlenen mesaj dizeden farklı. Ayrıntı: `HALLUCINATIONS.md` madde 1.
- `PowerChiCont` sınıfının contingency güç hesabını yaptığı: yalnızca ada dayanıyor, kod incelenmedi.
- "Noncentrality parameter λ" dizesinin kullanıcı arayüzü etiketi olduğu (`0x609414` veri bölgesinde): ad ve adres bölgesine dayalı çıkarım.
- `0x5cc7c8`, `0x5cc9e8`, `0x5ccf14` hata mesajlarının hangi koşullarda gösterildiği: xrefs ile izlenmedi. G*Power'da gözlemlenen mesajlar bu dizelerle aynı metinde değil; hangisinin hangi girdiyle tetiklendiği bilinmiyor.
- `FUN_00487d20` içindeki mesajın hangi kanala (diyalog, günlük) yazıldığı bilinmiyor.
