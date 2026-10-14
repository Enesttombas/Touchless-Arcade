# 10. AR Maskeler: maske değiştirme anlaşılmıyor ve kendi kendine değişiyor (P0, küçük iş)

> **Enes kararı (2026-10-12 gece, son hali, bu şartnameyi aşar):** "çok akıcı, kolayca değişmeli". Maske **başı yana yatırınca** değişir: sağa sonraki, sola önceki (`KAFA_TETIK`, eşik ~18°, 0.2 sn, baş düzelmeden tekrar yok). Eğilirken sıradaki maskenin ikonu o yandan kayarak gelir, halka dolar. Kaş ve avuç tetikleri kapalı (`KAS_TETIK`/`AVUC_TETIK = False`, avuç canlıda hiç düzgün çalışmadı). Oklar yedek. Menü dönüşü açık avuç 2 sn. Bunları geri çevirme.


Enes (2026-10-12, stanttan gözlem): "AR alanında efektleri değiştirmeyi kimse anlamadı. Uzun süre göz
kırpma vs. Bazıları kendi kendine değişti gibi. Net ve sorunsuz bir çözüm."
Dosya: `prototipler/p_maske.py`. Testler: `kabul_prototip/test_cila.py`, `test_ozel2.py` (`PROTOTIP=p_maske`).

## Teşhis (kodda doğrulandı, Opus 2026-10-12)

Bugün maskeyi **yedi ayrı şey** değiştiriyor. Çoğu insanın kendiliğinden yaptığı hareketler:

| Tetik | Kod yeri | Neden yanlışlıkla tetikleniyor |
|---|---|---|
| Göz kırpma ≥ 0.18 sn (tek ya da iki göz) | `isle()` ~s.737 | Doğal uzun kırpma, gülerken gözleri kısma, aşağı bakma, gözlük yansıması. Ziyaretçi bunu "kendi kendine değişti" diye görür |
| Kaş kaldırma ≥ 0.12 sn | ~s.754 | Kendini maskeyle görünce **şaşırmak** tam olarak kaş kaldırmaktır. İlk tepki maskeyi değiştiriyor |
| Başı ~20° eğme | ~s.747 | Gülerken, arkadaşına dönerken, ekrana yan bakarken |
| El sallama (hızlı yatay hamle) | `_salla` | Arkadaşa el sallamak, selam vermek, kolu düzeltmek |
| Avuç aç → yumruk (1.2 sn) | `_el_hareketleri` | Jest tanıma kaçırıyor ya da rastgele yakalıyor. Neon Kılıç'ta aynı jest yüzünden takılma yaşandı ve beklemeyle çözüldü |
| **Otomatik vitrin: 12 sn'de bir bütün maskeler ilerler** | `isle()` ~s.720 | Yüz varken bile çalışıyor. "Kendi kendine değişti"nin kesin kaynağı |
| Ok düğmesine el tutma 0.6 sn | `_dugmeler` | Tek bilinçli ve sağlam yol. Ama altı yolun arasında kayboluyor |

Ayrıca hiçbir değişimde **nedeni** gösterilmiyor. Kişi neyin değiştirdiğini göremeyince zihinsel model
kuramıyor; yedi gizli kural öğrenilemez. Ekrandaki açıklama da üç farklı yolu birden sayıyor.

## Çözüm ilkesi (bütün oyunlara genellenir, README kural 9)

1. **Kalıcı sonuç doğuran eylem (maske/mod/oyun değiştirme) yalnız görünür bir hedefle olur:**
   ekranda bir düğme, ele tutunca dolan halka, sonra değişim. Kişi neye dokunduğunu görür.
2. **Yüz ifadeleri ve doğal hareketler hiçbir şeyi değiştirmez, yalnız o anki efekti oynatır.**
   Kaş kaldırınca kulaklar zıplar, ağız açınca ateş/kalp çıkar, göz kırpınca yıldız parlar. İnsanların
   doğal tepkisi ödüllendirilir ama kontrol bozulmaz.
3. **Hiçbir şey kişiye sormadan değişmez.** Yüz varken otomatik dönüş yok.
4. **Her değişimin nedeni ve sonucu 1 sn görünür:** "→ KEDİ" etiketi ve kayma animasyonu.

## Tasarım

### Tek kontrol: iki büyük ok düğmesi (var olanı güçlendir)
- Sol ok = önceki, sağ ok = sonraki. Bugünkü `_dugmeler` mantığı korunur:
  - el 0.6 sn tutulunca halka dolar,
  - el çekilmeden ikinci değişim olmaz (`_dugme_kilit`),
  - en yakın yüz değişir (`_yakin_yuz`).
- Düğme etiketi ve ikonu daha okunur olur:
  - içinde bir sonraki/önceki maskenin ikonu (var),
  - altında `ELİNİ TUT` yazısı,
  - yarıçap 54'ten ~70 px'e büyür, isabet payı +30 kalır.
- **Konum:** omuz hizasında, ekran kenarından ~%9 içeride. Kolu yana açınca ulaşılsın, uzanmak gerekmesin.
  Kişi kadrajın bir tarafındaysa (yüz x < 0.3 ya da > 0.7) düğmeler 0.5 sn yumuşak geçişle kişinin
  omuz genişliğinin ~1.6 katı yanına yaklaşır. Böylece kenardaki kişi de karşı oka ulaşabilir.
- El, 01 §2 Oyuncu Kapısı'ndan geçmiş olmalı. Kadraj kenarından giren yabancı parmak ucu düğmeyi doldurmaz.
- **Kalabalık (2–3 yüz):** düğmeler ekranda bir çift kalır. Değişen kişi, düğmeye uzanan elin sahibi
  (01 §4 ortak kimlik: el ↔ poz bileği ↔ yüz). Sahip bulunamazsa ele en yakın yüz değişir
  (bugünkü davranış). Halka dolarken, değişecek yüzün çevresinde ince bir halka yanar. Kişi kimin
  maskesinin değişeceğini önceden görür.

### Kaldırılanlar
- Göz kırpma, kaş kaldırma, baş eğme, el sallama, avuç-yumruk: **maske değiştirmez**. Kod silinmez,
  `Prototip.ESKI_TETIKLER = False` bayrağının arkasına alınır (A/B ve geri dönüş için). Varsayılan kapalı.
- Otomatik 12 sn döngüsü: **yalnız kimse yokken** çalışır (çekim ekranı vitrini). Yüz görününce durur.

### Yüz ifadeleri efekte bağlanır (kaldırılan tetiklerin yerine)
Her maske en az bir ifadeye tepki verir. Var olanlar korunur: `jaw` ile Köpek dili, Gökkuşağı,
bükülme. Eksik olanlara eklenir:
- Kaş kaldırma: kulak/boynuz/taç 0.2 sn zıplar (`kas_carpan` zaten var, değişimden ayrılır, ölçeği artar).
- Göz kırpma: göz bölgesinde küçük yıldız/parıltı (Kalp Göz'de kalpler kırpışır).
- Ağız açma: maskeye uygun parçacık. Ejderha ateşi Şeytan'da, kalpler Ayıcık'ta, baloncuk Uzaylı'da.
  Kişi başına en fazla 2 sn'de bir patlama.
- Baş eğme: sarkan parçalar (kulak, püskül, korsan şapkası) eğim yönüne savrulur (02 §3 Verlet ile ya da basit yay).
Ekranın altında maskeye göre değişen tek satır ipucu: "Ağzını aç!" / "Kaşlarını kaldır!". Kişi
3 sn içinde denemezse ipucu kaybolur, 10 sn sonra bir kez daha gelir.

### Öğretme (yazısız, 3 saniyede)
- Yüz ilk göründüğünde 2.5 sn boyunca hayalet bir el animasyonu omuzdan sağ oka gider ve halkayı
  doldurur. Okun altında `ELİNİ TUT → MASKE DEĞİŞİR`. Gerçek bir değişim olmaz, yalnız gösterim.
- Kişi 8 sn hiç değişim yapmazsa oklar 2 kez nabız atar (ölçek 1.0 → 1.12 → 1.0). Ses yok, sadece görsel.
- `ACIKLAMA` tek yola iner: "Elini yandaki oka tut: maskeni değiştir. Ağzını aç, kaşını kaldır: maske canlansın!"

### Geri bildirim (her değişimde)
- Kişinin başının üstünde 1 sn: yeni maskenin ikonu ve adı (`→ KEDİ`), kayarak gelir.
- Eski maske düğme yönüne kayıp solar, yenisi karşı taraftan gelir (bugünkü `eski_oran/yeni_oran`
  geçişine yatay kayma eklenir). Yön, hangi oka basıldığıyla tutarlı.
- "pop" sesi ve parçacık (var).

### Foto anı (var olan, netleştir)
- Maske 6 sn değişmezse 3-2-1 ve flaş. Kalsın, ama geri sayım rakamlarının altına "📸 Poz ver!"
  ikonunu `emoji_sprite` ile ekle. İnsanlar 3-2-1'i "bir şey değişecek" sanmasın. Diske kayıt yok.

## Kabul (`test_maske_kontrol.py`, `PROTOTIP=p_maske`, en az 10)
Eski davranışı test eden testler (`test_cila.py`: `test_maske_bas_egme_ve_el_sallama_degistirir`,
`test_maske_el_sallama_ileri_geri_tek_degisim`, `test_maske_kas_kaldirma_degistirir_tutmak_tekrarlamaz`,
`test_maske_kisa_kirpma_ve_avuc_ac_kapa_degistirir`) bilinçli olarak **tersine çevrilir**: aynı girdi,
yeni beklenti "değişmez". Test sayısı düşmez. Değişiklik `ILERLEME.md`'ye gerekçesiyle yazılır.

1. İki göz 0.6 sn kapalı (`eyeBlink*` 0.9) → maske değişmez, göz efekti bayrağı açılır.
2. Kaş 1 sn yukarıda → maske değişmez, `kas_carpan` > 1 olur.
3. Baş 0.5 rad eğik 1 sn → maske değişmez.
4. El yüzün önünde hızla sallanır (bugünkü sallama testi girdisi) → maske değişmez.
5. Avuç → yumruk 0.5 sn içinde → maske değişmez.
6. Yüz varken 30 sn hiçbir girdi yok → maske değişmez. Yüz yokken 12 sn → vitrin ilerler.
7. El sağ okta 0.6 sn → sonraki maske. 0.4 sn → değişmez. 3 sn tutmak tek değişim.
   El çekilip tekrar 0.6 sn → bir değişim daha.
8. Sol ok → önceki maske (indeks −1, sarmalı).
9. İki yüz: sağ yüzün eli (poz bileği eşleşmesi) sağ oka uzanır → yalnız sağ yüz değişir. Doluş sırasında hedef yüz bayrağı doğru.
10. Kadraj kenarında yarım görünen, Oyuncu Kapısı'ndan geçmemiş el okun üstünde 2 sn → değişim yok.
11. Değişimden sonra 1 sn boyunca etiket durumu (`→ <ad>`) açık, sonra kapanır.
12. `ESKI_TETIKLER = True` iken eski göz kırpma testi yine değiştirir (geri dönüş yolu çalışıyor).
- `--kiyas`: isle p95 ≤ 20 ms (yeni efektler dahil).

## Canlı doğrulama (Enes ile, stantta ya da masada)
3 kişiye hiçbir şey anlatmadan maskeyi açtır ve şunları say:
- maskeyi kendi başına değiştirebilen kişi sayısı,
- ilk başarılı değişime kadar geçen süre,
- istemeden değişim sayısı.
Hedef: 3 kişinin 3'ü de 10 sn içinde değiştirsin, istemeden değişim 0 olsun. Sonuç `ILERLEME.md`'ye.
