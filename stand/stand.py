"""Stant ekranı: önden geçenlere canlı komik filtre + parmakla havada çizim ve imza duvarı.

  KAMERA=1 ..\\app\\.venv\\Scripts\\python.exe stand.py          (TAM_EKRAN=1 ile tam ekran açılır)
  ..\\app\\.venv\\Scripts\\python.exe stand.py --olc FOTO.jpg     pencere açmadan hız ölçer
  ..\\app\\.venv\\Scripts\\python.exe stand.py --onizleme FOTO.jpg CIKTI_KLASORU   her durumun ekran görüntüsü

Ekran üç durumda:
  BOŞ    kimse yok        karartılmış kamera, büyük başlık, imza duvarı galerisi, uçuşan emojiler
  UZAK   vücut var yüz yok   kafaya yapışan emoji, bileklerden parıltı, "Yaklaş!" çağrısı
  YAKIN  yüz görünüyor     her yüze efekt (6 sn'de bir değişir), parmak ucundan parıltı
Çizim: işaret parmağını 0.6 sn kaldır. İşaret = çiz, V = kalem kalkık, açık avuç = sil,
       üstteki renk dairesinde parmağı tut = renk seç, başparmak yukarı = duvara kaydet.
       El 2.5 sn görünmezse de çizim duvara eklenir.
Tuşlar: E sonraki efekt, C çizimi temizle, F tam ekran, Q/ESC çık.
Duvara yalnız çizim kaydedilir (kişinin fotoğrafı kaydedilmez): duvar/*.png
"""
import math
import os
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parent
MODEL = KOK.parent / "app" / "modeller"
DUVAR = KOK / "duvar"
HATA = KOK / "stand_hata.txt"
G, Y = 1280, 720
EFEKT_SN = 6.0
EL_KAYIP_SN = 2.5
BOS_SN = 1.5             # bu kadar süre kimse görünmezse tanıtım ekranı
BASLIK = os.environ.get("STANT_BASLIK", "MEME KAMERA")
RENKLER = [(255, 255, 255), (60, 60, 255), (60, 220, 255), (80, 220, 80), (255, 160, 40), (230, 80, 230)]  # BGR
EFEKTLER = ["Dev gözler", "Emoji kafa", "Kocaman kafa", "Thug life", "Dev ağız", "Kral tacı", "Minik yüz"]
EMOJILER = ["😎", "🤡", "👽", "🐸", "🤖", "💀", "😂", "🦄", "🐵", "🎃"]
FONT_YAZI = next((f for f in (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf",
                                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux (Türkçe harfler)
                                "/System/Library/Fonts/Supplemental/Arial Bold.ttf")  # macOS
                   if Path(f).is_file()), None)
FONT_EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"


# ---------------------------------------------------------------- kamera
class Kamera(threading.Thread):
    """Arka planda okur; 2 sn kare gelmezse kamerayı yeniden açar (kablo çıkıp takılırsa)."""

    def __init__(self, indeks: int):
        super().__init__(daemon=True)
        self.indeks = indeks
        self.cap = self._ac()
        self.kare, self.calis, self.t_son = None, True, time.time()

    def _ac(self):
        # KAMERA=http://... ise ağ yayını (ör. HP stant ekranının kamerası), değilse yerel kamera indeksi
        if isinstance(self.indeks, str) and not self.indeks.isdigit():
            cap = cv2.VideoCapture(self.indeks, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        cap = cv2.VideoCapture(int(self.indeks), cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, G)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Y)
        return cap

    def run(self):
        while self.calis:
            ok, f = self.cap.read()
            if ok:
                self.kare, self.t_son = cv2.resize(cv2.flip(f, 1), (G, Y)), time.time()
            elif time.time() - self.t_son > 2:
                self.cap.release()
                time.sleep(0.5)
                self.cap, self.t_son = self._ac(), time.time()
            else:
                time.sleep(0.01)

    def kapat(self):
        self.calis = False
        self.join(1)
        self.cap.release()


# ---------------------------------------------------------------- sprite (yazı, emoji) ve bindirme
def _pil_bgra(im: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGBA2BGRA)


@lru_cache(maxsize=256)
def yazi_sprite(metin: str, boyut: int, renk=(255, 255, 255)) -> np.ndarray:
    """Türkçe karakterli, siyah kenarlı yazı (BGRA). renk BGR."""
    f = ImageFont.truetype(FONT_YAZI, boyut) if FONT_YAZI else ImageFont.load_default()
    kenar = max(2, boyut // 12)
    x0, y0, x1, y1 = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), metin, font=f, stroke_width=kenar)
    im = Image.new("RGBA", (x1 - x0 + 2, y1 - y0 + 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-x0 + 1, -y0 + 1), metin, font=f, fill=tuple(renk[::-1]) + (255,),
                            stroke_width=kenar, stroke_fill=(0, 0, 0, 255))
    return _pil_bgra(im)


@lru_cache(maxsize=32)
def emoji_sprite(e: str, boyut: int = 256) -> np.ndarray:
    """Renkli emoji (Segoe UI Emoji), kenarlarına kırpılmış BGRA."""
    f = ImageFont.truetype(FONT_EMOJI, 109)   # renkli bitmap katmanı bu boyutta keskin
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), e, font=f, embedded_color=True)
    kutu = im.getbbox() or (0, 0, 160, 160)
    im = im.crop(kutu)
    olcek = boyut / max(im.size)
    im = im.resize((max(1, round(im.width * olcek)), max(1, round(im.height * olcek))), Image.LANCZOS)
    return _pil_bgra(im)


def bindir(img: np.ndarray, rgba: np.ndarray, x: int, y: int, opak: float = 1.0) -> None:
    """BGRA sprite'ı sol üst köşesi (x, y) olacak şekilde alfa ile yerinde bindirir; taşan kısım kırpılır."""
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(img.shape[1], x + w), min(img.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3] if opak >= 1 else cv2.convertScaleAbs(s[..., 3], alpha=opak)
    a3 = cv2.merge([a, a, a])
    bolge = img[y0:y1, x0:x1]
    on = cv2.multiply(np.ascontiguousarray(s[..., :3]), a3, scale=1 / 255)
    arka = cv2.multiply(bolge, cv2.bitwise_not(a3), scale=1 / 255)
    cv2.add(on, arka, dst=bolge)


def bindir_merkez(img, rgba, cx, cy, boyut=None, aci=0.0, opak=1.0) -> None:
    """Sprite'ı (cx, cy) merkezine, en uzun kenarı `boyut` piksel olacak ve `aci` derece döndürülmüş koyar."""
    rgba = donmus(rgba, boyut, aci)
    h, w = rgba.shape[:2]
    bindir(img, rgba, int(cx - w / 2), int(cy - h / 2), opak)


_DONMUS: dict = {}


def donmus(rgba, boyut=None, aci=0.0):
    """Boyutlandırılmış + döndürülmüş sprite; boyut 4 px, açı 2 derece adımla önbellekte (her kare yeniden hesaplanmaz)."""
    bq = None if boyut is None else max(4, int(round(boyut / 4)) * 4)
    aq = int(round(aci / 2)) * 2
    anahtar = (id(rgba), bq, aq)
    if anahtar not in _DONMUS:
        if len(_DONMUS) > 600:
            _DONMUS.clear()
        _DONMUS[anahtar] = _donmus_hesapla(rgba, bq, aq)
    return _DONMUS[anahtar]


def _donmus_hesapla(rgba, boyut, aci):
    if boyut is not None:
        olcek = boyut / max(rgba.shape[:2])
        rgba = cv2.resize(rgba, None, fx=olcek, fy=olcek, interpolation=cv2.INTER_LINEAR)
    if abs(aci) > 1:
        h, w = rgba.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), aci, 1.0)
        cos, sin = abs(M[0, 0]), abs(M[0, 1])
        yw, yh = int(h * sin + w * cos), int(h * cos + w * sin)
        M[0, 2] += yw / 2 - w / 2
        M[1, 2] += yh / 2 - h / 2
        rgba = cv2.warpAffine(rgba, M, (yw, yh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    return rgba


def yazi_koy(img, metin, x, y, boyut, renk=(255, 255, 255), hiza="sol", olcek=1.0, opak=1.0) -> None:
    s = yazi_sprite(metin, boyut, tuple(renk))
    if olcek != 1.0:
        s = cv2.resize(s, None, fx=olcek, fy=olcek, interpolation=cv2.INTER_LINEAR)
    if hiza == "orta":
        x -= s.shape[1] // 2
    elif hiza == "sag":
        x -= s.shape[1]
    bindir(img, s, int(x), int(y), opak)


# ---------------------------------------------------------------- yüz efektleri
def sisir(img: np.ndarray, cx: float, cy: float, r: float, k: float) -> None:
    """Yerinde mercek: k>0 büyüt (şişir), k<0 küçült. r yarıçapı dışında görüntü değişmez."""
    r = int(r)
    if r < 8:
        return
    x0, y0, x1, y1 = int(cx) - r, int(cy) - r, int(cx) + r, int(cy) + r
    if x0 < 0 or y0 < 0 or x1 >= img.shape[1] or y1 >= img.shape[0]:
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(img.shape[1] - 1, x1), min(img.shape[0] - 1, y1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    d = np.sqrt(dx * dx + dy * dy) / r
    olcek = np.where(d < 1, 1 - k * (1 - d * d) ** 2, 1).astype(np.float32)
    harita_x = (cx + dx * olcek).astype(np.float32)
    harita_y = (cy + dy * olcek).astype(np.float32)
    img[y0:y1, x0:x1] = cv2.remap(img, harita_x, harita_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def nokta(lm, i):
    return lm[i].x * G, lm[i].y * Y


def cizgi_acisi(a, b) -> float:
    """İki noktayı soldan sağa birleştiren çizginin cv2 döndürme açısı (derece, saat yönünün tersi +)."""
    if a[0] > b[0]:
        a, b = b, a
    return -math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def thug_gozluk(img: np.ndarray, lm) -> None:
    """Piksel 'deal with it' gözlüğü, göz çizgisine döndürülmüş."""
    sol, sag = np.array(nokta(lm, 33)), np.array(nokta(lm, 263))
    if sol[0] > sag[0]:
        sol, sag = sag, sol
    merkez = (sol + sag) / 2
    u = sag - sol
    gen = np.linalg.norm(u)
    if gen < 10:
        return
    u /= gen
    v = np.array([-u[1], u[0]])
    desen = ["XXXXXXXXXXXXXXXXXXXXXXX",
             "XXXXXXXXXXXXXXXXXXXXXXX",
             ".XWWXXXXX...XWWXXXXX...",
             ".XXWWXXXX...XXWWXXXX...",
             "..XXXXXX.....XXXXXX....",
             "...XXXX.......XXXX....."]
    hucre = gen * 2.1 / len(desen[0])
    sol_ust = merkez - u * hucre * len(desen[0]) / 2 - v * hucre * 2.2
    for j, satir in enumerate(desen):
        for i, c in enumerate(satir):
            if c == ".":
                continue
            p = sol_ust + u * hucre * i + v * hucre * j
            dortgen = np.array([p, p + u * hucre, p + u * hucre + v * hucre, p + v * hucre], np.int32)
            cv2.fillConvexPoly(img, dortgen, (255, 255, 255) if c == "W" else (10, 10, 10), cv2.LINE_AA)


def efekt_uygula(img: np.ndarray, lm, efekt: int, emoji: str = "😎") -> None:
    xs = np.array([p.x for p in lm]) * G
    ys = np.array([p.y for p in lm]) * Y
    yuz_r = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2
    goz_ara = np.linalg.norm(np.subtract(nokta(lm, 33), nokta(lm, 263)))
    aci = cizgi_acisi(nokta(lm, 33), nokta(lm, 263))
    ad = EFEKTLER[efekt]
    if ad == "Dev gözler":  # iris merkezleri (468, 473)
        for i in (468, 473):
            sisir(img, *nokta(lm, i), goz_ara * 0.55, 0.75)
    elif ad == "Emoji kafa":
        bindir_merkez(img, emoji_sprite(emoji), xs.mean(), ys.mean(), yuz_r * 2.6, aci)
    elif ad == "Kocaman kafa":
        sisir(img, xs.mean(), ys.mean(), yuz_r * 1.6, 0.6)
    elif ad == "Thug life":
        thug_gozluk(img, lm)
    elif ad == "Dev ağız":
        ax, ay = np.mean([nokta(lm, 13), nokta(lm, 14)], axis=0)
        sisir(img, ax, ay, goz_ara * 0.75, 0.8)
    elif ad == "Kral tacı":  # alın noktası 10, yüz yukarı yönünde biraz yukarı
        alin = np.array(nokta(lm, 10))
        yukari = alin - np.array(nokta(lm, 152))
        yukari /= np.linalg.norm(yukari) or 1
        cx, cy = alin + yukari * yuz_r * 0.85
        bindir_merkez(img, emoji_sprite("👑"), cx, cy, yuz_r * 1.9, aci)
    elif ad == "Minik yüz":
        sisir(img, xs.mean(), ys.mean(), yuz_r * 1.5, -0.6)


# ---------------------------------------------------------------- vücut (yüz görünmezken)
def poz_kafa(lm):
    """Poz noktalarından kafa merkezi, boyu ve açısı; kafa görünmüyorsa None. lm normalize (x, y, visibility)."""
    def gor(i):
        return getattr(lm[i], "visibility", 1.0) > 0.5
    if not gor(0):
        return None
    burun = np.array(nokta(lm, 0))
    if gor(7) and gor(8):
        k1, k2 = np.array(nokta(lm, 7)), np.array(nokta(lm, 8))
        gen = np.linalg.norm(k1 - k2)
        aci = cizgi_acisi(k1, k2)
        merkez = (k1 + k2) / 2 * 0.6 + burun * 0.4
    elif gor(11) and gor(12):
        gen = np.linalg.norm(np.subtract(nokta(lm, 11), nokta(lm, 12))) * 0.5
        aci, merkez = 0.0, burun
    else:
        return None
    if gen < 6:
        return None
    return float(merkez[0]), float(merkez[1] - gen * 0.15), float(gen * 2.3), aci


# ---------------------------------------------------------------- parıltı parçacıkları
class Parcaciklar:
    """Hafif numpy parçacık sistemi: yay() ile doğar, guncelle() ile yerçekimi ve sönme, ciz() ile toplamsal ışık."""

    def __init__(self, tavan: int = 900):
        self.tavan = tavan
        self.p = np.zeros((0, 2), np.float32)
        self.v = np.zeros((0, 2), np.float32)
        self.omur = np.zeros(0, np.float32)
        self.renk = np.zeros((0, 3), np.float32)

    def yay(self, x: float, y: float, adet: int, renk=None, hiz: float = 4.0) -> None:
        if adet <= 0:
            return
        aci = np.random.uniform(0, 2 * np.pi, adet)
        h = np.random.uniform(0.3, 1.0, adet) * hiz
        v = np.stack([np.cos(aci) * h, np.sin(aci) * h - hiz * 0.4], 1).astype(np.float32)
        if renk is None:
            hsv = np.stack([np.random.randint(0, 180, adet), np.full(adet, 200), np.full(adet, 255)], 1).astype(np.uint8)
            r = cv2.cvtColor(hsv[None], cv2.COLOR_HSV2BGR)[0].astype(np.float32)
        else:
            r = np.tile(np.float32(renk), (adet, 1))
        self.p = np.concatenate([self.p, np.tile(np.float32([x, y]), (adet, 1))])[-self.tavan:]
        self.v = np.concatenate([self.v, v])[-self.tavan:]
        self.omur = np.concatenate([self.omur, np.random.uniform(0.5, 1.1, adet).astype(np.float32)])[-self.tavan:]
        self.renk = np.concatenate([self.renk, r])[-self.tavan:]

    def guncelle(self, dt: float) -> None:
        dt = min(dt, 0.1)
        self.v[:, 1] += 9.0 * dt
        self.v *= 0.97
        self.p += self.v * dt * 30
        self.omur -= dt
        canli = self.omur > 0
        self.p, self.v, self.omur, self.renk = self.p[canli], self.v[canli], self.omur[canli], self.renk[canli]

    def ciz(self, img: np.ndarray) -> None:
        if not len(self.p):
            return
        katman = np.zeros_like(img)
        for (x, y), o, r in zip(self.p.astype(int), self.omur, self.renk):
            c = tuple(float(k * min(1.0, o * 1.5)) for k in r)
            cv2.circle(katman, (int(x), int(y)), 2 + int(4 * min(1.0, o)), c, -1, cv2.LINE_AA)
        cv2.add(img, katman, dst=img)


# ---------------------------------------------------------------- el
def uzanma(lm, uc):
    """Parmak ucu bileğe uzaklığı / el boyu: açık ~1.9, kıvrık ~1.0."""
    b = math.dist((lm[0].x, lm[0].y), (lm[9].x, lm[9].y)) or 1e-6
    return math.dist((lm[0].x, lm[0].y), (lm[uc].x, lm[uc].y)) / b


def el_durumu(lm) -> str:
    """'ciz' (yalnız işaret açık), 'kalk' (işaret+orta), 'sil' (avuç açık), 'yok'."""
    acik = [uzanma(lm, uc) > 1.45 for uc in (8, 12, 16, 20)]
    if all(acik):
        return "sil"
    if acik[0] and acik[1] and not acik[2] and not acik[3]:
        return "kalk"
    if acik[0] and not acik[1]:
        return "ciz"
    return "yok"


# ---------------------------------------------------------------- duvar
def duvar_yukle(adet: int = 12):
    DUVAR.mkdir(exist_ok=True)
    return [k for k in (cv2.imread(str(f)) for f in sorted(DUVAR.glob("*.png"))[-adet:]) if k is not None]


def kirp_sigdir(img: np.ndarray, w: int, h: int) -> np.ndarray:
    """Siyah zeminli çizimi çizgilerin kutusuna kırpar ve oranı koruyarak w×h kutunun ortasına sığdırır."""
    ys, xs = np.nonzero(img.max(axis=2) > 30)
    if len(xs):
        pay = int(0.08 * max(xs.max() - xs.min(), ys.max() - ys.min())) + 6
        img = img[max(0, ys.min() - pay): ys.max() + pay + 1, max(0, xs.min() - pay): xs.max() + pay + 1]
    olcek = min(w / img.shape[1], h / img.shape[0])
    k = cv2.resize(img, (max(1, int(img.shape[1] * olcek)), max(1, int(img.shape[0] * olcek))),
                   interpolation=cv2.INTER_AREA if olcek < 1 else cv2.INTER_LINEAR)
    tuval = np.zeros((h, w, 3), np.uint8)
    y0, x0 = (h - k.shape[0]) // 2, (w - k.shape[1]) // 2
    tuval[y0:y0 + k.shape[0], x0:x0 + k.shape[1]] = k
    return tuval


def bulanik_karanlik(img: np.ndarray, oran: float = 0.35) -> np.ndarray:
    """Ucuz bulanıklık (küçült-büyüt) + karartma: tanıtım ekranının arka planı."""
    kucuk = cv2.resize(img, (G // 16, Y // 16), interpolation=cv2.INTER_AREA)
    return cv2.convertScaleAbs(cv2.resize(kucuk, (G, Y), interpolation=cv2.INTER_LINEAR), alpha=oran)


# ---------------------------------------------------------------- sahne
class Stant:
    """Algılama sonuçlarından ekranı çizer; pencere ve modellerden bağımsız (testte sahte noktalarla sürülür)."""

    def __init__(self):
        self.kucukler = duvar_yukle()
        self.tuval = np.zeros((Y, G, 3), np.uint8)
        self.parca = Parcaciklar()
        self.efekt, self.t_efekt = 0, None
        self.mod, self.son_el, self.son_isaret_t, self.bas_t = "filtre", 0.0, None, None
        self.renk, self.renk_aday, self.renk_t = 0, None, 0.0
        self.kalem, self.onceki = None, None   # yumuşatılmış parmak ucu, son çizilen nokta
        self.durum, self.son_kisi = "bos", -1e9
        self.uc_onceki = {}
        self.mesaj, self.mesaj_t = None, 0.0
        self.t_onceki = None
        self._kucuk_onbellek = {}

    def kucuk(self, k, w, h):
        anahtar = (id(k), w, h)
        if anahtar not in self._kucuk_onbellek:
            self._kucuk_onbellek[anahtar] = kirp_sigdir(k, w, h)
        return self._kucuk_onbellek[anahtar]

    # -- yardımcılar
    def efekt_ilerlet(self, simdi):
        self.efekt, self.t_efekt = (self.efekt + 1) % len(EFEKTLER), simdi

    def bildir(self, metin, simdi):
        self.mesaj, self.mesaj_t = metin, simdi

    def duvara_kaydet(self, simdi) -> bool:
        if not self.tuval.any():
            return False
        DUVAR.mkdir(exist_ok=True)
        ad = DUVAR / f"{time.strftime('%Y%m%d-%H%M%S')}.png"
        cv2.imwrite(str(ad), cv2.resize(self.neon(self.tuval), (G // 2, Y // 2), interpolation=cv2.INTER_AREA))
        k = cv2.imread(str(ad))
        if k is not None:
            self.kucukler = (self.kucukler + [k])[-12:]
        self.bildir("İmzan duvara eklendi!", simdi)
        return True

    @staticmethod
    def neon(tuval: np.ndarray) -> np.ndarray:
        """Çizgilerin etrafına renkli ışık halesi."""
        kucuk = cv2.resize(tuval, (G // 4, Y // 4), interpolation=cv2.INTER_AREA)
        hale = cv2.resize(cv2.GaussianBlur(kucuk, (0, 0), 3), (G, Y), interpolation=cv2.INTER_LINEAR)
        return cv2.add(cv2.addWeighted(hale, 2.2, hale, 0, 0), tuval)

    def parilti_el(self, eller, simdi):
        """Her elin işaret parmağı ucundan, hızına göre parıltı saçar."""
        yeni = {}
        for i, lm in enumerate(eller):
            x, y = lm[8].x * G, lm[8].y * Y
            onceki = self.uc_onceki.get(i)
            hiz = math.dist((x, y), onceki) if onceki else 0
            self.parca.yay(x, y, int(min(10, 1 + hiz / 6)))
            yeni[i] = (x, y)
        self.uc_onceki = yeni

    # -- ana çizim
    def isle(self, kare, yuzler, eller, jestler, pozlar, simdi):
        if self.t_efekt is None:
            self.t_efekt = simdi
        dt = 0.0 if self.t_onceki is None else simdi - self.t_onceki
        self.t_onceki = simdi
        kafalar = [k for k in (poz_kafa(p) for p in pozlar) if k]

        if yuzler or kafalar or eller:
            self.son_kisi = simdi
        if yuzler:
            self.durum = "yakin"
        elif kafalar or eller:
            self.durum = "uzak"
        elif simdi - self.son_kisi > BOS_SN:
            self.durum = "bos"

        durum, uc, jest = "yok", None, None
        if eller:
            durum = el_durumu(eller[0])
            uc = (eller[0][8].x * G, eller[0][8].y * Y)
            jest = jestler[0] if jestler else None
            self.son_el = simdi

        if self.mod == "cizim":
            self._cizim(kare, durum, uc, jest, simdi)
        elif self.durum == "bos":
            kare = self._tanitim(kare, simdi)
        else:
            self._filtre(kare, yuzler, kafalar, eller, pozlar, durum, simdi)

        self.parca.guncelle(dt)
        self.parca.ciz(kare)
        if self.mesaj and simdi - self.mesaj_t < 2.2:
            yazi_koy(kare, self.mesaj, G // 2, Y // 2 - 50, 64, (80, 255, 120), "orta",
                     olcek=1.0 + 0.15 * max(0.0, 0.3 - (simdi - self.mesaj_t)) / 0.3)
        return kare

    def _filtre(self, kare, yuzler, kafalar, eller, pozlar, durum, simdi):
        if simdi - self.t_efekt > EFEKT_SN:
            self.efekt_ilerlet(simdi)
        tur = int(simdi // EFEKT_SN)
        for i, lm in enumerate(yuzler):
            efekt_uygula(kare, lm, self.efekt, EMOJILER[(i + tur) % len(EMOJILER)])
        if not yuzler:
            for i, (cx, cy, boy, aci) in enumerate(kafalar):
                bindir_merkez(kare, emoji_sprite(EMOJILER[(i + tur) % len(EMOJILER)]), cx, cy, boy, aci)
            for p in pozlar:   # bileklerden parıltı (el modeli uzaktan zor yakalar)
                for b in (15, 16):
                    if getattr(p[b], "visibility", 1.0) > 0.5:
                        self.parca.yay(p[b].x * G, p[b].y * Y, 2)
        self.parilti_el(eller, simdi)
        # işaret parmağı 0.6 sn kalkık kalırsa çizime geç
        if durum == "ciz":
            self.son_isaret_t = self.son_isaret_t or simdi
            gecen = simdi - self.son_isaret_t
            if eller:
                cx, cy = eller[0][8].x * G, eller[0][8].y * Y
                cv2.ellipse(kare, (int(cx), int(cy)), (26, 26), -90, 0, 360 * min(1.0, gecen / 0.6),
                            (0, 220, 255), 5, cv2.LINE_AA)
            if gecen > 0.6:
                self.mod, self.kalem, self.onceki, self.bas_t = "cizim", None, None, None
                self.tuval[:] = 0
        else:
            self.son_isaret_t = None

        if yuzler:
            yazi_koy(kare, EFEKTLER[self.efekt], 24, 18, 52, (0, 220, 255))
            dolu = min(1.0, (simdi - self.t_efekt) / EFEKT_SN)
            cv2.rectangle(kare, (26, 92), (26 + int(220 * dolu), 98), (0, 220, 255), -1)
            yazi_koy(kare, "İşaret parmağını kaldır: havaya çiz!", G - 24, 24, 30,
                     (255, 255, 255), "sag")
        else:
            nabiz = 1.0 + 0.06 * math.sin(simdi * 5)
            yazi_koy(kare, "Yaklaş! Yüzüne filtre gelsin", G // 2, 24, 56, (0, 220, 255), "orta", olcek=nabiz)
        self._duvar_serit(kare)

    def _duvar_serit(self, kare):
        if not self.kucukler:
            yazi_koy(kare, "İMZA DUVARI: işaret parmağını kaldır, çiz!", 20, Y - 52, 32, (0, 220, 255))
            return
        w, h = 150, 84
        for i, k in enumerate(self.kucukler[-8:]):
            x = 10 + i * (w + 8)
            kare[Y - h - 10: Y - 10, x: x + w] = self.kucuk(k, w, h)
            cv2.rectangle(kare, (x, Y - h - 10), (x + w, Y - 10), (255, 255, 255), 2)

    def _tanitim(self, kare, simdi):
        ekran = bulanik_karanlik(kare)
        # uçuşan emojiler (arkada)
        for i, e in enumerate(EMOJILER[:7]):
            t = simdi * 0.35 + i * 0.9
            x = G / 2 + math.sin(t * (0.7 + i * 0.13)) * (G * 0.44)
            y = Y / 2 + math.cos(t * (0.9 + i * 0.07) + i) * (Y * 0.32)
            bindir_merkez(ekran, emoji_sprite(e), x, y, 110, math.sin(t * 2) * 20, opak=0.85)
        if self.kucukler:   # imza galerisi: 4x3, en yenisi büyür
            sutun, w, h = 4, 272, 153
            liste = self.kucukler[-12:]
            satir = (len(liste) + sutun - 1) // sutun
            y0 = 175 + (3 - satir) * (h + 12) // 2
            vurgu = int(simdi / 1.5) % len(liste)
            for i, k in enumerate(liste):
                x = (G - sutun * (w + 12)) // 2 + (i % sutun) * (w + 12)
                y = y0 + (i // sutun) * (h + 12)
                ekran[y:y + h, x:x + w] = self.kucuk(k, w, h)
                cv2.rectangle(ekran, (x, y), (x + w, y + h), (0, 220, 255) if i == vurgu else (200, 200, 200),
                              4 if i == vurgu else 1)
            yazi_koy(ekran, "İMZA DUVARI", G // 2, 128, 34, (255, 255, 255), "orta")
        else:
            yazi_koy(ekran, "İlk imzayı sen at!", G // 2, Y // 2 - 40, 60, (255, 255, 255), "orta")
        nabiz = 1.0 + 0.05 * math.sin(simdi * 3)
        yazi_koy(ekran, BASLIK, G // 2, 30, 96, (0, 220, 255), "orta", olcek=nabiz)
        cagri = ["Yaklaş: yüzüne filtre gelsin", "İşaret parmağını kaldır: havaya imzanı at"][int(simdi / 3) % 2]
        yazi_koy(ekran, cagri, G // 2, Y - 80, 46, (255, 255, 255), "orta")
        return ekran

    def _cizim(self, kare, durum, uc, jest, simdi):
        if uc is not None:
            self.kalem = uc if self.kalem is None else (0.55 * self.kalem[0] + 0.45 * uc[0],
                                                        0.55 * self.kalem[1] + 0.45 * uc[1])
        cv2.convertScaleAbs(kare, dst=kare, alpha=0.55)   # çizim modunda kamera geri planda kalsın
        if self.tuval.any():   # çizimi neon ışıkla bindir (paletin altında kalsın)
            cv2.add(kare, self.neon(self.tuval), dst=kare)
        # renk paleti (üstte)
        secili = None
        for i, r in enumerate(RENKLER):
            cx = G // 2 - (len(RENKLER) - 1) * 45 + i * 90
            cv2.circle(kare, (cx, 50), 30 if i == self.renk else 22, r, -1, cv2.LINE_AA)
            cv2.circle(kare, (cx, 50), 30 if i == self.renk else 22, (0, 0, 0), 2, cv2.LINE_AA)
            if self.kalem and math.dist(self.kalem, (cx, 50)) < 40:
                secili = i
        if secili is not None:
            if secili != self.renk_aday:
                self.renk_aday, self.renk_t = secili, simdi
            elif simdi - self.renk_t > 0.4:
                self.renk = secili
            self.onceki = None
        elif durum == "ciz" and self.kalem:
            p = (int(self.kalem[0]), int(self.kalem[1]))
            if self.onceki:
                cv2.line(self.tuval, self.onceki, p, RENKLER[self.renk], 10, cv2.LINE_AA)
                self.parca.yay(p[0], p[1], 2, RENKLER[self.renk], hiz=2.5)
            self.onceki = p
        else:
            self.onceki = None
        if durum == "sil":
            self.tuval[:] = 0
        # başparmak yukarı 0.5 sn: duvara kaydet
        if jest == "Thumb_Up":
            self.bas_t = self.bas_t or simdi
            if simdi - self.bas_t > 0.5:
                self.duvara_kaydet(simdi)
                self.mod, self.son_isaret_t, self.bas_t = "filtre", None, None
                return
        else:
            self.bas_t = None
        if self.kalem:
            cv2.circle(kare, (int(self.kalem[0]), int(self.kalem[1])), 12, RENKLER[self.renk], 3, cv2.LINE_AA)
        yazi_koy(kare, "İşaret: çiz   V: kalemi kaldır   Avuç: sil   Başparmak yukarı: kaydet",
                 G // 2, Y - 60, 30, (255, 255, 255), "orta")
        if simdi - self.son_el > EL_KAYIP_SN:  # el gitti: duvara ekle, filtreye dön
            self.duvara_kaydet(simdi)
            self.mod, self.son_isaret_t = "filtre", None


# ---------------------------------------------------------------- algılama
class Algilayici:
    """Yüz + el her karede paralel; vücut modeli (35 ms) yalnız önceki karede yüz yoksa koşar."""

    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
        self.mp = mp
        taban = mp_python.BaseOptions
        video = vision.RunningMode.VIDEO
        self.yuz = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=taban(model_asset_path=str(MODEL / "face_landmarker.task")), running_mode=video, num_faces=4))
        self.el = vision.GestureRecognizer.create_from_options(vision.GestureRecognizerOptions(
            base_options=taban(model_asset_path=str(MODEL / "gesture_recognizer.task")), running_mode=video,
            num_hands=2, min_hand_detection_confidence=0.3, min_hand_presence_confidence=0.3,
            min_tracking_confidence=0.3))
        self.poz = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=taban(model_asset_path=str(MODEL / "pose_landmarker_lite.task")), running_mode=video,
            num_poses=3))
        self.havuz = ThreadPoolExecutor(3)
        self.ts, self.yuz_vardi = 0, False

    def algila(self, kare):
        self.ts += 33
        mpi = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(kare, cv2.COLOR_BGR2RGB))
        fy = self.havuz.submit(self.yuz.detect_for_video, mpi, self.ts)
        fe = self.havuz.submit(self.el.recognize_for_video, mpi, self.ts)
        fp = None if self.yuz_vardi else self.havuz.submit(self.poz.detect_for_video, mpi, self.ts)
        yuzler = fy.result().face_landmarks or []
        e = fe.result()
        pozlar = (fp.result().pose_landmarks or []) if fp else []
        jestler = [g[0].category_name if g and g[0].score > 0.6 else None for g in (e.gestures or [])]
        self.yuz_vardi = bool(yuzler)
        return yuzler, e.hand_landmarks or [], jestler, pozlar


def hata_yaz(e: BaseException) -> None:
    with open(HATA, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {''.join(traceback.format_exception(e))}\n")


def olc(foto: str, kare_sayisi: int = 60) -> None:
    """Pencere açmadan: bir fotoğrafla tüm hattın (algılama + çizim) kare süresini ölçer."""
    kare = cv2.resize(cv2.imread(foto), (G, Y))
    alg, st = Algilayici(), Stant()
    for durum_adi, yuz_zorla in (("yakin (yuz+el)", True), ("uzak (yuz+el+poz)", False)):
        sureler = []
        for i in range(kare_sayisi):
            alg.yuz_vardi = yuz_zorla
            t0 = time.perf_counter()
            y, e, j, p = alg.algila(kare)
            st.isle(kare.copy(), y, e, j, p, time.time())
            sureler.append(time.perf_counter() - t0)
        ms = np.median(sureler[5:]) * 1000
        print(f"{durum_adi}: {ms:.1f} ms/kare  ~{1000 / ms:.0f} FPS  yuz={len(y)} el={len(e)} poz={len(p)}")


def onizleme(foto: str, cikti: str) -> None:
    """Pencere açmadan her durumun bir ekran görüntüsünü yazar (gerçek algılama, fotoğraf kaydedilmez)."""
    out = Path(cikti)
    out.mkdir(parents=True, exist_ok=True)
    kare = cv2.resize(cv2.imread(foto), (G, Y))
    alg = Algilayici()
    y, e, j, _ = alg.algila(kare)
    alg.yuz_vardi = False
    _, _, _, p = alg.algila(kare)
    t = 1000.0
    for ad, efekt in (("yakin_emoji", 1), ("yakin_gozler", 0), ("yakin_tac", 5), ("yakin_thug", 3)):
        st = Stant()
        st.efekt, st.t_efekt = efekt, t
        cv2.imwrite(str(out / f"{ad}.png"), st.isle(kare.copy(), y, e, j, p, t + 0.1))
    st = Stant()
    cv2.imwrite(str(out / "uzak.png"), st.isle(kare.copy(), [], [], [], p, t))
    st = Stant()
    cv2.imwrite(str(out / "bos.png"), st.isle(kare.copy(), [], [], [], [], t + 5))
    print("onizleme:", sorted(f.name for f in out.glob("*.png")))


def main():
    alg = Algilayici()
    kam = Kamera(int(os.environ.get("KAMERA", "0")))
    kam.start()
    pencere = "Stant"
    cv2.namedWindow(pencere, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(pencere, G, Y)
    tam = os.environ.get("TAM_EKRAN") == "1"
    if tam:
        cv2.setWindowProperty(pencere, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    st = Stant()
    while True:
        if kam.kare is None:
            time.sleep(0.01)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
            continue
        kare = kam.kare.copy()
        simdi = time.time()
        try:
            kare = st.isle(kare, *alg.algila(kare), simdi)
        except Exception as e:  # stantta tek kare hatası uygulamayı kapatmasın
            hata_yaz(e)
        cv2.imshow(pencere, kare)
        k = cv2.waitKey(1) & 0xFF
        if k in (ord("q"), 27):
            break
        if k in (ord("e"), ord("E")):
            st.efekt_ilerlet(simdi)
        if k in (ord("c"), ord("C")):
            st.tuval[:] = 0
        if k in (ord("f"), ord("F")):
            tam = not tam
            cv2.setWindowProperty(pencere, cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN if tam else cv2.WINDOW_NORMAL)
        if cv2.getWindowProperty(pencere, cv2.WND_PROP_VISIBLE) < 1:
            break
    kam.kapat()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--olc":
        olc(sys.argv[2])
    elif len(sys.argv) > 3 and sys.argv[1] == "--onizleme":
        onizleme(sys.argv[2], sys.argv[3])
    else:
        main()
