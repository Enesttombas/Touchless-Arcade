# Değişiklikler

## v0.4.1 (2026-10-15)

- **Ses kaldırıldı:** Oyunda hiç ses yok. Ses sentezi, meme mp3'leri ve ses kütüphaneleri (`pygame-ce`, `sounddevice`) kaldırıldı; indirme paketi küçüldü.
- **Kısayol şeridi:** Oyun ekranının sol altında göze batmayan küçük bir şerit hep duruyor: `[F] tam ekran`, `[M] menü`.

## v0.4.0 (2026-10-15)

- **Tek tık kurulum:** Python kurmak gerekmiyor. `BASLAT.bat` ilk açılışta oyunun kendi taşınabilir Python'unu ve paketlerini `app\python` içine kurar.
- README'nin en üstüne **İndir** düğmesi eklendi; kurulum 3 adıma indi.
- **Hazır Windows paketi:** GitHub her `master` güncellemesinde taşınabilir Python ve tüm paketler dahil hazır ZIP'i kendisi üretip "windows" sürümüne koyar. İndir düğmesi bu ZIP'i gösterir; ilk açılışta hiçbir şey indirilmez.
- CI'da bu kurulumu sıfırdan deneyen bir Windows işi eklendi.

## v0.3.1 (2026-10-15)

- README'ye stantta gerçek oyuncularla çekilmiş canlı klipler eklendi (Neon Kılıç, Gülme Düellosu, Kanat Rotası) ve bir AR Maskeler fotoğrafı.

## v0.3.0 (2026-10-15)

**Düzeltmeler**
- **Çizim Kâhini:** Canlı kamerada çizim çıkmıyordu.
  - El bir an kaybolup geri gelince takipçi ona yeni bir kimlik veriyordu; oyun bu eli tanımıyor, tur donuyordu. Artık oyuncu dönen elle devam eder.
  - Kameraya doğru uzatılan parmak "bükülü" sayılıyordu. Artık parmak uzunluğu 3B (derinlik dahil) ölçülüyor.
  - Yüzden uzak tutulan el artık reddedilmiyor.
- **Altın Vuruş:** Oynaması çok zordu ve top bazen iki kez gidiyordu.
  - Topu yakalamak için parmak ucunu topun yakınında kısa süre tutmak yetiyor.
  - Hızlı fiske de şut sayılıyor. Tek hareket her zaman tek şut olur.
  - Yol çizdiğin nokta, topun gittiği yerdir.
  - Yeni neon sanal kaleci: bekler, yalandan ters tarafa yatar, köşeye uçar, yere düşer. Kurtarışlar çizilen eldivenlerden hesaplanır; 200 rastgele şutta kurtarış oranı %20–40.

**Sadeleştirme**
- Bütün oyunlar tek ekranda; sayfa geçişi kaldırıldı.
- İşlem Dizisi ve Cümle Dizisi oyunları kaldırıldı.
- Taş Kağıt Makas menüde soluk ve devre dışı bir kart olarak duruyor.
- Kurulum tek dosya: `BASLAT.bat` ilk açılışta kendini kurar.
- Klasörler `oyunlar/` ve `tests/` olarak sadeleşti. Kullanılmayan prototipler, iç planlama notları ve stant ağ betikleri kaldırıldı.
- Linux ve macOS'ta Türkçe karakterler için yedek font eklendi.

## v0.2.0 (2026-10-15)

- Menü kartlarına giriş animasyonu, seçim halkası ve ilerleme çubuğu eklendi.
- `REDUCED_MOTION=1` ile dekoratif hareketler kapatılabiliyor.
- Kamera gerektirmeyen önizleme aracı eklendi (`tools/render_preview.py`); README görselleri bununla üretiliyor.
- Model lisansları ve SHA256 özetleri `THIRD_PARTY_NOTICES.md`'ye eklendi.

## v0.1.0 (2026-10-13)

- İlk sürüm: tek pencerede dokunmadan seçilen kamera oyunları, boşta menüye dönüş, çökme yalıtımı ve kabul testleri.
