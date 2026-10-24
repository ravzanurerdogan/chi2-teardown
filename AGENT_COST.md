# AGENT_COST.md

Maliyet ücretsiz katmanlarla karşılandı. Token sayıları yalnızca ölçebildiklerimiz; ölçemediklerimizi tahmin etmedik, [DOLDUR] ile işaretledik.

| Ajan | Ne için | Model | İstek / token | İterasyon | Maliyet |
|---|---|---|---|---|---|
| Gemini CLI (API anahtarıyla) | İlk REA denemesi | gemini-3.8-flash (ana), gemini-3.5-flash-lite (yardımcı) | Ana model 9 istek, 0 token işlendi. Yardımcı model 1 istek, 771 giriş / 25 çıkış token (`/stats` çıktısı) | 3 deneme, sonuç alınamadı | 0 (ücretsiz) |
| Antigravity | Oturum 1: REA + Ghidra ile söküm | Gemini 3.8 Flash (High) | Tek konuşma. Token sayısı ölçülmedi. Kota doldu, 27.10.2026 13:05'te yenileniyor | Tek konuşmada yaklaşık 6 temel sorgu (dize arama, xrefs, fonksiyon bulma, pseudocode). Araç çağrısı sayısı ölçülmedi | 0 (ücretsiz) |
| Claude (süreç sohbeti) | Kurulum desteği, vektör çapraz kontrolü, SPEC.md, test koşucusu, belge taslakları | Claude (Sonnet 5.5) | Token sayısı ölçülmedi (arayüzde sayaç yok) | Tek sohbet, bütün proje | Ayrıca ücret ödenmedi |
| Claude (ayrı oturum) | Oturum 2: yalnızca SPEC.md ve CONTRACT.md ile kod yazımı | [MODEL ADI: o sohbetin alt kısmındaki model seçiciye bak] | Token sayısı ölçülmedi | Tek oturum (testler önce, sonra kod) | Ayrıca ücret ödenmedi |

## Neler yaşandı

- Gemini CLI'da ana model sıfır token işledi, istek sessizce yeniden denendi ve oturum dakikalarca yanıtsız kaldı. Google ile girişi de reddedildi ("this client is no longer supported"). Antigravity'ye geçildi.
- Antigravity'nin ücretsiz kotası söküm sırasında doldu. Söküm bu yüzden dar tutuldu (sadece χ² ile ilgili adresler).
- İlk REA çağrısı REA'nın yaklaşık 200 araçlık kataloğunu bağlama döktü. Bu, bağlamı şişirdi ve yavaşlatmanın büyük sebebiydi.

## Neyi farklı yapardık

1. Kuruluma daha erken başlar, ortam değişkenlerini (`JAVA_HOME`, `GHIDRA_INSTALL_DIR`) en başta doğrulardık. `JAVA_HOME`'un sonuna yanlışlıkla `\bin\java.exe` eklemek bir günümüze mal oldu.
2. Ajana ilk günden dar, tek hedefli sorular sorardık ("şu adresin xrefs'i"). Geniş sorular kota ve zaman harcadı.
3. Araç çıktısının (JSON) ekran görüntüsünü ajanın özetinden önce kaydederdik. Özetler bazen kanıt değil yorum içeriyor.
4. Oracle vektörlerini ve ekran görüntülerini söküme paralel, baştan toplardık.
5. Token kullanımını her oturumda kaydederdik. Şimdi bazı değerleri bilemiyoruz.

## Temiz oda notu

Oturum 2 yalnızca `SPEC.md` ile başladı, Ghidra çıktısını görmedi. Arayüz biçimi (CLI bayrakları, hata kodları) SPEC.md'de olmadığı için kodu yazan oturum `CONTRACT.md`'ye de başvurdu. `CONTRACT.md` hocanın verdiği arayüz belgesidir, decompile çıktısı içermez.

## Sonradan eklenen iterasyon: başlatma süresi

Kod ilk hâlinde Windows'ta soğuk ilk çağrıda 1,98 s sürüyordu (sınır 2 s, süreç başlangıcı dahil). Kodu yazan Claude oturumuna başlatma süresini azaltma isteği verildi. Sonuç: 550 çağrının en yavaşı 0,21 s, 106 test 1,55 s. Bu iterasyonda ajan merkezi ve merkezsiz χ² dağılım fonksiyonlarını scipy'siz (yalnızca `math`, `decimal`) yeniden yazdı; scipy yalnızca testlerde kaldı. Sayısal sonuçlar değişmedi (oracle 50/50, statsmodels 500/500). Ölçümü ancak teslimden birkaç gün önce yaptık, daha erken ölçseydik bu iterasyonu atlardık.
