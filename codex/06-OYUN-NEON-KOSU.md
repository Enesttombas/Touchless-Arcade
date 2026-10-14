# 06. Neon Koşu: Subway Surfers tarzı sonsuz koşu (Fikir 5)

Dosya: `prototipler/p_neon_kosu.py`. `IHTIYAC = {"el"}` (parmak modu) ya da `{"poz"}` (beden modu).

## Yorum: parmak mı, beden mi?
Enes parmak kontrolü önerdi. İkisini de yap; **stantta varsayılan beden modu** olsun:
- Beden modunda oyuncu sağa sola **adım atarak** şerit değiştirir, **zıplar**, **çömelir**. Seyirci
  oyuncunun bütün vücudunu oynarken görür. Kinect'in stantlarda tuttuğu tam olarak bu (bkz.
  araştırma). Ayrık hareketler gecikmeye toleranslı.
- Parmak modu masa başı/yakın oynayış için. Çalışır ama dışarıdan izleyene sıkıcı görünür.

## Tasarım
### Sahne
- Sözde 3B pist: kaybolma noktasına daralan 3 şerit, neon kenar çizgileri, hıza bağlı hız çizgileri ve
  hafif kamera sallantısı. Zemin ızgarası akar (80'ler synthwave estetiği).
- **Koşucu = oyuncunun kendisi:** paylaşılan `Maskeci` maskesiyle oyuncunun silüeti kesilir, küçültülür
  ve koşucu olarak pistin önünde çizilir. Silüete neon kenar ışığı eklenir. "Ekranda ben koşuyorum"
  etkisi, stantta en güçlü an bu. Maske yoksa neon çubuk adam yedeği çizilir.
- Engeller z'de doğar, perspektifle büyür. Üç tür:
  - **alçak bariyer** (zıpla),
  - **yüksek kiriş** (çömel),
  - **tren bloğu** (şerit değiştir).
  Ayrıca altın ve mıknatıs gibi güçlendiriciler var. Engel en az 1.2 sn önceden görünür olur.

### Kontrol eşlemesi
- **Beden modu:**
  - Şerit: omuz ortasının x'i kadrajın üçte birlik bölgelerine eşlenir. Sınırda %6 histerezis var, titreşimle şerit zıplamaz.
  - Zıplama: omuz ortası y'si, son 1 sn'lik taban çizgisinin gövde boyunun %12'si kadar üstüne 150 ms içinde çıkar.
  - Çömelme: omuz ortası gövde boyunun %18'i kadar altına iner.
  - Taban çizgisi yavaşça uyarlanır; oyuncu öne arkaya yürüyünce bozulmaz.
- **Parmak modu:**
  - Şerit: parmak x'i, histerezisle.
  - Zıplama: hızlı yukarı fiske ya da parmağın üst çizgiyi geçmesi.
  - Çömelme: yumruk jesti (`Closed_Fist`) ya da alt çizgi.
- Eylemler ayrık olaydır, bir eylem 0.6 sn sürer. Oyun mantığı "olay geldi mi" diye bakar, sürekli konuma bakmaz.

### Akış
- Bekleme: koşucu silüeti yerinde koşar, "Sağa-sola adım at, zıpla, çömel" ve 3 küçük animasyonlu ikon.
- 3-2-1, sonra 60–90 sn koşu. Hız 25 sn'de bir kademe artar. 3 can var. Çarpınca 1 sn yanıp sönen
  dokunulmazlık. Mesafe + altın = skor. Oturumun en iyi 5 skoru.
- İki oyuncu (beden modu, geniş kadraj): ekran ikiye bölünür, her yarıda bir pist. Çoğu stantta tek kişi
  daha okunur olduğu için bu isteğe bağlı.

## Gecikme bütçesi
Beden modu ≤ 250 ms, parmak modu ≤ 150 ms. Engel görünürlük süresi (≥ 1.2 sn) gecikmenin 5 katından büyük kalmalı.

## Kabul (`test_neon_kosu.py`, en az 8)
1. Sahte poz omuz ortası sol üçte birde → şerit 0. Sınırda ±%3 salınım şerit değiştirmez (histerezis).
2. Omuzlar 150 ms'de gövdenin %15'i kadar yükselir → zıplama olayı. Yavaş yükselme → olay yok.
3. Omuzlar %20 iner → çömelme.
4. Alçak bariyer + zıplama aktif → çarpışma yok. Zıplama yok → can −1.
5. Yüksek kiriş + çömelme → geçiş. Tren bloğu aynı şeritte → can −1.
6. Dokunulmazlık 1 sn içinde ikinci çarpmayı saymaz.
7. Engel doğuşundan çarpışma çizgisine süre ≥ 1.2 sn (en yüksek hız kademesinde de).
8. Parmak modu: fiske zıplatır, `Closed_Fist` çömeltir.
- `--kiyas`: isle p95 ≤ 20 ms. Maske silüeti dahil.
