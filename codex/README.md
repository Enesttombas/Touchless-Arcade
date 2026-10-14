# Codex görev paketi: Stant AR oyunları, faz 2

Hazırlayan: Claude Opus 5.5, 2026-10-12. İsteyen: Enes. Uygulayıcı: Codex.
Bu klasör yalnız plan ve şartname içerir; kod yok. Kodu Codex **bizzat** yazar
(işi başka bir işçiye devretme; tat ve his işi bu, devredilince kalite düşüyor).

## Okuma sırası

| Dosya | Ne | Öncelik |
|---|---|---|
| `README.md` | Bu dosya: kurallar, sıra, kabul | önce |
| `00-DONANIM-VE-YAYIN.md` | HP ekranı + kamera + laptop bağlantısı, gecikme | **P0** (stant günü) |
| `01-ALTYAPI.md` | Ölçüm, Oyuncu Kapısı (yanlış algılama), filtre/öngörü, kimlik takibi | **P0** |
| `10-AR-MASKE-KONTROL.md` | AR Maskeler: değiştirme anlaşılmıyor / kendi kendine değişiyor | **P0** (küçük, canlı şikâyet) |
| `02-AR-KALITE.md` | Daha iyi insan analizi, 3B/"4D" efektler, GPU, görsel cila | P1 |
| `03-OYUN-CEVAP-YAGMURU.md` | Fikir 1: kelimeler insanlara çarpan bilgi yarışması | **P1 (amiral gemisi)** |
| `04-OYUN-NEON-TEL.md` | Fikir 2: parmakla labirent, gecikme araştırması | P2 |
| `05-OYUN-PARMAK-KUSU.md` | Fikir 3: parmağı izleyen Flappy Bird | P1 (kolay kazanç) |
| `06-OYUN-NEON-KOSU.md` | Fikir 5: Subway Surfers tarzı | P2 |
| `07-OYUN-CIZ-TAHMIN.md` | Fikir 7: havaya çiz, yapay zekâ ve insanlar tahmin etsin | P1 |
| `08-REKABETCI-OYUNLAR.md` | Fikir 6: Gülme Düellosu gibi rekabetçi oyunlar | P2 |
| `09-HOCAYI-ETKILEYECEK.md` | Fikir 4: profesörü etkileyecek deneyimler | P2 |
| `11-OYUN-PENALTI.md` | Futbol: parmakla sapan şut, bedenle kalecilik, frikik (Enes isteği) | P3 (**en son**) |
| `12-OYUN-INSAN-DIZISI.md` | Hoca isteği: İşlem Dizisi + Cümle Dizisi, insanlar kartla sıraya geçer (3–5 kişi) | **P1** (2026-10-13) |
| `ARASTIRMA-KAYNAKLAR.md` | Web araştırmasının özeti ve kaynakları (YEREL / KAYNAK / ÖLÇ sınıflı) | başvuru |
| `OLCUM-PROTOKOLU.md` | Camdan cama gecikme, aşama zamanları, titreşim ölçümü | 00 ve 01 ile |
| `PLAN-RAPORU.md` (+ `.pdf`) | Enes için özet: yorumlar, öncelik, açık kararlar | başvuru |

Önerilen yapım sırası: 00 → 01 → 10 → 03 → 05 → 07 → 02 → 08 (ilk üç oyun) → 04 → 06 → 09 → 11.
Her dosyanın sonunda **Kabul** bölümü var; o bölüm yeşil olmadan sonraki dosyaya geçme.

## Proje gerçekleri (değiştirme, üstüne kur)

- Kök: `C:\Users\Enes\Documents\EnesOS\work\meme-kamera`
- Python: `app\.venv\Scripts\python.exe` (mediapipe 1.0.1, opencv 5.0.0, numpy 2.4.6,
  onnxruntime 1.30.0, torch 2.6.0+cu124, pygame-ce 2.5.8). Yeni paket gerekiyorsa gerekçesini
  ilgili dosyanın sonuna yaz, `pip install` ile bu venv'e kur, sürümü sabitle.
- Laptop: i9-14900HX, RTX 4080 Laptop 12 GB. Stant ekranı: HP ProOne 440 G3 (i5-7500T, GPU yok).
- Uygulama: `prototipler/stant_app.py` (menü + 5 oyun). Ortak çekirdek `prototipler/cekirdek.py`
  (`Algi`, `Algilayici`, `Maskeci`, `Ses`, `panel`, `halka`, `parilti`, `sahte_el/yuz/poz`).
  Çekirdek eski `stand/stand.py` dosyasını kütüphane olarak içeri alır (yazı, sprite, parçacık); silme.
- Oyun sözleşmesi (`cekirdek.py` başı): her `p_*.py` bir `Prototip` sınıfı verir: `AD`, `ACIKLAMA`,
  `IHTIYAC` (set: `yuz`, `blend`, `yuz2`, `el`, `poz`, `poz?`), `SIRA`, `__init__(ses)`,
  `isle(kare, algi, simdi) -> kare` (BGR 1280x720, aynalı), isteğe bağlı `tus(k)`.
  Oyun sürerken `self.durum == "oyun"` olmalı; bu, stant_app'in boşta menüye dönüşünü engeller.
- Testler: `kabul_prototip/` (pytest). Oyuna özel testler `PROTOTIP=p_x` ortam değişkeniyle seçilir
  (`test_ozel.py`, `test_cila.py` kalıbı). Bugünkü taban (2026-10-12, `python -m pytest -q kabul_prototip`): **41 passed, 32 skipped, rc 0**.
- Görsel dil: neon, koyu panel, Türkçe metin `yazi_koy` ile (emoji metne gömülmez, `emoji_sprite` ayrı).
  Renkler `cekirdek.py` sabitleri (SARI, CAMGOBEGI, PEMBE, YESIL, BEYAZ, KIRMIZI).
- Gizlilik: ziyaretçi fotoğrafı/videosu diske yazılmaz. Skor tablosunda yüz yok, takma ad/renk var.

## Değişmez kurallar

1. **Ölç, sonra iddia et.** Performans iddiası `01-ALTYAPI.md` §1 ölçüm aracının çıktısıyla verilir.
   Kare bütçesi: `isle()` medyan ≤ 14 ms, p95 ≤ 25 ms (1280x720, laptop). Algı ayrı iş parçacığında.
2. **Kör kabul.** Her oyun için kamerasız, sahte noktalarla sürülen pytest yaz (en az dosyada yazan sayı).
   Testler gerçek davranışı kontrol etsin (durum geçişi, skor, çarpışma), "hata vermedi" değil.
3. **Mevcut testleri kırma.** Taban 41 passed korunur. Test sayısı düşerse dur ve nedenini yaz.
4. **Ortak kod ortakta.** Filtre, kapı, kimlik takibi, ölçüm gibi şeyler oyun dosyasına kopyalanmaz;
   `01-ALTYAPI.md`'deki modüllere yazılır, oyunlar onları çağırır.
5. **Gecikmeye dayanıklı tasarım.** Hiçbir oyun 1 karelik (33 ms) hassasiyet istemez. Her oyunun
   şartnamesinde gecikme bütçesi var; ona uy.
6. **Stant akışı.** Her oyun: bekleme/çağrı ekranı → 3-2-1 → oyun (30–90 sn) → sonuç (≤ 6 sn) → bekleme.
   Öğretmeye gerek kalmasın: kuralı ekranda ≤ 8 kelimeyle ve hareketli bir örnekle göster.
7. **Commit.** `work/meme-kamera` şu an git'te izlenmiyor. İlk iş olarak Enes'ten onay alıp
   kaynak dosyaları (`*.py`, `*.md`, `*.bat`, `kabul_prototip/`) commit et; `app/.venv`, model
   dosyaları, `duvar/`, `__pycache__`, `.omc/` hariç (`.gitignore`). Git/push kararı Enes'in.
8. Her fazın sonunda `codex/ILERLEME.md` dosyasına ekle: tarih, ne yapıldı, koşulan komut,
   gerçek çıkış kodu, ölçüm tablosu, açık kalanlar.
9. **Kontrol ilkesi (10'dan genellenir).** Kalıcı sonuç doğuran eylem (maske, mod ya da oyun değiştirme)
   yalnız ekranda görünen bir hedefe ele tutulup dolan halkayla olur. Göz kırpma, kaş, baş eğme, el
   sallama gibi doğal hareketler hiçbir şeyi değiştirmez, yalnız anlık efekt oynatır. Kişi oradayken
   hiçbir şey kendiliğinden değişmez. Her değişimin sonucu 1 sn görünür.

## Yeni dosya yerleşimi

```
prototipler/
  oyuncu.py        # Oyuncu Kapısı + kimlik takibi (01 §2, §4)
  filtre.py        # One Euro filtre + öngörü (01 §3)
  olcum.py         # kare profili, gecikme testi (01 §1)
  sahne3d.py       # (isteğe bağlı) GPU efekt/bileşim katmanı (02 §4)
  p_cevap_yagmuru.py, p_parmak_kusu.py, p_neon_tel.py, p_neon_kosu.py, p_ciz_tahmin.py,
  p_refleks.py, p_tas_kagit.py, p_duvar_delik.py, p_kafa_pencere.py ...
  veri/sorular.json, veri/ciz_kelimeler.json
  modeller/ciz_tanima.onnx (07)
kabul_prototip/
  test_altyapi.py, test_oyuncu_kapisi.py, test_yeni_oyunlar.py ...
```

stant_app.py menüsü 5 karta göre çizilmiş (`DENEYIMLER`). Oyun sayısı artınca menüyü
2 sayfa ya da kaydırmalı şerit yap (kart başına el ile seçim korunur), operatör tuşları 1-9 + N/B kalır.
