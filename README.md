# Stant Kamera Oyunları / Standalone Camera Arcade

[![CI](https://github.com/Enesttombas/stant-kamera-oyunlari/actions/workflows/ci.yml/badge.svg)](https://github.com/Enesttombas/stant-kamera-oyunlari/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3119/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Bilingual README: [Türkçe](#türkçe) | [English](#english)*

---

<div align="center">
  <img src="docs/media/menu.png" alt="Stant Kamera Oyunları Ana Menü" width="720"/>
  <p><em>Sentetik menü önizlemesi (gerçek render motoru ve yapay landmark verileriyle üretilmiştir; canlı kamera kaydı değildir).</em></p>
  <img src="docs/media/demo.gif" alt="Oyun İçi Animasyon Önizlemesi" width="600"/>
  <p><em>Sentetik oyun akışı ve geçiş demosu (11 deneyim; gerçek render motoru ve yapay hareketlerle üretilmiştir, canlı kamera kaydı değildir).</em></p>
</div>

---

<a name="türkçe"></a>
## 🇹🇷 Türkçe

Üniversite ve kulüp stantlarında ziyaretçilerin dokunmasız (touch-free), canlı aynalı kamera karşısında el ve beden hareketleriyle oynayabileceği arcade oyun koleksiyonu.

### Deneyimler ve Oyun Listesi (11 Oyun)

#### 9 Temel Oyun (9 Core Games)
1. **Neon Kılıç** (`p_neon_kilic`): İşaret parmağını kılıç gibi kullanarak ekranda uçuşan meyveleri dilimleme.
2. **Gülme Düellosu** (`p_gulmeme`): İki kişilik karşılıklı yüz mimik düellosu (gülmeme ve göz kırpmama meydan okuması).
3. **AR Maskeler** (`p_maske`): 3B yüz dönüşüm matrisleriyle gerçek zamanlı filtreler ve interaktif maskeler.
4. **Kanat Rotası / Parmak Kuşu** (`p_parmak_kusu`): İşaret parmağının dikey konumuyla boruların arasından kuşu uçurma.
5. **Bilgi Yağmuru** (`p_cevap_yagmuru`): Yukarıdan düşen doğru cevap kutusunun altına bedenle geçerek puan toplama.
6. **Silahşor Düellosu / Refleks** (`p_refleks`): İki oyuncunun 'ÇEK' sinyaliyle ellerini en hızlı şekilde doğrulttuğu kovboy düellosu.
7. **Hayalet Klonlar** (`p_hayalet_klon`): Zaman klonları ve görünmezlik pelerini efektlerinin birleşimi.
8. **Altın Vuruş / Penaltı** (`p_penalti`): Beden duruşuyla yön ve falsolu şut çekerek kaleciyi avlama.
9. **Çizim Kâhini** (`p_ciz_tahmin`): Havada parmakla çizilen nesneleri yerel Quick, Draw! ONNX sinir ağıyla tahmin etme.

#### 2 Ek Çok Oyunculu Dizi Oyunu (2 Extra Multiplayer Sequence Games)
10. **İşlem Dizisi** (`p_islem_dizisi`): 3–5 oyuncunun üzerlerindeki sayılar ve işlem kartlarıyla matematiksel eşitliği sağlamak için yer değiştirdiği takım oyunu.
11. **Cümle Dizisi** (`p_cumle_dizisi`): 3–5 oyuncunun başlarının üzerindeki kelimeleri doğru sıraya dizerek anlamlı cümle oluşturduğu işbirlikli yarışma.

### Hızlı Başlangıç (Windows)

#### Gereksinimler
- Windows 10/11 (64-bit)
- Python **3.11** (kurulum sırasında `py launcher` ve `PATH` seçili olmalıdır)
- Standart USB veya dahili RGB kamera (720p veya 1080p, 30+ FPS)

#### Kurulum
Depo kök dizininde kurulum betiğini çalıştırın (Python bağımlılıklarını indirir; depodaki model dosyalarının varlığını kontrol eder):
```cmd
KUR.bat
```

#### Başlatma
Uygulama doğrudan Python kaynak kodundan çalışır (derlenmiş EXE zorunlu değildir):
- **Kaynaktan çalıştırma**:
  ```cmd
  BASLAT.bat
  ```
  veya:
  ```cmd
  app\.venv\Scripts\python.exe prototipler\stant_app.py
  ```
- *(İsteğe bağlı)* Daha önce derlenmiş `Stant.exe` mevcutsa onunla da açılabilir.

### Kontroller

- **Menüde Seçim**: Elinizi kartın üzerinde 1 saniye tutun ya da klavyeden `1`–`9` tuşlarıyla geçerli sayfadaki kartı seçin.
- **Menüde Sayfa Değiştirme**: Ekrandaki sol/sağ butonların üstünde elinizi tutun veya `N` (Sonraki Sayfa) / `B` (Önceki Sayfa) tuşlarına basın.
- **Oyun İçinde Geçiş**: Oyun sırasında `N` (Sonraki Oyun) ve `B` (Önceki Oyun) tuşlarıyla deneyimler arasında geçiş yapabilir, `1`–`9` tuşlarıyla doğrudan ilgili oyuna atlayabilirsiniz.
- **Menüye Dönüş**: Sol alt köşeye açık avucunuzu 3 saniye tutun ya da klavyeden `M` tuşuna basın.
- **Dizi Oyunları Kontrolü**: `p_islem_dizisi` ve `p_cumle_dizisi` içinde `3`, `4`, `5` ile oyuncu sayısı, `Boşluk` ile mod değiştirilir.
- **Pencere ve Çıkış**: `F` tam ekran aç/kapat, `Q` veya `Esc` çıkış.
- **Azaltılmış Hareket (Erişilebilirlik)**: `REDUCED_MOTION=1` veya `AZ_HAREKET=1` ortam değişkeni menü kartı salınımını ve giriş kaymasını kapatır; parmak izi kuyruğunu sınırlar.

### Kamerasız Sentetik Önizleme
Canlı kamera veya donanım algılayıcıları olmadan menüyü ve 11 oyunun başlangıç/kısa sahnelerini sentetik olarak üretmek için:
```cmd
app\.venv\Scripts\python.exe tools/render_preview.py
```
*(Hızlı önizleme modu: `tools/render_preview.py --quick`)*

### Testleri Çalıştırma
```cmd
app\.venv\Scripts\python.exe -m pytest -q kabul_prototip -p no:cacheprovider
```

### Gizlilik ve Veri Güvenliği
- **Model Çıkarımı**: MediaPipe ve Quick, Draw! ONNX çıkarımları yerel CPU üzerinde gerçekleştirilir.
- **Kamera Akışı**: Standart uygulamada ziyaretçi kamera görüntüleri yalnızca anlık bellek (RAM) üzerinde işlenir ve diske veya internete yüklenmez.
- **Yerel Ağ Köprüsü (Opsiyonel)**: Stantta isteğe bağlı `kamera_kopru.py` kullanıldığında, görüntü akışı operatör tarafından yapılandırılmış yerel TCP ağı (`tcp://<IP>:<PORT>`) üzerinden aktarılır.
- **Kurulum Ağı**: `KUR.bat` ilk çalıştırmada `requirements.txt` bağımlılıklarını pip üzerinden indirir.

---

<a name="english"></a>
## 🇬🇧 English

A turnkey collection of touch-free, vision-based arcade games designed for exhibition booths and club events, powered by real-time MediaPipe and OpenCV pipelines.

### Experiences & Game Roster (11 Games)

#### 9 Core Games
1. **Neon Blade** (`p_neon_kilic`): Use your index finger as a glowing neon katana to slice flying fruits.
2. **No-Laugh Duel** (`p_gulmeme`): Head-to-head facial expression challenge tracking smiles and blink frequency.
3. **AR Masks** (`p_maske`): Real-time interactive masks rendered with 3D facial transformation matrices.
4. **Wing Route / Finger Bird** (`p_parmak_kusu`): Control bird altitude through pipe gaps with index finger positioning.
5. **Answer Shower** (`p_cevap_yagmuru`): Physical trivia game positioning your body under the correct falling answer column.
6. **Cowboy Duel / Reflex** (`p_refleks`): Quick-draw reaction duel triggered on visual draw signals.
7. **Ghost Clones** (`p_hayalet_klon`): Fusion of temporal silhouette echo clones and invisibility cloak effects.
8. **Golden Strike / Penalty** (`p_penalti`): Full-body penalty shootout with kick velocity and curve detection.
9. **Drawing Oracle** (`p_ciz_tahmin`): Air-canvas drawing with real-time classification powered by a local Quick, Draw! ONNX model.

#### 2 Extra Multiplayer Sequence Games
10. **Operation Sequence** (`p_islem_dizisi`): 3–5 players physically swap positions to satisfy arithmetic equality.
11. **Sentence Sequence** (`p_cumle_dizisi`): 3–5 players sort overhead word tokens into valid syntax sentences.

### Quick Start (Windows)

#### Prerequisites
- Windows 10/11 (64-bit)
- Python **3.11** (with `py launcher` enabled and in `PATH`)
- Standard USB or integrated webcam (720p/1080p, 30+ FPS recommended)

#### Installation
Run the installer batch file (downloads pip packages and dependencies):
```cmd
KUR.bat
```

#### Running the App
The application runs directly from Python source (standalone executable is optional):
- **Launch via source**:
  ```cmd
  BASLAT.bat
  ```
  or:
  ```cmd
  app\.venv\Scripts\python.exe prototipler\stant_app.py
  ```
- *(Optional)* If pre-compiled `Stant.exe` is present, it can be launched directly.

### Controls

- **Menu Selection**: Hold hand over card for 1.0 second, or press numbers `1`–`9` to pick the card on the **current** menu page.
- **Menu Pagination**: Hold hand over the on-screen left/right arrows, or press `N` (Next Page) / `B` (Previous Page).
- **In-Game Switching**: During gameplay, press `N` / `B` to cycle to the Next / Previous available game, or press `1`–`9` to jump to a specific game.
- **Return to Menu**: Hold open palm in the bottom-left corner for 3 seconds, or press `M`.
- **Sequence Games**: In `p_islem_dizisi` / `p_cumle_dizisi`, press `3`, `4`, `5` to adjust player count, or `Space` for mode toggle.
- **Window & Exit**: `F` toggles fullscreen; `Q` or `Esc` exits.
- **Reduced Motion (Accessibility)**: `REDUCED_MOTION=1` or `AZ_HAREKET=1` disables decorative card bobbing, entrance translation, and truncates fingertip trails.

### Synthetic Headless Preview
To generate preview assets without connecting a physical camera:
```cmd
app\.venv\Scripts\python.exe tools/render_preview.py
```
*(Quick preview subset mode: `tools/render_preview.py --quick`)*

### Running Automated Tests
```cmd
app\.venv\Scripts\python.exe -m pytest -q kabul_prototip -p no:cacheprovider
```

### Privacy, Networking & Limitations
- **Local Inference**: MediaPipe and ONNX vision inference execute entirely on the local CPU.
- **Video Privacy**: Standard booth deployment processes camera video frames exclusively in memory (RAM); no visitor video is written to disk or uploaded to remote cloud services.
- **LAN Bridge Transmission (Optional)**: If the optional `kamera_kopru.py` bridge is deployed, video frames are transmitted uncompressed over the operator's private local TCP network (`tcp://<IP>:<PORT>`).
- **Network Installation**: `KUR.bat` accesses PyPI via pip to install dependencies during initial setup.

### Documentation Links
- **Architecture**: [`docs/architecture.md`](docs/architecture.md)
- **Troubleshooting**: [`docs/troubleshooting.md`](docs/troubleshooting.md)
- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md)
- **Third-Party Model Notices & Licenses**: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
- **Hardware & Broadcast Architecture**: [`codex/00-DONANIM-VE-YAYIN.md`](codex/00-DONANIM-VE-YAYIN.md)
- **Multi-Player Measurement Protocol**: [`codex/DIZI-OLCUM.md`](codex/DIZI-OLCUM.md)
- **Security & Privacy Policy**: [`SECURITY.md`](SECURITY.md)
- **Contribution Guidelines**: [`CONTRIBUTING.md`](CONTRIBUTING.md)
