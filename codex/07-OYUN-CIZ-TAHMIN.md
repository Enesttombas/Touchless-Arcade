# 07. Çiz-Tahmin: havaya çiz, yapay zekâ ve insanlar tahmin etsin (Fikir 7)

Dosya: `prototipler/p_ciz_tahmin.py`, model: `prototipler/modeller/ciz_tanima.onnx`,
eğitim betiği: `prototipler/egitim/ciz_egit.py`, kelimeler: `prototipler/veri/ciz_kelimeler.json`.
`IHTIYAC = {"el"}`.

## Yorum: klasik Pictionary'nin stant sorunu
Çizen kişinin gizli kelimeyi görmesi gerekir ama çizen de ekrana bakıyor. Ekranı seyirci de görüyor.
Kelimeyi ekranda gösterirsen herkes görür. Bu yüzden düz "biri çizer, diğerleri tahmin eder" stantta
ek bir düzenek ister. Önerim: oyunun merkezine **yapay zekâyı** koymak (Google'ın "Quick, Draw!"
oyununun mekaniği): kişi çizerken model canlı tahmin eder ve "Bence bu… kedi!" der. Bu hem
teknik olarak etkileyici (hocaya canlı sinir ağı çıkarımı göstermek), hem de gizli kelime sorununu çözer:
kelimeyi ekranda **herkes** görür, yarış "yapay zekâya en hızlı tanıtmak" olur. İnsanlarla tahmin
modu, kartlı ayrı bir parti modu olarak kalır.

## Modlar
1. **YZ Tahmin Etsin** (varsayılan, tek kişi): ekranda kelime yazar ("BALIK", 20 sn). Kişi işaret
   parmağıyla havaya çizer. Sağ tarafta modelin en iyi 3 tahmini, güven çubuklarıyla canlı akar.
   Doğru kelime 1. sırada ve güveni ≥ 0.6 olunca "BİLDİM!" denir, kalan süre puana eklenir.
   3 kelime = 1 oyun.
2. **Düello** (iki kişi): ekran ikiye bölünür, aynı kelimeyi iki kişi çizer. Modelin önce tanıdığı kazanır.
   Gülme Düellosu'nun rekabet enerjisini taşır.
3. **Seyirci Tahmin** (parti modu, isteğe bağlı): kelime çizene gizli verilir. Seçenekler: fiziksel
   kart destesi (en sağlam) ya da operatör laptopunun ekranı. Ekranda kelime yerine "?" ve sayaç görünür.
   Seyirci bağırır. Operatör `D` (doğru) tuşuna basınca kelime açılır ve puan çizene gider. Model de
   tahmin ettiği için "yapay zekâ seyirciden önce bildi mi" yan yarışı oluşur.

## Çizim tekniği (mevcut koddan devral)
- `stand/stand.py` çizim mantığı: işaret parmağı = çiz, V = kalem kalkık, açık avuç = sil.
  01 §3 filtreli parmak ucu kullanılır. Kalem kalkık/inik ayrımı, havada çizimin en zayıf yanı.
  Önerilen ek kontrol (mod seçilebilir): **çimdik** (başparmak ucu 4 – işaret ucu 8 mesafesi el boyunun
  %25'inin altında) = kalem iniyor. Daha doğal, iki yöntemi canlı dene ve ölç.
- Çizgiler neon ışıkla çizilir (`Stant.neon`). Çizim kişinin önünde, yarı saydam karanlık panelde durur.

## Model (Codex üretir, ölçerek)
- Veri: Google Quick, Draw! veri setinin 28x28 `numpy_bitmap` sürümü (kategori başına `.npy`). Erişim ve
  lisans `ARASTIRMA-KAYNAKLAR.md`'de. **İndirme onayı verildi (Enes 2026-10-12).** İndirilen boyutu ve adresi `ILERLEME.md`'ye yaz.
- **Kategori sayısı küçük:** 25–40 kelime. Havada çizmesi kolay, Türkçe adı net olanlar seçilir:
  güneş, ev, balık, kalp, yıldız, ağaç, araba, kedi, şemsiye, saat, gözlük, bulut, elma, muz, köprü,
  dağ, çiçek, bisiklet, gitar, uçak, yılan, örümcek, dondurma, ay, şimşek, anahtar, ampul, kupa,
  makas, tavşan... `ciz_kelimeler.json` İngilizce kategori ↔ Türkçe ad eşlemesi.
- Eğitim: küçük bir CNN (3 konv. blok + 2 tam bağlı) PyTorch ile, RTX 4080'de kategori başına
  ~20k örnek. Hedef: test doğruluğu ≥ %90 (Quick, Draw! bitmap'lerinde). ONNX'e aktar,
  `onnxruntime` CPU'da çalıştır. Çıkarım < 3 ms; çizim sürerken 4 Hz tahmin yeterli.
- **Alan farkı (domain gap) kritik:** havada çizilen çizgi titrek ve kesintili, veri seti fare/dokunmatik.
  Ön işleme Quick, Draw! biçimine benzetilmeli: çizgileri kutuya sığdır, en-boy oranını koru, kenar
  boşluğu bırak, sabit kalınlıkta çiz, 28x28'e indir. Eğitimde artırma: rastgele titreşim, kalınlık
  değişimi, küçük dönme, çizgi kopukluğu. Ayrıca `--canli-test`: Codex ya da Enes 10 kelimeyi havada
  çizer, tanıma oranını `ILERLEME.md`'ye yazar. Canlı oran %70'in altındaysa önce ön işlemeyi düzelt.
- Yedek: model dosyası yoksa oyun "YZ Tahmin" modunu gizler, Seyirci modu çalışır.

## Hocaya anlatılacak an
Bilim Modu'nda (01 §1) modelin girdisi olan 28x28 görüntü köşede büyütülmüş gösterilir. Yanında
olasılık dağılımı çubukları ve "parametre sayısı / çıkarım ms" yazar. "Çizdiğin şey modele böyle
görünüyor" anı öğretici ve etkileyici.

## Kabul (`test_ciz_tahmin.py`, en az 8)
1. Ön işleme: bilinen bir çizgi listesi (kare) 28x28'e ortalanmış, kutuya sığmış, kalınlık sabit.
2. Boş çizim modele gönderilmiyor, tahmin listesi boş.
3. Model dosyası varken: veri setinden ayrılmış 200 test örneğiyle doğruluk ≥ %85 (test makinesinde
   eğitilmiş modelle; CI'da model yoksa bu test atlanır, nedeni yazılır).
4. Sahte tahmin ("doğru kelime %70") → "BİLDİM" durumu, kalan süre puana eklendi.
5. 20 sn dolunca kelime "bilinemedi" ile geçer.
6. V jesti kalemi kaldırır: o sırada parmak hareketi çizgi eklemez. Avuç siler.
7. Düello: iki kimlikli el iki ayrı tuvale çizer. Önce bilinen taraf kazanır.
8. Seyirci modu: `D` tuşu doğru sayar, kelime açılır.
- `--kiyas`: isle p95 ≤ 18 ms (tahmin ayrı iş parçacığında ya da 4 Hz).
