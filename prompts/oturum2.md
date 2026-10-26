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

## Sonradan verilen istem 2 (MCP adaptörü)

```
Mevcut gpower-clone projesine +15 puanlık MCP sunucusu katmanı ekle. Kurallar kısa:

1. Tek dosya: src/mcp_server.py. Tek yeni bağımlılık: resmi `mcp` paketi (pip install mcp), `from mcp.server.fastmcp import FastMCP`. Sunucu stdio üzerinden çalışsın: python src/mcp_server.py
2. Tek araç: power_analysis. Parametreler (hepsi gevşek tipli, doğrulamayı motor yapsın): test (str, zorunlu), mode (str, zorunlu), w, alpha, power, beta_alpha_ratio (number, opsiyonel), df, n_total (integer, opsiyonel). Yalnızca None olmayanları motora ilet.
3. Hesap mantığı KOPYALANMAYACAK: araç doğrudan gpower_clone.engine'i çağırsın. Çıktı biçimi CLI ile birebir aynı olmalı: CLI'nin JSON üretme ve hata dönüştürme kodunu yeniden kullan (gerekirse küçük bir ortak fonksiyona taşı, davranışı değiştirme). Başarıda CLI'nin stdout'undaki tek satır JSON'u metin olarak döndür. Hata durumunda istisna fırlatma; aynı hata JSON'unu ({"error","code","field"}) metin olarak döndür.
4. tests/test_mcp_equivalence.py: oracle/vectors.csv'deki her satır (50), CONTRACT.md Bölüm 9'daki 5 chi2 açık vektörü ve en az 10 geçersiz girdi (eksik alan, bilinmeyen alan, modla ilgisiz alan, bilinmeyen mod, w=0, df=0) için araç fonksiyonunun çıktısı ile CLI'nin (subprocess: python src/gpower-clone ...) stdout'unu karşılaştır; ikisi birebir aynı metin olmalı. Ek olarak sunucuyu stdio ile başlatıp araç listesinde power_analysis'i gören ve bir çağrının CLI ile aynı döndüğünü doğrulayan küçük bir protokol testi ekle (10 saniyeyi aşıyorsa atla).
5. Mevcut hiçbir davranışı değiştirme: şu an 287 test geçiyor ve hepsi geçmeye devam etmeli. Motor yalnızca standart kütüphaneyi kullanmaya devam etsin; `mcp` yalnızca mcp_server.py içinde import edilsin.
6. Bittiğinde pytest tests -q çıktısını ve oluşturduğun dosyaların listesini ver.
```
