"""Stant uygulaması: 3 ayrı deneyim arasında geçiş (içerik birleşmez), kamerasız."""
import importlib

from test_ozel import C, KARE, algi

S = importlib.import_module("stant_app")


def _uyg():
    return S.StantUygulama(C.Ses(acik=False))


def _kart_merkez(u, i):
    x0, y0, x1, y1 = u.menu.kartlar()[i]
    return (x0 + x1) / 2 / C.G, (y0 + y1) / 2 / C.Y


def test_menuden_el_tutarak_secilir_ve_deneyimler_ayri_kalir():
    u = _uyg()
    assert u.etkin is None and len(u.moduller) == len(S.DENEYIMLER)
    t = 1000.0
    cx, cy = _kart_merkez(u, 0)
    el = C.sahte_el(cx, cy, "avuc")
    for _ in range(45):
        t += 0.033
        u.isle(KARE(), algi([el], ["Open_Palm"]), t)
        if u.etkin is not None:
            break
    assert u.etkin == 0 and u.moduller[0].__name__ == "p_neon_kilic"
    # deneyimin kendi örneği çalışır, sonraki karelerde menü değil o işler
    for _ in range(5):
        t += 0.033
        assert u.isle(KARE(), algi(), t).shape == (C.Y, C.G, 3)
    assert type(u._ornek(0)).__module__ == "p_neon_kilic"


def test_tuslar_ve_kimse_yoksa_menuye_doner():
    u = _uyg()
    t = 2000.0
    assert u.tus(ord("3"), t) and u.etkin == 2
    assert u.tus(ord("n"), t) and u.etkin == 3
    assert u.tus(ord("b"), t) and u.etkin == 2
    assert u.tus(ord("m"), t) and u.etkin is None
    u.tus(ord("1"), t)
    for _ in range(int((S.BOS_DONUS_SN + 1) / 0.1)):
        t += 0.1
        u.isle(KARE(), algi(), t)
    assert u.etkin is None


def test_sol_alt_koseye_avuc_menuye_dondurur_ve_ornek_korunur():
    u = _uyg()
    t = 3000.0
    u.tus(ord("3"), t)
    ilk = u._ornek(2)
    # Bilek ve tüm noktalar kadrajda; eski fixture bileği ekran dışına koyuyordu.
    el = C.sahte_el(.09, .73, "avuc", olcek=.075)
    for _ in range(int((S.EV_SN + 1) / 0.033)):  # EV_SN (Enes 2026-10-12/13)
        t += 0.033
        u.isle(KARE(), algi([el], ["Open_Palm"]), t)
        if u.etkin is None:
            break
    assert u.etkin is None
    u.tus(ord("3"), t)
    assert u._ornek(2) is ilk  # rekorlar/oda ezberi kaybolmaz


def test_her_deneyim_birkac_kare_cokmeden_isler():
    u = _uyg()
    t = 4000.0
    for i in range(len(u.moduller)):
        u.sec(i, t)
        for _ in range(4):
            t += 0.033
            out = u.isle(KARE(), algi([C.sahte_el(0.5, 0.5, "isaret")], yuz=True, poz=True), t)
            assert out.shape == (C.Y, C.G, 3)


def test_grid9_sinirlar_ayrik_ve_satir_sirali():
    u = _uyg()
    kartlar = u.menu.kartlar()
    assert len(kartlar) == 9
    for x0, y0, x1, y1 in kartlar:
        assert 0 <= x0 < x1 <= C.G
        assert 0 <= y0 < y1 <= C.Y
    for r in range(3):
        for c in range(3):
            idx = r * 3 + c
            x0, y0, x1, y1 = kartlar[idx]
            if c > 0:
                prev_x0, prev_y0, prev_x1, prev_y1 = kartlar[idx - 1]
                assert x0 >= prev_x1
                assert y0 == prev_y0
            if r > 0:
                above_x0, above_y0, above_x1, above_y1 = kartlar[idx - 3]
                assert y0 >= above_y1
                assert x0 == above_x0
    for i in range(9):
        for j in range(i + 1, 9):
            ax0, ay0, ax1, ay1 = kartlar[i]
            bx0, by0, bx1, by1 = kartlar[j]
            kesisir = ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0
            assert not kesisir


def test_tuslar_dolu_karti_secer_bos_kart_degistirmez():
    u = _uyg()
    t = 5000.0
    u.tus(ord("2"), t)
    assert u.etkin == 1
    for k in range(ord("1")+len(u.moduller), ord("9") + 1):
        assert u.tus(k, t) is True
        assert u.etkin == 1
    for i in range(len(u.moduller)):
        u.tus(ord("m"), t)
        for _ in range(2):
            if u.menu.sayfa == i // 9:
                break
            u.tus(ord("n"), t)
        assert u.menu.sayfa == i // 9
        assert u.tus(ord("1") + i % 9, t) is True
        assert u.etkin == (None if i in u.kapali else i)
    u.tus(ord("m"), t)
    for k in range(ord("1") + len(u.moduller) % 9, ord("9") + 1):
        assert u.tus(k, t) is True
        assert u.etkin is None


def test_kapali_oyun_menude_durur_ama_acilmaz(monkeypatch):
    # Enes 2026-10-13: kapalı kart soluk dursun, açılmasın (tuş, el, n/b ile de). TKM artık menüde
    # değil; mekanizma ortadaki bir kartla sınanır.
    tkm = S.DENEYIMLER.index("p_refleks")
    monkeypatch.setattr(S, "KAPALI", {"p_refleks"})
    u = _uyg()
    assert u.kapali == {tkm} and u.menu.adlar[tkm]
    u.tus(ord("1") + tkm, 6000.0)
    assert u.etkin is None
    cx, cy = _kart_merkez(u, tkm)
    t = 6000.0
    for _ in range(90):
        t += 0.033
        u.isle(KARE(), algi([C.sahte_el(cx, cy, "avuc")], ["Open_Palm"]), t)
    assert u.etkin is None
    u.tus(ord("1") + tkm - 1, t)
    u.tus(ord("n"), t)
    assert u.etkin == tkm + 1
    u.tus(ord("b"), t)
    assert u.etkin == tkm - 1


def test_bos_karta_avuc_secim_yapmaz():
    u = S.StantUygulama(C.Ses(acik=False), [importlib.import_module(n) for n in S.DENEYIMLER[:3]])
    cx, cy = _kart_merkez(u, len(u.moduller))
    t = 6000.0
    el = C.sahte_el(cx, cy, "avuc")
    for _ in range(50):
        t += 0.033
        u.isle(KARE(), algi([el], ["Open_Palm"]), t)
    assert u.etkin is None
    assert u.menu.uzerinde is None


def test_menu_numaralar_cizilir(monkeypatch):
    u = _uyg()
    yazilar = []
    orijinal = S.yazi_koy

    def sahte_yazi(kare, metin, *args, **kwargs):
        yazilar.append(str(metin))
        return orijinal(kare, metin, *args, **kwargs)

    monkeypatch.setattr(S, "yazi_koy", sahte_yazi)
    out = u.isle(KARE(), algi(), 100.0)
    assert out.shape == (C.Y, C.G, 3)
    assert "1" in yazilar and "2" in yazilar and "3" in yazilar


def test_sol_alt_koseye_sarkan_el_menuye_atmaz():
    # Enes 2026-10-12: maske değiştirirken aşağıda duran el (jest yok / yumruk) menüye atıyordu
    u = _uyg()
    t = 3000.0
    u.tus(ord("3"), t)
    el = C.sahte_el(.09, .73, "avuc", olcek=.075)
    for i in range(90):
        t += 0.033
        u.isle(KARE(), algi([el], [None]), t)
    assert u.etkin == 2


def test_maske_butun_maskeler_filtreli_akista_cokmez():
    # 2026-10-12: filtreli (numpy float64) yüz noktaları Dev Gözler'de cv2.remap'i çökertip menüye atıyordu
    import os, gezgin
    u = _uyg()
    t = 7000.0
    i = S.DENEYIMLER.index("p_maske")
    u.tus(ord("1") + i, t)
    p = u._ornek(i)
    hata = gezgin.HATA_DOSYASI
    once = hata.stat().st_size if hata.exists() else 0
    for _ in range(len(p.MASKELER)):
        u.tus(32, t)  # boşluk: sonraki maske
        for _ in range(6):
            t += 0.066
            a = algi([C.sahte_el(.55, .62, "avuc")], [None])
            a.yuzler, a.blend = [C.sahte_yuz()], [{"jawOpen": .6, "browInnerUp": .5}]
            u.isle(KARE(), a, t)
            assert u.etkin == i, f"maske oyunu kapandı (maske {p.takipler[0].maske_idx if p.takipler else '?'})"
    assert (hata.stat().st_size if hata.exists() else 0) == once


def test_yeni_oyun_tek_cokmede_ayni_kartta_yenilenir(monkeypatch):
    import gezgin
    monkeypatch.setattr(gezgin,'hata_kaydet',lambda e:None)
    u=_uyg();u.sec(3,8000.)
    p=u._ornek(3)
    monkeypatch.setattr(p,'isle',lambda *a:(_ for _ in ()).throw(ValueError('sentetik')))
    u.isle(KARE(),algi(),8000.1)
    assert u.etkin==3 and u._ornek(3) is not p


def test_uc_cokme_on_saniyede_menu_ve_gecici_uyari(monkeypatch):
    import gezgin
    monkeypatch.setattr(gezgin,'hata_kaydet',lambda e:None)
    u=_uyg();u.sec(3,9000.)
    for j in range(3):
        monkeypatch.setattr(u._ornek(3),'isle',lambda *a:(_ for _ in ()).throw(ValueError('sentetik')))
        u.isle(KARE(),algi(),9000.+j)
    assert u.etkin is None and u.dinlenme_t==9002.
    calls=[];monkeypatch.setattr(S,'yazi_koy',lambda k,m,*a,**kw:calls.append(m))
    u.isle(KARE(),algi(),9003.)
    assert 'Bu oyun dinleniyor' in calls
    calls.clear();u.isle(KARE(),algi(),9004.1)
    assert 'Bu oyun dinleniyor' not in calls


def test_her_kartin_kendi_cizilmis_ikonu_var():
    import numpy as np
    fonk = [S.ikon_kus, S.ikon_yagmur, S.ikon_duello, S.ikon_tkm, S.ikon_penalti, S.ikon_ciz, S.ikon_hayalet_klon]
    for f in fonk:
        ik = f()
        assert ik.shape == (200, 200, 4) and ik.dtype == np.uint8
        assert (ik[:, :, 3] > 0).mean() > .05, f.__name__  # boş tuval değil
        p = ik[:, :, :3].max(axis=2)
        kenar = np.concatenate([p[:2].ravel(), p[-2:].ravel(), p[:, :2].ravel(), p[:, -2:].ravel()])
        assert f is S.ikon_kus or (kenar > 200).mean() < .02, f.__name__  # çizim tuvalden taşmıyor (kuşta borular bilerek kenarda)
    imzalar = {f().tobytes()[:4000:7] for f in fonk}
    assert len(imzalar) == len(fonk)
    u = S.StantUygulama(C.Ses(acik=False))
    for i, ad in enumerate(S.DENEYIMLER):
        assert u.menu.ikonlar[i].shape[2] == 4, ad
    yedek = S._tuval()
    assert all(not np.array_equal(ik[:, :, :3], yedek[0]) for ik in u.menu.ikonlar)


def test_parmak_uclari_neon_cizilir_ve_iz_tutulur():
    import numpy as np
    el = C.sahte_el(0.4, 0.5)
    kare = np.zeros((C.Y, C.G, 3), np.uint8)
    izler = []
    S.parmak_izi(kare, algi([el]), izler, 0.0)
    x, y = map(int, S.px(el, 8))
    assert kare[y, x].min() > 200  # işaret parmağı ucunda beyaz çekirdek
    x, y = map(int, S.px(el, 20))
    assert kare[y, x].max() < 60  # diğer parmaklar çizilmez (Enes: tek parmak izi)
    for q in el:
        q.x += 0.02
    S.parmak_izi(np.zeros_like(kare), algi([el]), izler, 0.1)
    assert len(izler) == 1 and len(izler[0]) == 2  # aynı el: iz uzar
    S.parmak_izi(np.zeros_like(kare), algi([el]), izler, 0.5)
    assert len(izler[0]) == 1  # 0.25 sn'den eski iz düşer
    bos = np.zeros_like(kare)
    S.parmak_izi(bos, algi(), izler, 0.6)
    assert izler == [] and not bos.any()  # el yoksa hiçbir şey çizilmez


def test_parmak_izi_kendi_cizenler_disinda_her_oyunda(monkeypatch):
    cagri = []
    monkeypatch.setattr(S, "parmak_izi", lambda kare, a, izler, simdi: cagri.append(1))
    for i, ad in enumerate(S.DENEYIMLER):
        if ad in S.KAPALI:
            continue
        u = _uyg()
        u.sec(i, 0.0)
        cagri.clear()
        u.isle(KARE(), algi([C.sahte_el(0.5, 0.5)]), 5.0)
        kendi = ad in S.KENDI_IMLECI or getattr(u.moduller[i].Prototip, "KENDI_IMLECI", False)
        assert bool(cagri) == (not kendi), ad
    assert getattr(importlib.import_module("p_cevap_yagmuru").Prototip, "KENDI_IMLECI", False)  # Enes: Bilgi Yağmuru'nda iz yok


def test_hayalet_klon_iki_eski_deneyimi_tek_kartta_sirayla_oynatir():
    # Enes 2026-10-13: TKM yerine eski Zaman Klonları + Görünmezlik Pelerini, tek oyun gibi.
    # Enes 2026-10-15: TKM menüde soluk, devre dışı kart olarak durur.
    import p_gorunmez
    import p_hayalet_klon as H
    import p_zaman_klonu
    assert "p_hayalet_klon" in S.DENEYIMLER and S.DENEYIMLER[-1] == "p_tas_kagit"
    assert S.KAPALI == {"p_tas_kagit"}
    p = H.Prototip(C.Ses(acik=False))
    assert isinstance(p.etkin, p_zaman_klonu.Prototip) and p.parcalar[1] is None  # ikinci model tembel
    t = 100.0
    for _ in range(3):
        assert p.isle(KARE(), algi(), t).shape == (C.Y, C.G, 3)
        t += 0.033
    assert isinstance(p.etkin, p_zaman_klonu.Prototip)
    t += H.Prototip.PARCA_SN
    assert p.isle(KARE(), algi(), t).shape == (C.Y, C.G, 3)
    assert isinstance(p.etkin, p_gorunmez.Prototip)  # süre dolunca pelerine geçer
    klon = p.parcalar[0]
    p.tus(ord("v"))
    assert p.etkin is klon  # V elle geri döner, aynı örnek korunur
    p.tus(32)  # boşluk etkin deneyimin kendi modunu değiştirir
    assert klon.mod == "Neon"
    assert isinstance(p.durum, str)
