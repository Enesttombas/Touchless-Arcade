# 00. Donanım, görüntü yayını ve kamera hattı (P0)

> **Enes kararı (2026-10-12):** Ethernet kablosu sağlanacak (Çözüm A uygulanır). Ayrı USB webcam
> yok; kamera **HP'nin kendi kamerası** (Çözüm B zorunlu, Çözüm C kapsam dışı).

## Sorun

- Stant ekranı **HP ProOne 440 G3** All-in-One. Resmi QuickSpecs arka port listesinde HDMI için
  **"HDMI out"** yazıyor (kaynak: HP QuickSpecs, ProOne 440/490 G3 23.8"). Bu cihazda görüntü girişi
  yok; HDMI ile monitör olarak kullanılamaz. Bağlanamamanın sebebi bir güvenlik önlemi değil, donanım.
  (Video girişi yeni nesilde var: ProOne 440 **G9**'da "HDMI-in / Monitor Mode". G3'te yok.)
- Aynı belgede: **Gigabit Ethernet** ve **1 MP (720p) HP TrueVision webcam** var.
- Bugünkü hat (2026-10-12):
  - HP kamerası → `C:\stand\kamera_yayin.py` (MJPEG HTTP :8090, 640x480 @ ~15 FPS, 720p'de ~10 FPS)
    → telefon hotspot'u → laptopta algılama ve çizim.
  - Laptop → Sunshine → hotspot → HP'de Moonlight (720p, 30 FPS, 6 Mbps).
  - Görüntü iki kez telefon üzerinden kablosuz gidiyor. Kamera düşük FPS'te. Sonuç: gecikme, takılma, bulanıklık.
- Laptopta Gigabit Ethernet var (Realtek Gaming GbE, şu an bağlı değil). Laptopta sanal ekran sürücüleri
  de var (SudoMaker / Parsec Virtual Display Adapter).

## Çözüm A (önerilen): laptop ile HP arasında doğrudan Ethernet kablosu

Tek bir Cat5e/Cat6 kablo laptopu doğrudan HP'ye bağlar; router gerekmez (her iki kart da otomatik
çapraz bağlantı yapar). İnternet gerekiyorsa laptop Wi-Fi'da kalır, kablo yalnız stant içi trafiği taşır.

Yapılacaklar (Codex komut ve betik hazırlar, kurulumu Enes yapar):

1. Statik IP adresi ver. Laptop Ethernet `192.168.77.1/24`, HP `192.168.77.2/24`; ağ geçidi boş kalır.
   Ağ profilini Private yap. `kurulum/ag_kur_laptop.ps1` ve `kurulum/ag_kur_hp.cmd` yaz. HP'de
   PowerShell açılmıyor, o yüzden `netsh` ile cmd betiği.
2. Güvenlik duvarı. Laptopta güvenlik duvarı şu an üç profilde de kapalı; bu bir açık. Betik açsın ve
   yalnız bu alt ağdan şunlara izin versin: Sunshine (TCP 47984, 47989, 47990, 48010; UDP 47998–48000,
   48002, 48010) ve kamera köprüsü (TCP/UDP 8090).
3. Sunshine (laptop): NVENC, düşük gecikme ön ayarı, B-frame kapalı. Uygulamayı **sanal ekranda**
   aç: SudoMaker sanal ekranı 1920x1080 @ 60 Hz. Sunshine o ekranı yayınlar, laptop ekranı
   operatöre kalır.
4. Moonlight (HP): 1080p, 60 FPS, 20 Mbps, H.264 (HD 630 donanımla çözer), V-Sync kapalı.
   Komut: `Moonlight.exe stream 192.168.77.1 Desktop --resolution 1920x1080 --fps 60 --bitrate 20000 --video-codec H.264`.
   Komut satırı bayrakları kurulu sürümde farklıysa `Moonlight.exe --help` çıktısına göre düzelt.
5. Beklenti: ağ katkısı 1 ms'nin altına iner, kablosuz takılmalar biter. Sunshine/Moonlight
   kodlama + çözme gecikmesi kablolu ağda tipik olarak tek haneli-iki haneli ms'dir (kaynak:
   `ARASTIRMA-KAYNAKLAR.md`). Doğru sayı §Ölçüm ile alınır.

## Çözüm B: HP kamerasını hızlandır ve "en son kare" köprüsüne geç

HP kamerası kullanılmak zorunda. Bugünkü HTTP MJPEG akışı arabelleğe kare biriktirebilir; bu
gecikmeyi büyütür. Hedef: 640x480 ya da 960x540 @ 30 FPS, uçtan uca kamera katkısı ≤ 60 ms.

1. **Kamera ayarı:** DirectShow'da `CAP_PROP_FOURCC = MJPG` iste. Ardından 640x480 ve 1280x720 için
   30 FPS dene. Düşük ışıkta webcam'ler otomatik pozlamayla FPS düşürür; bugünkü 10–15 FPS'in sebebi
   bu olabilir. `kamera_kopru.py --tara` şunları ölçüp tablo yazar:
   - desteklenen çözünürlük / FPS / FOURCC,
   - `CAP_PROP_AUTO_EXPOSURE` ve `CAP_PROP_EXPOSURE` ile manuel pozlamada gerçek FPS.
   Stanta küçük bir halka ışık önerisini sonuçla birlikte Enes'e yaz.
2. **Köprü** `prototipler/kamera_kopru.py` (tek dosya, iki rol):
   - `--gonder` (HP'de): kamerayı okur, JPEG (kalite 80) yapar. Kare numarası ve gönderim zamanıyla
     TCP üzerinden gönderir (uzunluk önekli çerçeve). **Kuyruk tutmaz**: alıcı yetişemiyorsa eski kareyi atar.
   - `AgKamera(adres)` (laptopta): `stand.Kamera` ile aynı arayüz (`kare`, `t_son`, `kapat()`, iş
     parçacığı). Yalnız en son kareyi tutar. `KAMERA=tcp://192.168.77.2:8090` ile seçilir;
     `KAMERA=0/1/http://` davranışı aynen kalır.
   - Saat farkı: bağlantı başında 10 ping-pong ile ofset ve RTT ölçülür. Her karenin "çekim → laptop"
     gecikmesi `olcum.py` kaydına yazılır.
   - Bağlantı koparsa 1 sn'de bir yeniden bağlanır; uygulama çökmez, ekranda "Kamera bekleniyor" yazar.
3. HP'de köprüyü masaüstü oturumunda başlat. Daha önce ölçülen tuzak: SSH oturumunda başlatılan
   süreç oturum düşünce ölüyor; `schtasks /it` kalıbını kullan. Bir de `Stant-HP.bat` yaz:
   köprüyü ve Moonlight'ı sırayla açsın.

## Çözüm C (kapsam dışı, Enes 2026-10-12: kamera HP'nin kendisi): USB webcam

- 60 FPS verebilen bir USB webcam (720p60 sınıfı) HP'nin üst kenarına takılır. Bakış açısı HP
  kamerasıyla aynı olur. USB kablosu laptopa gider; 3 m üstünde aktif uzatma gerekir.
- Kamera ağ hattı tamamen kalkar. Kamera katkısı yaklaşık 33 ms'den 17 ms'ye iner, kare başına hareket bulanıklığı azalır.
- Parmak hassasiyeti isteyen oyunlar (04 Neon Tel, 05 Parmak Kuşu, 06 Neon Koşu parmak modu) bundan
  en çok kazanır. Şu an uygulanmaz. HP kamerasında 30 FPS çıkmazsa bu ölçümle birlikte Enes'e yeniden önerilir.
  Yazılım tarafında `KAMERA=<indeks>` zaten yeterli.

## Elenen seçenekler (neden)

| Seçenek | Neden değil |
|---|---|
| HDMI ile HP'ye bağlamak | 440 G3'te HDMI yalnız çıkış |
| USB HDMI yakalama kartı + HP'de tam ekran görüntüleyici | Ucuz kartlar MJPEG sıkıştırır, gecikme ekler; kablolu Moonlight'tan iyi değil |
| Miracast / kablosuz ekran | Bugünkü sorunun aynısı |
| Her şeyi HP'de koşmak | i5-7500T, GPU yok; yüz + el + segmentasyon birlikte yetmez. Yalnız acil durum "hafif mod" olabilir (yalnız yüz, 640x360) |
| Organizasyondan HDMI girişli TV/monitör istemek | **Sorulmaya değer**: bulunursa laptop → HDMI en iyisi (ekran gecikmesi ≈ 0). Kamera yine HP'nin ya da USB'nin olur |

## Ölçüm (zorunlu, gecikme iddiası buna dayanır)

1. **Yazılım içi aşama zamanları** (`olcum.py`, 01 §1): HP çekim → laptop alış → algı bitti →
   çizim bitti → `imshow`. Ekranda `B` tuşuyla açılan "Bilim Modu" katmanında ve CSV'de görünür.
2. **Camdan cama (glass-to-glass) toplam gecikme.** Telefonun ağır çekim videosu (240 FPS) hem
   gerçek eli hem HP ekranını aynı kadrajda çeker. El hızla aşağı iner, ekrandaki el iner. İki an
   arasındaki kare sayısı / 240 = toplam gecikme. Her hat (bugünkü hotspot, Ethernet, USB kamera)
   için 5 deneme yapılır, medyanı `ILERLEME.md`'ye yazılır. Prosedürü `codex/OLCUM-PROTOKOLU.md`
   olarak tek sayfa yaz.

## Kabul

- `kamera_kopru.py` için pytest (yerel döngü, gerçek kamera yok): sahte kare üreten gönderici
  `127.0.0.1` portuna 100 kare yollar, alıcı yavaş tüketir. Şunlar doğrulanır:
  (a) alıcının elindeki kare hep en yenisi (kare no artıyor, ara kareler atlanabiliyor),
  (b) bağlantı kesilip yeniden açılınca alıcı 2 sn içinde kare almaya devam ediyor,
  (c) `AgKamera` arayüzü `stand.Kamera` ile aynı.
  En az 3 test.
- Ağ kurulum betikleri yazıldı. Enes kablo takıp çalıştırınca camdan cama ölçüm tablosu
  `ILERLEME.md`'de yer alıyor. Betikleri Codex çalıştırmaz, Enes çalıştırır: ağ ve güvenlik duvarı
  ayarı sistem ayarıdır.
