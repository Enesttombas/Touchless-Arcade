# 02. AR kalitesi: daha iyi insan analizi, 3B/"4D" efektler, GPU cila (P1)

Enes'in isteği: "AR alanına çok daha optimize, çok daha iyi insan analiz edebilmesi, efektlerin çok daha
4D ve kaliteli olması." Bu dosya oyunların ortak görsel ve algı katmanını yükseltir. Oyun dosyaları bu
katmanı çağırır, kendi kopyalarını yazmaz.

## Yerelde doğrulanan durum (2026-10-12, `app/.venv`)

| Olgu | Sonuç | Sonuç doğuran komut |
|---|---|---|
| MediaPipe Tasks GPU delegate (Windows) | **Yok**: `Delegate.GPU` ile `NotImplementedError` | face_landmarker ile deneme |
| torch CUDA | **Var**: `True, NVIDIA GeForce RTX 4080 Laptop GPU` | `torch.cuda.is_available()` |
| onnxruntime sağlayıcıları | **Yalnız CPU**: `['AzureExecutionProvider', 'CPUExecutionProvider']` | `onnxruntime.get_available_providers()` |
| `cv2.ximgproc` (guided filter) | **Var** | `hasattr(cv2, 'ximgproc')` |
| moderngl / glfw | **Kurulu değil** | `importlib.util.find_spec` |
| Segmentasyon modeli | Yalnız `pose_landmarker_lite.task` maskesi (`Maskeci`, ~37 ms, arka planda). `selfie_multiclass` dosyası **yok** | `ls app/modeller` |

Sonuç: GPU'ya giden yol ya **torch CUDA** (zaten çalışıyor) ya da `onnxruntime-gpu` kurulumu.
`onnxruntime-gpu` kurulursa CPU paketiyle çakışır. Önce kaldır, sonra kur, sürümü sabitle ve CUDA
sağlayıcısının listede çıktığını göster. İkisinden hangisi seçilirse seçilsin `ILERLEME.md`'ye yaz.

## §1 İnsan analizi: "kim var, nerede, ne yapıyor"

Hedef: her oyun aynı soruya aynı cevabı alsın. Tek bir **Sahne** nesnesi, her karede şunu verir:
`kisiler: list[Kisi]`. `Kisi` alanları: `id`, `yuz`, `el[]`, `poz`, `maske_bolge`, `derinlik_sira`, `aktif`.
Bu, 01 §2 Oyuncu Kapısı ile 01 §4 kimlik takibinin çıktısıdır; burada yalnız üstüne eklenenler var.

1. **Ortak kişi kimliği:** yüz, el ve poz ayrı modellerden gelir. Onları tek kişiye bağla:
   - el bileği noktası ↔ poz bileği (15/16) mesafesi,
   - yüz merkezi ↔ poz burnu (0) mesafesi.
   Eşleşmeyen el "sahipsiz el" kuralına (01 §2) düşer. Bu, kalabalıkta başkasının elinin oyuncunun
   kuşunu sürmesini engeller.
2. **Derinlik sırası (kim önde):** tek kamerada mutlak derinlik yok, ama göreli sıra yeterli:
   - yüz göz arası px büyüklüğü,
   - omuz genişliği,
   - poz `z` değeri.
   Bu üçünün ağırlıklı ortalaması `derinlik_sira` verir. Oklüzyon (önde olan efektin önünde kalır)
   ve "aktif oyuncu en öndeki" kararı bunu kullanır.
3. **Daha iyi maske:**
   - Bugünkü poz maskesi tek sınıf ve kenarı titrek.
   - Seçenek A (önerilen, ucuz): mevcut maskeye **guided filter** (`cv2.ximgproc.guidedFilter`,
     rehber = gri kare, r=8, eps=1e-3) ve **zamansal EMA** (α 0.5–0.7, hareketli bölgede α yüksek) ekle.
     Saç kenarı ve titreme belirgin iyileşir, maliyet ~1–2 ms (ölç).
   - Seçenek B: MediaPipe `selfie_multiclass_256x256` modeli. Altı sınıf verir: arka plan, saç, beden derisi,
     yüz derisi, kıyafet, diğer. Kıyafet rengi değiştirme, saç efekti ve "yalnız yüzü parlat" gibi
     şeyleri mümkün kılar. Model indirme onayı verildi (Enes 2026-10-12); adres ve boyut `ILERLEME.md`'ye yazılır.
     Ayrı arka plan iş parçacığında çalışır, `Maskeci` arayüzü korunur.
4. **Poz modeli:** `lite` yetersiz kalırsa (ölç: kol hızlıyken bilek kaybı oranı) `full` dene.
   Gecikme farkını `olcum.py --kiyas` ile göster. Sadece ölçümle kazandıysa geç.
5. **Çok kişi sınırı:** MediaPipe poz en çok `num_poses` kişi verir ve kimlik tutmaz. 4+ kişide
   01 §4'teki Hungarian eşleştirme yeterli. YOLO-Pose/RTMPose gibi ağır modellere **geçme**; stant
   oyunları en çok 2–3 aktif oyuncu ister.

## §2 3B: düz çıkartma yerine sahneye oturan nesne

Bugünkü maskeler ve efektler 2B sprite: yüz döndükçe sprite dönmez, kulağın arkasına geçemez.

1. **Kafa pozu:** `FaceLandmarkerOptions(output_facial_transformation_matrixes=True)` her yüz için
   4x4 metrik dönüşüm verir. `cekirdek.Algilayici`'ya isteğe bağlı aç; yalnız gereken oyun ister
   (`IHTIYAC` içine `"yuz3b"`). Matrisi 01 §3 filtresinden geçir (konum One Euro, dönüş için
   kuaternion slerp ile yumuşatma). Yoksa gözlük titrer.
2. **Bileşim katmanı `sahne3d.py`:**
   - Tercih **ModernGL** (bağımsız GL bağlamı, FBO'ya çiz, `read_into` ile önceden ayrılmış tampona oku).
     Kurulum gerekir (`pip install moderngl`, sürümü sabitle).
   - **Oklüzyon:** önce kanonik yüz örgüsü yalnız derinliğe çizilir (`color_mask=False`). Sonra 3B
     nesne (gözlük, şapka, boynuz) çizilir. Kafanın arkasında kalan kısım görünmez. Gerçekçiliğin
     en büyük sıçraması bu.
   - Nesneler: `.obj` ya da prosedürel (torus, koni, şerit). İlk sürümde dış varlık indirme yok.
   - **Işık uyumu:** kameranın ortalama parlaklığı ve renk sıcaklığı (yüz bölgesinin ortalama BGR'si)
     nesnenin ortam ışığına verilir. Karanlık stantta nesne parlamaz, oturur.
   - **Yedek:** GL bağlamı açılmazsa (HP'de ya da sürücü sorununda) 2B sprite yoluna döner; oyun çökmez.
3. **CPU yolu korunur:** `sahne3d` yoksa her oyun bugünkü gibi çalışır. Testler GL'siz koşar.

## §3 "4D" ne demek (benim yorumum)

"4D" sinema anlamında: 3B + **zaman** + **bedene tepki**. Somut olarak:
- **Fizikli ikincil hareket:** şapka püskülü, saç tutamı, kuyruk ve kulak yay-sönüm zinciriyle
  kafayı gecikmeli izler (Verlet, 3–6 düğüm). Kafa durunca sallanmaya devam eder. Ucuz ve çok canlı.
- **Bedenle etkileşen parçacıklar:** parçacıklar maskeye çarpar, omuzda birikir, el geçince dağılır
  (Text Rain fikri, `ARASTIRMA-KAYNAKLAR.md`). Maske mesafe alanı (`distanceTransform`, yarım çözünürlük)
  her karede bir kez hesaplanır, bütün parçacıklar O(1) okur.
- **Derinlik katmanı:** efekt kişinin hem önünde hem arkasında olabilir. Halka gövdenin arkasından
  geçip önüne döner: arka yarı maskenin altına, ön yarı üstüne çizilir. 2B'de bile 3B hissi verir.
- **Zaman efektleri:** yankı izi (son N maskeli kare, solan renkle), ağır çekim anı (kilit/vuruş
  anında 0.4 sn yavaşlatma, 03'te kullanılıyor), zaman donması (Zaman Klonları zaten yapıyor).
- **Ses:** olay sesleri konuma göre sol/sağ kanala dağıtılır (`Ses` sınıfına pan ekle).

## §4 Görsel cila (GPU varsa GPU'da, yoksa CPU'da yarım çözünürlükte)

- **Bloom:** parlak neon katmanı ayrı çizilir, yarım ve çeyrek çözünürlükte bulanıklaştırılıp eklenir.
  Bugünkü `parilti` her nesne için ayrı blur yapıyorsa tek geçişe topla (01 §5 yavaşlık adayıyla birlikte).
- **Renk derecelendirme:** oyun başına 3B LUT (koyu-mavi neon, sıcak sonuç ekranı). LUT 17³, numpy ile
  `cv2.LUT` kanal başına ya da GL'de doku.
- **Vinyet + film greni + hafif kromatik sapma:** yalnız arka plan kamerasına, UI'ye değil.
- **Ekran sarsıntısı ve flaş:** olay başına, genliği tavanlı, 0.25 sn.
- **Yazı:** sonuç ve skor sayıları "sayaç" animasyonuyla dolar, ölçek yayla zıplar.

## §5 Bütçe ve sıra

Sıra (her adım ölçülür, kazancı yoksa geri alınır):
1. Maske guided filter + EMA (Seçenek A).
2. Ortak kişi kimliği ve derinlik sırası (§1.1, §1.2).
3. Bloom tek geçiş + LUT + vinyet (CPU).
4. İkincil hareket (Verlet) AR Maskeler oyununda: püskül/kulak.
5. `sahne3d.py` ModernGL + oklüzyon: tek nesne (gözlük) ile kanıt, sonra genişlet.
6. (İsteğe bağlı) multiclass segmentasyon, Enes onayıyla.

Kare bütçesi README'deki gibi: `isle()` medyan ≤ 14 ms, p95 ≤ 25 ms. Bu dosyadaki her ek, `--kiyas`
çıktısında önce/sonra satırı ile gelir.

## §6 MediaPipe'ın Windows'ta GPU'suz olması: ölçülen etki ve çözüm yolu

**Ölçüm (2026-10-12, laptop CPU, 1280x720 kare, VIDEO modu, 70 kare, 3 örnek görsel):**

| Model ve ayar | Medyan ms | Not |
|---|---|---|
| Yüz (num_faces 4, blendshape) | 13–16 | ucuz, sorun değil |
| Yüz (num_faces 1) | 13 | |
| El + jest (num_hands 2) | 41–57 | el bulunsa da bulunmasa da yüksek |
| El + jest (num_hands 1) | 28–56 | el bulunduğunda yarıya iniyor |
| Poz lite (num_poses 3) | 55–61 | |
| Poz lite (num_poses 1) | 28–41 | |
| Poz lite + segmentasyon maskesi | 70–97 | **en pahalı parça** |

Okuma: algı ayrı iş parçacığında olsa bile el ve poz modelleri tek başına 30–60 ms, maske 70–97 ms.
Yani algı en iyi durumda ~15–25 Hz güncelleniyor; canlıda hissedilen gecikmenin ve "donma"nın bir
nedeni bu. `num_X` olandan büyük olunca MediaPipe eksik kişiyi aramak için **dedektörü her karede
yeniden koşuyor** (bulunan < istenen). Ölçümdeki 2–3 kişilik ayarların pahalı olması bununla uyumlu
(tahmin; dedektör süresini ayrıca ölçerek doğrula).

**Çözüm yolu (sırayla; her adım önce/sonra ölçülür):**
1. **Bedava CPU kazancı (hemen):**
   - Oyun başına `IHTIYAC`'a göre `num_hands` / `num_poses` / `num_faces` ayarla. Tek oyunculuk
     oyunda 1, düelloda 2.
   - "Ek kişi ara" işini her karede değil, 0.5 sn'de bir, ayrı bir IMAGE modu çağrısıyla yap.
   - Maske her karede gerekmiyorsa 2 karede bir güncelle; aradaki karelerde EMA ile taşı (§1.3).
   - Laptop prize takılı ve Windows güç modu "En iyi performans" olmalı. Ölçüm raporuna yaz.
2. **Maskeyi GPU'ya taşı (en büyük kazanç):** poz modelinin maskesi yerine torch CUDA'da çalışan
   bir video matting modeli. Aday: **Robust Video Matting** (RVM, MobileNetV3, GPL-3.0 lisans,
   [github.com/PeterL1n/RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting)). Zamansal
   olarak tutarlı (titremez), saç kenarı iyi. README'deki hız iddiası (eski bir GPU'da HD ~100 FPS)
   bu laptopta **ölçülmedi**. Hedef: 1280x720'de ≤ 8 ms, `downsample_ratio` 0.25–0.4. Tutarsa
   `Maskeci`'nin içi değişir, arayüzü aynı kalır; poz modeli maskesiz çalışır (70–97 → 28–60 ms).
3. **El ve poz için GPU (orta iş):** MediaPipe `.task` dosyaları içinde TFLite modelleri var (avuç
   dedektörü, el noktaları, poz dedektörü, poz noktaları). Bunların ONNX dönüşümleri hazır bulunuyor
   (PINTO_model_zoo; ya da `tf2onnx --tflite` ile kendin çevir). `onnxruntime-gpu` (CUDA) ya da
   `onnxruntime-directml` ile koş. Ancak MediaPipe'ın yaptığı ön/son işlemeyi yeniden yazman gerekir:
   anchor çözme, NMS, avuçtan ROI'ye döndürülmüş kırpma, kareler arası ROI takibi. Önce el için yap,
   kazancı ölç, sonra poz.
   - Alternatif: RTMPose/RTMW (gövde + el + yüz noktaları tek modelde, çok kişide güçlü, ONNX). Yüz
     blendshape'i vermez; yüz MediaPipe'ta kalır (zaten ucuz).
4. **Önerilmeyen yollar:**
   - WSL2 içinde Linux MediaPipe GPU: GL/EGL sürücü zinciri belirsiz, kamera ve pencere köprüsü ek iş. Denemeye değmez.
   - MediaPipe'ı Windows için GPU'lu derlemek: framework Windows'ta GPU yolunu desteklemiyor.

Kabul: §5 kare bütçesine ek olarak algı güncelleme hızı (Hz) `olcum.py`'da raporlanır. Hedef: tek
oyuncuda algı ≥ 30 Hz, maske ≥ 25 Hz.

## Kabul (`test_ar_kalite.py`, en az 8)

1. Guided filter + EMA: sahte titreyen maske (her karede ±3 px kayan kenar) çıktısında kenar
   salınımı girdinin ≤ %40'ı.
2. Ortak kimlik: sahte poz (bilek x=0.3) + iki el (x=0.31, x=0.8). Birinci el kişiye bağlanır,
   ikincisi sahipsiz kalır.
3. Derinlik sırası: göz arası daha büyük olan yüz `derinlik_sira=0`.
4. Kafa matrisi filtresi: gürültülü sabit matriste çıktı dönüşü < 1° oynar.
5. Verlet zinciri: kafa ani 100 px kayınca uç düğüm aynı karede gitmez, 1 sn içinde ±2 px'e oturur.
6. Parçacık-maske çarpışması: maskenin içine doğan parçacık bir sonraki adımda dışarı itilir.
7. `sahne3d` yoksa (import hatası taklidi) oyun 2B yoluna düşer, istisna yok.
8. Bloom/LUT açıkken 1280x720 karede ek maliyet ölçülür ve rapora yazılır (eşik: ≤ 4 ms medyan).
- GL testleri ayrı işaretle (`@pytest.mark.gl`); GL yoksa atlanır, nedeni yazılır.
