import importlib
import json
import os
import re
import sys
import numpy as np
import pytest

# meme-kamera/prototipler dizinini sys.path'e ekle
_BU_DIZIN = os.getcwd()
_PROTOTIP_DIR = os.path.abspath(os.path.join(_BU_DIZIN, "prototipler"))
_UST_PROTOTIP_DIR = os.path.abspath(os.path.join(_BU_DIZIN, "..", "prototipler"))

for _d in (_PROTOTIP_DIR, _UST_PROTOTIP_DIR):
    if os.path.isdir(_d) and _d not in sys.path:
        sys.path.insert(0, _d)


def _sayi_coz(metin: str) -> int:
    """Kart uzerindeki pozitif veya parantezli negatif sayi metnini integer'a cevirir."""
    m = metin.strip()
    if m.startswith("(") and m.endswith(")"):
        return int(m[1:-1])
    return int(m)


# ============================================================================
# 1. ISLEM DIZISI KOR TESTLERI
# ============================================================================


def test_islem_icerik_import_ve_sozlesme():
    """p_islem_dizisi modulu ve IslemIcerik sinifi sozlesmeye uygun olmali."""
    mod = importlib.import_module("p_islem_dizisi")
    assert hasattr(mod, "IslemIcerik"), "IslemIcerik sinifi bulunamadi"
    rng = np.random.default_rng(42)
    icerik = mod.IslemIcerik(rng=rng)
    assert hasattr(icerik, "uret"), "uret metodu eksik"
    assert hasattr(icerik, "dogru_mu"), "dogru_mu metodu eksik"


@pytest.mark.parametrize("tohum", [42, 123, 999])
@pytest.mark.parametrize("n", [3, 4, 5])
def test_islem_dizisi_1200_soru_toplu_gecerlilik(tohum, n):
    """3 tohum x 3 N x 1200 = 10800 soruda uretilen kanonik diziler ve kurallar dogrulanir."""
    mod = importlib.import_module("p_islem_dizisi")
    rng = np.random.default_rng(tohum)
    icerik = mod.IslemIcerik(rng=rng)

    gorulen_oplar = set()

    for soru_no in range(1200):
        kartlar = icerik.uret(n, soru_no=soru_no)

        assert isinstance(kartlar, list), "uret list dondurmelidir"
        assert len(kartlar) == n, f"Kart sayisi N={n} olmalidir, alinan: {len(kartlar)}"
        assert hasattr(icerik, "kartlar"), "uret sonrasi .kartlar niteligi bulunmali"
        assert icerik.kartlar == kartlar
        assert hasattr(icerik, "op"), "uret sonrasi .op niteligi bulunmali"

        op = icerik.op
        gorulen_oplar.add(op)

        # Kanonik uretim dogru_mu ile True vermelidir
        assert icerik.dogru_mu(kartlar) is True, f"Kanonik kartlar dogru_mu olmadi: {kartlar} (op: {op})"

        # A, B, C ayiklama sozlesmesi:
        # N=3: [A, B, C], op ve = ekranda sabit, .op'tan alinir
        # N=4: [A, op, B, C], = ekranda sabit
        # N=5: [A, op, B, '=', C]
        if n == 3:
            a_str, b_str, c_str = kartlar[0], kartlar[1], kartlar[2]
        elif n == 4:
            a_str, b_str, c_str = kartlar[0], kartlar[2], kartlar[3]
            assert kartlar[1] == op, f"N=4'te kartlar[1] op olmali ({kartlar[1]} != {op})"
        else:  # n == 5
            a_str, b_str, c_str = kartlar[0], kartlar[2], kartlar[4]
            assert kartlar[1] == op, f"N=5'te kartlar[1] op olmali ({kartlar[1]} != {op})"
            assert kartlar[3] == "=", f"N=5'te kartlar[3] '=' olmali ({kartlar[3]})"

        a = _sayi_coz(a_str)
        b = _sayi_coz(b_str)
        c = _sayi_coz(c_str)

        # A, B: [-100, 100]
        assert -100 <= a <= 100, f"A aralik disinda: {a}"
        assert -100 <= b <= 100, f"B aralik disinda: {b}"

        # A, B, C hepsi birbirinden farkli
        assert a != b, f"A ve B esit olamaz: {a} == {b}"
        assert a != c, f"A ve C esit olamaz: {a} == {c}"
        assert b != c, f"B ve C esit olamaz: {b} == {c}"

        # Islem ozel kurallari
        if op in ("/", "÷"):
            assert b != 0, "Bolmede payda 0 olamaz"
            assert b not in (1, -1), f"Bolmede B ±1 olamaz, alinan: {b}"
            assert c != 0, "Bolmede bolum (C) 0 olamaz"
            assert a == b * c, f"Bolme tam sayi degil ya da esitlik bozuk: {a} != {b} * {c}"
        elif op in ("*", "×"):
            assert a not in (0, 1, -1), f"Carpma carpani A 0 veya ±1 olamaz: {a}"
            assert b not in (0, 1, -1), f"Carpma carpani B 0 veya ±1 olamaz: {b}"
            assert c == a * b, f"Carpma esitligi hatali: {c} != {a} * {b}"
        elif op in ("+",):
            assert c == a + b, f"Toplama esitligi hatali: {c} != {a} + {b}"
        elif op in ("-", "−"):
            assert c == a - b, f"Cikarma esitligi hatali: {c} != {a} - {b}"

    # 4 islem de uretilmis olmali
    assert len(gorulen_oplar) >= 4, f"Dort islem kapsanmadi: {gorulen_oplar}"


def test_islem_ilk_iki_soru_negatif_sayisi_ve_ayni_op_ustuste():
    """Ilk 2 soruda en fazla 1 negatif sayi; her 5 soruluk turda ayni op ustuste max 2."""
    mod = importlib.import_module("p_islem_dizisi")
    rng = np.random.default_rng(2026)
    icerik = mod.IslemIcerik(rng=rng)

    for tur in range(100):
        op_gecmisi = []
        for soru_no in range(5):
            kartlar = icerik.uret(5, soru_no=soru_no)
            a = _sayi_coz(kartlar[0])
            b = _sayi_coz(kartlar[2])
            c = _sayi_coz(kartlar[4])
            op = kartlar[1]
            op_gecmisi.append(op)

            if soru_no < 2:
                negatif_sayisi = sum(1 for x in (a, b, c) if x < 0)
                assert negatif_sayisi <= 1, f"Ilk 2 soruda en cok 1 negatif olabilir, alinan: {a}, {b}, {c}"

        # Ayni islem ust uste en fazla 2 kez gelebilir
        for i in range(len(op_gecmisi) - 2):
            assert not (op_gecmisi[i] == op_gecmisi[i + 1] == op_gecmisi[i + 2]), (
                f"Ayni op ust uste 3 kez geldi: {op_gecmisi}"
            )


def test_islem_manuel_dogru_mu_vektorleri_n5():
    """N=5 manuel kart dizilimleri ve esitlik vektorleri testi."""
    mod = importlib.import_module("p_islem_dizisi")
    icerik = mod.IslemIcerik(rng=np.random.default_rng(1))
    icerik.kartlar = ["12", "+", "5", "=", "17"]

    # Temel kabul vektorleri
    assert icerik.dogru_mu(["12", "+", "5", "=", "17"]) is True
    assert icerik.dogru_mu(["5", "+", "12", "=", "17"]) is True  # Toplama A/B swap kabul
    assert icerik.dogru_mu(["17", "=", "12", "+", "5"]) is True  # = sol taraf kabul
    assert icerik.dogru_mu(["17", "=", "5", "+", "12"]) is True

    # Cikarma vektorleri
    icerik.kartlar = ["12", "-", "5", "=", "7"]
    assert icerik.dogru_mu(["12", "-", "5", "=", "7"]) is True
    assert icerik.dogru_mu(["5", "-", "12", "=", "7"]) is False  # Cikarma swap gecersiz
    assert icerik.dogru_mu(["7", "=", "12", "-", "5"]) is True

    # Negatif ve carpma / bolme
    icerik.kartlar = ["(-6)", "×", "(-7)", "=", "42"]
    assert icerik.dogru_mu(["(-6)", "×", "(-7)", "=", "42"]) is True
    assert icerik.dogru_mu(["(-7)", "×", "(-6)", "=", "42"]) is True
    icerik.kartlar = ["42", "÷", "(-6)", "=", "(-7)"]
    assert icerik.dogru_mu(["42", "÷", "(-6)", "=", "(-7)"]) is True
    assert icerik.dogru_mu(["(-6)", "÷", "42", "=", "(-7)"]) is False

    # Gecersiz sentaks vektorleri
    icerik.kartlar = ["12", "+", "5", "=", "17"]
    assert icerik.dogru_mu(["=", "12", "+", "5", "17"]) is False
    assert icerik.dogru_mu(["12", "5", "+", "=", "17"]) is False
    assert icerik.dogru_mu(["12", "+", "=", "5", "17"]) is False
    assert icerik.dogru_mu(["12", "+", "5", "17", "="]) is False
    assert icerik.dogru_mu(["1", "7", "=", "12", "+"]) is False


def test_islem_manuel_dogru_mu_vektorleri_n4_ve_n3():
    """N=4 (sabit =) ve N=3 (sabit op ve =) icin dogru_mu vektorleri."""
    mod = importlib.import_module("p_islem_dizisi")
    icerik = mod.IslemIcerik(rng=np.random.default_rng(2))

    # N=4: [A, op, B, C] -> A op B = C
    icerik.kartlar = ["12", "+", "5", "17"]
    assert icerik.dogru_mu(["12", "+", "5", "17"]) is True
    assert icerik.dogru_mu(["5", "+", "12", "17"]) is True
    assert icerik.dogru_mu(["12", "+", "17", "5"]) is False
    assert icerik.dogru_mu(["17", "+", "5", "12"]) is False

    icerik.kartlar = ["20", "-", "8", "12"]
    assert icerik.dogru_mu(["20", "-", "8", "12"]) is True
    assert icerik.dogru_mu(["8", "-", "20", "12"]) is False

    # N=3: [A, B, C] -> op sabit .op uzerinden eklenir
    icerik.op = "+"
    icerik.kartlar = ["9", "16", "25"]
    assert icerik.dogru_mu(["9", "16", "25"]) is True
    assert icerik.dogru_mu(["16", "9", "25"]) is True
    assert icerik.dogru_mu(["25", "9", "16"]) is False

    icerik.op = "-"
    icerik.kartlar = ["25", "9", "16"]
    assert icerik.dogru_mu(["25", "9", "16"]) is True
    assert icerik.dogru_mu(["9", "25", "16"]) is False

    icerik.op = "*"
    icerik.kartlar = ["3", "7", "21"]
    assert icerik.dogru_mu(["3", "7", "21"]) is True
    assert icerik.dogru_mu(["7", "3", "21"]) is True


# ============================================================================
# 2. CUMLE DIZISI VE VERI BANKASI KOR TESTLERI
# ============================================================================


def test_cumle_bankasi_json_semasi_ve_sayim():
    """veri/dizi_cumleler.json semasi, sayimlar ve dil kurallari."""
    json_yolu = None
    for aday in (
        os.path.join(_PROTOTIP_DIR, "veri", "dizi_cumleler.json"),
        os.path.join(_UST_PROTOTIP_DIR, "veri", "dizi_cumleler.json"),
        os.path.join(_BU_DIZIN, "veri", "dizi_cumleler.json"),
    ):
        if os.path.isfile(aday):
            json_yolu = aday
            break

    assert json_yolu is not None, "veri/dizi_cumleler.json dosyasi bulunamadi"

    with open(json_yolu, "r", encoding="utf-8") as f:
        veri = json.load(f)

    assert "cumleler" in veri, "JSON 'cumleler' anahtari icermeli"
    cumleler = veri["cumleler"]
    assert isinstance(cumleler, list)

    id_kumesi = set()
    n3_sayisi = 0
    n4_sayisi = 0
    n5_sayisi = 0

    noktalama_sonu = re.compile(r"[.!?…]$")

    for kayit in cumleler:
        # Alan sozlesmesi
        for anahtar in ("id", "kelimeler", "kabul", "konu"):
            assert anahtar in kayit, f"Eksik anahtar: {anahtar} kayitta: {kayit}"

        cid = kayit["id"]
        assert cid not in id_kumesi, f"Tekrarlanan cumle id: {cid}"
        id_kumesi.add(cid)

        kelimeler = kayit["kelimeler"]
        kabul = kayit["kabul"]
        k = len(kelimeler)

        assert 3 <= k <= 5, f"Kelime sayisi 3, 4 veya 5 olmali: {cid} (k={k})"
        if k == 3:
            n3_sayisi += 1
        elif k == 4:
            n4_sayisi += 1
        elif k == 5:
            n5_sayisi += 1

        # Kelime uzunlugu kurali: <= 12 harf
        for kelime in kelimeler:
            assert not any(c.isspace() for c in kelime), f"Kart birden cok kelime: {cid}: {kelime}"
            assert sum(c.isalpha() for c in kelime) <= 12, f"Kelime 12 harften uzun: '{kelime}' ({cid})"

        # Kabul kurallari
        assert isinstance(kabul, list) and len(kabul) > 0, f"Kabul bos olamaz: {cid}"
        kanonik_indeksler = list(range(k))
        assert kanonik_indeksler in kabul, f"Kanonik sira [0..N-1] kabul icinde olmali: {cid}"

        # Ilk kelime buyuk harf, son kelime noktalamali ipucu kurali
        ilk_kelime = kelimeler[0]
        son_kelime = kelimeler[-1]
        assert ilk_kelime[0].isupper() or ilk_kelime[0] in "İIĞÜŞÖÇ", (
            f"Kanonik ilk kelime buyuk harfle baslamali: {ilk_kelime} ({cid})"
        )
        assert noktalama_sonu.search(son_kelime), (
            f"Kanonik son kelime noktalama ile bitmeli: {son_kelime} ({cid})"
        )

        for perm in kabul:
            assert isinstance(perm, list) and len(perm) == k, f"Gecersiz perm uzunlugu: {perm} ({cid})"
            assert sorted(perm) == kanonik_indeksler, f"Permutasyon hatali: {perm} ({cid})"

            # Buyuk harfli kelime sonda, noktalama ile biten kelime basta olamaz
            assert perm[0] != (k - 1), f"Noktali kelime basta olamaz: perm={perm} ({cid})"
            assert perm[-1] != 0, f"Buyuk harfli kelime sonda olamaz: perm={perm} ({cid})"

    # Minimum sayim kurali: >= 25 (3 kelime), >= 50 (4 kelime), >= 30 (5 kelime)
    assert n3_sayisi >= 25, f"3 kelimelik cumle sayisi yetersiz: {n3_sayisi} < 25"
    assert n4_sayisi >= 50, f"4 kelimelik cumle sayisi yetersiz: {n4_sayisi} < 50"
    assert n5_sayisi >= 30, f"5 kelimelik cumle sayisi yetersiz: {n5_sayisi} < 30"


def test_cumle_icerik_import_ve_uret_dogru_mu():
    """CumleIcerik uret ve dogru_mu davranisi."""
    mod = importlib.import_module("p_cumle_dizisi")
    assert hasattr(mod, "CumleIcerik"), "CumleIcerik sinifi bulunamadi"

    icerik = mod.CumleIcerik(rng=np.random.default_rng(101))

    for n in (3, 4, 5):
        kelimeler = icerik.uret(n, soru_no=0)
        assert isinstance(kelimeler, list)
        assert len(kelimeler) == n
        assert hasattr(icerik, "kayit"), "CumleIcerik.kayit niteligi bulunmali"
        assert isinstance(icerik.kayit, dict)
        for anahtar in ("id", "kelimeler", "kabul", "konu"):
            assert anahtar in icerik.kayit

        # Kanonik sira dogru kabul edilmeli
        assert icerik.dogru_mu(kelimeler) is True

        # Gecersiz ters sira dogru kabul edilmemeli
        ters_dizi = list(reversed(kelimeler))
        # Eger ters sira kabulde yoksa False vermeli
        ters_indeksler = list(reversed(range(n)))
        if ters_indeksler not in icerik.kayit["kabul"]:
            assert icerik.dogru_mu(ters_dizi) is False


def test_cumle_icerik_tur_ici_ve_son_15_tekrar_ve_topik_kurali():
    """Tur ici 5 soruda id tekrar etmez, son 15 cumle tekrar etmez, turda ayni konu max 2."""
    mod = importlib.import_module("p_cumle_dizisi")
    icerik = mod.CumleIcerik(rng=np.random.default_rng(555))

    son_15_id = []

    for tur in range(4):
        tur_idleri = []
        tur_konulari = []

        for soru_no in range(5):
            icerik.uret(4, soru_no=soru_no)
            cid = icerik.kayit["id"]
            konu = icerik.kayit["konu"]

            # Tur ici tekrar yok
            assert cid not in tur_idleri, f"Tur icinde cumle tekrar etti: {cid}"
            tur_idleri.append(cid)
            tur_konulari.append(konu)

            # Son 15 id icinde tekrar yok
            assert cid not in son_15_id, f"Son 15 cumle kurali bozuldu: {cid} hafizada vardi"

        # Tur tamamlandi, son 15 listesini guncelle
        son_15_id.extend(tur_idleri)
        if len(son_15_id) > 15:
            son_15_id = son_15_id[-15:]

        # Ayni turda ayni konudan en fazla 2 cumle
        konu_sayilari = {}
        for k in tur_konulari:
            konu_sayilari[k] = konu_sayilari.get(k, 0) + 1
            assert konu_sayilari[k] <= 2, f"Turda ayni konudan 2'den fazla geldi: {k} (sayi: {konu_sayilari[k]})"


# ============================================================================
# 3. PROTOTIP SINIFI VE METAVERILERI KOR TESTLERI
# ============================================================================


def test_prototip_sozlesmesi_islem_dizisi():
    """p_islem_dizisi.Prototip AD, IHTIYAC, KAPI kurallari."""
    mod = importlib.import_module("p_islem_dizisi")
    assert hasattr(mod, "Prototip"), "p_islem_dizisi icinde Prototip sinifi olmali"
    proto_cls = mod.Prototip

    assert hasattr(proto_cls, "AD"), "Prototip.AD niteligi olmali"
    assert proto_cls.AD == "İşlem Dizisi"

    assert hasattr(proto_cls, "IHTIYAC"), "Prototip.IHTIYAC niteligi olmali"
    assert proto_cls.IHTIYAC == {"poz"}

    assert hasattr(proto_cls, "KAPI"), "Prototip.KAPI sozluk niteligi olmali"
    assert isinstance(proto_cls.KAPI, dict)
    assert proto_cls.KAPI.get("poz_omuz_min") == pytest.approx(0.035, abs=1e-4)


def test_prototip_sozlesmesi_cumle_dizisi():
    """p_cumle_dizisi.Prototip AD, IHTIYAC, KAPI kurallari."""
    mod = importlib.import_module("p_cumle_dizisi")
    assert hasattr(mod, "Prototip"), "p_cumle_dizisi icinde Prototip sinifi olmali"
    proto_cls = mod.Prototip

    assert hasattr(proto_cls, "AD"), "Prototip.AD niteligi olmali"
    assert proto_cls.AD == "Cümle Dizisi"

    assert hasattr(proto_cls, "IHTIYAC"), "Prototip.IHTIYAC niteligi olmali"
    assert proto_cls.IHTIYAC == {"poz"}

    assert hasattr(proto_cls, "KAPI"), "Prototip.KAPI sozluk niteligi olmali"
    assert isinstance(proto_cls.KAPI, dict)
    assert proto_cls.KAPI.get("poz_omuz_min") == pytest.approx(0.035, abs=1e-4)
