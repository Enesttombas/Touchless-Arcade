"""Ortak çekirdek modülü: algılama, ses sentezi, görsel yardımcılar ve stant arayüzü.

Prototip arayüzü:
  Her p_*.py dosyası bir `Prototip` sınıfı tanımlar:
    AD: str (Prototip adı)
    ACIKLAMA: str (Nasıl oynandığını anlatan tek satır açıklama)
    IHTIYAC: set (Örn: {"yuz", "el", "poz?"}; olası değerler: "yuz", "blend", "el", "poz", "poz?")
    SIRA: int (Gezgindeki sıra numarası, örn: 1)
    __init__(self, ses): Ses nesnesi alır
    isle(self, kare, algi, simdi) -> kare (BGR 1280x720 aynalı kare döner)
    tus(self, k): İsteğe bağlı tuş işleme metodu (k: int ASCII veya tuş kodu)
"""
from __future__ import annotations

import math
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

# stand modülünü içe aktarma
_stand_dizin = os.environ.get("STAND_DIZIN")
if _stand_dizin:
    _stand_yol = Path(_stand_dizin)
else:
    _stand_yol = Path(__file__).resolve().parent.parent / "stand"

if str(_stand_yol) not in sys.path:
    sys.path.insert(0, str(_stand_yol))

import stand

# stand'dan istenen adları yeniden dışa aktar
G = stand.G
Y = stand.Y
MODEL = stand.MODEL
Parcaciklar = stand.Parcaciklar


def Kamera(indeks: Any = 0) -> Any:
    """Kamera fabrikasi: 'tcp://' ile baslayan ag adresleri icin AgKamera, digerleri icin stand.Kamera."""
    if isinstance(indeks, str) and indeks.startswith("tcp://"):
        from kamera_kopru import AgKamera
        return AgKamera(indeks)
    return stand.Kamera(indeks)


bindir = stand.bindir
bindir_merkez = stand.bindir_merkez
emoji_sprite = stand.emoji_sprite
_EMOJI = __import__("re").compile("[\U0001F000-\U0001FFFF☀-➿️‍]")


def yazi_koy(img, metin, *a, **k):
    """stand.yazi_koy; yazı fontunda emoji yok (□ basar), emojiler ayıklanır. Emoji için emoji_sprite."""
    return stand.yazi_koy(img, _EMOJI.sub("", str(metin)).strip(), *a, **k)


yazi_sprite = stand.yazi_sprite
bulanik_karanlik = stand.bulanik_karanlik
uzanma = stand.uzanma
el_durumu = stand.el_durumu
Stant = stand.Stant

# Renk sabitleri (BGR)
SARI = (0, 220, 255)
CAMGOBEGI = (255, 220, 60)
PEMBE = (200, 80, 255)
YESIL = (90, 230, 90)
BEYAZ = (255, 255, 255)
KIRMIZI = (60, 60, 255)


# ---------------------------------------------------------------- Algılama Veri Yapısı ve Sınıfı
@dataclass
class Algi:
    yuzler: List[Any] = field(default_factory=list)
    blend: List[Dict[str, float]] = field(default_factory=list)
    eller: List[Any] = field(default_factory=list)
    el_taraf: List[str] = field(default_factory=list)
    jestler: List[Optional[str]] = field(default_factory=list)
    pozlar: List[Any] = field(default_factory=list)
    el_skor: List[float] = field(default_factory=list)
    jest_skor: List[float] = field(default_factory=list)
    yuz_id: List[int] = field(default_factory=list)
    el_id: List[int] = field(default_factory=list)
    poz_id: List[int] = field(default_factory=list)


class Algilayici:
    """MediaPipe tabanlı çoklu algılayıcı; sadece istenen modelleri ThreadPoolExecutor ile paralel koşturur."""

    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        self.mp = mp
        taban = mp_python.BaseOptions
        video = vision.RunningMode.VIDEO

        self.yuz = vision.FaceLandmarker.create_from_options(
            vision.FaceLandmarkerOptions(
                base_options=taban(model_asset_path=str(MODEL / "face_landmarker.task")),
                running_mode=video,
                num_faces=4,
                output_face_blendshapes=True,
                # stantta yüzler uzak/yan olabiliyor: varsayılan 0.5 ikinci oyuncuyu kaçırıyordu
                min_face_detection_confidence=0.35,
                min_face_presence_confidence=0.35,
                min_tracking_confidence=0.35,
            )
        )
        self._yari_yuz = None  # "yuz2" için ilk kullanımda kurulur (IMAGE modu, yarım kare)
        self._kalabalik_yuz = None  # "kalabalik": arka arkaya duran kalabalık için 12 yüzlük ayrı model
        self.el = vision.GestureRecognizer.create_from_options(
            vision.GestureRecognizerOptions(
                base_options=taban(model_asset_path=str(MODEL / "gesture_recognizer.task")),
                running_mode=video,
                num_hands=2,
                min_hand_detection_confidence=0.3,
                min_hand_presence_confidence=0.3,
                min_tracking_confidence=0.3,
            )
        )
        self.poz = vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=taban(model_asset_path=str(MODEL / "pose_landmarker_lite.task")),
                running_mode=video,
                num_poses=6,
            )
        )
        self.havuz = ThreadPoolExecutor(3)
        self.ts = 0
        self.yuz_vardi = False

    def _yarilarda_ara(self, rgb: np.ndarray, yuzler: List[Any], blend: List[Dict[str, float]]):
        """İki kişilik oyunlarda: tam karede 2 yüz yoksa sol/sağ yarıyı ayrı tarar (yüz modele 2 kat büyük
        görünür, uzaktaki ya da yandaki ikinci oyuncu da bulunur). Bulunanı tam kare koordinatına çevirir."""
        if self._yari_yuz is None:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
            self._yari_yuz = [vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(MODEL / "face_landmarker.task")),
                running_mode=vision.RunningMode.IMAGE, num_faces=2, output_face_blendshapes=True,
                min_face_detection_confidence=0.3, min_face_presence_confidence=0.3)) for _ in range(3)]
        W = rgb.shape[1]
        pay = W // 10
        parcalar = [(0, 0, W // 2 + pay), (1, W // 2 - pay, W), (2, W // 4, 3 * W // 4)]  # sol, sağ, orta

        def tara(i: int, x0: int, x1: int):
            parca = np.ascontiguousarray(rgb[:, x0:x1])
            return x0, x1, self._yari_yuz[i].detect(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=parca))

        while len(blend) < len(yuzler):
            blend.append({})
        for x0, x1, r in self.havuz.map(lambda a: tara(*a), parcalar):
            olcek, kay = (x1 - x0) / W, x0 / W
            for j, nokta in enumerate(r.face_landmarks or []):
                yeni = [_Nokta(n.x * olcek + kay, n.y, n.z) for n in nokta]
                if any(abs(y[1].x - yeni[1].x) < 0.06 and abs(y[1].y - yeni[1].y) < 0.1 for y in yuzler):
                    continue  # zaten bulunmuş yüz
                yuzler.append(yeni)
                bs = r.face_blendshapes[j] if r.face_blendshapes and j < len(r.face_blendshapes) else []
                blend.append({c.category_name: c.score for c in bs})
        return yuzler, blend

    def algila(self, kare_bgr: np.ndarray, ihtiyac: Set[str]) -> Algi:
        self.ts += 33

        kos_yuz = bool(ihtiyac & {"yuz", "blend", "poz?"})
        kos_el = "el" in ihtiyac

        kos_poz = False
        if "poz" in ihtiyac:
            kos_poz = True
        elif "poz?" in ihtiyac and not self.yuz_vardi:
            kos_poz = True

        if not (kos_yuz or kos_el or kos_poz):
            return Algi()

        rgb = cv2.cvtColor(kare_bgr, cv2.COLOR_BGR2RGB)
        mpi = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)

        yuz_modeli = self.yuz
        if "kalabalik" in ihtiyac:
            if self._kalabalik_yuz is None:
                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision
                self._kalabalik_yuz = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
                    base_options=mp_python.BaseOptions(model_asset_path=str(MODEL / "face_landmarker.task")),
                    running_mode=vision.RunningMode.VIDEO, num_faces=12, output_face_blendshapes=False,
                    min_face_detection_confidence=0.3, min_face_presence_confidence=0.3, min_tracking_confidence=0.3))
            yuz_modeli = self._kalabalik_yuz
        fy = self.havuz.submit(yuz_modeli.detect_for_video, mpi, self.ts) if kos_yuz else None
        fe = self.havuz.submit(self.el.recognize_for_video, mpi, self.ts) if kos_el else None
        fp = self.havuz.submit(self.poz.detect_for_video, mpi, self.ts) if kos_poz else None

        yuzler: List[Any] = []
        blend: List[Dict[str, float]] = []
        if fy is not None:
            ry = fy.result()
            yuzler = ry.face_landmarks or []
            if ry.face_blendshapes:
                for b_list in ry.face_blendshapes:
                    blend.append({cat.category_name: cat.score for cat in b_list})
            if "yuz2" in ihtiyac and len(yuzler) < 2:
                yuzler, blend = self._yarilarda_ara(rgb, list(yuzler), list(blend))
            self.yuz_vardi = bool(yuzler)

        eller: List[Any] = []
        el_taraf: List[str] = []
        el_skor: List[float] = []
        jestler: List[Optional[str]] = []
        jest_skor: List[float] = []
        if fe is not None:
            re = fe.result()
            eller = re.hand_landmarks or []
            if re.handedness:
                for h in re.handedness:
                    el_taraf.append(h[0].category_name if h else "")
                    el_skor.append(h[0].score if h else 0.0)
            if re.gestures:
                for g in re.gestures:
                    jest_skor.append(g[0].score if g else 0.)
                    if g and g[0].score > 0.6:
                        jestler.append(g[0].category_name)
                    else:
                        jestler.append(None)

        pozlar: List[Any] = []
        if fp is not None:
            rp = fp.result()
            pozlar = rp.pose_landmarks or []

        return Algi(
            yuzler=yuzler,
            blend=blend,
            eller=eller,
            el_taraf=el_taraf,
            el_skor=el_skor,
            jestler=jestler,
            jest_skor=jest_skor,
            pozlar=pozlar,
        )


class Maskeci:
    """Kişi maskesi arka planda (poz segmentasyonu ~37 ms, döngüyü bekletmez). ver(kare) -> son maske
    (Y//2, G//2) float32 0..1, ya da henüz/hiç yoksa None (model açılmazsa hep None)."""

    def __init__(self):
        self.maske, self._kare, self._olay = None, None, threading.Event()
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
            self._mod = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(MODEL / "pose_landmarker_lite.task")),
                running_mode=vision.RunningMode.VIDEO, num_poses=6, output_segmentation_masks=True))
            threading.Thread(target=self._dongu, daemon=True).start()
        except Exception:  # noqa: BLE001
            self._mod = None

    def ver(self, kare: np.ndarray):
        if self._mod is not None:
            self._kare = cv2.resize(kare, (G // 2, Y // 2), interpolation=cv2.INTER_AREA)
            self._olay.set()
        return self.maske

    def _dongu(self):
        import mediapipe as mp
        ts = 0
        while True:
            self._olay.wait()
            self._olay.clear()
            ts += 33
            try:
                rgb = cv2.cvtColor(self._kare, cv2.COLOR_BGR2RGB)
                r = self._mod.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
                m = np.zeros((Y // 2, G // 2), np.float32)
                for s in r.segmentation_masks or []:  # birden çok kişi: birleşim
                    m = np.maximum(m, cv2.resize(s.numpy_view().squeeze(), (G // 2, Y // 2)))
                self.maske = m
            except Exception:  # noqa: BLE001
                pass


def on_plan(m: np.ndarray, oran: float = 0.3, min_alan: float = 0.004) -> np.ndarray:
    """Kalabalık süzgeci: en büyük kişi lekesinin `oran`ından küçük lekeleri (arkadan geçenler) atar.
    Öndeki oyuncu(lar) kalır; tek leke varsa maske aynen döner."""
    ikili = (m > 0.5).astype(np.uint8)
    n, etiket, ist, _ = cv2.connectedComponentsWithStats(ikili, connectivity=8)
    if n <= 2:
        return m
    alan = ist[1:, cv2.CC_STAT_AREA]
    tut = np.zeros(n, np.uint8)
    tut[1:] = alan >= max(alan.max() * oran, min_alan * m.size)
    if tut[1:].all():
        return m
    kalan = cv2.dilate(tut[etiket], cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    return m * kalan.astype(m.dtype)


# ---------------------------------------------------------------- Ses Sentezi ve Çalma
def sentez(ad: str, hz: int = 44100) -> np.ndarray:
    """Kısa ses efektleri veya MIDI notası sentezler.

    Çıktı float64/float32 dizisi [-1.0, 1.0], 0.01sn .. 2.0sn, tepe > 0.01.
    """
    rng = np.random.RandomState(42)

    if ad == "kick":
        sure = 0.22
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        f = 140 * np.exp(-t * 22) + 35
        faz = 2 * np.pi * np.cumsum(f) / hz
        dalga = np.sin(faz) * np.exp(-t * 14)

    elif ad == "snare":
        sure = 0.18
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        ton = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 28)
        gurultu = rng.uniform(-1.0, 1.0, len(t)) * np.exp(-t * 18)
        dalga = 0.4 * ton + 0.6 * gurultu

    elif ad == "hihat":
        sure = 0.06
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        gurultu = rng.uniform(-1.0, 1.0, len(t))
        dalga = gurultu * np.exp(-t * 60)

    elif ad == "clap":
        sure = 0.2
        N = int(hz * sure)
        dalga = np.zeros(N, dtype=np.float64)
        for gecikme_ms in [0, 12, 24]:
            bas = int(hz * (gecikme_ms / 1000.0))
            kalan = N - bas
            if kalan > 0:
                tk = np.linspace(0, kalan / hz, kalan, endpoint=False)
                gk = rng.uniform(-1.0, 1.0, kalan) * np.exp(-tk * 35)
                dalga[bas:] += gk * 0.5

    elif ad == "pop":
        sure = 0.05
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        f = 400 + 400 * np.exp(-t * 40)
        faz = 2 * np.pi * np.cumsum(f) / hz
        dalga = np.sin(faz) * np.exp(-t * 50)

    elif ad == "ding":
        sure = 0.5
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        dalga = (np.sin(2 * np.pi * 1200 * t) * 0.7 + np.sin(2 * np.pi * 2400 * t) * 0.3) * np.exp(-t * 7)

    elif ad == "bonk":
        sure = 0.15
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        f = 320 * np.exp(-t * 25)
        faz = 2 * np.pi * np.cumsum(f) / hz
        dalga = np.sin(faz) * np.exp(-t * 18)

    elif ad == "woosh":
        sure = 0.35
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        zarf = np.sin(np.pi * t / sure) ** 2
        gurultu = rng.uniform(-1.0, 1.0, len(t))
        dalga = gurultu * zarf

    elif ad == "basari":
        sure = 0.4
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        aralik = int(len(t) / 3)
        dalga = np.zeros(len(t), dtype=np.float64)
        farkli_f = [523.25, 659.25, 783.99]  # C5, E5, G5
        for i, f_nota in enumerate(farkli_f):
            bas = i * aralik
            son = (i + 1) * aralik if i < 2 else len(t)
            alt_t = np.linspace(0, (son - bas) / hz, son - bas, endpoint=False)
            dalga[bas:son] = np.sin(2 * np.pi * f_nota * alt_t) * np.exp(-alt_t * 5)

    elif ad == "zap":
        sure = 0.15
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        f = 1200 * (1.0 - t / sure) ** 2 + 100
        faz = 2 * np.pi * np.cumsum(f) / hz
        dalga = np.sin(faz) * np.exp(-t * 10)

    elif ad.startswith("nota") and ad[4:].isdigit():
        nn = int(ad[4:])
        frec = 440.0 * (2.0 ** ((nn - 69) / 12.0))
        sure = 0.6
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        # Yumuşak çan: temel ve harmonikler
        dalga = (
            np.sin(2 * np.pi * frec * t) * 0.7
            + np.sin(2 * np.pi * frec * 2 * t) * 0.2
            + np.sin(2 * np.pi * frec * 3 * t) * 0.1
        ) * np.exp(-t * 4.5)

    else:
        # Bilinmeyen ad: kısa bip
        sure = 0.08
        t = np.linspace(0, sure, int(hz * sure), endpoint=False)
        dalga = np.sin(2 * np.pi * 600 * t) * np.exp(-t * 15)

    tepe = np.abs(dalga).max()
    if tepe > 1e-6:
        dalga = dalga / tepe * 0.95
    else:
        dalga = np.full_like(dalga, 0.5)

    return dalga.astype(np.float32)


class Ses:
    """Pygame mikserini yönetir ve ses çalar; hataları sessizce yutar."""

    def __init__(self, acik: bool = True):
        self.acik = acik
        self.onbellek: Dict[str, Any] = {}
        self.kanallar = 1
        if not self.acik:
            return

        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=1024)
            aktif = pygame.mixer.get_init()
            if aktif:
                self.kanallar = aktif[2]
                pygame.mixer.set_num_channels(24)
            else:
                self.acik = False
        except Exception:
            self.acik = False

    def cal(self, ad: str, ses: float = 0.7) -> None:
        if not self.acik:
            return

        try:
            import pygame

            snd = self.onbellek.get(ad)
            if snd is None:
                d = sentez(ad, 44100)
                d16 = (d * 32767).clip(-32768, 32767).astype(np.int16)
                if self.kanallar == 2:
                    d_ses = np.column_stack([d16, d16])
                else:
                    d_ses = d16
                snd = pygame.sndarray.make_sound(d_ses)
                self.onbellek[ad] = snd

            snd.set_volume(max(0.0, min(1.0, float(ses))))
            snd.play()
        except Exception:
            pass


# ---------------------------------------------------------------- Görsel Yardımcılar
def px(lm: Any, i: int) -> Tuple[float, float]:
    """Landmark noktasını piksel koordinatına çevirir (x*G, y*Y)."""
    return lm[i].x * G, lm[i].y * Y


def panel(
    img: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    renk: Tuple[int, int, int] = (20, 20, 28),
    opak: float = 0.6,
    kenar: Optional[Tuple[int, int, int]] = None,
) -> None:
    """Yarı saydam koyu panel çizer. Koordinatlar görüntü dışına taşsa da çökmez."""
    H, W = img.shape[:2]
    cx0, cy0 = max(0, int(x0)), max(0, int(y0))
    cx1, cy1 = min(W, int(x1)), min(H, int(y1))

    if cx1 > cx0 and cy1 > cy0:
        bolge = img[cy0:cy1, cx0:cx1]
        renk_bgr = np.array(renk, dtype=np.uint8)
        cv2.addWeighted(bolge, 1.0 - opak, np.full_like(bolge, renk_bgr), opak, 0, dst=bolge)

    if kenar is not None:
        cv2.rectangle(img, (int(x0), int(y0)), (int(x1), int(y1)), kenar, 1, cv2.LINE_AA)


def baslik(
    img: np.ndarray,
    metin: str,
    alt: Optional[str] = None,
    renk: Tuple[int, int, int] = SARI,
) -> None:
    """Üst ortada 50 px başlık + 28 px alt satır koyar."""
    yazi_koy(img, metin, G // 2, 24, 50, renk=renk, hiza="orta")
    if alt:
        yazi_koy(img, alt, G // 2, 84, 28, renk=BEYAZ, hiza="orta")


def halka(
    img: np.ndarray,
    cx: int,
    cy: int,
    oran: float,
    r: int = 34,
    renk: Tuple[int, int, int] = SARI,
    kalinlik: int = 6,
) -> None:
    """0..1 dolum halkası (-90 dereceden başlar)."""
    oran = max(0.0, min(1.0, float(oran)))
    if oran <= 0:
        return
    aci = int(360 * oran)
    cv2.ellipse(
        img,
        (int(cx), int(cy)),
        (int(r), int(r)),
        -90,
        0,
        aci,
        renk,
        kalinlik,
        cv2.LINE_AA,
    )


def parilti(
    img: np.ndarray,
    katman: np.ndarray,
    guc: float = 1.8,
    sigma: float = 3.0,
) -> None:
    """Siyah zeminli parlak katmanı çeyrek çözünürlükte bulanıklaştırıp hale olarak + katmanın kendisini toplar."""
    H, W = img.shape[:2]
    kucuk = cv2.resize(katman, (max(1, W // 4), max(1, H // 4)), interpolation=cv2.INTER_AREA)
    hale_kucuk = cv2.GaussianBlur(kucuk, (0, 0), sigma)
    hale = cv2.resize(hale_kucuk, (W, H), interpolation=cv2.INTER_LINEAR)
    hale_guc = cv2.convertScaleAbs(hale, alpha=guc)
    cv2.add(img, hale_guc, dst=img)
    cv2.add(img, katman, dst=img)


# ---------------------------------------------------------------- Sahte Veri Üreticileri
class _Nokta:
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class _NoktaPoz:
    def __init__(self, x: float, y: float, z: float = 0.0, visibility: float = 0.95):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.visibility = float(visibility)


def sahte_el(
    x: float = 0.5,
    y: float = 0.5,
    durum: str = "isaret",
    olcek: float = 0.1,
) -> List[_Nokta]:
    """21 nokta: bilek (x, y+2*olcek), orta MCP 9 (x, y+olcek), işaret 8 ≈ (x, y).

    stand.el_durumu ile sırasıyla 'ciz', 'sil', 'kalk', 'yok' vermeli.
    """
    pts = [_Nokta(x, y + 2.0 * olcek) for _ in range(21)]
    pts[9] = _Nokta(x, y + olcek)

    acik_8 = durum in ("isaret", "avuc", "v")
    acik_12 = durum in ("avuc", "v")
    acik_16 = durum == "avuc"
    acik_20 = durum == "avuc"

    pts[8] = _Nokta(x, y) if acik_8 else _Nokta(x, y + olcek)
    pts[12] = _Nokta(x, y) if acik_12 else _Nokta(x, y + olcek)
    pts[16] = _Nokta(x, y) if acik_16 else _Nokta(x, y + olcek)
    pts[20] = _Nokta(x, y) if acik_20 else _Nokta(x, y + olcek)

    return pts


def sahte_yuz(cx: float = 0.5, cy: float = 0.5, r: float = 0.15) -> List[_Nokta]:
    """478 nokta: gözler, dudaklar, burun, çene ve alın anlamlı yerlerde."""
    pts = [_Nokta(cx, cy) for _ in range(478)]

    # Gözler ve irisler
    # 33: sol göz dış, 263: sağ göz dış
    pts[33] = _Nokta(cx - r * 0.45, cy - r * 0.15)
    pts[263] = _Nokta(cx + r * 0.45, cy - r * 0.15)
    # İrisler
    pts[468] = _Nokta(cx - r * 0.35, cy - r * 0.15)
    pts[473] = _Nokta(cx + r * 0.35, cy - r * 0.15)
    # Göz kapakları
    pts[159] = _Nokta(cx - r * 0.35, cy - r * 0.22)
    pts[145] = _Nokta(cx - r * 0.35, cy - r * 0.08)
    pts[386] = _Nokta(cx + r * 0.35, cy - r * 0.22)
    pts[386] = _Nokta(cx + r * 0.35, cy - r * 0.22)
    pts[374] = _Nokta(cx + r * 0.35, cy - r * 0.08)

    # Burun
    pts[1] = _Nokta(cx, cy)

    # Dudaklar ve ağız köşeleri
    # 13: üst dudak iç, 14: alt dudak iç
    pts[13] = _Nokta(cx, cy + r * 0.38)
    pts[14] = _Nokta(cx, cy + r * 0.45)
    # 61: sol ağız köşesi, 291: sağ ağız köşesi
    pts[61] = _Nokta(cx - r * 0.25, cy + r * 0.42)
    pts[291] = _Nokta(cx + r * 0.25, cy + r * 0.42)

    # Alın ve çene
    pts[10] = _Nokta(cx, cy - r * 0.8)
    pts[152] = _Nokta(cx, cy + r * 0.8)

    return pts


def sahte_poz(cx: float = 0.5, cy: float = 0.5, s: float = 1.0) -> List[_NoktaPoz]:
    """33 nokta ayakta kişi: 0,2,5,7,8,11-16,17-22,23-28 görünür (0.95), diğerleri 0.1."""
    gorunur_indeksler = {
        0, 2, 5, 7, 8,
        11, 12, 13, 14, 15, 16,
        17, 18, 19, 20, 21, 22,
        23, 24, 25, 26, 27, 28,
    }

    pts: List[_NoktaPoz] = []
    for i in range(33):
        v = 0.95 if i in gorunur_indeksler else 0.1
        pts.append(_NoktaPoz(cx, cy, 0.0, visibility=v))

    return pts
