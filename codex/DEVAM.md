# DEVAM: yeni Codex oturumu için tek brief (2026-10-12)

Kök: `C:\Users\Enes\Documents\EnesOS\work\meme-kamera`. Python: `app\.venv\Scripts\python.exe`.
Önceki oturum saatlerce altyapıda kaldı. Bu oturumun amacı **oynanabilir oyunları hızla teslim etmek**.
Kodu sen bizzat yaz, başka işçiye devretme.

## Şu anki durum (Opus kontrolü)
- 00 donanım: `prototipler/kamera_kopru.py` ve `kabul_prototip/test_kamera_kopru.py` yazıldı, yeşil.
  HP ve kablo olmadan geri kalanı test edilemiyor: **00'a dokunma**, HP gelince yapılacak.
- Stant uygulaması: 3×3 menü, 1–3 tuşları, masaüstü EXE hazır (`stant_app.py`, `cekirdek.py` değişti,
  commit edilmedi). Loop ve Gölge Pelerini kapalı.
- 01 altyapı: yarım. Titreşim filtresinde bir formül hatası bulunmuştu. `oyuncu.py`, `filtre.py`,
  `olcum.py` henüz yok ya da bitmedi.
- Test tabanı: **53 passed, 32 skipped, rc 0** (Opus koştu, 2026-10-12). Bu sayı düşmez.
- `codex/ILERLEME.md` hiç yazılmadı: ilk iş bunu oluştur ve yukarıdaki durumu yaz.

- **Opus düzeltmesi (2026-10-12 gece):** AR maske başı yana yatırınca değişir (kaş/avuç kapalı), menü dönüşü 2 sn açık avuç. Ayrıntı `10-AR-MASKE-KONTROL.md` başı. `p_maske.py`/`stant_app.py`'de bunu geri alma.

## Yeni sıra (oyunlar öne alındı)
Her şartnameyi `codex/<dosya>.md`'den oku; README kuralları geçerli (özellikle kural 9).

| # | İş | Zaman kutusu |
|---|---|---|
| 1 | 01 minimum: `filtre.py` (One Euro + öngörü) ve `oyuncu.py` (Oyuncu Kapısı + basit kimlik). `olcum.py` yalnız `--kiyas` + p50/p95; Bilim Modu sonra | 60 dk |
| 2 | 10 AR maske kontrolü | 45 dk |
| 3 | 05 Parmak Kuşu | 60 dk |
| 4 | 03 Cevap Yağmuru (amiral gemisi) | 120 dk |
| 5 | 08'den Kovboy Düellosu + Taş-Kağıt-Makas | 90 dk |
| 6 | 11 Penaltı Düellosu | 120 dk |
| 7 | 07 Çiz-Tahmin (indirme onayı var) | 120 dk |
| 8 | 04 Neon Tel, 06 Neon Koşu | 90 dk her biri |
| 9 | 08 kalanları (Duvardaki Delik, Heykel), 09 hoca, 02 AR kalite | kalan zamanda |

## Hız kuralları (zorunlu)
1. **Zaman kutusu:** süre dolunca oyun çalışır ve temel testleri yeşilse kapat. Eksikleri
   `ILERLEME.md`'ye "sonra" diye yaz ve sıradakine geç. Cila için geri dönme.
2. **Önce oynanır hal:** sırayla oyun döngüsü, menüye kart, temel kabul testleri, en son görsel cila.
3. **Testler:** çalışırken yalnız o oyunun test dosyasını koş. Tüm takımı yalnız iş bitince koş:
   `app\.venv\Scripts\python.exe -m pytest -q kabul_prototip -p no:cacheprovider`.
   Şartnamedeki test sayısını hedefle. Zaman kutusu dolarsa en kritik davranış testleri (durum geçişi,
   skor, çarpışma) yeterli; kalanlar ILERLEME'ye açık iş.
4. **Yapma:** web araştırması, HP/ağ/kurulum işi, mevcut oyunlarda şartname dışı yeniden yazım,
   uzun planlama. Belirsizlikte şartnamedeki varsayılanı seç, ILERLEME'ye not düş, devam et.
5. **Menü:** her yeni oyun stant menüsüne kart olarak eklenir (3×3 yetmezse 2. sayfa).
6. **Commit:** her iş bitince yerel commit at. Yalnız `work/meme-kamera` altındaki kendi kaynak
   dosyalarını stage et (log, txt, tsv, `.venv`, model, `__pycache__` hariç). Depoda başka
   değişiklikler var, onlara dokunma. Push yok.
7. **Rapor:** her iş bitince `ILERLEME.md`'ye tek blok yaz: tarih-saat, iş, değişen dosyalar,
   koşulan test komutu ve gerçek sonucu (`N passed`), açık kalanlar. Bitti demek için gerçek komut çıkışı şart.

## Bitiş
Tablodaki 1–7 bitince Enes'e kısa özet ver: hangi oyunlar menüde, test sonucu, açık kalanlar.
8–9 için zaman varsa devam et.
