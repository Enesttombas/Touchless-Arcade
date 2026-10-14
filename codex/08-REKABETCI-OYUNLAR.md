# 08. Rekabetçi oyunlar: Gülme Düellosu'nun kardeşleri (Fikir 6)

Enes: "İnsanların gülmeme challenge'ı çok hoşuna gitti. O tarz rekabetçi başka ne yapılabilir?"

## Gülme Düellosu neden tuttu (tasarım ilkesi buradan çıkar)
1. **Kural bir cümle:** "Gülen kaybeder." Okumadan anlaşılır.
2. **Rakip insan, yanında:** iki kişi omuz omuza. Seyirci de hakem gibi tarafını tutar.
3. **Seyirci için komik:** oyuncunun yüzü oyunun kendisi. İzleyen de eğlenir.
4. **Kısa ve kesin bitiş:** 10–40 sn, tek an kazananı belirler.
5. **Algı affedici:** ifade/jest ayrık olay. Birkaç yüz ms gecikme sonucu değiştirmez.

Aşağıdaki her öneri bu beş ilkeye göre puanlandı (5 = hepsini karşılıyor). Kamera hattı gecikmeli
olduğu için (00) refleksi ms'ye bağlı oyunlarda **adil zamanlama** kuralı var: iki oyuncu aynı karede
ölçülür, ikisi de aynı gecikmeyi yer. Kazananı karşılaştırma belirler, mutlak süre değil.

## Önerilen ilk dört (bu sırayla yap)

### A. Kovboy Düellosu (`p_refleks.py`), puan 5
- İki oyuncu yan yana, elleri belde. Ekranda western sahnesi, ıslık ve rüzgâr sesi.
- Rastgele 2–6 sn sonra "ATEŞ!" yazar ve silah sesi gelir. İlk **parmak tabanca** jestini yapan
  (işaret ileri, başparmak yukarı; ya da sadece elini belden göğüs yüksekliğine kaldırma) kazanır.
- **Erken çeken** (sinyalden önce el kalkar) anında kaybeder. Bu, tahminle oynamayı cezalandırır
  ve seyirciye en komik anı verir.
- Adil zamanlama: sinyalin çizildiği kare indeksi `k0`, her oyuncunun tetik karesi `k1`. Fark kare
  sayısı × kare süresi tepki süresidir. Eşitlikte (aynı kare) tekrar.
- Kazananın tepki süresi büyük yazılır: "0.31 sn". Oturum rekoru tutulur.
- Algı: `el` (iki oyuncu). Oyuncu Kapısı ve kimlik takibi (01 §2, §4) her eli konumuna göre sol/sağ oyuncuya bağlar.
- Tek kişi modu: kişi YZ kovboya karşı. YZ tepki süresi her raunt kısalır (0.6 → 0.35 sn).

### B. Taş-Kağıt-Makas Turnuvası (`p_tas_kagit.py`), puan 4
- `gesture_recognizer.task` hazır jestleri: `Closed_Fist` = taş, `Open_Palm` = kağıt, `Victory` = makas.
- "Taş… kağıt… makas… ŞİMDİ!" Geri sayım sesle. "ŞİMDİ" anından sonraki 0.4 sn içinde en yüksek
  skorla görülen jest geçerli. Daha önce gösterilen jest sayılmaz (hile önleme).
- Mod 1: iki insan, 3'te 2 alan. Mod 2: insan vs YZ. YZ ilk turlarda rastgele, sonra oyuncunun
  son 5 seçiminden basit bir frekans modeliyle tahmin eder. Ekranda "YZ seni okuyor: %62" yazar.
  Hocaya "insanlar rastgele değil" mesajı verir.
- Jest güveni < 0.6 ise "tekrar" denir, puan verilmez.

### C. Duvardaki Delik (`p_duvar_delik.py`), puan 5
- Kinect'in *Hole in the Wall*'u (`ARASTIRMA-KAYNAKLAR.md`). Uzaktan bir duvar yaklaşır, duvarda
  insan şeklinde bir delik var (yıldız, T-pozu, tek ayak, çömelme, eğik).
- Duvar oyuncuya ulaştığında oyuncunun maskesi deliğin içinde mi diye bakılır:
  `uyum = |maske ∩ delik| / |maske|` ve taşma = `|maske \ delik| / |maske|`.
  Uyum ≥ 0.85 ve taşma ≤ 0.15 ise geçer, duvar oyuncunun içinden geçip parçalanır. Değilse duvar
  oyuncuyu "iter": ekran sarsılır, puan yok.
- Delik şekilleri poz şablonlarından üretilir (17 eklem → kalın çizgilerle insan silüeti). Kişinin
  boyuna göre ölçeklenir (omuz genişliği). Uzun ya da kısa kişi haksızlığa uğramaz.
- İki oyuncu: iki delikli duvar, aynı anda. Ya da tek büyük delik, iki kişi birlikte sığar (iş birliği modu).
- Duvar en az 3 sn önceden görünür; gecikmeye toleranslı.
- Algı: `poz` + `Maskeci` (02 §1.3 iyileştirilmiş maske tercih).

### D. Heykel / Kırmızı Işık (`p_heykel.py`), puan 4
- Müzik çalar, herkes dans eder. Müzik **kesilince** herkes donar. 2 sn içinde hareket eden elenir.
- Hareket ölçüsü: poz eklemlerinin (omuz, dirsek, bilek, kalça) filtreli hızının ortalaması, gövde
  boyuna oranlı. Kare farkı (`absdiff`) **kullanma**: kalabalıkta arkadan geçen kişi oyuncuyu eler.
  Eşik, oyun başındaki 2 sn "dur" kalibrasyonunda ölçülen titreşimin 3 katı.
- Müzik kesilmesinden sonra 0.6 sn tolerans. Kesilme anı rastgele.
- Çok kişili (4 kişiye kadar), elenen kişinin silüeti griye döner ve "taş kesildi" efekti alır.
- Son kalan kazanır. Seyirci çok güler: dondukları pozlar komik.

## Diğer adaylar (değerlendirildi, sonraya)

| Oyun | Fikir | Puan | Not |
|---|---|---|---|
| Göz Kırpmama | Önce kırpan kaybeder | 5 | **Zaten var** (Gülme oyunundaki Göz Kırpma modu). Ayrı oyun yapma |
| İfade Taklidi | Ekrandaki emojiyi ilk taklit eden (blendshape benzerliği) | 4 | `p_ifade_oyunu.py` var. Düello moduna çevir: iki kişi aynı emoji |
| Ağızla Yakala | Düşen meyveyi ağzı açarak yakala (`jawOpen`) | 3 | Komik ama tek kişide sıkıcı. İki kişi aynı yağmurda yarışırsa 4 |
| Yanak Şişirme | En uzun süre `cheekPuff` tutabilen | 3 | Blendshape gürültülü olabilir. Önce ölç |
| Kafa Topu Voleybolu | Kafayla topu karşı sahaya | 4 | `p_kafa_topu.py` var. İki kişilik file eklenirse güçlü |
| Halat Çekme | İki takım el sallayarak (hız toplamı) halat çeker | 4 | Çok kişi, kalabalık enerjisi. Kimlik takibi şart |
| Ali Baba Dedi Ki | "Ali Baba dedi ki: kolunu kaldır" | 3 | Poz sınıflandırması gerekir. Dil komik ama tempo yavaş |
| Ayna Ayna | Biri poz verir, öbürü 3 sn içinde kopyalar (poz benzerliği) | 4 | 08-C'deki poz şablon kodunu paylaşır |

## Ortak altyapı (yeni kod oyuna değil buraya)
- `rekabet.py`: iki/çok oyuncu yuvası (sol/sağ ya da kimlik), raunt sayacı, "3'te 2", geri sayım,
  kazanan ilanı (konfeti + taç + isim rengi), oturum rekor tablosu. Gülme Düellosu da bu modüle taşınabilir
  (davranışı değiştirmeden, testleri koruyarak).
- **Adil zamanlama yardımcısı:** olay karesi indeksi tabanlı karşılaştırma. Duvar saati kullanma.
- **Tekrar oynatma:** kazanma anının son 1.5 sn'si bellekte halka tamponda tutulur (diske yazılmaz),
  sonuç ekranında ağır çekim oynatılır. Seyirci için en güçlü an bu. Gizlilik kuralına uyar.

## Kabul (`test_rekabet.py` + oyun başına, en az 12 toplam)
1. Kovboy: sinyalden önce kalkan el, o oyuncuya "erken" kaybı verir.
2. Kovboy: iki tetik farklı karede, erken olan kazanır. Aynı karede eşitlik ve tekrar.
3. Kovboy: sinyal anı 2–6 sn aralığında, tohumla tekrarlanabilir.
4. TKM: "ŞİMDİ"den önce gösterilen jest sayılmaz. Sonraki 0.4 sn içindeki en yüksek skorlu jest geçerli.
5. TKM: kural tablosu (taş > makas > kağıt > taş). Düşük güvende "tekrar".
6. TKM YZ: oyuncu 5 kez taş oynarsa YZ'nin kağıt seçme oranı ≥ %60.
7. Duvar: delikle birebir aynı maske geçer. %30 taşan maske geçmez.
8. Duvar: delik şablonu kişinin omuz genişliğiyle ölçeklenir (iki farklı boyda aynı oran).
9. Heykel: dururken 3× titreşimin altında kalan oyuncu elenmez. Kolunu sallayan elenir.
10. Heykel: arkadan geçen kişi (oyuncu olmayan, kapıdan geçmemiş) kimseyi elemez.
11. Rekabet: 3'te 2. İkinci galibiyette oyun biter, kazanan doğru.
12. Tekrar tamponu en fazla 1.5 sn × FPS kare tutar, diske yazmaz.
- `--kiyas`: her oyunda isle p95 ≤ 20 ms.
