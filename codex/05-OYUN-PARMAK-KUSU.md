# 05. Parmak Kuşu: parmak ucunu izleyen Flappy Bird (Fikir 3)

Dosya: `prototipler/p_parmak_kusu.py`. `IHTIYAC = {"el"}`.
Mevcut `p_ucan_kafa.py` (ağız açınca zıplayan Flappy) sütun, çarpışma ve skor mantığı için başlangıç
olarak okunabilir. Kopyalamak yerine ortak parçayı fonksiyona çıkar.

## Yorum
Kuş doğrudan parmak ucuna yapıştırılırsa (kuş y = parmak y) iki sorun çıkar. Oyun "kuş" hissini
kaybeder, imleç sürmeye döner. Ayrıca titreşim ve gecikme doğrudan görünür. Doğru çözüm, kuşu parmağa
**yay-sönüm (spring-damper)** ile bağlamak. Kuş parmağın gösterdiği yüksekliğe ivmelenerek gider,
hızına göre burnu yukarı/aşağı eğilir, kanat çırpma animasyonu hıza bağlı. Bu hem canlı görünür hem
titreşimi ve küçük gecikmeyi doğal olarak gizler. Oyuncu "kuşu yönlendiriyorum" der, "imleç sürüyorum" demez.

## Tasarım
- Kuş x sabit (ekranın %30'u). Hedef y = süzülmüş parmak ucu y. Kontrol bölgesi kadrajın orta %70'i;
  bu bölge ekranın tamamına eşlenir, kazanç ≤ 1.4.
- Parmak ile kuş arasında ince, esnek bir **ışık bağı** (lastik ip) çizilir. Kontrolün nasıl çalıştığını
  hiç yazı olmadan öğretir.
- **Mod A: Süzül** (varsayılan, stant için): yukarıdaki yay kontrolü. Sütunlar soldan akar. Boşluk
  başta kuş boyunun 3.4 katı, 20 sütunda 2.4 katına iner. Hız kademeli artar. 8. sütundan sonra
  boşluklar yavaşça yukarı-aşağı kayar.
- **Mod B: Gerçek Flappy** (zor, `Boşluk` ile): yerçekimi var. Parmağın hızla **yukarı fiske**
  hareketi (dikey hız > eşik, 120 ms penceresinde) bir kanat çırpışı sayılır. Ayrık olay olduğu için
  gecikmeye toleranslı. Boşluklar Mod A'dan %20 geniş.
- **İki oyuncu:** karede iki oyuncu eli varsa (Oyuncu Kapısı'ndan geçmiş, kimlikli) iki kuş olur:
  farklı renk, aynı sütunlar. Önce düşen kaybeder. Oyun kendiliğinden düelloya döner.
- **El kaybolursa:** kuş 1 sn süzülür (yavaş alçalır, "elini göster" halkası çıkar), sonra düşer.
- **Çarpışma kutusu** sprite'ın %70'i. Sütun kenarına sıyırmak affedilir, kıvılcım çıkar.
- Görsel: paralaks katmanları (uzak neon şehir, yakın sütunlar), kuş parçacık izi bırakır, her
  geçişte "ding" ve skor sayısının zıplaması. Kamera görüntüsü karartılmış arka planda: oyuncu kendini görür.
- Tur 60 sn üst sınır ya da ölüm. Oturumun en iyi 5 skoru.

## Gecikme bütçesi
Mod A 200 ms gecikmeye kadar oynanır (yay zaten ~150 ms gecikmeli). Mod B ≤ 150 ms ister.

## Kabul (`test_parmak_kusu.py`, en az 7)
1. Parmak sabit yükseklikte: kuş 1 sn içinde o yüksekliğe oturur, aşma ≤ %15, titreşim yok (±4 px parmak gürültüsünde kuş ±1.5 px).
2. Parmak ani 300 px sıçrar: kuş tek karede ışınlanmaz.
3. Sütun boşluğundan geçiş skoru +1. Sütuna çarpınca tur biter.
4. Kenar sıyırması (kutunun dışı, sprite'ın içi) ölüm değil.
5. Mod B: yukarı fiske kanat çırpar, yavaş yukarı hareket çırpmaz.
6. İki kimlikli el → iki kuş. Biri düşünce kazanan doğru.
7. El 0.8 sn kaybolur: kuş ölmez. 1.5 sn kaybolur: düşer.
- `--kiyas`: isle p95 ≤ 15 ms.
