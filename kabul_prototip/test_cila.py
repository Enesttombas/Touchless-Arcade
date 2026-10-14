import pytest
import math
"""Kör kabul, stant finali cila turu (PROTOTIP'e göre; diğerleri atlanır)."""
import numpy as np

from test_ozel import C, KARE, algi, baslat_avuc, sadece, yeni


@sadece("p_zaman_klonu")
def test_klon_gokkusagi_modu_ve_yanki_sayisi():
    p = yeni()
    gorulen = set()
    t = 1000.0
    for _ in range(4):
        gorulen.add(p.mod)
        p.tus(32)
        for _ in range(3):
            t += 0.033
            p.isle(KARE(), algi(), t)
    assert {"Loop", "Neon", "Klon", "Gökkuşağı"} <= gorulen
    assert isinstance(p.yanki_sayisi, int) and 3 <= p.yanki_sayisi <= 9


@sadece("p_zaman_klonu")
def test_klon_loop_me_klonlar_birikir_ve_kisi_gidince_sifirlanir():
    """TikTok Loop Me: her 2.5 sn'lik hareket döngüde oynayan klona dönüşür; klon eski yerinde görünür."""
    p = yeni()
    assert p.mod == "Loop"
    H, W = C.Y // 2, C.G // 2
    durum = {"x": 60}

    def maske():
        m = np.zeros((H, W), np.float32)
        m[80:320, durum["x"]:durum["x"] + 80] = 1.0
        return m
    p.maskeci.ver = lambda kare: maske()

    def sahne():
        k = np.full((C.Y, C.G, 3), 60, np.uint8)
        x = durum["x"] * 2
        k[160:640, x:x + 160] = (40, 200, 240)  # kişi: sarı-turuncu
        return k
    t = 1000.0
    for i in range(int(6.0 / 0.033)):  # 6 sn boyunca soldan sağa yürür
        t += 0.033
        durum["x"] = 60 + int(i * 2.0)
        cikti = p.isle(sahne(), algi(), t)
    assert len(p.loop_klipler) >= 2
    # kişi tek başına 160 px genişlikte; klonlar eski konumlarda ek kişi olarak görünür
    assert int((cikti[400, :, 2] > 150).sum()) > 2 * 160  # canlı kişiden fazlası: klonlar da görünür
    for _ in range(int(3.5 / 0.033)):  # kişi gider
        t += 0.033
        p.maskeci.ver = lambda kare: np.zeros((H, W), np.float32)
        p.isle(np.full((C.Y, C.G, 3), 60, np.uint8), algi(), t)
    assert p.loop_klipler == []


@sadece("p_neon_kilic")
def test_kilic_kombo_ve_skor_tablosu():
    p = yeni()
    assert p.kombo == 0 and p.skorlar == []
    t = baslat_avuc(p, 1000.0)
    for _ in range(40 * 31):
        t += 0.033
        p.isle(KARE(), algi(), t)
        if p.durum == "sonuc":
            break
    assert p.durum == "sonuc"
    assert len(p.skorlar) == 1 and p.skorlar[0] == p.skor


@sadece("p_gulmeme")
def test_gulmeme_geri_sayim_sonra_oyun():
    p = yeni()

    def iki():
        a = C.Algi()
        a.yuzler = [C.sahte_yuz(0.7, 0.45), C.sahte_yuz(0.3, 0.45)]
        a.blend = [{}, {}]
        return a
    durumlar, t = [], 1000.0
    for _ in range(200):
        t += 0.033
        p.isle(KARE(), iki(), t)
        if not durumlar or durumlar[-1] != p.durum:
            durumlar.append(p.durum)
        if p.durum == "oyun":
            break
    assert "geri_sayim" in durumlar and durumlar[-1] == "oyun"
    assert durumlar.index("geri_sayim") < durumlar.index("oyun")


def _iki_yuz(x1, x2, b1=None, b2=None, r1=0.12, r2=0.12):
    a = C.Algi()
    a.yuzler = [C.sahte_yuz(x1, 0.45, r1), C.sahte_yuz(x2, 0.45, r2)]
    a.blend = [dict(b1 or {}), dict(b2 or {})]
    return a


def _oyuna_gir(p, uret, t):
    for _ in range(200):
        t += 0.033
        p.isle(KARE(), uret(), t)
        if p.durum == "oyun":
            return t
    raise AssertionError(p.durum)


@sadece("p_gulmeme")
def test_gulmeme_iki_oyuncu_ayni_yarida_da_oynar():
    """İki oyuncu ekranın aynı yarısında dursa da düello başlar; arkadaki küçük seyirci sayılmaz."""
    p = yeni()

    def uc():
        a = _iki_yuz(0.62, 0.86)
        a.yuzler.append(C.sahte_yuz(0.2, 0.3, 0.04))  # uzaktaki seyirci
        a.blend.append({"mouthSmileLeft": 0.9, "mouthSmileRight": 0.9})
        return a
    t = _oyuna_gir(p, uc, 1000.0)
    for _ in range(40):  # uzaktaki seyirci gülüyor: oyun sürer
        t += 0.033
        p.isle(KARE(), uc(), t)
    assert p.durum == "oyun"


@sadece("p_gulmeme")
def test_goz_kirpma_kapali_tuslar_gulmede_birakir():
    p = yeni()
    for k in (32, ord("k"), ord("K")):
        p.tus(k)
        assert p.mod == "Gülme" and "gülen" in p.ACIKLAMA


@sadece("p_gulmeme")
def test_goz_kirpma_modu_ilk_kirpan_kaybeder():
    p = yeni()
    p.MODLAR = ("Gülme", "Göz Kırpma"); p.rekorlar["Göz Kırpma"] = 0.0
    p.tus(32)
    assert p.mod == "Göz Kırpma"
    acik = {"eyeBlinkLeft": 0.1, "eyeBlinkRight": 0.1, "mouthSmileLeft": 0.9, "mouthSmileRight": 0.9}
    t = _oyuna_gir(p, lambda: _iki_yuz(0.3, 0.7, acik, acik), 1000.0)
    for _ in range(20):  # gülmek bu modda kaybettirmez
        t += 0.033
        p.isle(KARE(), _iki_yuz(0.3, 0.7, acik, acik), t)
    assert p.durum == "oyun"
    kirp = dict(acik, eyeBlinkLeft=0.85, eyeBlinkRight=0.85)
    for _ in range(3):  # sağdaki 3 kare (~0.1 sn) göz kırpar
        t += 0.033
        p.isle(KARE(), _iki_yuz(0.3, 0.7, acik, kirp), t)
    assert p.durum == "sonuc" and p.kaybeden == "sag"


@sadece("p_gulmeme")
def test_gulme_ve_goz_kirpma_ayri_mod_tusla_gecer_kendiliginden_degismez():
    p = yeni()
    p.MODLAR = ("Gülme", "Göz Kırpma"); p.rekorlar["Göz Kırpma"] = 0.0
    t = 1000.0
    for _ in range(int(25 / 0.033)):  # kimse yokken 25 sn: mod kendiliğinden değişmez
        t += 0.033
        p.isle(KARE(), algi(), t)
    assert p.mod == "Gülme" and "gülen" in p.ACIKLAMA
    p.tus(ord("k"))
    assert p.mod == "Göz Kırpma" and "kırpan" in p.ACIKLAMA
    p.tus(ord("k"))
    assert p.mod == "Göz Kırpma"
    p.tus(ord("g"))
    assert p.mod == "Gülme"
    p.tus(32)
    assert p.mod == "Göz Kırpma"
    # Gülme modunda göz kırpmak kaybettirmez
    p.tus(ord("g"))
    acik = {"eyeBlinkLeft": 0.1, "eyeBlinkRight": 0.1, "mouthSmileLeft": 0.05, "mouthSmileRight": 0.05}
    t = _oyuna_gir(p, lambda: _iki_yuz(0.3, 0.7, acik, acik), t)
    kirp = dict(acik, eyeBlinkLeft=0.95, eyeBlinkRight=0.95)
    for _ in range(30):
        t += 0.033
        p.isle(KARE(), _iki_yuz(0.3, 0.7, kirp, kirp), t)
    assert p.durum == "oyun"


@sadece("p_gulmeme")
def test_goz_kirpma_dogal_dar_goz_aninda_elenmez():
    """Gözü doğal olarak kısık (blink 0.5) oyuncu taban ölçümüyle hemen kaybetmez; gerçek kırpışta kaybeder."""
    p = yeni()
    p.MODLAR = ("Gülme", "Göz Kırpma"); p.rekorlar["Göz Kırpma"] = 0.0
    p.tus(ord("k"))
    dar = {"eyeBlinkLeft": 0.5, "eyeBlinkRight": 0.5}
    acik = {"eyeBlinkLeft": 0.1, "eyeBlinkRight": 0.1}
    t = _oyuna_gir(p, lambda: _iki_yuz(0.3, 0.7, dar, acik), 1000.0)
    for _ in range(30):
        t += 0.033
        p.isle(KARE(), _iki_yuz(0.3, 0.7, dar, acik), t)
    assert p.durum == "oyun"
    for _ in range(4):
        t += 0.033
        p.isle(KARE(), _iki_yuz(0.3, 0.7, {"eyeBlinkLeft": 0.95, "eyeBlinkRight": 0.95}, acik), t)
    assert p.durum == "sonuc" and p.kaybeden == "sol"


@sadece("p_gorunmez")
def test_gorunmez_kisi_cikmadan_oda_ezberlenir_ve_uc_mod():
    p = yeni()
    m = np.zeros((360, 640), np.float32)
    m[120:240, 260:380] = 1.0  # kadrajdan hiç çıkmayan kişi (%6)
    p.maskeci.ver = lambda kare: m
    t = 1000.0
    for _ in range(40):
        t += 0.033
        p.isle(KARE(), algi(), t)
        if p.plaka_hazir:
            break
    assert p.plaka_hazir, f"kapsama={getattr(p, 'kapsama', None)}"
    assert 0.9 <= p.kapsama <= 1.0
    gorulen = set()
    for _ in range(4):
        gorulen.add(p.mod)
        p.tus(32)
        for _ in range(3):
            t += 0.033
            p.isle(KARE(), algi(), t)
    assert {"Pelerin", "Hayalet", "Uçan Kafa"} <= gorulen


@sadece("p_maske")
def test_maske_eski_sekiz_korunur_populer_eklendi():
    p = yeni()
    eski = ["Kral", "Havalı", "Kedi", "Şeytan", "Uzaylı", "Korsan", "Ayıcık", "Kalp Göz"]
    assert all(m in p.MASKELER for m in eski)
    assert len(p.MASKELER) >= 13 and p.MASKELER[0] == "Köpek"


@sadece("p_maske")
def test_maske_bas_egme_degistirir_el_sallama_degistirmez():
    p = yeni()
    t = 1000.0

    def yuz(egim=0.0):
        a = algi(yuz=True, blend={})
        lm = a.yuzler[0]
        cx, cy = lm[1].x, lm[1].y
        c, s_ = math.cos(egim), math.sin(egim)
        for n in lm:  # yüzü burun etrafında döndür (ayna görüntüde sağa eğme = pozitif açı)
            dx, dy = (n.x - cx) * C.G, (n.y - cy) * C.Y
            n.x, n.y = cx + (dx * c - dy * s_) / C.G, cy + (dx * s_ + dy * c) / C.Y
        return a
    for _ in range(10):
        t += 0.033
        p.isle(KARE(), yuz(), t)
    ilk = list(p.maskeler)
    for _ in range(15):
        t += 0.033
        p.isle(KARE(), yuz(0.5), t)
    ikinci = list(p.maskeler)
    assert ikinci != ilk  # Enes 2026-10-12: baş eğme maskeyi değiştirir
    for _ in range(15):  # eğik kalmak tekrar değiştirmez
        t += 0.033
        p.isle(KARE(), yuz(0.5), t)
    assert list(p.maskeler) == ikinci
    for i in range(6):  # el yüzün önünde hızla kayar: sonraki maske
        t += 0.033
        a = yuz()
        a.eller = [C.sahte_el(0.75 - i * 0.07, 0.5, "avuc")]
        a.jestler = [None]
        p.isle(KARE(), a, t)
    assert list(p.maskeler) == ikinci


def _maske_idx(p):
    return p.MASKELER.index(p.maskeler[0])


@sadece("p_maske")
def test_maske_el_sallama_ileri_geri_degistirmez():
    """Gerçek sallama (sağ-sol-sağ-sol, bulanıklıkla düşen karelerle) maskeyi bir kez ilerletir; geri almaz."""
    p = yeni()
    t = 1000.0
    for _ in range(6):
        t += 0.05
        p.isle(KARE(), algi(yuz=True, blend={}), t)
    ilk = _maske_idx(p)
    xs = [0.55, 0.62, 0.70, None, 0.74, 0.66, 0.57, 0.50, None, 0.58, 0.67, 0.73, 0.65, 0.56, 0.50]
    for x in xs:  # ~20 fps
        t += 0.05
        a = algi(yuz=True, blend={})
        if x is not None:
            a.eller, a.jestler = [C.sahte_el(x, 0.35, "avuc")], [None]
        p.isle(KARE(), a, t)
    assert _maske_idx(p) == ilk
    for _ in range(10):  # el durur: yeni sallama kabul edilir
        t += 0.05
        a = algi(yuz=True, blend={})
        a.eller, a.jestler = [C.sahte_el(0.50, 0.35, "avuc")], [None]
        p.isle(KARE(), a, t)
    for x in (0.58, 0.66, 0.74):
        t += 0.05
        a = algi(yuz=True, blend={})
        a.eller, a.jestler = [C.sahte_el(x, 0.35, "avuc")], [None]
        p.isle(KARE(), a, t)
    assert _maske_idx(p) == ilk


@sadece("p_maske")
def test_maske_kas_kaldirma_degistirmez():
    p = yeni()
    t = 1000.0
    for _ in range(30):  # bu kişinin kaşı doğal olarak biraz yukarıda (0.2)
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"browInnerUp": 0.2}), t)
    ilk = _maske_idx(p)
    for _ in range(30):  # 1 sn kaş yukarıda: tek değişim
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"browInnerUp": 0.8}), t)
    assert _maske_idx(p) == ilk  # kaş yalnız efekt
    for _ in range(10):
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"browInnerUp": 0.15}), t)
    for _ in range(10):
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"browOuterUpLeft": 0.7, "browOuterUpRight": 0.7}), t)
    assert _maske_idx(p) == ilk


@sadece("p_maske")
def test_maske_ok_dugmesine_el_tutmak_degistirir():
    p = yeni()
    t = 1000.0
    for _ in range(5):
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={}), t)
    ilk = _maske_idx(p)
    sx, sy = p._dugme_merkez(1)
    for _ in range(30):  # sağ oka 1 sn el: bir kez sonraki
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(sx / C.G, sy / C.Y - 0.1, "avuc")], [None], yuz=True, blend={}), t)
    assert _maske_idx(p) == (ilk + 1) % len(p.MASKELER)
    lx, ly = p._dugme_merkez(-1)
    for _ in range(30):  # sol ok: önceki
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(lx / C.G, ly / C.Y - 0.1, "avuc")], [None], yuz=True, blend={}), t)
    assert _maske_idx(p) == ilk


@sadece("p_maske")
def test_maske_tum_maskeler_cizilir_ve_hizli():
    import time
    p = yeni()
    t = 1000.0
    sureler = []
    for i in range(len(p.MASKELER)):
        for _ in range(8):
            t += 0.033
            a = algi(yuz=True, blend={"jawOpen": 0.6})
            t0 = time.perf_counter()
            cikti = p.isle(KARE(), a, t)
            sureler.append(time.perf_counter() - t0)
        assert cikti.shape == (C.Y, C.G, 3)
        p._degistir(p.takipler[0], 1, t)
    sureler.sort()
    assert sureler[len(sureler) // 2] < 0.03, sureler[len(sureler) // 2]


@sadece("p_maske")
def test_maske_kisa_kirpma_ve_avuc_ac_kapa_degistirmez():
    p = yeni()
    t = 1000.0
    for _ in range(5):
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={}), t)
    ilk = list(p.maskeler)
    for _ in range(7):  # ~0.23 sn tek göz kırpma
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"eyeBlinkLeft": 0.8, "eyeBlinkRight": 0.1}), t)
    ikinci = list(p.maskeler)
    assert ikinci == ilk
    for jest in ["Open_Palm"] * 4 + ["Closed_Fist"] * 2:
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.5, 0.5, "avuc")], [jest], yuz=True, blend={}), t)
    assert list(p.maskeler) == ikinci  # avuç tetiği varsayılan kapalı (Enes 2026-10-12: kaş değiştirir)


@sadece("p_neon_kilic")
def test_kilic_meme_modu_secilir_ve_memeler_ucar():
    p = yeni()
    assert p.mod == "meyve" and len(p.meyve_tam) >= 12
    t = 1000.0
    for _ in range(50):  # avuç sağ kartın üstünde: meme modu seçilip başlar
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.8, 0.55, "avuc")], ["Open_Palm"]), t)
    assert p.durum == "oyun" and p.tur_modu == "meme"
    assert len(p.meyve_tam) >= 30
    for _ in range(90):
        t += 0.033
        p.isle(KARE(), algi(), t)
    assert any(not m.bomba for m in p.meyveler)


@sadece("p_neon_kilic")
def test_kilic_iki_kisinin_avucu_iki_kartta_secim_ziplamaz():
    """Biri Meyve'de biri Meme'de avuç tutarsa seçim zıplamaz; seçili kart dolar ve oyun başlar."""
    p = yeni()
    if not p.memeler:
        pytest.skip("meme görselleri yok")
    t = 1000.0
    for _ in range(int(2.2 / 0.033)):
        t += 0.033
        eller = [C.sahte_el(0.27, 0.45, "avuc"), C.sahte_el(0.73, 0.45, "avuc")]
        p.isle(KARE(), algi(eller, ["Open_Palm", "Open_Palm"]), t)
    assert p.durum == "oyun" and p.tur_modu == "meyve"


@sadece("p_neon_kilic")
def test_kilic_jest_tanınmasa_da_kart_secilir_ve_geri_donulur():
    """Jest 'None'/yumruk olsa bile el hangi kartın üstündeyse o seçilir; Meme -> Meyve -> Meme takılmadan gider.
    Yanda sarkan el (kartın altı) oyun başlatmaz."""
    p = yeni()
    if not p.memeler:
        pytest.skip("meme görselleri yok")
    t = 1000.0
    for x, beklenen in ((0.73, "meme"), (0.27, "meyve"), (0.73, "meme"), (0.27, "meyve")):
        for _ in range(10):
            t += 0.033
            p.isle(KARE(), algi([C.sahte_el(x, 0.45, "yumruk")], [None]), t)
        assert p.mod == beklenen and p.durum == "bekle"
    for _ in range(int(3.0 / 0.033)):  # el aşağıda sarkıyor
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.27, 0.85, "yumruk")], [None]), t)
    assert p.durum == "bekle"
    for _ in range(int(1.7 / 0.033)):  # meme kartında jestsiz el 1.5 sn: meme turu başlar
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.73, 0.45, "isaret")], [None]), t)
    assert p.durum == "oyun" and p.tur_modu == "meme"


@sadece("p_neon_kilic")
def test_kilic_meyve_turundan_sonra_meme_secilebilir():
    """Hata: avuç meyve kartından meme kartına kayarken dolum sürüyor, oyun yine meyveyle başlıyordu."""
    p = yeni()
    t = 1000.0
    for _ in range(50):  # meyve turu başlar
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.2, 0.55, "avuc")], ["Open_Palm"]), t)
    assert p.durum == "oyun" and p.tur_modu == "meyve"
    while p.durum != "bekle":  # tur ve sonuç ekranı biter, oyuncu eli havada tutar
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.2, 0.55, "avuc")], ["Open_Palm"]), t)
    for _ in range(30):  # 1 sn meyve kartında: dolum başlar ama bitmez
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.2, 0.55, "avuc")], ["Open_Palm"]), t)
    assert p.durum == "bekle"
    for _ in range(60):  # meme kartına geçer
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.8, 0.55, "avuc")], ["Open_Palm"]), t)
        if p.durum == "oyun":
            break
    assert p.durum == "oyun" and p.tur_modu == "meme"
