# Stant AR oyunları, faz 2: plan raporu

Hazırlayan: Claude Opus 5.5 · 2026-10-12 · İsteyen: Enes · Uygulayıcı: Codex

Kod yazılmadı. Bu rapor araştırmayı, yorumları ve Codex için hazırlanan şartname paketini özetler.
Şartnameler: `work/meme-kamera/codex/`.

## 1. Kısa sonuç

- Yedi fikrin hepsi mevcut altyapıyla (MediaPipe yüz/el/poz + maske, `stant_app.py`) yapılabilir.
  Önce iki altyapı sorunu çözülmeli. Biri **yanlış oyuncu algısı** (tırnak ucu bile oyuncu sayılıyor).
  Öbürü **görüntü/kamera hattının gecikmesi**. İkisi çözülmeden yeni oyunlar stantta kötü görünür.
- HP ekranın HDMI'ı görüntü almıyor çünkü **440 G3'te HDMI yalnız çıkış**. Bu bir güvenlik kilidi değil,
  donanım özelliği (HP föyü; görüntü girişi ancak 440 G9'da var). Çözüm: laptop ile HP arasına doğrudan
  **Ethernet kablosu** ve Sunshine/Moonlight 1080p60. Kamera HP'nin kendisi; ağdan yalnız en son kareyi taşıyan bir köprüyle gelir.
- Amiral gemisi: **Cevap Yağmuru** (Fikir 1). Hızlı kazanç: **Parmak Kuşu** (Fikir 3). Hocaya:
  **Sihirli Pencere** + **Sıvı Ayna** + **Bilim Modu**.

## 2. Üretilen dosyalar

| Dosya | İçerik |
|---|---|
| `README.md` | Codex'in kuralları, okuma ve yapım sırası, proje gerçekleri, kare bütçesi |
| `00-DONANIM-VE-YAYIN.md` | HDMI teşhisi, Ethernet + Sunshine kurulumu, kamera köprüsü, USB kamera seçeneği |
| `01-ALTYAPI.md` | Ölçüm aracı, **Oyuncu Kapısı**, One Euro filtre + öngörü, çok kişi kimlik takibi |
| `02-AR-KALITE.md` | Daha iyi insan analizi, 3B nesne + oklüzyon, "4D" efektler, GPU cila |
| `03`–`07` | Beş oyun şartnamesi (Fikir 1, 2, 3, 5, 7) |
| `08-REKABETCI-OYUNLAR.md` | Fikir 6: Kovboy Düellosu, Taş-Kağıt-Makas, Duvardaki Delik, Heykel |
| `09-HOCAYI-ETKILEYECEK.md` | Fikir 4: Sihirli Pencere, Sıvı Ayna, Kaputun Altı, hoca turu senaryosu |
| `ARASTIRMA-KAYNAKLAR.md` | İki web araştırmasının özeti; her iddia YEREL / KAYNAK / ÖLÇ diye sınıflı |
| `OLCUM-PROTOKOLU.md` | 240 FPS telefonla camdan cama gecikme ölçümü |

Her şartnamenin sonunda kör kabul testleri var (toplam ~90 test). Codex yeşil olmadan sonraki dosyaya geçmez.

## 3. Yedi fikir: yorum ve öneri

**1. Cevap Yağmuru (kelimeler insanlara gelir).** En güçlü fikir. Stantın kimliği olabilir. Ekranı 2–3
şeritli bir ışık koridoruna çevirdim. Kişinin şeridi kalça ortasından okunur (el sallamak yanlış seçim
yaptırmaz). Kelimeler perspektifle yaklaşır, çarpma anında ağır çekim olur. Doğru cevapta kelime
yeşil yanıp kişinin **içinden geçer** (maske ile önde/arkada çizim). Yanlışta harfler kişinin üstüne
dökülür ve kırmızıya döner (Text Rain göndermesi). Ekler: kimlikli puan, 3 doğru serisine taç,
Hayatta Kalma modu, soru bankasında matematik üretilir, genel kültür elle doğrulanır.

**2. Neon Tel (parmakla labirent).** Sorunun dört parçası var: titreşim, gecikme, kopma/ışınlanma, kol
yorgunluğu. "İmleç = parmak, değersen ölürsün" stantta başarısız olur. Önerim lunaparktaki
"elektrikli tel" oyunu. İmleç parmağı hız tavanıyla **izler**, kareler arası yolu boyunca çarpışma
kontrol edilir, duvara yaklaşınca önce **uyarı** gelir, değince kontrol noktasına dönülür. Koridor
genişliği ölçülen titreşim ve gecikmeden formülle hesaplanır. Dar seviyeler yalnız kablolu hatta açılır.

**3. Parmak Kuşu (Flappy Bird).** Kuşu parmağa doğrudan yapıştırmak yerine **yay-sönüm** ile bağladım.
Kuş canlı görünür, titreşim ve küçük gecikme kendiliğinden gizlenir. Parmakla kuş arasında ışık bağı
olduğu için yazısız öğretir. İki el görünürse iki kuşlu düelloya döner. Zor modda gerçek Flappy:
parmakla yukarı fiske kanat çırpar.

**4. Hocayı etkileyecek.** Hoca renkli efektten çok "bu nasıl oluyor?" anına ve ardından kaputun
açılmasına etkilenir. (1) **Sihirli Pencere:** kafa takipli 3B ekran (Johnny Lee 2007). Kamera ekrana
gömülü olduğu için bizde iyi çalışır. (2) **Sıvı Ayna:** GPU'da akışkan simülasyonu, beden engel,
el kuvvet. (3) **Kaputun Altı:** canlı model çıktıları, filtre grafiği, gecikme şeridi. Her oyunda
`B` tuşu Bilim Modu'nu açar. 3 dakikalık hoca turu senaryosu dosyada.

**5. Neon Koşu (Subway Surfers).** Parmakla yapılabilir ama dışarıdan izleyene sıkıcı görünür.
Varsayılanı **beden modu** yaptım: adım atınca şerit değişir, zıplayınca zıplar, çömelince kayar.
Koşucu, oyuncunun maskelenmiş kendi silüeti. Engeller en az 1.2 sn önceden görünür. Parmak modu da var.

**6. Rekabetçi oyunlar.** Gülme Düellosu'nun tutma nedeni: tek cümle kural, yan yana rakip, seyirciye
komik, kısa ve kesin bitiş, gecikmeye dayanıklı. Bu ölçüyle sıralandı: **Kovboy Düellosu**
(erken çeken kaybeder), **Taş-Kağıt-Makas** (insan ya da sizi "okuyan" YZ'ye karşı), **Duvardaki
Delik** (Kinect klasiği, maske uyumu), **Heykel** (müzik kesilince don). Adil zamanlama: iki oyuncu
aynı karede karşılaştırılır, gecikme ikisine eşit yansır. Göz Kırpmama zaten var, ayrı yapılmadı.

**7. Çiz-Tahmin.** Klasik Pictionary'nin stant sorunu: kelimeyi ekranda gösterirsen herkes görür.
Önerim oyunun merkezine **yapay zekâyı** koymak. Kişi havaya çizer, model canlı tahmin eder
("Bence… balık!"). Yarış, YZ'ye en hızlı tanıtmak. Model Quick, Draw! verisiyle 25–40 kategoride
bizim eğittiğimiz küçük bir CNN olacak. Havada çizim ile veri seti arasındaki fark için ön işleme ve
artırma şart. İnsanlarla tahmin modu kartla ya da operatör ekranıyla ayrıca var.

## 4. İki acil sorun

**Yanlış oyuncu algısı.** Kodda menünün "kişi var" kararı ham algıya bakıyor. Kadrajın kenarındaki
yarım el bile oyuncu sayılıyor. Dedektörü sıkılaştırmak yerine tek bir **Oyuncu Kapısı** öneriyorum.
Kapı şunlara bakar: kare içindeki nokta oranı (kesik elin noktaları kare dışına taşar), en küçük boyut,
güven, kenar payı, süre histerezisi (0.3–0.4 sn görünmeden aday, 0.6–1 sn kaybolmadan düşmez). Ek
kurallar: sahibi olmayan el sayılmaz, hareketsiz poster yüzü süzülür. Oyuncunun yüzüne dolan bir
halka "seni gördüm" geri bildirimi verir.

**Ekran ve kamera.** Bugünkü hatta HP kamerası 15 FPS'te telefon hotspot'undan geçiyor, görüntü
Moonlight 720p30 ile geri dönüyor. Gecikmenin büyüğü burada. Çözüm sırası:
(A) laptop ile HP arasında doğrudan Ethernet, sabit IP, güvenlik duvarında yalnız gerekli portlar,
Sunshine 1080p60.
(B) HP kamerası için "yalnız en son kare" köprüsü (tampon birikmesi biter).
(USB webcam seçeneği Enes kararıyla kapsam dışı.) Gerçek gecikme 240 FPS telefon
videosuyla ölçülecek (protokol hazır).

## 5. Yapım sırası

00 donanım → 01 altyapı → 10 AR maske kontrolü → 03 Cevap Yağmuru → 05 Parmak Kuşu → 07 Çiz-Tahmin → 02 AR kalite →
08 (ilk üç oyun) → 04 Neon Tel → 06 Neon Koşu → 09 hoca deneyimleri → 11 Penaltı Düellosu.

## 6. Doğrulanan ve doğrulanmayan

- **Yerelde doğrulandı:** MediaPipe Windows'ta GPU kullanamıyor (`NotImplementedError`). torch CUDA
  RTX 4080'de çalışıyor. Kurulu onnxruntime'da CUDA yok. `cv2.ximgproc` var. moderngl kurulu değil.
- **Kaynakla doğrulandı:** HP 440 G3 HDMI yalnız çıkış. Quick, Draw! verisi CC BY 4.0, kategori dosyası
  ~97 MB. FaceLandmarker 4x4 kafa matrisi verebiliyor.
- **Ölçülmedi (tahmin):** araştırma raporlarındaki uçtan uca gecikme tablosu, Depth Anything hızları,
  hazır Quick Draw modelinin doğruluğu. Codex bunları ölçmeden karar vermeyecek.

## 6b. AR Maskeler: "kimse değiştirmeyi anlamadı" (ek, `10-AR-MASKE-KONTROL.md`)

Kodda maskeyi yedi ayrı şey değiştiriyor: göz kırpma (0.18 sn), kaş kaldırma (0.12 sn), baş eğme, el
sallama, avuç-yumruk, ok düğmesi ve **yüz varken bile 12 sn'de bir otomatik dönüş**. "Kendi kendine
değişti" etkisinin kaynağı otomatik dönüş, kırpma ve kaş. Kendini maskeyle gören kişi şaşırıp kaşını
kaldırıyor, bu da maskeyi değiştiriyor. Çözüm: maskeyi yalnız iki büyük ok düğmesi değiştirir (ele
0.6 sn tut, halka dolar). Yüz ifadeleri hiçbir şeyi değiştirmez, maskeyi canlandırır (ağız açınca ateş,
kaş kaldırınca kulak zıplar). Yüz varken otomatik dönüş kapanır. Yazısız 2.5 sn'lik hayalet el gösterimi
ve her değişimde "→ KEDİ" etiketi eklenir. Aynı ilke bütün oyunlara kural olarak yazıldı.

## 6c. Futbol: Penaltı Düellosu (ek, `11-OYUN-PENALTI.md`, en son yapılır)

Düz fiske HP kamerasının ~15 FPS'inde 2–3 nokta eder; yön kaba çıkar, falso hiç çıkmaz. Bu yüzden şut
sapan gibi atılır: parmakla topu tut, geri çek (yön, güç ve falso bu yavaş hareketten okunur, yörünge
canlı çizilir), hızlı bir hamleyle fırlat (yalnız tetik). Kaleci bütün bedeniyle oynar, kendi silüeti kalede
durur. Top oyunda 1.2–1.5 sn uçar ve son anda ağır çekime girer; bu uçuş ölçülen gecikmenin en az 4 katı
olur. 5'er atış, roller değişir; tek kişiye YZ kaleci ya da Kaleci Challenge; seviye 2 frikik barajı.

## 7. Kararlar (Enes, 2026-10-12)

1. **Ethernet kablosu sağlanacak.** Laptop ile HP arasındaki doğrudan kablo hattı uygulanır.
2. **Ayrı USB webcam yok;** kamera HP'nin kendi kamerası. "En son kare" köprüsü ve pozlama ayarı zorunlu.
3. **Veri/model indirme onaylandı** (Quick, Draw!, segmentasyon, derinlik modelleri).
4. **Text Rain metni:** Opus varsayılan koydu, `veri/text_rain.txt` ile değişir.
5. Açık: `work/meme-kamera` için ilk commit onayı; HDMI girişli TV sorusu (artık gerekli değil).

## 7b. MediaPipe GPU sorunu (ek ölçüm)

Laptop CPU'sunda el modeli 28–57 ms, poz 28–61 ms, poz + maske 70–97 ms sürüyor; yüz yalnız 13–16 ms.
Algı bu yüzden ~15–25 Hz'de kalıyor. Çözüm sırası (`02-AR-KALITE.md` §6): kişi sayısı ayarını oyuna
göre düşürmek (bedava), maskeyi torch CUDA'da çalışan bir video matting modeline taşımak (en büyük
kazanç), el/poz modellerini ONNX'e çevirip GPU'da koşmak (orta iş). WSL2 ve kaynak derleme önerilmez.

## 8. Codex'e nasıl verilir

Codex'i `C:\Users\Enes\Documents\EnesOS\work\meme-kamera` kökünde aç ve şunu yaz:

> `codex/README.md` dosyasını oku ve sırayla uygula. Önce `00` ve `01`. Her dosyanın Kabul bölümü
> yeşil olmadan sonrakine geçme. İlerlemeyi `codex/ILERLEME.md`'ye yaz. Commit ve indirme öncesi bana sor.
