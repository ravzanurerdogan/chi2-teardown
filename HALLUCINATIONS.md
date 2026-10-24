# HALLUCINATIONS.md

Yapay zekâ yardımcılarının yanlış çıkardığı şeyler, nasıl fark edildikleri ve hangi testin yakaladığı.
Kullandığımız araçlar: Antigravity ajanı (REA ile söküm, Oturum 1), bir Claude sohbeti (süreç yardımcısı, SPEC.md ve test koşucusu), ayrı bir Claude oturumu (kod yazımı, Oturum 2).

## 1. Etki büyüklüğü kontrolünün eşiği ve anlamı (Antigravity ajanı, Oturum 1)

**İddia.** `FUN_00487d20` fonksiyonu için ajan şunu yazdı: iki sayının mutlak farkı 1e-6 veya daha küçükse etki büyüklüğü sıfır kabul edilir ve hata mesajı üretilir. Karşılaştırılan iki sayının "etki büyüklüğü veya H0/H1 değerleri" olduğunu söyledi.

**Neden şüpheliydi.** Sözde kod yalnızca iki sayının farkına bakıyordu, hangi sayılar olduğunu göstermiyordu. Bu kısım [AJAN] olarak işaretlendi, çünkü "bunun kanıtı hangi fonksiyonda?" sorusunun cevabı yoktu.

**Nasıl yanlışlandı.** G*Power arayüzünde (oracle) w eşiği doğrudan denendi:
- w = 0.0000009999 reddedildi (v034), w = 0.0000005 reddedildi (v033), w = 0 reddedildi (v024).
- w = 0.000001 kabul edildi (v022), w = 0.0000010001 kabul edildi (v035).

Yani gözlenen kural "w ≥ 1e-6 kabul". Ajanın okuduğu "fark ≤ 1e-6 ise reddet" biçimi, karşılaştırılan çift (w, 0) ise w = 1e-6'yı reddederdi, ama G*Power kabul ediyor. Ayrıca arayüz mesajı ("effect size w must be greater 1e-06") dizedeki mesajdan ("must not be zero") farklı, yani gözlenen reddin kaynağı farklı bir kontrol olabilir.

**Yakalayan test.** `oracle/vectors.csv` v022, v024, v033, v034, v035 ve `tests/test_chi2_spec.py` içindeki sınır senaryoları.

**Sonuç.** SPEC.md'de w kuralı yalnızca oracle'dan alındı, pseudocode yorumu kullanılmadı.

## 2. Alfa için üst sınır (Claude süreç sohbeti)

**İddia.** v041 (α = 0.9) kabul, v042 (α = 0.99) red görünce asistan "α için üst sınır 0.9 ile 0.99 arasında" dedi.

**Nasıl yanlışlandı.** v038 ve v042'nin hata mesajı "power must be greater than or equal to alpha" idi: red sebebi α'nın büyük olması değil, α > güç (0.95) olmasıydı. Ek vektörler bunu doğruladı: α = 0.95 ve güç = 0.95 kabul (v049), α = 0.9999999 ve güç = 0.9999999 kabul (v050). Gerçek kurallar: α ve güç [1e-7, 1−1e-7] aralığında olmalı, güç ≥ α olmalı.

**Yakalayan test.** v038, v042, v049, v050 ve hata mesajlarının kaydı.

## 3. "Elle kontrol ettim" iddiası (Claude süreç sohbeti)

**İddia.** İlk oracle sonucu (w = 0.3, α = 0.05, güç = 0.95, df = 2 için N = 172) bildirilince asistan "elle kontrol ettim, beklenen sonuç" dedi. Oysa o anda hiçbir hesap yapmamıştı.

**Nasıl fark edildi.** Asistan bir sonraki mesajda iddiayı geri aldı ("fazla iddialıydı, G*Power'ı çalıştıramıyorum"). Sonra scipy ile gerçekten hesaplandı: N = 171'de güç 0.9493 (hedefin altı), N = 172'de 0.9504692, kritik değer 5.9914645, λ = 15.48. Hepsi oracle ile tuttu.

**Dersi.** Sonuç doğru çıktı ama iddia kanıtsızdı. Kanıtsız iddiaları [AJAN] etiketi gibi ele aldık, her sayıyı bağımsız hesapla doğruladık.

## Halüsinasyon olmayan ama yanıltıcı olabilecek bir olay: bayat ortam

Antigravity ajanı önce REA'nın kullanılabilir olmadığını (Hayır), sonra Java kontrolünün başarısız olduğunu bildirdi. İkisi de **doğruydu**: ajanın başlatıldığı ortamda `JAVA_HOME` kullanıcı değişkeni yanlış değerdeydi (sonunda `\bin\java.exe` vardı). Başka bir terminalde aynı kontrol geçiyordu. Ajanın ham araç çıktısını (JSON) isteyerek yorumuna güvenmeden doğrulandı. Halüsinasyon sayılmadı, ortam farkıydı.
