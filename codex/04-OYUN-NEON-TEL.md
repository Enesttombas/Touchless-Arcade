# 04. Neon Tel: parmak ucuyla labirent (Fikir 2)

Dosya: `prototipler/p_neon_tel.py`. `IHTIYAC = {"el"}` (Burun modunda `{"yuz"}`).

## Enes'in sorusu
"Kuş bakışı 2B labirentte parmak ucuyla duvarlara değmeden sona gidelim. Parmak ucu çok hassas ve
gecikme var. Bunu nasıl yapabiliriz?"

## Yorum: sorunun dört ayrı parçası var
1. **Titreşim:** ham parmak ucu kare kare birkaç piksel oynar. Dar koridorda bu, oyuncu hiç hareket
   etmezken bile duvara değmesi demektir.
2. **Gecikme:** bugünkü kablosuz hatta (HP kamerası 15 FPS + hotspot + Moonlight) ekrandaki imleç
   gerçek parmağın yüzlerce ms gerisinde olabilir. Bunun sayısı 00'daki camdan cama ölçümüyle alınır.
   Oyuncu imleci görerek düzeltme yapar; gecikme bu döngüyü salınıma sokar. Yanlışa düzeltme, sonra aşma.
3. **Kopma ve ışınlanma:** el bir kare kaybolup başka yerde bulunursa imleç duvarın içinden "ışınlanır".
   15 FPS'te hızlı el iki kare arasında 50+ px yol alır.
4. **Yorgunluk:** kolu havada tutmak 30–40 sn sonra yorar ("gorilla arm"). Tur kısa olmalı.

Bu yüzden saf "imleç = parmak ucu, değersen ölürsün" tasarımı stantta başarısız olur. Aşağıdaki
tasarım her parçayı ayrı çözer. Hepsi uygulanırsa oyun gecikmeli hatta bile oynanır. Dar koridorlu
zor seviyeler yalnız Ethernet + USB kamera hattında açılır.

## Tasarım: "elektrikli tel" (buzz wire) teması
Lunaparktaki klasik "tel halkayı değdirmeden götür" oyunu herkesin bildiği bir mekanik. Labirent
duvarları neon elektrik telleri, imleç parlayan bir enerji küresi. Duvara yaklaşınca vızıltı yükselir,
kıvılcım saçılır. Değince elektrik çarpar.

### Kontrol: parmak imleci "çeker", imleç parmak değildir
- Oyun mantığı **imleç** üzerinden çalışır. İmleç, süzülmüş parmak ucunu (01 §3) **hız tavanıyla**
  izler (ör. 900 px/sn). Ani sıçramada imleç ışınlanmaz, yolu boyunca ilerler.
- **Kaydırmalı çarpışma:** imlecin bu karede kat ettiği doğru parçası boyunca örnekleme yapılır.
  Labirentin mesafe haritası (`cv2.distanceTransform`, bir kez hesaplanır) her örnekte O(1) okunur.
  Hızlı hareket duvarı atlayamaz.
- **Tut-bırak:** oyun, parmak ucu başlangıç küresinin üstünde 0.5 sn tutunca başlar (halka dolar).
  El kaybolursa ya da parmak imleçten 90 px'ten uzağa kopuk düşerse imleç **donar** ve gri olur.
  Devam etmek için parmak donmuş imlecin üstüne getirilip 0.3 sn tutulur. Elini çekip labirentin
  sonuna koyarak hile yapmak böylece imkânsız olur.
- **Burun modu** (isteğe bağlı, `Boşluk` ile): imleci burun ucu sürer. Kafa hareketi parmaktan yavaş
  ve kararlıdır; yüz algısı daha az titrer. Hassas seviye için iyi bir alternatif, ayrıca seyirciye çok komik görünür.

### Affedici çarpışma
- Duvarın **görsel kalınlığı** çarpışma kalınlığından büyük. Değme yarıçapı görselin ~%70'i.
- **Uyarı bölgesi:** duvara < 25 px yaklaşınca küre turuncu olur, vızıltı ve kıvılcım artar. Oyuncu
  değmeden düzeltme şansı bulur. Gecikmeye en iyi panzehir bu.
- **Değince:** "zap" sesi ve beyaz flaş gelir. 1 can gider (3 can). İmleç son geçilen kontrol noktasına
  (her ~%20 yolda bir ışıklı halka) döner. Baştan başlamak yok.
- Skor = süre + değme cezası. Oturumun en iyi 5 süresi tutulur.

### Koridor genişliği kuralı (sayısal)
`koridor ≥ 2 × (imleç yarıçapı + titreşim_p95 + v_tipik × gecikme)`.
Örnek: yarıçap 14 px, titreşim 3 px, tipik el hızı 300 px/sn, gecikme 0.15 sn → ≥ 2×(14+3+45) ≈ 124 px.
Kolay seviye bu yüzden geniş başlar. `olcum.py --titresim` ve 00 ölçümü varsa genişlik bu
değerlerden **otomatik** ayarlanır (`veri/filtre_ayar.json`). Ekranda "Hassasiyet: Kolay/Orta/Zor" gösterilir.

### Seviyeler (her biri 20–35 sn)
1. **Isınma:** geniş, birkaç dönüşlü yol (koridor ~130 px).
2. **Labirent:** yinelemeli geri izleme (recursive backtracker) ile tohumlu üretilen ızgara labirent
   (koridor ~100 px), çözüm yolu ≤ 1.6 ekran genişliği. Tohum gösterilir; aynı labirentte rekabet edilir.
3. **Hareketli tel:** iki duvar parçası yavaşça kayar ya da döner.
4. **Karanlık:** yalnız kürenin çevresi aydınlık (el feneri efekti). Çok etkileyici, seyirci büyük ekranda bütünü görmek ister.

### Görsel
- Kuş bakışı ama düz değil. Teller hafif 3B kabartma: ışıklı üst yüz, koyu yan yüz ve zemine düşen yumuşak
  gölge. Kamera görüntüsü %25 parlaklıkta arkada kalır, oyuncu kendini görür.
- Küre arkasında ışık kuyruğu (öngörülü konumla çizilebilir, mantık süzülmüş konumla çalışır).
- Elektrik arkları: telle küre arasında rastgele kırık çizgi, mesafe azaldıkça sıklaşır.

## Gecikme bütçesi
- Ethernet + USB kamera hattında (hedef toplam ≤ 120 ms) bütün seviyeler.
- Kablosuz hatta yalnız 1–2. seviye ve geniş koridor. Oyun açılışında ölçülen gecikme ayardan okunur, zor seviyeler kilitlenir.

## Kabul (`test_neon_tel.py`, en az 8)
1. Labirent üretici: tohum aynıysa aynı labirent. Başlangıçtan bitişe yol var (BFS). Bütün koridorlar ≥ ayarlı genişlik.
2. Başlangıç küresinde 0.5 sn tutunca oyun başlar. Öncesinde imleç hareket etmez.
3. Parmak tek karede duvarın öbür yanına sıçrar: imleç ışınlanmaz, kaydırmalı çarpışma değme sayar
   ya da imleç tavanla duvara kadar ilerler. Duvarın içinden geçiş asla olmaz.
4. El kaybolunca imleç donar. Parmak başka yerde görünürse imleç kımıldamaz. Donmuş imlecin üstünde 0.3 sn sonra devam eder.
5. Değme: can −1, imleç son kontrol noktasında.
6. 3 değmede tur biter, sonuç ekranı gelir, ≤ 6 sn sonra bekleme.
7. Uyarı bölgesinde değme sayılmaz, uyarı bayrağı açık.
8. Bitişe ulaşınca süre kaydedilir, en iyi 5 sıralı.
- `--kiyas`: isle p95 ≤ 20 ms.
