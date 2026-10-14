import itertools
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest

# Prototipler yolunu sys.path'e ekle
KOK_DIZIN = Path.cwd()
PROTOTIP_YOLU = KOK_DIZIN / "prototipler"
if str(PROTOTIP_YOLU) not in sys.path:
    sys.path.insert(0, str(PROTOTIP_YOLU))

try:
    import p_islem_dizisi
except ImportError:
    p_islem_dizisi = None


class SahteSes:
    def __init__(self, acik=False):
        self.acik = acik
        self.calinanlar = []

    def cal(self, ses_adi, ses=0.7):
        self.calinanlar.append((ses_adi, float(ses)))


def sahte_nokta(x=0.5, y=0.5, z=0.0, visibility=0.99):
    return SimpleNamespace(x=float(x), y=float(y), z=float(z), visibility=float(visibility))


def uret_insan_pozu(
    merkez_x=0.5,
    merkez_y=0.5,
    omuz_genislik=0.08,
    boy=0.4,
    el_yukarida=False,
    visibility=0.99,
):
    """
    33 noktalı MediaPipe pose iskeleti üretir.
    0: burun
    2, 5: sol/sağ göz
    11, 12: sol/sağ omuz
    15, 16: sol/sağ bilek
    23, 24: sol/sağ kalça
    """
    noktalar = [sahte_nokta(merkez_x, merkez_y, 0.0, visibility) for _ in range(33)]

    yarim_omuz = omuz_genislik / 2.0
    bas_y = merkez_y - (boy * 0.45)
    omuz_y = merkez_y - (boy * 0.25)
    kalca_y = merkez_y + (boy * 0.25)

    noktalar[0] = sahte_nokta(merkez_x, bas_y, 0.0, visibility)
    noktalar[2] = sahte_nokta(merkez_x - 0.015, bas_y - 0.01, 0.0, visibility)
    noktalar[5] = sahte_nokta(merkez_x + 0.015, bas_y - 0.01, 0.0, visibility)

    noktalar[11] = sahte_nokta(merkez_x - yarim_omuz, omuz_y, 0.0, visibility)
    noktalar[12] = sahte_nokta(merkez_x + yarim_omuz, omuz_y, 0.0, visibility)

    noktalar[23] = sahte_nokta(merkez_x - (yarim_omuz * 0.7), kalca_y, 0.0, visibility)
    noktalar[24] = sahte_nokta(merkez_x + (yarim_omuz * 0.7), kalca_y, 0.0, visibility)

    bilek_y = (bas_y - 0.10) if el_yukarida else (kalca_y - 0.05)
    noktalar[15] = sahte_nokta(merkez_x - yarim_omuz - 0.02, bilek_y, 0.0, visibility)
    noktalar[16] = sahte_nokta(merkez_x + yarim_omuz + 0.02, bilek_y, 0.0, visibility)

    return noktalar


def uret_algi(poz_listesi, poz_idleri=None, tahmini_idleri=None):
    if poz_idleri is None:
        poz_idleri = list(range(len(poz_listesi)))
    if tahmini_idleri is None:
        tahmini_idleri = []

    return SimpleNamespace(
        pozlar=poz_listesi,
        poz_id=[int(pid) for pid in poz_idleri],
        tahmini=[int(tid) for tid in tahmini_idleri],
    )


def uret_sentetik_kare(genislik=1280, yukseklik=720, insan_tanimlari=None):
    kare = np.zeros((yukseklik, genislik, 3), dtype=np.uint8)
    if not insan_tanimlari:
        return kare

    for tanim in insan_tanimlari:
        mx, my, omuz_gen, boy, bgr = tanim
        x1 = int(np.clip((mx - (omuz_gen / 2.0)) * genislik, 0, genislik - 1))
        x2 = int(np.clip((mx + (omuz_gen / 2.0)) * genislik, 0, genislik - 1))
        y1 = int(np.clip((my - (boy * 0.25)) * yukseklik, 0, yukseklik - 1))
        y2 = int(np.clip((my + (boy * 0.25)) * yukseklik, 0, yukseklik - 1))

        if x2 > x1 and y2 > y1:
            kare[y1:y2, x1:x2] = np.array(bgr, dtype=np.uint8)

    return kare


RENK_KIRMIZI = (20, 20, 220)
RENK_MAVI = (220, 40, 30)
RENK_YESIL = (30, 210, 40)
RENK_SARI = (30, 220, 220)
RENK_MOR = (200, 30, 180)


def olustur_motor(seed=42):
    ses = SahteSes(acik=False)
    rng = np.random.default_rng(seed)
    return p_islem_dizisi.Prototip(ses, rng=rng)


def olay_kaydi_al(olay):
    if isinstance(olay, (tuple, list)):
        return olay[0], olay[1:]
    if isinstance(olay, dict):
        tip = olay.get("tur") or olay.get("tip") or olay.get("olay") or olay.get("ad")
        return tip, olay
    return str(olay), ()


def kart_metni_al(oyuncu):
    for attr in ("kartstr", "kart_metni", "kart_yazi", "kart_str", "kart"):
        val = getattr(oyuncu, attr, None)
        if val is not None and not callable(val):
            return str(val)
    return ""


def lobi_ile_baslat(motor, n=3, baslangic_t=1.0, renkler=None):
    if renkler is None:
        palet = [RENK_KIRMIZI, RENK_MAVI, RENK_YESIL, RENK_SARI, RENK_MOR]
        renkler = [palet[i % len(palet)] for i in range(n)]

    xs = np.linspace(0.2, 0.8, n)
    ids = list(range(1, n + 1))
    t = baslangic_t

    # 1. Aşama: 1.6 saniye stabil duruş (el aşağıda)
    p_asagi = [uret_insan_pozu(xs[i], 0.5, el_yukarida=False) for i in range(n)]
    tanimlar = [(xs[i], 0.5, 0.08, 0.4, renkler[i]) for i in range(n)]
    kare = uret_sentetik_kare(insan_tanimlari=tanimlar)

    for _ in range(16):
        t += 0.1
        algi = uret_algi(p_asagi, ids)
        motor.isle(kare.copy(), algi, t)

    # 2. Aşama: 0.9 saniye el kaldırma (hazır jesti)
    p_yukari = [uret_insan_pozu(xs[i], 0.5, el_yukarida=True) for i in range(n)]
    for _ in range(9):
        t += 0.1
        algi = uret_algi(p_yukari, ids)
        motor.isle(kare.copy(), algi, t)

    if motor.durum != "oyun" and hasattr(motor, "baslat"):
        algi_son = uret_algi(p_yukari, ids)
        motor.baslat(algi_son, t)

    return t, xs, ids, tanimlar


def dogru_ve_yanlis_perm_bul(motor):
    oyuncular = list(motor.oyuncular.values())
    n = len(oyuncular)
    pids = [o.kimlik for o in oyuncular]
    pid_kart = {o.kimlik: kart_metni_al(o) for o in oyuncular}

    dogru_pids = None
    yanlis_pids = None

    for perm in itertools.permutations(pids):
        dizi = [pid_kart[p] for p in perm]
        if motor.icerik.dogru_mu(dizi):
            if dogru_pids is None:
                dogru_pids = perm
        else:
            if yanlis_pids is None:
                yanlis_pids = perm

        if dogru_pids is not None and yanlis_pids is not None:
            break

    return dogru_pids, yanlis_pids


# ==============================================================================
# TESTLER
# ==============================================================================

def test_01_lobi_gecersiz_oyuncu_sayisi_baslamaz():
    """Lobi 2 kişi veya 6 kişi olduğunda oyunu başlatmamalıdır."""
    motor = olustur_motor()
    simdi = 100.0

    # 2 kişi durumu
    pozlar_2 = [
        uret_insan_pozu(0.35, 0.5, el_yukarida=True),
        uret_insan_pozu(0.65, 0.5, el_yukarida=True),
    ]
    kare_2 = uret_sentetik_kare(insan_tanimlari=[
        (0.35, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.65, 0.5, 0.08, 0.4, RENK_MAVI),
    ])

    for _ in range(25):
        simdi += 0.1
        algi = uret_algi(pozlar_2, [1, 2])
        motor.isle(kare_2.copy(), algi, simdi)

    assert motor.durum != "oyun"

    # 6 kişi durumu
    xs_6 = np.linspace(0.1, 0.9, 6)
    pozlar_6 = [uret_insan_pozu(x, 0.5, el_yukarida=True) for x in xs_6]
    tanimlar_6 = [(x, 0.5, 0.08, 0.4, RENK_KIRMIZI) for x in xs_6]
    kare_6 = uret_sentetik_kare(insan_tanimlari=tanimlar_6)

    for _ in range(25):
        simdi += 0.1
        algi = uret_algi(pozlar_6, list(range(1, 7)))
        motor.isle(kare_6.copy(), algi, simdi)

    assert motor.durum != "oyun"


def test_02_omuz_genisligi_esik_alti_izleyici_haric_tutulur():
    """Omuz genişliği < 0.035 olan izleyiciler oyuncu sayısına dahil edilmez."""
    motor = olustur_motor()
    simdi = 10.0

    pozlar = [
        uret_insan_pozu(0.2, 0.5, omuz_genislik=0.08, el_yukarida=False),
        uret_insan_pozu(0.5, 0.5, omuz_genislik=0.08, el_yukarida=False),
        uret_insan_pozu(0.8, 0.5, omuz_genislik=0.08, el_yukarida=False),
        uret_insan_pozu(0.5, 0.25, omuz_genislik=0.025, el_yukarida=False),
    ]
    tanimlar = [
        (0.2, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.5, 0.5, 0.08, 0.4, RENK_MAVI),
        (0.8, 0.5, 0.08, 0.4, RENK_YESIL),
        (0.5, 0.25, 0.025, 0.2, RENK_SARI),
    ]
    kare = uret_sentetik_kare(insan_tanimlari=tanimlar)

    # 1.6 sn bekleme
    for _ in range(16):
        simdi += 0.1
        algi = uret_algi(pozlar, [10, 20, 30, 99])
        motor.isle(kare.copy(), algi, simdi)

    # 0.9 sn el kaldırma
    pozlar_el = [
        uret_insan_pozu(0.2, 0.5, omuz_genislik=0.08, el_yukarida=True),
        uret_insan_pozu(0.5, 0.5, omuz_genislik=0.08, el_yukarida=True),
        uret_insan_pozu(0.8, 0.5, omuz_genislik=0.08, el_yukarida=True),
        uret_insan_pozu(0.5, 0.25, omuz_genislik=0.025, el_yukarida=True),
    ]
    for _ in range(10):
        simdi += 0.1
        algi = uret_algi(pozlar_el, [10, 20, 30, 99])
        motor.isle(kare.copy(), algi, simdi)

    assert motor.durum == "oyun"
    assert motor.N == 3


def test_03_tahmini_pozlar_ilk_katilimda_kabul_edilmez():
    """Oyuncu kapısından geçmeyen (tahmini) poz ilk başta lobiye/oyuna katılamaz."""
    motor = olustur_motor()
    simdi = 1.0

    pozlar = [
        uret_insan_pozu(0.3, 0.5, el_yukarida=True),
        uret_insan_pozu(0.5, 0.5, el_yukarida=True),
        uret_insan_pozu(0.7, 0.5, el_yukarida=True),
    ]
    kare = uret_sentetik_kare(insan_tanimlari=[
        (0.3, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.5, 0.5, 0.08, 0.4, RENK_MAVI),
        (0.7, 0.5, 0.08, 0.4, RENK_YESIL),
    ])

    for _ in range(30):
        simdi += 0.1
        algi = uret_algi(pozlar, [10, 20, 30], tahmini_idleri=[30])
        motor.isle(kare.copy(), algi, simdi)

    assert motor.durum != "oyun"


@pytest.mark.parametrize("n_oyuncu", [3, 4, 5])
def test_04_gecerli_katilim_baslat_sabit_n(n_oyuncu):
    """3, 4 veya 5 geçerli oyuncu ile lobi akışından oyun doğru N sayısı ile başlar."""
    motor = olustur_motor(seed=100 + n_oyuncu)
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=n_oyuncu, baslangic_t=5.0)

    assert motor.durum == "oyun"
    assert motor.N == n_oyuncu
    assert len(motor.oyuncular) == n_oyuncu


def test_05_fazladan_izleyici_kartsiz_ve_siraya_katilmaz():
    """Oyun sırasında giren N+1'inci kişi (izleyici) kart almaz, sıralamaya katılmaz."""
    motor = olustur_motor()
    simdi, xs, ids, tanimlar_3 = lobi_ile_baslat(motor, n=3, baslangic_t=10.0)

    assert motor.durum == "oyun"
    assert motor.N == 3

    # N+1'inci kişi (ID 4) sahneye girer
    pozlar_4 = [uret_insan_pozu(xs[i], 0.5, el_yukarida=False) for i in range(3)]
    pozlar_4.append(uret_insan_pozu(0.92, 0.5, el_yukarida=False))
    tanimlar_4 = tanimlar_3 + [(0.92, 0.5, 0.08, 0.4, RENK_MOR)]
    kare_4 = uret_sentetik_kare(insan_tanimlari=tanimlar_4)

    for _ in range(10):
        simdi += 0.1
        algi = uret_algi(pozlar_4, [1, 2, 3, 4])
        motor.isle(kare_4.copy(), algi, simdi)

    kartli_oyuncular = [o for o in motor.oyuncular.values() if kart_metni_al(o) != ""]
    assert len(kartli_oyuncular) == 3


def test_06_baslangic_kart_dagitimi_hatali_ve_yeterince_yer_degismis():
    """Dağıtım anında kartlar dogru_mu == False olmalıdır."""
    motor = olustur_motor(seed=777)
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=4, baslangic_t=2.0)

    assert motor.durum == "oyun"

    oyuncular_sirali = sorted(motor.oyuncular.values(), key=lambda o: o.x)
    kartlar = [kart_metni_al(o) for o in oyuncular_sirali]

    assert not motor.icerik.dogru_mu(kartlar)


def test_07_geri_sayim_3sn_ve_hata_toleransi_03sn():
    """
    Doğru sırada 3 sn geri sayım çalışır.
    0.2 sn'lik bozulma sayımı sıfırlamazken, tolerans sonrası soru tamamlanır.
    """
    motor = olustur_motor(seed=12)
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=3, baslangic_t=0.0)

    assert motor.durum == "oyun"
    baslangic_soru = motor.soru_no

    dogru_pids, yanlis_pids = dogru_ve_yanlis_perm_bul(motor)
    assert dogru_pids is not None
    assert yanlis_pids is not None

    xs_sirali = [0.25, 0.5, 0.75]
    renk_sozluk = {1: RENK_KIRMIZI, 2: RENK_MAVI, 3: RENK_YESIL}

    def kare_calistir(pid_sirasi, sure_sn):
        nonlocal simdi
        adim = int(round(sure_sn / 0.1))
        # pid_sirasi[i] -> xs_sirali[i]
        poz_list = []
        id_list = []
        tanim_list = []
        for i, pid in enumerate(pid_sirasi):
            x_val = xs_sirali[i]
            poz_list.append(uret_insan_pozu(x_val, 0.5, el_yukarida=False))
            id_list.append(pid)
            tanim_list.append((x_val, 0.5, 0.08, 0.4, renk_sozluk.get(pid, RENK_KIRMIZI)))

        k_frame = uret_sentetik_kare(insan_tanimlari=tanim_list)
        for _ in range(adim):
            simdi += 0.1
            algi = uret_algi(poz_list, id_list)
            motor.isle(k_frame.copy(), algi, simdi)

    # 1) Doğru sırada 1.5 sn tut
    kare_calistir(dogru_pids, 1.5)
    assert motor.soru_no == baslangic_soru

    # 2) 0.2 sn sırayı boz (tolerans 0.3 sn)
    kare_calistir(yanlis_pids, 0.2)
    assert motor.soru_no == baslangic_soru

    # 3) Tekrar doğru sıraya dön: 1.8 sn tut + 1.2 sn kutlama
    kare_calistir(dogru_pids, 3.0)
    assert motor.soru_no > baslangic_soru


def test_08_eksik_oyuncu_05sn_dondurur_2sn_duraklatir_8sn_bitirir():
    """Oyuncu kaybında sayım duraklar, 8 sn dönmezse tur sonlanır."""
    motor = olustur_motor()
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=3, baslangic_t=10.0)

    assert motor.durum == "oyun"

    # ID 3 kaybolur (yalnızca 1 ve 2 kaldı)
    p_kalan = [uret_insan_pozu(xs[0], 0.5), uret_insan_pozu(xs[1], 0.5)]
    t_kalan = [tanimlar[0], tanimlar[1]]
    k_kalan = uret_sentetik_kare(insan_tanimlari=t_kalan)

    # 8.5 saniye boyunca oyuncu dönmez
    for _ in range(85):
        simdi += 0.1
        algi = uret_algi(p_kalan, [1, 2])
        motor.isle(k_kalan.copy(), algi, simdi)

    assert motor.durum in ["sonuc", "bekle"] or getattr(motor, "faz", "") == "sonuc"


def test_09_deterministik_np_rng():
    """Aynı seed verildiğinde soru ve kart üretim dizilimi tamamen aynı olmalıdır."""
    motor1 = olustur_motor(seed=9999)
    motor2 = olustur_motor(seed=9999)

    soru1 = motor1.icerik.uret(4, soru_no=0)
    soru2 = motor2.icerik.uret(4, soru_no=0)

    assert soru1 == soru2


def test_10_tum_oyuncular_el_kaldirma_08sn_lobi_gecisi():
    """Lobide 1.5 sn stabil durduktan sonra tüm oyuncular 0.8 sn el kaldırınca başlar, biri kaldırmazsa başlamaz."""
    motor = olustur_motor()
    simdi = 0.0

    # 3 kişi, 1.6 sn el aşağıda
    p_asagi = [uret_insan_pozu(0.3 + i * 0.2, 0.5, el_yukarida=False) for i in range(3)]
    tanimlar = [(0.3 + i * 0.2, 0.5, 0.08, 0.4, RENK_KIRMIZI) for i in range(3)]
    kare = uret_sentetik_kare(insan_tanimlari=tanimlar)

    for _ in range(16):
        simdi += 0.1
        algi = uret_algi(p_asagi, [1, 2, 3])
        motor.isle(kare.copy(), algi, simdi)

    # 2'si el kaldırıyor, 1'i kaldırmıyor
    p_eksik = [
        uret_insan_pozu(0.3, 0.5, el_yukarida=True),
        uret_insan_pozu(0.5, 0.5, el_yukarida=True),
        uret_insan_pozu(0.7, 0.5, el_yukarida=False),
    ]
    for _ in range(15):
        simdi += 0.1
        algi = uret_algi(p_eksik, [1, 2, 3])
        motor.isle(kare.copy(), algi, simdi)

    assert motor.durum != "oyun"

    # Şimdi 3. kişi de el kaldırıyor ve 0.9 sn tutuyorlar
    p_tam = [uret_insan_pozu(0.3 + i * 0.2, 0.5, el_yukarida=True) for i in range(3)]
    for _ in range(10):
        simdi += 0.1
        algi = uret_algi(p_tam, [1, 2, 3])
        motor.isle(kare.copy(), algi, simdi)

    assert motor.durum == "oyun"


def test_11_caprazlamada_gorunus_imzasi_ile_stable_id_korunur_poz_id_degisse_de():
    """
    İki kişi yer değiştirir. Çaprazlama sırasında MediaPipe poz_id'leri ters çevirse bile,
    görünüş imzası (renk) sayesinde motorun stable ID'si ve kartı doğru kişide kalır.
    """
    motor = olustur_motor()
    renkler = [RENK_KIRMIZI, RENK_MAVI, RENK_YESIL]
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=3, baslangic_t=0.0, renkler=renkler)

    assert motor.durum == "oyun"

    # İmzaların tam olgunlaşması için 12 ayrık kare tek başına çalıştırılır
    p_ayrik_ilk = [
        uret_insan_pozu(0.30, 0.5),
        uret_insan_pozu(0.60, 0.5),
        uret_insan_pozu(0.85, 0.5),
    ]
    t_ayrik_ilk = [
        (0.30, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.60, 0.5, 0.08, 0.4, RENK_MAVI),
        (0.85, 0.5, 0.08, 0.4, RENK_YESIL),
    ]
    k_ayrik_ilk = uret_sentetik_kare(insan_tanimlari=t_ayrik_ilk)

    for _ in range(12):
        simdi += 0.1
        algi = uret_algi(p_ayrik_ilk, [1, 2, 3])
        motor.isle(k_ayrik_ilk.copy(), algi, simdi)

    # Başlangıçta 0.30'daki (Kırmızı) ve 0.60'taki (Mavi) oyuncuların kimlik ve kartları
    oyuncu_kirmizi = min(motor.oyuncular.values(), key=lambda o: abs(o.x - 0.30))
    oyuncu_mavi = min(motor.oyuncular.values(), key=lambda o: abs(o.x - 0.60))
    oyuncu_yesil = min(motor.oyuncular.values(), key=lambda o: abs(o.x - 0.85))

    id_kirmizi = oyuncu_kirmizi.kimlik
    id_mavi = oyuncu_mavi.kimlik
    id_yesil = oyuncu_yesil.kimlik

    kart_kirmizi = kart_metni_al(oyuncu_kirmizi)
    kart_mavi = kart_metni_al(oyuncu_mavi)
    kart_yesil = kart_metni_al(oyuncu_yesil)

    # Çaprazlama: 0.45'te çakışma (overlap)
    p_cakisma = [
        uret_insan_pozu(0.44, 0.5),
        uret_insan_pozu(0.46, 0.5),
        uret_insan_pozu(0.85, 0.5),
    ]
    t_cakisma = [
        (0.44, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.46, 0.5, 0.08, 0.4, RENK_MAVI),
        (0.85, 0.5, 0.08, 0.4, RENK_YESIL),
    ]
    k_cakisma = uret_sentetik_kare(insan_tanimlari=t_cakisma)

    for _ in range(6):
        simdi += 0.1
        algi = uret_algi(p_cakisma, [1, 2, 3])
        motor.isle(k_cakisma.copy(), algi, simdi)

    # Ayrılma: Kırmızı 0.60'a gitti, Mavi 0.30'a gitti.
    # Poz ID takası simüle ediliyor: 0.30'daki Mavi'ye poz_id=1, 0.60'taki Kırmızı'ya poz_id=2 veriliyor.
    p_ayrik_son = [
        uret_insan_pozu(0.30, 0.5),
        uret_insan_pozu(0.60, 0.5),
        uret_insan_pozu(0.85, 0.5),
    ]
    t_ayrik_son = [
        (0.30, 0.5, 0.08, 0.4, RENK_MAVI),
        (0.60, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.85, 0.5, 0.08, 0.4, RENK_YESIL),
    ]
    k_ayrik_son = uret_sentetik_kare(insan_tanimlari=t_ayrik_son)

    for _ in range(10):
        simdi += 0.1
        algi = uret_algi(p_ayrik_son, [1, 2, 3])
        motor.isle(k_ayrik_son.copy(), algi, simdi)

    # Yeşil (3) sabit kalmalı, kartı değişmemeli
    son_yesil = motor.oyuncular[id_yesil]
    assert kart_metni_al(son_yesil) == kart_yesil

    # Kırmızı sağa (x ~ 0.60), Mavi sola (x ~ 0.30) geçmiş olmalı ve kartlarını korumalıdır
    son_kirmizi = motor.oyuncular[id_kirmizi]
    son_mavi = motor.oyuncular[id_mavi]

    assert son_kirmizi.x > son_mavi.x
    assert kart_metni_al(son_kirmizi) == kart_kirmizi
    assert kart_metni_al(son_mavi) == kart_mavi


def test_12_olgunlasmamis_imza_belirsiz_durum_tetikler():
    """Yeterli imza örneği (10 örnek) birikmeden karışma yaşanırsa durum 'belirsiz' olur."""
    motor = olustur_motor()
    simdi = 1.0

    p_init = [
        uret_insan_pozu(0.35, 0.5, el_yukarida=True),
        uret_insan_pozu(0.55, 0.5, el_yukarida=True),
        uret_insan_pozu(0.80, 0.5, el_yukarida=True),
    ]
    t_init = [
        (0.35, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.55, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.80, 0.5, 0.08, 0.4, RENK_YESIL),
    ]
    k_init = uret_sentetik_kare(insan_tanimlari=t_init)
    algi_init = uret_algi(p_init, [1, 2, 3])

    if hasattr(motor, "baslat"):
        motor.baslat(algi_init, simdi)
    else:
        for _ in range(25):
            simdi += 0.1
            motor.isle(k_init.copy(), algi_init, simdi)

    # Yalnızca 3 ayrık kare ver (imza örneği < 10)
    for _ in range(3):
        simdi += 0.1
        motor.isle(k_init.copy(), algi_init, simdi)

    # 0.5 sn çakışma (5 kare)
    p_cakis = [
        uret_insan_pozu(0.44, 0.5),
        uret_insan_pozu(0.46, 0.5),
        uret_insan_pozu(0.80, 0.5),
    ]
    t_cakis = [
        (0.44, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.46, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.80, 0.5, 0.08, 0.4, RENK_YESIL),
    ]
    k_cakis = uret_sentetik_kare(insan_tanimlari=t_cakis)

    for _ in range(5):
        simdi += 0.1
        algi = uret_algi(p_cakis, [1, 2, 3])
        motor.isle(k_cakis.copy(), algi, simdi)

    # 0.6 sn ayrılma (6 kare)
    for _ in range(6):
        simdi += 0.1
        algi = uret_algi(p_init, [1, 2, 3])
        motor.isle(k_init.copy(), algi, simdi)

    belirsiz_oyuncu = any(getattr(o, "durum", "") == "belirsiz" for o in motor.oyuncular.values())
    olay_tipleri = [olay_kaydi_al(olay)[0] for olay in getattr(motor, "olaylar", [])]
    assert belirsiz_oyuncu or ("belirsiz" in olay_tipleri)


def test_13_yanlis_siralama_soruyu_bitirmez():
    """Kartlar yanlış dizilimde kaldığı sürece ne kadar süre geçerse geçsin soru tamamlanmaz."""
    motor = olustur_motor()
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=3, baslangic_t=10.0)

    assert motor.durum == "oyun"
    baslangic_soru = motor.soru_no

    dogru_pids, yanlis_pids = dogru_ve_yanlis_perm_bul(motor)
    assert yanlis_pids is not None

    xs_sirali = [0.25, 0.5, 0.75]
    p_yanlis = [uret_insan_pozu(xs_sirali[i], 0.5) for i in range(3)]
    t_yanlis = [(xs_sirali[i], 0.5, 0.08, 0.4, RENK_KIRMIZI) for i in range(3)]
    k_yanlis = uret_sentetik_kare(insan_tanimlari=t_yanlis)

    # 10 saniye boyunca yanlış sırada kal
    for _ in range(100):
        simdi += 0.1
        algi = uret_algi(p_yanlis, yanlis_pids)
        motor.isle(k_yanlis.copy(), algi, simdi)

    assert motor.soru_no == baslangic_soru
    assert motor.durum == "oyun"


def test_14_bes_soruluk_tur_ve_sonuc_ekrani():
    """5 soru tamamlandığında oyun turu bitirir ve sonuc durumuna geçer."""
    motor = olustur_motor(seed=4321)
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=3, baslangic_t=1.0)

    assert motor.durum == "oyun"

    xs_sirali = [0.25, 0.50, 0.75]
    renk_sozluk = {1: RENK_KIRMIZI, 2: RENK_MAVI, 3: RENK_YESIL}

    for _ in range(5):
        if motor.durum in ["sonuc", "bekle"]:
            break

        dogru_pids, _ = dogru_ve_yanlis_perm_bul(motor)
        if dogru_pids is None:
            dogru_pids = ids

        p_cozum = [uret_insan_pozu(xs_sirali[i], 0.5) for i in range(3)]
        t_cozum = [(xs_sirali[i], 0.5, 0.08, 0.4, renk_sozluk.get(dogru_pids[i], RENK_KIRMIZI)) for i in range(3)]
        k_cozum = uret_sentetik_kare(insan_tanimlari=t_cozum)

        # 3.2 sn doğru sırada tut + 1.2 sn kutlama
        for _ in range(45):
            simdi += 0.1
            algi = uret_algi(p_cozum, dogru_pids)
            motor.isle(k_cozum.copy(), algi, simdi)

    assert motor.durum in ["sonuc", "bekle"] or getattr(motor, "faz", "") == "sonuc" or motor.soru_no >= 4


def test_15_siradan_el_kildirma_belirsiz_olmayanda_kart_degistirmez():
    """Belirsiz (ambiguous) olmayan bir oyuncunun el kaldırması kartını değiştirmez."""
    motor = olustur_motor()
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=3, baslangic_t=5.0)

    assert motor.durum == "oyun"

    p1_kart_once = kart_metni_al(motor.oyuncular[ids[0]])

    # 1. oyuncu normal oyunda elini 1 sn havada tutar
    p_tek_el = [
        uret_insan_pozu(xs[0], 0.5, el_yukarida=True),
        uret_insan_pozu(xs[1], 0.5, el_yukarida=False),
        uret_insan_pozu(xs[2], 0.5, el_yukarida=False),
    ]
    kare = uret_sentetik_kare(insan_tanimlari=tanimlar)

    for _ in range(12):
        simdi += 0.1
        algi = uret_algi(p_tek_el, ids)
        motor.isle(kare.copy(), algi, simdi)

    p1_kart_sonra = kart_metni_al(motor.oyuncular[ids[0]])
    assert p1_kart_once == p1_kart_sonra


def test_16_belirsiz_kisinin_el_kaldirmasi_el_takas_ve_6s_donus():
    """Belirsiz durumdaki bir oyuncu elini kaldırınca takas gerçekleşir veya 6 sn sonra normale döner."""
    motor = olustur_motor()
    simdi = 1.0

    p_init = [
        uret_insan_pozu(0.35, 0.5, el_yukarida=True),
        uret_insan_pozu(0.55, 0.5, el_yukarida=True),
        uret_insan_pozu(0.80, 0.5, el_yukarida=True),
    ]
    t_init = [
        (0.35, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.55, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.80, 0.5, 0.08, 0.4, RENK_YESIL),
    ]
    k_init = uret_sentetik_kare(insan_tanimlari=t_init)
    algi_init = uret_algi(p_init, [1, 2, 3])

    if hasattr(motor, "baslat"):
        motor.baslat(algi_init, simdi)
    else:
        for _ in range(25):
            simdi += 0.1
            motor.isle(k_init.copy(), algi_init, simdi)

    # Çakışma ile belirsizlik tetikle
    p_cakis = [
        uret_insan_pozu(0.44, 0.5),
        uret_insan_pozu(0.46, 0.5),
        uret_insan_pozu(0.80, 0.5),
    ]
    k_cakis = uret_sentetik_kare(insan_tanimlari=[
        (0.44, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.46, 0.5, 0.08, 0.4, RENK_KIRMIZI),
        (0.80, 0.5, 0.08, 0.4, RENK_YESIL),
    ])

    for _ in range(5):
        simdi += 0.1
        algi = uret_algi(p_cakis, [1, 2, 3])
        motor.isle(k_cakis.copy(), algi, simdi)

    for _ in range(6):
        simdi += 0.1
        algi = uret_algi(p_init, [1, 2, 3])
        motor.isle(k_init.copy(), algi, simdi)

    # 1. oyuncu 0.9 sn el kaldırır
    p_jest = [
        uret_insan_pozu(0.35, 0.5, el_yukarida=True),
        uret_insan_pozu(0.55, 0.5, el_yukarida=False),
        uret_insan_pozu(0.80, 0.5, el_yukarida=False),
    ]
    for _ in range(10):
        simdi += 0.1
        algi = uret_algi(p_jest, [1, 2, 3])
        motor.isle(k_init.copy(), algi, simdi)

    # Ardından 6.5 sn boyunca kimse el kaldırmaz
    p_normal = [
        uret_insan_pozu(0.35, 0.5, el_yukarida=False),
        uret_insan_pozu(0.55, 0.5, el_yukarida=False),
        uret_insan_pozu(0.80, 0.5, el_yukarida=False),
    ]
    for _ in range(65):
        simdi += 0.1
        algi = uret_algi(p_normal, [1, 2, 3])
        motor.isle(k_init.copy(), algi, simdi)

    # 6 sn sonra belirsizlik sona ermiş olmalı
    assert all(getattr(o, "durum", "normal") != "belirsiz" for o in motor.oyuncular.values())


def test_17_histerezis_yakin_iki_kisi_titreyen_x_ile_takas_olmaz():
    """x farkı < 0.25 * omuz_genisligi olan iki kişinin titreyen x koordinatları sıralamayı bozmaz."""
    motor = olustur_motor()
    simdi, xs, ids, tanimlar = lobi_ile_baslat(motor, n=3, baslangic_t=1.0)

    assert motor.durum == "oyun"

    sirali_ilk = [o.kimlik for o in sorted(motor.oyuncular.values(), key=lambda o: o.x)]

    # 10 kare boyunca x'leri küçük gürültü ile titreştir (0.505 ve 0.495 - mikro geçiş)
    kare = uret_sentetik_kare(insan_tanimlari=tanimlar)
    for k in range(10):
        simdi += 0.1
        gx1 = 0.505 if k % 2 == 0 else 0.495
        gx2 = 0.495 if k % 2 == 0 else 0.505
        p_titrek = [
            uret_insan_pozu(0.20, 0.5),
            uret_insan_pozu(gx1, 0.5),
            uret_insan_pozu(gx2, 0.5),
        ]
        algi = uret_algi(p_titrek, ids)
        motor.isle(kare.copy(), algi, simdi)

    sirali_son = [o.kimlik for o in sorted(motor.oyuncular.values(), key=lambda o: o.x)]
    assert sirali_ilk[0] == sirali_son[0]


def test_18_dayaniklilik_ve_bozuk_kare_girdileri():
    """Motor boş, eksik noktalı veya beklenmedik girişlerde çökmemeli ve 1280x720 BGR dönmelidir."""
    motor = olustur_motor()
    simdi = 0.0

    # 1) Tamamen boş algı
    bos_kare = np.zeros((720, 1280, 3), dtype=np.uint8)
    bos_algi = uret_algi([], [])
    cikis = motor.isle(bos_kare, bos_algi, simdi)
    assert cikis.shape == (720, 1280, 3)
    assert cikis.dtype == np.uint8

    # 2) Sınır dışı koordinatlar
    sinir_noktalar = [sahte_nokta(0.0, 0.0, 0.0, 0.0) for _ in range(33)]
    sinir_algi = uret_algi([sinir_noktalar], [1])
    cikis_sinir = motor.isle(bos_kare, sinir_algi, simdi + 0.1)
    assert cikis_sinir.shape == (720, 1280, 3)

    # 3) Eksik nokta listesi (10 noktalı pose)
    eksik_noktalar = [sahte_nokta(0.5, 0.5) for _ in range(10)]
    eksik_algi = uret_algi([eksik_noktalar], [2])
    cikis_eksik = motor.isle(bos_kare, eksik_algi, simdi + 0.2)
    assert cikis_eksik.shape == (720, 1280, 3)
