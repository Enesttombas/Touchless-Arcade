# CILA-YENI-7: Enes'in 2026-10-13 bulguları

Kaynak: Enes'in canlı denemesi (2026-10-13). Yazan: Opus. Uygulayan: Codex.
`CILA-YENI-6.md`'deki genel kurallar (kalite çıtası, **KAMERA GÖRÜNTÜSÜ ZEMİNDİR**, süreç, yasaklar)
aynen geçerli. Bu dosya yeni işleri ve sırayı verir.

## 0. Önce: durum ve dokunulmayanlar

- **Taş-Kağıt-Makas menüden çıktı (Enes 2026-10-13).** 7. kartta artık `p_hayalet_klon.py` var: eski
  Zaman Klonları + Görünmezlik Pelerini tek oyun ("Hayalet Klonlar"), Opus yazdı. `KAPALI` boş küme,
  mekanizma testte duruyor. `stant_app.py`, `p_hayalet_klon.py`, `p_zaman_klonu.py`, `p_gorunmez.py`'ye
  dokunma. TKM üzerinde yeni iş yapma (dosya ve testleri yerinde kalır).
  `p_tas_kagit.py` dosyasında commit edilmemiş değişikliğin varsa önce `test_cila_tkm.py`'yi koş.
  Yeşilse `wip(tkm): ...` diye yerel commit at, kırmızıysa dosyaya dokunma ve ILERLEME'ye yaz.
- **Opus'un commit edilmemiş dosyaları:** `stant_app.py` (KAPALI satırları), `test_stant_app.py`,
  `p_maske.py`, `test_maske_kontrol.py`, `test_cila.py`.
  - Geri alma.
  - Simge işi için `stant_app.py`'ye dokunman gerekirse Opus'un satırlarını koru. O commit'e dahil olabilirler.
- **Eski 3 oyun** (Neon Kılıç, Gülme Düellosu, AR Maskeler): adı, simgesi ve kodu değişmez.
- **Yasak:**
  - `git add -A`, stash, checkout, push;
  - kurulum/HP/ağ dosyaları;
  - web araştırması (soru bankası dahil; bkz. madde 3).

> **Opus ekledi (2026-10-13 06:25):** `stant_app.py` artık her oyunun üstüne parmak ucu izi çiziyor (`parmak_izi`,
> Neon Kılıç ve Maske hariç). Oyunun kendi imleci varsa çift çizmemek için sınıfa `KENDI_IMLECI = True` yaz
> (Çiz Tahmin'de imleci sen yapıyorsan bunu kullan). `Stant.exe` yeniden derlendi (kaynak `kurulum/StantLauncher.cs`,
> derleme `kurulum/stant-exe-derle.ps1`): açılırken eski kopyaları kapatır. Bu dosyalara ve `parmak_izi`'ne dokunma.

## Sıra (her biri ayrı test ve ayrı yerel commit)

| # | İş | Dosya | Süre |
|---|---|---|---|
| **0** | **Silahşor/Kovboy: takılma + sade arayüz (en acil)** | `p_refleks.py` | 60 dk |
| 1 | Kuş: hareketli boru boşluğu | `p_parmak_kusu.py` | 30 dk |
| 2 | Çiz Tahmin: çizim hataları | `p_ciz_tahmin.py` | 90 dk |
| ~~3~~ | ~~Cevap Yağmuru: iki mod~~ **OPUS YAPIYOR (Enes 2026-10-13). `p_cevap_yagmuru.py`, `veri/sorular*.json`, `test_cila_cevap.py`, `test_cevap_yagmuru.py` dosyalarına DOKUNMA.** Aşağıdaki madde 3 yalnız bilgi içindir. | — | — |
| 4 | ~~6 oyuna simge + ad~~ **OPUS YAPTI (2026-10-13).** Senden yalnız: `p_ciz_tahmin.py` içinde `AD='Çizim Kâhini'` ve `test_ciz_tahmin.py:113` beklentisi. `stant_app.py` simgelerine ve diğer `AD`'lara dokunma. | `p_ciz_tahmin.py` | 5 dk |
| 5 | Penaltı: mekanik doğrulama | `p_penalti.py` | 20 dk |
| **6** | **Altın Vuruş: çift şut + kolay kontrol + yalancıktan atlayan kaleci (acil, 0'dan sonra)** | `p_penalti.py` | 120 dk |

---

## 0. Kovboy Düellosu (`p_refleks.py`): "elini beline indir"de takılıyor, arayüz çok karmaşık

**Bulgu (Enes, canlı ekran görüntüsü):** Oyun "ELİNİ BELE İNDİR" ekranında kalıyor, raunt başlamıyor.
Ekranda aynı anda 7 ayrı yazı ve iki büyük kutu var:
- "BAŞLA" paneli;
- "El belde; ATEŞ yazınca kaldır!";
- "Elini bu hedefte tut";
- "1. El belde 2. ATEŞ 3. Hızla kaldır";
- "SOL / KILIF" ve "YZ / KILIF".

Oyuncu ne yapacağını anlamıyor.

**Kök neden (Opus, kodda doğrulandı):**
- `raunt_hazir` (satır ~39) her oyuncunun elini kılıf kutusunda **görmek** istiyor. Satır ~52'de el kayıpsa `hazir=False` oluyor.
- Stant kamerasında bel çoğu zaman kadraj dışında kalıyor. MediaPipe belde, yanda ya da cepte duran eli de güvenilir bulmuyor.
- Sonuç: "hazır" hiç oluşmuyor.
- Bu kural CILA-YENI-6 P0'daki Opus şartnamesinden geldi. **O kural iptal**, yerine aşağıdaki geçer.

**Yeni mantık: "el görünmüyorsa hazırsın"**
- Oyuncular **yüzden** tanınır. Ekranın sol yarısındaki yüz SOL oyuncu, sağdaki SAĞ oyuncudur.
  Tek yüz varsa rakip YZ'dir. Yüz yoksa vitrin.
- **Hazır** = o oyuncunun tarafında, omuz çizgisinin üstünde el yok.
  - Omuz çizgisi: yüz kutusunun alt kenarı + yüz yüksekliğinin 0,5'i.
  - Durum 0,6 sn sürmeli.
  - Elin görünmemesi de hazır sayılır.
  - "Hazır" için el algısı **hiç gerekmez**.
- **ATEŞ!** sinyali, herkes hazır olduktan sonra 1,5–4 sn rastgele beklemeyle gelir.
- **Çekiş** = ATEŞ'ten sonra o tarafta, omuz çizgisinin üstünde bir elin görüldüğü ilk kare.
  Avuç, yumruk ya da parmak fark etmez. Kare tabanlı adalet (`erken_kare`) aynı kalır.
- **Erken çekiş** = ATEŞ'ten önce, omuz çizgisinin üstünde 2 ardışık karede el görülmesi.
  Raunt "ERKEN!" ile karşıya verilir.
- **Kilitlenme yok:**
  - 4 sn içinde hazır olmayan oyuncuya ekranda tek bir büyük ipucu çıkar: "ELLERİ İNDİR".
  - 8 sn sonra o oyuncu seyirci olur. 1 kişi kalırsa YZ'ye karşı oynanır.
  - Bu kural CILA-YENI-6 madde 1'deki 3 sn kuralının yerine geçer.
- Yeni raunt: sonuç 2,5 sn görünür, sonra yine "eller aşağı" beklenir.

**Sade arayüz** (aynı anda en fazla 2 yazı; kutu yok):
| Durum | Ekranda |
|---|---|
| Bekleme | Ortada tek büyük yazı "ELLER AŞAĞI". Her oyuncunun başının üstünde adı ("SOL"/"SAĞ"/"YZ") ve hazır olunca yeşil ✓ |
| Hazır | "HAZIR…" yavaşça nabız atar, ekran kenarı hafif kararır (gerilim) |
| ATEŞ! | Ekranı kaplayan beyaz flaş + dev "ATEŞ!" + silah sesi |
| Sonuç | Kazananın yüzünün çevresinde halka + "SOL KAZANDI • 0,284 sn". Erken çekene kırmızı "ERKEN!" |

- **Kaldırılacak:**
  - kılıf kutuları;
  - "Elini bu hedefte tut";
  - 1-2-3 adım listesi;
  - "BAŞLA" paneli;
  - alttaki iki ayrı "… / KILIF" etiketi.
- Kural, oyun başındaki geçiş kartında **tek cümle** ile verilir: "Eller aşağı. ATEŞ yazınca elini kaldır!".
  İlk raunttan önce 2 sn'lik kısa animasyon gösterilir (çöp adam değil, ok + el simgesi).
- Kamera görüntüsü zemindir (CILA-YENI-6 kuralı). Western tonu yalnız üstüne biner.

**Testler** (en az 7):
- hiç el görünmeyen iki yüz 0,6 sn sonra hazır olur ve ATEŞ gelir;
- ATEŞ'ten sonra ilk kaldıran kazanır;
- ATEŞ'ten önce tek karelik el erken sayılmaz, 2 kare sayılır;
- belde kısmen görünen el (omuz çizgisinin altında) hazırlığı bozmaz;
- 8 sn hazır olmayan oyuncu seyirci olur ve oyun ilerler;
- tek yüzde YZ'ye karşı oynanır;
- herhangi bir durumda ekrandaki yazı sayısı ≤ 2 (çizim çağrısı sayacıyla).

Gerçek kamera kontrolü: iki kişi, eller yanda ya da cepte; 3 raunt. Kamera yoksa bunu "kontrol edilmedi" diye yaz.

## 1. Parmak Kuşu: boru boşluğu aşağı yukarı hareket etmeli

**Bulgu (Enes):** "Borular sabit durmamalı, aralarındaki boşluk aşağı yukarı hareket etmeli."
**Kod:** şu an `cy = p['y'] + (24*sin(simdi*.7) if skor >= 8 else 0)`. Salınım skor 8'den önce yok,
genliği küçük ve bütün borularda aynı faz var. Aynı ifade 92. ve 170. satırda iki kez yazılmış.

İstenen:
- Boşluk **ilk borudan itibaren** salınır. Her borunun kendi fazı (doğuşta rastgele) ve frekansı olur.
  Yan yana borular aynı anda aynı yöne gitmez.
- Genlik skorla büyür: `A = min(35 + 7*skor, 120)` px. Frekans `0.6 → 1.3 rad/s` arasında skorla artar.
  Bu, mevcut hızlanmaya (her skorda %4, tavan 2,2×) eklenir.
- Boşluk merkezi ekran içinde kalır: `[aralik/2 + 40, Y - aralik/2 - 40]`.
- Adalet: boşluğun dikey hızı, kuşun en büyük tırmanma hızının %60'ını geçmez.
- Çizim ve çarpışma **tek fonksiyondan** aynı `cy`'yi alır. İki ayrı ifade kalmaz.
- Görsel ipucu: hareketli borunun ağzında yukarı-aşağı küçük ok ya da ışık izi olsun, hareket okunsun.
- Testler (en az 5):
  - aynı `t` anında iki borunun `cy`'si farklı;
  - skor 0'da genlik > 0;
  - genlik tavanı aşmıyor;
  - merkez sınır içinde;
  - dikey hız sınırı aşılmıyor;
  - çizilen `cy` ile çarpışma `cy`'si eşit.

## 2. Çiz Tahmin (`p_ciz_tahmin.py`): "çizmiyor, yarım yamalak çiziyor"

**Bulgu (Enes, canlı):** Parmakla çizerken çizgi hiç çıkmıyor ya da parça parça çıkıyor.
`c69afaa6` commit'i ve sonraki commit edilmemiş "kamera takviyesi" bunu çözmedi.

**Önce teşhis, sonra düzelt.** Tahmin yürütme, ölç:
1. `CIZ_TANI=1` ortam değişkeniyle ekranda her kare için şu tanı şeridini göster:
   - el var/yok;
   - Oyuncu Kapısı eli geçirdi mi;
   - kalem durumu (iner/kalkar) ve **neden** (ör. "orta parmak açık", "el kayıp 0.3 sn", "sıçrama");
   - nokta sayısı.
2. Aynı bilgiyi yalnız landmark ve durum olarak (görüntü değil) `%TEMP%\ciz_tani.jsonl` dosyasına yaz.
   Ziyaretçi görüntüsü diske yazılmaz.
3. Olası kökler; her birini kayıtla doğrula ya da ele:
   - Kalem kuralı fazla katı: "işaret açık + orta kapalı" stant mesafesinde titrer.
   - Oyuncu Kapısı küçük/kenardaki eli düşürüyor.
   - 15 FPS'te ardışık noktalar ara eşiğini aşıp yeni çizgi açıyor.
   - Yumuşatma gecikmesi ucu kırpıyor.
   - En küçük hareket eşiği yavaş çizimi yutuyor.

**Hedef davranış** (teşhis başka kök gösterirse ILERLEME'ye yaz ve gerekçeyle uyarla):
- **Kalem kuralı basit olsun:** işaret parmağı ucu, işaret kökünden belirgin uzaktaysa kalem iner.
  Orta parmak şartı kalkar.
  - Kalem 2 kare, kalkış 4 kare histerezisle değişir.
  - Avuç 1 sn açık tutulursa son çizgi geri alınır, 2 sn tutulursa her şey silinir. Halka göstergesi olur.
- El 0,4 sn'den kısa kaybolursa çizgi kopmaz; dönüşte ara nokta doldurulur.
- 15 FPS ve 1/8 sn kare aralığında bile çizgi sürekli olur. Kopma eşiği kare süresine göre ölçeklenir.
- Kalem indikten sonra ilk mürekkep ≤ 150 ms içinde çıkar.
- Parmak ucunda her zaman görünür imleç olsun: kalem inikken dolu, kalkıkken halka.
  Kişi sistemin ne gördüğünü anlar.

**Kabul ölçütü** (sentetik iz üretici: bilinen bir şekli, örneğin daire, yıldız ya da ev, landmark dizisine çevir):
- 15 FPS, %10 kare kaybı, ±6 px titreşim ve parmak bükülme gürültüsüyle:
  - hedef yolun **≥ %92'si** mürekkebe 12 px içinde olsun;
  - tek vuruşluk şekilde istenmeyen kopma ≤ 1 olsun.
- Tanı kaydından yeniden oynatma testi (en az 3 farklı sentetik oturum).
- Bir de gerçek kamerayla, ya da kamera yoksa `FARE_EL=1` ile, 3 şekil çizilip ekran görüntüsüyle ILERLEME'ye konur.
  Fare ile oynamak "insanla kabul" sayılmaz; bunu açıkça yaz.

## 3. Cevap Yağmuru: iki mod, giderek zorlaşan ve tekrar etmeyen sorular

**İstek (Enes):** "1. mod genel kültür, git gide zorlaşsın, hep aynı düzenle aynı sorular çıkmasın.
2. mod sayısal işlem, git gide zorlaşsın: toplama, çıkarma, bölme, işlem önceliği ve karışıklıkla zorlayacağız."

**Mod seçimi:** Oyun başında iki büyük kart çıkar: **GENEL KÜLTÜR** ve **SAYI USTASI**.
Kartın üstünde el 1 sn tutulunca seçim yapılır (1/2 tuşları da çalışır). 8 sn seçim yoksa son mod
seçilir. Düşen cevap mekaniği ve oyuncu takibi aynı kalır.

**Ortak zorluk eğrisi:** 5 seviye.
- 3 ardışık doğru cevap seviyeyi 1 artırır; 2 ardışık yanlış 1 düşürür; taban 1.
- Seviye ve süre çubuğu ekranda görünür.
- Seviye arttıkça soru süresi ve düşüş hızı değişir: süre 12 sn → 6 sn, düşüş 1× → 1,6×.

### Mod 1: Genel kültür
- Soru bankası ayrı bir veri dosyasında olur (`prototipler/veri/sorular_genel.json`). Her soruda şu alanlar bulunur:
  `id, seviye(1-5), kategori, soru, dogru, yanlislar[3]`.
- **En az 200 soru:** seviye başına ≥ 40, en az 6 kategori (bilim, tarih, coğrafya, spor, sanat/edebiyat, teknoloji).
- **Zamanla değişen bilgi yasak:** nüfus, rekor, "en son", görevdeki kişiler, fiyat gibi sorular girmez.
  - Tartışmalı ya da belirsiz soru da girmez.
  - Yanlış şıklar makul olsun, saçma olmasın.
  - Türkçe yazım kusursuz olsun.
- **Tekrar yok:**
  - Her oturum bankayı seviye seviye karıştırır ve torbadan çeker; torba bitmeden aynı soru gelmez.
  - Son 60 soru uygulama çalıştığı sürece bellekte tutulur ve yeni oturumda da öncelikle atlanır.
  - Şık sırası her seferinde karışır.
- Banka web araştırmasız, bilinen sabit bilgiden yazılır. Opus sonra örneklem denetimi yapacak.
  Emin olmadığın soruyu koyma.

### Mod 2: Sayı Ustası (üretilen sorular, banka yok)
Sorular kodla üretilir, böylece tekrar pratikte olmaz. Bütün cevaplar tam sayıdır; bölme her zaman tam bölünür.
| Seviye | Örnek | Kural |
|---|---|---|
| 1 | 7 + 5, 13 − 6 | tek/iki basamak toplama-çıkarma, sonuç ≥ 0 |
| 2 | 48 − 19, 36 + 47 | iki basamak, eldeli/onluk bozmalı |
| 3 | 7 × 8, 72 ÷ 9 | çarpım tablosu ve tam bölme |
| 4 | 3 + 4 × 2, 20 − 12 ÷ 4 | iki işlem, **işlem önceliği tuzağı** |
| 5 | 18 ÷ 3 + 4 × (5 − 2), 6 − 2 × (7 − 4) | üç işlem, parantez, negatif ara/sonuç olabilir |

**Yanlış şıklar bilinçli tuzak olur:** Seviye 4–5'te bir yanlış şık mutlaka "soldan sağa hesaplanmış"
(önceliği yok sayan) sonuç olur. Diğer tuzaklar:
- ±1 / ±10;
- işaret hatası;
- parantezi yok saymak.

Tuzak doğru cevapla çakışırsa başka bir tuzak üretilir.

Sonuç ekranında doğru çözüm adım adım kısa gösterilir. Örnek: "4 × 2 = 8 → 3 + 8 = 11".

**Testler** (en az 10):
- her seviyede 200 üretimde cevap tam sayı, şıklar benzersiz ve doğru cevaptan farklı;
- seviye 4–5'te öncelik tuzağı var;
- art arda 50 soruda tekrar yok (Mod 1 ve Mod 2);
- zorluk eğrisi (3 doğruda yukarı, 2 yanlışta aşağı, taban 1);
- banka şeması doğrulaması (alanlar, seviye dağılımı ≥ 40, `yanlislar` 3 ve benzersiz);
- mod seçimi el ve tuşla çalışıyor, 8 sn sonra varsayılan seçiliyor.

## 4. Menü: 6 yeni oyuna simge ve profesyonel ad

> **OPUS YAPTI (2026-10-13):** 6 simge `stant_app.py` (`ikon_kus`, `ikon_yagmur`, `ikon_duello`, `ikon_tkm`,
> `ikon_penalti`, `ikon_ciz`) + `test_her_kartin_kendi_cizilmis_ikonu_var`; adlar Kanat Rotası, Bilgi Yağmuru,
> Silahşor Düellosu, Altın Vuruş değişti (testler dahil). "Kâ" yazı tipinde doğru çıkıyor (kontrol edildi).
> Sende kalan tek iş: Çiz Tahmin işini bitirirken `p_ciz_tahmin.py` `AD`'ını **Çizim Kâhini** yap ve
> `test_ciz_tahmin.py` satır 113'teki beklentiyi güncelle. Aşağıdaki metin yalnız bilgi içindir.

İlk 3 kart gibi her yeni oyuna da prosedürel simge gelecek (emoji ya da harici görsel yok).
Mevcut `ikon_kilic`/`ikon_gulme` ile aynı stilde olacak: `_tuval`/`_bgra`, neon kontur, `parilti`, 72 px'te net.
Şu an bu kartlarda yalnız rakam var.

| Kart | Yeni ad (`AD`) | Simge |
|---|---|---|
| 4 | **Kanat Rotası** | kanatlı kuş + iki boru arası boşluk |
| 5 | **Bilgi Yağmuru** (adı Opus koyar; sen yalnız simgeyi `stant_app.py`'de çiz) | düşen damla/kartlar içinde "?" ve "+" |
| 6 | **Silahşor Düellosu** | iki çapraz tabanca + şerif yıldızı |
| 7 | Taş Kağıt Makas (aynı ad) | el simgesi; menü soluk çizdiği için ayrıca bir şey yapma |
| 8 | **Altın Vuruş** | top + kavisli iz + kale ağı |
| 9 | **Çizim Kâhini** | kalem ucu + parlayan çizgi + küçük göz |

- Ad iki kelime olsun; menü ilk boşluktan ikiye böler. "Kâ" harfinin yazı tipinde doğru çıktığını ekran görüntüsünde kontrol et.
  Çıkmazsa "Çizim Kahini" kullan ve ILERLEME'ye yaz.
- Oyun içi geçiş kartı da yeni adı gösterir (`proto.AD`). `ACIKLAMA` metinleri kısa ve emir kipinde kalır.
- Kabul: menünün ekran görüntüsü (`%TEMP%\cila_kareler\menu.png`). 9 simgenin hepsi ayırt edilir,
  TKM soluk durur.
- Test: `ikonlar` listesinde 9 öğe var, ilk 3 değişmemiş (piksel özeti eşit), yeni 6'nın hepsi
  rakam kartından farklı.

## 5. Penaltı (Altın Vuruş): mekanik doğrulama

**Bulgu (Enes):** "Şu an çok saçma, yay mekaniği gibi. Parmakla yönü, yolu ve ivmeyi çiziyormuşuz gibi olmalı."
`2f267d27` sapanı kaldırıp yol çizme mekaniğini getirdi. Enes büyük ihtimalle eski sürümü gördü.
Yeni kod yazmadan önce kontrol et:
- Ekranda ya da yazılarda "çek-bırak", "ger", "sapan" kalıntısı kaldı mı?
- Tanıtım animasyonu, parmağın topa değip kaleye doğru **yol çizdiğini** gösteriyor mu?
- Çizilen yol, top giderken parlayan iz olarak görünüyor mu?
- Topun uçuşu çizilen kavisi izliyor mu?

Eksik olan varsa yalnız onu düzelt. Mekaniği yeniden tasarlama. ILERLEME'ye "Enes tekrar denesin" notu düş.

## 6. Altın Vuruş (`p_penalti.py`): çift şut, zor kontrol, sanal kaleci (Enes 2026-10-13, canlı)

**Bulgu (Enes):** "Kontrolleri çok zor ve topu atıyorum 2 kez gidiyor, buga girip." / "Kaleci olsun,
yalancıktan da olsun; top giderken atlasın, animasyonlu şekilde."

**6a. Çift şut (önce teşhis, kanıtla).** Tek bir parmak hareketi iki uçuş başlatıyor. Olası kökler (doğrula ya da ele):
- `atis_sonuc` sonrası `yeni_atis` fazı `bekle`'ye alıyor, parmak hâlâ topun 60 px yakınında; 0,3 sn kilitle ikinci çizim başlıyor.
- `ciz` fazında `.28 sn` duraksama şutu erken atıyor; hareketin kalanı yeni bir şut oluyor.
- `kontrol` aynı karede iki kez çağrılıyor ya da `sut` iki kez giriyor (`gecmis`, `atilan` iki artıyor mu?).
Hedef: bir atıştan sonra parmak **topun 140 px dışına çıkıp geri gelmeden** yeni atış kilitlenmez; sonuç ekranı
bitmeden hiç kilitlenmez. Kabul testi: aynı sentetik el dizisini (dokun, çiz, dur, parmak topta kalsın 3 sn)
oynat, `sut` tam 1 kez çağrılır, `atilan[rol]` tam 1 artar.

**6b. Kontrol kolaylaşsın** (yöntem serbest, sonuç ölçülsün):
- Kalem şartı gevşesin: yalnız işaret parmağı ucu yeter, orta parmak kapalı olmak zorunda değil.
- Topu yakalama yarıçapı stant mesafesinde ≥ 90 px; kilit ≤ 0,2 sn.
- Kısa ve hızlı bir fiske (≥ 80 px, ≤ 0,35 sn) da şut sayılır; yolun sonunda durmak şart değil.
- Kabul: 15 FPS, ±6 px titreşim, %10 kare kaybıyla 20 sentetik fiske/çizimden ≥ 19'u tam 1 şut üretir;
  rastgele el sallama (topa değmeyen) 0 şut üretir.

**6c. Sanal kaleci, yalancıktan atlar.** Tek oyunculu modda (gerçek kaleci yokken) kalede çizilmiş bir kaleci olsun.
Önceki "avatar yok" kararı Enes'in bu isteğiyle değişti; iki kişilik modda gerçek kişi kaleci olmaya devam eder.
- Görünüm: neon çizgi stilinde (diğer kartlar gibi), kafa + gövde + kollar + eldiven; emoji/hazır görsel yok.
- Bekleme: ağırlığını sağa sola verir, hafif zıplar (canlı dursun).
- Şut gelince: önce **yanlış tarafa küçük bir aldatma** (≈ 0,15 sn), sonra seçtiği köşeye **uzanarak atlama**
  (gövde eğilir, kollar uzanır, ≈ 0,4 sn), yere düşüş. Top uçuşuyla eş zamanlı.
- Zorluk adil: kaleci yaklaşık %30 kurtarır; köşeye ve üst direğe yakın şutlar daha zor kurtarılır.
  Kurtarışta "KURTARDI!" ve eldiven parlaması, golde kaleci yerde kalır.
- Karar mevcut `kale_karari` ile tutarlı olsun: çizilen kaleci kolu topa değdiyse `Tutuş`, değmediyse `GOL`.
- Kabul: 200 rastgele şutta kurtarış oranı %20–40; aynı şutta karar ile çizim tutarlı (kol topa değmeden
  `Tutuş` yok). Animasyon karelerinin ekran görüntüleri (bekleme, aldatma, atlama, yer) `%TEMP%\cila_kareler\`.

Dokunma: `stant_app.py`, `p_cevap_yagmuru.py`, `p_hayalet_klon.py` (Opus).

## Bitiş

- Tam takım: `app/.venv/Scripts/python.exe -m pytest -q kabul_prototip -p no:cacheprovider`, çıkış 0.
  Test sayısı mevcut 202'den düşmez.
- 2000+ karelik gürültülü döngü 1, 2, 3 ve 5. işlerin hepsinde exception'sız tamamlanır.
- Her iş için önce/sonra ekran görüntüleri.
- ILERLEME'ye ne yapıldı, hangi komut, gerçek çıkış kodu ve kontrol edilmeyenler yazılır.
