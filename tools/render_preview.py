"""tools/render_preview.py: Headless synthetic renderer for menu.png and demo.gif.

Uses actual app rendering and synthetic landmarks, without camera/audio/MediaPipe initialization.
Output targets:
- docs/media/menu.png
- docs/media/demo.gif
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import List

import cv2
import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "oyunlar"))

import cekirdek as ck
import stant_app

OYUN_BILGILERI = [
    ("p_neon_kilic", "Neon Kılıç"),
    ("p_gulmeme", "Gülme Düellosu"),
    ("p_maske", "AR Maskeler"),
    ("p_parmak_kusu", "Kanat Rotası"),
    ("p_cevap_yagmuru", "Bilgi Yağmuru"),
    ("p_refleks", "Silahşor Düellosu"),
    ("p_hayalet_klon", "Hayalet Klonlar"),
    ("p_penalti", "Altın Vuruş"),
    ("p_ciz_tahmin", "Çizim Kâhini"),
]


def _arkaplan(t: float = 0.0) -> np.ndarray:
    """Canlı aynalı kamera arka planını simüle eden sentetik arka plan (mor/mavi tonlu stant ortamı)."""
    kare = np.zeros((ck.Y, ck.G, 3), dtype=np.uint8)
    ys = np.linspace(25, 45, ck.Y)[:, None]
    xs = np.linspace(35, 65, ck.G)[None, :]
    kare[:, :, 0] = np.clip(xs * 0.7 + ys * 0.5 + 8 * math.sin(t * 1.5), 0, 255).astype(np.uint8)
    kare[:, :, 1] = np.clip(ys * 0.8 + 20, 0, 255).astype(np.uint8)
    kare[:, :, 2] = np.clip(xs * 0.9 + 30, 0, 255).astype(np.uint8)
    for x in range(120, ck.G, 200):
        cv2.line(kare, (x, 0), (x - 60, ck.Y), (45, 35, 55), 2, cv2.LINE_AA)
    return kare


def sahte_menu_algi(cx: float, cy: float, jest: str = "Open_Palm", olcek: float = 0.08) -> ck.Algi:
    """Menü için landmark 9'u tam (cx, cy) merkezine koyan ve kapi filtresinden geçen sahte algı."""
    a = ck.Algi()
    el = ck.sahte_el(cx, cy - olcek, "avuc" if jest == "Open_Palm" else "isaret", olcek=olcek)
    a.eller = [el]
    a.el_taraf = ["Right"]
    a.el_skor = [0.95]
    a.jestler = [jest]
    a.jest_skor = [0.95]
    return a


def sahte_oyun_algi(o_idx: int, t: float, step: int) -> ck.Algi:
    """Her deneyim için uygun ve doğal sentetik algı verisi üretir."""
    a = ck.Algi()
    if o_idx == 0:  # p_neon_kilic
        hx = 0.25 + 0.5 * ((step + 1) / 4)
        hy = 0.55 - 0.2 * math.sin(step * 1.1)
        el = ck.sahte_el(hx, hy, "isaret", olcek=0.08)
        a.eller = [el]
        a.el_taraf = ["Right"]
        a.el_skor = [0.95]
        a.jestler = ["Pointing_Up"]
        a.jest_skor = [0.95]
    elif o_idx == 1:  # p_gulmeme
        y1 = ck.sahte_yuz(0.30, 0.40, 0.12)
        y2 = ck.sahte_yuz(0.70, 0.40, 0.12)
        b1 = {"jawOpen": 0.05, "mouthSmileLeft": 0.75, "mouthSmileRight": 0.75}
        b2 = {"jawOpen": 0.02, "mouthSmileLeft": 0.05, "mouthSmileRight": 0.05}
        a.yuzler = [y1, y2]
        a.blend = [b1, b2]
    elif o_idx == 2:  # p_maske
        y = ck.sahte_yuz(0.50, 0.42, 0.14)
        a.yuzler = [y]
        a.blend = [{"jawOpen": 0.4, "browInnerUp": 0.3}]
    elif o_idx == 3:  # p_parmak_kusu
        hy = 0.40 + 0.18 * math.sin(step * 1.3)
        el = ck.sahte_el(0.48, hy, "isaret", olcek=0.08)
        a.eller = [el]
        a.el_taraf = ["Right"]
        a.el_skor = [0.95]
        a.jestler = ["Pointing_Up"]
        a.jest_skor = [0.95]
    elif o_idx == 4:  # p_cevap_yagmuru
        px_pos = 0.35 + 0.12 * step
        pz = ck.sahte_poz(px_pos, 0.52)
        a.pozlar = [pz]
        a.yuzler = [ck.sahte_yuz(px_pos, 0.30, 0.1)]
    elif o_idx == 5:  # p_refleks
        el1 = ck.sahte_el(0.28, 0.50, "isaret", olcek=0.08)
        el2 = ck.sahte_el(0.72, 0.50, "isaret", olcek=0.08)
        a.eller = [el1, el2]
        a.el_taraf = ["Left", "Right"]
        a.el_skor = [0.95, 0.95]
        a.jestler = ["Pointing_Up", "Pointing_Up"]
        a.jest_skor = [0.95, 0.95]
        a.yuzler = [ck.sahte_yuz(0.28, 0.30, 0.1), ck.sahte_yuz(0.72, 0.30, 0.1)]
    elif o_idx == 6:  # p_hayalet_klon
        pz = ck.sahte_poz(0.50 + 0.06 * math.sin(step), 0.50)
        a.pozlar = [pz]
        a.yuzler = [ck.sahte_yuz(0.50, 0.28, 0.1)]
    elif o_idx == 7:  # p_penalti
        pz = ck.sahte_poz(0.48 + 0.08 * math.sin(step), 0.50)
        a.pozlar = [pz]
    elif o_idx == 8:  # p_ciz_tahmin
        hx = 0.48 + 0.12 * math.cos(step * 1.2)
        hy = 0.48 + 0.12 * math.sin(step * 1.2)
        el = ck.sahte_el(hx, hy, "isaret", olcek=0.08)
        a.eller = [el]
        a.el_taraf = ["Right"]
        a.el_skor = [0.95]
        a.jestler = ["Pointing_Up"]
        a.jest_skor = [0.95]
    return a


def render_menu(cikis_yolu: Path) -> np.ndarray:
    """docs/media/menu.png oluşturur (landmark9 ile seçili kart ve hover ilerlemesi)."""
    ck.stand._DONMUS.clear()
    uyg = stant_app.StantUygulama(ck.Ses(acik=False))
    kare = _arkaplan(0.0)
    kartlar = uyg.menu.kartlar()
    # 4. kart (p_parmak_kusu, indeks 3) üzerinde hover ilerlemesi
    x0, y0, x1, y1 = kartlar[3]
    cx, cy = (x0 + x1) / 2.0 / ck.G, (y0 + y1) / 2.0 / ck.Y
    algi = sahte_menu_algi(cx, cy, jest="Open_Palm")
    t = 1.0
    out = None
    # 30 kare ilerleterek ~%55 hover ilerlemesi oluştur (halka ve ilerleme çubuğu)
    for step in range(30):
        t = 1.0 + (step + 1) * 0.033
        out = uyg.isle(kare.copy(), algi, t)

    assert out is not None
    assert uyg.menu.uzerinde == 3, f"Kart secimi basarisiz: uzerinde={uyg.menu.uzerinde}"
    assert uyg.menu.sure >= 0.4, f"Hover suresi yetersiz: sure={uyg.menu.sure}"

    cikis_yolu.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(cikis_yolu), out)
    if not ok or not cikis_yolu.is_file():
        raise RuntimeError(f"Gorsel kaydedilemedi: {cikis_yolu}")
    print(f"Saved menu snapshot: {cikis_yolu} ({out.shape[1]}x{out.shape[0]})")
    return out


def _kare_isle(out: np.ndarray, o_idx: int, ad_tr: str, mod_ad: str) -> Image.Image:
    """Görseli etiketler ve GIF boyutuna küçültür."""
    caption = f"#{o_idx + 1} {ad_tr} ({mod_ad})"
    ck.panel(out, ck.G // 2 - 240, 14, ck.G // 2 + 240, 50, renk=(16, 12, 26), opak=0.85)
    cv2.rectangle(out, (ck.G // 2 - 240, 14), (ck.G // 2 + 240, 50), ck.CAMGOBEGI, 2, cv2.LINE_AA)
    ck.yazi_koy(out, caption, ck.G // 2, 21, 19, renk=ck.BEYAZ, hiza="orta")
    rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb).resize((640, 360), Image.Resampling.BILINEAR)
    return im.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)


def render_demo(cikis_yolu: Path, quick: bool = False) -> None:
    """docs/media/demo.gif oluşturur (gerçek oyun görselleri, afiş sonrası net akış)."""
    uyg = stant_app.StantUygulama(ck.Ses(acik=False))
    kareler: List[Image.Image] = []
    durations: List[int] = []

    # 1. Menüde gezinme ve hover sahneleri
    t = 10.0
    kartlar = uyg.menu.kartlar()
    k0_cx = (kartlar[0][0] + kartlar[0][2]) / 2.0 / ck.G
    k0_cy = (kartlar[0][1] + kartlar[0][3]) / 2.0 / ck.Y

    menu_adim = 4 if quick else 6
    for step in range(menu_adim):
        t += 0.08
        lerp = step / max(1, menu_adim - 1)
        cur_x = 0.5 * (1.0 - lerp) + k0_cx * lerp
        cur_y = 0.7 * (1.0 - lerp) + k0_cy * lerp
        algi = sahte_menu_algi(cur_x, cur_y, jest="Open_Palm")
        out = uyg.isle(_arkaplan(t), algi, t)
        rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb).resize((640, 360), Image.Resampling.BILINEAR).convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
        kareler.append(im)
        durations.append(180)

    # 2. Deneyimler
    oyun_secim = [0, 3, 8] if quick else list(range(len(OYUN_BILGILERI)))
    for o_idx in oyun_secim:
        mod_ad, ad_tr = OYUN_BILGILERI[o_idx]
        uyg.sec(o_idx, t)

        # 2a. Kısa geçiş sahnesi (afiş) - 1 kare
        t += 0.08
        algi = sahte_oyun_algi(o_idx, t, 0)
        out = uyg.isle(_arkaplan(t), algi, t)
        kareler.append(_kare_isle(out, o_idx, ad_tr, mod_ad))
        durations.append(180)

        # 2b. Afiş süresini (1.7s) atla ve gerçek oyun görselini yakala!
        t = uyg.gecis_t + 1.82

        game_kare_sayisi = 2 if quick else 3
        for sub in range(game_kare_sayisi):
            t += 0.12
            algi = sahte_oyun_algi(o_idx, t, sub + 1)
            out = uyg.isle(_arkaplan(t), algi, t)
            kareler.append(_kare_isle(out, o_idx, ad_tr, mod_ad))
            durations.append(220)

    # 3. Menüye dönüş (2 kare)
    uyg.sec(None, t)
    for sub in range(2):
        t += 0.08
        algi = sahte_menu_algi(0.5, 0.5, jest="Open_Palm")
        out = uyg.isle(_arkaplan(t), algi, t)
        rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb).resize((640, 360), Image.Resampling.BILINEAR).convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
        kareler.append(im)
        durations.append(180)

    cikis_yolu.parent.mkdir(parents=True, exist_ok=True)
    assert len(kareler) > 5, "Demo en az 5 kare olmalıdır"
    kareler[0].save(
        str(cikis_yolu),
        save_all=True,
        append_images=kareler[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    boyut_mb = cikis_yolu.stat().st_size / (1024 * 1024)
    print(f"Saved demo animation: {cikis_yolu} ({len(kareler)} frames, {boyut_mb:.2f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic headless preview generator")
    parser.add_argument("--output", type=str, default="", help="Custom output directory or file prefix")
    parser.add_argument("--quick", action="store_true", help="Generate faster preview with fewer frames")
    args = parser.parse_args()

    menu_path = REPO_ROOT / "docs" / "media" / "menu.png"
    demo_path = REPO_ROOT / "docs" / "media" / "demo.gif"

    if args.output:
        out_base = Path(args.output).resolve()
        if out_base.is_dir() or not out_base.suffix:
            menu_path = out_base / "menu.png"
            demo_path = out_base / "demo.gif"
        else:
            menu_path = out_base.with_suffix(".png")
            demo_path = out_base.with_suffix(".gif")

    print(f"Generating synthetic preview (quick={args.quick})...")
    render_menu(menu_path)
    render_demo(demo_path, quick=args.quick)
    print("Preview generation complete.")


if __name__ == "__main__":
    main()
