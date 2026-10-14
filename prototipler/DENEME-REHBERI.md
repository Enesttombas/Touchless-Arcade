# Stant Prototipleri — Deneme Rehberi

2026-10-11. 17 prototip hazır. Hepsi tek uygulamada; tuşla geçiyorsun. Hepsinin kör kabul testi yeşil.
Ziyaretçi fotoğrafı kaydedilmez (yalnız Filtre + İmza Duvarı'nda başparmak yukarı yapınca, eski stant davranışı).

## STANT UYGULAMASI (asıl kullanılacak): masaüstünde `Stant.bat`

5 oyun ayrı ayrı durur, içerikleri karışmaz; uygulama yalnız aralarında geçiş yapar. Tam ekran, kamera 1.

- **Ziyaretçi (elle):** açılışta 5 kartlı menü. Elini bir kartın üstünde 1 sn tut, oyun açılır.
  Menüye dönmek için sol alt köşeye avuç tut (1,2 sn). 12 sn kimse yoksa (oyun sürmüyorsa) kendi menüye döner.
- **Operatör (klavye):** **1** Zaman Klonları, **2** Neon Kılıç, **3** Gülme Düellosu, **4** Görünmezlik Pelerini,
  **5** AR Maskeler. **M** menü. **N / B** sonraki / önceki oyun. **Boşluk** oyunun kendi modunu değiştirir
  (Neon Kılıç'ta bekleme ekranında Meyve/Meme). **F** tam ekran aç/kapa. **Q / Esc** çıkış.
- Laptop kamerasıyla: komut satırında `set KAMERA=0` sonra `Stant.bat`.
- **Oyun içi tuşlar:** Zaman Klonları: Boşluk = Neon / Klon / Gökkuşağı. Neon Kılıç: Boşluk (bekleme ekranında) = Meyve / Meme.
  Gülme Düellosu: R = düelloyu sıfırla. Görünmezlik: Boşluk = Pelerin / Hayalet / Uçan Kafa, R = odayı yeniden ezberle
  (kamera oynadıysa ya da arka plan değiştiyse). AR Maskeler: Boşluk = sonraki maske.
  Zaman Klonları 15 sn, Görünmezlik 12 sn, AR Maskeler 12 sn'de bir kendiliğinden de değişir; elle değiştirince sayaç sıfırlanır.
- Kalabalık: arkadan geçen küçük/uzak kişiler Zaman Klonları ve Görünmezlik'te efekte girmez; öndeki oyuncular ayrı ayrı işlenir.
- Ekranda övgü/ipucu süsü yok (HARİKA, KOMBO, GÖRÜNMEZSİN, köşe yazıları kaldırıldı); yalnız oyun için gereken skor/süre/sonuç kalır.

## Nasıl açılır

`prototipler\Prototipler.bat` dosyasına çift tıkla. Tam ekran açılır, kamera 1 seçilir.

- Laptop kamerasıyla denemek için: komut satırında `set KAMERA=0` yazıp sonra `Prototipler.bat` çalıştır.
- **1-9, 0**: ilk 10 prototipe doğrudan geç. **N / B**: sonraki / önceki (11-17 bunlarla; B ilk prototipten sona sarar).
- **F**: tam ekran aç/kapa. **Q / Esc**: çık. **Boşluk**: çoğu prototipte mod değiştirir.
- Vitrin modu: `set OTOMATIK=10` ile açarsan 10 sn'de bir kendi kendine sıradakine geçer. Stantta kimse oynamazken dikkat çekmek için.

## Stant modu: seçilen 5 (cilalı)

`prototipler\Stant5.bat`: yalnız seçilen 5 prototip, tam ekran, kamera 1. Kadrajda kimse yokken 25 sn'de bir
sıradakine geçer (vitrin); biri oynarken ya da oyun sürerken geçmez. N / B ile elle de geçilir.

| Sıra | Ad | Cila turunda eklenenler |
|---|---|---|
| 1 | Zaman Klonları | Renkli neon yankılar; dans ettikçe yankı sayısı 3'ten 7'ye çıkar; boşluk: Neon / Klon / Gökkuşağı |
| 2 | Neon Kılıç | Kombo sayacı, ikiye bölünen meyveler, kılıç izi, süre çubuğu, oturumun en iyi 5 skoru, rekor konfetisi |
| 3 | Gülme Düellosu | 3-2-1 "CİDDİ KAL!" geri sayımı, gülme çubukları, kışkırtan emojiler, konfetili sonuç, renkli yüz halkaları |
| 4 | Görünmezlik Pelerini | Kişi kadrajdan çıkmasa da odayı ezberler (biraz sağa sola kay, %92'de hazır); yeni "Uçan Kafa" modu |
| 5 | AR Maskeler | 3 yeni maske (Korsan, Ayıcık, Kalp Göz), titremesiz takip, "Poz ver!" anı; maske değiştirmek için göz kırp ya da avucunu aç-kapa |

Her prototipte birden fazla kopya vardı; sen canlı deneyip seçtin (`Secim.bat` eski hali ile kopyaları sırayla açar).

## Prototipler (tüm 17)

| Tuş | Ad | Ne yapıyorsun | Hız |
|---|---|---|---|
| 1 | Filtre + İmza Duvarı | Eski stant: işaret parmağıyla havaya çiz, avuç siler, başparmak yukarı kaydeder | ~26 FPS |
| 2 | Zaman Yarığı | Tarama çizgisi ekrandan geçer; geçerken hareket edersen yüzün/vücudun eğilip bükülür | ~37 FPS |
| 3 | Neon Kılıç | Fruit Ninja: avucunu göster, başla; parmağını savurup meyveleri kes, bombaya dokunma | ~23 FPS |
| 4 | Kafa Topu | Kafanla topu sektir, düşürme | ~35 FPS |
| 5 | Uçan Kafa | Flappy Bird: ağzını açınca zıplarsın, sütunların arasından geç | ~29 FPS |
| 6 | Surat Ustası | Ekrandaki emojinin yüz ifadesini taklit et, puan topla | ~40 FPS |
| 7 | Gülme Düellosu | İki kişi ekrana bakar, ilk gülen kaybeder | ~41 FPS |
| 8 | Büyücü | Avucunu aç, mandala çıksın; iki eli birleştirip hızla aç, enerji ışını fırlat | ~20 FPS |
| 9 | Hava Davulu | Parmağını neon pedlere yukarıdan hızla indir, ses çıkar | ~19 FPS |
| 0 | Işık Tozu | Hareket ettikçe vücudundan ışık tozu saçılır (tema boşlukla değişir) | çok hızlı |
| 0 sonra N | Zaman Klonları | Hareket ettikçe arkanda renkli neon kopyaların kalır (dans etmek için ideal) | ~73 FPS* |
| 0 sonra N N | Stil Aynası | Avucunu salla, görüntü ASCII / çizgi roman / pop-art gibi stillere geçer | ~22 FPS |
| 0 sonra N N N | Görünmezlik Pelerini | Önce 1 sn kadrajdan çık (oda ezberlenir), sonra gir: görünmez olursun; boşluk = Hayalet modu, R = odayı yeniden ezberle | ~165 FPS |
| 1 sonra B B B B | Çiz ve Yuvarla | İşaret parmağıyla havaya neon rampa çiz; yukarıdan düşen toplar rampada yuvarlanıp sepete girsin; avuç siler | ~20 FPS |
| 1 sonra B B B | Balon Patlat | Yükselen sabun balonlarını parmak ucu ya da burunla patlat; altın 3 puan, bombalı -3; kalabalıkla oynanır | ~20 FPS |
| 1 sonra B B | Kaleydoskop | Yüzün canlı kaleydoskobun merkezi olur; kafanı eğ döner, ağzını aç yakınlaşır; boşluk 6/8/12 dilim | ~28 FPS |
| 1 sonra B | AR Maskeler | Her yüze ayrı maske (taç, neon gözlük, kedi, şeytan, uzaylı); ağız aç: kalp/ateş saçar, göz kırp: maske değişir | ~40 FPS |

FPS laptopta, sahte kareyle ölçüldü (`gezgin.py --olc`); el algısı gerektirenler (3, 8, 9, Stil Aynası) en yavaşlar ama oynanır.
\* Zaman Klonları ilk ölçümde 11 FPS'ti; karışım kodunu hızlandırdım, 93 ms'den 14 ms'ye indi. Kamera zaten 30 FPS verir; 30 üstü "takılmaz" demek.

## Bilinen küçük şeyler (prototip seviyesi)

- Neon Kılıç'ın bomba kırmızısı ve Büyücü'nün ışın beyazı yumuşatıldı (en çok %28 / %40 opaklık).
- Hava Davulu'nda pedler alt yarıda; kameraya çok yakın durursan yüzüne denk gelir, biraz geri dur.
- Çiz ve Yuvarla'da çizgilerin parlaması güçlü (beyaza kaçıyor); beğenirsen tonu kısarız.
- Kafa Topu'nda kafanı hiç oynatmazsan top 2 sekmeden sonra düşer (bilerek: oynatman gerek).
- Görünmezlik Pelerini oda ezberi ister: arka plan sabitse en iyi çalışır, kalabalık stantta "R" ile yenile.
- Gülme Düellosu için kadrajda iki yüz şart, tek kişide "arkadaşını çağır" der.

## Seçim için önerim

Dikkat çekme + kalite + stant akışı açısından en güçlü aday seti:

1. **Zaman Klonları** — uzaktan bile göze çarpar, öğretmeye gerek yok, vitrin için en iyisi.
2. **Neon Kılıç** — herkesin bildiği oyun, kısa tur, skor rekabeti.
3. **Gülme Düellosu** — iki kişiyi stante çeker, izleyen de güler (bal kavanozu etkisi).
4. **Görünmezlik Pelerini** — "vay" anı yüksek, fotoğraf çektirmelik.
5. **AR Maskeler** — grupla fotoğraf anı, öğretmeye gerek yok.
6. **Balon Patlat** veya **Uçan Kafa** — kalabalık / komik, sıra bekletir.

Sen dene, beğendiklerini söyle; onları cilalarız (ses, skor tablosu, geçiş animasyonu, vitrin döngüsü).

## Dosyalar

- Prototipler: `work/meme-kamera/prototipler/p_*.py` (ortak çekirdek `cekirdek.py`, hub `gezgin.py`)
- Alternatif kopyalar (işçinin ürettiği ikinci versiyonlar): `prototipler/_alternatif/`
- Fikir araştırması: `work/meme-kamera/arastirma-fikir/rapor.pdf`
- Kabul testleri: `work/meme-kamera/kabul_prototip/`
