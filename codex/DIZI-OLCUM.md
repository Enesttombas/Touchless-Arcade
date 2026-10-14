# İnsan Dizisi: Saha Ölçüm ve Operatör Kılavuzu

Bu belge, **İşlem Dizisi** ve **Cümle Dizisi** oyunlarının sahada kamera doğrulaması, veri toplama ve çaprazlama (re-ID) başarım testleri için operatör talimatıdır.

> **NOT:** Gerçek kamera ve fiziksel insanlarla yapılan saha ölçümleri **henüz tamamlanmamıştır (beklemede)**. Bu kılavuz, testlerin standart protokol ile yürütülmesini sağlar; uydurma kamera sonucu içermez.

---

## 1. Menüden Başlatma ve Operatör Tuşları

1. **Menü Erişimi:**
   - Ana menüde sayfalar arasında geçiş için klavyeden `N` (sonraki sayfa) veya `B` (önceki sayfa) kullanılır.
   - 2. sayfada:
     - **1. Kart:** İşlem Dizisi (`p_islem_dizisi.py`)
     - **2. Kart:** Cümle Dizisi (`p_cumle_dizisi.py`)
2. **Lobi ve Oyuncu Sayısı:**
   - Bekleme/lobi ekranında hedef oyuncu sayısını sabitlemek için operatör tuşları: `3`, `4` veya `5`.
   - Başlatmak için: `Boşluk` (Space).
   - Oyuncular jestle başlatmak isterse: N kişi yan yana durup aynı anda bileklerini burun üstünde 0.8 sn tutar.

---

## 2. Saha ve Kamera Kurulum Gereksinimleri

- **Mesafe:** Oyuncular ile kamera arası **2.5 m – 3.5 m** (5 kişi için 3.0 – 3.5 m önerilir).
- **Görüş Alanı & Işık:**
  - Tüm oyuncuların (3–5 kişi) omuzları kadrajda kalmalı ve omuz genişliği ekranda `≥ 0.035` olmalıdır.
  - Dengeli ön/üst aydınlatma gereklidir. Arkadan gelen doğrudan güneş ışığı veya parlak spot (ters ışık) engellenmelidir.
- **Gizlilik ve Algılayıcı Sınırı:**
  - Yalnızca MediaPipe PoseLandmarker (`num_poses=6`) aktiftir.
  - **Yüz ve el tespit modelleri ASLA açılmaz.**
  - El kaldırma jesti doğrudan poz iskeletinden (bilek 15/16 ve burun 0) çözülür.

---

## 3. Veri Kaydı ve Canlı Operatör Doğrulaması

Kayıt aracı: `prototipler/dizi_olcum.py` (veya oyun içindeki ölçüm kancası).

- **`K` Tuşu (Kayıt Başlat/Durdur):**
  - Kayıt `TEMP/` dizini altına `.jsonl` formatında yazılır.
  - **Gizlilik Güvencesi:** Diske hiçbir kamera karesi / ham görüntü yazılmaz. Yalnızca iskelet noktaları, poz kimlikleri, atama matrisi, sayısal imza vektörleri ve durum olayları (`karisma`, `cozum`, `belirsiz`) kaydedilir.
- **Canlı Doğrulama Tuşları (`D` ve `Y`):**
  - **Sadece çaprazlama tamamlandıktan sonra** operatör sonucu etiketler:
    - `D`: Kartlar ve oyuncu ataması **doğru** kişide kaldı.
    - `Y`: Kart yanlış kişiye geçti (takas hatası / sessiz yanlış).
  - Canlı etiketler JSONL akışına `tip: etiket` olarak, o anki oyuncu eşlemesiyle eklenir.

---

## 4. 5 Standart Test Senaryosu

Her senaryo hem **3.0 m** hem **3.5 m** mesafede, her biri **en az 10 çaprazlama** içerecek şekilde tekrarlanır:

1. **Farklı Kıyafetler (`differentshirtscross`):**
   - 2-3 kişi belirgin farklı renklerde üst giysilerle yer değiştirir.
2. **Benzer Kıyafet ve Saç (`sameshirts+hair`):**
   - 2 kişi aynı/koyu renk (örn. siyah tişört) ve benzer saç yapısıyla çaprazlama yapar.
3. **Üç Kişi:** Ortadaki kişi yana geçer.
4. **Beş Kişi:** Tam tur, serbest oyun.
5. **Hızlı Hareket:** Koşarak hızlı yer değiştirme.

Ek olarak kadrajdan çıkıp dönmeyi ve küçük omuzlu izleyicinin kart almamasını kontrol edin. Laptop ve HP ProOne kamera sonuçlarını ayrı kaydedin. Sessiz yanlış/çaprazlama hedefi 1, 3, 4, 5 için ≤%5; benzer koyu kıyafetli 2. senaryoda ≤%15. Yanlışların en az %70'i belirsiz işaretlenmeli; gereksiz belirsiz/çaprazlama ≤%20 olmalı.

---

## 5. Analiz Metrikleri ve Çevrimdışı Tekrar Oynatma

Kaydedilen JSONL dosyası kamera olmadan motora tekrar verilebilir:

- **Olgun İmza Kontrolü:** Kişi yalnızken 10 güvenli örneğe ulaşma süresi.
- **Belirsizlik Süresi:** Kartın sarı "?" rozetiyle kaldığı süre (hedef: < 2.5 sn içinde çözülme veya el takası).
- **İlk Atama Gecikmesi:** Çaprazlama bittikten sonra ayrılma anı ile çözüm arasındaki gecikme (hedef: ≤ 0.25 sn).
- **Taban Kıyaslaması (False Flip):**
  - İmza açık: `--tekrar <dosya.jsonl>`
  - Yalnız `oyuncu.py` poz kimliğini kullanan taban: `--tekrar <dosya.jsonl> --imzasiz`
  - İki raporun eşlemeleri, belirsizlik süreleri ve etiketli hataları karşılaştırılır.
  - `canli_dogruluk`, kayıttaki D/(D+Y) oranıdır. Tekrarın `dogruluk` alanı yalnız etiketten doğrulanabilen eşlemeleri kullanır. Y etiketinden farklı bir eşleme çıkarsa hangi kişinin doğru olduğu bilinmez; örnek `bilinmeyen` sayılır. Etiketsiz kayıtta doğruluk `null` olur.

---

## 6. Performans Bütçesi ve Sınırlar

| Bileşen | Sınır / Hedef | Açıklama |
|---|---|---|
| `isle()` medyan | **≤ 14.0 ms** | 1280×720 giriş (laptop) |
| `isle()` p95 | **≤ 25.0 ms** | Tepe gecikme sınırı |
| 5 kişi İmza Hesabı | **≤ 2.0 ms** | 64×64 HSV histogram + Lab |
| Algılama Modelleri | Yalnız Pose | El ve Yüz kapalı |
| Görüntü Depolama | 0 bayt | Sadece sayısal vektör / JSONL |

---

## 7. Çalıştırma Komutları (PowerShell)

Tüm komutlar projenin kök dizininde, sanal ortam Python yorumlayıcısıyla çalıştırılır:

```powershell
& app/.venv/Scripts/python.exe prototipler/stant_app.py
& app/.venv/Scripts/python.exe prototipler/dizi_olcum.py --tekrar "$env:TEMP/dizi_kayit_örnek.jsonl"
& app/.venv/Scripts/python.exe prototipler/dizi_olcum.py --tekrar "$env:TEMP/dizi_kayit_örnek.jsonl" --imzasiz
& app/.venv/Scripts/python.exe prototipler/dizi_olcum.py --gurultu
& app/.venv/Scripts/python.exe prototipler/dizi_olcum.py --onizleme --cikti "$env:TEMP/dizi_onizleme"
& app/.venv/Scripts/python.exe prototipler/olcum.py --kiyas --kareler 300
```

Kayıt yolunu K tuşundan sonra ekranda gösterilen gerçek dosya yoluyla değiştirin. Önizlemeler sentetiktir; saha kabulü yerine geçmez. Süre kıyası kamera/algılama gecikmesini içermez.

