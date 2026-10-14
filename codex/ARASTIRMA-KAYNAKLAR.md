# Araştırma özeti ve kaynaklar (başvuru)

Ham raporlar (Gemini işçi, 2026-10-12):
- `arastirma-yeni-oyunlar/teknik/rapor.md` ve `rapor-k2.md`: gecikme, filtre, GPU, 3B, segmentasyon, Quick Draw.
- `arastirma-yeni-oyunlar/oyunlar/rapor.md`: Kinect/EyeToy/Nex, sanat enstalasyonları, stant ilkeleri.

İşçi raporlarındaki sayılar kanıt değildir. Aşağıda her iddia üç sınıftan birine konur:
- **[YEREL]** bu makinede komutla doğrulandı,
- **[KAYNAK]** Opus kaynağı açıp okudu,
- **[ÖLÇ]** doğrulanmadı, Codex ölçmeden tasarım kararına dayanak yapmaz.

## 1. Donanım ve yayın (00)

| İddia | Sınıf | Kaynak |
|---|---|---|
| HP ProOne 440 G3'teki HDMI portu **yalnız çıkış**; görüntü girişi yok | [KAYNAK] | [HP 440 G3 ürün föyü (Dustin)](https://media.dustin.eu/media/d200001001602615/proone-440-g3-aio-product-data-sheet-brochure.pdf), [HP QuickSpecs c08017709](https://h20195.www2.hp.com/v2/GetDocument.aspx?docname=c08017709), [Alza ürün sayfası](https://www.alza.cz/EN/hp-proone-440-23-8-g3-d5114476.htm) |
| Yeni nesil 440 G9'da HDMI **girişi** var (yani G3'te yokluk tasarım gereği, güvenlik kilidi değil) | [KAYNAK] | [HP ProOne 440 G9 föyü](https://www.copiadorasinnovadas.es/wp-content/uploads/2023/03/HP-ProOne-440-G9.pdf) |
| 440 G3: Gigabit Ethernet, 1 MP webcam, i5-7500T, ayrık GPU yok | [KAYNAK] | aynı föyler; HP forumları (h30434.www3.hp.com) |
| Laptopta Realtek GbE, SudoMaker ve Parsec sanal ekran sürücüleri var | [YEREL] | aygıt listesi |
| Sunshine/Moonlight akış ek gecikmesi kablolu ağda birkaç ms | [ÖLÇ] | [Sunshine](https://github.com/LizardByte/Sunshine), [Moonlight docs](https://github.com/moonlight-stream/moonlight-docs). İşçi raporundaki "uçtan uca 42–60 ms" tablosu ölçüm değil, tahmin |
| 60 FPS USB kamera + `CAP_PROP_BUFFERSIZE=1` + iş parçacıklı okuma, tampon birikmesini önler | [ÖLÇ] | OpenCV VideoCapture belgeleri. Değerler kameraya göre değişir |

## 2. Algı ve GPU (01, 02)

| İddia | Sınıf | Not |
|---|---|---|
| MediaPipe Tasks Python, Windows'ta GPU delegate desteklemiyor (`NotImplementedError`) | [YEREL] + [KAYNAK] | face_landmarker ile denendi. [mediapipe #5126](https://github.com/google-ai-edge/mediapipe/issues/5126) |
| torch 2.6.0+cu124 CUDA çalışıyor (RTX 4080 Laptop) | [YEREL] | `torch.cuda.is_available()` → True |
| onnxruntime 1.30.0 kurulumunda CUDA sağlayıcısı yok | [YEREL] | yalnız CPU + Azure |
| `cv2.ximgproc.guidedFilter` mevcut | [YEREL] | |
| FaceLandmarker `output_facial_transformation_matrixes` ile 4x4 dönüşüm verir | [KAYNAK] | [Face landmarker Python kılavuzu](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python) |
| `selfie_multiclass_256x256` 6 sınıf: arka plan, saç, beden derisi, yüz derisi, kıyafet, diğer | [KAYNAK] | [Image segmenter](https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter) |
| `num_poses > 1` pratikte kararsız, üst üste binen kişiyi kaybediyor | [ÖLÇ] | İşçi raporu GitHub kayıtlarına dayandırıyor (#5274, #5842); bizim kodda `num_poses=3` çalışıyor, kalabalıkta ölç |
| El takibi i9'da ~15–25 ms | [ÖLÇ] | [Hand landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) resmi sayı Pixel 6 içindir |
| Depth Anything V2 Small, RTX'te ONNX CUDA ~13–20 ms | [ÖLÇ] | [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2), [arXiv 2406.09414](https://arxiv.org/abs/2406.09414) yalnız V100/A100 sayısı verir. Laptop sayısı tahmin |
| ByteTrack iki aşamalı eşleştirme | [KAYNAK] | [arXiv 2110.06864](https://arxiv.org/abs/2110.06864). Bizde gereksiz; Hungarian yeterli (01 §4) |
| ModernGL bağımsız bağlam + FBO `read_into` | [KAYNAK] | [ModernGL belgeleri](https://moderngl.readthedocs.io/) |
| Guided filter (He & Sun) | [KAYNAK] | [Fast Guided Filter arXiv 1505.00996](https://arxiv.org/abs/1505.00996) |

## 3. Filtre ve gecikme (01 §3, 04)

- **One Euro Filter** (Casiez, Roussel, Vogel, CHI 2012): kesim frekansı hızla artar, yavaşta titreşimi
  keser, hızlıda gecikmeyi azaltır. Başlangıç: normalize koordinatlarda `min_cutoff` 0.5–1.0 Hz, `beta`
  0.005–0.05, `d_cutoff` 1.0. Kesin değer `olcum.py --titresim` ile kalibre edilir.
  [Resmi sayfa](https://gery.casiez.net/1euro/), [DOI 10.1145/2207676.2208639](https://doi.org/10.1145/2207676.2208639). [KAYNAK]
- **Öngörü sınırı:** filtre gecikmeyi geri saramaz. Doğrusal öngörü köşelerde aşırı fırlatır (overshoot).
  Ufuk ≤ 0.05–0.08 sn, tavanlı. İki rapor da aynı yönde. [ÖLÇ: bizim hatta en iyi τ]
- **Kaydırmalı çarpışma (CCD):** kareler arası hareket parçası boyunca çarpışma testi. Hızlı hareket
  duvarı atlayamaz. Standart oyun fiziği tekniği, 04'te `distanceTransform` ile.

## 4. Oyun ve deneyim referansları (03–09)

Oyunlar raporundaki bağlantıların çoğu **ana sayfa** (gamingbolt.com, gamedeveloper.com, github.com).
Yani iddia ile kaynak sayfası arasında bağ zayıf. Aşağıdakiler genel bilinen olgulardır. Tasarıma ilham
verir, sayı kaynağı değildir.

| Referans | Ne aldık | Kaynak |
|---|---|---|
| Kinect *Hole in the Wall* (2011) | 08-C Duvardaki Delik | oyunlar raporu (zayıf kaynak) |
| Kinect *Adventures!* Reflex Ridge (eğil-zıpla engelleri) | 06 beden modu | oyunlar raporu (zayıf kaynak) |
| Sony EyeToy (2003), kare farkı ile hareket | 08-D'de kare farkı **kullanılmaz** (kalabalık sorunu) | oyunlar raporu (zayıf kaynak) |
| Camille Utterback & Romy Achituv, *Text Rain* (1999) | 03 yanlış cevap efekti, 09-5 bekleme ekranı | [SAAM](https://americanart.si.edu/). Raporda eser sayfası 404, sanatçı sayfası 429 döndü |
| Johnny Chung Lee, Wii Remote kafa takipli ekran (2007) | 09-1 Sihirli Pencere | [IEEE Pervasive Computing 2008](https://ieeexplore.ieee.org/document/4570188). Proje sayfası raporda 503 |
| Kooima, *Generalized Perspective Projection* | 09-1 asimetrik frustum matematiği | Bilinen teknik not; bu çalışmada açılmadı |
| Jos Stam, *Stable Fluids* (SIGGRAPH 1999) | 09-3 Sıvı Ayna | Bilinen makale; bu çalışmada açılmadı |
| Google *Quick, Draw!* + Sketch-RNN (Ha & Eck) | 07 | [Veri seti](https://github.com/googlecreativelab/quickdraw-dataset), [arXiv 1704.03477](https://arxiv.org/abs/1704.03477) |
| Göz kırpma EAR (Soukupová & Čech 2016) | Gülme oyunundaki Göz Kırpma modu (var) | [CVWW 2016](https://api.semanticscholar.org/CorpusID:21124316) |
| Stant ilkeleri: tur 45–90 sn, 5 sn'de anlaşılır kural, saatlik sıfırlanan skor tablosu | README akış kuralı, 03/08 skor | [workinman.com](https://www.workinman.com) (pazarlama kaynağı, zayıf) |

## 5. Quick, Draw! veri erişimi (07)

- 28x28 bitmap dosyaları: `https://storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap/<kategori>.npy`.
  Örnek: `cat.npy` 96.6 MB. [KAYNAK: veri seti deposu ve HEAD isteği]
- 30 kategorinin tamamı ~2–3 GB eder. Kategori başına 20k örnek yeterli. `.npy` başlığı okunup HTTP
  Range ile yalnız ilk N satır indirilebilir. Codex bunu denemeden önce Enes'ten onay alır.
- Lisans: veri seti CC BY 4.0 (depo README'sinde). Atıf `ciz_egit.py` başına yazılır.
- `zarqankhn/quickdraw-345-tflite` (HF): raporda %76 Top-1 deniyor. [ÖLÇ] Doğrulanmadı ve kullanılmıyor,
  kendi 25–40 sınıflık modelimizi eğitiyoruz.
