# 09. Profesörü etkileyecek deneyimler (Fikir 4)

Enes: "Çok daha etkileyici, göz alan ve profesör hocamı etkileyecek neler olabilir?"

## Yorum: hocayı ne etkiler
Bir bilgisayar mühendisliği hocası "renkli efekt" görmeye alışkındır. Onu etkileyen iki şey var:
1. **"Bu nasıl oluyor?" anı:** gözünün önünde fiziksel olarak imkânsız görünen bir şey. Bunlar
   ekranın derinleşmesi, kendi bedeninin sıvıyı itmesi, kendi görüntüsünün 3B nokta bulutuna dönmesi.
2. **Sonra kaputun açılması:** aynı sahnenin altında çalışan modeli, sayıları, filtreyi ve gecikme
   bütçesini görmek. Arkasında mühendislik olduğunu kanıtlar.
Bu yüzden her gösteri **bir büyü + bir açıklama katmanı** olarak tasarlanır. `B` tuşu (Bilim Modu,
01 §1) her oyunda kaputu açar.

## Önerilen öncelik: 1 → 3 → 2 (sonra 4–6)

### 1. Sihirli Pencere: kafa takipli 3B ekran (`p_kafa_pencere.py`)
- Johnny Chung Lee'nin 2007 Wii Remote gösterisi (`ARASTIRMA-KAYNAKLAR.md`). Ekran bir pencereye
  döner: içinde derin bir oda ve havada süzülen nesneler var. Kişi kafasını sağa sola, öne arkaya
  oynatınca perspektif tam bir pencereden bakıyormuş gibi değişir. Gözlük gerekmez.
- Bizim avantajımız: kamera **ekranın üstüne gömülü** (HP), yani kamera-ekran konumu sabit ve biliniyor.
- Matematik (off-axis / asimetrik frustum):
  - Göz konumu `E = (ex, ey, ez)` ekran merkezine göre cm. ex/ey: iki göz ortası noktasının görüntü
    konumundan, kamera yatay görüş açısıyla. ez: göz bebekleri arası px'ten (yetişkin ortalaması ~6.3 cm),
    `ez = f_px × 6.3 / ipd_px`.
  - Ekran fiziksel ölçüsü (HP 440 G3, 23.8"): ~52.7 × 29.6 cm. Kamera ekranın üst kenarında ortada.
  - Frustum: `sol = (-W/2 - ex) × yakın / ez`, `sag = (W/2 - ex) × yakın / ez`, üst/alt benzer.
    Görüş matrisi gözü E'ye öteler. Ayrıntı: Kooima "Generalized Perspective Projection".
  - **Kalibrasyon:** f_px tek adımla bulunur: kişi ekrandan 60 cm uzakta durur, `C` tuşu. Sonuç
    `veri/pencere_ayar.json`'a yazılır.
- Sahne (CPU ile yeterli, GL varsa daha iyi): neon ızgaralı derin oda (5 duvar çizgi ızgarası), içinde
  dönen nesneler, odanın içinden ekranın **önüne** taşan bir nesne. Önüne taşma, yanılsamanın en güçlü
  anı. Göz konumu 01 §3 filtresinden geçer; öngörü τ ≤ 0.05 sn. Gecikme bu demoda yanılsamayı en çok
  bozan şey, bu yüzden 00'daki Ethernet + USB kamera hattında gösterilir.
- **Tek izleyici sınırı:** yanılsama yalnız takip edilen kişi için doğru. Ekranda "Pencereye tek göz
  bak, kafanı oynat" yazar, aktif kişinin yüzüne küçük bir halka konur. Seyirci başkasının bakışıyla
  hareket eden odayı görür, bu da merak uyandırır.
- Bilim Modu: köşede kuş bakışı diyagram: ekran, göz konumu, frustum çizgileri canlı. Hocaya
  "projeksiyon matrisini kafana göre her karede yeniden kuruyoruz" anı.

### 3. Sıvı Ayna: bedenle itilen akışkan (`p_sivi_ayna.py`)
- Jos Stam "Stable Fluids" (1999) ızgara akışkanı. Kişinin maskesi **engel**, el hızı **kuvvet**,
  parmak uçları **boya kaynağı**. Kişi elini savurdukça renkli duman girdap yapar, gövdeden sekip etrafından akar.
- Uygulama: **torch CUDA** (yerelde çalışıyor, 02 durum tablosu). Izgara 256×144, adveksiyon
  (yarı-Lagrange, `grid_sample`), basınç için 20–30 Jacobi iterasyonu, vorticity confinement ile
  girdap korunur. Boya 3 kanal, sönümlü. Sonuç yukarı ölçeklenip kameranın üstüne eklenir.
- Hedef: simülasyon adımı ≤ 6 ms (ölç). Tutmazsa ızgarayı 192×108'e düşür.
- GPU yoksa (HP'de ya da CUDA hatasında): 128×72 numpy yedeği ya da oyun menüde gizlenir.
- Bilim Modu: hız alanı okları, basınç ısı haritası, "Navier–Stokes, 25 iterasyon, 4.1 ms" etiketi.

### 2. Kaputun Altı: Bilim Modu sahnesi (01 §1'in sunuma dönüşmüş hali)
- 01 §1'deki `B` katmanı her oyunda çalışır. Buna ek olarak menüde ayrı bir **"Nasıl çalışıyor?"**
  deneyimi: aynı canlı görüntü 4 panele bölünür:
  1. ham kamera + gecikme sayacı,
  2. yüz örgüsü (478 nokta) + blendshape çubukları (gülümseme, kaş, ağız),
  3. el iskeleti + ham ve One Euro filtreli parmak izi grafiği yan yana (titreşimin nasıl söndüğü görünür),
  4. poz iskeleti + maske + kimlik numaraları.
- Altta boru hattı şeridi: `kamera 16 ms → ağ 4 ms → algı 18 ms → çizim 9 ms → ekran`. Gerçek ölçümden
  gelir (01 §1). Hoca için asıl kanıt bu.
- Kişi gülümseyince 2. paneldeki çubuk dolar. Etkileşimli olduğu için sıkıcı değil.

### 4. Hologram: tek kameradan 3B nokta bulutu (`p_hologram.py`, deneysel)
- Monoküler derinlik modeli (Depth Anything V2 Small) her kareden derinlik haritası çıkarır. Maskeli
  kişi pikselleri 3B noktaya dönüşür, yavaşça dönen mavi "hologram" olarak çizilir (Star Wars mesajı tadı).
- **Doğrulanmadı:** araştırma raporundaki RTX hız sayıları (ONNX CUDA ~13–20 ms) yerelde ölçülmedi
  ve onnxruntime'da CUDA sağlayıcısı yok (02). Torch CUDA ile çalıştır, önce hızı ölç.
  Model indirme onayı verildi (Enes 2026-10-12). Derinlik 10–15 Hz'de güncellense yeter, dönüş her karede.
- Kabul edilebilir değilse (≥ 40 ms ve kare düşüyorsa) bu fikir kapatılır, sonuç `ILERLEME.md`'ye yazılır.

### 5. Text Rain selamı (bekleme ekranı)
- Utterback & Achituv'un *Text Rain* (1999) eseri. Boşta, menünün arkasında, kişinin silüetine
  harfler yağar, omuzlarında birikir. Kişi kolunu kaldırınca harfleri tutar, kolunu çekince harfler düşmeye devam eder.
- Metin `veri/text_rain.txt` dosyasından okunur (satır başına bir dize, Enes istediği zaman değiştirir).
  Varsayılan (Opus seçti, Enes 2026-10-12 "sen bir şey koy"):
  `YAPAY ZEKÂ SENİ GÖRÜYOR` · `KOLUNU KALDIR, HARFLERİ YAKALA` · `KAMERA + SİNİR AĞI = SİHİR` ·
  `BİR OYUN SEÇ, BİR EL SALLA`. Harfler sütunlara dizeyi soldan sağa okuyacak sırayla dağıtılır;
  bir kişi kollarını açınca dize omzunda okunabilir hale gelir.
- 02 §3'teki maske mesafe alanını kullanır; ucuz. Stantın önünden geçeni durduran "çağrı" olarak en güçlü aday.

### 6. Galaksi Beden
- Kişinin maskesi 20–40k parçacığa örneklenir, parçacıklar kişinin şeklinde durur. El savrulunca
  galaksi gibi dağılır, yerçekimiyle geri toplanır. torch CUDA ile kolay. Görsel olarak çok güçlü ama
  "bilim" katmanı zayıf. Sıvı Ayna'dan sonra.

## Hoca turu senaryosu (3 dakika, operatör tuşlarıyla)
1. Text Rain bekleme ekranı (hoca yaklaşırken harfler omzuna yağar).
2. Sihirli Pencere (kafasını oynatır, nesne ekrandan taşar), sonra `B`: frustum diyagramı.
3. Sıvı Ayna (eliyle dumanı iter), sonra `B`: hız alanı.
4. Çiz-Tahmin (07): havaya çizer, YZ bilir, sonra `B`: 28×28 girdi + olasılıklar.
5. Kaputun Altı paneli: "bütün bunlar tek laptopta, gerçek zamanlı, gecikme X ms".
Operatör kısayolu: `H` tuşu bu sırayla deneyimler arasında ilerler.

## Kabul (`test_hoca.py`, en az 8)
1. Pencere: göz ekran merkezindeyken frustum simetrik (sol = -sağ).
2. Pencere: göz sağa kayınca frustum sola kayar, işaret doğru. ipd_px yarıya inince ez iki katı.
3. Pencere: kalibrasyon dosyası yokken varsayılan f_px ile çalışır, hata yok.
4. Akışkan: engel (maske) içindeki hız her adımdan sonra 0. Toplam boya sönümle azalır, patlamaz (NaN yok, 500 adım).
5. Akışkan: CUDA yokken yedek yol ya da menüde gizleme, istisna yok.
6. Kaputun Altı: boru hattı şeridi 01 §1 profilinden gelen sayıları gösterir (sahte profil ile).
7. Text Rain: maske üstüne düşen harf maskenin üst kenarında durur, maske çekilince düşmeye devam eder.
8. `H` turu: deneyim sırası doğru, son adımdan sonra menüye döner.
- `--kiyas`: Pencere ve Text Rain isle p95 ≤ 18 ms. Sıvı Ayna p95 ≤ 25 ms.
