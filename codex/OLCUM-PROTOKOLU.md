# Ölçüm protokolü: camdan cama gecikme ve kare bütçesi (tek sayfa)

Her gecikme iddiası bu protokolün çıktısına dayanır. Sonuç `codex/ILERLEME.md`'ye tabloyla yazılır.

## A. Camdan cama (glass-to-glass) toplam gecikme
Gereç: 240 FPS ağır çekim çekebilen telefon, sabit tripod ya da masaya dayanmış telefon.
1. Oyun: `PROTOTIP=p_olcum` (ya da Bilim Modu açık herhangi bir oyun). Ekranda büyük, keskin bir parmak
   ucu imleci çizilir, süzgeç **kapalı** (`FILTRE=0`). Filtre gecikmesi ayrıca ölçülür.
2. Telefon kadrajı aynı anda hem gerçek eli hem HP ekranını görsün. Işık yeterli olsun (bulanık kare sayılmaz).
3. El, ekranın önünde hızlı ve tek bir aşağı darbe yapar ve sert durur. 5 tekrar, aralarında 2 sn.
4. Videoda her tekrar için: gerçek elin durduğu kare `a`, ekrandaki imlecin durduğu kare `b`.
   Gecikme = (b − a) / 240 sn. Medyan ve en büyük değer raporlanır.
5. Hat başına tekrar et ve tabloya yaz:

| Hat | Kamera | Yayın | Medyan ms | En büyük ms | Not |
|---|---|---|---|---|---|
| Bugünkü | HP MJPEG 640x480@15 | hotspot + Moonlight 720p30 | | | |
| A | HP kamera köprüsü | Ethernet + Moonlight 1080p60 | | | |
| C | USB 60 FPS kamera laptopta | Ethernet + Moonlight 1080p60 | | | |
| Referans | laptop dahili kamera | laptop ekranı | | | yayın yok, alt sınır |

6. Filtre açıkken (`FILTRE=1`) aynı ölçümü yalnız seçilen hatta tekrarla. Fark, filtre gecikmesidir.

## B. Yazılım içi aşama zamanları (01 §1 `olcum.py`)
- Her kare için damgalar: çekim (köprü saati + ofset), alış, algı bitti, çizim bitti, `imshow`.
- 60 sn kayıt sonrası CSV ve özet: aşama başına medyan / p95. Kare bütçesi: `isle()` medyan ≤ 14 ms,
  p95 ≤ 25 ms.
- `--kiyas A B`: aynı kayıtlı sahte girdi akışıyla iki sürümü karşılaştırır. Her optimizasyon önce/sonra
  satırıyla raporlanır.

## C. Titreşim (01 §3 kalibrasyonu)
- El 5 sn hareketsiz, kameradan 1.5 m. Parmak ucu px konumunun standart sapması ve p95 sapması.
  Filtre kapalı ve açık. Sonuç `veri/filtre_ayar.json` (04 koridor genişliği buradan okunur).

## Kurallar
- Her ölçüm satırında tarih, hat, çözünürlük/FPS, kod sürümü (dosya değişiklik zamanı ya da commit).
- Tek deneme sonucu yazılmaz; en az 5.
- Ölçülemeyen hat "ölçülmedi" diye yazılır, tahmin konmaz.
