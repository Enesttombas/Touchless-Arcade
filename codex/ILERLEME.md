# Faz 2 ilerleme

## 2026-10-12 — başlangıç
- Kaynak: DEVAM.md, “Şu anki durum”. Önceki işler tekrar uygulanmadı.
- 00 kamera köprüsü hazır; HP/ağ kapsam dışında.
- Önceki 3×3 menü ve çekirdek değişiklikleri çalışma ağacında korunuyor.
- Önceki test tabanı: 53 passed, 32 skipped, rc 0 (Opus beyanı; bu oturumda tekrar koşulmadı).
- Sıra: minimum altyapı → AR kontrol → Parmak Kuşu → Cevap Yağmuru → iki düello → Penaltı → Çiz-Tahmin.
- Araştırma yapılmayacak; kod bu oturumda doğrudan yazılacak. Her iş ayrı gerçek test ve yerel commit ile kapanacak.

## 2026-10-12 21:33 — 1: minimum altyapı (60 dk kutusu içinde)
- Değişenler: `prototipler/{filtre,oyuncu,olcum,cekirdek,stant_app}.py`, `kabul_prototip/{test_altyapi,test_stant_app}.py`.
- One Euro türevi ham önceki örnekten hesaplanır; düşük hızda görsel öngörü kapanır, sıçrama 35 px ile sınırlıdır. Ortak kapı süre/boyut/güven/kenar ve sahip denetimi uygular; kısa kayıp, kimlik ve hizalı yan listeler korunur.
- Komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_altyapi.py kabul_prototip/test_stant_app.py -p no:cacheprovider` → **25 passed, rc 0**.
- İlk denemede 2 hata bulundu ve giderildi: öngörü hızlı filtreyi aşıyordu; menü testi bileği kadraj dışında üretiyordu. Test sayısı azaltılmadan geçerli el fixture'ı kullanıldı.
- Komut: `app/.venv/Scripts/python.exe prototipler/olcum.py --kiyas` → **rc 0**, her menü oyununda 300 ölçüm:

| Oyun | p50 ms | p95 ms |
|---|---:|---:|
| Neon Kılıç | 13.86 | 16.81 |
| Gülme Düellosu | 20.40 | 24.57 |
| AR Maskeler | 10.94 | 18.68 |

- Sonra: Bilim Modu, canlı titreşim kalibrasyonu, çokgen oyun alanı, maskeyle kişi bağlama ve çapraz geçişte ileri kimlik eşlemesi. Kıyas kamera/algı gecikmesini ölçmez; mevcut 3 menü oyununu çalıştırdı.

## 2026-10-12 21:37 — 2: AR maske kontrolü (45 dk kutusu içinde)
- Değişenler: `prototipler/p_maske.py`, `kabul_prototip/{test_cila,test_maske_kontrol}.py`.
- Doğal göz/kaş/baş/el hareketleri maske değiştirmiyor; `ESKI_TETIKLER=True` geri dönüşü korunuyor. Vitrin yalnız yüz yokken döner. Büyük oklar, elini tut etiketi, hedef yüz halkası, kimlikle sahip seçimi ve bir saniyelik sonuç etiketi eklendi. Kenardaki oyuncuya oklar yaklaşır; ilk görünüşte hayalet el kontrolü gösterir.
- Komut: `PROTOTIP=p_maske app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_maske_kontrol.py kabul_prototip/test_cila.py kabul_prototip/test_ozel2.py -p no:cacheprovider` → **20 passed, 17 skipped, rc 0**. Atlananlar diğer prototiplerin seçici testleri.
- Eski dört doğal hareket testi, şartname gereği aynı girdinin değişim yapmadığını doğrulayacak şekilde çevrildi; test sayısı düşürülmedi.
- Sonra: 3 ziyaretçiyle öğretmeden canlı kullanım testi, okların 8 sn nabız animasyonu ve ifade efektlerinin ilave cilası. EXE doğrulandı: masaüstü Stant.lnk → Stant.exe → venv Python + güncel stant_app.py; açılmış uygulama yeniden başlatılmalı.

## 2026-10-12 21:45 — 3: Parmak Kuşu (60 dk kutusu içinde)
- Değişenler: `prototipler/{oyun_akis,p_parmak_kusu,p_ucan_kafa,stant_app}.py`, `kabul_prototip/{test_parmak_kusu,test_stant_app}.py`.
- Menü kartı 4. Yay-sönümlü Süzül, görünür mod hedefi ve operatör boşluğu ile Flappy, kimlikli iki kuş, artan zorluk, daraltılmış çarpışma dairesi, el kaybı toleransı, tur/rekor ekranı. Eski Uçan Kafa ile sütun çarpışma yardımcısı ortaklaştırıldı; hatalı kenar mesafesi düzeltildi.
- Komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_parmak_kusu.py -p no:cacheprovider` → **9 passed, rc 0**.
- 300 kare sentetik aktif tur ölçümü → **p50 3.53 ms, p95 4.66 ms, rc 0**. Kamera/algı süresi dahil değil.
- Menü kabul fixture'ları dolu/bos kart sayısını mevcut menüden alacak biçimde güncellendi; tüm takım işlerin sonunda koşulacak.
- Sonra: paralaks şehir, kıvılcım ve parçacık izi cilası; gerçek iki oyuncuyla kamera gecikmesi ve titreme denemesi.

## 2026-10-12 21:52 — 4: Cevap Yağmuru (120 dk kutusu içinde)
- Değişenler: `prototipler/{p_cevap_yagmuru,oyuncu,cekirdek,stant_app}.py`, `prototipler/veri/{sorular,ozel_sorular}.json`, `veri/sorular_inceleme.md`, `kabul_prototip/test_cevap_yagmuru.py`.
- Menü kartı 5. Altı poz, oyun özelinde uzak kişi eşiği, kalça/omuz şeridi, soru-yaklaşma-kilit-çarpışma-puan-podyum, kimlikli skor/seri/taç, eleme ve tek kişi süresi. 60 tarih bağımsız doğru/yanlış soru ve hesaplanan matematik; özel kategori boş. Operatör S/oklar ile şerit kaydırma kaydı. Çarpışmada tek Maskeci örneği, kişi kutusuyla kesilen maskeye renk tonlama ve cevabı arkasında çizme.
- Komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_cevap_yagmuru.py -p no:cacheprovider` → **13 passed, rc 0** (500 matematik hesabı dahil).
- İlk altı kişi çarpışma ölçümünde p95 61.07 ms bulundu. NumPy maske indeksleme yerine OpenCV copyTo kullanıldı. Aynı 300 kare ölçümü → **p50 12.73 ms / p95 22.79 ms, rc 0**; maskeler sentetik, algılama/segmentasyon süreleri dahil değil.
- `p_cevap_yagmuru.py --onizleme <çalışma dışı klasör>` → **rc 0**, beş görüntü üretildi ve tek tek açılarak incelendi: soru, yaklaşma, doğru/yanlış çarpışma, podyum. Bunlar sentetik kişiler/maskeler; canlı kamera kanıtı değildir.
- Sonra: 0.35× dramatik zaman, patlayan/takılan harf parçacıkları, ayak izi, uğultu ve madalya cilası; canlı altı kişilik maske ayrımı. Soru bankası insan incelemesi bekliyor; web doğrulaması yapılmadı. Model maskesi henüz yokken kutu çizgisi geri dönüşü var.

## 2026-10-12 21:55 — 5: Kovboy + Taş-Kağıt-Makas (90 dk kutusu içinde)
- Değişenler: `prototipler/{rekabet,p_refleks,p_tas_kagit,cekirdek,oyuncu,stant_app}.py`, `kabul_prototip/test_rekabet.py`.
- Menü kartları 6/7. Ortak kimlikli sol/sağ yuva, 3'te 2, eşitlik/tekrar ve yalnız RAM'de 1.5 sn tampon. Kovboy 2–6 sn rastgele sinyal, erken çekme cezası, aynı kare karşılaştırma ve 0.60→0.35 sn YZ. TKM sinyal sonrası 0.4 sn en güvenilir gerçek jest skoru, kural tablosu ve son beş tercihten YZ karşı hamlesi. El tarafı güveniyle jest güveni ayrıldı.
- Komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_rekabet.py -p no:cacheprovider` → **16 passed, rc 0**. RAM tamponu, adil kareler, kimlik, 3'te 2 ve YZ frekans kabulü dahil.
- 300'er sentetik kare → Kovboy **p50 3.57 / p95 4.44 ms**, TKM **p50 3.48 / p95 3.93 ms**, **rc 0**; kamera/algı hariç.
- Sonra: western çizim ve ses cilası, konfeti/taç; gerçek kamera kare zamanını tepki süresi etiketine bağlamak (kazanan karşılaştırması şu anda ortak çizim karesiyle adil). Gülme Düellosu taşınmadı; Duvardaki Delik/Heykel bu iş kapsamı dışında.

## 2026-10-12 22:01 — 6: Penaltı Düellosu (120 dk kutusu içinde)
- Değişenler: `prototipler/{p_penalti,stant_app}.py`, `kabul_prototip/test_penalti.py`.
- Menü kartı 8. Kimlikli parmakla 0.3 sn kilit, yavaş nişan/güç/falso ve son gerili parametreyle hızlı tetik; kayıpta/durgunlukta cezasız iptal. 1/120 sn yerçekimi/Magnus/sürtünme, perspektif, gecikmeye göre en az 1.3 sn uçuş ve son bölüm yavaşlığı. Kaleci 1.9 m ölçeğinde maske/poz/eldiven; 0.4 sn poz kaybı, tutuş/sektirme/gol/direk. 5'er şut, sırayla rol ve seri penaltı; YZ köşe öğrenimi, 10 şut kaleci challenge, görünür Frikik seçimi ve baraj; 16×8 Verlet ağ.
- Komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_penalti.py -p no:cacheprovider` → **16 passed, rc 0** (ikinci koşu da geçti).
- 300 sentetik uçuş karesi, kaleci maske çizimi + ağ dahil → **p50 6.76 / p95 7.55 ms, rc 0**. Kamera/segmentasyon hariç.
- Sonra: canlı iki kişiyle kamera alanı/nişan hassasiyeti, gerçek gecikme kalibrasyonu; gövde sektirmesinden sonra uçuşun geri yansıması, tribün/çim/iz/konfeti, fiziğin yan kamera tekrarı ve bilim ekranı. Üç boyutlu fizik ve gol kararı var; canlı kamera kullanımı henüz denenmedi.

## 2026-10-12 22:21 — 7: Çiz-Tahmin (120 dk kutusu içinde)
- Değişenler: `prototipler/{p_ciz_tahmin,stant_app,oyun_akis,rekabet}.py`, `prototipler/egitim/ciz_egit.py`, `prototipler/veri/ciz_kelimeler.json`, `kabul_prototip/{test_ciz_tahmin,test_rekabet,test_stant_app}.py` (son dosyada yalnız yeni dolu menüye ilişkin fixture).
- Menü kartı 9. İşaret parmağıyla neon çizim, V ile kalem kaldırma, avuçla silme; 28×28 ortalama/en-boy/kalınlık ön işlemesi, 4 Hz ilk üç tahmin ve %60 doğru eşiği. Üç kelime, 20 sn, kalan süre puanı; kimlikli iki tuval düellosu, kartlı Seyirci/D, model yokken yalnız Seyirci. Görünür mod hedefi, operatör boşluğu; I ile 28×28/166169 parametre/çıkarım zamanı ekranı.
- Onaylı veri adresi: `https://storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap/<kategori>.npy` (boşluklar `%20`). Kategoriler: sun, house, fish, key, star, tree, car, cat, umbrella, clock, eyeglasses, cloud, apple, banana, bridge, mountain, flower, bicycle, guitar, airplane, snake, spider, ice cream, moon, lightning. Her dosyanın yalnız ilk 21200 satırı Range ile alındı; başarılı indirmeler **25 × 16621312 = 415532800 byte (~396.28 MiB)**, başlık okuması dahil. Tam adres/satır/cache manifesti: `prototipler/modeller/ciz_indirme.json`. Google Creative Lab, CC BY 4.0.
- İlk denemede NumPy özel API sorunu düzeltildi; `heart` 404 döndüğü için anahtarla değiştirildi. İlk üç cache dosyası tekrar indirilmedi. Eğitim için eksik `onnx` venv'e eklendi; model/veri/venv Git'e alınmadı.
- Komut: `app/.venv/Scripts/python.exe prototipler/egitim/ciz_egit.py --ornek 20000 --epoch 14 --batch 512` → **rc 0**, RTX 4080 CUDA, 500000 eğitim + 25000 doğrulama; en iyi doğrulama **%91.896**, 138.43 sn. Küçük dönme/ölçek/kaydırma/kalınlık/kopukluk artırması. ONNX CPU'ya aktarıldı.
- Ayrılmış 200 örnekte bağımsız gerçek ONNX ölçümü → **184/200 (%92), rc 0**; çıkarım **p50 0.1785 / p95 0.2230 ms**. Bu örnekler eğitim ve epoch seçimine girmedi.
- Komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_ciz_tahmin.py kabul_prototip/test_rekabet.py -p no:cacheprovider` → **30 passed, rc 0** (13 çizim + 17 rekabet). Önceki çizim testi 12 passed; canlı kabul sayacı eklenince 13 oldu.
- Aktif Düello, iki sürekli hareketli tuval + gerçek ONNX, 300 kare → **p50 11.62 / p95 16.62 ms, rc 0**. İlk çift tuval neon çizimi 40.33 ms p95 verdi; birleşik neon önbelleği ve OpenCV panel işlemiyle düzeltildi. Kamera/algı dahil değil.
- Ortak akış düzeltmeleri: geri sayımda el kaybolunca boş oyun başlamaz; düello sonucundan beklemeye dönünce RAM kamera tamponu silinir. Dokuz dolu kartla boş kart fixture'ı açıkça üç kartlı uygulama kullanır. Başka oturumun AR baş yatırma/remap düzeltmeleri korunuyor; bu commit'e alınmadı.
- `app/.venv/Scripts/python.exe prototipler/p_ciz_tahmin.py --help` → **rc 0**. `--canli-test` 10 kelimelik gerçek kamera denemesini başlatır, tamamlandığında yalnız kelime/doğruluk/süreyi `modeller/ciz_canli_test.json` içine yazar; görüntü kaydetmez. Bu canlı komut burada çalıştırılmadı.
- `app/.venv/Scripts/python.exe prototipler/olcum.py --kiyas` → **rc 0**, dokuz deneyimde 300'er sentetik kare. p95 ms: Neon 16.38, Gülme 21.56, AR 16.90, Kuş 3.19, Yağmur 7.45, Kovboy 3.66, TKM 3.67, Penaltı 5.37, Çizim 4.92. Bu genel kıyas tek sabit el/yüzle çalışır; canlı/altı kişi/aktif çizim yükü değildir. Aktif yük ölçümleri ilgili iş bloklarında ayrı verilmiştir.
- Sonra: insanla 10 kelimelik canlı doğruluk (hedef ≥%70), çimdik kalem alternatifi, sesli tahmin ve görsel cila. Bitmap doğruluğu canlı havada çizim doğruluğu değildir. HP/ağ işi ve araştırma yapılmadı; 8–9 kapsamına girilmedi.

## 2026-10-12 22:21 — 1–7 son kabul
- Komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider` → **162 passed, 32 skipped, rc 0**, 83.53 sn. Önceki ilk son koşu 160 passed/32 skipped idi; canlı 10 kelime sayacı ve sonuç sonrası RAM temizliği testleri eklendikten sonra tamamı tekrar geçti. Başlangıçtaki 53 passed tabanı azalmadı.
- Dokuz menü kartı: Neon Kılıç, Gülme Düellosu, AR Maskeler, Parmak Kuşu, Cevap Yağmuru, Kovboy Düellosu, Taş-Kağıt-Makas, Penaltı Düellosu, Çiz Tahmin. Operatör 1–9; masaüstü EXE güncel kaynak kodunu çalıştırır, açık örnek yeniden başlatılmalıdır.
- İlk altı yerel commit: `34f6675f`, `55255902`, `5a826d1c`, `55e90b33`, `c9d7aef4`, `4295f1b3`; bu blok yedinci işin commit'iyle kaydedilir. Push yapılmadı. İlgisiz veya başka oturumun kirli kaynakları korunuyor.
- Canlı ziyaretçi/çoklu kişi testi, gerçek kamera gecikmesi, soru bankasının insan incelemesi ve belirtilen cila açık. HP/ağ ve 8–9 işleri bu teslimde yapılmadı.

## Cila — başlangıç / Cevap Yağmuru önce
- `CILA-YENI-6.md` uygulandı; eski üç oyun ve Opus'un kirli değişiklikleri korunuyor. Çökme için iki test önce **2 failed, rc 1**, ardından düzeltme ile `test_stant_app.py` **12 passed, rc 0**.
- Cevap Yağmuru'nun beş durumunda üçer PNG üretildi; `%TEMP%/cila_kareler/once/p_cevap_yagmuru_galeri.png` açıldı. Görülen 7 kusur: küçük başlık; çıplak/boş bekleme; öğretici beden yok; soru ile kişi puanı aynı alanda; çarpışan cevap/kişi sayısı; ham kimlik numaraları; sonuçta boş alan ve tekrar ipucu/konfeti yok. Kaybolan oyuncuda tur zamanı akıyor (davranış kontrolü eklenecek).
- 2026-10-12 22:57 — Çökme kapanışı: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider` → **164 passed, 32 skipped, rc 0**, 99.03 sn. `stant_app.py` yalnız hata toparlama değişti; `test_stant_app.py` yalnız sondaki iki yeni test index'e alınır. Önce: tek hatada menü; sonra: aynı kartın yeni örneği, 10 sn/3 hata ile 2 sn dinlenme uyarısı. Mevcut Opus testi stage edilmez.

## P0 Kovboy — önce (canlı bulgu önceliği)
- Beş durumun üçer karesi üretildi ve galeri açıldı. Görülen 6 kusur: görünmeyen kılıf, hazırlık göstergesi yok, küçük başlık, western atmosfer yok, ATEŞ görsel etkisi yok, sonuçta tekrar ipucu yok. Davranış: tek sıçrama/kayıp erken sayılıyor; herkese hazır kapısı ve raunt arası geri dönme kapısı yok.
- Yağmurda daha önce kırmızı yakalanan boş segmentasyon ROI ve kayıpta akan süre düzeltmeleri bu arada çalışma ağacında tutulacak; Yağmur commit'i kendi aşamasında.

## P0 TKM — önce
- Galeri açıldı: 5 kusur; şekil kartı yok, ritim küçük ve yalnız metin, sonuçta şekil ikonu yok, kazanan kuralı açıklanmıyor, küçük elde yaklaşma uyarısı yok. Mevcut tanıma yalnız jest etiketine bağlı.

## P0 Kovboy — sonra / kabul
- Önceki 6 görsel kusurun 5'i kapandı: görünür renkli kılıf/HAZIR, büyük başlık, ATEŞ flaşı, sonuç ipucu. Canlı kamera %85 parlaklıkla korunur; sahte galeri kişileri gerçek uygulamada kullanılmaz. Western dekorunu artırma "sonra": Enes canlı insan görüntüsünü özellikle istedi, sahneyi kapatmayacak kenar süsleriyle sınırlı.
- Hazırlık 0.5 sn; tüm kayıtlı eller hazırsa sayaç ilerler. Kayıp/alt kadraj çıkışı silahı boşa alır, tek sıçrama ceza değil; erken 2 ardışık kare, ateş sonrası ilk kare. Sonuç ≥2.5 sn ve herkes kılıfta olmadan yeni raunt yok.
- Yeni regresyonlar ilk **4 failed, 1 passed, rc 1**; düzeltme ve mevcut zamanlama fixture güncellemesi sonrası `test_rekabet.py test_cila_yeni.py` **26 passed, rc 0**, 76.88 sn (Yağmurun önceki 3 kontrolü de bu koşudaydı). Kovboy 2005 gürültülü kare exception'sız.
- Sonra galerisi üretildi/açıldı. `olcum.py --kiyas --kareler 150` **rc 0**, Kovboy p95 **10.10 ms**; kamera/algı hariç. Eski oyunlar kıyas sırasında >20 ms olabilir, kapsam gereği değiştirilmedi.
- Fare deneme aracı var; fiziksel kamera/fareyle iki tur bu ortamda yapılmadı, canlı kullanıcı hissi doğrulaması açık.
- P0 Kovboy tam takım: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider` → **173 passed, 32 skipped, rc 0**, 145.26 sn. Bu kabul TKM kod değişikliğinden önce tamamlandı.

## P0 Çiz Tahmin — önce
- Beş durumun galerisi açıldı: 5 kusur; kalem durumu görünmüyor, ince/sabit çizgi, kaldır/sil açıklaması eksik, geri al yok, tahmin metni çizim alanıyla karışıyor. Çizim davranışında 120 px eşiği/kayıpta hemen kesilme/jest etiketine bağlılık var.

## P0 TKM — sonra / kabul
- 5/5 kusur kapandı: büyük şekil kartları, ses/pop ritmi, büyük sonuç ikonları ve ezilme, uygulanan kural, YAKLAŞ kapısı. Giriş kartları bekleme ve üç saniyelik geri sayımda görünür.
- Nokta tabanlı parmak eklem açısı + bilek uzaklığı; yanlış jest etiketi noktaları ezmez. 0.6 sn seçim penceresi; bilek–orta MCP <45 px veya kayıpta sayaç durur; tanınmayan şekil puansız tekrar.
- İlk regresyon **4 failed, 1 passed, rc 1**; `test_rekabet.py test_cila_tkm.py -k 'not 2005'` → **22 passed, rc 0**. TKM kodu sonrası tam takım → **179 passed, 32 skipped, rc 0**, 158.04 sn; 2005 gürültülü kare dahil.
- Sonra galerisi üretildi/açıldı. `olcum.py --kiyas --kareler 150` → **rc 0**, TKM p95 **5.78 ms**. Fiziksel kamera/fareyle iki tur kontrol edilmedi; gerçek uzaktan parmak okunabilirliği Enes'in canlı denemesine açık.

## P0 Parmak Kuşu — önce
- Galeri açıldı: 6 kusur; karakter yerine oval, tek çizgili kanat, arka plan yok, içi boş dikdörtgen borular, skor efekti/rekor yok, ölüm/madalya yok. İki kuş aynı x/y'de üst üste geliyor. Skor hızını yeniden kuracağız; el kaybı ölüm olmayacak.

## P0 Çiz Tahmin — sonra / kabul
- 5/5 kusur kapandı: dolu/boş kalem ucu, One Euro yumuşatma, 6–14 px yuvarlak uçlu hız çizgisi, görünür el kuralları ve 1 sn avuçla silme halkası, 1 sn bekletmeli GERİ AL, tahminler daha aşağı/büyük.
- Noktadan işaret açık/orta kapalı kuralı; kapalı 2 kare histerezis, 15 FPS araları ≤4 px parçalarla doluyor. Ham sıçrama >0.12G ya da kayıp >0.25 sn yeni çizgi; tek kare yanlış şekil çizmez, kısa kayıp çizgiyi gereksiz kesmez.
- İlk test taslağı zaman argümanı uyuşmazlığıyla 6 failed verdi; mevcut API ile anlamlı regresyon koşusu **3 failed, 3 passed, rc 1**. Düzeltme sonrası `test_ciz_tahmin.py test_cila_ciz.py -k 'not 2005'` → **19 passed, rc 0** (ayrılmış gerçek ONNX 200 örneği dahil).
- Tam takım → **186 passed, 32 skipped, rc 0**, 192.65 sn; 2005 çizim gürültülü kare dahil. Sonra galerisi açıldı. `olcum.py --kiyas --kareler 150` → **rc 0**, çizim p95 **4.91 ms** (sabit el; aktif iki tuval yükü finalde ayrıca ölçülecek).
- Fare aracı mevcut; insanla canlı 10 kelime doğruluğu ve fiziksel fareyle 2 tur henüz yapılmadı. Yeni CNN eğitimi/veri indirme yok.

### Cila P0 — Parmak Kuşu (2026-10-12)
- Önce: 6 kusur (oval kuş, kanat yok, boş zemin, kutu borular, skor/rekor zayıf, hız sabit). Sonra: 0 açık görsel kusur; üç kareli kanat, dönen karakter, üç katman paralaks, gölgeli boru, parçacık/ölüm efekti, madalya ve sayaç.
- Hız: her skorda %4, tavan 2,2×; boşluk en az başlangıcın %75'i. Dikey kontrol bağımsız; el kaybı cezasız duraklatır. İki kuşun görünür konumu ve çarpışma konumu eşleşir.
- Kırmızı doğrulama: yeni testlerde 2 failed, 2 passed; düzeltmeden sonra odak 13 passed. 2005 float64/kaybolma/kenar/0–6 kişi/değişken zaman karesi exception olmadan tamamlandı.
- Komut: app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider → çıkış 0, 191 passed, 32 skipped (221,55 sn).
- Komut: app/.venv/Scripts/python.exe prototipler/olcum.py --kiyas --kareler 150 → çıkış 0; Kuş p95 6,37 ms. Diğer yeni oyunlar: Yağmur 5,55; Kovboy 6,33; TKM 6,18; Penaltı 5,30; Çiz 4,79 ms. Kamera/algı hariç.
- Önce/sonra PNG galerileri TEMP/cila_kareler/once ve sonra klasörlerinde açılarak incelendi. Bunlar sentetik algı ve test görüntüsüdür; gerçek kamera testi değildir.
- Kontrol edilmedi: fiziksel kamera ile iki tur, gerçek el hissi. Fare geliştirici modu mevcut; oynandı diye sayılmadı.

## Cila Cevap Yağmuru — görsel sonrası ara kontrol
- Önce galerisinde 7 kusur: küçük başlık, boş bekleme, bedenle şerit öğretimi yok, soru/kişi yazıları karışıyor, cevap/sayaç çakışıyor, ham kimlik numaraları, zayıf podyum. Sonra galerisi açıldı: büyük soru kartı, ayak izleri, dönen/büyüyen cevaplar, renkli kişi skor sütunları, seri/taç/+100, podyum/konfeti. 7 kapandı.
- Bankadaki 60 kayıt okundu; cevap indeksleri korunarak 30 başkent ifadesindeki iyelik yazımı düzeltildi. Brasília yazımı ve belirsiz Rio kısaltması → Rio de Janeiro. Yeni/güncel olgu eklenmedi, web araştırması yapılmadı.
- Yeni kırmızı test: kaybolan kişinin elenmesi ve karanlık kamera zemini için 2 failed, 2 passed, rc 1. Düzeltme sonrası odak 17 passed, rc 0. Tam takım/ölçüm sürüyor; kabul tamamlanmadan commit yok.

## Cila Penaltı — önce
- Beş durumdan üçer kare ve galeri üretildi/açıldı. 6 kusur: küçük/ince kale ve ağ, top ölçeği/gölge eksik, çim/stadyum çerçevesi yok, kalecinin çizilmiş çöp adamla gösterilmesi, iç faz adları ve belirsiz öğretici, etkisiz gol/tekrar. Canlı kamera zemini korunacak; insan yerine avatar kullanılmayacak.
- Kullanıcının düzeltmesi eski sapan şartnamesinin üstündedir: top üzerinde kısa kilit, parmakla kaleye doğru yol çizme; yön ve falso çizilen yoldan, güç hız/ivmeden. El kaybı şut sayılmaz; yol sonunda durarak veya iki parmak göstererek vurulur.

## Cila Cevap Yağmuru — kabul / yerel commit
- `test_cevap_yagmuru.py test_cila_cevap.py -k 'not 2005'` → 17 passed, rc 0. Tam takım (Penaltı yeni testleri eklenmeden başlayan koşu): 193 passed, 32 skipped, rc 0; 274,99 sn. Yağmur 2005 gürültülü kare testi dahil.
- `olcum.py --kiyas --kareler 150` → rc 0; Yağmur p95 8,76 ms, kamera/algı hariç. Önce/sonra galeri açıldı. Gerçek kamera/iki fiziksel tur kontrolü açık; sentetik görüntü bunların yerine sayılmadı.
- Kilit sonrası kısmi kişi kaybı artık kişiye yanlış/elenme cezası vermiyor. Tümü kayıpta soru saati durur; 0,5 sn sonra uyarı. Boş maske ROI sınırları kırmızı testten sonra düzeltildi. Kameranın %85 parlaklığı korunuyor.
- Sonra: harflerin silüet üzerine tek tek birikmesi ve yanal sahne geçişi henüz uygulanmadı; temel doğru/yanlış silüet, patlama, ses ve puan geri bildirimi mevcut. Önceki 7 yerleşim kusuru kapandı.

## Cila Penaltı — sonra / kabul
- Önce 6 yerleşim/görsel kusur; sonra galerisi açıldı, 6 kapandı: büyük perspektifli kale/dalgalanan ağ, dönen/gölgeli top ve kavisli iz, çim/ışık çerçevesi, çizilmiş kaleci kaldırıldı (insan tam ekran canlı kamerada), anlaşılır yol çizme ipuçları, gol/kurtarış patlaması ve fiziği yeniden çizen ağır çekim. Sonuç/başlangıç metnini ağ kapatmıyor.
- Sapan kaldırıldı: tek parmak top üzerinde 0,3 sn → kaleye doğru yol çiz. Yön çizgiyle aynı yönde; falso en az 6 noktada eğrilikten; güç hız ve pozitif ivmeden, 0,25–1 tavanı. Yol sonunda 0,28 sn durmak veya iki kare kalemi kaldırmak şut. Kayıp/sıçrama/durgun iptal hak yakmaz.
- Görünürlüğü sıfır kaleci noktalarının boş min() çökmesi ve kayıp kaleciye gol yazılması kırmızı testle yakalandı. İlk koşu 7 failed, 12 passed, rc 1. Sonra odak 19 passed, rc 0; görsel son düzeltme sonrası tekrar 19 passed, rc 0.
- Tam takım: 197 passed, 32 skipped, rc 0 (307,10 sn), Penaltı 2005 gürültülü kare dahil. Bu koşu son Kovboy/Çiz kamera takviyesinden önce yüklenmiş kodu denetledi; onların final kabulü ayrı koşulacak.
- olcum.py --kiyas --kareler 150 → rc 0, Penaltı p95 12,99 ms; kamera/algı hariç. İki kişilik gerçek maske modelinin algı maliyeti bu sayıya dahil değil.
- Sonra: yandan ayrı sanal kamera tekrarı yok; mevcut fizik aynı perspektifte ağır çekim tekrar edilir. Fiziksel iki tur kontrol edilmedi. Yeni kamera denemesi: indeks 0 Iriun “Please start Iriun Webcam” ekranı; indeks 1 sekiz saniyede kare vermedi. İnsan görüntüsüyle kabul yapılmış sayılmadı, HP/ağ/kurulum işi açılmadı.

## Final cila — Kovboy ve canlı kamera (2026-10-13)
- Önceki 6 kusurdan hafif western atmosferi de kenar tozu/çerçeveyle kapandı. İnsan yerine karakter yok; kamera %85, kılıf alanı yalnız %18 örtü. Ortak yeni oyun akışında da kamera %85: TKM/Çiz zeminleri kararmıyor. Test aracındaki çizilmiş kişiler yalnız sentetik kamera girdisidir, oyun karakteri değildir.
- Ek bulunan sorun: hazır olmayan/kaybolan ikinci oyuncu beklemeyi kilitliyordu. 3 sn sonra o rauntta seyirci; tek hazır oyuncu refleks modunda devam eder. SAĞ tek kaldığında çekiş puanı SAĞ'a yazılır. Bekleme süresi seyirciye ayırmadan önceye geri taşınmaz; kayıp erken çekiş değildir.
- Yeni kilit/kamera regresyonlarında ilk 3 failed, rc 1; düzeltme sonrası ayrı Kovboy koşusu: `test_rekabet.py test_cila_yeni.py -k 'not 2005'` → **25 passed, 1 deselected, rc 0**, 4,69 sn.
- Gürültü aracı güçlendirildi: gerçekten değişen dört parmak pozu, noktalara ayrı float64 titreme, yanlış/None jest etiketi, 0–6 kişi, kenar ve boş kareler. Altı oyun toplam **12.030 kare**, exception yok.
- Final tam takım: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider` → **202 passed, 32 skipped, rc 0**, 333,47 sn. Taban 162 düşmedi. Skip edilenler başarılı sayılmadı.
- Final `olcum.py --kiyas --kareler 150` → **rc 0**; p95 ms: Kuş 11,44; Yağmur 14,30; Kovboy 13,79; TKM 11,41; Penaltı 15,14; Çiz 6,99. Kamera/algı hariç; altı yeni oyun ≤20 ms. Eski Gülme/AR Maske >20 ms; kapsam dışı oldukları için değiştirilmedi.
- Kovboy/TKM/Çiz/Kuş/Yağmur son galerileri tekrar üretildi ve açıldı; her durum üç kare. Gerçek insan/fare ile iki tur kabulü açık: mevcut kamera Iriun bekleme görüntüsü veriyor. Sentetik galeri gerçek insan kabulü yerine geçmez.

## Final cila — Çiz Tahmin (2026-10-13)
- Önce 5 kusur → sonra 0 açık yerleşim/çizgi kusuru. Ek kamera kararması kırmızı pixel testiyle yakalandı; tuval altındaki kamera %76,5 görünürlüğe yükseltildi. Mod/süre yazıları ≥26 px. Kayıp uyarısı 0,5 sn bekler; yeni tur eski kayıp zamanını taşımaz.
- `test_ciz_tahmin.py test_cila_ciz.py -k 'not 2005'` → **20 passed, 1 deselected, rc 0**, 4,49 sn; tam takım yukarıdaki **202 passed**, Çiz 2005 gürültülü kare dahil.
- Aktif Düello ölçümü: iki hareketli el, 210 kare (ilk 10 ısınma), her tuvalde 535 enterpole nokta; ONNX ve neon dahil. Negatif hedef adı sayesinde tur boyunca çizim sürdürülerek gerçek model hesaplandı. **p50 12,02 / p95 18,72 ms**, son ONNX 0,22 ms; ≤20 ms assert ve rc 0. Kamera/algı ölçülmedi.
- Son galeri tekrar açıldı. Fiziksel insanla 10 kelime ve iki fare turu açık; CNN'in önceki ayrılmış veri testi canlı doğruluk testi sayılmadı.

## Final cila — Taş Kağıt Makas (2026-10-13)
- Önce 5 kusur → sonra 0 açık giriş/ritim/sonuç yerleşim kusuru. Parlak kamera zeminiyle üç şekil kartı ve sonuç tekrar incelendi; kartlar geri sayımı örtmüyor. Kayıp uyarısının çok erken görünmesi ayrıca düzeltildi: ilk 0,5 sn yalnız el gösterme ipucu, sonra "Seni göremiyorum"; dönüşte uyarı temizlenir, puan cezası yok.
- Yeni gecikme regresyonu önce **1 failed, rc 1**; düzeltmeden sonra ayrı `test_rekabet.py test_cila_tkm.py -k 'not 2005'` → **23 passed, 1 deselected, rc 0**, 4,72 sn. Tam takım **202 passed**, TKM 2005 gürültülü kare dahil; son p95 **11,41 ms**.
- Gerçek stant mesafesinde parmak okuma ve iki fiziksel tur açık; sentetik şekil testleri bunların yerine geçmez.

## Final cila — Cevap Yağmuru ve kapanış (2026-10-13)
- Önce 7 kusur → sonra 0 açık yerleşim kusuru. Yanlış cevabın harfleri kişinin gövdesi üstüne düşüyor; 120 ms/≤4 px titreme ve ilk 0,3 sn yavaş düşüş eklendi. Önceki "harfler sonra" kaydı kapandı. Son galeri açıldı; kişi/kamera zemini korunuyor.
- Ayrı `test_cevap_yagmuru.py test_cila_cevap.py -k 'not 2005'` → **17 passed, 1 deselected, rc 0**, 4,50 sn. Tam takım **202 passed, 32 skipped, rc 0**; Yağmur 2005 gürültülü kare dahil. Son p95 **14,30 ms**.
- Görsel önce/sonra: Kovboy **6→0**, TKM **5→0**, Çiz **5→0**, Kuş **6→0**, Yağmur **7→0**, Penaltı **6→0**. Bunlar açılan galerilerdeki kayıtlı kusurların sayısıdır; tüm olası kusurların sıfır olduğu iddia edilmez. Kuş ölüm/tüy/madalya sahnesi de son araç güncellemesiyle tekrar incelendi.
- Zaman kutusu sonunda "sonra": Yağmurda ayrı yanal sahne geçişi (mevcut öğelerde büyüme/dönme var), Penaltıda yandan ayrı sanal kamera (mevcut perspektifte fizik ağır çekimi var). Canlı kişi tanınabilirliği, iki fare turu ve Çiz canlı 10 kelime henüz doğrulanmadı; Iriun gerçek kişi karesi vermedi. HP/ağ araştırması yapılmadı.
- Çökme + dört ayrı P0 + Yağmur/Penaltı + son kamera/uyarı düzeltmeleri yerel commitlerle ayrıldı. Eski Neon/Gülme/AR Maske kodu ve kullanıcının p_maske/test değişiklikleri korunuyor, stage edilmedi. Push yok.
- Mevcut Stant.exe Python kaynaklarını başlatır; güncel oyunu görmek için açık uygulamayı kapatıp yeniden açmak gerekir. Derleme/kurulum/başlatıcı değişikliği yapılmadı.

## CILA-YENI-7 / 0 — Kovboy kilitlenmesi ve sade arayüz (2026-10-13)
- Kılıf kuralı iptal edildi. SOL/SAĞ oyuncular yüzden seçiliyor; omuz üstünde el yoksa (el tamamen görünmese de) 0,6 sn sonra hazır. Sonra 1,5–4 sn bekleme ve ATEŞ. Tek kare erken hareket sayılmaz; iki ardışık kare sayılır. 8 sn hazır olmayan seyirci; tek kişi YZ ile devam eder. Raunt sonucu 2,5 sn kalır.
- Önce galeride 6 yığılmış arayüz kusuru; sonra kılıf kutuları, BAŞLA paneli ve adım listesi kaldırıldı. İki yazı çağrısı sınırı için oyuncu adları tek başlık satırında, hazır işaretleri yüzlerin üstünde; kamera zemini korunuyor. Galeriler: TEMP/cila7/once ve TEMP/cila7/sonra/p_refleks_galeri.png; ikisi de açıldı.
- Yeni regresyonlar önce 9 failed / 2 passed, rc 1; düzeltme sonrası 11 passed, rc 0. İlgili eski/yeni testler: 36 passed, 1 deselected, rc 0. Tam `pytest -q kabul_prototip -p no:cacheprovider`: **214 passed, 32 skipped, rc 0**, 288,62 sn; 2005 karelik Kovboy gürültü testi dahil. Oyun çizimi p95 **9,21 ms** (kamera/algı hariç).
- Gerçek kamerada iki insanla 3 raunt kontrol edilmedi; mevcut Iriun bekleme görüntüsü insan kabulü değildir.
- Güncel CILA-YENI-7 madde 3 Opus'a ayrılmış: Yağmur kodu/bankası/testleri değiştirilmeyecek. TKM/KAPALI, eski üç oyun ve Opus'un kirli dosyaları korunuyor.

## CILA-YENI-7 / 1 — Kuşun hareketli boru boşlukları (2026-10-13)
- Önce: skor 0–7'de sabit boşluk; bütün borularda aynı faz; ağızda hareket ipucu yok; çizim/çarpışma hesabı iki yerde. Önce ve sonra galerileri TEMP/cila7/{once,sonra}/p_parmak_kusu_galeri.png üretildi ve açıldı.
- Sonra: boru doğarken ayrı faz/frekans alır; genlik hedefi min(35+7×skor,120), faz frekansı 0,6–1,3 rad/sn. Faz entegre edilir, genlik hedefe 42 px/sn ile yaklaşır; skor artışı boşluğu ışınlamaz. Dikey hız ≤276 px/sn (kuş tırmanma hızının %60'ı). Merkez güvenli ekran sınırında; kayıp elde hareket durur. Boru ağızlarında küçük neon oklar var.
- `bosluk_y` tek hesap; çizim aynı karede çarpışmanın sakladığı merkezi ve boşluk genişliğini kullanır. Skorun o karede değiştiği durum ayrıca test edildi. Eski çarpışma fixture'ı yeni hareketli merkezle uyumlandı, test silinmedi.
- Yeni testler önce **7 failed, rc 1**. Ayrı `test_cila7_kus.py test_parmak_kusu.py test_cila_kus.py`: **21 passed, rc 0**, 60,62 sn; 2005 gürültülü kare dahil. `olcum.py --kiyas --kareler 100`: Kuş p95 **10,61 ms**, rc 0; ayrıca iki kuş+dört görünür boru/200 aktif kare p50 **5,78**, p95 **7,49 ms**, ≤20 ms assert rc 0. Eski Gülme/Mask p95 23,90/21,26 ms; bu kapsamda değiştirilmedi.
- Gerçek kişi/fareyle iki tur kontrol edilmedi; sentetik görüntü fiziksel kabul değildir.
- Tam takım: `pytest -q kabul_prototip -p no:cacheprovider` → **221 passed, 32 skipped, rc 0**, 350,35 sn; 202 tabanı korunuyor.

## CILA-YENI-7 / 2 — Çiz Tahmin, düzeltme ÖNCESİ ölçüm (2026-10-13)
- Önce galeri açıldı: açıklama iki parmakta kaldır diyor; bunun katı orta-parmak şartı sahte gürültülü izde çizgiyi kesiyor. `CIZ_TANI=1` tanı şeridi/kaydı eklenirken mevcut 20 test yeşil kaldı (1 gürültü testi hariç, rc 0); oyun mantığı henüz değiştirilmedi. Tanı sadece landmark/durum yazar, kamera görüntüsü yazmaz. TEMP/ciz_tani.jsonl ve TEMP/cila7/ciz_tani_once.png üretildi.
- 15 FPS, %10 kayıp, her landmarkta ±6 px ve sık orta-parmak açılması: daire kapsamı %53,9, yıldız %45,4, ev %46; dairede 28 istenmeyen kopma. Orta-parmak açık 72 kare saptandı. Ayrı 15 FPS/170 px ve 8 FPS/220 px hareketlerde 12 karede 12 ayrı çizgi, sıfır mürekkep: sabit sıçrama eşiği doğrulandı. 15 FPS/1 px harekette 205 mürekkep pikseli: küçük hareketin yutulması bu izde elendi.
- Gerçek OyuncuKapisi sınıfı: ilk 0,35 sn aday bekleme, ardından 10 kabul, küçültülen elde 14 'küçük' reddi. Genel kapı eşikleri değiştirilmez; yeni tanı kapı reddini/aday beklemeyi görünür kılar. Ham el sayısı, kapının zaten verdiği canlı/aday/red bilgilerinden hesaplanır; reddedilen elin landmarkları kapıdan çıkmadığı için kayıtta yoktur.
- Yeni kabul testleri düzeltmeden önce **9 failed, 1 passed, rc 1**. İlk noktanın mürekkep olmaması ve 0,25 sn kayıp eşiği de bu testlerde doğrulandı. Bundan sonra yalnız ölçülen kalem/histerezis, ilk mürekkep, zamanla ölçeklenen sıçrama, kısa kayıp ve avuç işlemleri düzeltilecek.

## CILA-YENI-7 / 2 — Çiz Tahmin, düzeltme ve kabul
- Ölçülen nedenler düzeltildi: orta parmak şartı kalktı; işaret ucu/kök uzaklığıyla kalem 2 karede iner, 4 bükülü karede kalkar. İlk nokta mürekkep olur (8 FPS testinde 125 ms); 0,4 sn altı kayıp birleştirilir, sıçrama eşiği süreyle ölçeklenir, ara noktalar doldurulur. Uçta dolu/halka imleç; avuç 1 sn son çizgiyi geri alır, 2 sn tümünü siler.
- Aynı 15 FPS, %10 kayıp, ±6 px ve parmak gürültüsüyle daire/yıldız/ev kapsamı ayrı ayrı **%100**, istenmeyen kopma **0**. Üç JSONL oturumunun tekrar oynatılması aynı çizgileri ve aynı mürekkep piksellerini verdi. Gerçek OyuncuKapisi sınıfıyla 0,35 sn ısınma sonrası üç şekil de %100 / 0; global kapı değiştirilmedi.
- `pytest -q kabul_prototip/test_cila7_ciz.py kabul_prototip/test_ciz_tahmin.py kabul_prototip/test_cila_ciz.py -k "not 2005" -p no:cacheprovider`: **34 passed, 1 deselected, rc 0**, 17,60 sn. 14 yeni vaka; mevcut testler iptal edilen kalem kuralına göre güncellendi, test silinmedi.
- `FARE_EL=1` fare olay yolu üç şekille otomatik sürüldü; ekran görüntüleri TEMP/cila7/{daire,yildiz,ev}_fare.png. Kamera yerine sentetik zemin var. Fareyi bir insan elle kullanmadı; insanla kabul sayılmaz. Önce/sonra galeri ve tanı görselleri açıldı: TEMP/cila7/{once,sonra}/p_ciz_tahmin_galeri.png, ciz_tani_once.png, {daire,yildiz,ev}_sonra.png; kayıtlar yalnız landmark/durum içeriyor.
- Aktif iki kişilik çizimde ilk p95 **22,37 ms**, ≤20 assert rc 1. Neon hesabı tuval çevresine sınırlandı ve parıltı çeyrek çözünürlükte hesaplandı: p50 **8,65**, p95 **15,24 ms**, assert rc 0. `olcum.py --kiyas --kareler 100`: Çiz p95 **15,42 ms**, rc 0 (kamera/algı hariç). Eski Gülme/Mask kapsam dışı bırakıldı.
- Tam takım: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider` → **236 passed, 32 skipped, rc 0**, 340,93 sn; Çiz 2005 gürültülü kare dahil. Test sayısı 202 tabanının üstünde. Opus'un ad/simge/test değişiklikleri çalışma ağacında birlikte sınandı; bu committe stage edilmedi.

## CILA-YENI-7 / 3–4 — güncel görev paylaşımı ve Çizim Kâhini adı
- Madde 3 güncel dosyada Opus'a ayrıldı; Yağmur kodu/bankası/testlerine dokunulmadı. Madde 4'ün simgeleri ve diğer adları Opus yapmış; yalnız Çiz Tahmin → **Çizim Kâhini** ve kendi menü test beklentisi değiştirildi. `stant_app.py`, KAPALI, TKM ve Opus'un test/AD değişiklikleri stage edilmedi.
- Ayrı menü/ad/ikon testi: `pytest -q kabul_prototip/test_ciz_tahmin.py kabul_prototip/test_stant_app.py -k "menu or ikon or kayıt or kayit" -p no:cacheprovider` → **9 passed, 20 deselected, rc 0**, 14,48 sn. Menü üretiminde 9 simge, son ad ve TKM kapalı {6} assertleri rc 0.
- TEMP/cila_kareler/menu.png açıldı: Kâ harfi doğru; dokuz ayrı simge ve soluk TKM görülüyor. Bu commit yalnız kalan ad/test ve bu kaydı içerir. Tam takım son Penaltı doğrulamasıyla yeniden koşulacak.

## CILA-YENI-7 / 5 — Altın Vuruş doğrulama, önce
- Kaynak/galeri kontrolü: oyun yazılarında çek-bırak, germe, sapan kalıntısı yok. Yön tersine dönmüyor; hız/ivme güç, kavis falso üretiyor; mevcut fizik yeniden tasarlanmayacak.
- İki görsel eksik bulundu: tanıtımda topa dokunup yol çizmek yerine salınan makas eli var; uçuşta yalnız kısa noktalı kuyruk var, sürekli parlayan yol yok. TEMP/cila7/once/p_penalti_galeri.png açıldı. Yalnız bu ikisi düzeltilecek; Opus'un Altın Vuruş AD satırı stage edilmeyecek.

## CILA-YENI-7 / 5 — Altın Vuruş doğrulama, sonra
- Parmak topa değerek kaleye doğru kavisli yol çizer; tanıtımın tek parmağı, başlangıç noktası ve hareketi test edildi. Uçuşun fizik noktaları topa kadar sürekli ince sarı çekirdek + geniş saydam ışıkla çiziliyor. Yön/hız/ivme/falso fiziği değişmedi; Enes tekrar denesin.
- Yeni testler önce **2 failed, rc 1**. Ayrı `pytest -q kabul_prototip/test_cila7_penalti.py kabul_prototip/test_penalti.py kabul_prototip/test_cila_penalti.py -p no:cacheprovider` → **22 passed, rc 0**, 51,72 sn; 2005 gürültülü kare dahil.
- Önce/sonra TEMP/cila7/{once,sonra}/p_penalti_galeri.png açıldı. Son görüntüde topa değen tek parmak ve kesintisiz sarı uçuş izi var. Sentetik kişi zemini kullanıldı; gerçek kamera insan kabulü değil.
- `olcum.py --kiyas --kareler 100` → rc 0; Penaltı p95 **14,27 ms**, Çiz **14,75 ms**. Ek 200 aktif kavisli uçuş karesi: p50 **8,47**, p95 **10,27 ms**, ≤20 assert rc 0; kamera/algı hariç. Eski Gülme/Mask kapsam dışı >20 ms, değiştirilmedi.
- Gerçek insanla/fareyle iki tur kontrol edilmedi. EXE kaynakları açar; açık Stant kapatılıp yeniden açılmalı. Opus'un Altın Vuruş AD/test adı, diğer kirli dosyaları ve TKM/KAPALI korunuyor; yalnız kendi görsel yamaları ayrı stage edilecek.

- Son tam takım: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider` → **240 passed, 32 skipped, rc 0**, 330,02 sn. 202 tabanı düşmedi; Kuş/Çiz/Penaltı 2005'er gürültülü kare testleri dahil. Son ad değişikliği de bu tam koşuda doğrulandı.
- Bana ayrılan 0, 1, 2, kalan 4 ve 5 işleri tamamlandı; her biri ayrı yerel commit. Güncel dosyada 3 Opus'a ait; onun bankasını veya modlarını tamamlandı diye raporlamıyorum. Push, add -A, stash, checkout kullanılmadı.

## 2026-10-14 — 12 / İnsan Dizisi: uygulama ve otomatik kabul

- İşlem Dizisi ve Cümle Dizisi ortak `dizi_motor.py` üzerinden çalışıyor; menü 11 oyun, ikinci sayfa N/B, yerel 1/2 seçimi. Yalnız poz modeli; 3/4/5 + Boşluk ve el kaldırarak başlatma. Kartlar, 5 soruluk tur, sayım toleransları, izleyici reddi, kayıp/geri dönüş, görünüş imzası ve belirsiz çift takası eklendi.
- Cümle bankası 105 kayıt: 3 kişi 25, 4 kişi 50, 5 kişi 30. Enes ilk taslağı ve 21 kayıtlık düzeltmeyi ayrı ayrı onayladı; durum `onayli`. Sema/kelime kartı kontrolü rc 0. İşlem doğrulaması tam rasyonel aritmetik; 10.800 üretilmiş soru kontrol edildi.
- Sayısal K kaydı TEMP JSONL'ye 33 landmark, tahmin bayrakları, tam gövde/saç imza vektörleri, eşlemeler, olaylar ve başlangıç durumunu yazar. Görüntü kaydetmez. D/Y operatör etiketleri; kamera olmadan `--tekrar`, yalnız poz kimliğini kullanan `--imzasiz` tabanı. Etiketsiz doğruluk null; Y'den farklı yeni eşlemelerin doğruluğu bilinmeyen sayılır. K/D/K gerçek oyun tuş yolu her iki oyunda, iki deterministik tekrar modu ile rc 0; bu sentetik kanıttır, insan kabulü değildir.
- Yeni testler: motor 20, imza 14, içerik 18, kayıt/tekrar 5 = 57 vaka. Menüdeki 17 mevcut test ile odaklı komut: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip/test_insan_dizisi.py kabul_prototip/test_kimlik_imza.py kabul_prototip/test_dizi_icerik.py kabul_prototip/test_dizi_olcum.py kabul_prototip/test_stant_app.py -p no:cacheprovider` → **74 passed, rc 0**, 33,84 sn. Son kayıt raporu düzeltmesinden sonra kayıt/tekrar beş testi yeniden **5 passed, rc 0** (0,84 sn).
- Tam paket: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider` → **302 passed, 32 skipped, 2 failed, rc 1**, 304,89 sn. İki hata başlangıçta da vardı: `test_cekirdek::test_gezgin_prototipleri_kesfeder_ve_arayuz_tam` mevcut Yağmur'un `kalabalik` ihtiyacını tanımıyor; `test_rekabet::test_menu_iki_kart_ve_cizim` eski TKM menü indeksini bekliyor. Görev dışı üretim/test beklentileri değiştirilmedi. Başlangıç: 245 passed, 32 skipped, aynı iki failed.
- `dizi_olcum.py --gurultu` → her oyunda **2000 aktif oyun karesi**, toplam 4000, rc 0. Eksik/NaN landmark, 2–6 kişi, düşük görünürlük ve boş kare dahil. Sekiz sentetik PNG gerçek `isle()` çizimiyle üretildi ve incelendi; `C:/w/insan-dizisi-kabul-20261013/onizleme/`. İşlem/Cümle ekranları yan panelde açıldı.
- Son hız komutu: `app/.venv/Scripts/python.exe prototipler/olcum.py --kiyas --kareler 300` → **rc 0**, kamera/algı hariç, 1280×720 ve beş renkli poz:

| Bileşen | Medyan ms | p95 ms | Hedef |
|---|---:|---:|---|
| İşlem Dizisi | 6,51 | 8,65 | medyan ≤14, p95 ≤25 |
| Cümle Dizisi | 6,85 | 9,05 | medyan ≤14, p95 ≤25 |
| 5 görünüş imzası | 1,60 | 1,71 | medyan ≤2 |

- Sır taraması: görev dosyalarında TruffleHog `filesystem --no-verification --no-update --fail --fail-on-scan-errors` → 0 bulgu, **rc 0**. Derleme/18+ gerçek test/AST kabul hilesi kontrolü rc 0. Önceki prototip SHA256 karşılaştırmasında yalnız görevdeki `stant_app.py`, `olcum.py`, `kimlik_imza.py` değişti; kalan prototipler korundu. Gemini kapısında kilitli mevcut modelin ad eşlemesine tek alias eklendi; alternatif model kullanılmadı. Commit/push yapılmadı.
- **Açık kabul:** fiziksel 3–5 kişi ve gerçek kamera ile §9'daki beş senaryo, her biri en az 10 çaprazlama; laptop ve HP kamera ayrı ölçülecek. Sessiz yanlış/belirsizlik oranlarına ilişkin saha sonucu henüz yok. Operatör ve komut kılavuzu: `codex/DIZI-OLCUM.md`.