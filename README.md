# Touchless Arcade — Stant Kamera Oyunları

[![CI](https://github.com/Enesttombas/Touchless-Arcade/actions/workflows/ci.yml/badge.svg)](https://github.com/Enesttombas/Touchless-Arcade/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3119/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Dokunmadan oynanan kamera oyunları.** Ziyaretçi ekranın karşısına geçer; eliyle, yüzüyle ve bedeniyle oynar. Kumanda, dokunmatik ekran ya da kurulum gerekmez. Üniversite ve kulüp stantları için yapıldı.

*Touch-free camera arcade for booths and events: just stand in front of the screen and play with your hands, face and body.* [English ↓](#english)

## Stantta canlı

<div align="center">

<a href="docs/media/canli/neon-kilic.mp4"><img src="docs/media/canli/neon-kilic.gif" alt="Neon Kılıç, iki oyuncu" width="640"/></a>

**Neon Kılıç**: iki oyuncu birlikte dilimliyor. Tur başında **Meyve** ya da **Meme** modu seçilir; bu klip Meme modundan.

<a href="docs/media/canli/gulme-duellosu.mp4"><img src="docs/media/canli/gulme-duellosu.gif" alt="Gülme Düellosu" width="600"/></a>

**Gülme Düellosu**: iki kişi bakışır, ilk gülen kaybeder.

<a href="docs/media/canli/kanat-rotasi.mp4"><img src="docs/media/canli/kanat-rotasi.gif" alt="Kanat Rotası" height="560"/></a>

**Kanat Rotası**: kuşu parmağınla uçur.

<img src="docs/media/canli/ar-maskeler.jpg" alt="AR Maskeler, dört kişi aynı anda" width="640"/>

**AR Maskeler**: kadrajdaki herkes kendi maskesini seçiyor.

</div>

<sub>Üniversite stantında gerçek oyunculardan kayıtlar. Tam videoyu açmak için önizlemeye tıkla.</sub>

## Ekran görüntüleri

<div align="center">
  <img src="docs/media/menu.png" alt="Ana menü" width="720"/>
  <br/>
  <img src="docs/media/demo.gif" alt="Oyunlardan kısa demo" width="600"/>
  <p><sub>Görseller oyunun kendi render motoruyla sentetik verilerle üretildi; canlı kamera kaydı değildir.</sub></p>
</div>

## Oyunlar

| | Oyun | Nasıl oynanır |
|---|---|---|
| 1 | **Neon Kılıç** | İşaret parmağın kılıç olur; **Meyve** ya da **Meme** modunda uçuşanları dilimle. |
| 2 | **Gülme Düellosu** | İki kişi karşı karşıya: ilk gülen ya da göz kırpan kaybeder. |
| 3 | **AR Maskeler** | Yüzüne gerçek zamanlı 3B maskeler ve filtreler. |
| 4 | **Kanat Rotası** | Parmağının yüksekliğiyle kuşu boruların arasından geçir. |
| 5 | **Bilgi Yağmuru** | Düşen doğru cevabın altına bedeninle koş. |
| 6 | **Silahşor Düellosu** | "ATEŞ!" yazınca elini en hızlı kaldıran kazanır. |
| 7 | **Hayalet Klonlar** | Zaman klonların ve görünmezlik pelerini. |
| 8 | **Altın Vuruş** | Parmağını topa koy, kalede nişan aldığın yere yol çiz. Neon kaleci yalandan yatıp köşeye uçar. |
| 9 | **Çizim Kâhini** | Havada çiz; yapay zekâ ne çizdiğini tahmin etsin. |

*Taş Kağıt Makas* menüde soluk ve devre dışı bir kart olarak durur.

## Kurulum ve çalıştırma

1. [Python 3.11](https://www.python.org/downloads/release/python-3119/)'i kur. Kurulumda **"Add python.exe to PATH"** kutusunu işaretle.
2. Bu depoyu indir (**Code → Download ZIP**) ve klasörü aç.
3. **`BASLAT.bat`**'a çift tıkla.

İlk açılışta gerekli paketleri kendisi kurar; bu birkaç dakika sürer. Sonraki açılışlar anında başlar. Bir USB ya da dahili kamera yeterlidir.

## Kontroller

Kameranın parmağını en iyi algılaması için **işaret parmağını yukarı kaldır, avuç içini kameraya dön**, diğer parmakları kapat. Parmak ucunu doğrudan kameraya uzatırsan kamera parmağı kısaltılmış görür ve takip kopabilir.

<div align="center"><img src="docs/media/parmak-durusu.gif" alt="Doğru parmak duruşu: işaret parmağı yukarı, avuç kameraya" width="600"/></div>


| Ne | Hareketle | Klavyeyle |
|---|---|---|
| Oyun seç | Elini kartın üstünde 1 sn tut | `1`–`9` |
| Menüye dön | Sol alt köşede avucunu 3 sn aç | `M` |
| Tam ekran / çıkış | | `F` / `Q` |

## Nasıl çalışıyor?

- Yüz, el ve beden takibi: **Google MediaPipe**. Çizim tanıma: **Quick, Draw!** verisiyle eğitilmiş küçük bir **ONNX** ağı. Görüntü işleme: **OpenCV**.
- Her şey bilgisayarda yerel çalışır. Kamera görüntüsü yalnız bellekte işlenir; diske yazılmaz, internete gönderilmez.
- Ayrıntılar: [mimari](docs/architecture.md) · [sorun giderme](docs/troubleshooting.md) · [lisanslar](THIRD_PARTY_NOTICES.md) · [değişiklikler](CHANGELOG.md)

## Geliştirme

```cmd
app\.venv\Scripts\python.exe -m pytest -q tests
app\.venv\Scripts\python.exe tools\render_preview.py --quick
```

Kodun yapısı: `oyunlar/` (oyunlar ve menü), `stand/` (ortak çizim/efekt kütüphanesi), `app/modeller/` (MediaPipe modelleri), `tests/`.

---

<a name="english"></a>
## English

**Stant Kamera Oyunları** is a collection of 9 touch-free arcade games for exhibition booths. Visitors play with their hands, face and body in front of a mirrored live camera. No controller, touch screen or sign-up is needed.

**Run it on Windows:**
1. Install [Python 3.11](https://www.python.org/downloads/release/python-3119/) and tick **"Add python.exe to PATH"**.
2. Download this repository (**Code → Download ZIP**).
3. Double-click **`BASLAT.bat`**. The first run installs the dependencies; later runs start instantly.

**Controls:** raise your index finger with the palm facing the camera (don't point the fingertip straight at the lens). Hold your hand over a card for 1 s to pick a game. Hold an open palm in the bottom-left corner for 3 s to return to the menu. Keyboard: `1`–`9` select, `M` menu, `F` fullscreen, `Q` quit.

**Live demos:** see the clips under *Stantta canlı* above, recorded with real players at a university booth.

**Tech:** MediaPipe (face, hands, pose), OpenCV, ONNX Runtime (a Quick, Draw! sketch classifier) and pygame-ce audio. Everything runs locally on the CPU, and camera frames never leave memory.

## Lisans

[MIT](LICENSE). Üçüncü taraf modellerin lisansları: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
