# 01. Ortak altyapı: ölçüm, Oyuncu Kapısı, filtre/öngörü, kimlik takibi (P0)

Bütün oyunların kalitesini bu dosya belirler. Önce bunu bitir.

---

## §1 Ölçüm ve "Bilim Modu" — `prototipler/olcum.py`

**Neden:** Canlıda donma/lag görüldü (Enes 2026-10-12); kök neden ölçülmedi. Tahmin değil sayı lazım.

İstenen:
- `Profil` nesnesi: `with prof.asama("algila"):` gibi aşama süresi toplar. Son 300 karenin medyanı ve
  p95'i hesaplanır. Kamera karesinin çekim zamanından ekrana çıkışa kadar geçen yaş ("kare yaşı") ayrıca tutulur.
- `stant_app.py` döngüsünde şu aşamalar: `kamera_bekle`, `kapi`, `isle(oyun adı)`, `goster`. Algı
  iş parçacığında: `algila_yuz`, `algila_el`, `algila_poz`, `yuz2`. Ayrıca algı sonucunun yaşı:
  çizimde kullanılan algı kaç ms önceki kareye ait.
- `FPS_LOG=1` ise her 2 sn'de bir satır yazılır ve `olcum/<tarih>.csv` dosyasına eklenir.
- **Çevrimdışı kıyas:** `python olcum.py --kiyas` her oyunu kamerasız, sahte `Algi` ile "oyun"
  durumunda 300 kare koşturur. Oyun başına isle medyan/p95 tablosu basar. Bu tablo `ILERLEME.md`'ye girer.
- **Bilim Modu** (`B` tuşu, bütün oyunlarda açılır/kapanır): yarı saydam katmanda şunlar görünür:
  - FPS ve aşama süreleri,
  - yüz örgüsü noktaları, el iskeleti ve poz iskeleti,
  - her oyuncunun kimlik numarası,
  - Oyuncu Kapısı'nın reddettiği algıların gri kutusu ve ret sebebi (§2),
  - blendshape çubukları (ilk yüz için en yüksek 6).
  Profesöre "kaputun altını" göstermek için de kullanılır (bkz. 09).

**Kabul:** `test_altyapi.py`: Profil medyan/p95'i bilinen sürelerde doğru hesaplıyor. `--kiyas` 5 oyunu
çalıştırıp tabloyu basıyor, rc 0. En az 3 test. İlk ölçüm tablosu `ILERLEME.md`'de.

---

## §2 Oyuncu Kapısı: "tırnak ucu bile görünse oyuncu sayılıyor" sorunu — `prototipler/oyuncu.py`

### Teşhis (kodda doğrulandı)
- `cekirdek.Algilayici` eşikleri bilerek düşük: el için algılama/varlık/takip 0.3, yüz 0.35.
  Bu, uzaktaki oyuncuyu kaçırmamak için seçildi; bedeli yanlış algılama.
- Hiçbir katmanda boyut, kenar ya da süre süzgeci yok:
  - `stant_app.py:211` `kisi_var = bool(algi.yuzler or algi.eller or algi.pozlar)`: tek karelik tek
    algı boşta menüye dönüşü erteliyor.
  - `AnaMenu.isle` her eli imleç sayıyor.
  - Oyunlar `algi.eller[0]`, `algi.yuzler` listelerini doğrudan kullanıyor.
- MediaPipe el modeli, karenin kenarından yalnız parmak ucu girdiğinde bile 21 noktanın hepsini
  tahmin eder. Görünmeyen noktaları kare dışına (x,y ∉ [0,1]) yerleştirir. Bu, ucuz ve güçlü bir ayırt edici sinyal.

### Çözüm ilkesi
Algılayıcıyı gevşek bırak (takip kopmasın), **kararı tek yerde, yazılımda ver**. Yeni bir kişi
"oyuncu" olmak için sıkı koşulları geçmeli. Oyuncu olduktan sonra gevşek koşulla takipte kalır
(histerezis). Bütün oyunlar ve menü süzülmüş algıyı görür. Tek düzeltme her yere uygulanır.

### Kurallar (varsayılanlar; oyun başına `Prototip.KAPI = {...}` ile değiştirilebilir)
| Kural | El | Yüz | Poz (vücut) |
|---|---|---|---|
| **Kare içi oranı**: noktaların kenardan %1 içeride olanların oranı | ≥ 0.85 (21 noktadan ≥ 18) | ≥ 0.90 | gövde noktaları 11,12,23,24'ten ≥ 3 görünür (visibility > 0.6) |
| **Boyut** | bilek(0) – orta MCP(9) ≥ 0.030·G px | göz dışı köşeler 33–263 ≥ 0.035·G | omuz genişliği ≥ 0.06·G |
| **Güven** | el tarafı skoru ≥ 0.70 (Algilayici bunu şu an atıyor; `Algi.el_skor` olarak ekle) | – | – |
| **Kenar payı**: kutu merkezi kenara yakınsa | merkez kenardan ≥ 0.04·G | ≥ 0.04·G | – |
| **Süre (aday → oyuncu)** | 0.35 sn kesintisiz | 0.30 sn | 0.40 sn |
| **Tutma (oyuncu → kayıp)** | 0.6 sn | 1.0 sn | 1.0 sn |
| **Takipte gevşeme**: oyuncu olduktan sonra | boyut ×0.7, oran ≥ 0.6, güven yok | oran ≥ 0.7 | – |

Ek kurallar:
- **Sahipsiz el:** karede yüz ya da poz varsa, bir el ancak bir sahibe bağlanabiliyorsa yeni oyuncu olabilir.
  Sahip iki şekilde belirlenir: bileği bir poz bileğine ≤ 0.08·G uzaklıkta, ya da bir yüzün 3 yüz
  genişliği yarıçaplı alanında. Karede yalnız el varsa (oyuncu çok yakın), boyut + oran + süre yeterli.
  `KAPI["el_sahip_sart"]` ile kapatılabilir.
- **Poster/afiş yüzü:** stantta afişlerde yüz olabilir. Bir yüzün noktaları 8 sn boyunca neredeyse hiç
  oynamıyorsa (ortalama yer değiştirme < 0.002·G/kare ve blendshape değişimi yok), o konumdaki yüz
  "durgun" etiketi alır ve yok sayılır. Etiket 30 sn sonra sıfırlanır.
- **Oyun alanı (isteğe bağlı):** oyun bir çokgen verebilir (ör. Cevap Yağmuru'nda zemin şeritleri). Dışında kalan algı oyuncu olmaz.
- **Geri bildirim:** aday oyuncu, kapıyı geçmesine kalan süre kadar dolan soluk bir halkayla gösterilir.
  Gecikme hissi yerine "beni gördü" hissi verir. Reddedilenler yalnız Bilim Modu'nda görünür.

### Arayüz
```
kapi = OyuncuKapisi(ayar)            # stant_app'te tek örnek
suzulmus: Algi = kapi.suz(algi, simdi, kural=oyunun_KAPI_sozlugu)
```
- Dönen `Algi` aynı alanları taşır (eski oyunlar değişmeden çalışır). Yalnız kabul edilen oyuncuların
  noktaları bulunur, ayrıca `yuz_id`, `el_id`, `poz_id` (§4) ve `adaylar`, `redler` listeleri eklenir.
- Sıralamalar korunur: `jestler`, `el_taraf`, `blend` listeleri süzülen elemanlarla hizalı kalır.
- Tutma süresi içinde kaybolan oyuncunun son noktası (§3 öngörüsüyle) verilir. Oyunlar tek karelik
  kopuşlarda titremez. `Algi.tahmini` alanı hangi noktanın tahmin olduğunu söyler.
- `stant_app.py`: `kisi_var`, menü imleçleri, ev düğmesi ve `proto.isle` süzülmüş algıyla çalışır.

### Kabul (`test_oyuncu_kapisi.py`, en az 8 test, sahte noktalarla)
1. Yalnız parmak ucu kenarda: noktaların çoğu x > 1.0. 3 sn boyunca hiçbir karede oyuncu olmaz.
2. Çok küçük el (`sahte_el(olcek=0.01)`) oyuncu olmaz.
3. Ortada normal el 0.2 sn sonra aday, 0.4 sn sonra oyuncu.
4. Oyuncu el 0.4 sn kaybolur, hâlâ oyuncu (tahmini). 0.8 sn sonra düşer.
5. Tek karelik yüz `kisi_var`'ı tetiklemez. `StantUygulama` 12 sn kuralıyla menüye döner.
6. 10 sn hiç oynamayan yüz "durgun" sayılır ve yok sayılır. Oynayan yüz kabul edilir.
7. Menü: kenardaki el kart seçemez. Ortadaki el 1 sn tutunca seçer.
8. Yüz + poz varken uzaktaki sahipsiz el oyuncu olmaz. Poz bileğine yakın el olur.
9. Süzülmüş `Algi`'de `jestler` ve `el_taraf` elemanları doğru ellerle hizalı.
Ayrıca mevcut 37 test geçer. 5 oyun süzülmüş algıyla `--kiyas`'ta çalışır.

---

## §3 Titreşim ve gecikme: filtre + öngörü — `prototipler/filtre.py`

**Neden:** Ham nokta titrer (parmak ucunda birkaç piksel). Kamera + algı + yayın gecikmesi var.
Neon Tel, Parmak Kuşu ve AR maskeler ikisinden de doğrudan etkilenir.

İstenen:
- `OneEuro(min_cutoff, beta, d_cutoff)` (Casiez 2012): skaler ve numpy dizi (N×2 / N×3) için,
  vektörel çalışsın. 478 yüz noktası tek çağrıda süzülür. Zaman damgası gerçek saniye; sabit dt varsayma.
- `Ongorucu(sure_ms, tavan_px)`: süzülmüş konum + süzülmüş hız × `sure_ms`. Sıçrama tavanla sınırlanır.
  Hız düşükken öngörü kapanır, durağan elde aşma olmasın.
- `NoktaTakip`: kimliğe (§4) bağlı filtre durumları. Yeni kimlik gelince sıfırlanır, oyuncu düşünce silinir.
- **Ayar:** varsayılan değerler araştırma özetindeki aralıktan (`ARASTIRMA-KAYNAKLAR.md`). Sonra
  **titreşim kalibrasyonu** ile ayarlanır: `olcum.py --titresim` oyuncudan 3 sn parmağını sabit
  tutmasını, sonra 3 sn hızlı sallamasını ister. Sabitteki titreşim p95'ini ve hareketteki gecikmeyi
  (süzülmüş - ham faz farkı) ölçer, `veri/filtre_ayar.json` dosyasına yazar.
- Kural: oyun mantığı (çarpışma, seçim) **süzülmüş** konumu kullanır. Görsel iz (parıltı kuyruğu)
  süzülmüş + öngörülü konumu kullanabilir.

**Kabul (`test_filtre.py`, en az 5):**
- Sabit nokta + ±4 px gürültü: çıkış p95 sapması ≤ 1.5 px.
- 1000 px/sn doğrusal hareket: süzülmüş konumun gecikmesi ≤ 40 ms. Öngörü açıkken ≤ 15 ms.
- Ani 300 px sıçramada öngörü tavanı aşılmıyor.
- Değişken dt'de (20–60 ms) kararlı.
- 478×3 dizi süzme süresi < 0.3 ms.

---

## §4 Çok kişi kimlik takibi — `oyuncu.py` içinde

**Neden:** Cevap Yağmuru'nda kişi başına skor, AR'da kişi başına kalıcı maske, düellolarda
"sol oyuncu / sağ oyuncu" kararlılığı. Bugün listeler her karede yeniden sıralanıyor; iki kişi yer
değiştirince efektler sıçrıyor.

İstenen:
- Her tür (yüz, el, poz) için ayrı takipçi: merkez + boyut benzerliğiyle eşleştirme (≤ 6 nesne,
  açgözlü en yakın eşleşme yeterli). Eşik dışı kalan yeni kimlik alır. Tutma süresi §2'deki gibi.
- Kimlik başına sabit renk (palet sırasıyla) ve isteğe bağlı takma ad ("Oyuncu 1", "Mor").
- Yüz ↔ poz ↔ el bağlama: aynı kişiye ait algılar ortak bir `kisi_id` altında toplanır.
  Yüz burnu ↔ poz burnu (0) yakınlığı, el bileği ↔ poz bileği (15/16) yakınlığı.
- Maske (segmentasyon) için: poz kutusuyla kesişen maske bölgesi o kişinin maskesi sayılır. Cevap
  Yağmuru'nda kişi başına kırmızı/yeşil boyamak için gerekli.

**Kabul (`test_kimlik.py`, en az 4):** iki yüz çapraz yer değiştirirken kimlikler korunuyor (hız
sürekliliği). Bir yüz 0.5 sn kaybolup aynı yere dönünce aynı kimliği alıyor. 2 sn sonra dönerse yeni
kimlik alıyor. El ve yüz aynı `kisi_id`'ye bağlanıyor.

---

## §5 Bilinen yavaşlık adayları (ölçümle doğrula, sonra düzelt)

Kod okumasından çıkan adaylar (2026-10-12). Her birini §1 ölçümüyle önce/sonra tablosuna koy.
Ölçüm iyileşme göstermezse geri al.

1. **`yuz2` taraması** (`cekirdek.py:189`): karede < 2 yüz varsa her karede 3 ek FaceLandmarker (IMAGE)
   koşuyor. AR Maskeler'de tek kişiyle hep çalışır. Öneri: en çok 0.5 sn'de bir ara ve yalnız oyun
   ikinci oyuncu ararken (bekleme ekranı) çalıştır. Bulunan yüz VIDEO modundaki takipçiye devredilir.
2. **Meme sesleri**: `pygame.mixer.music.load` döngü içinde diskten okuyor (`p_neon_kilic.py:172`,
   `p_gulmeme.py:66`). Oyun açılışında `pygame.mixer.Sound` olarak arka planda önyükle.
3. **`parilti()` kare başına birden çok kez** tam ekran çalışıyor (Neon, Gülme, Maske). Kare başına tek
   bir ışık katmanı topla, tek `parilti` çağır. GPU yolunu 02 §4'te değerlendir.
4. **`Parcaciklar.ciz`** (`stand.py:332`): parçacık başına Python döngüsünde `cv2.circle`. Öneri:
   önceden çizilmiş boyut kademeli ışık sprite'ları, toplu toplamalı bindirme ya da küçük katmana
   çizip büyütme. 300 parçacıkta < 1.5 ms hedef.
5. **`Maskeci` her oyunda ayrı model** (`p_zaman_klonu`, `p_gorunmez`): `cekirdek`'te tek paylaşılan
   örnek olsun (ilk çağrıda kurulur). Oyunlar `ver()` ile aynı maskeyi alır.
6. **Maskeler ikon hazırlığı** (`p_maske.py:851`): ilk girişte 14 maske çiziliyor. Uygulama açılışında
   arka planda önceden hazırla.
7. **Kamera**: MJPG FOURCC iste (bkz. 00). `Kamera` iş parçacığında `resize + flip` her kare yapılıyor;
   kaynak zaten 1280x720 ise resize atlanır.

**Kabul:** `--kiyas` tablosunda Maskeler ve Gülme'nin isle p95 değeri önce/sonra yazılı ve düşmüş.
Canlı FPS_LOG'da algı yaşı medyanı ≤ 60 ms (laptop kamerasıyla). Mevcut testler yeşil.
