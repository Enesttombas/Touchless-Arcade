"""Kamera koprusu, AgKamera, hata toleransi ve stant arayuzu testleri."""

import math
import os
import socket
import struct
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "oyunlar"))

import cekirdek as ck
import kamera_kopru as kk
import stant_app as stant


def _bekle(kosul, zaman_asimi: float = 3.0):
    bitis = time.monotonic() + zaman_asimi
    while time.monotonic() < bitis:
        if kosul():
            return True
        time.sleep(0.01)
    return False


def test_kopru_akis_mirror_reconnect_ve_cached_frame():
    """Loopback 100 kare akis, yavas orneklem ile bosluklar, tek mirror (1280x720), restart <= 2s ve onbellek."""
    sayac = [0]

    def kaynak():
        if sayac[0] >= 100:
            return None
        sayac[0] += 1
        kare = np.zeros((24, 32, 3), np.uint8)
        kare[:, :16] = (10, 20, sayac[0])
        kare[:, 16:] = (150, 160, sayac[0])
        return kare

    sunucu = kk.Gonderici(kaynak, adres=("127.0.0.1", 0), fps=120)
    sunucu.start()
    port = sunucu.adres[1]

    istemci = kk.AgKamera(f"tcp://127.0.0.1:{port}")
    istemci.start()

    try:
        assert isinstance(istemci, threading.Thread)
        # Slow application samples record with gaps (kuyruksuz en guncel kare davranisi)
        ornekler = []
        for _ in range(4):
            time.sleep(0.08)
            ornekler.append(istemci.kare_no)

        assert _bekle(lambda: istemci.kare_no == 100, zaman_asimi=3.0)
        assert any(b - a > 1 for a, b in zip(ornekler, ornekler[1:])), f"Bosluklar olmali: {ornekler}"
        assert istemci.bagli is True
        assert istemci.kare is not None
        assert istemci.kare.shape == (720, 1280, 3)
        # Yatay tek cevirme: sol taraf parlak olmali
        assert istemci.kare[360, 100, 0] > istemci.kare[360, 1180, 0] + 80
        assert istemci.rtt_ms >= 0.0
        assert math.isfinite(istemci.ofset_sn)

        # Sunucu durdur ve yeniden baslatma suresi <= 2s kontrol et
        sunucu.kapat()
        assert _bekle(lambda: not istemci.bagli, zaman_asimi=1.5)

        kaynak2 = lambda: np.full((24, 32, 3), 210, np.uint8)
        sunucu2 = kk.Gonderici(kaynak2, adres=("127.0.0.1", port), fps=30)
        t_basla = time.monotonic()
        try:
            sunucu2.start()
            assert _bekle(
                lambda: istemci.bagli and istemci.kare is not None and istemci.kare[100, 100, 0] > 190,
                zaman_asimi=2.0,
            )
            assert (time.monotonic() - t_basla) <= 2.0
        finally:
            sunucu2.kapat()
    finally:
        istemci.kapat()
        sunucu.kapat()

    # Duraklatilmis tek karelik kaynak: 2. istemci de onbellekten ayni kareyi alir
    kalan = [1]

    def tek_kare_kaynak():
        if kalan[0] > 0:
            kalan[0] -= 1
            return np.full((24, 32, 3), 88, np.uint8)
        return None

    sunucu_tek = kk.Gonderici(tek_kare_kaynak, adres=("127.0.0.1", 0), fps=30)
    sunucu_tek.start()
    port_tek = sunucu_tek.adres[1]
    assert _bekle(lambda: sunucu_tek.kare_no == 1, zaman_asimi=2.0)

    try:
        for _ in range(2):
            ist = kk.AgKamera(f"tcp://127.0.0.1:{port_tek}")
            ist.start()
            try:
                assert _bekle(lambda: ist.kare_no == 1, zaman_asimi=2.0)
                assert ist.kare is not None
                assert abs(int(ist.kare[100, 100, 0]) - 88) < 5
            finally:
                ist.kapat()
    finally:
        sunucu_tek.kapat()


def test_hata_toleransi_gecersiz_urller():
    """Gecersiz URL formatlari ve port sinirlari AgKamera tarafindan reddedilir."""
    for gecersiz_url in ("http://127.0.0.1:8090", "tcp://:8090", "tcp://127.0.0.1:0", "tcp://127.0.0.1:99999"):
        with pytest.raises(ValueError):
            kk.AgKamera(gecersiz_url)


@pytest.mark.parametrize(
    "senaryo_adi,veri_uretici",
    [
        ("nan_timestamp", lambda: kk.HEADER_STRUCT.pack(1, float("nan"), 10) + b"0123456789"),
        ("oversize_payload", lambda: kk.HEADER_STRUCT.pack(1, time.time(), kk.MAX_PAYLOAD + 1) + b"x" * 16),
        ("broken_jpeg", lambda: kk.HEADER_STRUCT.pack(1, time.time(), len(b"BOZUK_JPEG_VERISI_123")) + b"BOZUK_JPEG_VERISI_123"),
        ("truncated_header", lambda: b"\x00" * 4),
        ("truncated_payload", lambda: kk.HEADER_STRUCT.pack(1, time.time(), 500) + b"KISA_VERI"),
    ],
)
def test_hata_toleransi_bozuk_ag_paketleri(senaryo_adi, veri_uretici):
    """Parametrize bozuk paket senaryolarinda gercek 10-ping handshake sonrasi hata yakalanir ve thread hayatta kalir."""
    sahte_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sahte_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sahte_srv.bind(("127.0.0.1", 0))
    sahte_srv.listen(1)
    srv_port = sahte_srv.getsockname()[1]

    ist = kk.AgKamera(f"tcp://127.0.0.1:{srv_port}")
    ist.start()

    conn = None
    try:
        sahte_srv.settimeout(2.0)
        conn, _ = sahte_srv.accept()

        for _ in range(kk.PING_PONG_COUNT):
            p = conn.recv(kk.PING_STRUCT.size)
            assert len(p) == kk.PING_STRUCT.size
            (t_ist,) = kk.PING_STRUCT.unpack(p)
            conn.sendall(kk.PONG_STRUCT.pack(t_ist, time.time()))

        assert _bekle(lambda: ist.bagli, zaman_asimi=1.0)

        # Bozuk veriyi gonder
        bozuk_veri = veri_uretici()
        conn.sendall(bozuk_veri)

        # Istemci hatayi gorup baglantiyi kesmeli veya bagli=False olmali; thread hayatta kalmali
        assert _bekle(lambda: not ist.bagli, zaman_asimi=2.0)
        assert ist.is_alive()
    finally:
        if conn:
            try:
                conn.close()
            except OSError:
                pass
        sahte_srv.close()
        ist.kapat()
        assert not ist.is_alive()


def test_yavas_istemci_ve_tricklesocket_deadlines():
    """Yavas istemci durumunda TrickleSocket <= 0.8s'de zaman asimina ugrar, sunucu kilitlenmez."""
    # TrickleSocket mutlak deadline dogrulamasi
    class TrickleSocket:
        def settimeout(self, value):
            pass

        def send(self, data):
            time.sleep(0.09)
            return min(4096, len(data))

    t_basla = time.monotonic()
    try:
        gonderildi = kk._tam_gonder(TrickleSocket(), b"x" * 131072)
        assert gonderildi is False
    except (TimeoutError, OSError):
        pass
    assert time.monotonic() - t_basla < 0.8, "Mutlak gonderim deadline asildi"

    # Sunucu tarafli yavas okuyan istemci testi
    sunucu = kk.Gonderici(lambda: np.zeros((24, 32, 3), np.uint8), adres=("127.0.0.1", 0), fps=60)
    sunucu.start()
    try:
        yavas_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        yavas_sock.connect(sunucu.adres)
        for _ in range(kk.PING_PONG_COUNT):
            p = kk.PING_STRUCT.pack(time.time())
            yavas_sock.sendall(p)
            yavas_sock.recv(kk.PONG_STRUCT.size)

        time.sleep(0.5)
        assert sunucu.is_alive()
        assert sunucu.calis
        yavas_sock.close()
    finally:
        sunucu.kapat()
        assert not sunucu.is_alive()


def test_kaynak_istisnasi_guvenli_kapanis():
    """Kaynak fonksiyonu istisna firlattiginda sunucu hata kaydeder ve iplikleri temiz sonlanir."""
    def hatali_kaynak():
        raise RuntimeError("Kamera sensor hatasi")

    sunucu_hata = kk.Gonderici(hatali_kaynak, adres=("127.0.0.1", 0), fps=30)
    sunucu_hata.start()
    time.sleep(0.2)
    try:
        assert sunucu_hata.hata is not None
        assert not sunucu_hata.calis
    finally:
        sunucu_hata.kapat()
    assert not sunucu_hata.is_alive()
    assert not sunucu_hata._yakalama_ipligi.is_alive()


def test_kamera_fabrika():
    """cekirdek.Kamera fabrikasi yerel ve ag URL tiplerini dogru ornekler."""
    with patch("stand.Kamera") as mock_stand_kam:
        mock_stand_kam.return_value = "STAND_KAMERA_ORNEGI"

        k0 = ck.Kamera(0)
        assert k0 == "STAND_KAMERA_ORNEGI"
        mock_stand_kam.assert_called_with(0)

        k_http = ck.Kamera("http://192.168.1.50:8080/video")
        assert k_http == "STAND_KAMERA_ORNEGI"
        mock_stand_kam.assert_called_with("http://192.168.1.50:8080/video")

        k_tcp = ck.Kamera("tcp://127.0.0.1:8090")
        assert isinstance(k_tcp, kk.AgKamera)


def test_gui_gercek_main_bekleme_ve_kurtarma_dongusu():
    """stant_app.main() gercek calistirilip None -> disconnect -> stale -> recovery adimlari ve UI sayaclari dogrulanir."""
    durumlar = [
        (None, False, 0.0),                                       # 1. None
        (np.ones((720, 1280, 3), np.uint8), False, 100.0),       # 2. disconnect (bagli=False)
        (np.ones((720, 1280, 3), np.uint8), True, 98.0),         # 3. stale (t_son eski)
        (np.ones((720, 1280, 3), np.uint8), True, 100.0),        # 4. canli recovery
    ]
    kamera = MagicMock()
    kamera.kare, kamera.bagli, kamera.t_son = durumlar[0]
    adim = [0]

    def sahte_wait_key(gecikme):
        if adim[0] == 3:
            return ord("q")
        adim[0] += 1
        kamera.kare, kamera.bagli, kamera.t_son = durumlar[adim[0]]
        return 255

    algilayici = MagicMock()
    algilayici.algila.return_value = stant.ck.Algi()
    oyun = MagicMock()
    oyun.ihtiyac = set()
    oyun.isle.side_effect = lambda kare, algi, t: kare

    with patch.dict(os.environ, {"ASENKRON_ALGI": "0", "FPS_LOG": "0", "TAM_EKRAN": "0"}), \
         patch.object(stant.ck, "Kamera", return_value=kamera), \
         patch.object(stant.ck, "Algilayici", return_value=algilayici), \
         patch.object(stant.ck, "Ses"), \
         patch.object(stant, "StantUygulama", return_value=oyun), \
         patch.object(stant.ck, "yazi_koy") as sahte_yazi, \
         patch.object(stant.time, "time", return_value=100.0), \
         patch.multiple(
             stant.cv2,
             namedWindow=MagicMock(),
             resizeWindow=MagicMock(),
             imshow=MagicMock(),
             waitKey=MagicMock(side_effect=sahte_wait_key),
             getWindowProperty=MagicMock(return_value=1),
             destroyAllWindows=MagicMock(),
         ):
        stant.main()

        assert stant.cv2.imshow.call_count == 4
        assert sahte_yazi.call_count == 3
        assert all(c.args[1] == "Kamera bekleniyor" for c in sahte_yazi.call_args_list)
        assert algilayici.algila.call_count == 1
        assert oyun.isle.call_count == 1
        kamera.kapat.assert_called_once()


def test_idle_handshake_ve_hizli_kapanma():
    """Gonderici beklemedeyken veya istemci bagliyken kapat cagrildiginda <= 1.5s icinde sonlanir."""
    sunucu = kk.Gonderici(lambda: None, adres=("127.0.0.1", 0), fps=30)
    sunucu.start()

    idle = socket.create_connection(sunucu.adres, timeout=1)
    time.sleep(0.05)
    t0 = time.monotonic()
    sunucu.kapat()
    idle.close()
    gecen = time.monotonic() - t0

    assert not sunucu.is_alive()
    assert gecen < 1.5

