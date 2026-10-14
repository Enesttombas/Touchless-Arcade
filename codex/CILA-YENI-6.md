# CİLA: yeni 6 oyunu en yüksek kaliteye çıkar (Enes 2026-10-12 gece)

Kök: `C:\Users\Enes\Documents\EnesOS\work\meme-kamera`. Python: `app\.venv\Scripts\python.exe`.
Enes'in değerlendirmesi: "Bitmiş ama her şey yarım yamalak, çok sorunlu." Bu turun amacı **yeni oyun
eklemek değil**, var olan 6 oyunu stantta gururla gösterilecek kaliteye getirmek. Kodu sen bizzat yaz.

## P0: Enes'in canlı test bulguları (önce bunlar, 2026-10-12 gece)

### Kovboy Düellosu: "elleri aşağı götürünce durduk yere restart atıyor"
> **İPTAL (2026-10-13):** Bu bölümdeki kılıf kutusu ve "el kaybı = hazır değil" kuralı oyunu kilitledi.
> Yerine `CILA-YENI-7.md` madde 0 geçer: "el görünmüyorsa hazırsın".
Teşhis (Opus, `p_refleks.py` `adim()`):
- El `y > .55Y` olunca `hazir`, sonra `y < .48Y` olunca "çekti" sayılıyor. İki eşik arası ~50 px.
- ATEŞ'ten önce elin titremesi, kolu düzeltmek ya da elin kadraj altından çıkıp başka yükseklikte geri
  gelmesi "erken" sayılıyor. Erken çekiş `raunt_bitir` çağırıyor, ziyaretçi bunu "restart" diye görüyor.
- Kadraj altına yakın el Oyuncu Kapısı'nda "kenarda" diye düşüp geri geliyor; bu da sıçrama üretiyor.

Yeniden tasarla (kurallar sabit, uygulama serbest):
1. **Kılıf bölgesi** ekranda görünür: alt %35'te her oyuncu için kendi renginde kutu. El kutuda 0.5 sn
   durunca kutu yeşil ve "HAZIR" olur. **Sinyal, bütün oyuncular hazır olmadan başlamaz.**
   Kilitlenme yasak: "bütün oyuncular" = şu an kamerada görünenler. 3 sn içinde kılıfa inmeyen ya da
   kadrajdan çıkan oyuncu o rauntta seyirci olur; en az 2 hazır oyuncu varsa raunt başlar. Tek kişi kaldıysa
   tek kişilik refleks moduna (rakip = süre rekoru) geçer. Ekran hiçbir durumda "bekliyor"da donup kalmaz.
   Algılama ve çekiş tespiti her karede anlık çalışır; hazırlık süresi yalnız sinyalden önceki bekleme içindir.
2. **El kaybı erken çekiş değildir.** Kutudan çıkan ya da kaybolan elin oyuncusu yalnız "hazır değil"
   olur, ekranda "ELİNİ BELE İNDİR" yazar. Raunt bitmez, sayaç durur.
3. **Erken çekiş** yalnız şu durumda: el kılıf çizgisinin **0.15Y üstüne** çıkar ve bunu **2 ardışık karede**
   korur. Erken çekişte büyük "ERKEN!" ve kısa ceza animasyonu. Raunt yalnız onay animasyonundan sonra
   yenilenir.
4. Çekiş (ATEŞ sonrası): el kılıf çizgisinin 0.15Y üstüne çıktığı **ilk kare**. Kare tabanlı adalet (`erken_kare`) aynı kalır.
5. Raunt arası: sonuç 2.5 sn görünür. Yeni raunt ancak herkes tekrar kılıfa inince başlar, kendiliğinden başlamaz.

Testler (gerçekçi gürültüyle): titreyen el (±30 px) erken sayılmaz; kadraj altına çıkıp dönen el erken
sayılmaz; tek karelik sıçrama erken sayılmaz; gerçek 2 karelik yükselişte erken sayılır; biri hazır
değilken sinyal gelmez.

### Taş-Kağıt-Makas: "oyunu anlamadım"
- **Kuralı anlatan giriş (≤ 4 sn):** üç büyük kart. Her kartta el pozu çizimi ve adı: ✊ TAŞ, ✋ KAĞIT,
  ✌ MAKAS. Altında "TAŞ makası, MAKAS kağıdı, KAĞIT taşı yener".
- **Ritim:** iki oyuncu yumruğunu sallar. Ekranda büyük "TAŞ… KAĞIT… MAKAS… ŞİMDİ!", her kelimede pop ve
  ses, hayalet el sallanır. "ŞİMDİ!"den sonraki 0.6 sn içindeki el şekli okunur.
- **Sonuç:** iki oyuncunun seçtiği şekil büyük ikonla kendi başının üstünde. Kazanan ikon kaybedeni ezer.
  Altında hangi kuralın uygulandığı yazar ("MAKAS kağıdı keser").
- **Tanıma güvenilir olmalı:** AR maskede `Closed_Fist`/`Open_Palm` stant mesafesinde güvenilmez çıktı.
  - MediaPipe jest etiketine tek başına güvenme. El noktalarından **parmak açıklık sayımı** yap
    (uç–eklem–bilek açısı): 0 açık = taş, 4–5 açık = kağıt, işaret + orta açık = makas.
  - İkisi uyuşmazsa noktalardan sayımı esas al.
  - El küçükse (bilek→orta eklem < 45 px) "YAKLAŞ" uyarısı ver, tur başlamasın.
  - Okunamazsa "Elini net göster", tur tekrar, ceza yok.

### Çiz Tahmin (`p_ciz_tahmin.py`, ayrı oyun): "çizilme sorunları"
Bu bulgu Kovboy ve TKM'den bağımsız, yalnız Çiz Tahmin oyununa ait: havada parmakla çizilen çizginin
kendisi sorunlu. Bu kurallar zorunlu, uygulaması serbest:
- **Kalem iniş/kalkış:** yalnız işaret parmağı açık ve orta parmak kapalıyken çizer (noktalardan, jest
  etiketinden değil). Histerezis: kalkmak için 2 kare kapalı gerekir. Kalem durumu parmak ucunda
  görünür (dolu daire = çiziyor, boş = kalemi kaldırdı).
- **Kopuk çizgi yok:** 15 FPS'te kareler arası nokta boşluğu çizgiyle (segment) birleştirilir, gerekirse
  ara nokta enterpolasyonu.
- **Yanlış uzun çizgi yok:** iki nokta arası > 0.12G ise ya da el > 0.25 sn kaybolduysa yeni çizgi başlar,
  ekranı boydan boya kesen çizgi oluşmaz.
- **Pürüzsüz:** uç nokta One Euro (01 `filtre.py`) ile süzülür. Kalınlık hıza göre 6–14 px, uçlar yuvarlak.
- **Silme ve bitirme:** avuç açık 1 sn silme (halka dolar); geri al = son çizgiyi sil (ekranda düğme, el tutma).
- Testler: 15 FPS kayıtlı yol, kesintisiz çizgi oluşturur. El kaybı sonrası yeni çizgi başlar. Sıçrama
  çizgi oluşturmaz. Orta parmak açıkken çizmez.

### Parmak Kuşu (`p_parmak_kusu.py`, ayrı oyun): "görseller berbat, oyun giderek hızlanmalı"
Bu bulgu yalnız Parmak Kuşu'na ait.
- **Görseller baştan:** düz şekiller ve renk kutuları kabul edilmez. Hedef "bitmiş mobil oyun" görünümü:
  - **Kuş:** gövde, göz, gaga, kanat çizilmiş karakter (sprite ya da prosedürel çizim). Kanat çırpma
    animasyonu en az 3 kare. Yükselirken burun yukarı, düşerken aşağı döner (±25°).
  - **Arka plan:** 3 katmanlı paralaks (gökyüzü gradyanı, uzak bulut/şehir silueti, yakın tepe/çim),
    katmanlar farklı hızda kayar.
  - **Borular/engeller:** gölgeli, kenarlı, ağızlı boru görünümü ya da tema uyumlu neon sütun. Düz dikdörtgen olmaz.
  - **Efekt:** her geçilen boruda "+1" pop ve kısa parıltı. Ölümde tüy parçacığı, ekran sarsıntısı, 0.3 sn yavaş çekim.
  - **Arayüz:** büyük skor (gölgeli, sayarak artan), oturum rekoru, sonuçta madalya (bronz/gümüş/altın eşiği).
  - Görsel kararlar `%TEMP%\cila_kareler` ekran görüntüleriyle önce/sonra kanıtlanır.
- **Giderek hızlanma (zorunlu):**
  - Kayma hızı skorla artar: başlangıç `v0`, her geçilen boruda +%4, tavan `2.2 × v0`.
  - Boru arası boşluk hız arttıkça hafifçe daralır (tabanı adil kalacak şekilde, en dar hâli ilk hâlin %75'i).
  - Hız artışı her 5 skorda ekranda kısa "HIZLANIYOR!" yazısıyla bildirilir.
  - Adalet: kuşun dikey kontrol tepkisi hızdan bağımsız kalır. Çarpışma kutusu görünenden %10 küçük.
  - Testler:
    - skor arttıkça kayma hızı tekdüze artar ve tavanı aşmaz;
    - boşluk tabanın altına inmez;
    - aynı girdiyle 1/60 ve 1/15 sn adımda boru konumu farkı < 5 px (kare süresinden bağımsız).

## Kapsam

**Dokunulacak (yalnız bunlar):**

| Oyun | Dosya | Şartname |
|---|---|---|
| Parmak Kuşu | `prototipler/p_parmak_kusu.py` | `codex/05-*.md` |
| Cevap Yağmuru | `prototipler/p_cevap_yagmuru.py` | `codex/03-*.md` |
| Kovboy Düellosu | `prototipler/p_refleks.py` | `codex/08-*.md` |
| Taş-Kağıt-Makas | `prototipler/p_tas_kagit.py` | `codex/08-*.md` |
| Penaltı Düellosu | `prototipler/p_penalti.py` | `codex/11-*.md` |
| Çiz Tahmin | `prototipler/p_ciz_tahmin.py` | `codex/07-*.md` |

- Bunların test dosyaları ve yalnız bu oyunların kullandığı yardımcılar (`rekabet.py` vb.) da kapsamda.
- Yeni ortak görsel yardımcı dosya açılabilir, örneğin `prototipler/gorsel.py`. Ortak modül
  (`cekirdek.py`, `oyuncu.py`, `filtre.py`) yalnız hata düzeltmek için değişir. Davranışı değiştirme.

**YASAK, dokunma:**
- Eski 3 oyun: `p_neon_kilic.py`, `p_gulmeme.py`, `p_maske.py`, ayrıca `__k*` kopyaları.
  - Testleri de: `test_cila.py`, `test_ozel*.py`, `test_maske_kontrol.py`, `test_stant_app.py`'deki mevcut testler.
    Çökme testi `test_stant_app.py`'nin sonuna eklenebilir.
  - AR maske Enes'in son kararıyla çalışıyor (başı yatır = değiştir, `10-AR-MASKE-KONTROL.md` başı). Geri alma.
- `stant_app.py`'de tek izin aşağıdaki "Çökme" maddesi. Menü/EV_SN/köşe davranışını değiştirme.
- `kurulum/`, `kamera_kopru.py` (00), HP/ağ işi, web araştırması, push.

## Zorunlu süreç (her oyun için sırayla)

1. **Ekran görüntüsü turu (önce bak, sonra düzelt).** `kabul_prototip/goruntule.py` yaz (test değil, araç):
   - Her oyunun her durumu (bekle, geri sayım, oyun, olay anı, sonuç) için sahte algıyla 3–5 kare üretip
     `%TEMP%\cila_kareler\<oyun>_<durum>.png` olarak kaydet. Bu klasör depoya girmez.
   - PNG'leri **kendin aç ve bak**. Her oyun için gördüğün kusurları `ILERLEME.md`'ye madde madde yaz:
     taşan yazı, üst üste binme, okunmayan renk, boş ekran, kadraj dışı çizim, yanlış ölçek.
   - Cila bitince aynı kareleri tekrar üret ve bak. Önce/sonra listesini yaz.
2. **Gerçeğe yakın girdiyle hata avı.** Testlerdeki temiz sahte veri gerçeği yansıtmıyor. Her oyunu şu
   girdilerle 2000+ karelik bir döngüde koştur, `isle()` hiç exception atmasın:
   - koordinatları `numpy.float64` olan, filtreden geçmiş noktalar. AR maskede `cv2.remap` tam bu sebeple çöktü;
     `cv2` fonksiyonlarına giden diziler `float32`/`int32` olmalı;
   - kare kare kaybolup geri gelen el/yüz/poz (her 5 karede 1–3 kare boş);
   - kadraj kenarında yarım el, 0–6 kişi aynı anda, `jestler` içinde `None`;
   - kare aralığı 1/60 ile 1/8 sn arasında oynayan zaman (HP kamerası ~15 FPS);
   - oyun ortasında herkesin çıkması ve 1 sn sonra geri gelmesi.
   Bulduğun her hatayı önce kırmızı bir testle yakala, sonra düzelt.
3. **Canlı his kontrolü (kamera yerine fare).** Mümkünse `FARE_EL=1` gibi bir geliştirici modu ekle: fare
   işaret parmağı ucunu taklit eder. Her oyunu bununla 2 tur oyna. Takılma, gecikme hissi, belirsiz
   kural varsa düzelt. (Kamerasız ortamda yalnız bu yol var.)
4. **Kabul:** oyunun test dosyası + tam takım yeşil, `olcum.py --kiyas` p95 ≤ 20 ms. Sonra o oyun için
   yerel commit (yalnız kapsamdaki dosyalar), `ILERLEME.md` bloğu (önce/sonra kusur listesi, komut, gerçek sonuç).

## Kalite çıtası (her oyunda zorunlu)

Stant ziyaretçisi 3 saniyede ne yapacağını anlamalı, oyun "ucuz demo" değil "bitmiş oyun" gibi durmalı.

- **Giriş:** oyun adı büyük, 1 satır kural (≤ 8 kelime), hayalet el/beden animasyonu ile nasıl oynanacağı gösterilir.
  "Hazır mısın? 3-2-1" geri sayımı ölçeklenen rakamlarla, ses ile.
- **Geri bildirim her olaya:** puan alınca sayı yükselip solar (+10), parçacık patlaması, kısa ekran
  sarsıntısı (≤ 6 px, 120 ms), ses. Hata/ölümde kırmızı flaş ve "yavaş çekim" 0.3 sn.
- **Hareket:** hiçbir öğe ışınlanmaz. Konum/ölçek/opaklık geçişleri easing ile (ease-out-back, 150–300 ms).
  Puan sayacı sayarak artar. Sahne geçişlerinde kayma veya solma var.
- **Tipografi ve renk:** başlık ≥ 48 px, gövde ≥ 26 px, uzaktan (3 m) okunur. Her yazının arkasında
  yarı saydam panel ya da kontur var. Kamera görüntüsü üstünde bile okunur. Oyun başına tek renk paleti,
  neon kontur + parıltı (`parilti`) tutarlı.
- **Oyuncu kimliği:** iki kişilik oyunlarda her oyuncunun rengi ve adı ("SOL"/"SAĞ" ya da P1/P2) başının
  üstünde. Kimin puan aldığı karışmaz.
- **Sonuç ekranı ≤ 6 sn:** kazanan büyük, konfeti, skor tablosu, "Tekrar: elini kaldır" ipucu. Sonra
  kendiliğinden bekleme durumuna döner.
- **Boşta:** kimse yokken çekici bir "vitrin" animasyonu (oyunun kendi sahnesinden döngü).
- **Kararlılık:** algı kaybında oyun donmaz ve ceza vermez; "Seni göremiyorum" uyarısı 0.5 sn sonra çıkar.
- **KAMERA GÖRÜNTÜSÜ ZEMİNDİR (Enes, kesin kural):** stant oyunlarının amacı insanların ekranda **kendilerini**
  görmesi. Kovboy, TKM, Penaltı, Cevap Yağmuru ve Çiz Tahmin'de canlı kamera karesi her durumda tam ekran zemin
  kalır. Oyuncunun yerine çizilmiş karakter, çöp adam ya da avatar **konmaz**. Atmosfer yalnız üstüne biner:
  renk tonu (≤ %35 karışım), vinyet, parçacık, çerçeve, yazı. Oyuncunun yüzü ve elleri her karede net görünür.
  Kabul: her oyunun ekran görüntüsü gerçek bir kamera karesiyle (`goruntule.py`) alınır ve kişi tanınır olmalı.
  Tek istisna Parmak Kuşu'nun oyun alanı; orada da kamera köşede ya da yarı saydam zeminde görünür.

## Oyun başına odak (şartnameyle birlikte oku)

- **Parmak Kuşu:** paralaks arka plan (3 katman), kanat çırpma animasyonu, borularda neon kontur, skor
  rekoru. Çarpışma kutusu görünenden %10 küçük (adil his). Ölümde yavaş çekim ve tüy parçacığı.
- **Cevap Yağmuru (amiral gemisi):** soru kartı büyük ve okunur. Düşen cevaplar dönerek iner. Doğru
  yakalamada yeşil patlama + "+10", yanlışta kırmızı titreme. Seri için alev sayacı, 3 doğru serisine taç. Kişi başına renkli puan
  sütunu. Soru bankasındaki yazım hatalarını ve belirsiz soruları ayıkla (liste ILERLEME'ye).
- **Kovboy Düellosu:** western atmosfer **kamera görüntüsünün üstüne** (gün batımı renk tonu, toz parçacığı, saloon yazı tipi hissi). Oyuncular kendilerini görür; çizilmiş kovboy yok.
  "ATEŞ!" anında ekran beyaz flaş + silah sesi. Erken çekene "ERKEN!" ve ceza animasyonu. Reaksiyon
  süresi ms ile büyük gösterilir. Adalet: zamanlama kare tabanlı ve `rekabet.py` ile aynı kalır.
- **Taş-Kağıt-Makas:** "TAŞ… KAĞIT… MAKAS!" ritmik sayım (her kelimede ölçek pop), el şeklinin büyük ikonu
  oyuncunun elinin yanında. Kazanan ikon kaybedeni "ezer" animasyonu. Jest tanınmazsa "elini net göster",
  tur iptal, ceza yok.
- **Penaltı Düellosu:** çim dokusu, stadyum ışığı, perspektifli kale. Ağ şişmesi görünür (Verlet zaten
  var, çizimini belirginleştir). Yörünge önizlemesi noktalı ve falsoyla kavisli. "GOL!" / "KURTARIŞ!"
  büyük. Gol sonrası ağır çekim tekrarı. Topun gölgesi ve dönme çizgisi.
- **Çiz Tahmin:** çizgi kalem gibi pürüzsüz (filtreli, kalınlık hıza göre). Tahminler canlı ilk 3 olarak
  barla gösterilir. Doğru tahminde konfeti. Kalem kaldırma/bırakma net ipucuyla.
  Yanlışlıkla çizgi oluşmasın: yalnız işaret parmağı açıkken çizer.

## Çökme (stant_app.py, tek izinli değişiklik)

Bugün bir oyunda exception olunca uygulama **sessizce ana menüye** atıyor. Ziyaretçi bunu "menüye attı"
diye görüyor (AR maskede yaşandı). Yeni davranış:
- `hata.txt`'ye yaz (var);
- aynı oyunu yeniden başlat (aynı kart, yeni örnek);
- 10 sn içinde 3. çökmede menüye dön ve ekranda 2 sn "Bu oyun dinleniyor" yaz.

Test: sahte bir oyunun `isle()`'si bir kez exception atar, uygulama aynı oyunda kalır. Üç kez atarsa menüye döner.

## Sıra ve zaman kutusu

1. Çökme davranışı (20 dk).
2. P0 bulguları: Kovboy (60 dk), TKM (60 dk), Çiz Tahmin çizim (60 dk), Parmak Kuşu görsel + hızlanma (75 dk). Her biri ayrı commit.
3. Cevap Yağmuru, Penaltı (90 dk her biri).
4. Kovboy, TKM, Çiz Tahmin ve Parmak Kuşu görsel cilası (45 dk her biri).

Süre dolunca oyunun kalan kusurlarını ILERLEME'ye "sonra" diye yaz ve sıradakine geç. Bitince Enes'e kısa
özet: her oyunun önce/sonra kusur sayısı, test sonucu (`N passed`), açık kalanlar.

## Bitti ölçütü

- 6 oyunun her birinde ekran görüntüsü kusur listesi kapatılmış (ya da "sonra" diye gerekçeli).
- Gürültülü girdi döngüsünde 6 oyunun hiçbiri exception atmıyor (testle kanıtlı).
- Tam takım yeşil, test sayısı düşmedi (taban: 162 passed).
- Eski 3 oyunda **senin** değişikliğin yok. Dikkat: `p_maske.py`, `test_cila.py`, `test_maske_kontrol.py`,
  `test_stant_app.py` içinde Opus'un commit edilmemiş değişiklikleri var (baş eğme ile maske, float32 remap,
  menü testi). Bunları **geri alma, düzenleme, stage etme**. Commit'lerinde `git add` ile yalnız kendi
  dosyalarını tek tek ekle; `git add -A` / `git add .` / `git checkout --` / `git stash` kullanma.
