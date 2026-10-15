"""README oyun turu GIF'i: menü + her oyun için tek kart. Kullanım: python tools/oyun_turu.py docs/media/oyun-turu.gif"""
import sys
sys.path.insert(0, 'oyunlar')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import cekirdek as ck, stant_app as S

W, H = 640, 360
F = __import__("stand").FONT_YAZI or "DejaVuSans-Bold.ttf"
NASIL = {
    "p_neon_kilic": "Parmağın kılıç olur: uçan meyveleri ya da memeleri dilimle.",
    "p_gulmeme": "İki kişi karşı karşıya: ilk gülen kaybeder.",
    "p_maske": "Başını yana yatır, yüzündeki maske değişsin.",
    "p_parmak_kusu": "Parmağını yukarı aşağı oynat, kuşu borulardan geçir.",
    "p_cevap_yagmuru": "Doğru cevabın tarafına geç, puanı topla.",
    "p_refleks": "ATEŞ yazınca elini rakibinden önce kaldır.",
    "p_hayalet_klon": "Hareket et, klonların seni takip etsin.",
    "p_penalti": "Parmağını topa koy, köşeye yol çiz, kaleciyi geç.",
    "p_ciz_tahmin": "Havaya bir şey çiz, yapay zekâ tahmin etsin.",
}
uyg = S.StantUygulama(ck.Ses(acik=False))

def zemin():
    y = np.linspace(0, 1, H)[:, None, None]
    ust, alt = np.array([34, 20, 26]), np.array([18, 12, 16])
    return np.broadcast_to(ust + (alt - ust) * y, (H, W, 3)).astype(np.uint8).copy()

def yazi(img, metin, y, boy, renk):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil)
    f = ImageFont.truetype(F, boy); w = d.textlength(metin, font=f)
    d.text(((W - w) / 2, y), metin, font=f, fill=renk[::-1])
    img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

def kart(i):
    img = zemin(); ad = S.DENEYIMLER[i]; renk = S.RENKLER[i % len(S.RENKLER)]
    cv2.rectangle(img, (24, 24), (W - 24, H - 24), renk, 2, cv2.LINE_AA)
    yazi(img, f"{i + 1} / 9", 40, 15, (150, 150, 160))
    ck.bindir_merkez(img, uyg.menu.ikonlar[i], W // 2, 140, boyut=130)
    yazi(img, uyg.menu.adlar[i], 222, 34, renk)
    yazi(img, NASIL[ad], 278, 17, (235, 235, 235))
    return img

def menu():
    img = cv2.imread('docs/media/menu.png')
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)

sahneler = [menu()] + [kart(i) for i in range(9)]
kareler, sureler = [], []
for k, sah in enumerate(sahneler):
    onceki = sahneler[k - 1] if k else sahneler[-1]
    for a in (0.33, 0.66):  # yumuşak geçiş
        kareler.append(cv2.addWeighted(onceki, 1 - a, sah, a, 0)); sureler.append(70)
    kareler.append(sah); sureler.append(2600 if k == 0 else 1900)
pil = [Image.fromarray(cv2.cvtColor(k, cv2.COLOR_BGR2RGB)) for k in kareler]
pil = [p.convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for p in pil]
pil[0].save(sys.argv[1], save_all=True, append_images=pil[1:], duration=sureler, loop=0, optimize=True)
