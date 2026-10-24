# Oturum 2 (yazım)

Ajan: ayrı, yeni bir Claude sohbeti. Girdi olarak yalnızca `SPEC.md` ve hocanın verdiği `CONTRACT.md` eklendi. Ghidra çıktısı, LEDGER.md ve söküm sohbeti gösterilmedi.

## İlk prompt

```
Bu bir eğitim ödevi. Ekteki SPEC.md ve CONTRACT.md'ye uygun bir komut satırı programı yaz: gpower-clone, χ² olumsallık tablosu (chi2-contingency) için a-priori ve post-hoc modları.
Kurallar: Python, scipy kullanılabilir. Hesap tek bir motor dosyasında olsun, CLI onu çağıran ince bir katman olsun. SPEC.md dışında hiçbir kaynağa başvurma. Önce SPEC.md'deki tablolardan pytest testleri yaz, sonra kodu yaz. N'yi bulmak için doğrusal tarama yapma, 2 saniye sınırı var.
```

## Sonradan verilen istem (başlatma süresi)

```
gpower-clone tek çağrıda Windows'ta 1,79 saniye sürüyor, sınır 2 saniye. Başlatma süresini en az yarıya indir.
Önce python -X importtime ile hangi import'ların yavaş olduğunu ölç ve bana göster.
Sonra importları gerekli olana kadar ertele (örneğin scipy.special'ı yalnızca hesap yapılacağı zaman import et, hata durumlarında hiç import etme), argparse yerine elle ayrıştırmayı değerlendir.
Hesap sonuçları değişmemeli, 102 testin hepsi geçmeye devam etmeli.
```

Not: Oturum 2 CLI biçimi ve hata kodları için `CONTRACT.md`'ye de başvurdu. `CONTRACT.md` hocanın arayüz belgesidir, decompile çıktısı içermez.
