"""Kör kabul, 3. tur oyunları (PROTOTIP'e göre; diğerleri atlanır)."""
from test_ozel import C, KARE, algi, sadece, yeni


@sadece("p_balon")
def test_balon_parmakla_patlar_sure_bitince_sonuc():
    p = yeni()
    assert p.durum == "bekle"
    t = 1000.0
    for _ in range(45):  # yüz 1 sn görünür: oyun başlar
        t += 0.033
        p.isle(KARE(), algi(yuz=True), t)
    assert p.durum == "oyun"
    hedef = None
    for _ in range(150):
        t += 0.033
        p.isle(KARE(), algi(), t)
        uygun = [b for b in p.balonlar if b.tur != "bomba" and 80 < b.y < C.Y - 80 and 80 < b.x < C.G - 80]
        if uygun:
            hedef = uygun[0]
            break
    assert hedef is not None, "5 sn içinde patlatılacak balon çıkmadı"
    once = p.skor
    for _ in range(3):  # işaret ucu (ve başparmak, olcek küçük) balonun içinde
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(hedef.x / C.G, hedef.y / C.Y, "isaret", olcek=0.01)]), t)
    assert hedef not in p.balonlar and p.skor > once
    for _ in range(50 * 31):
        t += 0.033
        p.isle(KARE(), algi(), t)
        if p.durum == "sonuc":
            break
    assert p.durum == "sonuc"


@sadece("p_cizim_fizik")
def test_cizim_rampa_toplari_tutar_avuc_siler():
    p = yeni()
    assert p.durum == "bekle"
    t = 1000.0
    for i in range(30):  # y=0.6'da soldan sağa yatay çizgi (x 256..998 px)
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.2 + 0.02 * i, 0.6, "isaret")]), t)
    assert p.durum == "oyun" and len(p.cizgiler) >= 3
    gecen, goruldu = [], 0
    for _ in range(150):  # toplar düşer, çizginin altına geçmemeli
        t += 0.033
        p.isle(KARE(), algi(), t)
        orta = [b for b in p.toplar if 320 < b.x < 930]
        goruldu += len(orta)
        gecen += [b.y for b in orta if 0.6 * C.Y + 12 < b.y < 0.6 * C.Y + 120]
    assert goruldu > 0, "çizgi üstüne top düşmedi"
    assert not gecen, f"top çizgiden geçti: {gecen[:3]}"
    for _ in range(30):  # avuç 1 sn: silinir
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.5, 0.5, "avuc")], ["Open_Palm"]), t)
    assert len(p.cizgiler) == 0


@sadece("p_maske")
def test_maske_her_yuze_farkli_bosluk_degistirir():
    p = yeni()

    def iki():
        a = C.Algi()
        a.yuzler = [C.sahte_yuz(0.3, 0.45), C.sahte_yuz(0.7, 0.45)]
        a.blend = [{}, {}]
        return a
    t = 1000.0
    for _ in range(10):
        t += 0.033
        p.isle(KARE(), iki(), t)
    assert len(p.maskeler) == 2 and p.maskeler[0] != p.maskeler[1]
    assert all(m in p.MASKELER for m in p.maskeler)
    once = list(p.maskeler)
    p.tus(32)
    for _ in range(15):
        t += 0.033
        p.isle(KARE(), iki(), t)
    assert p.maskeler != once
    t += 0.033
    p.isle(KARE(), algi(), t)
    assert len(p.maskeler) == 2  # tek kare kaçırma: maske son konumda tutulur, titremez
    for _ in range(15):  # 0.5 sn yüz yok: maske düşer
        t += 0.033
        p.isle(KARE(), algi(), t)
    assert p.maskeler == []


@sadece("p_kaleydoskop")
def test_kaleydoskop_mod_bosluk_ile_degisir():
    p = yeni()
    assert p.mod in (6, 8, 12)
    once = p.mod
    p.tus(32)
    p.isle(KARE(), algi(yuz=True), 1000.0)
    assert p.mod in (6, 8, 12) and p.mod != once
