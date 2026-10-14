"""Bilgi Yağmuru soru motoru: tekrar etmeyen torba, seviye merdiveni, tuzaklı sayısal sorular.

Kamerasız test edilir (cv2 yok). Sayısal sorularda yanlış şıklar rastgele değil, bilinen
öğrenci hatalarıdır: işlem önceliğini yok saymak, parantezi unutmak, elde/onluk, işaret.
"""
import re
from fractions import Fraction

EKSI = '−'
_JETON = re.compile(r'\d+|[+−×÷()]')
_ISLEM = {'+': lambda x, y: x + y, '−': lambda x, y: x - y, '×': lambda x, y: x * y, '÷': lambda x, y: x / y}


def yaz(n):
    """Tam sayıyı ekranda gösterilecek biçimde yazar; eksi işareti U+2212."""
    n = int(n)
    return f'{EKSI}{-n}' if n < 0 else str(n)


def _yz(v):
    return yaz(v) if Fraction(v).denominator == 1 else f'{float(v):.2f}'.replace('.', ',')


def _sayi(v):
    return int(v) if v.denominator == 1 else float(v)


def coz(ifade, oncelikli=True):
    """İfadeyi adım adım indirger. Döner: (Fraction değer, ['4 × 2 = 8', ...]).

    oncelikli=False: parantez yine önce, ama işlemler öncelik gözetmeden soldan sağa.
    """
    t = [Fraction(int(x)) if x.isdigit() else x for x in _JETON.findall(ifade)]
    adimlar = []
    while len(t) > 1:
        if '(' in t:
            a = max(i for i, x in enumerate(t) if x == '(')
            b = t.index(')', a)
        else:
            a, b = -1, len(t)
        ic = t[a + 1:b]
        if len(ic) == 1:
            t[a:b + 1] = ic
            continue
        i = 1
        if oncelikli:
            i = next((k for k in range(1, len(ic), 2) if ic[k] in ('×', '÷')), 1)
        x, op, y = ic[i - 1], ic[i], ic[i + 1]
        z = _ISLEM[op](x, y)
        adimlar.append(f'{_yz(x)} {op} {_yz(y)} = {_yz(z)}')
        ic[i - 1:i + 2] = [z]
        t[a + 1:b] = ic
    return t[0], adimlar


def hesapla(ifade):
    return _sayi(coz(ifade)[0])


def soldan_saga(ifade):
    """İşlem önceliği hatası yapan öğrencinin cevabı."""
    return _sayi(coz(ifade, oncelikli=False)[0])


def _r(rng, a, b):
    return int(rng.integers(a, b + 1))


# ---------------------------------------------------------------- sayısal soru üretimi
def _ifade(rng, seviye):
    """Seviyeye göre (ifade, tuzak adayları) üretir. Adaylar: [(etiket, değer)], öncelikli olan başta."""
    if seviye == 1:
        a, b = _r(rng, 2, 49), _r(rng, 1, 19)
        if rng.random() < .5:
            return f'{a} + {b}', [('bir', a + b + 1), ('bir', a + b - 1), ('on', a + b + 10)]
        a, b = max(a, b), min(a, b)
        return f'{a} − {b}', [('bir', a - b + 1), ('bir', a - b - 1), ('ters', a + b)]
    if seviye == 2:
        while True:
            a, b = _r(rng, 15, 89), _r(rng, 12, 79)
            if rng.random() < .5 and a % 10 + b % 10 >= 10:
                return f'{a} + {b}', [('elde', a + b - 10), ('on', a + b + 10), ('bir', a + b + 1)]
            a, b = max(a, b), min(a, b)
            if a % 10 < b % 10:
                return f'{a} − {b}', [('onluk', a - b + 10), ('on', a - b - 10), ('bir', a - b - 1)]
    if seviye == 3:
        a, b = _r(rng, 2, 12), _r(rng, 3, 15)
        if rng.random() < .5:
            return f'{a} × {b}', [('komsu', a * (b + 1)), ('komsu', a * (b - 1)), ('bir', a * b + 1)]
        return f'{a * b} ÷ {a}', [('bir', b + 1), ('bir', b - 1), ('carpim', a * b - a)]
    if seviye == 4:
        b, c, m = _r(rng, 2, 9), _r(rng, 2, 9), _r(rng, 1, 9)
        kalip = int(rng.integers(4))
        if kalip == 0:
            ifade = f'{_r(rng, 2, 40)} + {b} × {c}'
        elif kalip == 1:
            ifade = f'{b * c + _r(rng, 1, 40)} − {b} × {c}'
        elif kalip == 2:
            ifade = f'{c * m} + {c * b} ÷ {c}'
        else:
            ifade = f'{c * (m + b)} − {c * b} ÷ {c}'
        return ifade, []
    a, b, c = _r(rng, 2, 9), _r(rng, 2, 9), _r(rng, 2, 9)
    d, e = _r(rng, 2, 15), _r(rng, 2, 15)
    kalip = int(rng.integers(3))
    if kalip == 0:
        ifade = f'{a * b} ÷ {b} + {c} × ({d} − {e})'
    elif kalip == 1:
        k, m = _r(rng, 1, 9), _r(rng, 2, 12)
        ifade = f'{c * m} − {c * k} ÷ {c} × ({d} − {e})'
    else:
        a, q = _r(rng, 2, 5), _r(rng, 2, 6)
        d = _r(rng, 1, a * q - 1)
        ifade = f'({d} + {a * q - d}) ÷ {a} + {b} × {c}'
    return ifade, []


def _siklar(rng, dogru, oncelikli, digerleri):
    """Doğru dışında iki tam sayı, benzersiz şık seçer. Döner: (değerler, etiketler)."""
    sira = [digerleri[i] for i in rng.permutation(len(digerleri))] if digerleri else []
    secilen, etiket = [], []
    for e, v in oncelikli + sira:
        v = Fraction(v)
        if v.denominator == 1 and v != dogru and v not in secilen:
            secilen.append(v)
            etiket.append(e)
        if len(secilen) == 2:
            break
    k = 2
    while len(secilen) < 2:
        for v in (dogru + k, dogru - k):
            if v not in secilen and len(secilen) < 2:
                secilen.append(v)
                etiket.append('yakin')
        k += 1
    return secilen, etiket


def sayisal(rng, seviye, haric=()):
    """Seviyeye uygun tuzaklı işlem sorusu. haric: son sorulan id'ler, tekrar üretilmez."""
    seviye = max(1, min(5, int(seviye)))
    for _ in range(200):
        ifade, adaylar = _ifade(rng, seviye)
        kimlik = f's{seviye}-{ifade}'
        dogru, cozum = coz(ifade)
        ss = coz(ifade, oncelikli=False)[0]
        if kimlik in haric or dogru.denominator != 1:
            continue
        if seviye <= 3 and dogru < 0:
            continue
        oncelik = []
        if seviye >= 4:
            # tuzak ancak inandırıcı büyüklükteyse tuzaktır; 896 gibi şık kendini ele verir
            makul = lambda v: abs(v - dogru) <= max(30, abs(dogru))
            if ss == dogru or ss.denominator != 1 or not makul(ss):
                continue
            oncelik = [('oncelik', ss)]
            adaylar = [('isaret', -dogru), ('bir', dogru + 1), ('bir', dogru - 1), ('on', dogru + 10)]
            if '(' in ifade:
                parsiz = coz(ifade.replace('(', '').replace(')', ''))[0]
                (oncelik if makul(parsiz) else adaylar).append(('parantez', parsiz))
        yanlis, tuzak = _siklar(rng, dogru, oncelik, adaylar)
        degerler = [dogru] + yanlis
        p = rng.permutation(3)
        return dict(id=kimlik, kategori='sayısal', tip='coktan', soru=f'{ifade} = ?',
                    secenekler=[yaz(degerler[i]) for i in p], dogru_indeks=int(list(p).index(0)),
                    zorluk=seviye, kaynak='Hesaplanan işlem', cozum=cozum, tuzaklar=tuzak)
    raise RuntimeError(f'seviye {seviye} için soru üretilemedi')


# ---------------------------------------------------------------- banka torbası ve zorluk merdiveni
class Torba:
    """Seviye başına karışık torba: torba bitmeden aynı soru gelmez.

    Yeniden dolumda son çekilenlerin 3/4'ü torbanın sonuna atılır; tur dönerken
    az önce görülen soru hemen geri gelmez. Banka yerinde değişmez.
    """

    def __init__(self, banka, rng):
        self.rng = rng
        self.gruplar = {}
        for s in banka:
            self.gruplar.setdefault(int(s['zorluk']), []).append(s)
        self.torbalar = {z: [] for z in self.gruplar}
        self.son = {z: [] for z in self.gruplar}

    def cek(self, seviye):
        z = min(self.gruplar, key=lambda k: (abs(k - seviye), k))
        grup = self.gruplar[z]
        if not self.torbalar[z]:
            sira = [grup[i] for i in self.rng.permutation(len(grup))]
            yakin = set(self.son[z][-(len(grup) * 3 // 4):]) if len(grup) > 1 else set()
            self.torbalar[z] = [s for s in sira if s['id'] not in yakin] + [s for s in sira if s['id'] in yakin]
        s = dict(self.torbalar[z].pop(0))
        self.son[z] = (self.son[z] + [s['id']])[-len(grup):]
        if s['tip'] == 'coktan':
            p = self.rng.permutation(len(s['secenekler']))
            s['secenekler'] = [s['secenekler'][i] for i in p]
            s['dogru_indeks'] = int(list(p).index(s['dogru_indeks']))
        return s


class Merdiven:
    """3 ardışık doğru bir seviye çıkarır, 2 ardışık yanlış bir seviye indirir."""

    def __init__(self, en_az=1, en_cok=5):
        self.en_az, self.en_cok, self.seviye = en_az, en_cok, en_az
        self.dogru_seri = self.yanlis_seri = 0

    def kaydet(self, dogru):
        """Döner: seviye değişimi (+1, −1 ya da 0)."""
        if dogru:
            self.dogru_seri, self.yanlis_seri = self.dogru_seri + 1, 0
        else:
            self.dogru_seri, self.yanlis_seri = 0, self.yanlis_seri + 1
        adim = 1 if self.dogru_seri >= 3 else -1 if self.yanlis_seri >= 2 else 0
        if adim:
            once = self.seviye
            self.seviye = min(max(self.seviye + adim, self.en_az), self.en_cok)
            self.dogru_seri = self.yanlis_seri = 0
            return self.seviye - once
        return 0
