# 12. İnsan Dizisi: İşlem Dizisi + Cümle Dizisi (hoca isteği, Enes 2026-10-13)

Hazırlayan: Claude Opus 5.5, 2026-10-13. Uygulayıcı: Codex (**bizzat yaz, başka işçiye devretme**).
Öncelik: **P1**. Bu iki oyunu hoca istedi; stant günü gösterilecek.
Önce `README.md` (değişmez kurallar), `01-ALTYAPI.md` §2 ve §4 oku. Bu dosya §4'ü bu oyun için genişletir.

## 0. Hocanın isteği (kelimesi kelimesine, WhatsApp 22:23)

> "Rastgele iki sayı (-100 100) aralığında olsun. Bir de işlem seç, sonuncusu da bu işlemin sonucu olacak.
> Kişiler sağdan sola doğru sıraya geçtiğinde 3 saniye sayar diğer soruya geçersin.
> Bir diğerinde de 4 kelimelik cümleler olacak, yine doğru sıraya geçtiklerinde biter."

Enes'in netleştirmeleri (2026-10-13, bağlayıcı):
- Oyuncu sayısı **3, 4 veya 5**, tura göre değişken.
- **Yalnız kamera.** Renkli kart, yelek, fiziksel malzeme yok. Diğer Stant oyunları gibi kamera insanları görür.
- "Sağdan sola" = yalnız **"sıraya geçin"** demek. Özel bir yön kuralı yok: ekranda soldan sağa okunur.
- Dört işlem de olsun (+ − × ÷).

## 1. Oyunun özü (tek cümle)

Ekrandaki her oyuncunun başının üstünde bir **kart** asılı durur (sayı, işlem ya da kelime). Oyuncular
birbirinin önünden geçip yer değiştirerek kartları doğru sıraya dizer. Sıra **3 saniye** bozulmadan
kalınca soru biter, yeni kartlar dağıtılır.

İki oyun **tek motoru** paylaşır, yalnız içerik paketi değişir:

| Menü adı | Dosya | Kartlar |
|---|---|---|
| **İşlem Dizisi** | `prototipler/p_islem_dizisi.py` | sayı / işlem / `=` / sonuç |
| **Cümle Dizisi** | `prototipler/p_cumle_dizisi.py` | cümlenin kelimeleri |

Ortak motor: `prototipler/dizi_motor.py`. Görünüş imzası (kimlik kurtarma): `prototipler/kimlik_imza.py`.
İçerik: `prototipler/veri/dizi_cumleler.json`. Testler: `kabul_prototip/test_insan_dizisi.py`,
`kabul_prototip/test_kimlik_imza.py`.

İki oyun menüde **iki ayrı kart** olarak görünür (hoca iki oyun istedi). Menü şu an 9 karttır; 11 kart
sığmıyorsa README'deki "2 sayfa ya da kaydırmalı şerit" kuralını uygula. Kart başına el ile seçim korunur.

## 2. Asıl risk: kart yanlış kişiye geçmesin

Oyunun tamamı **insanların birbirinin önünden geçmesinden** oluşuyor. Bu da kamera için en kötü durum:

- İki kişi çakışınca MediaPipe PoseLandmarker arkadakini birkaç kare kaybeder.
- Bugünkü `oyuncu.py` takibi (`OyuncuKapisi.suz`) **yalnız konum + hız** ile açgözlü en yakın eşleşme
  yapar. Görünüş bilgisi yok.
- Kaybolan kişi geri geldiğinde (çaprazlama tam ortasında, iki kişi neredeyse aynı x'teyken) en yakın
  eşleşme kimlikleri **takas edebilir**. Kart yanlış kişide kalır. Oyuncu doğru yerde durduğu hâlde oyun
  "yanlış" der. Bu oyunu öldüren tek hatadır.

Bu henüz **ölçülmedi**, beklenen davranış bu. §9'daki ölçümün ilk koşusu bunu bugünkü takiple ölçer
(taban), sonra düzeltilmiş hâliyle tekrar ölçer.

Çözüm üç katmandan oluşur. Üçü de bu dosyanın kapsamında:

1. **Görünüş imzası** (`kimlik_imza.py`, §3): kişinin gövdesindeki kıyafet renginden çıkarılan küçük bir
   vektör. Kişi yalnızken öğrenilir, çakışmadan sonra karar verirken kullanılır.
2. **Karışma olayı çözümü** (`dizi_motor.py`, §4): iki ya da daha çok kişi çakıştığında kartlar
   **dondurulur**; ayrıldıklarında yalnız o gruptaki kişiler için "takas mı, değil mi" kararı imza + hareket
   maliyetiyle verilir. Yani bütün sahne değil, tek bir küçük atama problemi çözülür.
3. **İnsan düzeltmesi** (§4.4): karar belirsizse kart sarı "?" ile işaretlenir; belirsiz çiftten biri elini
   başının üstüne kaldırınca iki kartı takas eder. Sessiz yanlış yerine görünür belirsizlik.

**Yasak:** kimlik sorununu oyunu kolaylaştırarak gizlemek (örneğin kartı kişiye değil konuma bağlamak).
Kart kişiye yapışıktır, oyunun anlamı budur.

## 3. `kimlik_imza.py`: görünüş imzası

Saf fonksiyonlar + küçük bir sınıf. Görüntü diske yazılmaz, imza yalnız bellekte tutulur (gizlilik kuralı).

### 3.1 Bölge
- Gövde dörtgeni: poz noktaları 11 (sol omuz), 12 (sağ omuz), 24 (sağ kalça), 23 (sol kalça).
- Dörtgeni merkezine doğru **%20 küçült** (kenardaki kol ve arka plan sızmasın).
- Kalçalar görünmüyorsa (visibility < 0.5): omuzlardan aşağı **omuz genişliği × 1.2** boyunda dikdörtgen.
- Bölge kare dışına taşıyorsa kırp. Kalan alan < 400 piksel ise imza **çıkarılmaz** (None).
- Ayrıca küçük ikinci bölge: **baş üstü / saç** (burun 0'dan yukarı, göz arası × 1.5 kare). Ağırlığı düşük
  (§3.3). Aynı tişörtlü iki kişiyi ayırmaya yardım eder.

### 3.2 Vektör
- Bölgeyi 64×64'e küçült, HSV'ye çevir.
- **H–S 2B histogram**: H 16 kutu, S 4 kutu, yalnız V ≥ 40 ve S ≥ 30 pikseller (siyah/gri gürültüsü
  renk kutularına girmesin). Ayrıca **akromatik kısım**: S < 30 pikselleri için V 4 kutu (siyah, koyu gri,
  açık gri, beyaz). Toplam 64 + 4 = 68 boyut, L1 normalize.
- Ek: bölgenin Lab ortalaması (3 sayı), aydınlık farklarına karşı yedek.
- Aynı vektör saç bölgesi için de çıkarılır.

### 3.3 Uzaklık
- `uzaklik(a, b) = 0.75 · bhattacharyya(gövde) + 0.15 · bhattacharyya(saç) + 0.10 · min(1, ΔE_Lab / 40)`.
- Saç imzası yoksa ağırlığı gövdeye ekle.
- 0 = aynı, 1 = tamamen farklı.

### 3.4 Öğrenme (yalnız güvenli anlarda)
`Imza` sınıfı, kimlik başına:
- `guncelle(kimlik, vektor, simdi, yalniz: bool)`: yalnız kişi **yalnızken** öğrenir. Yalnız demek:
  pozunun kutusu (omuz-kalça kutusu %30 genişletilmiş) başka hiçbir pozun kutusuyla kesişmiyor ve kişi
  `tahmini` değil.
- Üstel ortalama, α = 0.1. İlk 10 güvenli örnek birikmeden imza **"olgun değil"** sayılır.
- Saniyede en çok 10 güncelleme. Her karede hesaplamak gerekmez, maliyet bütçesi §10.
- Kimlik silinince imza da silinir. Tur bitince her şey sıfırlanır.

### 3.5 Kabul (`test_kimlik_imza.py`, en az 6 test)
Sentetik kare: siyah zemin, `sahte_poz` noktalarına göre gövde dörtgeni düz renkle boyanır.
1. Aynı renkli iki boyamada uzaklık < 0.15.
2. Kırmızı ile mavi gövde arasında uzaklık > 0.6.
3. Siyah ile koyu lacivert ayrılıyor (uzaklık > 0.25). Akromatik kısım burada çalışmalı.
4. Gövde aynı, saç farklı: uzaklık, aynı-aynı durumundan büyük.
5. Alan < 400 px ya da kare dışı bölge: `None` döner, hata vermez.
6. Kesişen iki pozda `yalniz=False`, imza güncellenmiyor (değeri değişmiyor).
7. (öneri) %30 parlaklık düşüşünde aynı kişinin uzaklığı < 0.3.

## 4. `dizi_motor.py`: ortak motor

### 4.1 Oyuncu modeli
Her oyuncu: `kimlik` (oyuncu.py poz kimliği), `kart` (indeks), `x` (süzülmüş gövde ortası x'i, 0–1),
`imza`, `renk` (kimlik paleti), `durum` (`normal`, `donmus`, `belirsiz`).

Gövde x'i: kalça ortası (23, 24). Kalçalar görünmezse omuz ortası (11, 12). İkisi de visibility < 0.5
ise o kare için x güncellenmez, son değer korunur.

Ekran aynalı. **Okuma sırası = ekranda soldan sağa artan x.** Yön kuralı yok (Enes: "sıraya geçin" kastı).

### 4.2 Oyun alanı ve sayım
- Oyun alanı: ekran x'inde 0.04–0.96, kişinin omuz genişliği ≥ `0.035` (Cevap Yağmuru'ndaki
  `KAPI = {"poz_omuz_min": .035}` kalıbı). Daha küçük görünen kişi (arkadaki izleyici) sayılmaz.
- **Oyuncu Kapısı'ndan geçmeyen poz sayılmaz** (`algi.tahmini`, `adaylar`, `redler` kuralları).
- Tura katılım sayısı N, lobide belirlenir (§5.1) ve tur boyunca **sabittir**.

### 4.3 Karışma olayı (çakışma)
Her karede iki koşulla "karışma grubu" kurulur:
- iki oyuncunun gövde kutuları %30 genişletilmiş hâlde kesişiyor, **ya da**
- bir oyuncu `tahmini` (pozu kayıp, takip son konumla dolduruyor) ve başka bir oyuncuya yakın
  (x farkı < 1.5 × omuz genişliği).

Karışma başlayınca:
- Gruptaki oyuncuların kartları ve sıradaki yerleri **dondurulur**. Kart ekranda kişiyi izlemeye devam
  eder ama hafif saydamlaşır, kenarında dönen ince halka "takip ediliyor" der.
- Grubun başlangıç anındaki kimlik → imza eşleşmesi, giriş x'leri ve hızları saklanır.
- Bu sırada sıra kontrolü yapılır ama **geri sayım başlamaz** (dondurulmuş grup varsa geri sayım beklemede).

Karışma bitince (grup üyeleri 0.25 sn boyunca ayrık kalınca) **çözüm**:
- Gruptaki oyuncu sayısı k (genelde 2, en çok 5). Gruptaki eski kimlikler ile şimdiki pozlar arasında
  k×k maliyet matrisi:
  `maliyet = 0.7 · imza_uzakligi + 0.3 · hareket_maliyeti`.
  `hareket_maliyeti`: çakışma girişindeki hızla, kişinin şimdiki konumu ne kadar tutarlı (sabit hız
  varsayımıyla öngörülen konuma uzaklık / omuz genişliği, 0–1'e kırpılır).
- k ≤ 5 için tüm permütasyonları dene (en çok 120), en düşük toplam maliyetli atamayı seç. scipy'ye gerek yok.
- **Güven payı:** en iyi ile ikinci en iyi atamanın toplam maliyet farkı `pay`.
  - `pay ≥ 0.15` → atama uygulanır, kartlar yeni sahiplerine bağlanır, `durum = normal`.
  - `pay < 0.15` ya da gruptaki imzalardan biri olgun değil → en iyi atama yine uygulanır, ama ilgili
    kişiler `durum = belirsiz` olur (§4.4).
- Ayrıntı: `oyuncu.py`'nin verdiği poz kimliği çaprazlamada değişmiş olabilir. Motor kendi
  **oyuncu → poz kimliği** eşlemesini tutar, karar sonrası onu günceller. `oyuncu.py`'nin kendi
  davranışını bu oyun için değiştirme (diğer oyunlar onu kullanıyor). Gerekirse `OyuncuKapisi`'na
  geriye uyumlu, varsayılanı kapalı bir seçenek ekle ve diğer testler yeşil kalsın.

Bütün olaylar `self.olaylar` listesine yazılır: `("karisma", t, kimlikler)`, `("cozum", t, atama, pay)`,
`("belirsiz", t, kimlikler)`, `("el_takas", t, a, b)`. Ölçüm (§9) ve test bunu okur.

### 4.4 Belirsizlik ve el ile düzeltme
- Belirsiz kişinin kartı sarı kenarlı, köşesinde "?" rozeti. Ekranın altında tek satır:
  **"Kart yanlış kişide mi? Elini kaldır."**
- Belirsiz çiftten biri **bileği (15 ya da 16) burnun (0) üstünde 0.8 sn tutarsa**: çiftin kartları takas
  edilir, iki kişi de `normal` olur, 1 sn "Değişti!" yazısı ve ses (`Ses.cal`). Halka dolumu gösterilir
  (README kural 9: kalıcı eylem görünür dolan halkayla olur).
- Belirsiz durumda **2.5 sn** kimse el kaldırmazsa ve kişiler 1 sn boyunca ayrık kalırsa, imza yeniden
  karşılaştırılır (artık daha çok güvenli örnek var). Pay ≥ 0.15 olursa sessizce düzeltilir ya da onaylanır.
  Belirsizlik sonsuza kadar kalmaz: 6 sn sonra `normal` olur.
- Geri sayım belirsiz kişi varken de çalışabilir. Kartların gösterdiği sıra doğruysa oyuncular ne
  gördüyse ona inanır. Bu, sahneyle uyumludur: oyuncular kartlara bakıp dizilir.
- Belirsiz olmayan kişi el kaldırırsa hiçbir şey olmaz (doğal el kaldırma kartı değiştirmez, kural 9).

### 4.5 Sıra kontrolü ve histerezis
- Oyuncular x'e göre sıralanır. Sıra, ancak **iki komşu oyuncunun x farkı ≥ 0.25 × ortalama omuz genişliği**
  olduğunda değişmiş sayılır. Daha yakın iki kişi önceki sıralarını korur. Böylece yan yana duran iki kişinin
  sırası titreşmez.
- İçerik paketi `dogru_mu(kart_dizisi) -> bool` verir (§6, §7). Motor her karede kart dizisini oluşturup sorar.

### 4.6 3 saniyelik geri sayım
- `dogru_mu == True` olunca sayım başlar. Ekranda büyük halka + "3, 2, 1" ve her saniye tik sesi.
- Sıra bozulursa **0.3 sn tolerans**: bu sürede düzelirse sayım kaldığı yerden devam eder. Aşılırsa sayım
  sıfırlanır, halka kırmızı yanıp söner, "Bozuldu!" yazısı çıkar (0.6 sn).
- Bir oyuncunun pozu kaybolursa (takip son konumla dolduruyorsa) en çok 0.5 sn boyunca sıra son bilinen
  konumla hesaplanır. Bundan uzun kayıpta sayım duraklar (sıfırlanmaz), "N kişi görmem lazım" uyarısı çıkar.
- 3 sn dolunca: doğru sesi, kartlar yeşil parlar, sıra boyunca soldan sağa dalga efekti, 1 sn kutlama, sonra
  sonraki soru.

### 4.7 Kartın çizimi
- Kart, kişinin **başının üstünde** durur: burnun (0) y'si − 1.6 × göz arası (yoksa omuz ortası − 1.1 × omuz
  genişliği). Ekran üstüne taşarsa üst sınıra yapışır, kişinin üstünde ince ok bırakılır.
- Kart konumu One Euro ile süzülür (`filtre.py`, 01 §3). Kart titremez ama kişiyi takip eder.
- **Okunurluk:** HP ekranında 3 m'den okunmalı. Kart yazı yüksekliği **en az 56 px** (1280×720'de),
  genişlik metne göre, en az 150 px. Uzun kelimeler (> 9 harf) yazı boyunu küçültmez, kartı genişletir.
  Çok yakın iki kartın taşmasını önlemek için kartlar yatayda iterek ayrılır (kişiye bağlı ok kalır).
- **Görsel dil:** koyu yarı saydam panel (`panel`), neon kenar oyuncunun kimlik renginde.
  Sayı kartı dikdörtgen, **işlem kartı daire** (farklı şekil: `−` işlem kartı ile `(-37)` sayısı asla
  karışmasın), `=` kartı ince yatay hap şekli. Cümle kartları dikdörtgen.
- Kişinin üstünde ince iskelet çizgisi (kimlik renginde, %40 opak): hocaya "kamera seni görüyor" hissi.
  Belirgin ama oyunu boğmasın.
- Ekranın altında **hedef şeridi**: N boş kutu, yalnız sıra numaraları (1..N). Doğru konumdaki kartlar
  kutularında yeşil yanmaz (cevabı ele vermesin), yalnız tam doğru olunca hepsi birden yeşil olur.
  İpucu verildiğinde (§5.4) ilgili kutu açılır.

## 5. Akış (iki oyunda aynı)

Durumlar: `bekle → lobi → dagit → coz ↔ sayim → kutla → (sonraki soru: dagit) → sonuc → bekle`.
`OyunAkisi` (oyun_akis.py) kalıbını kullan; `oyun` sırasında `self.durum == "oyun"` sözleşmesi korunmalı
(stant_app boşta menüye dönmesin). Motorun iç durumları ayrı alan (`self.faz`) olsun.

### 5.1 Lobi: oyuncu sayısı
- Bekleme ekranı: "3–5 kişi yan yana durun". Alandaki geçerli oyuncu sayısı canlı gösterilir:
  her oyuncunun başında boş kart ve büyük sayaç "4 kişi".
- Sayı 3, 4 ya da 5 olup **1.5 sn sabit** kalınca: "Hazırsanız hepiniz elinizi kaldırın".
- **Tüm oyuncular** bileğini burnun üstünde **0.8 sn** tutunca (dolan halkalar her kişinin kartında) tur
  başlar. N bu andaki sayıdır.
- 2 kişi: "En az 3 kişi lazım". 6+ kişi: "En fazla 5 kişi, biri geri çekilsin". Fazladan biri olduğu sürece
  başlamaz.
- Operatör tuşları: `3`, `4`, `5` sayısı zorlar (stant görevlisi için), `Boşluk` başlat. Tuş yoksa her şey
  jestle çalışır.

### 5.2 Dağıtım
- Kartlar ekranın üstünden kişilerin başına uçar (0.8 sn, sırayla 0.1 sn arayla, "fıp" sesi).
- **Başlangıç dizisi asla doğru olmamalı**: rastgele permütasyon üret, `dogru_mu` doğruysa yeniden karıştır.
  Ayrıca kaba zorluk: en az ⌈N/2⌉ kart doğru yerinde olmasın (yerinde olan kart sayısı ≤ N − ⌈N/2⌉).
- Dağıtım soldan sağa mevcut sıradaki kişilere yapılır.

### 5.3 Tur
- Tur **5 soru** (`SORU_SAYISI = 5`). Toplam süre ölçülür.
- Soru başına puan: `max(100, 1000 − 12 × saniye)`. Kullanılan ipucu başına −150.
- Tur ortasında oyuncu sayısı N'nin altına düşerse: 2 sn bekle, sonra duraklat ("Biri eksik, geri gel").
  8 sn içinde dönen kişi imzayla yeniden bağlanır (§4.3 çözümünün aynısı, grup = eksik kimlikler + yeni
  pozlar). Dönmezse tur biter, kazanılan puan sonuçta gösterilir.
- Alana N+1'inci kişi girerse: kart verilmez, gri "izleyici" etiketi alır, sıra kontrolüne katılmaz. Oyun
  durmaz. Yalnız izleyici bir oyuncuyla karışırsa normal karışma çözümüne girer (imzası olmayan aday =
  yüksek maliyet).

### 5.4 İpucu ve pas
- 20 sn: 1. hedef kutusunda doğru kart görünür (silik).
- 35 sn: son kutu da açılır.
- 50 sn: "Pas için hepiniz el kaldırın" çıkar. Hepsi 0.8 sn el kaldırırsa soru geçilir, 0 puan.
- Sürelerin hepsi sınıf sabiti, test bunları kısaltabilsin.

### 5.5 Sonuç
- Toplam puan, toplam süre, takım adı (rastgele: "Neon Kartallar", "Mor Şimşekler" gibi 20 ad listesi).
  En iyi 5 takım listesi (yüz yok, gizlilik kuralı). ≤ 6 sn sonra bekleme ekranı.

### 5.6 Kuralı öğretme
Bekleme ekranında **8 kelimeyi geçmeyen** kural + hareketli örnek: üç silüet, başlarında `7`, `+`, `5`,
`=`, `12` kartları. Silüetlerden ikisi yer değiştirir, sıra doğru olunca yeşile döner. 4 sn döngü.
- İşlem Dizisi: **"Kartları doğru işlem olacak şekilde dizin!"**
- Cümle Dizisi: **"Yer değiştirin, cümleyi doğru kurun!"**

## 6. İşlem Dizisi içeriği (`p_islem_dizisi.py`)

### 6.1 Kartlar oyuncu sayısına göre
| N | Kartlar | Ekranda sabit |
|---|---|---|
| 3 | `A`, `B`, `C` | arada işlem ve `=` sabit: `[ ] + [ ] = [ ]` |
| 4 | `A`, `op`, `B`, `C` | yalnız `=` sabit, son kutudan önce: `[ ][ ][ ] = [ ]` |
| 5 | `A`, `op`, `B`, `=`, `C` | hiçbir şey sabit değil |

Hocanın tarifine en yakın N = 4 ve 5. N = 3'te işlem ekranda gösterilir, çünkü 3 kişiyle hem iki sayı
hem işlem hem sonuç olamaz.

### 6.2 Soru üretimi
- A ve B: tam sayı, **−100 ile 100 arası** (dahil). C: işlemin sonucu (aralık dışına çıkabilir:
  toplama ±200, çarpma ±10000). Enes onayladı.
- İşlem eşit olasılıkla `+`, `−`, `×`, `÷`.
- `÷`: önce B seç (0 ve ±1 hariç), sonra bölüm q seç (0 hariç), A = B × q. A aralık dışıysa yeniden seç.
  Sonuç **her zaman tam sayı**, sıfıra bölme **asla yok**.
- `×`: 0 ve ±1 çarpanı yok (çok kolay).
- Hiçbir soruda A, B, C'den ikisi eşit olmasın (kartlar birbirinden ayırt edilsin).
- Aynı turda aynı işlem üst üste 2'den çok gelmesin.
- Zorluk (sınıf sabiti `ZORLUK`, varsayılan "karışık"): ilk 2 soruda negatif sayı en çok bir tane, sonra
  serbest. Kolay stant ziyaretçisi ısınsın.
- `rng` dışarıdan verilebilsin (`np.random.default_rng(tohum)`), test tekrarlanabilir olsun.

### 6.3 Gösterim
- Negatif sayılar **parantezle**: `(-37)`. Pozitifte işaret yok: `37`.
- İşlem kartı simgeleri: `+`, `−` (U+2212 değil, fontta görünürlüğünü kontrol et; görünmüyorsa `-`),
  `×`, `÷`. `yazi_koy` fontunda bu dört simgenin çizildiğini **ekran görüntüsüyle** doğrula.

### 6.4 Doğruluk kontrolü (`dogru_mu`)
Tek doğru sıra kodlanmaz. Kart dizisi **gerçekten doğru bir eşitlik** kuruyorsa kabul edilir:
- Diziye sabit öğeleri ekle (N = 3'te işlem ve `=`, N = 4'te `=`).
- Tam olarak bir `=` olmalı; iki taraf da `sayı` ya da `sayı işlem sayı` olmalı. Başta/sonda `=`, iki işlem
  yan yana, işlemle biten taraf → geçersiz.
- Sayı kartları birleştirilmez (`3` ile `7` yan yana `37` olmaz).
- `fractions.Fraction` ile hesapla, iki taraf **tam eşitse** doğru.
- Böylece `12 + 5 = 17` ve `5 + 12 = 17` ikisi de doğru. N = 5'te `17 = 12 + 5` de doğru.
  `−` ve `÷`'de sıra önemlidir, hesap kendisi karar verir.
- Sabit işlemli N = 3 sorusunda birden fazla doğru dizilim olabilir (`A + B = C` / `B + A = C`). Hepsi kabul.

### 6.5 Kabul (İşlem Dizisi kısmı)
- 10 000 rastgele soru (3 tohum × N ∈ {3,4,5}): her birinde üretilen kanonik dizi `dogru_mu == True`;
  `÷` sorularında bölüm tam sayı, B ≠ 0; A, B ∈ [−100, 100]; A, B, C üçü farklı.
- 10 000 soruda başlangıç dağıtımı `dogru_mu == False`.
- Elle vakalar: `12 + 5 = 17` ✓, `5 + 12 = 17` ✓, `17 = 12 + 5` ✓ (N=5), `12 − 5 = 7` ✓, `5 − 12 = 7` ✗,
  `(-6) × (-7) = 42` ✓, `42 ÷ (-6) = (-7)` ✓, `= 12 + 5 17` ✗, `12 5 + = 17` ✗, `1 7 = 12 + 5`-tipi
  birleştirme ✗.

## 7. Cümle Dizisi içeriği (`p_cumle_dizisi.py`, `veri/dizi_cumleler.json`)

### 7.1 Kelime sayısı = oyuncu sayısı
Hoca 4 kelime dedi; oyuncu sayısı değişken olduğu için banka **3, 4 ve 5 kelimelik** cümle içerir. N = 4
varsayılan ve en zengin bölüm.

### 7.2 Türkçe tuzağı: sözcük sırası serbest
"Ben okula hızlı gittim" de "Ben hızlı okula gittim" de doğrudur. Tek bir sırayı doğru saymak, doğru dizilen
oyuncuyu yanlış sayar. Bu oyunun en kolay bozulacağı yer burası.

Kural:
- Her cümlede `kelimeler` (kanonik sıra) ve `kabul` (kabul edilen **tüm** sıralar, her biri indeks listesi)
  alanları var. Kanonik sıra `kabul` içinde olmak zorunda.
- `dogru_mu`: oyuncuların kart dizisi `kabul` listesindeki sıralardan biriyse doğru.
- Aynı kelime iki kez geçiyorsa (örn. "çok çok"), eşit kartların yer değiştirmesi aynı dizi sayılır
  (karşılaştırmayı indeksle değil **metinle** yap).
- Cümle seçme ilkesi: **yüklem sonda**, ekler sırayı mümkün olduğunca belirlesin. Devrik ya da şiirsel ama
  dilbilgisel olarak doğru sıraları da `kabul`e yaz; insanlar dizerken onları da kurabilir.
- İpucu: ilk kelimenin büyük harfi ve son kelimenin noktası **kartta görünür** (`IPUCU_BUYUK_HARF = True`).
  Bu, olası sıraları çok azaltır ve oyunu adil yapar. Büyük harfli kelime sonda, noktalı kelime başta
  olan sıraları `kabul`e **yazma**.

### 7.3 Banka
- En az **25 adet 3 kelimelik, 50 adet 4 kelimelik, 30 adet 5 kelimelik** cümle.
- Konu karışımı: üniversite/kampüs, teknoloji ve yapay zekâ, İstanbul, yemek, spor, günlük hayat. Esprili
  olanlar iyi ("Robot bize çay demledi."). Kişi adı yok (gerçek kişi, hoca, öğrenci adı **yok**).
- Uygunsuz, siyasi, dini, cinsiyetçi içerik yok. Her kelime en çok 12 harf.
- Bir cümlede iki kelime **aynı yazılmasın** (kart karışıklığı), mecbur kalınırsa §7.2 metin kuralı geçerli.
- Örnek biçim:

```json
{
  "surum": 1,
  "cumleler": [
    {"id": "c4-001", "kelimeler": ["Kedi", "masadan", "bardağı", "düşürdü."],
     "kabul": [[0, 1, 2, 3], [0, 2, 1, 3]], "konu": "gunluk"},
    {"id": "c3-001", "kelimeler": ["Robot", "çay", "demledi."],
     "kabul": [[0, 1, 2]], "konu": "teknoloji"},
    {"id": "c5-001", "kelimeler": ["Öğrenciler", "kantinde", "sıcak", "simit", "yedi."],
     "kabul": [[0, 1, 2, 3, 4], [0, 2, 3, 1, 4]], "konu": "kampus"}
  ]
}
```

- Banka yazıldıktan sonra `veri/dizi_cumleler_inceleme.md` üret: her cümle, kanonik sıra ve kabul edilen
  diğer sıralar okunur metin olarak ("Kedi bardağı masadan düşürdü."). **Enes bunu okuyup onaylayacak**;
  onaylanana kadar banka "taslak" sayılır. Opus da dil kontrolü yapabilir. Codex kendi dil tahminini kesin
  doğru sayıp kapatmasın.

### 7.4 Soru seçimi
- Tur içinde aynı cümle tekrar gelmez. Turlar arasında son 15 cümle tekrar gelmez (bellekte tut).
- Konu çeşitliliği: aynı turda aynı konudan en çok 2 cümle.

### 7.5 Kabul (Cümle Dizisi kısmı)
- Şema testi: her kayıtta `id` benzersiz, `kelimeler` uzunluğu 3–5, `kabul` boş değil, kanonik sıra
  içinde, her `kabul` öğesi geçerli bir permütasyon, büyük harfli kelime başta, noktalı kelime sonda
  (`IPUCU_BUYUK_HARF` açıkken), kelime ≤ 12 harf.
- Sayım testi: 3/4/5 kelime için en az 25/50/30 cümle.
- `dogru_mu`: kanonik ✓, listedeki alternatif ✓, listede olmayan permütasyon ✗, aynı metinli iki kartın
  yeri değişince ✓.
- Her cümle için başlangıç dağıtımı `dogru_mu == False` (tek kabul sıralı ve N=3 cümlelerde bile).

## 8. Kör kabul testleri (`test_insan_dizisi.py`, en az 18 test)

`PROTOTIP` kalıbını izle (`test_ozel.py`, `test_cila.py`). Kamera yok; `sahte_poz` ile sahte kişiler,
`simdi` elle ilerletilir. Görünüş için sentetik kare: her sahte kişinin gövdesi farklı düz renkle boyanır
(§3.5 aracı). Hem `p_islem_dizisi` hem `p_cumle_dizisi` için koşulacak testler `parametrize` ile.

1. Oyuncu yok → `bekle`. 3 kişi 1.5 sn → lobi "hazır". Hepsi el kaldırır 0.8 sn → tur başlar, N=3,
   `self.durum == "oyun"`.
2. 2 kişi ve 6 kişi: tur başlamaz, doğru uyarı metni üretilir.
3. Lobide 4 kişi, biri el kaldırmıyor → başlamaz.
4. Dağıtım sonrası dizi `dogru_mu == False`, her oyuncunun tam bir kartı var, kartlar benzersiz.
5. Kişileri doğru sıraya getirince (sahte pozların x'lerini değiştir, aralarda çaprazlama yok) sayım başlar,
   3.0 sn sonra soru biter, sonraki soru dağıtılır.
6. Sayım 2.0. sn'de sıra 0.2 sn bozulup düzelirse sayım sıfırlanmaz; 0.5 sn bozulursa sıfırlanır.
7. Yan yana çok yakın iki kişi (x farkı < 0.25 omuz) titreşen x ile sırasını değiştirmez (histerezis).
8. **Temiz çaprazlama:** farklı renkli 2 kişi yer değiştirir, ortada 8 kare boyunca biri kayıp (poz listesinden
   çıkar). Sonunda kartlar doğru kişide, `olaylar`da `karisma` + `cozum` var, `belirsiz` yok.
9. **Kimlik takası tuzağı:** aynı senaryo, ama `oyuncu.py`'nin verdiği poz kimlikleri çaprazlamadan sonra
   bilerek **ters** veriliyor. Motor imzayla doğru kişiye bağlıyor.
10. **Aynı renkli iki kişi** çaprazlıyor: `belirsiz` olayı yazılıyor, kartlarda "?" var.
11. Belirsiz çiftten biri el kaldırınca 0.8 sn sonra kartlar takas, `el_takas` olayı; belirsiz olmayan
    kişinin el kaldırması hiçbir kartı değiştirmiyor.
12. 3 kişilik grup karışması (ortadaki iki yana geçer): permütasyon çözümü doğru.
13. 5 kişiyle tam tur: 5 soru doğru dizilir, `sonuc` durumuna geçer, puan > 0, ≤ 6 sn sonra `bekle`.
14. Tur ortasında bir oyuncu 3 sn kaybolup aynı renkle başka x'te döner: aynı kartı geri alır.
15. Bir oyuncu 9 sn dönmez: tur biter, sonuç ekranı.
16. N+1'inci küçük kişi (izleyici, omuz < 0.035) ve büyük izleyici: kart almaz, sıra kontrolüne girmez.
17. İpucu zamanlayıcısı (sabitler kısaltılmış): 20 sn kutu ipucu, 50 sn pas, hepsi el kaldırınca soru geçilir,
    puan 0.
18. `isle()` her durumda 1280×720×3 BGR döner, istisna atmaz; 2000 rastgele gürültülü kare (eksik
    noktalar, NaN, boş algı, ani 6 kişi) boyunca çökme yok (Kuş/Çiz/Penaltı 2005 kare testinin kalıbı).
19. Menü testi: iki oyun `DENEYIMLER`'de, kendi ikonlarıyla menüde görünüyor, adlar "İşlem Dizisi" ve
    "Cümle Dizisi".

Testler önce kırmızı görülsün (kod yokken ya da ilgili kısım eksikken), sonra yeşil. İkisi de ILERLEME'ye.

## 9. Gerçek ölçüm (kamerayla, Enes ya da arkadaşlarıyla)

Kör test kimliği sentetik renkle sınar; gerçek kıyafet, ışık ve kamera gürültüsü ayrıca ölçülür.

### 9.1 Kayıt aracı
`prototipler/dizi_olcum.py`:
- Oyun açıkken `K` tuşu kaydı başlatır/bitirir. Kayıt: kare başına poz noktaları, poz kimlikleri, motorun
  oyuncu → kart eşlemesi, imza vektörleri (sayılar, **görüntü değil**), `olaylar`. JSONL, `TEMP` altına.
- `--tekrar dosya.jsonl` kaydı motora tekrar oynatır (kamera yok). İmza parametreleri değiştirilip aynı
  kayıtla yeniden ölçülebilir.
- Operatör her çaprazlamadan sonra kartlar doğruysa `D`, yanlışsa `Y` tuşuna basar. Etiket kayda yazılır.
  Bu, "doğru" kararının kaynağıdır.

### 9.2 Protokol
- Kamera HP ProOne'un kendisi (stant günü kurulumu, `00-DONANIM-VE-YAYIN.md`). Laptop kamerasıyla da
  ayrı koşu yap, ayrı raporla.
- Oyuncular **3 m** geride (5 kişi için gerekirse 3.5 m). 5 kişinin tamamı kadrajda ve omuzları ≥ 0.035
  mi, önce bunu ölç ve yaz. Değilse kamera yerini/uzaklığını yaz, sonra devam et.
- Senaryolar, her biri **en az 10 çaprazlama**:
  a) 2 kişi, farklı renk kıyafet; b) 2 kişi, ikisi de koyu/siyah; c) 3 kişi, ortadaki yana geçer;
  d) 5 kişi tam tur, serbest oyun; e) koşarak hızlı yer değiştirme.
- Taban: aynı senaryolar **imzasız** (yalnız `oyuncu.py` konumu) hâliyle de ölçülür, karşılaştırma için.

### 9.3 Ölçüt
| Ölçü | Hedef |
|---|---|
| Sessiz yanlış (kart yanlış kişide, belirsiz işareti yok) / çaprazlama | **≤ %5** (a, c, d, e); b'de ≤ %15 |
| Yanlışlardan belirsiz olarak işaretlenen oran | ≥ %70 |
| Gereksiz belirsiz (kart doğru ama "?") / çaprazlama | ≤ %20 |
| El takasıyla düzelen belirsizler | ölç, yaz |
| İmzasız tabana göre sessiz yanlış farkı | yaz (iddia bu tabloyla verilir) |

Hedef tutmazsa: önce eşikleri `--tekrar` ile ayarla (aynı kayıt, yeni parametre). Yine tutmazsa §11.

## 10. Performans bütçesi

- Algı: mevcut `Algilayici`, `IHTIYAC = {"poz"}` (gerekirse `"el"` yok; el kaldırma poz bileğinden okunur).
  PoseLandmarker `num_poses=6` zaten var. Yüz ve el modeli **açılmaz**.
- `isle()`: README kuralı: medyan ≤ 14 ms, p95 ≤ 25 ms (laptop, 1280×720). İmza hesabı 5 kişi için
  ≤ 2 ms hedef (64×64 küçültme + histogram), saniyede ≤ 10 güncelleme.
- `olcum.py --kiyas` iki yeni oyunu da kapsasın, 5 sahte kişiyle ölç, ILERLEME'ye tablo.
- Kart sprite'ları önbellekli (`yazi_sprite`, metin + renk anahtarı). Döngüde disk okuma yok.

## 11. Yedek plan (yalnız §9 hedefleri tutmazsa, Enes onayıyla)

Bağımlılık ekleme kararı Enes'in. Sıra:
1. İmza bölgesini genişlet (kol + bacak üst kısmı), H kutusunu 24'e çıkar, ağırlıkları `--tekrar` ile tara.
2. Küçük bir ReID ağı (ONNX, onnxruntime zaten kurulu; örn. OSNet x0.25, ~1 MB) ile gövde kırpığından
   gömme vektörü. Lisansı ve kaynak URL'sini `ARASTIRMA-KAYNAKLAR.md`'ye yaz. Model dosyası `modeller/`.
3. Kişi algısı için YOLO11n-pose + BoT-SORT (ultralytics, **AGPL-3.0**, yeni paket). En son çare; MediaPipe
   pozu 5 kişide 3–3.5 m'de kişi kaçırıyorsa (kare başına algılama < %95, §9.2 ölçümü) düşünülür.
Hiçbirini ölçüm kanıtı olmadan ekleme.

## 12. Gecikme bütçesi

Bu oyun bedenle oynanır. 300 ms gecikme bile hissedilmez; 3 sn'lik sayım ve 0.3 sn tolerans gecikmeyi
emer. Kablosuz yayın hattında da çalışır. Tek hassas an el kaldırma halkasıdır, 0.8 sn tutma onu da emer.

## 13. Sesler

`Ses` sentezi ya da önyüklenmiş: kart dağıtma "fıp", sayım tiki (her saniye, son saniyede tiz), doğru
fanfarı, "bozuldu" kısa vızıltı, el takası "çın", tur sonu podyum. Ses seviyesi stant ortamında
duyulacak kadar ama sayım tiki ≤ 0.5.

## 14. Teslim ve kabul sırası

1. `kimlik_imza.py` + `test_kimlik_imza.py` (önce kırmızı, sonra yeşil).
2. `dizi_motor.py` + İşlem Dizisi içerik + testler 1–13, 17–18.
3. Cümle bankası taslağı + `dizi_cumleler_inceleme.md` → **Enes'e göster, onay bekle** (dil işi).
   Bu sırada 4. adıma geçilebilir.
4. Cümle Dizisi + testler, menü kaydı + ikonlar (`ikon_islem`, `ikon_cumle`: neon, mevcut ikon dilinde).
5. Tam takım: `app\.venv\Scripts\python.exe -m pytest -q kabul_prototip -p no:cacheprovider`.
   Taban **240 passed, 32 skipped, rc 0** (CILA-YENI-7 sonu). Düşerse dur, nedenini yaz.
6. `olcum.py --kiyas` tablosu.
7. Görsel kabul: `--onizleme` ile 8 ekran görüntüsü (lobi 4 kişi, dağıtım, işlem kartları 5 kişi,
   belirsiz "?" kartı, sayım halkası, doğru dalgası, cümle kartları 4 kişi, sonuç). Codex bunlara kendisi
   bakıp kontrol eder: kart okunur mu, `−` ve `(-37)` karışıyor mu, kartlar üst üste biniyor mu.
   Sonra Enes'e.
8. §9 gerçek ölçüm: Enes ve arkadaşlarıyla. Codex aracı hazırlar, protokolü kısa bir `DIZI-OLCUM.md`
   kâğıdına döker (ne yapılacak, hangi tuş). Sonuç tablosu ILERLEME'ye.

Her adım sonunda `ILERLEME.md`'ye: tarih, ne yapıldı, komut, gerçek çıkış kodu, ölçüm, açık kalan.
Commit Enes'in kararıyla (README kural 7); başka oturumların kirli dosyalarını stage etme.

## 15. Açık sorular (Codex karar vermez, ILERLEME'de Enes'e sorar)

- Stant günü fiziksel alan: 5 kişi için 3.5 m genişlik ve 3–3.5 m derinlik var mı?
- Yerde bant çizgisi (oyun alanı sınırı) yapıştırılabilir mi? (Kamera dışı bir yardım ama oyunun kendisi
  yine yalnız kamerayla çalışır.)
- Hoca belirli bir soru süresi ya da puanlama istiyor mu? Varsayılan: 5 soru, süreye göre puan.
