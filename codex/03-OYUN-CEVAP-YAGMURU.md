# 03. Cevap Yağmuru: kelimeler insanlara çarpar (Fikir 1, amiral gemisi)

Dosya: `prototipler/p_cevap_yagmuru.py`, veri: `prototipler/veri/sorular.json`.
`IHTIYAC = {"poz", "yuz"}`, çoklu kişi. Hedef: 2–6 kişi aynı anda, seyirci de anlıyor.

## Enes'in fikri (özü korunur)
İnsanlar kameradan biraz uzaklaşır. Ekranda bir soru belirir (matematik, doğru/yanlış, genel kültür).
Cevap kelimeleri insanların üstüne doğru gelir. Her kişi doğru bildiği kelimenin geldiği bölgede durur.
Kelime çarptığında doğru cevapta duranlar **yeşil yanar ve kelime içlerinden geçip gider**, yanlışta
duranlar **kırmızıya döner**.

## Tasarım (Opus önerisi, eklemelerle)

### Sahne: üç şeritli "ışık koridoru"
- Kadrajın alt yarısında, zemin perspektifinde 2 ya da 3 şerit var. Doğru/Yanlış için 2 şerit, çoktan
  seçmeli için 3. Şeritler kaybolma noktasına doğru daralan ışık perdeleri olarak çizilir: kenarlarda
  dikey neon ışık perdesi, zeminde şerit rengi. Kişinin hangi şeritte olduğu **kalçaların orta
  noktasıyla** belirlenir (poz 23/24; görünmüyorsa omuz ortası 11/12).
- Cevap kelimeleri kaybolma noktasından (ekranın üst-orta bölgesi) doğar. Kendi şeritlerinde z ekseninde
  yaklaşarak büyür: perspektif ölçek ∝ 1/z, hafif yalpalama ve dönme var. Bu 3B hissi verir ("4D":
  yaklaşırken ses yükselir, şerit zemini kelimenin ışığıyla aydınlanır).
- Soru kartı üstte, büyük ve okunur (≥ 54 px). Kalan süre kelimelerin yaklaşmasıyla görünür; ayrıca
  sayaç gerekmez, isteğe bağlı ince çubuk.

### Akış (tur ≈ 10–12 sn, oyun 6 soru ≈ 75 sn)
1. **Toplan** (bekleme): "Kadraja gir, tam boy görün" + zeminde ayak izi işaretleri. En az 1 oyuncu
   (Oyuncu Kapısı'ndan geçmiş poz) 1.5 sn görününce 3-2-1.
2. **Soru** (2.5 sn): soru kartı iner, şeritlerin uzak ucunda cevaplar belirir.
3. **Düşün ve yer değiştir** (6 sn): kelimeler yaklaşır. Her şeridin üstünde o şeritte duran kişi
   sayısı görünür ("2 kişi"); seyirci için tansiyon. Son 1.5 sn kalp atışı sesi ve şerit ışıkları nabız atar.
4. **Kilit** (çarpışmadan 0.4 sn önce): şerit ataması dondurulur. Son anda kaçanı yakalamak için
   kilit anındaki konum geçerli. Kilit anında hafif ağır çekim (zaman 0.35×, 0.6 sn) olur; dramatik an.
5. **Çarpışma** (1.5 sn):
   - **Doğru şerit:** kelime yeşile döner, kişinin silüetine ulaşınca içinden geçer. Bu, kişi
     maskesiyle yapılır: kelime önce kişinin önünde, çarpışma derinliğini geçince maskenin arkasında çizilir.
     Böylece gerçekten içinden geçmiş görünür. Silüet kenarı yeşil parlar, yeşil kıvılcımlar çıkar, "ding" sesi.
   - **Yanlış şerit:** kelime kişinin göğsünde patlar. Harfler parçalanıp kişinin omuzlarına düşer ve
     silüet üstünde birikir (Camille Utterback'in "Text Rain" eserine selam: harfler maske kenarına
     takılıp durur). Kişinin silüeti 0.8 sn kırmızı tonlanır, ekran hafif sarsılır, "bonk" sesi.
   - **Boş şerit:** kelime ekranın dışına uçup gider.
6. **Puan** (1 sn): her kişinin başının üstünde renkli kimlik halkası ve puanı (+100; seri bonusu +50/+100)
   görünür. 3 doğru serisi yapan kişinin başında taç belirir (yüz ya da poz kafa noktasına bağlı).
7. 6 soru sonra **podyum**: ilk 3 kişinin başına madalya iner, konfeti. Skor tablosu takma ad/renkle
   tutulur (yüz kaydı yok). Oturumun en iyi 5 skoru bekleme ekranında döner.

### Modlar
- **Puan** (varsayılan, 2–6 kişi): yukarıdaki akış.
- **Hayatta Kalma** (kalabalık): yanlış yapan kişinin başında kalıcı kırmızı X belirir ve kişi kenara
  çekilmeye davet edilir. Ayakta kalan son kişi kazanır. Kimlik takibiyle zorlanır: X'li kişi doğru
  yapsa da puan almaz.
- **Tek kişilik antrenman**: tek oyuncuyla zorluk hızla artar (süre 6 → 3.5 sn).

### Soru bankası `veri/sorular.json`
- Şema: `{id, kategori, tip: "dy"|"coktan", soru, secenekler[], dogru_indeks, zorluk 1-3, kaynak?}`.
- **Matematik soruları üretilir** (bankada tutulmaz). Örnekler: "7 × 8 = ?", "√144 = ?", "%25'i 80 olan
  sayı?", "2⁵ = 32 (D/Y)". Yanlış seçenekler yakın değerlerden seçilir. Doğru cevap kodla hesaplanır,
  hiç hatalı olmaz. Zorluk tura göre artar.
- **Genel kültür / doğru-yanlış:** başlangıç için en az 60 soru. Yalnız kolay doğrulanabilir, tarih
  bağımsız olgular (başkentler, birimler, bilim temelleri, Türkçe dil oyunları). Güncel olay, sıralama,
  "en büyük/en yeni" gibi eskiyebilen soru **yok**. Her soruya `kaynak` alanı (kısa) yaz. Bankanın
  doğruluğunu Enes'in gözden geçirmesi için `veri/sorular_inceleme.md` listesi üret.
- **Stanta özel kategori:** "Bilgisayar mühendisliği / yapay zekâ" (ör. "1 bayt = 8 bit (D/Y)",
  "Python bir programlama dilidir"). Üniversite/bölüm soruları için boş bir `ozel` kategorisi aç; Enes doldurur.
- **Emoji bilmece** (isteğe bağlı): "🍎 + 📱 = ?" → Apple. Emoji `emoji_sprite` ile çizilir.

## Teknik
- **Algı:** PoseLandmarker `num_poses` 4–6 (lite). Oyuncu Kapısı'nın poz kuralı ve kimlik takibi
  (01 §2, §4) zorunlu. Uzak kişi küçük görünür: poz için boyut eşiğini bu oyunda düşür
  (`KAPI = {"poz_omuz_min": 0.035}`), şerit alanı dışını yok say.
- **Kişi maskesi:** paylaşılan `Maskeci`. Kişi başına maske = maske ∩ kişinin poz kutusunun
  genişletilmiş hali. Renk tonlama ve "içinden geçme" bununla yapılır. Maske gecikmesi (~1 kare)
  çarpışma anında sorun değil.
- **Kararsız bölge:** şerit sınırının ±%3'ünde duran kişi için şerit çizgisi sarı yanar ve "Çizgide
  durma!" uyarısı çıkar. Kilitte en yakın şerit merkezine atanır.
- **Kelime çizimi:** perspektif ölçekli yazı sprite'ı (`yazi_sprite` önbellekli) + şerit renginde ışık.
  Çok uzun kelimeler 2 satıra bölünür. Ölçek adımları önbelleğe alınır (`donmus` kalıbı).
- **Ses:** yaklaşırken artan uğultu (önceden sentezlenmiş, ses seviyesi z'ye bağlı), ding, bonk,
  tik-tak, podyum fanfarı. Hepsi `Ses` sentezi ya da önyüklenmiş dosya; döngüde disk okuma yok.
- **Kamera yerleşimi önerisi:** HP üst kamerası göğüs/baş hizasında. Oyuncular 2–3 m geride ve tam
  boy görünür. Stant zeminine şeritleri gösteren renkli bant yapıştırılırsa ekrandaki şeritlerle eşleşir.
  Bu ucuz ama çok etkili bir dokunuş. Ekrandaki şerit sınırları bu bantlara göre `S` tuşuyla kalibre
  edilebilir: operatör sınırları ok tuşlarıyla kaydırır, `veri/serit_ayar.json` dosyasına yazılır.

## Gecikme bütçesi
Kişiler bedenleriyle yer değiştirir; 300 ms gecikme bile hissedilmez. Kritik olan yalnız kilit anı ve
o an ekranda gösterilir. Bu oyun bugünkü kablosuz hatta bile çalışır.

## Kabul (`test_cevap_yagmuru.py`, `PROTOTIP=p_cevap_yagmuru`, en az 10 test)
1. Oyuncu yokken bekleme. 1 oyuncu (sahte poz) 1.5 sn görününce geri sayım, sonra `durum == "oyun"`.
2. Üretilen 500 matematik sorusunun hepsinde `secenekler[dogru_indeks]` hesapla doğrulanıyor ve seçenekler benzersiz.
3. Doğru şeritte duran sahte kişi: çarpışma sonrası puanı arttı, durumu "dogru".
4. Yanlış şeritteki kişi: puan yok, "yanlis" durumu, kişi maskesi bölgesinde kırmızı tonlama var
   (piksel ortalaması kırmızıya kaydı).
5. Kilitten sonra şerit değiştiren kişi kilit anındaki şeride göre değerlendirilir.
6. Kararsız bölgedeki kişi en yakın şeride atanır.
7. İki kişi yer değiştirince puanlar kimliğe bağlı kalır, karışmaz.
8. Seri: 3 doğru üst üste → taç bayrağı açık.
9. Hayatta Kalma modunda X'li kişi doğru yapsa da puan almaz, son kalan kazanır.
10. 6 soru sonunda podyum durumu ve sıralama doğru, ≤ 6 sn sonra beklemeye döner.
11. `sorular.json` şema doğrulaması: zorunlu alanlar, `dogru_indeks` aralıkta.
- `olcum.py --kiyas`: 6 sahte kişiyle isle p95 ≤ 25 ms.
- Görsel kabul: `--onizleme` çıktısı olarak 5 ekran görüntüsü üret (soru, yaklaşma, doğru çarpışma,
  yanlış çarpışma, podyum). Enes'e gösterilmeden önce Codex bunlara kendi bakıp kontrol eder.
