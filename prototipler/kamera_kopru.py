"""HP-Laptop kamera koprusu ve DShow profil tarama modulu."""

import argparse
import math
import select
import socket
import struct
import sys
import threading
import time
import urllib.parse
from typing import Callable, Optional, Tuple

import cv2
import numpy as np

MAX_PAYLOAD = 8 * 1024 * 1024  # 8 MiB sinir
HEADER_STRUCT = struct.Struct("!QdI")  # sequence (uint64), t_cekim (double), payload_len (uint32)
PING_PONG_COUNT = 10
PING_STRUCT = struct.Struct("!d")       # t_istemci (double)
PONG_STRUCT = struct.Struct("!dd")      # t_istemci (double), t_sunucu (double)


def _tam_oku(sock: socket.socket, boyut: int, zaman_asimi: float = 1.0) -> Optional[bytes]:
    """Soketten mutlak monotonic deadline ile tam boyutta bayt okur; koparsa veya zaman asiminda None doner."""
    deadline = time.monotonic() + zaman_asimi
    tampon = bytearray()
    while len(tampon) < boyut:
        kalan = deadline - time.monotonic()
        if kalan <= 0:
            return None
        try:
            sock.settimeout(max(kalan, 0.001))
            parca = sock.recv(boyut - len(tampon))
            if not parca:
                return None
            tampon.extend(parca)
        except (socket.timeout, OSError):
            return None
    return bytes(tampon)


def _tam_gonder(sock: socket.socket, veri: bytes, zaman_asimi: float = 0.5) -> bool:
    """Tam veriyi mutlak monotonic deadline ile gonderir; zaman asimi veya soket hatasinda False doner."""
    deadline = time.monotonic() + zaman_asimi
    toplam = 0
    uzunluk = len(veri)
    while toplam < uzunluk:
        kalan = deadline - time.monotonic()
        if kalan <= 0:
            return False
        try:
            sock.settimeout(max(kalan, 0.001))
            gonderilen = sock.send(veri[toplam:])
            if gonderilen <= 0:
                return False
            toplam += gonderilen
        except (socket.timeout, OSError):
            return False
    return True


class Gonderici(threading.Thread):
    """Kamera karelerini sikistirip TCP uzerinden AgKamera'ya yayinlar."""

    def __init__(
        self,
        kaynak: Callable[[], Optional[np.ndarray]],
        adres: Tuple[str, int] = ("0.0.0.0", 8090),
        fps: float = 30.0,
    ):
        super().__init__(daemon=True)
        self.kaynak = kaynak
        self.fps = max(1.0, float(fps))
        self.calis = True
        self.hata: Optional[Exception] = None

        self.kare_no: int = 0
        self._son_jpeg: Optional[bytes] = None
        self._son_kare_no: int = 0
        self._son_t_cekim: float = 0.0
        self._kilit = threading.Lock()
        self._yeni_kare_olayi = threading.Event()

        self._istemci_kilit = threading.Lock()
        self._aktif_istemci: Optional[socket.socket] = None

        self._sunucu_soket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sunucu_soket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sunucu_soket.bind(adres)
        self._sunucu_soket.listen(1)
        self._sunucu_soket.settimeout(0.2)

        self.adres: Tuple[str, int] = self._sunucu_soket.getsockname()

        self._yakalama_ipligi = threading.Thread(
            target=self._yakalama_dongusu, daemon=True, name="GondericiYakalama"
        )

    def start(self):
        self._yakalama_ipligi.start()
        super().start()

    def _yakalama_dongusu(self):
        periyot = 1.0 / self.fps
        try:
            while self.calis:
                baslangic = time.monotonic()
                try:
                    kare = self.kaynak()
                except Exception as e:
                    self.hata = e
                    self.calis = False
                    break

                # Frame capture timestamp: read completion, not sensor hardware exposure
                t_cekim = time.time()

                if kare is not None:
                    if isinstance(kare, np.ndarray) and kare.size > 0:
                        try:
                            basarili, kodlanmis = cv2.imencode(
                                ".jpg", kare, [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                            )
                            if not basarili:
                                raise RuntimeError("cv2.imencode basarisiz")
                            jpeg_baytlar = kodlanmis.tobytes()
                        except Exception as e:
                            self.hata = e
                            self.calis = False
                            break

                        with self._kilit:
                            self.kare_no += 1
                            self._son_kare_no = self.kare_no
                            self._son_t_cekim = t_cekim
                            self._son_jpeg = jpeg_baytlar
                            self._yeni_kare_olayi.set()

                gecen = time.monotonic() - baslangic
                kalan = periyot - gecen
                if kalan > 0:
                    time.sleep(kalan)
        except Exception as e:
            self.hata = e
            self.calis = False
        finally:
            self._yeni_kare_olayi.set()

    def run(self):
        while self.calis:
            try:
                istemci_soket, _ = self._sunucu_soket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with self._istemci_kilit:
                self._aktif_istemci = istemci_soket

            try:
                self._istemciye_hizmet_et(istemci_soket)
            finally:
                with self._istemci_kilit:
                    if self._aktif_istemci is istemci_soket:
                        self._aktif_istemci = None
                try:
                    istemci_soket.close()
                except OSError:
                    pass

    def _istemciye_hizmet_et(self, istemci: socket.socket):
        try:
            istemci.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 64 * 1024)
        except OSError:
            pass

        try:
            # 10 Ping-Pong zaman senkronizasyonu
            for _ in range(PING_PONG_COUNT):
                if not self.calis:
                    return
                ping_verisi = _tam_oku(istemci, PING_STRUCT.size, zaman_asimi=1.0)
                if ping_verisi is None:
                    return
                (t_istemci,) = PING_STRUCT.unpack(ping_verisi)
                if not math.isfinite(t_istemci):
                    return
                t_sunucu = time.time()
                pong_verisi = PONG_STRUCT.pack(t_istemci, t_sunucu)
                if not _tam_gonder(istemci, pong_verisi, zaman_asimi=0.5):
                    return

            son_gonderilen_kare_no = 0

            # Baglanan her client onbellekteki en son kareyi yeni event beklemeden hemen alir
            with self._kilit:
                kare_no = self._son_kare_no
                t_cekim = self._son_t_cekim
                jpeg = self._son_jpeg

            if jpeg is not None and kare_no > 0:
                baslik = HEADER_STRUCT.pack(kare_no, t_cekim, len(jpeg))
                if not _tam_gonder(istemci, baslik + jpeg, zaman_asimi=0.5):
                    return
                son_gonderilen_kare_no = kare_no

            while self.calis:
                # Yeni kare bekle
                if not self._yeni_kare_olayi.wait(timeout=0.05):
                    # Kaynak duraklatilmisken veya yeni kare gelmezken istemci baglantiyi kesti mi kontrol et (MSG_PEEK)
                    try:
                        r, _, _ = select.select([istemci], [], [], 0)
                        if r:
                            peek = istemci.recv(1, socket.MSG_PEEK)
                            if not peek:
                                break  # Istemci kapandi / EOF
                    except (OSError, socket.error):
                        break
                    continue

                with self._kilit:
                    kare_no = self._son_kare_no
                    t_cekim = self._son_t_cekim
                    jpeg = self._son_jpeg
                    self._yeni_kare_olayi.clear()

                if jpeg is None or kare_no <= son_gonderilen_kare_no:
                    continue

                baslik = HEADER_STRUCT.pack(kare_no, t_cekim, len(jpeg))
                if not _tam_gonder(istemci, baslik + jpeg, zaman_asimi=0.5):
                    break
                son_gonderilen_kare_no = kare_no

        except (socket.timeout, BrokenPipeError, ConnectionResetError, OSError):
            pass

    def kapat(self):
        self.calis = False
        with self._istemci_kilit:
            if self._aktif_istemci is not None:
                try:
                    self._aktif_istemci.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    self._aktif_istemci.close()
                except OSError:
                    pass
        try:
            self._sunucu_soket.close()
        except OSError:
            pass
        self._yeni_kare_olayi.set()
        if self._yakalama_ipligi.is_alive():
            self._yakalama_ipligi.join(timeout=1.0)
        if self.is_alive():
            self.join(timeout=1.0)


class AgKamera(threading.Thread):
    """TCP uzerinden yayinlanan Gonderici kamerasina baglanip kareleri alir."""

    def __init__(self, adres: str = "tcp://192.168.77.2:8090"):
        super().__init__(daemon=True)
        self.raw_adres = adres
        self.host, self.port = self._ayristir_adres(adres)

        self.calis = True
        self.bagli: bool = False
        self.kare: Optional[np.ndarray] = None
        self.kare_no: int = 0
        self.t_son: float = 0.0
        self.t_alim: float = 0.0
        self.t_cekim: float = 0.0
        self.ofset_sn: float = 0.0
        self.rtt_ms: float = 0.0
        self.gecikme_ms: float = 0.0

        self._kapat_olayi = threading.Event()
        self._soket_kilit = threading.Lock()
        self._aktif_soket: Optional[socket.socket] = None

    @staticmethod
    def _ayristir_adres(url: str) -> Tuple[str, int]:
        if not isinstance(url, str) or not url.startswith("tcp://"):
            raise ValueError(f"Gecersiz protokol URL (tcp:// bekleniyor): {url}")
        parcalanmis = urllib.parse.urlsplit(url)
        host = parcalanmis.hostname
        port = parcalanmis.port
        if not host or port is None or not (1 <= port <= 65535):
            raise ValueError(f"Gecersiz ag adresi/portu: {url}")
        return host, port

    def run(self):
        while self.calis and not self._kapat_olayi.is_set():
            soket = None
            try:
                soket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                with self._soket_kilit:
                    self._aktif_soket = soket

                soket.settimeout(1.0)
                soket.connect((self.host, self.port))

                # 10 Ping-pong ile RTT ve ofset hesaplama
                en_iyi_rtt = float("inf")
                secilen_ofset = 0.0

                for _ in range(PING_PONG_COUNT):
                    if not self.calis or self._kapat_olayi.is_set():
                        raise ConnectionAbortedError("Durduruldu")
                    t0_mono = time.monotonic()
                    t0_wall = time.time()
                    ping_verisi = PING_STRUCT.pack(t0_wall)
                    if not _tam_gonder(soket, ping_verisi, zaman_asimi=0.5):
                        raise ConnectionResetError("Ping gonderilemedi")

                    pong_verisi = _tam_oku(soket, PONG_STRUCT.size, zaman_asimi=1.0)
                    if pong_verisi is None:
                        raise ConnectionResetError("Pong cevabi alinamadi")
                    t1_mono = time.monotonic()

                    t_istemci_echo, t_sunucu = PONG_STRUCT.unpack(pong_verisi)
                    if not (math.isfinite(t_istemci_echo) and math.isfinite(t_sunucu)):
                        raise ConnectionResetError("Pong gecersiz deger iceriyor")
                    if abs(t_istemci_echo - t0_wall) > 1.0:
                        raise ConnectionResetError("Pong echo uyusmuyor")

                    rtt = t1_mono - t0_mono
                    if rtt < en_iyi_rtt:
                        en_iyi_rtt = rtt
                        secilen_ofset = t_sunucu - (t0_wall + (rtt / 2.0))

                self.rtt_ms = en_iyi_rtt * 1000.0
                self.ofset_sn = secilen_ofset
                self.bagli = True

                # Kare akisi alma dongusu: idle frame timeout 1s
                while self.calis and not self._kapat_olayi.is_set():
                    baslik_bayt = _tam_oku(soket, HEADER_STRUCT.size, zaman_asimi=1.0)
                    if baslik_bayt is None:
                        break

                    kare_no, t_sunucu_cekim, uzunluk = HEADER_STRUCT.unpack(baslik_bayt)
                    if (
                        not math.isfinite(t_sunucu_cekim)
                        or uzunluk <= 0
                        or uzunluk > MAX_PAYLOAD
                    ):
                        break

                    jpeg_bayt = _tam_oku(soket, uzunluk, zaman_asimi=1.0)
                    if jpeg_bayt is None:
                        break

                    try:
                        dizi = np.frombuffer(jpeg_bayt, dtype=np.uint8)
                        kod_cozulmus = cv2.imdecode(dizi, cv2.IMREAD_COLOR)
                    except Exception:
                        kod_cozulmus = None

                    if kod_cozulmus is None:
                        break

                    t_simdi = time.time()
                    # Ayna ve olcekleme: yalnizca 1 kez yatay cevir ve 1280x720 yap
                    islenmis = cv2.flip(kod_cozulmus, 1)
                    if islenmis.shape[0] != 720 or islenmis.shape[1] != 1280:
                        islenmis = cv2.resize(
                            islenmis, (1280, 720), interpolation=cv2.INTER_LINEAR
                        )

                    self.t_alim = t_simdi
                    self.t_son = t_simdi
                    self.t_cekim = t_sunucu_cekim - self.ofset_sn
                    self.gecikme_ms = (self.t_alim - self.t_cekim) * 1000.0
                    self.kare_no = kare_no
                    self.kare = islenmis

            except (socket.timeout, OSError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                self.bagli = False
                with self._soket_kilit:
                    if soket:
                        try:
                            soket.close()
                        except OSError:
                            pass
                    self._aktif_soket = None

            if self.calis and not self._kapat_olayi.is_set():
                self._kapat_olayi.wait(timeout=1.0)

    def kapat(self):
        self.calis = False
        self.bagli = False
        self._kapat_olayi.set()
        with self._soket_kilit:
            if self._aktif_soket:
                try:
                    self._aktif_soket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    self._aktif_soket.close()
                except OSError:
                    pass
        if self.is_alive():
            self.join(timeout=2.0)


def _dshow_tara(kamera_idx: int, sure: float) -> int:
    """DirectShow format ve pozlama kombinasyonlarini tarayarak CSV olarak basar."""
    cozunurlukler = [(640, 480), (960, 540), (1280, 720)]
    pozlamalar = [
        ("auto", 0.75, None),
        ("man_-6", 0.25, -6.0),
        ("man_-4", 0.25, -4.0),
        ("man_-2", 0.25, -2.0),
    ]

    print(
        "istenen_w,istenen_h,istenen_fps,istenen_poz,surucu_w,surucu_h,surucu_fourcc,"
        "surucu_fps,surucu_poz_auto,surucu_poz_val,olculen_kare,olculen_sure_sn,olculen_fps"
    )

    toplam_basarili_kare = 0

    for gen, yuk in cozunurlukler:
        for poz_etiket, oto_deger, man_deger in pozlamalar:
            cap = None
            try:
                cap = cv2.VideoCapture(kamera_idx, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    continue

                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, gen)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, yuk)
                cap.set(cv2.CAP_PROP_FPS, 30.0)

                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, oto_deger)
                if man_deger is not None:
                    cap.set(cv2.CAP_PROP_EXPOSURE, man_deger)

                surucu_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                surucu_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc_raw = int(cap.get(cv2.CAP_PROP_FOURCC))
                surucu_fps = cap.get(cv2.CAP_PROP_FPS)
                surucu_auto = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                surucu_poz = cap.get(cv2.CAP_PROP_EXPOSURE)

                fourcc_str = "".join([chr((fourcc_raw >> 8 * i) & 0xFF) for i in range(4)])

                kare_sayac = 0
                t_baslangic = time.monotonic()
                t_bitis = t_baslangic + sure

                while time.monotonic() < t_bitis:
                    ret, _ = cap.read()
                    if ret:
                        kare_sayac += 1

                gerceklesen_sure = time.monotonic() - t_baslangic
                olculen_fps = kare_sayac / gerceklesen_sure if gerceklesen_sure > 0 else 0.0
                toplam_basarili_kare += kare_sayac

                print(
                    f"{gen},{yuk},30,{poz_etiket},{surucu_w},{surucu_h},{fourcc_str},"
                    f"{surucu_fps:.1f},{surucu_auto:.2f},{surucu_poz:.2f},{kare_sayac},"
                    f"{gerceklesen_sure:.2f},{olculen_fps:.2f}"
                )
            except Exception as e:
                print(f"Tarama hatasi: {e}", file=sys.stderr)
            finally:
                if cap is not None:
                    cap.release()

    return 0 if toplam_basarili_kare > 0 else 1


def _dshow_gonder(kamera_idx: int, host: str, port: int, fps: float, gen: int = 640, yuk: int = 480):
    """Kamerayi acar ve Gonderici ile TCP yayinina baslar."""
    cap = None
    gonderici = None
    try:
        cap = cv2.VideoCapture(kamera_idx, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, gen)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, yuk)
        cap.set(cv2.CAP_PROP_FPS, fps)

        if not cap.isOpened():
            print(f"HATA: Kamera {kamera_idx} acilamadi.", file=sys.stderr)
            sys.exit(1)
        print(f"Kamera modu: istenen {gen}x{yuk}, surucu "
              f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}", flush=True)

        def kare_kaynagi() -> Optional[np.ndarray]:
            ret, frame = cap.read()
            return frame if ret else None

        gonderici = Gonderici(kare_kaynagi, adres=(host, port), fps=fps)
        gonderici.start()
        print(f"Yayin basladi: {gonderici.adres[0]}:{gonderici.adres[1]} (Durdurmak icin Ctrl+C)")

        while gonderici.is_alive() and gonderici.calis:
            time.sleep(0.5)

        if gonderici.hata is not None:
            print(f"HATA: Gonderici hatasi: {gonderici.hata}", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"HATA: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if gonderici is not None:
            gonderici.kapat()
        if cap is not None:
            cap.release()
        print("\nYayin durduruldu, kaynaklar serbest birakildi.")


def main():
    parser = argparse.ArgumentParser(description="HP-Laptop Kamera Koprusu ve Profil Tarayici")
    grup = parser.add_mutually_exclusive_group(required=True)
    grup.add_argument("--gonder", action="store_true", help="Kamerayi ac ve TCP yayinina basla")
    grup.add_argument("--tara", action="store_true", help="Kamera profil ve pozlama matrisini tara")

    parser.add_argument("--kamera", type=int, default=0, help="Kamera aygit indeksi (varsayilan: 0)")
    parser.add_argument("--bind", type=str, default="192.168.77.2", help="Yayin IP adresi (varsayilan: 192.168.77.2)")
    parser.add_argument("--port", type=int, default=8090, help="Yayin portu (varsayilan: 8090)")
    parser.add_argument("--fps", type=float, default=30.0, help="Yayin hedef FPS (varsayilan: 30)")
    parser.add_argument("--sure", type=float, default=3.0, help="Tarama adim suresi (saniye, varsayilan: 3)")
    parser.add_argument("--boyut", type=str, default="640x480",
                        help="Gonderim cozunurlugu GxY (varsayilan: 640x480; 16:9 sensorde tam aci icin 1280x720)")

    args = parser.parse_args()

    if not (math.isfinite(args.fps) and args.fps > 0):
        print("HATA: --fps pozitif ve sonlu bir sayi olmalidir.", file=sys.stderr)
        sys.exit(1)
    if not (math.isfinite(args.sure) and args.sure > 0):
        print("HATA: --sure pozitif ve sonlu bir sayi olmalidir.", file=sys.stderr)
        sys.exit(1)

    if args.tara:
        kod = _dshow_tara(args.kamera, args.sure)
        sys.exit(kod)
    elif args.gonder:
        try:
            gen, yuk = (int(x) for x in args.boyut.lower().split("x"))
        except ValueError:
            parser.error(f"--boyut GxY olmali (ornek 1280x720): {args.boyut}")
        _dshow_gonder(args.kamera, args.bind, args.port, args.fps, gen, yuk)


if __name__ == "__main__":
    main()
