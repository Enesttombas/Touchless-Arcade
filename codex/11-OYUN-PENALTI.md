# 11. Penaltı Düellosu: parmakla sapan şut, bedenle kalecilik (Enes 2026-10-12, en son yapılır)

Dosya: `prototipler/p_penalti.py`. `IHTIYAC = {"el", "poz"}` (şutçu el, kaleci poz + `Maskeci`).
Ortak: 01 (Oyuncu Kapısı, filtre, kimlik), 02 §3 (Verlet), 08 `rekabet.py` (raunt, kazanan, tekrar tamponu).

## Enes'in fikri
"Parmakla ivme ve yön verip penaltı kullanmak." Opus yorumu ve gerekçesi aşağıda. Kaynaklar sonda.

## Neden düz fiske olmaz
Mobil Flick Kick Football'da kaydırmanın açısı yönü ve falsoyu verir. Dokunmatik ekran saniyede 120+
örnek verir. HP kamerası ise ~15 FPS (00), yani 150 ms'lik bir fiske 2–3 nokta eder. Bu noktalardan
yön kaba çıkar, falso hiç çıkmaz. Gecikme de fiskeyi geç yakalatır.
**Kural:** yön, güç ve falso **yavaş konum hareketinden** okunur. Hızlı hareket yalnız tetiktir.

## Şut kontrolü: sapan
Durumlar: `bekle → kilit → ger → ucus → sonuc`.
1. **Kilit:** şutçunun işaret parmağı ucu (01 §3 filtreli) ekrandaki topun üstünde (yarıçap + 30 px)
   0.3 sn durur. Halka dolar, top parlar. Oyuncu Kapısı'ndan geçmemiş el kilitleyemez.
2. **Ger:** parmak topun gerisine çekildikçe yön, güç ve falso hesaplanır:
   - çekme vektörü `d = top − parmak`,
   - **yön** = `d`'nin açısı (yatay sapma ±25°, dikey 0–18°),
   - **güç** = `|d|`, gövde ölçüsüyle normalize (omuz genişliği; yoksa göz arası × 4), 0.25–1.0'a kırpılır,
   - **falso** = çekme yolunun yanal sapması: yolun en uzak noktasının başlangıç-son kirişine işaretli
     uzaklığı / `|d|`, −1..1. En az 6 örnek yoksa falso 0.
   - Tahmini yörünge her karede noktalı çizgiyle çizilir (falsolu, aşağıdaki fizikle). Oyuncu
     nereye gideceğini görerek nişan alır. Gecikme burada yalnız çizginin yavaş izlemesi demek; adil.
3. **Tetik:** parmağın topa doğru hızlı hamlesi (2 kare içinde hız > eşik, ~1.2 gövde/sn).
   Ayrık olay olduğu için 15 FPS'te de yakalanır. Tetik anındaki son *gerili* değerler kullanılır,
   tetik hareketinin kendisi yönü bozmaz.
4. **İptal:** el kaybolursa ya da parmak 2 sn hareketsiz kalırsa kilit düşer, top yerine döner. Ceza yok.
- Ekrandaki öğretici yazı (≤ 8 kelime): "Topu tut, geri çek, fırlat!" ve hayalet el animasyonu (10'daki gibi).

## Top fiziği (3B, metre cinsinden)
- Penaltı noktası kale çizgisinden 11 m. Kale 7.32 × 2.44 m. Top yarıçapı 0.11 m.
- Başlangıç hızı `v0`: güçten 18–30 m/sn (gerçek penaltı ~25–30). **Oyun zamanı yavaştır:** uçuş
  1.2–1.5 sn sürecek şekilde zaman ölçeği ayarlanır. Son 0.35 sn ağır çekim (×0.4).
- İvme: `a = g + k_m·(ω × v) − k_d·|v|·v` (yerçekimi, Magnus, sürtünme). `ω` falsodan, dikey eksende.
  Sabit adım 1/120 sn ile entegre et, kare süresinden bağımsız.
- Ekrana perspektif izdüşümü: kamera penaltı noktasının 2 m gerisinde, 1.6 m yükseklikte. Top
  uzaklaştıkça küçülür, gölgesi zeminde.
- Uçuş süresi kuralı: `uçuş ≥ 4 × ölçülen gecikme` (`veri/filtre_ayar.json` ya da 00 ölçümü). Yoksa varsayılan 1.3 sn.

## Kaleci: beden
- Kalede, kalecinin `Maskeci` silüeti ölçeklenip durur. Gerçek boydan bağımsız olarak kalecinin
  boyu ~1.9 m'ye ölçeklenir; uzun ya da kısa olmak avantaj değil. Silüete neon kenar ve eldiven
  sprite'ı (bilek noktalarında) eklenir.
- Kurtarış testi top kale çizgisini geçtiği karede yapılır:
  - top dairesi el dairesiyle (bilek → orta parmak ucu, yarıçap 0.18 m) kesişiyorsa **tutuş**,
  - gövde maskesiyle kesişiyorsa **sektirme** (top yansır, sekme fiziği),
  - hiçbiri değilse ve kale içindeyse **gol**,
  - direk ya da üst direkle kesişiyorsa sekme sesi, gol değil.
- Kalecinin konumu 01 §3 ile süzülür. Öngörü τ ≤ 0.05 sn. Kaleci zıplayıp çömelebilir. Poz kaybı
  0.4 sn'ye kadar son konumla doldurulur.
- **Tek kişilik mod (YZ kaleci):** YZ, sapma ihtimaline göre atlar. Oyuncunun son 5 şutunun köşe
  dağılımını öğrenir ve ekranda "Kaleci seni okuyor: %70 sağ" der. Zorluk her golde artar.
- **Tek kişilik mod (Kaleci Challenge):** oyuncu kalede, YZ art arda 10 şut çeker, hız ve falso
  kademeli artar. Kurtarış sayısı oturum rekoru olur.

## Akış ve modlar
- **Düello (varsayılan, iki kişi):** soldaki şutçu, sağdaki kaleci (kimlik 01 §4). 5'er atış,
  her atıştan sonra roller değişir, eşitlikte seri penaltı. Bir tur ~60–90 sn.
- **Tek kişi:** yalnız el görünürse YZ kaleciye şut, yalnız tam beden görünürse Kaleci Challenge.
- **Seviye 2, Frikik:** top ile kale arasına 4 kişilik baraj (9.15 m). Düz şut barajda kalır, falso şart.
  Düello 5–5 biterse seri penaltı yerine frikik turu da seçilebilir.
- Sonuç ekranı ≤ 6 sn: skor, en hızlı şut (km/sa, gerçek ölçeğe göre), en iyi kurtarış.

## Görsel ve ses ("4D")
- Derinlikli kale, çim dokusu, gece stadyumu ışığı, tribün siluetleri (paralaks).
- **Fizikli ağ:** ağ 16×8 Verlet ızgarası; top çarpınca şişer ve dalgalanır (02 §3).
- Topta dönme çizgisi ve iz; falsolu şutta iz kavisli.
- Gol: "GOL" patlaması, konfeti, tribün sesi. Ardından son 1.5 sn yandan sanal kamerayla ağır çekim
  (fizik geçmişinden yeniden çizim; kamera görüntüsü kaydedilmez).
- Kurtarışta kalecinin silüeti 0.4 sn donar ve parlar, "KURTARIŞ!" yazar.
- Bilim Modu (`B`): yörünge denklemi, Magnus vektörü, gerilen yol noktaları ve falso hesabı.

## Gecikme bütçesi
Şut tarafı ≤ 300 ms (nişan yavaş, tetik ayrık). Kaleci tarafı uçuş süresiyle dengelenir (yukarıdaki kural).

## Kabul (`test_penalti.py`, `PROTOTIP=p_penalti`, en az 12)
1. Parmak topta 0.3 sn → kilit. 0.2 sn → kilit yok. Kapıdan geçmemiş el → kilit yok.
2. Düz geriye çekme → yatay sapma ≈ 0 (±2°), falso ≈ 0.
3. Sola çekme → top sağa gider (sapan ters yönü). Aynalı görüntüde işaret doğru.
4. Kavisli çekme yolu (yay) → falso işareti yolun bükülme yönüyle tutarlı. 6 örnekten az → falso 0.
5. Güç: çekme mesafesi iki katına çıkınca `v0` artar, sınırlarda kırpılır.
6. Tetik: 2 kare içinde eşik üstü hamle → şut. Yavaş ileri hareket → şut yok.
7. Fizik: falsosuz ortadaki şut kale merkezine iner (±0.1 m). Falsolu şut aynı yöne kıvrılır.
   Adım süresinden bağımsız (1/30 ve 1/60 kare döngüsünde iniş farkı < 0.05 m).
8. Uçuş süresi ayarlı gecikmenin ≥ 4 katı (0.3 sn gecikmede ≥ 1.2 sn).
9. Kaleci: el dairesi top yolunda → tutuş. Gövde maskesinde → sektirme. İkisi de değil, kale içi → gol. Direk → sekme, gol yok.
10. Düello: 5'er atış sonrası skor doğru, eşitlikte seri penaltı, roller her atışta değişiyor.
11. YZ kaleci: oyuncu 5 kez sağa atınca YZ'nin sağa atlama oranı ≥ %60.
12. Frikik: düz şut baraja çarpar, yeterli falsolu şut barajı geçer.
13. El kaybında kilit düşer, top yerine döner, atış hakkı yanmaz.
- `--kiyas`: isle p95 ≤ 20 ms (ağ fiziği ve silüet dahil).

## Kaynaklar (bkz. konuşma araştırması, 2026-10-12)
- Flick Kick Football, kaydırma açısıyla yön ve falso; arcade modunda barajlar:
  [PocketGamer](https://www.pocketgamer.co.uk/articles/024906/r/), [TouchArcade](https://toucharcade.com/games/flick-kick-football-kickoff).
- Kinect Sports penaltı: biri kaleci, biri şutçu; "Super Saver" kalecilik oyunu:
  [Wikipedia](https://en.wikipedia.org/wiki/Kinect_Sports), [Giant Bomb](https://www.giantbomb.com/games/3030-31703/).
- MotionSports kaleciye karar süresi için ağır çekim kullanıyor: [PureXbox](https://www.purexbox.com/reviews/2010/11/motionsports_360).
- Gerçek penaltıda top 0.4–1.2 sn'de kaleye ulaşıyor. Kaleci tepkisi ölçüme göre 0.37 sn ile 0.7+ sn arası:
  [250 penaltı çalışması](https://lida.sport-iat.de/dfb/Record/4017215?lng=en), [Motricidade 2024](https://revistas.rcaap.pt/motricidade/article/view/31429).
  Bu sayılar tasarım gerekçesidir, oyun sabiti değildir. Oyun sabitleri bizim gecikme ölçümümüzden gelir.
