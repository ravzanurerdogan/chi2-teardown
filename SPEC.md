# SPEC.md — chi2-contingency (K4)

Bu belge yalnızca davranışı tanımlar. Kod, decompile çıktısı ya da algoritma kopyası içermez.
Kaynak etiketleri: **[DOK]** CONTRACT.md ya da yayımlanmış yöntem, **[ORACLE vNNN]** G*Power 3.1.9.7 arayüzünden okunan değer (`oracle/vectors.csv`), **[VARSAYIM]** doğrulanmamış karar.

## 1. Kapsam

- Test kimliği: `chi2-contingency` (G*Power: χ² tests, Goodness-of-fit tests: Contingency tables).
- Zorunlu modlar: `a-priori`, `post-hoc`. İsteğe bağlı: `compromise`, `criterion`, `sensitivity` (Bölüm 7).
- Komut ve JSON biçimi CONTRACT.md 1.0.0 ile aynıdır. Bu belge onu tekrar etmez, yalnızca bu aileye özgü davranışı ekler.

## 2. Matematiksel model [DOK]

- `ncp = w² · n_total`
- `critical_chi2` = merkezi χ²(df) dağılımının `1 − alpha` kuantili.
- `power` = merkezsiz χ²(df, ncp) dağılımında `critical_chi2` değerinin üstünde kalan olasılık.
- `beta = 1 − power`.
- `df` bir girdidir, çıktı değildir.

## 3. A priori modu

Girdiler: `w, alpha, power, df`. Çıktılar: `ncp, critical_chi2, n_total, actual_power`.

**Çözücü kuralı.** `n_total`, gücün hedef `power` değerine eşit ya da büyük olduğu **en küçük pozitif tam sayıdır** (alt sınır 1). `actual_power` bu `n_total` için hesaplanan güçtür ve hedeften küçük olamaz. `ncp` bu `n_total` ile hesaplanır. [ORACLE v001..v020, v035..v050]

**Performans.** `n_total` 1.5e13 mertebesine çıkabilir (w = 1e-6). Çözücü doğrusal tarama yapmamalı, 2 saniye içinde bitmelidir. `n_total` JSON tam sayısı olarak yazılır. [VARSAYIM: bu büyüklükte G*Power yalnızca 5 anlamlı basamak gösterdiği için tam N doğrulanamaz.]

```gherkin
Feature: A priori güç analizi, χ² olumsallık tablosu

  Scenario Outline: Gerekli örneklem büyüklüğü G*Power ile aynıdır
    Given test "chi2-contingency" ve mod "a-priori"
    When w <w>, alpha <alpha>, power <power> ve df <df> verilir
    Then n_total tam olarak <n_total> olur
    And ncp <ncp> değerine, critical_chi2 <critical_chi2> değerine, actual_power <actual_power> değerine 1e-6 toleransla eşit olur
    And çıkış kodu 0 olur ve stdout tek satır JSON'dur

    Examples:
      | id   | w     | alpha     | power     | df  | ncp        | critical_chi2 | n_total | actual_power |
      | v001 | 0.3   | 0.05      | 0.95      | 2   | 15.4800000 | 5.9914645     | 172     | 0.9504692    |
      | v002 | 0.3   | 0.05      | 0.95      | 1   | 13.0500000 | 3.8414588     | 145     | 0.9507851    |
      | v003 | 0.3   | 0.05      | 0.95      | 3   | 17.1900000 | 7.8147279     | 191     | 0.9502399    |
      | v004 | 0.3   | 0.05      | 0.95      | 4   | 18.6300000 | 9.4877290     | 207     | 0.9506581    |
      | v005 | 0.1   | 0.05      | 0.95      | 2   | 15.4500000 | 5.9914645     | 1545    | 0.9500866    |
      | v006 | 0.5   | 0.05      | 0.95      | 2   | 15.5000000 | 5.9914645     | 62      | 0.9507228    |
      | v007 | 0.3   | 0.01      | 0.95      | 2   | 20.7000000 | 9.2103404     | 230     | 0.9505563    |
      | v008 | 0.3   | 0.10      | 0.95      | 2   | 13.0500000 | 4.6051702     | 145     | 0.9503684    |
      | v009 | 0.3   | 0.05      | 0.80      | 2   | 9.7200000  | 5.9914645     | 108     | 0.8036939    |
      | v010 | 0.3   | 0.05      | 0.90      | 2   | 12.6900000 | 5.9914645     | 141     | 0.9008626    |
      | v011 | 0.3   | 0.05      | 0.99      | 2   | 21.4200000 | 5.9914645     | 238     | 0.9900681    |
      | v012 | 0.3   | 0.05      | 0.95      | 6   | 20.8800000 | 12.5915872    | 232     | 0.9502375    |
      | v013 | 0.3   | 0.05      | 0.95      | 10  | 24.3900000 | 18.3070381    | 271     | 0.9500419    |
      | v014 | 0.05  | 0.05      | 0.95      | 2   | 15.4450000 | 5.9914645     | 6178    | 0.9500226    |
      | v015 | 0.01  | 0.05      | 0.95      | 2   | 15.4433000 | 5.9914645     | 154433  | 0.9500008    |
      | v016 | 0.9   | 0.05      | 0.95      | 2   | 16.2000000 | 5.9914645     | 20      | 0.9588793    |
      | v017 | 1.0   | 0.05      | 0.95      | 2   | 16.0000000 | 5.9914645     | 16      | 0.9566863    |
      | v018 | 0.3   | 0.001     | 0.95      | 2   | 27.6300000 | 13.8155106    | 307     | 0.9508431    |
      | v036 | 0.3   | 0.0000001 | 0.95      | 2   | 52.5600000 | 32.2361913    | 584     | 0.9505492    |
      | v037 | 0.3   | 0.00000011| 0.95      | 2   | 52.2900000 | 32.0455709    | 581     | 0.9503838    |
      | v039 | 0.3   | 0.5       | 0.95      | 2   | 6.3900000  | 1.3862944     | 71      | 0.9510871    |
      | v040 | 0.3   | 0.05      | 0.9999999 | 2   | 56.7900000 | 5.9914645     | 631     | 0.9999999    |
      | v041 | 0.3   | 0.9       | 0.95      | 2   | 1.5300000  | 0.2107210     | 17      | 0.9515995    |
      | v047 | 0.3   | 0.05      | 0.95      | 100 | 56.8800000 | 124.3421134   | 632     | 0.9501569    |
      | pub  | 0.3   | 0.05      | 0.95      | 5   | 19.8000000 | 11.0704977    | 220     | 0.9502155    |

  Scenario: N yukarı yuvarlanır, gerçek güç hedefin altına düşmez
    Given w 0.3, alpha 0.05, power 0.95 ve df 2
    Then n_total 172 olur
    And n_total 171 olsaydı güç 0.9493 olurdu ve hedefin altında kalırdı
    And actual_power 0.9504692 olur, bu 0.95'ten küçük değildir

  Scenario Outline: Çok küçük gereken N (alt sınır 1)
    Given w <w>, alpha <alpha>, power <power> ve df 2
    Then n_total tam olarak <n_total> olur

    Examples:
      | id   | w   | alpha     | power     | n_total | ncp       | critical_chi2 | actual_power |
      | v019 | 0.3 | 0.05      | 0.06      | 2       | 0.18      | 5.9914645     | 0.0637738    |
      | v020 | 0.3 | 0.05      | 0.05      | 1       | 0.09      | 5.9914645     | 0.0568148    |
      | v048 | 5   | 0.05      | 0.95      | 1       | 25.0      | 5.9914645     | 0.9964734    |
      | v049 | 0.3 | 0.95      | 0.95      | 1       | 0.09      | 0.1025866     | 0.9521454    |
      | v050 | 0.3 | 0.9999999 | 0.9999999 | 1       | 0.09      | 0.0000002     | 0.9999999    |

  Scenario: Çok küçük etki büyüklüğünde devasa N
    Given w 0.000001, alpha 0.05, power 0.95 ve df 2
    Then ncp 15.4432356, critical_chi2 5.9914645 ve actual_power 0.95 olur
    And n_total yaklaşık 1.5443e13 olan bir JSON tam sayısıdır
    And w 0.0000010001 için n_total yaklaşık 1.544e13 olur
```

## 4. Post hoc modu

Girdiler: `w, alpha, n_total, df`. Çıktılar: `ncp, critical_chi2, power`.

```gherkin
Feature: Post hoc güç, χ² olumsallık tablosu

  Scenario Outline: Ulaşılan güç G*Power ile aynıdır
    Given test "chi2-contingency" ve mod "post-hoc"
    When w <w>, alpha <alpha>, n_total <n_total> ve df <df> verilir
    Then ncp <ncp>, critical_chi2 <critical_chi2> ve power <power> değerlerine 1e-6 toleransla eşit olur

    Examples:
      | id   | w   | alpha | n_total | df | ncp        | critical_chi2 | power     |
      | v029 | 0.3 | 0.05  | 100     | 2  | 9.0000000  | 5.9914645     | 0.7706831 |
      | v030 | 0.1 | 0.05  | 200     | 2  | 2.0000000  | 5.9914645     | 0.2255449 |
      | v031 | 0.5 | 0.05  | 50      | 4  | 12.5000000 | 9.4877290     | 0.8203819 |
      | v032 | 0.3 | 0.05  | 10      | 2  | 0.9000000  | 5.9914645     | 0.1238530 |
      | pub  | 0.3 | 0.05  | 100     | 5  | 9.0000000  | 11.0704977    | 0.6235846 |
```

## 5. Geçersiz girdiler

Kontrol sırası: eksik ya da tanınmayan alan, sayı biçimi, aralık, tutarlılık. [VARSAYIM: sıra yalnızca birden fazla hata varsa önemlidir. v028 (alpha=1, power=0.95) için G*Power aralık mesajı verdi, tutarlılık mesajı vermedi.]

Hata çıktısı: tek satır JSON `{"error": "...", "code": "...", "field": "..."}`, çıkış kodu 2.

```gherkin
Feature: Geçersiz girdilerin reddi (a priori)

  Scenario Outline: G*Power'ın reddettiği girdiler reddedilir
    Given test "chi2-contingency" ve mod "a-priori"
    When w <w>, alpha <alpha>, power <power> ve df <df> verilir
    Then stdout bir hata JSON'u olur ve çıkış kodu 2 olur
    And code <code> ve field <field> olur

    Examples: etki büyüklüğü [ORACLE]
      | id   | w            | alpha | power | df | code         | field | G*Power mesajı                          |
      | v024 | 0            | 0.05  | 0.95  | 2  | OUT_OF_RANGE | w     | effect size w must be greater 1e-06      |
      | v025 | -0.3         | 0.05  | 0.95  | 2  | OUT_OF_RANGE | w     | effect size w must be greater 1e-06      |
      | v033 | 0.0000005    | 0.05  | 0.95  | 2  | OUT_OF_RANGE | w     | effect size w must be greater 1e-06      |
      | v034 | 0.0000009999 | 0.05  | 0.95  | 2  | OUT_OF_RANGE | w     | effect size w must be greater 1e-06      |

    Examples: serbestlik derecesi
      | id   | w   | alpha | power | df | code         | field | G*Power mesajı                               |
      | v026 | 0.3 | 0.05  | 0.95  | 0  | OUT_OF_RANGE | df    | degrees of freedom must be greater or equal one |

    Examples: alpha ve power aralığı [1e-7, 1-1e-7]
      | id   | w   | alpha        | power      | df | code         | field | G*Power mesajı                          |
      | v027 | 0.3 | 0            | 0.95       | 2  | OUT_OF_RANGE | alpha | alpha is outside the admissible range (1e-07) |
      | v028 | 0.3 | 1            | 0.95       | 2  | OUT_OF_RANGE | alpha | alpha is outside the admissible range (1e-07) |
      | v044 | 0.3 | 0.0000000999 | 0.95       | 2  | OUT_OF_RANGE | alpha | alpha is outside the admissible range (1e-07) |
      | v045 | 0.3 | 0.05         | 1          | 2  | OUT_OF_RANGE | power | power is outside the admissible range (1e-07) |
      | v046 | 0.3 | 0.05         | 0.99999999 | 2  | OUT_OF_RANGE | power | power is outside the admissible range (1e-07) |

    Examples: tutarsızlık, power < alpha
      | id   | w   | alpha     | power | df | code         | field | G*Power mesajı                            |
      | v021 | 0.3 | 0.05      | 0.04  | 2  | INCONSISTENT | power | power must be greater than or equal to alpha |
      | v038 | 0.3 | 0.9999999 | 0.95  | 2  | INCONSISTENT | power | power must be greater than or equal to alpha |
      | v042 | 0.3 | 0.99      | 0.95  | 2  | INCONSISTENT | power | power must be greater than or equal to alpha |
      | v043 | 0.3 | 0.999999  | 0.95  | 2  | INCONSISTENT | power | (mesaj kaydedilmedi, v038 ve v042 ile aynı kural varsayıldı) |

  Scenario Outline: Sınırdaki değerler kabul edilir
    Given test "chi2-contingency" ve mod "a-priori"
    When w <w>, alpha <alpha>, power <power> ve df 2 verilir
    Then hesap başarılı olur ve çıkış kodu 0 olur

    Examples:
      | w         | alpha     | power     | not                              |
      | 0.000001  | 0.05      | 0.95      | w tam 1e-6, kabul (v022)          |
      | 0.0000010001 | 0.05   | 0.95      | w eşiğin hemen üstü (v035)        |
      | 0.3       | 0.0000001 | 0.95      | alpha alt sınır (v036)            |
      | 0.3       | 0.05      | 0.9999999 | power üst sınır (v040)            |
      | 0.3       | 0.05      | 0.05      | power eşittir alpha (v020)        |
      | 0.3       | 0.95      | 0.95      | alpha eşittir power, büyük değerler (v049) |
      | 0.3       | 0.9999999 | 0.9999999 | iki üst sınır birlikte (v050)     |
```

Özet kural listesi (a priori): w ≥ 1e-6; 1e-7 ≤ alpha ≤ 1 − 1e-7; 1e-7 ≤ power ≤ 1 − 1e-7; power ≥ alpha (eşitlik serbest); df ≥ 1.

## 6. CLI biçimi [DOK: CONTRACT.md]

```gherkin
Feature: Komut satırı sözleşmesi

  Scenario: Başarılı çağrı
    When "gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.95 --df 5" çalışır
    Then stdout tek satır JSON olur ve ncp, critical_chi2, n_total, actual_power alanlarını içerir
    And n_total, JSON tam sayısıdır ("220", "220.0" değil)
    And df çıktı alanı olarak yazılmaz ya da yazılırsa düzenek onu yok sayar

  Scenario: Eksik alan
    When --df verilmeden çalışır
    Then code "MISSING_PARAM" ve çıkış kodu 2 olur

  Scenario: Modla ilgisiz alan
    When post-hoc modunda --power verilir
    Then code "UNKNOWN_PARAM" ve çıkış kodu 2 olur

  Scenario: Bilinmeyen test ya da mod
    When --mode "foo" verilir
    Then code "UNSUPPORTED" ve çıkış kodu 2 olur

  Scenario: Sayı olmayan değer
    When --w "abc" verilir
    Then code "INVALID_VALUE" ve çıkış kodu 2 olur

  Scenario: Deterministik ve hızlı
    Then aynı girdi her çağrıda aynı çıktıyı verir ve çağrı 2 saniyede biter
    And ondalık ayırıcı her zaman noktadır
```

## 7. İsteğe bağlı modlar (bonus)

Tanımlar CONTRACT.md Bölüm 3'ten. Aşağıdaki değerler CONTRACT.md Bölüm 9'daki açık vektörlerden alınmıştır (w=0.3, n_total=100, df=5).

```gherkin
Feature: Bonus modlar

  Scenario: compromise (beta_alpha_ratio 1)
    Given w 0.3, beta_alpha_ratio 1, n_total 100, df 5
    Then ncp 9.0, critical_chi2 7.6804954, alpha 0.1747455, beta 0.1747455, power 0.8252545

  Scenario: criterion (power 0.95)
    Given w 0.3, power 0.95, n_total 100, df 5
    Then ncp 9.0, critical_chi2 4.6618452, alpha 0.4585253

  Scenario: sensitivity (alpha 0.05, power 0.95)
    Given alpha 0.05, power 0.95, n_total 100, df 5
    Then ncp 19.7801344, critical_chi2 11.0704977, w 0.4447486
```

## 8. Açık sorular ve varsayımlar

1. **[VARSAYIM]** Hata `code` eşlemesi (OUT_OF_RANGE, INCONSISTENT) CONTRACT.md örneğine ve G*Power mesajlarının sözcüklerine göre seçildi. w < 1e-6 için hoca farklı bir code bekliyor olabilir.
2. **[VARSAYIM]** Post hoc modunda alpha, df ve w için a priori ile aynı aralık kuralları geçerlidir. `n_total ≥ 2` CONTRACT.md Bölüm 5'ten. Post hoc için G*Power ile ayrıca denenmedi.
3. **[VARSAYIM]** Güç hedefe karşı karşılaştırması tolerans içermez (`≥`). Gücün hedefe tam eşit olduğu vektör oracle'da yok.
4. **[VARSAYIM]** `v047` için `critical_chi2` 7. basamağı oracle ekranından değil bağımsız hesaptan alındı. Ekranda 124.3421 görüldü.
5. Çok büyük `n_total` (w = 1e-6 civarı) için tam tamsayı oracle ile doğrulanamadı.
